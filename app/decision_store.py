"""Append-only local experiment/actual-fill ledger, beside existing JevWIN data."""
from dataclasses import asdict
from pathlib import Path
import json
import sqlite3
import time
from app_store import UserStore, _safe_payload, data_directory
from decision_engine import AccountState, decimal, money, POINT_VALUE
from app_core import number


class DecisionStore:
    def __init__(self, directory=None):
        directory = Path(directory) if directory else data_directory()
        directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(directory/'decision-lab.sqlite3')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, body TEXT NOT NULL); CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY, ts_ms INTEGER NOT NULL, kind TEXT NOT NULL, body TEXT NOT NULL, event_key TEXT UNIQUE);')
        if self.db.execute("SELECT body FROM state WHERE key='account'").fetchone() is None:
            legacy = UserStore(directory)
            settings = legacy.settings()
            legacy.close()
            try:
                current = str(number(settings.get('current', '400')))
                peak = str(number(settings.get('peak', current)))
            except ValueError:
                self.db.close()
                raise
            account = AccountState(equity_brl=current, peak_brl=str(max(decimal(peak), decimal(current))), available_margin_brl=str(max(decimal(current), decimal(0))), asof_ms=int(time.time()*1000))
            self._save(account)

    def _save(self, account):
        self.db.execute('INSERT INTO state VALUES(?,?) ON CONFLICT(key) DO UPDATE SET body=excluded.body', ('account', json.dumps(asdict(account), allow_nan=False)))
        self.db.commit()

    def account(self):
        return AccountState(**json.loads(self.db.execute("SELECT body FROM state WHERE key='account'").fetchone()[0]))

    def update_account(self, values, expected_revision):
        old = self.account()
        if type(expected_revision) is not int or old.revision != expected_revision:
            raise ValueError('Conta mudou; atualize os valores exibidos')
        allowed = {'equity_brl', 'available_margin_brl'}
        if set(values)-allowed or not values:
            raise ValueError('Campos de conta inválidos')
        equity = decimal(values.get('equity_brl', old.equity_brl))
        account = AccountState(equity_brl=str(equity), peak_brl=str(max(equity, decimal(old.peak_brl))), available_margin_brl=str(decimal(values.get('available_margin_brl', max(equity, decimal(0))), nonnegative=True)), positions=old.positions, revision=old.revision+1, asof_ms=int(time.time()*1000))
        with self.db:
            if old.positions and equity != decimal(old.equity_brl):
                self.record('financial_divergence', dict(origin='manual_reconciliation', previous_equity_brl=old.equity_brl, reported_equity_brl=str(equity), executions_preserved=True), commit=False)
            self.record('account_reconciliation', account.to_dict(), commit=False)
            self.db.execute('UPDATE state SET body=? WHERE key=?', (json.dumps(asdict(account)), 'account'))
        return account

    def _seen(self, key, payload):
        if not isinstance(key, str) or not 1 <= len(key) <= 128:
            raise ValueError('ID único da execução é obrigatório')
        row = self.db.execute('SELECT body FROM ledger WHERE event_key=?', (key,)).fetchone()
        if row and json.loads(row[0]) != payload:
            raise ValueError('ID já utilizado com valores diferentes')
        return bool(row)

    def open_position(self, key, side, quantity, price, margin, fees, symbol, *, executed_at_ms=None, hypothesis=None, expected_revision=None):
        payload = dict(side=side, quantity=quantity, price=str(price), margin=str(margin), fees=str(fees), symbol=symbol)
        if executed_at_ms is not None: payload['executed_at_ms'] = self._execution_time(executed_at_ms)
        if hypothesis is not None: payload['hypothesis'] = _safe_payload(hypothesis)
        if self._seen(key, payload):
            return self.account()
        account = self.account()
        price, margin, fees = decimal(price, nonnegative=True), decimal(margin, nonnegative=True), decimal(fees, nonnegative=True)
        if expected_revision is not None and expected_revision != account.revision:
            raise ValueError('Conta mudou; revise a execução declarada')
        if side not in ('buy', 'sell') or type(quantity) is not int or not 1 <= quantity <= 10000 or price <= 0 or price%5 or not isinstance(symbol, str) or not symbol.startswith('WIN') or len(symbol)>24:
            raise ValueError('Execução/posição inválida')
        if account.positions:
            p=account.positions[0]
            if p['side']!=side or p['symbol']!=symbol or p['quantity']+quantity>10000:
                raise ValueError('Somente parcelas da mesma posição consolidada são permitidas')
            total=p['quantity']+quantity
            p['entry_points']=str((decimal(p['entry_points'])*p['quantity']+price*quantity)/total)
            p['quantity']=total
            p['reserved_margin_brl']=money(decimal(p['reserved_margin_brl'])+margin)
            p['realized_brl']=money(decimal(p.get('realized_brl','0'))-fees)
        else:
            p=dict(id=key, side=side, quantity=quantity, entry_points=str(price), reserved_margin_brl=money(margin), symbol=symbol,
                   executed_at_ms=executed_at_ms if executed_at_ms is not None else int(time.time()*1000),
                   hypothesis_origin=_safe_payload(hypothesis), stop_points=None, target_points=None, premise=None,
                   realized_brl=money(-fees), manual_revision=0)
            account.positions=[p]
        divergence=margin>decimal(account.available_margin_brl) or fees>max(decimal(account.equity_brl),decimal(0))
        account.equity_brl = money(decimal(account.equity_brl)-fees)
        account.available_margin_brl = money(max(decimal(0), decimal(account.available_margin_brl)-margin-fees))
        account.revision += 1
        account.asof_ms = int(time.time()*1000)
        with self.db:
            if divergence:
                self.record('financial_divergence', dict(origin='actual_manual_entry', execution_key=key, reason='REPORTED_EXECUTION_EXCEEDS_INFORMED_CAPACITY', executions_preserved=True), commit=False)
            self.record('actual_manual_entry', payload, key=key, commit=False)
            self.record('account_after_fill', account.to_dict(), commit=False)
            self.db.execute('UPDATE state SET body=? WHERE key=?', (json.dumps(asdict(account)), 'account'))
        return account

    def close_position(self, key, quantity, price, fees, *, executed_at_ms=None, expected_revision=None):
        payload = dict(quantity=quantity, price=str(price), fees=str(fees))
        if executed_at_ms is not None:payload['executed_at_ms']=self._execution_time(executed_at_ms)
        if self._seen(key, payload):
            return self.account()
        account = self.account()
        if expected_revision is not None and expected_revision!=account.revision:
            raise ValueError('Conta mudou; revise a execução declarada')
        price, fees = decimal(price, nonnegative=True), decimal(fees, nonnegative=True)
        if not account.positions or type(quantity) is not int or not 1 <= quantity <= account.positions[0]['quantity'] or price <= 0 or price%5:
            raise ValueError('Saída parcial inválida')
        position = account.positions[0]
        gross = (price-decimal(position['entry_points']))*(1 if position['side']=='buy' else -1)*POINT_VALUE*quantity
        released = decimal(money(decimal(position['reserved_margin_brl'])*quantity/position['quantity']))
        position['realized_brl']=money(decimal(position.get('realized_brl','0'))+gross-fees)
        payload['position_id']=position['id']
        # The immutable execution payload must stay identical on retry.
        payload.pop('position_id')
        equity = decimal(account.equity_brl)+gross-fees
        account.equity_brl = money(equity)
        account.peak_brl = money(max(decimal(account.peak_brl), equity))
        account.available_margin_brl = money(max(decimal(0), min(max(equity, decimal(0)), decimal(account.available_margin_brl)+released+gross-fees)))
        position['quantity'] -= quantity
        position['reserved_margin_brl'] = money(decimal(position['reserved_margin_brl'])-released)
        if not position['quantity']:
            account.positions = []
        account.revision += 1
        account.asof_ms = int(time.time()*1000)
        with self.db:
            self.record('actual_manual_exit', payload, key=key, commit=False)
            self.record('account_after_fill', account.to_dict(), commit=False)
            self.db.execute('UPDATE state SET body=? WHERE key=?', (json.dumps(asdict(account)), 'account'))
        return account

    @staticmethod
    def _execution_time(value):
        if type(value) is not int or not 0<=value<=10**15:
            raise ValueError('Horário declarado inválido')
        return value

    def revise_position(self, *, key, expected_revision, stop, target, premise):
        if not isinstance(premise,str) or not 1<=len(premise.strip())<=1000:
            raise ValueError('Premissa manual obrigatória')
        stop,target=decimal(stop,nonnegative=True),decimal(target,nonnegative=True)
        if stop<=0 or target<=0 or stop%5 or target%5:raise ValueError('Stop/alvo fora do grid')
        payload=dict(stop_points=str(stop),target_points=str(target),premise=premise,origin='manual')
        if self._seen(key,payload):return self.account()
        account=self.account()
        if type(expected_revision) is not int or expected_revision!=account.revision or not account.positions:
            raise ValueError('Posição mudou; revise os valores exibidos')
        p=account.positions[0]
        if (p['side']=='buy' and stop>=target) or (p['side']=='sell' and stop<=target):
            raise ValueError('Geometria manual inconsistente')
        p.update(payload,manual_revision=p.get('manual_revision',0)+1)
        account.revision+=1;account.asof_ms=int(time.time()*1000)
        with self.db:
            self.record('position_manual_revision',payload,key=key,commit=False)
            self.db.execute('UPDATE state SET body=? WHERE key=?',(json.dumps(asdict(account)),'account'))
        return account

    def record(self, kind, payload, *, key=None, commit=True):
        body = json.dumps(_safe_payload(payload), ensure_ascii=False, allow_nan=False)
        if len(body)>2_000_000:
            raise ValueError('Registro experimental excede limite por evento')
        self.db.execute('INSERT INTO ledger(ts_ms,kind,body,event_key) VALUES(?,?,?,?)', (int(time.time()*1000), kind, body, key))
        if commit:
            self.db.commit()

    def history(self, limit=200):
        if type(limit) is not int or not 1 <= limit <= 10000:
            raise ValueError('Limite inválido')
        rows = self.db.execute('SELECT id,ts_ms,kind,body FROM ledger ORDER BY id DESC LIMIT ?', (limit,))
        return [dict(id=i, ts_ms=ts, kind=k, payload=json.loads(b)) for i, ts, k, b in rows]

    def close(self):
        self.db.close()

"""Persistent, transactional authorization of API spending, not billing inference."""
from datetime import datetime, timezone, date
import json
from pathlib import Path
import sqlite3
import time
from zoneinfo import ZoneInfo
from app_store import data_directory
from decision_engine import decimal, money


def _day(now_ms):
    return datetime.fromtimestamp(now_ms/1000, timezone.utc).astimezone(ZoneInfo('America/Sao_Paulo')).date().isoformat()


class ApiBudget:
    def __init__(self, directory=None):
        path=Path(directory) if directory else data_directory()
        path.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path/'decision-lab.sqlite3',timeout=5)
        self.db.executescript('''CREATE TABLE IF NOT EXISTS api_price(id INTEGER PRIMARY KEY CHECK(id=1),body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS api_attempt(request_id TEXT PRIMARY KEY,day TEXT NOT NULL,currency TEXT NOT NULL,
                reserved TEXT NOT NULL,estimated TEXT,confirmed TEXT,status TEXT NOT NULL,price TEXT NOT NULL,usage TEXT,billing_ref TEXT);
            CREATE TABLE IF NOT EXISTS api_billing_log(id INTEGER PRIMARY KEY,request_id TEXT,at_ms INTEGER,amount TEXT,reference TEXT);''')

    def config(self):
        row=self.db.execute('SELECT body FROM api_price WHERE id=1').fetchone()
        return json.loads(row[0]) if row else None

    def configure(self, values, *, now_ms=None):
        expected={'daily_calls','daily_spend','reserve_per_call','price_per_call','currency','source','effective_from','effective_until','conservative_basis','upper_bound_confirmed'}
        if not isinstance(values,dict) or set(values)!=expected:
            raise ValueError('Informe tetos, preço, moeda, fonte, vigência e base da reserva')
        if type(values['daily_calls']) is not int or not 1<=values['daily_calls']<=10000 or values['upper_bound_confirmed'] is not True:
            raise ValueError('Confirme um limite superior conservador por chamada')
        for field in ('currency','source','conservative_basis'):
            if not isinstance(values[field],str) or not 1<=len(values[field].strip())<=512:
                raise ValueError('Moeda, fonte e base da reserva são obrigatórias')
        if values['currency'] not in ('BRL','USD','EUR'):
            raise ValueError('Moeda não suportada')
        start,end=(date.fromisoformat(values[k]) for k in ('effective_from','effective_until'))
        if start>end:
            raise ValueError('Vigência inválida')
        v=dict(values)
        for field in ('daily_spend','reserve_per_call','price_per_call'):
            amount=decimal(v[field],nonnegative=True)
            if amount<=0 or amount!=decimal(money(amount)):
                raise ValueError('Valores de orçamento devem ser positivos em centavos')
            v[field]=money(amount)
        if decimal(v['reserve_per_call'])<decimal(v['price_per_call']):
            raise ValueError('Reserva não pode ser inferior ao preço informado')
        now_ms=now_ms if now_ms is not None else int(time.time()*1000)
        if not v['effective_from']<=_day(now_ms)<=v['effective_until']:
            raise ValueError('Preço fora da vigência')
        try:
            self.db.execute('BEGIN IMMEDIATE')
            old=self.config()
            if old and old['currency']!=v['currency'] and self.db.execute('SELECT 1 FROM api_attempt WHERE confirmed IS NULL LIMIT 1').fetchone():
                raise ValueError('Concilie o consumo pendente antes de mudar moeda')
            self.db.execute('INSERT INTO api_price VALUES(1,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',(json.dumps(v),))
            self.db.commit()
        except Exception:
            self.db.rollback();raise
        return self.snapshot(now_ms=now_ms)

    def snapshot(self, *, now_ms=None):
        now_ms=now_ms if now_ms is not None else int(time.time()*1000)
        day=_day(now_ms);config=self.config()
        currency=config['currency'] if config else None
        rows=self.db.execute('SELECT request_id,day,reserved,estimated,confirmed,status,currency FROM api_attempt').fetchall()
        relevant=[r for r in rows if r[6]==currency and (r[1]==day or r[4] is None)]
        reserved=sum((decimal(r[2]) for r in relevant if r[4] is None),decimal(0))
        confirmed=sum((decimal(r[4]) for r in relevant if r[4] is not None and r[1]==day),decimal(0))
        estimated=sum((decimal(r[3]) for r in relevant if r[3] is not None),decimal(0))
        calls=sum(r[1]==day for r in rows)
        reasons=[]
        if not config:reasons.append('API_PRICE_REQUIRED')
        else:
            if not config['effective_from']<=day<=config['effective_until']:reasons.append('API_PRICE_EXPIRED')
            if calls>=config['daily_calls']:reasons.append('DAILY_CALL_LIMIT')
            if confirmed+reserved+decimal(config['reserve_per_call'])>decimal(config['daily_spend']):reasons.append('DAILY_SPEND_LIMIT')
            # A billed amount above the attested cap invalidates that cap.
            if any(r[4] is not None and decimal(r[4])>decimal(r[2]) for r in relevant):reasons.append('RESERVE_UPPER_BOUND_BREACHED')
        return dict(day=day,timezone='America/Sao_Paulo',config=config,calls=calls,reserved=money(reserved),
                    estimated=money(estimated),confirmed=money(confirmed),eligible=not reasons,reason_codes=reasons,
                    pending=[dict(request_id=r[0],day=r[1],reserved=r[2],estimated=r[3],status=r[5]) for r in relevant if r[4] is None])

    def reserve(self, request_id, *, now_ms=None):
        if not isinstance(request_id,str) or not 1<=len(request_id)<=128:raise ValueError('ID de tentativa inválido')
        now_ms=now_ms if now_ms is not None else int(time.time()*1000)
        try:
            self.db.execute('BEGIN IMMEDIATE')
            if self.db.execute('SELECT 1 FROM api_attempt WHERE request_id=?',(request_id,)).fetchone():
                raise ValueError('Tentativa já reservada; não repita a chamada')
            status=self.snapshot(now_ms=now_ms)
            if not status['eligible']:raise ValueError('Orçamento indisponível: '+', '.join(status['reason_codes']))
            c=status['config']
            self.db.execute('INSERT INTO api_attempt(request_id,day,currency,reserved,status,price) VALUES(?,?,?,?,?,?)',
                            (request_id,status['day'],c['currency'],c['reserve_per_call'],'reserved',json.dumps(c)))
            self.db.commit()
        except Exception:
            self.db.rollback();raise
        return self.snapshot(now_ms=now_ms)

    def mark_response(self, request_id, *, usage=None, failed=False):
        row=self.db.execute('SELECT price FROM api_attempt WHERE request_id=?',(request_id,)).fetchone()
        if not row:raise ValueError('Reserva ausente')
        config=json.loads(row[0])
        self.db.execute('UPDATE api_attempt SET estimated=?,usage=?,status=? WHERE request_id=? AND confirmed IS NULL',
                        (config['price_per_call'] if usage else None,json.dumps(usage) if usage else None,
                         'failed_consumption_pending' if failed else 'consumption_pending',request_id))
        self.db.commit()

    def confirm(self, request_id, amount, *, reference, now_ms=None):
        amount=decimal(amount,nonnegative=True)
        if amount!=decimal(money(amount)) or not isinstance(reference,str) or not 1<=len(reference.strip())<=512:
            raise ValueError('Informe valor apurado e referência do faturamento')
        amount=money(amount)
        try:
            self.db.execute('BEGIN IMMEDIATE')
            row=self.db.execute('SELECT confirmed,billing_ref FROM api_attempt WHERE request_id=?',(request_id,)).fetchone()
            if not row:raise ValueError('Tentativa ausente')
            if row[0] is not None and (row[0]!=amount or row[1]!=reference):raise ValueError('Apuração já registrada com valores diferentes')
            if row[0] is None:
                self.db.execute('UPDATE api_attempt SET confirmed=?,billing_ref=?,status=? WHERE request_id=?',(amount,reference,'confirmed',request_id))
                self.db.execute('INSERT INTO api_billing_log(request_id,at_ms,amount,reference) VALUES(?,?,?,?)',
                                (request_id,now_ms if now_ms is not None else int(time.time()*1000),amount,reference))
            self.db.commit()
        except Exception:
            self.db.rollback();raise
        return self.snapshot(now_ms=now_ms)

    def close(self):self.db.close()

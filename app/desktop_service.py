"""Versioned JSON-lines Python sidecar. Only the owner thread mutates state."""
from __future__ import annotations
import argparse
import hashlib
from dataclasses import asdict
import json
from pathlib import Path
import queue
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
import webbrowser

from app_core import ObservationSession, DEFAULT_INPUTS, build_risk_study, jev_observation_state, can_classify
from app_store import resource_path, UserStore
from candidate_research import build_market_candidates, generate_candidate_scenario
from context_requests import attach_candidates
from decision_engine import AccountState, CostSchedule, MarketSnapshot, compare_plans, select_plan
from decision_store import DecisionStore
from jev_client import JevClient
from profit_bridge import CombinedExcelBridge, SourceBatch, MarketEvent, QuoteSnapshot, SourceHealth, read_csv_events
from release_updates import check_for_updates, current_version, update_state, trusted_release_url

EXPERIMENT_RESOURCES = ('desktop_service.py', 'app_core.py', 'app_store.py', 'capital_example.py',
                        'decision_engine.py', 'decision_store.py', 'context_requests.py', 'candidate_engine.py',
                        'candidate_research.py', 'flow_engine.py', 'profit_bridge.py', 'recommendation_engine.py',
                        'jev_client.py', 'copilot.py', 'capital_planner.py', 'risk.py', 'risk_research.py',
                        'config.json', 'flow_rules.json', 'observer_questions.json')


def batch_from_wire(data):
    health = data['health']
    return SourceBatch(tuple(MarketEvent(x.get('id'), x['symbol'], x['ts_ms'], x['price_points'], x['quantity'], x['aggressor']) for x in data['events']),
                       tuple(QuoteSnapshot(**x) for x in data['quotes']),
                       SourceHealth(**{k: health[k] for k in SourceHealth.__dataclass_fields__ if k in health}), tuple(data.get('warnings', [])))


def own_command(*args):
    return [sys.executable, *args] if getattr(sys, 'frozen', False) else [sys.executable, '-u', str(Path(__file__).resolve()), *args]


class ExcelCollector:
    """COM may hang forever. Timeout terminates this owned worker, never Excel."""
    def __init__(self, config, timeout=5):
        self.timeout = timeout
        self.process = subprocess.Popen(own_command('--excel-worker'), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                        text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
        self.responses = queue.Queue()
        self.pending_at = None
        self.next_read_at = 0.
        self._write(dict(config=config))
        def read():
            try:
                for line in self.process.stdout:
                    try:
                        self.responses.put(json.loads(line))
                    except ValueError:
                        self.responses.put({'error': 'Resposta inválida do coletor'})
            except (OSError, ValueError):
                pass
        threading.Thread(target=read, daemon=True).start()

    def _write(self, value):
        self.process.stdin.write(json.dumps(value, allow_nan=False)+'\n')
        self.process.stdin.flush()

    def poll(self):
        try:
            value = self.responses.get_nowait()
            self.pending_at = None
            return value
        except queue.Empty:
            pass
        if self.process.poll() is not None:
            raise ValueError('Coletor Excel encerrou; reconecte a fonte')
        if self.pending_at is not None and time.monotonic()-self.pending_at > self.timeout:
            self.close()
            raise ValueError('Excel ocupado: tempo excedido; coletor encerrado. Reconecte a fonte.')
        if self.pending_at is None and time.monotonic() >= self.next_read_at:
            self._write({'read': True})
            self.pending_at = time.monotonic()
            self.next_read_at = self.pending_at + 1.
        return None

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        for stream in (self.process.stdin, self.process.stdout):
            if stream:
                stream.close()


class DecisionService:
    def __init__(self, directory=None, *, update_checker=check_for_updates):
        self.store = DecisionStore(directory)
        self.settings = UserStore(directory)
        self.session = ObservationSession()
        self.costs = CostSchedule()
        self.latest_jev = None
        self.api_key = ''
        self.api_calls = 0
        self.api_limit = 120
        self.api_last_at = 0.
        self.pending_jev = False
        self.results = queue.Queue()
        self.update_results = queue.Queue()
        self.update_checker = update_checker
        self.updates = update_state(current_version())
        self.collector = None
        self.source_error = None
        self.sequence = 0
        self.closed = False
        self.code_hash = hashlib.sha256(b''.join(name.encode() + b'\0' + resource_path(name).read_bytes() for name in EXPERIMENT_RESOURCES)).hexdigest()
        legacy_settings = self.settings.settings()
        self.source_config = {k: v for k, v in legacy_settings.items() if k in ('symbol', 'workbook', 'tape_sheet', 'tape_range')}
        self.source_config.update({new: legacy_settings[old] for old, new in (('sheet', 'quote_sheet'), ('cell_range', 'quote_range')) if old in legacy_settings})
        saved = self.store.db.execute("SELECT body FROM state WHERE key='costs'").fetchone()
        if saved:
            self.costs = CostSchedule(**json.loads(saved[0]))

    def technical(self, market):
        # Reuse only the causal geometry recipe; legacy fixed-stop risk remains
        # available in Tkinter. The new engine evaluates every quantity itself.
        study = build_risk_study(DEFAULT_INPUTS, now_ms=market['ts_ms'])
        return build_market_candidates(self.session.engine, market, study['config'], study['account'], market['ts_ms'])

    def snapshot(self):
        market = self.session.snapshot()
        account = self.store.account()
        technical = self.technical(market)
        rows = technical['rows']
        plans = compare_plans(rows, account, self.costs, now_ms=market['ts_ms'])
        main = select_plan(plans, drawdown=min(1., account.to_dict()['drawdown']))
        latest = self.latest_jev if self.latest_jev and self.accepts(self.latest_jev) else None
        dimensions = None
        if latest:
            answers = latest['response']['answers']
            if latest['state'].get('candidate_setups'):
                dimensions = {k: answers.get('candidate_0_'+k, {}).get('noul') for k in ('support', 'contradiction', 'insufficient')}
            dimensions = dimensions or {'support': None, 'contradiction': None, 'insufficient': answers.get('evidence_insufficient', {}).get('noul')}
        history = self.store.history(200)
        equity_history = []
        for event in reversed(history):
            if event['kind'] in ('account_reconciliation', 'account_after_fill'):
                equity_history.append({'ts_ms': event['ts_ms'], 'equity_brl': event['payload']['equity_brl']})
        equity_history.append({'ts_ms': account.asof_ms or int(time.time()*1000), 'equity_brl': account.equity_brl})
        self.sequence += 1
        return {'schema_version': 1, 'sequence': self.sequence, 'generated_at_ms': int(time.time()*1000),
                'market': market, 'account': account.to_dict(), 'costs': asdict(self.costs), 'decision': main,
                'alternatives': plans[1:], 'technical': technical, 'context': dimensions,
                'jev': {'configured': bool(self.api_key), 'calls': self.api_calls, 'limit': self.api_limit,
                        'pending': self.pending_jev, 'current': latest is not None, 'model': 'jev-1.13.0', 'financial_probability': None},
                'source': {'error': self.source_error, 'excel_running': self.collector is not None, 'config': self.source_config},
                'equity_history': equity_history, 'history': history[:40],
                'updates': dict(self.updates),
                'research': {'status': 'EMPIRICAL_VALIDATION_PENDING', 'logistic_baseline': 'offline CLI: scripts/run_decision_lab.py',
                             'profitdll': 'SDK_AUTHORIZED_REQUIRED', 'risk_catalog': ['fixed_lot', 'fixed_cash', 'initial_fraction', 'current_fraction', 'kelly', 'fractional_kelly', 'drawdown_kelly', 'volatility', 'optimal_f', 'fixed_ratio', 'paroli', 'partial_reinvest', 'pyramiding', 'martingale', 'dalembert', 'fibonacci', 'labouchere'],
                             'profit_target': None, 'drawdown_pause': None}, 'orders_enabled': False}

    def accepts(self, result):
        market = self.session.snapshot()
        now = market['ts_ms']
        current = self.technical(market)['rows']
        original = result.get('state', {}).get('candidate_setups', [])
        fields = ('id', 'premise', 'hypothesis_version', 'entry_points', 'stop_points', 'target_points')
        same = all(any(all(str(row.get(k)) == str(old.get(k)) for k in fields) for row in current) for old in original)
        return (same and result.get('source_generation') == self.session.source_generation and result.get('account_revision') == self.store.account().revision
                and type(result.get('flow_ts_ms')) is int and 0 <= now-result['flow_ts_ms'] <= 2000)

    def command(self, method, params):
        if not isinstance(params, dict):
            raise ValueError('Parâmetros inválidos')
        if method == 'snapshot':
            pass
        elif method == 'updates.check':
            self.request_update_check()
        elif method == 'updates.open':
            if self.updates['status'] != 'available' or not trusted_release_url(self.updates['release_url']):
                raise ValueError('Nenhuma atualização verificada disponível')
            if not webbrowser.open(self.updates['release_url']):
                raise ValueError('Não foi possível abrir a página da atualização')
        elif method == 'source.demo':
            self.disconnect()
            fixture = generate_candidate_scenario()
            self.session.reset('WIN_SIM')
            self.session.mode = 'synthetic'
            self.session.clock_ms = fixture['now_ms']
            self.session.engine.set_source_quality(fixture['source_quality'])
            for event in fixture['events']:
                (self.session.engine.add_trade if event['type']=='trade' else self.session.engine.set_book)(event)
            self.session.warnings = ['Demonstração histórica sintética, sem dados atuais da B3.']
        elif method == 'account.update':
            self.store.update_account({k: v for k, v in params.items() if k != 'revision'}, params.get('revision'))
            self.latest_jev = None
        elif method == 'position.open':
            self.store.open_position(**params)
            self.latest_jev = None
        elif method == 'position.close':
            self.store.close_position(**params)
            self.latest_jev = None
        elif method == 'costs.update':
            costs = CostSchedule(**params)
            self.store.db.execute('INSERT INTO state VALUES(?,?) ON CONFLICT(key) DO UPDATE SET body=excluded.body', ('costs', json.dumps(asdict(costs))))
            self.store.db.commit()
            self.costs = costs
            self.latest_jev = None
        elif method == 'source.excel':
            self.disconnect()
            symbol = params.get('symbol', '')
            if not isinstance(symbol, str) or not symbol.startswith('WIN') or len(symbol)>24:
                raise ValueError('Informe o contrato WIN vigente')
            allowed = ('symbol', 'workbook', 'quote_sheet', 'quote_range', 'tape_sheet', 'tape_range')
            if set(params) != set(allowed) or any(not isinstance(v, str) or not v.strip() or len(v)>256 for v in params.values()):
                raise ValueError('Informe pasta, planilhas e intervalos válidos')
            self.collector = ExcelCollector(params)
            self.source_config = params
            self.settings.save_settings(dict(symbol=symbol, workbook=params['workbook'], sheet=params['quote_sheet'], cell_range=params['quote_range'], tape_sheet=params['tape_sheet'], tape_range=params['tape_range']))
            self.session.reset(symbol)
            self.session.mode = 'excel_observation'
        elif method == 'source.disconnect':
            self.disconnect()
            self.session.reset()
            self.session.mode = 'idle'
        elif method == 'source.replay':
            batch = read_csv_events(params['path'], symbol=params.get('symbol', ''))
            self.disconnect()
            self.session.reset(params.get('symbol') or (batch.events[0].symbol if batch.events else 'WIN_SIM'))
            self.session.ingest(batch, replay=True)
            self.store.record('replay_input', batch.to_dict())
        elif method == 'jev.configure':
            key, limit = params.get('api_key', ''), params.get('limit', 120)
            if not isinstance(key, str) or len(key)>4096 or type(limit) is not int or not 1 <= limit <= 10000:
                raise ValueError('Chave/orçamento inválidos')
            self.api_key, self.api_limit = key.strip(), limit
        elif method == 'jev.evaluate':
            self.request_jev()
        else:
            raise ValueError('Comando não autorizado ou desconhecido')
        return self.snapshot()

    def request_update_check(self):
        if self.updates['status'] == 'checking':
            return
        version = self.updates['current_version']
        self.updates = update_state(version, 'checking')
        def check():
            try:
                result = self.update_checker(version)
            except Exception:
                result = update_state(version, 'unavailable')
            self.update_results.put(result)
        threading.Thread(target=check, daemon=True).start()

    def request_jev(self):
        if not self.api_key or self.pending_jev or self.api_calls >= self.api_limit or time.monotonic()-self.api_last_at < 10:
            raise ValueError('Configure a chave, aguarde 10 segundos e confira o orçamento de chamadas')
        market = self.session.snapshot()
        allowed, reason = can_classify(market, now_ms=market['ts_ms'])
        if not allowed:
            raise ValueError(reason)
        state = jev_observation_state(market)
        questions = json.loads(resource_path('observer_questions.json').read_text(encoding='utf-8'))
        attach_candidates(state, questions, self.technical(market)['rows'])
        submitted_ms, submitted_monotonic = int(time.time()*1000), time.monotonic()
        envelope = dict(experiment_schema_version=1, call_id=str(uuid.uuid4()), state=state, questions=questions,
                        questions_sha256=hashlib.sha256(json.dumps(questions, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                        code_sha256=self.code_hash, policy_version='context-dimensions-v2', model_requested='jev-1.13.0',
                        submitted_at_ms=submitted_ms, clock_unit='unix_ms', latency_ms=None, api_cost_brl=None,
                        costs=asdict(self.costs), account=self.store.account().to_dict(),
                        flow_ts_ms=market.get('flow_ts_ms'), source_ts_ms=market['ts_ms'], source_generation=self.session.source_generation, account_revision=self.store.account().revision, mode=self.session.mode)
        self.store.record('jev_submitted', envelope)
        key = self.api_key
        self.pending_jev = True
        self.api_calls += 1
        self.api_last_at = time.monotonic()
        def evaluate():
            try:
                response = JevClient(api_key=key, timeout_seconds=3).evaluate(state, questions)
                self.results.put({'result': {**envelope, 'response': response, 'received_at_ms': int(time.time()*1000), 'latency_ms': (time.monotonic()-submitted_monotonic)*1000}})
            except Exception:
                self.results.put({'error': 'Falha na API JEV; confira a chave e a conexão', 'attempt': {**envelope, 'received_at_ms': int(time.time()*1000), 'latency_ms': (time.monotonic()-submitted_monotonic)*1000, 'status': 'FAILED_NO_VALID_RESPONSE'}})
        threading.Thread(target=evaluate, daemon=True).start()

    def tick(self):
        changed = False
        try:
            self.updates = self.update_results.get_nowait()
            changed = True
        except queue.Empty:
            pass
        if self.collector:
            try:
                value = self.collector.poll()
                if value and 'batch' in value:
                    batch = batch_from_wire(value['batch'])
                    self.session.ingest(batch)
                    self.store.record('market_batch', value['batch'])
                    self.source_error = None
                    changed = True
                elif value and 'error' in value:
                    raise ValueError(value['error'])
            except (ValueError, OSError, KeyError):
                self.source_error = 'Excel ocupado ou indisponível. Reconecte; houve interrupção na captura.'
                self.disconnect(clear_error=False)
                self.session.reset()
                self.session.mode = 'excel_observation'
                self.session.warnings = [self.source_error]
                changed = True
        try:
            value = self.results.get_nowait()
            self.pending_jev = False
            if 'result' in value:
                result = value['result']
                self.store.record('jev_experiment', {**result, 'accepted_current': self.accepts(result)})
                if self.accepts(result):
                    self.latest_jev = result
            else:
                self.source_error = value['error']
                self.store.record('jev_failed', value.get('attempt', {'status': 'FAILED_NO_VALID_RESPONSE'}))
            changed = True
        except queue.Empty:
            pass
        return changed

    def disconnect(self, clear_error=True):
        if self.collector:
            self.collector.close()
            self.collector = None
        self.latest_jev = None
        if clear_error:
            self.source_error = None

    def close(self):
        self.disconnect()
        self.store.close()
        self.settings.close()
        self.closed = True


def excel_worker():
    config = json.loads(sys.stdin.readline())['config']
    bridge = CombinedExcelBridge(**config)
    for line in sys.stdin:
        try:
            if json.loads(line).get('read'):
                value = {'batch': bridge.read().to_dict()}
            else:
                continue
        except Exception:
            value = {'error': 'Excel indisponível ou exportação inválida'}
        print(json.dumps(value, allow_nan=False), flush=True)


def main():
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--excel-worker', action='store_true')
    parser.add_argument('--data-dir')
    parser.add_argument('--diagnose', action='store_true')
    args = parser.parse_args()
    if args.excel_worker:
        excel_worker()
        return
    if args.diagnose:
        import platform
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            service = DecisionService(directory)
            try:
                snapshot = service.command('source.demo', {})
                print(json.dumps(dict(status='PASS', platform=platform.platform(), python=platform.python_version(),
                                      schema_version=snapshot['schema_version'], experimental=True, alternatives=len(snapshot['alternatives']),
                                      orders_enabled=False, financial_probability=snapshot['decision']['profit_probability'],
                                      code_sha256=service.code_hash), allow_nan=False), flush=True)
            finally:
                service.close()
        return
    service = DecisionService(args.data_dir)
    requests = queue.Queue()
    def read():
        for line in sys.stdin:
            requests.put(line)
        requests.put(None)
    threading.Thread(target=read, daemon=True).start()
    last_push = 0
    def emit(value):
        print(json.dumps(value, ensure_ascii=False, allow_nan=False), flush=True)
    try:
        while True:
            try:
                line = requests.get(timeout=.1)
                if line is None:
                    break
                request = {}
                try:
                    if len(line) > 65536:
                        raise ValueError('Mensagem muito grande')
                    request = json.loads(line, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Número inválido')))
                    if not isinstance(request, dict) or request.get('schema_version') != 1 or not isinstance(request.get('id'), str) or not 1 <= len(request['id']) <= 128:
                        raise ValueError('Versão/ID inválidos')
                    snapshot = service.command(request['method'], request.get('params', {}))
                    emit({'schema_version': 1, 'id': request['id'], 'result': snapshot})
                except (ValueError, KeyError, TypeError, ArithmeticError, OSError, sqlite3.Error):
                    emit({'schema_version': 1, 'id': request.get('id') if isinstance(request, dict) else None, 'error': 'Valores inválidos, estado mudou ou comando indisponível. Confira configuração, conta e fonte.'})
            except queue.Empty:
                pass
            changed = service.tick()
            if changed or time.monotonic()-last_push >= 1:
                emit({'schema_version': 1, 'event': 'snapshot', 'result': service.snapshot()})
                last_push = time.monotonic()
    except (BrokenPipeError, KeyboardInterrupt):
        pass
    finally:
        service.close()


if __name__ == '__main__':
    main()

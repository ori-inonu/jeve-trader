"""Versioned JSON-lines Python sidecar. Only the owner thread mutates state."""
from __future__ import annotations
import argparse
import hashlib
from dataclasses import asdict
from decimal import Decimal
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

from app_core import ObservationSession, DEFAULT_INPUTS, build_risk_study, can_classify
from app_store import resource_path, UserStore
from candidate_research import build_market_candidates, generate_candidate_scenario
from context_cycle import build_context, interpret_response
from credential_vault import WindowsCredentialVault
from capture_pilot import CapturePilot
from live_context import PilotBudget, ContextCadence, ContextAlert, DEFAULT_LIVE_SETTINGS, update_live_settings, relevant_projection
from decision_engine import AccountState, CostSchedule, MarketSnapshot, compare_plans, select_plan
from decision_store import DecisionStore
from jev_client import JevClient
from profit_bridge import CombinedExcelBridge, SourceBatch, MarketEvent, QuoteSnapshot, SourceHealth, RtdThrottleGuard, read_csv_events
from profit_ocr import capture_profit, profit_windows, validate_selection, OcrUnavailableError, runtime_status
from release_updates import check_for_updates, current_version, update_state, trusted_release_url
from multimarket_observer import MultimarketObserver

EXPERIMENT_RESOURCES = ('desktop_service.py', 'app_core.py', 'app_store.py', 'capital_example.py',
                        'decision_engine.py', 'decision_store.py', 'context_requests.py', 'candidate_engine.py',
                        'candidate_research.py', 'flow_engine.py', 'profit_bridge.py', 'recommendation_engine.py',
                        'jev_client.py', 'copilot.py', 'capital_planner.py', 'risk.py', 'risk_research.py',
                        'config.json', 'flow_rules.json', 'observer_questions.json')
EXPERIMENT_RESOURCES += ('live_context.py', 'credential_vault.py', 'context_cycle.py', 'context_identity.py', 'profit_ocr.py', 'profit_capture.cs', 'capture_pilot.py')
EXPERIMENT_RESOURCES += ('market_data_contract.py', 'public_crypto_feed.py', 'market_replay.py',
                        'multimarket_context.py', 'multimarket_economics.py', 'multimarket_observer.py')


def batch_from_wire(data):
    health = data['health']
    return SourceBatch(tuple(MarketEvent(x.get('id'), x['symbol'], x['ts_ms'], x['price_points'], x['quantity'], x['aggressor'], x.get('buyer_broker'),x.get('seller_broker')) for x in data['events']),
                       tuple(QuoteSnapshot(**x) for x in data['quotes']),
                       SourceHealth(**{k: health[k] for k in SourceHealth.__dataclass_fields__ if k in health}), tuple(data.get('warnings', [])),
                       tuple(data.get('books',[])),tuple(data.get('aggregates',[])),dict(data.get('capabilities',{})),dict(data.get('evidence',{})))


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
            if 'batch' in value or 'error' in value: self.pending_at = None
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
            self.next_read_at = self.pending_at + .25
        return None

    def close(self):
        if self.process.poll() is None:
            try:
                self._write({'close':True})
                self.process.wait(timeout=2)
            except (OSError, ValueError, subprocess.TimeoutExpired):
                self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        for stream in (self.process.stdin, self.process.stdout):
            if stream:
                stream.close()
        result = None
        while not self.responses.empty():
            value = self.responses.get_nowait()
            if 'rtd' in value: result = value['rtd']
        return result

    def control(self, value):
        self._write(value)


class DecisionService:
    def __init__(self, directory=None, *, update_checker=check_for_updates, credential_vault=None, client_factory=JevClient, multimarket_factory=MultimarketObserver):
        self.store = DecisionStore(directory)
        self.settings = UserStore(directory)
        self.pilot = CapturePilot(self.settings.directory)
        self.multimarket = multimarket_factory()
        self.session = ObservationSession()
        self.costs = CostSchedule()
        self.latest_jev = None
        self.api_key = ''
        self.credential_vault = credential_vault or (WindowsCredentialVault() if directory is None else None)
        self.jev_error = None
        if self.credential_vault:
            try:
                self.api_key = self.credential_vault.read()
            except OSError:
                self.jev_error = 'Credencial protegida indisponível; configure novamente'
        self.client_factory = client_factory
        self.engine_session_id = str(uuid.uuid4())
        self.credential_revision = 0
        # Permission to spend is deliberately not restored from disk.
        self.jev_enabled = False
        self.control_revision = 0
        self.pending_call_id = None
        self.context_settings = dict(DEFAULT_LIVE_SETTINGS)
        saved_context = self.store.db.execute("SELECT body FROM state WHERE key='live_context'").fetchone()
        if saved_context:
            saved = json.loads(saved_context[0])
            self.context_settings = update_live_settings(DEFAULT_LIVE_SETTINGS, {k:v for k,v in saved.items() if k != 'revision'})
            self.context_settings['revision'] = saved['revision']
        db_path = self.store.db.execute('PRAGMA database_list').fetchone()[2]
        self.budget = PilotBudget(db_path, daily=self.context_settings['daily_limit_usd'], total=self.context_settings['total_limit_usd'])
        self.cadence = ContextCadence()
        self.alert = ContextAlert()
        self.last_alert = None
        self.api_calls = 0
        self.api_limit = 10000
        self.api_last_at = 0.
        self.pending_jev = False
        self.results = queue.Queue()
        self.update_results = queue.Queue()
        self.discovery_results = queue.Queue()
        self.discovery = dict(status='idle', workbooks=[], scope='attached_excel_instance', cells_read=False)
        self.source_audit = dict(status='idle', tables=[])
        self.ocr = dict(enabled=False,status='off',windows=[],config={},runtime=runtime_status())
        self.ocr_results = queue.Queue()
        self.ocr_pending = False
        self.ocr_revision = 0
        self.ocr_next = 0.
        self.rtd_state = dict(status='unchanged', enabled=False, current_ms=None, previous_ms=None)
        rtd_recovery = self.store.db.execute("SELECT body FROM state WHERE key='rtd_recovery'").fetchone()
        if rtd_recovery:
            previous = json.loads(rtd_recovery[0])
            if previous.get('enabled') or previous.get('status')=='restore_unconfirmed':
                self.rtd_state = {**previous,'enabled':False,'status':'restore_unconfirmed'}
        self.update_checker = update_checker
        self.updates = update_state(current_version())
        self.collector = None
        self.source_error = None
        self.reconnect_enabled = False
        self.retry_at = 0.
        self.retry_delay = 1.
        self.sequence = 0
        self.closed = False
        self.last_batch = None
        self.context_valid = False
        self.code_hash = hashlib.sha256(b''.join(name.encode() + b'\0' + resource_path(name).read_bytes() for name in EXPERIMENT_RESOURCES)).hexdigest()
        ocr_manifest = resource_path('ocr_runtime/manifest.json')
        self.code_hash = hashlib.sha256(self.code_hash.encode() + (ocr_manifest.read_bytes() if ocr_manifest.is_file() else b'OCR_RUNTIME_UNAVAILABLE')).hexdigest()
        legacy_settings = self.settings.settings()
        self.source_config = {k: v for k, v in legacy_settings.items() if k in ('symbol', 'workbook', 'tape_sheet', 'tape_range')}
        self.source_config.update({new: legacy_settings[old] for old, new in (('sheet', 'quote_sheet'), ('cell_range', 'quote_range')) if old in legacy_settings})
        saved_profile = self.store.db.execute("SELECT body FROM state WHERE key='live_source'").fetchone()
        if saved_profile:
            profile = json.loads(saved_profile[0])
            self.source_config = profile['config']
            self.reconnect_enabled = profile['enabled']
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
        directional = dict(temperature=None, wait=None, selected='wait', candidate_key=None, geometry=None,
                           expires_at_ms=None, evaluated_at_ms=None, latency_ms=None, contextual=True, experimental=True, calibrated=False)
        if latest:
            interpretation = latest['interpretation']
            choice = interpretation['choice']
            scores = choice['raw']['probabilities']
            key = interpretation['selected_candidate_key']
            dimensions = interpretation['context_by_candidate'].get(key)
            candidate = next((c for c in latest['bundle']['candidates'] if c['candidate_key']==key), None)
            temperature = self.context_temperature(latest)
            directional.update(temperature=temperature, wait=scores['wait'],
                               selected=choice['selected'], candidate_key=key, geometry=candidate['geometry'] if candidate and temperature is not None else None,
                               expires_at_ms=latest['expires_at_ms'], evaluated_at_ms=latest['submitted_at_ms'], latency_ms=latest['latency_ms'])
        history = self.store.history(200)
        equity_history = []
        for event in reversed(history):
            if event['kind'] in ('account_reconciliation', 'account_after_fill'):
                equity_history.append({'ts_ms': event['ts_ms'], 'equity_brl': event['payload']['equity_brl']})
        equity_history.append({'ts_ms': account.asof_ms or int(time.time()*1000), 'equity_brl': account.equity_brl})
        self.sequence += 1
        capabilities = self.capabilities(market)
        self.pilot.observe(market, connected=self.collector is not None, caps=capabilities)
        return {'schema_version': 2, 'sequence': self.sequence, 'generated_at_ms': int(time.time()*1000),
                'market': market, 'account': account.to_dict(), 'costs': asdict(self.costs), 'decision': main,
                'alternatives': plans[1:], 'technical': technical, 'context': dimensions,
                'jev': {'configured': bool(self.api_key), 'calls': self.api_calls, 'limit': self.api_limit,
                        'enabled': self.jev_enabled, 'control_revision': self.control_revision,
                        'pending_call': self.pending_call_id,
                        'status': ('pending' if self.jev_enabled else 'draining') if self.pending_jev else ('enabled' if self.jev_enabled else 'off'),
                        'pending': self.pending_jev, 'current': latest is not None, 'model': 'jev-1.13.0', 'financial_probability': None},
                'directional': directional, 'context_settings': dict(self.context_settings),
                'context_by_candidate': latest['interpretation']['context_by_candidate'] if latest else {},
                'hypothesis_context': [dict(candidate_key=c['candidate_key'], family=c['family'], side=c['side'], aggressor_side=c['aggressor_side'],scenario_side=c['scenario_side'],literal_premise=c['literal_premise'],
                    dimensions=latest['interpretation']['context_by_candidate'][c['candidate_key']])
                    for c in latest['bundle']['candidates']+latest['bundle']['absorption_candidates']+latest['bundle']['exhaustion_candidates']] if latest else [],
                'budget': self.budget.snapshot(int(time.time()*1000)), 'jev_error': self.jev_error,
                'jev_retry_in_ms': max(0, self.cadence.retry_at_ms-int(time.time()*1000)),
                'alert': dict(episode=self.last_alert, active=bool(latest and self.last_alert
                    and self.last_alert.get('source_generation') == self.session.source_generation
                    and self.last_alert.get('engine_session_id') == self.engine_session_id
                    and self.last_alert.get('side')==({'buy_continuation':'buy','sell_continuation':'sell'}.get(directional['selected']))
                    and self.alert_conditions(latest) and self.context_settings['alerts_enabled'])),
                'source': {'error': self.source_error, 'excel_running': self.collector is not None, 'config': self.source_config,
                           'discovery': dict(self.discovery),
                           'audit': dict(self.source_audit), 'rtd': dict(self.rtd_state), 'ocr': dict(self.ocr),
                           'capabilities': capabilities, 'reconnect_enabled': self.reconnect_enabled,
                           'retry_in_ms': max(0, int((self.retry_at-time.monotonic())*1000)) if self.reconnect_enabled and not self.collector else None,
                           'observed_at_ms': market['evidence_coverage'].get('source_quality', {}).get('observed_at_ms')},
                'chart_points': list(self.session.chart),
                'equity_history': equity_history, 'history': [event for event in history if event['kind'].startswith('actual_manual') or event['kind'] == 'account_reconciliation'][:40],
                'updates': dict(self.updates), 'pilot': self.pilot.snapshot(),
                'multimarket': self.multimarket.snapshot(),
                'research': {'status': 'EMPIRICAL_VALIDATION_PENDING', 'logistic_baseline': 'offline CLI: scripts/run_decision_lab.py',
                             'profitdll': 'SDK_AUTHORIZED_REQUIRED', 'risk_catalog': ['fixed_lot', 'fixed_cash', 'initial_fraction', 'current_fraction', 'kelly', 'fractional_kelly', 'drawdown_kelly', 'volatility', 'optimal_f', 'fixed_ratio', 'paroli', 'partial_reinvest', 'pyramiding', 'martingale', 'dalembert', 'fibonacci', 'labouchere'],
                             'profit_target': None, 'drawdown_pause': None}, 'orders_enabled': False}

    def accepts(self, result):
        market = self.session.snapshot()
        now = int(time.time()*1000)
        current = self.technical(market)['rows']
        original = [c['geometry'] for c in result.get('bundle', {}).get('candidates', [])]
        fields = ('id', 'premise', 'hypothesis_version', 'entry_points', 'stop_points', 'target_points')
        same = all(any(all(str(row.get(k)) == str(old.get(k)) for k in fields) for row in current) for old in original)
        return (self.jev_enabled and result.get('control_revision') == self.control_revision
                and same and self.session.mode == 'excel_observation' and can_classify(market, now_ms=now)[0]
                and result.get('credential_revision') == self.credential_revision
                and result.get('parameter_revision') == self.context_settings['revision']
                and result.get('costs') == asdict(self.costs)
                and type(result.get('expires_at_ms')) is int and now <= result['expires_at_ms']
                and result.get('source_generation') == self.session.source_generation and result.get('account_revision') == self.store.account().revision
                and type(result.get('flow_ts_ms')) is int and 0 <= now-result['flow_ts_ms'] <= self.context_settings['validity_ms'])

    def capabilities(self, market):
        coverage, features = market['evidence_coverage'], market['computed_features']
        quote = market.get('last_quote')
        stamp = quote.get('ts_ms') if quote else None
        quote_fresh = type(stamp) is int and 0 <= int(time.time()*1000)-stamp <= self.context_settings['validity_ms']
        tape = bool(coverage.get('tape_fresh') and coverage.get('integrity_ok') and features.get('trade_count', 0))
        return dict(quote=quote is not None, quote_fresh=quote_fresh, tape=tape,
                    aggression=tape and features.get('unknown_aggressor_contracts') != features.get('total_contracts'),
                    price_depth=bool(coverage.get('book_fresh')), full_tape=coverage.get('source_quality', {}).get('full_tape') is True,
                    book_snapshot=bool(market.get('order_flow',{}).get('book')),
                    buyer_broker=bool(market.get('order_flow',{}).get('source_capabilities',{}).get('buyer_broker')),
                    seller_broker=bool(market.get('order_flow',{}).get('source_capabilities',{}).get('seller_broker')),
                    limitations=['Excel é captura parcial; não comprova continuidade.', 'Snapshots do livro não comprovam cancelamentos nem tape integral.'])

    def save_state(self, key, value):
        with self.store.db:
            self.store.db.execute('INSERT INTO state VALUES(?,?) ON CONFLICT(key) DO UPDATE SET body=excluded.body', (key, json.dumps(value, allow_nan=False)))

    def command(self, method, params):
        if not isinstance(params, dict):
            raise ValueError('Parâmetros inválidos')
        if method == 'snapshot':
            pass
        elif method == 'multimarket.start':
            if set(params) != {'duration_seconds'}:
                raise ValueError('Informe somente a duração explícita da coleta pública')
            duration = params['duration_seconds']
            if type(duration) is not int or not 1 <= duration <= 1800:
                raise ValueError('Duração deve ser inteira entre 1 e 1800 segundos')
            self.multimarket.start(duration_seconds=duration)
        elif method == 'multimarket.stop':
            if params: raise ValueError('Encerramento não aceita parâmetros')
            self.multimarket.stop()
        elif method == 'multimarket.synthetic':
            if params: raise ValueError('Fixture não aceita parâmetros de mercado')
            self.multimarket.synthetic()
        elif method == 'pilot.start':
            if params: raise ValueError('O piloto não aceita parâmetros de mercado')
            self.pilot.start(connected=self.collector is not None, mode=self.session.mode,
                             symbol=self.session.symbol, generation=self.session.source_generation)
        elif method == 'pilot.stop':
            if 'pilot_id' not in params or set(params) - {'pilot_id', 'visual', 'visual_session'}: raise ValueError('Informe o piloto e a medição visual opcional')
            self.pilot.stop(params['pilot_id'], visual=params.get('visual'), visual_session=params.get('visual_session','legacy'))
        elif method == 'pilot.checkpoint':
            if set(params) != {'pilot_id','visual','visual_session'}: raise ValueError('Informe o piloto e a sessão visual')
            self.pilot.checkpoint(params['pilot_id'], params['visual'], params['visual_session'])
        elif method == 'pilot.mark':
            if set(params) != {'pilot_id','scenario'}: raise ValueError('Informe somente piloto e cenário')
            self.pilot.mark(params['pilot_id'], params['scenario'])
        elif method == 'pilot.save':
            if set(params) != {'pilot_id'}: raise ValueError('Informe somente o piloto vigente')
            self.pilot.save(params['pilot_id'])
        elif method == 'source.discover':
            if self.discovery['status'] != 'checking':
                self.discovery = {**self.discovery, 'status':'checking', 'error':None}
                def discover():
                    try:
                        process = subprocess.run(own_command('--discover-excel'), capture_output=True, text=True, encoding='utf-8',
                            timeout=5, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
                        value = json.loads(process.stdout) if process.returncode == 0 else {'status':'unavailable', 'error':'Excel não encontrado ou ocupado; abra seu arquivo na mesma sessão.'}
                    except (OSError, ValueError, subprocess.TimeoutExpired):
                        value = {'status':'unavailable', 'error':'Excel ocupado ou indisponível; descoberta encerrada após 5 segundos.'}
                    self.discovery_results.put(value)
                threading.Thread(target=discover, daemon=True).start()
        elif method == 'updates.check':
            self.request_update_check()
        elif method == 'updates.open':
            if self.updates['status'] != 'available' or not trusted_release_url(self.updates['release_url']):
                raise ValueError('Nenhuma atualização verificada disponível')
            if not webbrowser.open(self.updates['release_url']):
                raise ValueError('Não foi possível abrir a página da atualização')
        elif method == 'source.demo':
            self.disconnect()
            self.reconnect_enabled = False
            fixture = generate_candidate_scenario()
            self.session.reset('WIN_SIM')
            self.session.mode = 'synthetic'
            self.session.clock_ms = fixture['now_ms']
            self.session.engine.set_source_quality(fixture['source_quality'])
            for event in fixture['events']:
                if event['type']=='trade':
                    if self.session.engine.add_trade(event)['accepted']:
                        self.session.chart.append((event['ts_ms'], float(event['price_points'])))
                elif self.session.engine.set_book(event)['accepted']:
                    book = {**event, 'market_ts_ms':event['ts_ms'], 'captured_at_ms':event['ts_ms'], 'kind':'synthetic_book_snapshot'}
                    self.session.last_book = book
                    self.session.book_history.append(book)
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
            symbol = params.get('symbol', '')
            import re
            if not isinstance(symbol, str) or re.fullmatch(r'WIN[FGHJKMNQUVXZ]\d{2}', symbol) is None:
                raise ValueError('Informe o contrato WIN vigente')
            required = {'symbol', 'workbook', 'quote_sheet', 'quote_range', 'tape_sheet', 'tape_range'}
            optional = {'book_sheet','book_range','vap_sheet','vap_range','window_mode','filters'}
            if not required <= set(params) or set(params)-required-optional or any(not isinstance(v, str) or len(v)>256 or (not v.strip() and k in ('symbol','workbook','quote_sheet','quote_range')) for k,v in params.items()):
                raise ValueError('Informe pasta, planilhas e intervalos válidos')
            from profit_bridge import _validate_range
            _validate_range(params['quote_range'])
            for kind in ('tape','book','vap'):
                if bool(params.get(kind+'_sheet')) != bool(params.get(kind+'_range')):
                    raise ValueError('Informe planilha e intervalo juntos: '+kind)
                if params.get(kind+'_sheet'): _validate_range(params[kind+'_range'])
            self.disconnect()
            self.source_config = params
            self.reconnect_enabled = True
            self.save_state('live_source', dict(config=params, enabled=True))
            self.retry_at, self.retry_delay = 0., 1.
            self.collector = ExcelCollector(params)
            self.settings.save_settings(dict(symbol=symbol, workbook=params['workbook'], sheet=params['quote_sheet'], cell_range=params['quote_range'], tape_sheet=params['tape_sheet'], tape_range=params['tape_range']))
            self.session.reset(symbol)
            self.session.mode = 'excel_observation'
        elif method in ('source.audit','source.rtd'):
            if not self.collector: raise ValueError('Conecte o perfil Excel primeiro')
            if method == 'source.rtd':
                if set(params) != {'enabled'} or type(params['enabled']) is not bool: raise ValueError('Informe enabled como booleano')
                self.collector.control({'throttle':params['enabled']})
            else:
                self.source_audit = dict(status='checking',tables=[])
                self.collector.control({'audit':True})
        elif method == 'source.ocr_windows':
            self.ocr['windows'] = profit_windows()
            self.ocr['runtime'] = runtime_status()
        elif method == 'source.ocr':
            if type(params.get('enabled')) is not bool or set(params)-{'enabled','selection'}:
                raise ValueError('Informe enabled e uma região selecionada')
            config = validate_selection(params.get('selection',{})) if params['enabled'] else {}
            runtime = runtime_status()
            self.ocr_revision += 1
            self.ocr = dict(enabled=params['enabled'],status=('ready' if runtime['available'] else 'unavailable') if params['enabled'] else 'off',
                            windows=self.ocr['windows'],config=config,runtime=runtime,
                            error=runtime['error'] if params['enabled'] else None)
        elif method == 'source.disconnect':
            self.disconnect()
            self.reconnect_enabled = False
            self.save_state('live_source', dict(config=self.source_config, enabled=False))
            self.session.reset()
            self.session.mode = 'idle'
        elif method == 'source.replay':
            batch = read_csv_events(params['path'], symbol=params.get('symbol', ''))
            self.disconnect()
            self.reconnect_enabled = False
            self.session.reset(params.get('symbol') or (batch.events[0].symbol if batch.events else 'WIN_SIM'))
            self.session.ingest(batch, replay=True)
            self.store.record('replay_input', batch.to_dict())
        elif method == 'jev.set_enabled':
            if set(params) != {'enabled'} or type(params['enabled']) is not bool:
                raise ValueError('Informe enabled como booleano')
            if params['enabled'] != self.jev_enabled:
                self.jev_enabled = params['enabled']
                self.control_revision += 1
                self.latest_jev = None
                self.last_alert = None
                self.alert.reset()
                self.cadence.last_projection = None
                self.cadence.retry_at_ms = 0
                self.cadence.retry_delay_ms = 3000
                self.jev_error = None
        elif method == 'jev.configure':
            key, limit = params.get('api_key', ''), params.get('limit', 10000)
            if not isinstance(key, str) or len(key)>4096 or type(limit) is not int or not 1 <= limit <= 10000:
                raise ValueError('Chave/orçamento inválidos')
            if self.credential_vault is None:
                raise ValueError('Credencial protegida indisponível neste ambiente isolado')
            if not key.strip():
                self.credential_vault.delete()
            else:
                self.credential_vault.write(key.strip())
            self.api_key, self.api_limit = key.strip(), limit
            self.credential_revision += 1
            self.jev_error = None
            self.latest_jev = None
            self.cadence.last_projection = None
        elif method == 'context.configure':
            configured = update_live_settings(self.context_settings, params)
            self.save_state('live_context', configured)
            self.context_settings = configured
            self.budget.daily = Decimal(configured['daily_limit_usd'])
            self.budget.total = Decimal(configured['total_limit_usd'])
            self.latest_jev = None
            self.alert.reset()
            self.last_alert = None
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
        if not self.jev_enabled:
            raise ValueError('JEV desligado; coleta e cálculos locais continuam ativos')
        if not self.api_key or self.pending_jev or self.api_calls >= self.api_limit:
            raise ValueError('Configure a chave e confira o limite de chamadas da sessão')
        market = self.session.snapshot()
        submitted_ms, submitted_monotonic = int(time.time()*1000), time.monotonic()
        allowed, reason = can_classify(market, now_ms=submitted_ms)
        if not allowed or self.session.mode != 'excel_observation':
            raise ValueError(reason)
        if not 0 <= submitted_ms-market['flow_ts_ms'] <= self.context_settings['validity_ms']:
            raise ValueError('Dado fora da validade configurada')
        rows = self.technical(market)['rows']
        projection = relevant_projection(market, rows, self.context_settings['revision'])
        if not self.cadence.start(projection, submitted_ms, self.context_settings['cadence_ms']):
            return False
        try:
            bundle = build_context(market, rows, engine_session_id=self.engine_session_id,
                                   market_session_id=self.engine_session_id+':'+str(self.session.source_generation),
                                   horizon_ms=self.context_settings['horizon_seconds']*1000)
            call_id = str(uuid.uuid4())
            self.budget.reserve(call_id, now_ms=submitted_ms)
        except Exception:
            self.cadence.finish()
            raise
        state, questions = bundle['state'], bundle['questions']
        envelope = dict(experiment_schema_version=2, call_id=call_id, state=state, questions=questions, bundle=bundle,
                        questions_sha256=bundle['question_set_hash'], parameter_revision=self.context_settings['revision'],
                        credential_revision=self.credential_revision,
                        control_revision=self.control_revision,
                        expires_at_ms=min(submitted_ms, market['flow_ts_ms'])+self.context_settings['validity_ms'],
                        code_sha256=self.code_hash, policy_version=bundle['question_version'], model_requested='jev-1.13.0',
                        submitted_at_ms=submitted_ms, clock_unit='unix_ms', latency_ms=None, api_cost_brl=None,
                        costs=asdict(self.costs), account=self.store.account().to_dict(),
                        flow_ts_ms=market.get('flow_ts_ms'), source_ts_ms=market['ts_ms'], source_generation=self.session.source_generation, account_revision=self.store.account().revision, mode=self.session.mode)
        try:
            self.store.record('jev_submitted', envelope)
        except sqlite3.Error:
            self.cadence.finish()
            raise
        key = self.api_key
        self.jev_error = None
        self.pending_jev = True
        self.pending_call_id = call_id
        self.api_calls += 1
        self.api_last_at = time.monotonic()
        def evaluate():
            try:
                client = self.client_factory(api_key=key, timeout_seconds=3)
                # No retries in the HTTP adapter. A request already dispatched
                # may finish after OFF; its control revision cannot become live.
                if not self.jev_enabled or envelope['control_revision'] != self.control_revision:
                    self.results.put({'cancelled': envelope})
                    return
                response = client.evaluate(state, questions)
                self.results.put({'result': {**envelope, 'response': response, 'received_at_ms': int(time.time()*1000), 'latency_ms': (time.monotonic()-submitted_monotonic)*1000}})
            except Exception:
                self.results.put({'error': 'Falha na API JEV; confira a chave e a conexão', 'attempt': {**envelope, 'received_at_ms': int(time.time()*1000), 'latency_ms': (time.monotonic()-submitted_monotonic)*1000, 'status': 'FAILED_NO_VALID_RESPONSE'}})
        threading.Thread(target=evaluate, daemon=True).start()
        return True

    @staticmethod
    def context_temperature(result):
        interpretation = result['interpretation']
        scores = interpretation['choice']['raw']['probabilities']
        dimension = interpretation['context_by_candidate'].get(interpretation['selected_candidate_key'])
        selected = interpretation['choice']['selected']
        available = bool(dimension and selected != 'wait' and not interpretation['choice']['exact_tie']
                         and dimension['support'] >= .7 and dimension['contradiction'] <= .3 and dimension['insufficient'] <= .3)
        return 100*(scores['buy_continuation']-scores['sell_continuation']) if available else None

    def alert_conditions(self, result):
        interpretation = result['interpretation']
        scores = interpretation['choice']['raw']['probabilities']
        dimension = interpretation['context_by_candidate'].get(interpretation['selected_candidate_key'])
        selected = interpretation['choice']['selected']
        candidate = next((c for c in result['bundle']['candidates'] if c['candidate_key']==interpretation['selected_candidate_key']), None)
        account = self.store.account()
        admissible = bool(candidate and self.costs.verified and account.asof_ms > 0 and any(
            plan['quantity'] == 1 for plan in compare_plans([candidate['geometry']], account, self.costs)))
        return bool(admissible and dimension and selected != 'wait' and not interpretation['choice']['exact_tie']
                    and dimension['support'] >= .7 and dimension['contradiction'] <= .3 and dimension['insufficient'] <= .3
                    and scores['wait'] <= .2 and abs(100*(scores['buy_continuation']-scores['sell_continuation'])) >= self.context_settings['alert_threshold']
                    and self.capabilities(self.session.snapshot())['quote_fresh'])

    def tick(self):
        changed = self.multimarket.poll()
        try:
            revision,value = self.ocr_results.get_nowait()
            self.ocr_pending = False
            if self.ocr['enabled'] and revision == self.ocr_revision:
                self.ocr.update(value)
                if value['status']=='unavailable': self.ocr_next=time.monotonic()+1
                changed = True
        except queue.Empty: pass
        if self.ocr['enabled'] and self.ocr['runtime']['available'] and not self.ocr_pending and time.monotonic()>=self.ocr_next:
            self.ocr_pending=True
            self.ocr_next=time.monotonic()+.25
            revision,config=self.ocr_revision,dict(self.ocr['config'])
            def read_ocr():
                try: value=dict(status='partial',observation=capture_profit(config),error=None)
                except OcrUnavailableError as error:
                    value=dict(status='unavailable',error=str(error),observation=None)
                except Exception:
                    value=dict(status='unavailable',error='Captura OCR indisponível. Confira a janela Profit, região e módulo OCR local.',observation=None)
                self.ocr_results.put((revision,value))
            threading.Thread(target=read_ocr,daemon=True).start()
        try:
            self.discovery = {**self.discovery, **self.discovery_results.get_nowait()}
            changed = True
        except queue.Empty:
            pass
        try:
            self.updates = self.update_results.get_nowait()
            changed = True
        except queue.Empty:
            pass
        if self.reconnect_enabled and not self.collector and time.monotonic() >= self.retry_at:
            try:
                self.collector = ExcelCollector(self.source_config)
                self.session.reset(self.source_config['symbol'])
                self.alert.reset()
                self.last_alert = None
                self.cadence.last_projection = None
                self.session.mode = 'excel_observation'
                self.last_batch = None
            except (ValueError, OSError):
                self.source_error = 'Não foi possível iniciar o coletor Excel; nova tentativa automática.'
                self.retry_at = time.monotonic()+self.retry_delay
                self.retry_delay = min(15., self.retry_delay*2)
            changed = True
        if self.collector:
            try:
                value = self.collector.poll()
                if value and 'batch' in value:
                    batch = batch_from_wire(value['batch'])
                    self.session.ingest(batch)
                    # Journal changed data only. Repeated COM polling timestamps
                    # are not a new market event or a continuity proof.
                    content = {k:value['batch'].get(k) for k in ('events', 'quotes', 'warnings','aggregates','capabilities')}
                    content['books'] = [{k:v for k,v in book.items() if k!='captured_at_ms'} for book in value['batch'].get('books',[])]
                    signature = json.dumps(content, sort_keys=True)
                    if signature != self.last_batch:
                        self.store.record('market_batch', value['batch'])
                        self.last_batch = signature
                    self.source_error = None
                    self.retry_delay = 1.
                    changed = True
                elif value and 'error' in value:
                    raise ValueError(value['error'])
                elif value and 'rtd' in value:
                    self.rtd_state = {**value['rtd'],'enabled':value['rtd'].get('status')=='changed'}
                    self.save_state('rtd_recovery',self.rtd_state)
                    changed = True
                elif value and 'audit' in value:
                    self.source_audit = value['audit']
                    if self.source_audit.get('rtd_observed'): self.rtd_state.update(current_ms=self.source_audit['rtd_observed']['current_ms'])
                    changed = True
            except (ValueError, OSError, KeyError):
                self.source_error = 'Excel ocupado ou indisponível. Reconecte; houve interrupção na captura.'
                self.disconnect(clear_error=False)
                self.session.reset()
                self.session.mode = 'excel_observation'
                self.session.warnings = [self.source_error]
                self.retry_at = time.monotonic()+self.retry_delay
                self.retry_delay = min(15., self.retry_delay*2)
                changed = True
        try:
            value = self.results.get_nowait()
            self.pending_jev = False
            self.pending_call_id = None
            self.cadence.finish()
            attempt = value.get('result', value.get('attempt', value.get('cancelled', {})))
            self.pilot.record_jev_attempt(attempt, 'cancelled' if 'cancelled' in value else 'response_received' if 'result' in value else 'failed')
            controlled = self.jev_enabled and attempt.get('control_revision') == self.control_revision
            if 'cancelled' in value:
                self.budget.settle(attempt['call_id'], dict(input_tokens=0, output_tokens=0))
                self.store.record('jev_cancelled_before_dispatch', attempt)
            elif 'result' in value:
                result = value['result']
                try:
                    # Consumption is independent of acceptance and OFF.
                    self.budget.settle(result['call_id'], result['response']['usage'])
                    result['interpretation'] = interpret_response(result['bundle'], result['response'])
                    if controlled:
                        self.cadence.finish(success=True)
                    accepted = self.accepts(result)
                    self.store.record('jev_experiment', {**result, 'accepted_current': accepted})
                    if accepted:
                        self.latest_jev = result
                        scores = result['interpretation']['choice']['raw']['probabilities']
                        episode = self.alert.update(self.context_temperature(result),
                            valid=True, geometry=self.alert_conditions(result), now_ms=int(time.time()*1000),
                            threshold=self.context_settings['alert_threshold'], rearm=self.context_settings['alert_rearm'],
                            cooldown_ms=self.context_settings['alert_cooldown_ms'])
                        if episode and self.context_settings['alerts_enabled']:
                            self.last_alert = {**episode, 'candidate_key':result['interpretation']['selected_candidate_key'],
                                               'source_generation':self.session.source_generation, 'engine_session_id':self.engine_session_id}
                            self.store.record('context_alert', self.last_alert)
                except (ValueError, KeyError, TypeError):
                    if controlled:
                        self.cadence.fail(int(time.time()*1000))
                        self.jev_error = 'Resposta ou uso inválido; reserva de custo mantida quando desconhecida.'
                    self.store.record('jev_failed', {**result, 'status':'INVALID_RESPONSE'})
            else:
                if controlled:
                    self.cadence.fail(int(time.time()*1000))
                    self.jev_error = value['error']
                self.store.record('jev_failed', value.get('attempt', {'status': 'FAILED_NO_VALID_RESPONSE'}))
            changed = True
        except queue.Empty:
            pass
        if self.jev_enabled and self.context_settings['automatic'] and self.api_key and not self.pending_jev and self.session.mode == 'excel_observation':
            try:
                changed = self.request_jev() or changed
            except ValueError as error:
                if 'Orçamento' in str(error):
                    self.jev_error = str(error)
        valid = bool(self.latest_jev and self.accepts(self.latest_jev))
        if self.context_valid != valid:
            self.context_valid, changed = valid, True
        return changed

    def disconnect(self, clear_error=True):
        if self.collector:
            restored = self.collector.close()
            if isinstance(restored,dict): self.rtd_state = {**restored,'enabled':False}
            elif self.rtd_state.get('enabled'):
                self.rtd_state.update(status='restore_unconfirmed',enabled=False)
            self.save_state('rtd_recovery',self.rtd_state)
            self.collector = None
        self.latest_jev = None
        self.alert.reset()
        self.last_alert = None
        self.cadence.last_projection = None
        if clear_error:
            self.source_error = None

    def close(self):
        self.multimarket.stop()
        self.pilot.close()
        self.ocr['enabled']=False
        self.ocr_revision+=1
        self.disconnect()
        self.budget.close()
        self.store.close()
        self.settings.close()
        self.closed = True


def excel_worker():
    config = json.loads(sys.stdin.readline())['config']
    bridge = CombinedExcelBridge(**config)
    throttle = RtdThrottleGuard()
    try:
        for line in sys.stdin:
            try:
                command = json.loads(line)
                if command.get('close'): break
                if command.get('read'): value = {'batch':bridge.read().to_dict()}
                elif command.get('audit'): value = {'audit':{**bridge.audit(), 'rtd_observed':throttle.observe()}}
                elif 'throttle' in command: value = {'rtd':throttle.enable() if command['throttle'] else throttle.restore()}
                else: continue
            except Exception:
                value = {'error':'Excel indisponível ou exportação inválida; confira o perfil selecionado'}
            print(json.dumps(value,allow_nan=False),flush=True)
    finally:
        try: value = {'rtd':throttle.restore()}
        except ValueError: value = {'rtd':dict(status='restore_unconfirmed',previous_ms=throttle.previous,restored=False)}
        print(json.dumps(value,allow_nan=False),flush=True)


def main():
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--excel-worker', action='store_true')
    parser.add_argument('--discover-excel', action='store_true')
    parser.add_argument('--data-dir')
    parser.add_argument('--diagnose', action='store_true')
    args = parser.parse_args()
    if args.discover_excel:
        from profit_bridge import discover_open_excel
        try:
            print(json.dumps({'status':'ready', **discover_open_excel()}, ensure_ascii=False))
        except ValueError:
            print(json.dumps({'status':'unavailable', 'error':'Excel não encontrado ou ocupado; abra seu arquivo na mesma sessão.'}))
        return
    if args.excel_worker:
        excel_worker()
        return
    if args.diagnose:
        import platform
        import tempfile
        from profit_ocr import diagnose_runtime
        ocr_runtime = runtime_status()
        ocr_diagnostic = diagnose_runtime() if ocr_runtime['available'] else dict(status='UNAVAILABLE', real_profit_tested=False)
        with tempfile.TemporaryDirectory() as directory:
            service = DecisionService(directory)
            try:
                snapshot = service.command('source.demo', {})
                print(json.dumps(dict(status='PASS', platform=platform.platform(), python=platform.python_version(),
                                      schema_version=snapshot['schema_version'], experimental=True, alternatives=len(snapshot['alternatives']),
                                      orders_enabled=False, financial_probability=snapshot['decision']['profit_probability'],
                                      code_sha256=service.code_hash, ocr_runtime=ocr_runtime, ocr_diagnostic=ocr_diagnostic), allow_nan=False), flush=True)
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
    pending_publish = False
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
                    if not isinstance(request, dict) or request.get('schema_version') not in (1, 2) or not isinstance(request.get('id'), str) or not 1 <= len(request['id']) <= 128:
                        raise ValueError('Versão/ID inválidos')
                    snapshot = service.command(request['method'], request.get('params', {}))
                    emit({'schema_version': request['schema_version'], 'id': request['id'], 'result': snapshot})
                except (ValueError, KeyError, TypeError, ArithmeticError, OSError, sqlite3.Error):
                    emit({'schema_version': 1, 'id': request.get('id') if isinstance(request, dict) else None, 'error': 'Valores inválidos, estado mudou ou comando indisponível. Confira configuração, conta e fonte.'})
            except queue.Empty:
                pass
            pending_publish = service.tick() or pending_publish
            if time.monotonic()-last_push >= .1 and (pending_publish or time.monotonic()-last_push >= 1):
                emit({'schema_version': 2, 'event': 'snapshot', 'result': service.snapshot()})
                last_push = time.monotonic()
                pending_publish = False
    except (BrokenPipeError, KeyboardInterrupt):
        pass
    finally:
        service.close()


if __name__ == '__main__':
    main()

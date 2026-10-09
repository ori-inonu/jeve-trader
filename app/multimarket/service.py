"""Single-owner multi-market coordinator; network workers never mutate domain state."""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, is_dataclass
from pathlib import Path
import hashlib
import json
from decimal import Decimal
from itertools import islice
import queue
import threading
import time


def process_rss_bytes():
    """Current process working set on Windows; unsupported hosts remain unknown."""
    import sys
    if sys.platform != 'win32':
        return None
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)]+[(name, ctypes.c_size_t) for name in
            ('peak', 'working', 'paged_peak', 'paged', 'nonpaged_peak', 'nonpaged', 'pagefile', 'pagefile_peak')]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    return counters.working if psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb) else None

from .contracts import EvaluationIdentity, EventEnvelope, Registry, SystemClock
from .market_state import MarketState
from .accounts import AccountLedger
from .scheduler import ContextScheduler, build_questions
from .journal import Journal


def wire(value):
    if hasattr(value, 'to_wire'):
        return value.to_wire()
    return asdict(value) if is_dataclass(value) else value


class MultimarketService:
    def __init__(self, data_dir, *, clock=None, adapters=None):
        self.clock = clock or SystemClock()
        self.directory = Path(data_dir) / 'multimarket'
        self.directory.mkdir(parents=True, exist_ok=True)
        self.registry = Registry(clock=self.clock)
        self.accounts = AccountLedger(self.directory / 'accounts.sqlite3', clock=self.clock)
        self.journal = Journal(self.directory / 'evidence.sqlite3')
        self.scheduler = ContextScheduler(dict(max_pending=8, min_interval_ms=2000,
            timeout_ms=10000, validity_ms=2000, model='jev-1.13.0', question_version='mm-context-v1'), clock=self.clock)
        self.scheduler.set_enabled(False)
        self.adapters = dict(adapters) if adapters is not None else self._public_adapters()
        self.states = {}
        self.statuses = {}
        self.costs = {}
        self.account_ids = {}
        self.context = None
        self.sequence = 0
        self.closed = False
        self.discovery_pending = set()
        self.discovery_generation = {}
        self.discovery_connect = {}
        self.discovery_results = queue.Queue(maxsize=8)
        self.jev_results = queue.Queue(maxsize=8)
        self.recording = False
        self.recording_workspace = None
        self.recording_reason = 'Gravação desligada; licença de retenção da fonte não confirmada'
        self._jev_executor = self._reserve = self._settle = self._available = None
        self._jev_revision = None
        self._inflight = None
        self.metrics = dict(events=0, duplicates=0, rejected=0, overflow=0,
            process_p95_ms=None, market_lag_ms=None, rss_bytes=None, gpu_bytes=None, jev_latency_ms=None)
        self.timings = deque(maxlen=400)
        self._last_memory_ns = 0

    def _public_adapters(self):
        from .adapters import PublicSpotAdapter
        from .network import BinancePublicTransport
        return {'binance_public_spot': PublicSpotAdapter(BinancePublicTransport(), clock=self.clock)}

    def configure_jev(self, executor, reserve, settle, available):
        """Callbacks share the existing credential vault/budget, never copy credentials."""
        self._jev_executor, self._reserve, self._settle, self._available = executor, reserve, settle, available

    def _selected(self):
        return self.registry.snapshot().get('selected_workspace_id')

    def _workspace(self, params):
        workspace_id = params.get('workspace_id') or self._selected()
        if not workspace_id or workspace_id not in self.states:
            raise ValueError('Selecione um workspace conectado')
        return self.registry.get_workspace(workspace_id)

    def _clear_context(self):
        self.context = None

    def _identity(self, workspace_id):
        workspace = self.registry.get_workspace(workspace_id)
        state = self.states[workspace_id].snapshot()
        source = self.registry.get_source(workspace.source_id)
        spec = self.registry.get_instrument(workspace.instrument_id)
        account_id = self.account_ids.get(workspace_id, workspace.account_id)
        account = self.accounts.view(account_id) if account_id else None
        features = state['features']
        trade_receipts = [t.get('received_monotonic_ns', 0) for t in state.get('recent_trades', [])]
        received = max(trade_receipts, default=0)
        quote = state.get('quote') or {}
        # Never renew the origin timestamp when a projection is republished.
        received = min(received, quote.get('received_monotonic_ns', received)) if received else 0
        return EvaluationIdentity(workspace_id=workspace_id, instrument_id=spec.instrument_id,
            source_id=source.source_id, epoch=state['epoch'], metadata_version=spec.metadata_version,
            feature_version=str(features['version']), question_version='mm-context-v1',
            cost_revision=self.costs.get(workspace_id, {}).get('revision', 0),
            account_id=account_id, account_revision=account['revision'] if account else 0,
            selection_revision=self.registry.selection_revision,
            event_range=features.get('event_range'), received_monotonic_ns=received)

    def _discover(self, params, connect):
        source_id = params.get('source_id', 'binance_public_spot')
        symbol = params.get('symbol', 'BTCUSDT')
        if source_id not in self.adapters or symbol != 'BTCUSDT':
            raise ValueError('Piloto disponível apenas para BTCUSDT spot público')
        if source_id in self.discovery_pending:
            self.discovery_connect[source_id] = self.discovery_connect.get(source_id, False) or connect
            return
        adapter = self.adapters[source_id]
        # One active stream per configured adapter; repeated connect is idempotent.
        for workspace_id in self.states:
            workspace = self.registry.get_workspace(workspace_id)
            if workspace.source_id == source_id and self.statuses[workspace_id]['status'] == 'live':
                self.registry.select(workspace_id)
                return
        self.discovery_pending.add(source_id)
        generation = self.discovery_generation.get(source_id, 0)+1
        self.discovery_generation[source_id] = generation
        self.discovery_connect[source_id] = connect
        self.statuses[source_id] = dict(status='connecting', reason='Descobrindo metadata pública')
        def discover():
            try:
                spec = adapter.discover(symbol)
                value = dict(source_id=source_id, spec=spec, generation=generation)
            except Exception:
                value = dict(source_id=source_id, generation=generation, error='Descoberta pública indisponível; confira conexão e disponibilidade regional')
            if not self.closed:
                try:
                    self.discovery_results.put_nowait(value)
                except queue.Full:
                    pass  # Cancelled generations cannot grow the owner queue.
        threading.Thread(target=discover, daemon=True, name='multimarket-discovery').start()

    def command(self, method, params):
        if not isinstance(params, dict):
            raise ValueError('Parâmetros inválidos')
        if not method.startswith('multimarket.'):
            raise ValueError('Comando multimercado inválido')
        name = method[len('multimarket.'):]
        if name == 'snapshot' or name == 'metrics':
            pass
        elif name in ('discover', 'connect'):
            self._discover(params, name == 'connect')
        elif name == 'select':
            self.registry.select(params['workspace_id'])
            self._clear_context()
        elif name == 'disconnect':
            if not params.get('workspace_id') and not self._selected():
                source_id = params.get('source_id', 'binance_public_spot')
                self.discovery_generation[source_id] = self.discovery_generation.get(source_id, 0)+1
                self.discovery_pending.discard(source_id)
                self.statuses[source_id] = dict(status='disconnected', reason='Descoberta cancelada')
                self.sequence += 1
                return self.snapshot()
            workspace = self._workspace(params)
            self.discovery_generation[workspace.source_id] = self.discovery_generation.get(workspace.source_id, 0)+1
            self.discovery_pending.discard(workspace.source_id)
            self.adapters[workspace.source_id].stop()
            self.states[workspace.workspace_id].invalidate('disconnected')
            self.statuses[workspace.workspace_id] = dict(status='disconnected', reason='Fonte desconectada')
            self._clear_context()
        elif name == 'account.reconcile':
            workspace = self._workspace(params)
            account = dict(params['account'])
            account['received_monotonic_ns'] = self.clock.monotonic_ns()
            result = self.accounts.reconcile(account)
            if result['status'] == 'rejected':
                raise ValueError('Snapshot de conta rejeitado: '+result['reason'])
            self.account_ids[workspace.workspace_id] = account['account_id']
            self._clear_context()
        elif name == 'account.fill':
            workspace = self._workspace(params)
            fill = dict(params['fill'])
            if fill['account_id'] != self.account_ids.get(workspace.workspace_id):
                raise ValueError('Fill de outra conta')
            fill['received_monotonic_ns'] = self.clock.monotonic_ns()
            self.accounts.ingest_fill(fill)
            self._clear_context()
        elif name == 'costs.update':
            from .contracts import decimal_text
            workspace = self._workspace(params)
            spec = self.registry.get_instrument(workspace.instrument_id)
            costs = dict(params['costs'])
            if costs.get('currency') != spec.settlement_currency or type(costs.get('verified')) is not bool:
                raise ValueError('Moeda ou verificação de custos inválida')
            for key in ('fee_rate', 'slippage'):
                if costs.get(key) is not None:
                    if not isinstance(costs[key], str):
                        raise ValueError('Custos devem ser strings decimais')
                    costs[key] = decimal_text(Decimal(costs[key]))
                    if costs[key].startswith('-'):
                        raise ValueError('Custo negativo')
            revision = self.costs.get(workspace.workspace_id, {}).get('revision', 0)+1
            self.costs[workspace.workspace_id] = {k: costs.get(k) for k in ('currency', 'verified', 'fee_rate', 'slippage')}
            self.costs[workspace.workspace_id]['revision'] = revision
            self._clear_context()
        elif name == 'jev.set_enabled':
            if type(params.get('enabled')) is not bool:
                raise ValueError('Controle JEV inválido')
            if params['enabled'] and (not self._available or not self._available()[0]):
                raise ValueError('Configure a chave JEV no laboratório legado')
            self.scheduler.set_enabled(params['enabled'])
            self._clear_context()
        elif name == 'recording.set':
            if type(params.get('enabled')) is not bool:
                raise ValueError('Controle de gravação inválido')
            workspace = self._workspace(params)
            source = self.registry.get_source(workspace.source_id)
            self.recording = bool(params['enabled'] and source.retention == 'allowed')
            self.recording_workspace = workspace.workspace_id if self.recording else None
            self.recording_reason = 'Gravação autorizada' if self.recording else 'Retenção não autorizada pela política da fonte'
        elif name == 'replay':
            workspace = self._workspace(params)
            source = self.registry.get_source(workspace.source_id)
            if source.export != 'allowed':
                raise ValueError('Exportação/replay não autorizado pela fonte')
            # Replay summaries are explicitly labelled and cannot replace live state.
            if params.get('namespace', workspace.workspace_id) != workspace.workspace_id:
                raise ValueError('Replay de outro workspace não autorizado')
            rows = list(islice(self.journal.replay(workspace.workspace_id), 2000))
            result = self.snapshot()
            result['replay'] = dict(mode='replay', events=rows, live=False)
            return result
        else:
            raise ValueError('Comando indisponível; ordens desabilitadas')
        self.sequence += 1
        return self.snapshot()

    def _admit_discovery(self, value):
        source_id = value['source_id']
        if value.get('generation') != self.discovery_generation.get(source_id):
            return
        connect = self.discovery_connect.pop(source_id, False)
        self.discovery_pending.discard(source_id)
        if 'error' in value:
            self.statuses[source_id] = dict(status='error', reason=value['error'])
            return
        adapter = self.adapters[source_id]
        spec, caps = value['spec'], adapter.capabilities()
        self.registry.register_source(caps)
        self.registry.register_instrument(spec)
        workspace_id = f'{source_id}:{spec.instrument_id}'
        if workspace_id not in self.states:
            workspace = self.registry.open_workspace(source_id=source_id, instrument_id=spec.instrument_id, workspace_id=workspace_id)
            self.states[workspace_id] = MarketState(spec, caps, clock=self.clock, workspace_id=workspace_id)
        self.registry.select(workspace_id)
        epoch = self.states[workspace_id].snapshot()['epoch']
        self.statuses[workspace_id] = dict(status='connecting' if connect else 'discovered', reason='Metadata verificada; aguardando observações')
        self.statuses.pop(source_id, None)
        if connect:
            try:
                if adapter.start(workspace_id=workspace_id, epoch=epoch, metadata_version=spec.metadata_version) is False:
                    self.statuses[workspace_id] = dict(status='error', reason='Conexão anterior ainda encerrando; reconecte a fonte')
            except (ValueError, RuntimeError):
                self.statuses[workspace_id] = dict(status='error', reason='Conexão anterior ainda encerrando; reconecte a fonte')
        self._clear_context()

    def _ingest(self, workspace_id, item):
        workspace = self.registry.get_workspace(workspace_id)
        state = self.states[workspace_id]
        if isinstance(item, dict):
            if item.get('kind') == 'metadata':
                spec = item['spec']
                if item['epoch'] < state.snapshot()['epoch']:
                    self.metrics['rejected'] += 1
                    return
                self.registry.register_instrument(spec)
                caps = self.registry.get_source(workspace.source_id)
                self.states[workspace_id] = MarketState(spec, caps, clock=self.clock,
                    workspace_id=workspace_id, epoch=item['epoch'])
                self._clear_context()
            elif item.get('kind') == 'source_status':
                previous = self.statuses.get(workspace_id, {}).get('status')
                self.statuses[workspace_id] = dict(status=item['status'], reason=item.get('reason'))
                if item['status'] in ('retrying', 'error', 'disconnected'):
                    if previous not in ('retrying', 'error', 'disconnected'):
                        state.invalidate(item.get('reason') or item['status'])
                    self._clear_context()
                    if 'overflow' in (item.get('reason') or ''):
                        self.metrics['overflow'] += 1
            elif item.get('kind') == 'diagnostic' and item.get('code') == 'message_rejected':
                self.metrics['rejected'] += 1
            return
        if not isinstance(item, EventEnvelope):
            self.metrics['rejected'] += 1
            return
        result = state.ingest(item)
        if result.duplicate:
            self.metrics['duplicates'] += 1
        elif result.applied:
            self.metrics['events'] += 1
            if item.market_ts_ms is not None:
                self.metrics['market_lag_ms'] = max(0, item.received_at_ms-item.market_ts_ms)
            if self.recording and self.recording_workspace == workspace_id:
                source = self.registry.get_source(workspace.source_id)
                self.journal.append('market_event', workspace_id, item.event_id, wire(item),
                    policy=dict(retention=source.retention, export=source.export))
        else:
            self.metrics['rejected'] += 1
        if result.resync_required:
            self._clear_context()
            adapter = self.adapters.get(workspace.source_id)
            if adapter and hasattr(adapter, 'request_resync'):
                adapter.request_resync()

    def _journal_context(self, kind, request, payload):
        identity = request['identity']
        if not self.recording or self.recording_workspace != identity.workspace_id:
            return
        source = self.registry.get_source(identity.source_id)
        self.journal.append(kind, identity.workspace_id, request['call_id']+':'+kind,
            dict(identity=wire(identity), call_id=request['call_id'], model=request['model'],
                question_version=request['question_version'], observed_at_ms=self.clock.wall_ms(),
                observed_monotonic_ns=self.clock.monotonic_ns(), **payload),
            policy=dict(retention=source.retention, export=source.export))

    def _context_tick(self):
        selected = self._selected()
        if self._available:
            available, revision = self._available()
            if revision != self._jev_revision:
                self._jev_revision = revision
                self._clear_context()
                if self._inflight:
                    self.scheduler.set_enabled(False)
        while not self.jev_results.empty():
            value = self.jev_results.get_nowait()
            identity = self._identity(selected) if selected else None
            if 'response' in value:
                try:
                    self._settle(value['call_id'], value['response']['usage'])
                except (ValueError, KeyError, TypeError):
                    value = dict(call_id=value['call_id'], error='Uso JEV inválido; reserva mantida')
            response = value.get('response', {'error': value.get('error', 'JEV indisponível')})
            result = self.scheduler.complete(value['call_id'], response, identity)
            if 'request' in value:
                self._journal_context('context_result', value['request'], dict(
                    status=result['status'], accepted_current=result.get('accepted', False),
                    reason=result.get('reason'), answers=result.get('answers'), usage=result.get('usage'),
                    latency_ms=value.get('latency_ms'), financial_probability=None))
            self._inflight = None
            self.metrics['jev_latency_ms'] = value.get('latency_ms')
            if result.get('accepted'):
                self.context = dict(status='current', model='jev-1.13.0', questions_version='mm-context-v1',
                    origin_monotonic_ns=result['origin_monotonic_ns'], answers=result['answers'],
                    identity=wire(result['identity']), financial_probability=None)
            else:
                self.context = None
        if not selected or not self.scheduler.snapshot()['enabled']:
            return
        state = self.states[selected].snapshot()
        if any(state['health'][domain]['status'] != 'live' for domain in ('quote', 'trades')):
            self._clear_context()
            return
        if self._inflight:
            return
        identity = self._identity(selected)
        feature_key = hashlib.sha256(json.dumps(state['features'], sort_keys=True, allow_nan=False).encode()).hexdigest()
        self.scheduler.offer(identity, build_questions(), feature_key, priority=0)
        request = self.scheduler.take()
        if not request:
            return
        workspace = self.registry.get_workspace(selected)
        source = self.registry.get_source(workspace.source_id)
        # Outbound derived market evidence also needs an affirmative source policy.
        if source.export != 'allowed':
            self.scheduler.complete(request['call_id'], {'error': 'Política de processamento/exportação da fonte não confirmada'}, identity)
            return
        if not self._available or not self._available()[0] or not self._jev_executor:
            self.scheduler.complete(request['call_id'], {'error': 'JEV indisponível'}, identity)
            return
        try:
            self._reserve(request['call_id'])
        except ValueError:
            self.scheduler.complete(request['call_id'], {'error': 'Orçamento do aplicativo indisponível'}, identity)
            return
        self._inflight = request['call_id']
        self._journal_context('context_request', request, dict(questions=request['questions'],
            feature_key=feature_key, features=state['features'], censoring='partial_source'))
        provider_state = dict(instrument_id=workspace.instrument_id, source_id=workspace.source_id,
            epoch=state['epoch'], full_tape=False, features=state['features'], health=state['health'])
        started = self.clock.monotonic_ns()
        def evaluate():
            try:
                response = self._jev_executor(provider_state, request['questions'])
                value = dict(call_id=request['call_id'], response=response, request=request)
            except Exception:
                value = dict(call_id=request['call_id'], error='JEV indisponível; resposta contextual bloqueada', request=request)
            value['latency_ms'] = max(0, (self.clock.monotonic_ns()-started)/1_000_000)
            if not self.closed:
                try:
                    self.jev_results.put_nowait(value)
                except queue.Full:
                    pass
        threading.Thread(target=evaluate, daemon=True, name='multimarket-context').start()
        self.metrics['jev_latency_ms'] = None

    def tick(self):
        if self.closed:
            return False
        started = time.perf_counter()
        changed = False
        while not self.discovery_results.empty():
            self._admit_discovery(self.discovery_results.get_nowait())
            changed = True
        for workspace_id in list(self.states):
            workspace = self.registry.get_workspace(workspace_id)
            adapter = self.adapters.get(workspace.source_id)
            if adapter:
                items = adapter.drain(limit=500)
                for item in items:
                    self._ingest(workspace_id, item)
                changed = bool(items) or changed
        self._context_tick()
        if self.clock.monotonic_ns()-self._last_memory_ns >= 1_000_000_000:
            self.metrics['rss_bytes'] = process_rss_bytes()
            self._last_memory_ns = self.clock.monotonic_ns()
        self.timings.append((time.perf_counter()-started)*1000)
        self.metrics['process_p95_ms'] = sorted(self.timings)[max(0, int(len(self.timings)*.95)-1)]
        if changed:
            self.sequence += 1
        return changed

    def snapshot(self):
        selected_id = self._selected()
        workspaces = []
        for workspace_id in self.states:
            workspace = self.registry.get_workspace(workspace_id)
            spec = self.registry.get_instrument(workspace.instrument_id)
            workspaces.append(dict(workspace_id=workspace_id, instrument_id=spec.instrument_id,
                source_id=workspace.source_id, symbol=spec.symbol, venue=spec.venue,
                segment=spec.segment, **self.statuses[workspace_id]))
        selected = None
        if selected_id:
            workspace = self.registry.get_workspace(selected_id)
            spec = self.registry.get_instrument(workspace.instrument_id)
            market = self.states[selected_id].snapshot()
            account_id = self.account_ids.get(selected_id, workspace.account_id)
            account = self.accounts.view(account_id) if account_id else None
            identity = self._identity(selected_id)
            context = dict(self.context) if self.context else None
            if context:
                age = (self.clock.monotonic_ns()-context['origin_monotonic_ns'])/1_000_000
                if context['identity'] != wire(identity) or not 0 <= age <= 2000:
                    context = None
                else:
                    context['age_ms'] = age
            reasons = []
            if any(market['health'][domain]['status'] != 'live' for domain in ('quote', 'trades')):
                reasons.append('Dados ausentes, vencidos ou inconsistentes')
            if not account or account.get('status') != 'reconciled':
                reasons.append('Conta não conciliada ou vencida')
            costs = self.costs.get(selected_id)
            if not costs or not costs.get('verified') or any(costs.get(k) is None for k in ('fee_rate', 'slippage')):
                reasons.append('Custos não verificados')
            reasons.append('Modelo financeiro não aprovado para este instrumento')
            selected = dict(workspace_id=selected_id, instrument_id=workspace.instrument_id,
                evaluation_identity=wire(identity),
                source_id=workspace.source_id, instrument=wire(spec), source=wire(self.registry.get_source(workspace.source_id)),
                market=market, account=account, costs=costs, context=context,
                decision=dict(action='wait', reason=' · '.join(reasons), quantity='0', profit_probability=None, net_profit=None))
        result = dict(schema_version=3, sequence=self.sequence, generated_at_ms=self.clock.wall_ms(),
            selected_workspace_id=selected_id, workspaces=workspaces, selected=selected,
            scheduler=self.scheduler.snapshot(), recording=dict(status='recording' if self.recording and self.recording_workspace == selected_id else 'off', reason=self.recording_reason),
            metrics=dict(self.metrics), gates={
                'b3': dict(status='blocked', reason='Provedor, licença e entitlement WIN/WDO ainda não qualificados'),
                'private_account': dict(status='blocked', reason='Integração read-only privada ainda não autorizada; conciliação manual identificada'),
                'financial_model': dict(status='blocked', reason='Corpus e avaliação temporal por instrumento pendentes'),
                'native_evidence': dict(status='unmeasured', reason='Janela Windows, GPU e jornada humana ainda não medidas')}, orders_enabled=False,
            discovery=[dict(source_id=k, **v) for k, v in self.statuses.items() if k not in self.states])
        return result

    def close(self):
        self.closed = True
        self.scheduler.set_enabled(False)
        for adapter in self.adapters.values():
            adapter.stop()
        self.accounts.close()
        self.journal.close()

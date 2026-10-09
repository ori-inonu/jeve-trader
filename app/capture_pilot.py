"""Local capture evidence. No market rows, account state or JEV requests."""
from __future__ import annotations

import time
import uuid
import json
import math
from pathlib import Path


def latency_bucket(ms):
    """Upper bounds: 1 ms up to 1 s, 10 ms to 2 s, 100 ms to 60 s."""
    step = 1 if ms <= 1000 else 10 if ms <= 2000 else 100
    return min(60000, math.ceil(ms / step) * step)


class Measurements:
    def __init__(self):
        self.buckets = {}
        self.count = self.overflow = 0
        self.minimum = self.maximum = None

    def add(self, value):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            return False
        bucket = latency_bucket(value)
        self.buckets[bucket] = self.buckets.get(bucket, 0) + 1
        self.count += 1
        self.overflow += value > 60000
        self.minimum = value if self.minimum is None else min(self.minimum, value)
        self.maximum = value if self.maximum is None else max(self.maximum, value)
        return True

    def summary(self):
        rank, seen, p95 = math.ceil(self.count*.95), 0, None
        for upper, count in sorted(self.buckets.items()):
            seen += count
            if seen >= rank:
                p95 = upper
                break
        if p95 == 60000 and self.overflow > self.count*.05: p95 = None
        return dict(count=self.count, min_ms=self.minimum, max_ms=self.maximum, p95_ms=p95,
                    overflow_over_60s=self.overflow, percentile_method='histogram_upper_bound')


SCENARIOS = ('burst', 'scroll', 'filter', 'hidden_tab', 'window_close', 'reconnect')


def visual_measurement(payload):
    if not isinstance(payload, dict) or set(payload) != {'buckets', 'excluded', 'overflow'}:
        raise ValueError('Histograma visual inválido')
    buckets = payload['buckets']
    if not isinstance(buckets, list) or len(buckets) > 1681:
        raise ValueError('Histograma visual inválido')
    metric = Measurements()
    for pair in buckets:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError('Histograma visual inválido')
        upper, count = pair
        if (type(upper) is not int or not 0 <= upper <= 60000 or latency_bucket(upper) != upper
                or upper in metric.buckets or type(count) is not int or not 1 <= count <= 10000000):
            raise ValueError('Histograma visual inválido')
        metric.buckets[upper] = count
        metric.count += count
    excluded, overflow = payload['excluded'], payload['overflow']
    if (metric.count > 10000000 or type(excluded) is not int or not 0 <= excluded <= 10000000
            or type(overflow) is not int or not 0 <= overflow <= metric.buckets.get(60000, 0)):
        raise ValueError('Histograma visual inválido')
    metric.overflow = overflow
    result = metric.summary()
    result.pop('min_ms'); result.pop('max_ms')  # Only bucket bounds are known.
    return {**result, 'excluded': excluded, 'measurement': 'frontend_receive_to_two_frames_foreground'}


def validate_saved_report(report):
    """Local checkpoints are input too; never trust their paths or UI shapes."""
    if not isinstance(report, dict) or type(report.get('schema_version')) is not int or report['schema_version'] != 1:
        raise ValueError('Checkpoint inválido')
    if (report.get('status') not in ('recording', 'finished', 'interrupted')
            or str(uuid.UUID(report.get('id', ''))) != report['id']):
        raise ValueError('Checkpoint inválido')
    for field in ('duration_ms','capture_samples','interruptions','contract_changes','started_at_ms'):
        if type(report.get(field)) is not int or report[field] < 0: raise ValueError('Checkpoint inválido')
    if not isinstance(report.get('symbol'), str): raise ValueError('Checkpoint inválido')
    if not isinstance(report.get('pending'), list) or not all(isinstance(p,str) for p in report['pending']):
        raise ValueError('Checkpoint inválido')
    if not isinstance(report.get('scenarios'), list) or not all(isinstance(s,dict)
            and s.get('scenario') in SCENARIOS and s.get('evidence_kind') == 'operator_declaration'
            and type(s.get('elapsed_ms')) is int and s['elapsed_ms'] >= 0 for s in report['scenarios']):
        raise ValueError('Checkpoint inválido')
    if not isinstance(report.get('timings'), dict): raise ValueError('Checkpoint inválido')
    for metric in report['timings'].values():
        if (not isinstance(metric,dict) or type(metric.get('count')) is not int or metric['count'] < 0
                or metric.get('p95_ms') is not None and (type(metric['p95_ms']) not in (int,float)
                    or not math.isfinite(metric['p95_ms']) or metric['p95_ms'] < 0)):
            raise ValueError('Checkpoint inválido')


class CapturePilot:
    def __init__(self, directory):
        self.active = None
        self.save_error = None
        self.report_path = None
        self.directory = Path(directory) / 'capture-pilots'
        self.last = dict(status='idle', id=None)
        latest = self.directory / 'latest.json'
        try:
            if latest.is_file():
                if latest.stat().st_size > 524288: raise ValueError('Checkpoint grande demais')
                report = json.loads(latest.read_text(encoding='utf-8'))
                validate_saved_report(report)
                report.update(acceptance='PENDING_REAL_REVIEW', report_path=str((self.directory/(report['id']+'.json')).resolve()))
                self.last = report
                if self.last['status'] == 'recording':
                    self.last.update(status='interrupted')
                    self.last['pending'] = list(dict.fromkeys(self.last['pending']+['process_interrupted']))
                    self._persist(self.last)
        except (OSError, ValueError, AttributeError, TypeError):
            self.last = dict(status='idle', id=None, save_error='Checkpoint local do piloto inválido ou indisponível; não foi retomado')

    def start(self, *, connected, mode, symbol, generation):
        if not connected or mode != 'excel_observation':
            raise ValueError('Conecte a captura Excel antes de iniciar o piloto')
        if self.active:
            raise ValueError('Um piloto já está em andamento')
        self.active = dict(id=str(uuid.uuid4()), status='recording', symbol=symbol,
                           source_generation=generation, started_at_ms=int(time.time()*1000),
                           schema_version=1, capture_samples=0, coverage=dict(fresh_quote_samples=0,
                           tape_samples=0, book_samples=0, broker_samples=0, trade_id_samples=0,
                           full_tape_samples=0, invalid_clock_samples=0), interruptions=0,
                           generation_changes=0, contract_changes=0, scenarios=[], events=[])
        self.started = self.last_checkpoint = time.monotonic()
        self.last_capture = None
        self.last_generation, self.last_symbol = generation, symbol
        self.last_connected = True
        self.save_error = self.report_path = None
        self.jev_ids = set()
        self.jev_attempts = dict(response_received=0, failed=0, cancelled=0)
        self.metrics = {k:Measurements() for k in ('quote_age_on_receive_ms','capture_to_receive_ms','jev_response_ms')}
        self.polling = dict(polling_effective_ms=None, rtd_change_interval_ms=None)
        self.visual = dict(count=0, p95_ms=None, excluded=0, measurement='frontend_receive_to_two_frames_foreground')
        self.visual_sessions = {}
        self.visual_checkpoint_at_ms = None
        self._persist(self.snapshot())

    def observe(self, market, *, connected, caps):
        if not self.active: return
        a = self.active
        generation, symbol = market['source_generation'], market['symbol']
        if generation != self.last_generation:
            a['generation_changes'] += 1
            self.last_generation = generation
            self._event('source_generation_changed')
        if symbol != self.last_symbol:
            a['contract_changes'] += 1
            self.last_symbol = symbol
            self._event('contract_changed')
        available = connected and market['application_mode'] == 'excel_observation'
        if available != self.last_connected:
            if not available: a['interruptions'] += 1
            self._event('capture_reconnected' if available else 'capture_interrupted')
            self.last_connected = available
        evidence = market.get('order_flow', {}).get('capture_evidence', {})
        received = evidence.get('received_at_ms')
        key = (generation, received)
        if available and type(received) is int and received >= a['started_at_ms'] and key != self.last_capture:
            self.last_capture = key
            a['capture_samples'] += 1
            cov = a['coverage']
            for field, enabled in (('fresh_quote_samples',caps.get('quote_fresh')), ('tape_samples',caps.get('tape')),
                    ('book_samples',caps.get('price_depth')), ('broker_samples',caps.get('buyer_broker') and caps.get('seller_broker')),
                    ('trade_id_samples',market.get('order_flow',{}).get('source_capabilities',{}).get('trade_id')),
                    ('full_tape_samples',caps.get('full_tape'))):
                cov[field] += bool(enabled)
            quote_ts = (market.get('last_quote') or {}).get('ts_ms')
            captured = evidence.get('captured_at_ms')
            for field, stamp in (('quote_age_on_receive_ms',quote_ts), ('capture_to_receive_ms',captured)):
                if type(stamp) is int and not self.metrics[field].add(received-stamp):
                    cov['invalid_clock_samples'] += 1
            for field in self.polling:
                value = evidence.get(field)
                if type(value) in (int,float) and math.isfinite(value) and value >= 0: self.polling[field] = value
        if time.monotonic()-self.last_checkpoint >= 30:
            self._persist(self.snapshot())
            self.last_checkpoint = time.monotonic()

    def record_jev_attempt(self, attempt, outcome):
        if not self.active or outcome not in self.jev_attempts: return
        submitted = attempt.get('submitted_at_ms')
        call_id = attempt.get('call_id')
        if (type(submitted) is not int or submitted < self.active['started_at_ms']
                or attempt.get('mode') != 'excel_observation' or not call_id or call_id in self.jev_ids): return
        self.jev_ids.add(call_id)
        self.jev_attempts[outcome] += 1
        self.metrics['jev_response_ms'].add(attempt.get('latency_ms'))

    def _event(self, kind):
        # Counters are never truncated; only the bounded diagnostic list is.
        if len(self.active['events']) < 64:
            self.active['events'].append(dict(kind=kind, elapsed_ms=int((time.monotonic()-self.started)*1000)))

    def checkpoint(self, pilot_id, visual, session):
        self._update_visual(pilot_id, visual, session)
        self._persist(self.snapshot())

    def _update_visual(self, pilot_id, visual, session):
        if not self.active or pilot_id != self.active['id']:
            raise ValueError('O piloto vigente mudou ou não está ativo')
        if (not isinstance(session, str) or not 1 <= len(session) <= 64
                or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in session)):
            raise ValueError('Sessão visual inválida')
        updated = visual_measurement(visual)
        previous = self.visual_sessions.get(session)
        if previous:
            old = visual_measurement(previous)
            old_buckets, new_buckets = dict(previous['buckets']), dict(visual['buckets'])
            if (updated['excluded'] < old['excluded'] or updated['overflow_over_60s'] < old['overflow_over_60s']
                    or any(new_buckets.get(k, 0) < count for k, count in old_buckets.items())):
                raise ValueError('Checkpoint visual regressivo')
        elif len(self.visual_sessions) >= 8:
            raise ValueError('Limite de sessões visuais do piloto atingido')
        sessions = {**self.visual_sessions, session: visual}
        buckets, excluded, overflow = {}, 0, 0
        for value in sessions.values():
            for upper, count in value['buckets']: buckets[upper] = buckets.get(upper, 0)+count
            excluded += value['excluded']; overflow += value['overflow']
        total = visual_measurement(dict(buckets=[[k,v] for k,v in buckets.items()], excluded=excluded, overflow=overflow))
        self.visual_sessions, self.visual = sessions, total
        self.visual_checkpoint_at_ms = int(time.time()*1000)

    def stop(self, pilot_id, *, interrupted=False, visual=None, visual_session='legacy'):
        if not self.active or pilot_id != self.active['id']:
            raise ValueError('O piloto vigente mudou ou não está ativo')
        if visual is not None:
            self._update_visual(pilot_id, visual, visual_session)
        report = self.snapshot()
        report.update(status='interrupted' if interrupted else 'finished', ended_at_ms=int(time.time()*1000))
        if interrupted: report['pending'].append('process_interrupted')
        self._persist(report)
        self.last, self.active = report, None

    def mark(self, pilot_id, scenario):
        if not self.active or pilot_id != self.active['id'] or scenario not in SCENARIOS:
            raise ValueError('Informe o piloto vigente e um cenário conhecido')
        if not any(s['scenario'] == scenario for s in self.active['scenarios']):
            self.active['scenarios'].append(dict(scenario=scenario, evidence_kind='operator_declaration',
                elapsed_ms=int((time.monotonic()-self.started)*1000)))
            self._persist(self.snapshot())

    def save(self, pilot_id):
        report = self.snapshot()
        if not pilot_id or pilot_id != report['id']:
            raise ValueError('Informe o piloto vigente')
        self._persist(report)
        if not self.active: self.last = report

    def _persist(self, report):
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            path = self.directory / (report['id']+'.json')
            self.report_path = report['report_path'] = str(path.resolve())
            self.save_error = report['save_error'] = None
            report['pending'] = [p for p in report.get('pending', []) if p != 'report_save_failed']
            body = json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2)
            for target in (path, self.directory / 'latest.json'):
                temp = target.with_suffix('.tmp')
                temp.write_text(body, encoding='utf-8')
                temp.replace(target)
        except OSError:
            self.save_error = report['save_error'] = 'Não foi possível salvar o relatório local do piloto'
            if 'report_save_failed' not in report['pending']: report['pending'].append('report_save_failed')

    def close(self):
        if self.active: self.stop(self.active['id'], interrupted=True)

    def snapshot(self):
        if not self.active: return dict(self.last)
        report = {**self.active, 'coverage':dict(self.active['coverage']),
                  'events':list(self.active['events']), 'scenarios':list(self.active['scenarios'])}
        report['duration_ms'] = max(0, int((time.monotonic()-self.started)*1000))
        report['timings'] = {k:v.summary() for k,v in self.metrics.items()}
        report['timings']['visual_after_receive_ms'] = dict(self.visual)
        report['visual_checkpoint_at_ms'] = self.visual_checkpoint_at_ms
        report['polling_last_observed'] = dict(self.polling)
        report['jev_attempts'] = dict(self.jev_attempts)
        pending = ['source_continuity_not_demonstrated', 'operator_review_required']
        if report['duration_ms'] < 1800000: pending.append('duration_below_30min')
        if not report['capture_samples']: pending.append('capture_samples_missing')
        if not self.visual['count']: pending.append('visual_samples_missing')
        elif self.visual['p95_ms'] is None: pending.append('visual_percentile_unbounded')
        elif self.visual['p95_ms'] > 250: pending.append('visual_p95_above_250ms')
        if report['contract_changes']: pending.append('contract_changed')
        if report['coverage']['invalid_clock_samples']: pending.append('clock_inconsistency')
        if len(report['scenarios']) != len(SCENARIOS): pending.append('operator_scenarios_missing')
        if self.save_error: pending.append('report_save_failed')
        report.update(pending=pending, acceptance='PENDING_REAL_REVIEW', report_path=self.report_path, save_error=self.save_error,
                      measurement_limits=['A idade da cotação usa relógios distintos; não é latência da bolsa.',
                        'O intervalo RTD é a última mudança amostrada, não todos os negócios.',
                        'Marcas de cenário são declarações do operador.',
                        'Medições visuais são salvas a cada 5 segundos; interrupções preservam somente o último checkpoint recebido.',
                        'Latência JEV inclui respostas recebidas e falhas do piloto, mesmo após OFF; cancelamentos sem envio não têm latência.',
                        'Não valida rentabilidade, inferência JEV nem tape completo.'])
        return report

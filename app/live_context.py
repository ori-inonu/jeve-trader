"""Bounded experimental live context. No financial estimator or order routing."""
from datetime import datetime
from decimal import Decimal
import json
import sqlite3
from zoneinfo import ZoneInfo
from context_cycle import observed_flow_context


class ContextCadence:
    def __init__(self):
        self.pending = False
        self.last_projection = None
        self.last_ms = -1_000_000
        self.retry_at_ms = 0
        self.retry_delay_ms = 3000

    def start(self, projection, now_ms, cadence_ms):
        if self.pending or now_ms < self.retry_at_ms or projection == self.last_projection or now_ms-self.last_ms < cadence_ms:
            return False
        self.pending, self.last_projection, self.last_ms = True, projection, now_ms
        return True

    def finish(self, success=False):
        self.pending = False
        if success:
            self.retry_at_ms, self.retry_delay_ms = 0, 3000

    def fail(self, now_ms):
        self.pending = False
        self.retry_at_ms = now_ms + self.retry_delay_ms
        self.retry_delay_ms = min(60000, self.retry_delay_ms * 2)


class ContextAlert:
    def __init__(self):
        self.armed = True
        self.last_ms = -1_000_000
        self.sequence = 0

    def reset(self):
        # A new capture/settings revision starts a new episode, never a reused ID.
        self.armed, self.last_ms = True, -1_000_000

    def update(self, temperature, *, valid, geometry, now_ms, threshold=80, rearm=60, cooldown_ms=15000):
        # Missing data cannot rearm an episode. A measured neutral interval can.
        if not valid or temperature is None:
            return None
        if abs(temperature) < rearm:
            self.armed = True
        if not geometry or not self.armed or abs(temperature) < threshold or now_ms-self.last_ms < cooldown_ms:
            return None
        self.armed, self.last_ms = False, now_ms
        self.sequence += 1
        return dict(id=self.sequence, side='buy' if temperature > 0 else 'sell', at_ms=now_ms,
                    temperature=temperature, experimental=True, calibrated=False)


DEFAULT_LIVE_SETTINGS = dict(revision=1, automatic=True, cadence_ms=1000, validity_ms=2000,
                             horizon_seconds=60, alert_threshold=80, alert_rearm=60,
                             alert_cooldown_ms=15000, alerts_enabled=True, sound_enabled=False,
                             daily_limit_usd='1', total_limit_usd='5')


def update_live_settings(current, values):
    allowed = set(DEFAULT_LIVE_SETTINGS)-{'revision'}
    if set(values)-allowed:
        raise ValueError('Parâmetro contextual desconhecido')
    result = {**current, **values, 'revision': current['revision']+1}
    bounds = dict(cadence_ms=(1000, 60000), validity_ms=(500, 2000), horizon_seconds=(5, 120),
                  alert_threshold=(1, 100), alert_rearm=(0, 99), alert_cooldown_ms=(15000, 300000))
    for key, (low, high) in bounds.items():
        if type(result[key]) is not int or not low <= result[key] <= high:
            raise ValueError('Parâmetro contextual fora do limite')
    if result['alert_rearm'] >= result['alert_threshold']:
        raise ValueError('Rearme deve ficar abaixo do limiar')
    for key in ('automatic', 'alerts_enabled', 'sound_enabled'):
        if type(result[key]) is not bool:
            raise ValueError('Controle inválido')
    for key, maximum in (('daily_limit_usd', 1), ('total_limit_usd', 5)):
        value = Decimal(str(result[key]))
        if not value.is_finite() or not 0 < value <= maximum:
            raise ValueError('Orçamento excede o piloto autorizado')
        result[key] = str(value)
    return result


def relevant_projection(market, rows, revision):
    """Exclude wall-clock-only changes; keep measured values and freshness."""
    import hashlib
    def stable(value):
        if isinstance(value, dict):
            return {k: stable(v) for k,v in value.items() if k not in ('ts_ms', 'start_exclusive_ms', 'end_inclusive_ms', 'observed_at_ms', 'last_event_ts_ms', 'coverage_start_ms', 'captured_at_ms', 'received_at_ms', 'market_ts_ms')}
        if isinstance(value, list):
            return [stable(v) for v in value]
        return value
    state = dict(symbol=market['symbol'], generation=market['source_generation'], revision=revision,
                 features=stable(market['computed_features']), coverage=stable(market['evidence_coverage']),
                 order_flow=stable(observed_flow_context(market)), phenomena=stable(market.get('hypotheses',[])),
                 rows=stable(rows))
    return hashlib.sha256(json.dumps(state, sort_keys=True, allow_nan=False).encode()).hexdigest()


class PilotBudget:
    """Durable worst-case reservation before HTTPS; failures remain unknown.

    Price snapshot: docs.typesafe.ai/models, checked 2026-10-07.
    64k combined request limit; $0.042/M input tokens, output free.
    Estimates are not provider invoices. No automatic pilot renewal.
    """
    rate = Decimal('0.042') / Decimal(1_000_000)
    reservation = Decimal(64000) * rate

    def __init__(self, path, *, daily='1', total='5'):
        self.daily, self.total = Decimal(daily), Decimal(total)
        if not 0 < self.daily <= 1 or not 0 < self.total <= 5:
            raise ValueError('Limite do piloto excedido')
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS live_api_pilot(id TEXT PRIMARY KEY, day TEXT NOT NULL, usd TEXT NOT NULL, settled INTEGER NOT NULL)')
        self.db.commit()

    @staticmethod
    def day(now_ms):
        return datetime.fromtimestamp(now_ms/1000, ZoneInfo('America/Sao_Paulo')).date().isoformat()

    def snapshot(self, now_ms):
        rows = self.db.execute('SELECT day,usd,settled FROM live_api_pilot').fetchall()
        estimated = sum((Decimal(r[1]) for r in rows if r[2]), Decimal(0))
        reserved = sum((Decimal(r[1]) for r in rows if not r[2]), Decimal(0))
        today = sum((Decimal(r[1]) for r in rows if r[0] == self.day(now_ms)), Decimal(0))
        fmt = lambda value: format(value.normalize(), 'f')
        return dict(estimated_usd=fmt(estimated), reserved_usd=fmt(reserved), committed_usd=fmt(estimated+reserved),
                    today_usd=fmt(today), daily_limit_usd=str(self.daily), total_limit_usd=str(self.total), billed_usd=None,
                    unknown_attempts=sum(not r[2] for r in rows), price_checked='2026-10-07',
                    price_source='https://docs.typesafe.ai/models', input_usd_per_million='0.042')

    def reserve(self, call_id, *, now_ms):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            state = self.snapshot(now_ms)
            if Decimal(state['today_usd'])+self.reservation > self.daily or Decimal(state['committed_usd'])+self.reservation > self.total:
                raise ValueError('Orçamento do piloto esgotado; nenhuma chamada enviada')
            self.db.execute('INSERT INTO live_api_pilot VALUES(?,?,?,0)', (call_id, self.day(now_ms), str(self.reservation)))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def settle(self, call_id, usage):
        tokens = usage.get('input_tokens')
        if type(tokens) is not int or not 0 <= tokens <= 64000:
            raise ValueError('Uso fora do limite contratado; reserva permanece desconhecida')
        with self.db:
            self.db.execute('UPDATE live_api_pilot SET usd=?,settled=1 WHERE id=? AND settled=0', (str(tokens*self.rate), call_id))

    def close(self):
        self.db.close()

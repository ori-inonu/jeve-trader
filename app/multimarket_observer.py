"""Owner-thread projection of a bounded, explicitly started public observer."""
from __future__ import annotations

import time


class MultimarketObserver:
    def __init__(self, *, feed_factory=None, clock_ms=None, clock_monotonic=None):
        self.feed_factory = feed_factory
        self.clock_ms = clock_ms or (lambda: int(time.time() * 1000))
        self.clock_monotonic = clock_monotonic or time.monotonic
        self.feed = None
        self.deadline = None
        self.batch = None
        self.vap = None
        self.instrument_id = None
        self.context = None
        self.features = {}
        self.state = 'off'
        self.origin = None
        self.error = None
        self.received = 0

    def start(self, *, duration_seconds):
        if type(duration_seconds) is not int or not 1 <= duration_seconds <= 1800:
            raise ValueError('Duração deve ser inteira entre 1 e 1800 segundos')
        self.stop()
        if self.feed_factory is None:
            from public_crypto_feed import PublicCryptoFeed
            factory = PublicCryptoFeed
        else:
            factory = self.feed_factory
        self.feed = factory()
        try:
            self.feed.start()
        except Exception:
            self.feed.stop()
            self.feed = None
            self.state = 'unavailable'
            self.error = 'Coletor público indisponível; confira dependência opcional e saúde da fonte.'
            raise ValueError(self.error) from None
        self.deadline = self.clock_monotonic() + duration_seconds
        self.state, self.origin, self.error = 'starting', 'live', None
        self.received = 0

    def _accept(self, batch):
        from market_replay import VolumeAtPrice
        from multimarket_context import build_multimarket_context
        if self.vap is None or self.instrument_id != batch.instrument.instrument_id:
            self.vap = VolumeAtPrice(batch.instrument)
            self.instrument_id = batch.instrument.instrument_id
        for trade in batch.trades:
            self.vap.accept(trade)
        self.received += len(batch.trades)
        now = self.clock_ms()
        self.features = self.vap.snapshot(start_ms=now - 60000, end_ms=now + 1)
        self.context = build_multimarket_context(
            batch, features={'volume_at_price': self.features},
            as_of_ms=now)
        self.batch = batch
        self.state = 'observing' if batch.health and all(h.valid and not h.stale for h in batch.health) else 'degraded'

    def poll(self):
        if self.feed is None:
            return False
        if self.clock_monotonic() >= self.deadline:
            self.stop()
            self.state = 'finished'
            return True
        try:
            self._accept(self.feed.poll(max_events=1000))
        except Exception:
            self.stop()
            self.state = 'invalid'
            self.error = 'Dados inconsistentes ou coletor indisponível; observação interrompida.'
        return True

    def synthetic(self):
        self.stop()
        self.origin, self.error = 'synthetic', None
        self.received = 0
        self._accept(synthetic_batch(self.clock_ms()))
        self.state = 'synthetic'

    def stop(self):
        feed, self.feed = self.feed, None
        try:
            if feed is not None:
                feed.stop()
        finally:
            self.deadline = None
            self.batch = self.vap = self.context = None
            self.instrument_id = None
            self.features = {}
            self.state = 'off'

    def snapshot(self):
        from multimarket_economics import evaluation_report
        return {
            'enabled': self.feed is not None, 'status': self.state,
            'origin': self.origin, 'error': self.error,
            'instrument': self.batch.instrument.to_dict() if self.batch else None,
            'source': self.batch.source.to_dict() if self.batch else None,
            'health': [h.to_dict() for h in self.batch.health] if self.batch else [],
            'book': self.batch.book.to_dict() if self.batch and self.batch.book else None,
            'features': self.context['features'] if self.context else {},
            'context': self.context, 'received_trades': self.received,
            'remaining_seconds': max(0, int(self.deadline - self.clock_monotonic())) if self.deadline else 0,
            'evaluation': evaluation_report(),
            'missing': self.context.get('missing', []) if self.context else ['source_not_started'],
            'orders_enabled': False, 'retention_enabled': False,
            'profit_probability': None, 'target_probability': None, 'ruin_probability': None,
            'objective': {'initial_capital_brl': '400', 'target_capital_brl': '4000',
                          'horizon': 'less_than_one_week', 'status': 'not_estimated'},
        }


def synthetic_batch(now_ms):
    """Deterministic local fixture; no data from a venue or a personal account."""
    from market_data_contract import FeedBatch, SourceDescriptor, SourceHealth
    from public_crypto_feed import BinanceSpotAdapter, LocalOrderBook
    adapter = BinanceSpotAdapter(session_epoch='synthetic-demo')
    instrument = adapter.instrument_from_exchange_info({'symbols': [{
        'symbol': 'BTCUSDT', 'baseAsset': 'BTC', 'quoteAsset': 'USDT', 'status': 'TRADING',
        'filters': [{'filterType': 'PRICE_FILTER', 'tickSize': '0.01'},
                    {'filterType': 'LOT_SIZE', 'stepSize': '0.00001'}],
    }]}, as_of_ms=now_ms)
    book = LocalOrderBook(instrument.instrument_id)
    stamp = {'receive_time_ms': now_ms, 'receive_monotonic_ns': 1000000, 'origin': 'synthetic'}
    book.buffer_delta(adapter.parse_delta({'e': 'depthUpdate', 's': 'BTCUSDT', 'E': now_ms,
        'U': 100, 'u': 101, 'b': [['99.00', '2.00000']], 'a': [['101.00', '3.00000']]}, **stamp))
    book.install_snapshot(adapter.parse_snapshot({'lastUpdateId': 100,
        'bids': [['99.00', '1.00000']], 'asks': [['101.00', '1.00000']]}, **stamp))
    trades = tuple(adapter.parse_trade({'e': 'trade', 's': 'BTCUSDT', 'E': now_ms,
        't': index, 'p': price, 'q': qty, 'T': now_ms - 1000 + index, 'm': maker}, **stamp)
        for index, price, qty, maker in [(1, '100.00', '0.10000', False),
                                       (2, '100.00', '0.20000', True),
                                       (3, '99.00', '0.05000', False)])
    source = SourceDescriptor('synthetic_btcusdt_v1', 'synthetic', 'binance_spot', 'spot',
        'binance-spot-json-v1', (), False, 'synthetic:local_fixture', 'synthetic_only', 'synthetic_only',
        None, 100, now_ms, ('synthetic-demo-v1',))
    health = tuple(SourceHealth(channel, True, 'live', True, False, 'partial', now_ms,
        now_ms, 1000000, channel == 'depth', 0, 0, 0, 0,
        'synthetic_fixture_partial', {'full_tape': False}) for channel in ('trade', 'depth'))
    return FeedBatch(source, instrument, trades, book.view(), health, ('synthetic_fixture',))

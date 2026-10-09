"""The owner projection uses actual contracts with injected offline transport."""
import unittest
from dataclasses import replace
from decimal import Decimal

from multimarket_observer import MultimarketObserver, synthetic_batch


class OfflineFeed:
    def __init__(self, batch):
        self.batch = batch
        self.starts = self.stops = 0
        self.fail = False

    def start(self):
        self.starts += 1

    def stop(self):
        self.stops += 1

    def poll(self, *, max_events):
        if self.fail:
            raise ValueError('private detail must not escape')
        return self.batch


class MultimarketObserverTests(unittest.TestCase):
    def test_explicit_start_dedup_stale_and_bounded_stop(self):
        clock = [100000]
        mono = [1.0]
        feed = OfflineFeed(synthetic_batch(clock[0]))
        observer = MultimarketObserver(feed_factory=lambda: feed,
            clock_ms=lambda: clock[0], clock_monotonic=lambda: mono[0])
        self.assertFalse(observer.snapshot()['enabled'])
        self.assertEqual(feed.starts, 0)
        observer.start(duration_seconds=2)
        observer.poll()
        first = observer.snapshot()
        self.assertEqual(first['features']['volume_at_price']['trade_count'], 3)
        quantity = first['features']['volume_at_price']['total_quantity']
        self.assertIsInstance(quantity, str)
        self.assertEqual(Decimal(quantity), Decimal('0.35'))
        self.assertIsNone(first['target_probability'])
        self.assertFalse(first['orders_enabled'])
        observer.poll()
        self.assertEqual(observer.snapshot()['features']['volume_at_price']['trade_count'], 3)
        feed.batch = replace(feed.batch, trades=(), health=tuple(
            replace(h, stale=True, valid=False, reason='no_update') for h in feed.batch.health))
        observer.poll()
        self.assertEqual(observer.snapshot()['status'], 'degraded')
        self.assertTrue(all(h['stale'] for h in observer.snapshot()['health']))
        mono[0] = 3.0
        observer.poll()
        final = observer.snapshot()
        self.assertEqual(final['status'], 'finished')
        self.assertFalse(final['enabled'])
        self.assertIsNone(final['book'])
        self.assertEqual(feed.stops, 1)

    def test_bad_batch_stops_and_sanitizes_failure(self):
        feed = OfflineFeed(synthetic_batch(100000))
        feed.fail = True
        observer = MultimarketObserver(feed_factory=lambda: feed, clock_ms=lambda: 100000)
        observer.start(duration_seconds=2)
        observer.poll()
        snapshot = observer.snapshot()
        self.assertEqual(snapshot['status'], 'invalid')
        self.assertFalse(snapshot['enabled'])
        self.assertNotIn('private detail', snapshot['error'])
        self.assertEqual(feed.stops, 1)


if __name__ == '__main__':
    unittest.main()

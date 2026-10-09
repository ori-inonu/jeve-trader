"""Service seams are observable without network or a financial account."""
import tempfile
import unittest

from desktop_service import DecisionService


class FakeObserver:
    def __init__(self):
        self.enabled = False
        self.stopped = 0
        self.duration = None
        self.invalid = False

    def start(self, *, duration_seconds):
        self.duration = duration_seconds
        self.enabled = True

    def synthetic(self):
        self.enabled = False

    def poll(self):
        return self.enabled

    def stop(self):
        self.stopped += 1
        self.enabled = False

    def snapshot(self):
        return {'enabled': self.enabled, 'status': 'invalid' if self.invalid else 'off',
                'origin': 'synthetic', 'orders_enabled': False,
                'profit_probability': None, 'target_probability': None}


class MultimarketServiceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.observer = FakeObserver()
        self.service = DecisionService(self.directory.name, multimarket_factory=lambda: self.observer)

    def tearDown(self):
        if not self.service.closed:
            self.service.close()
        self.directory.cleanup()

    def test_default_off_and_manual_win_capital_unchanged(self):
        before = self.service.snapshot()
        self.assertFalse(before['multimarket']['enabled'])
        after = self.service.command('multimarket.start', {'duration_seconds': 60})
        self.assertTrue(after['multimarket']['enabled'])
        self.assertEqual(before['account'], after['account'])
        self.assertEqual(before['market']['symbol'], after['market']['symbol'])
        self.assertFalse(after['orders_enabled'])
        self.service.tick()
        self.observer.invalid = True
        self.assertEqual(self.service.snapshot()['multimarket']['status'], 'invalid')
        self.service.command('multimarket.stop', {})
        self.assertFalse(self.observer.enabled)

    def test_only_explicit_bounded_duration_and_no_order_route(self):
        for params in ({}, {'duration_seconds': True}, {'duration_seconds': 0},
                       {'duration_seconds': 1801}, {'duration_seconds': 60, 'symbol': 'OTHER'}):
            with self.assertRaises(ValueError):
                self.service.command('multimarket.start', params)
        with self.assertRaises(ValueError):
            self.service.command('multimarket.order', {})
        self.service.command('multimarket.synthetic', {})
        with self.assertRaises(ValueError):
            self.service.command('multimarket.stop', {'secret': 'unused'})

    def test_close_stops_owned_worker_and_start_is_not_restored(self):
        self.service.command('multimarket.start', {'duration_seconds': 1})
        self.service.close()
        self.assertEqual(self.observer.stopped, 1)
        fresh = DecisionService(self.directory.name)
        try:
            self.assertFalse(fresh.snapshot()['multimarket']['enabled'])
        finally:
            fresh.close()


if __name__ == '__main__':
    unittest.main()

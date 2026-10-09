import unittest
from profitdll_contract import ProfitMarketDataAdapter


class ProfitAdapterTests(unittest.TestCase):
    def test_sdk_absent_and_sequence_gap_is_visible(self):
        adapter = ProfitMarketDataAdapter('WINV26', capacity=2, sequence_is_per_symbol=True)
        with self.assertRaises(RuntimeError):
            adapter.connect()
        for i in (1, 2, 4):
            adapter.on_trade(dict(id=str(i), symbol='WINV26', ts_ms=1000+i, price_points=100000, quantity=1, aggressor='buy'), sequence=i)
        batch = adapter.read(observed_at_ms=1010)
        self.assertFalse(batch.health.complete)
        self.assertFalse(batch.health.sequence_ok)
        self.assertIn('QUEUE_OVERFLOW', batch.warnings)
        self.assertIn('SEQUENCE_GAP', batch.warnings)
        self.assertEqual(len(batch.events), 2)

    def test_unknown_sequence_scope_never_asserts_continuity(self):
        adapter = ProfitMarketDataAdapter('WINV26')
        for i in (1, 4):
            adapter.on_trade(dict(id=str(i), symbol='WINV26', ts_ms=1000+i, price_points=100000, quantity=1, aggressor='buy'), sequence=i)
        batch = adapter.read(observed_at_ms=1010)
        self.assertFalse(batch.health.sequence_ok)
        self.assertFalse(batch.health.complete)
        self.assertNotIn('SEQUENCE_GAP', batch.warnings)

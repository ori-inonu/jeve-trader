import json
import tempfile
import unittest
from pathlib import Path

from multimarket.service import MultimarketService


class Clock:
    def __init__(self):
        self.wall = 10000
        self.mono = 10_000_000_000

    def wall_ms(self):
        return self.wall

    def monotonic_ns(self):
        return self.mono


class MultimarketIntegrationTests(unittest.TestCase):
    def test_boot_is_offline_versioned_and_separate_from_legacy_storage(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / 'journal.sqlite3'
            legacy.write_bytes(b'legacy storage fixture')
            service = MultimarketService(directory, clock=Clock(), adapters={})
            try:
                snapshot = service.command('multimarket.snapshot', {})
                self.assertEqual(snapshot['schema_version'], 3)
                self.assertFalse(snapshot['orders_enabled'])
                self.assertIsNone(snapshot['selected'])
                self.assertFalse(snapshot['scheduler']['enabled'])
                self.assertEqual(legacy.read_bytes(), b'legacy storage fixture')
                self.assertIn('b3', snapshot['gates'])
                with self.assertRaises(ValueError):
                    service.command('multimarket.order.send', {})
                json.dumps(snapshot, allow_nan=False)
            finally:
                service.close()

    def test_unknown_recording_policy_and_private_account_are_visible_gates(self):
        with tempfile.TemporaryDirectory() as directory:
            service = MultimarketService(directory, clock=Clock(), adapters={})
            try:
                snapshot = service.command('multimarket.snapshot', {})
                self.assertNotEqual(snapshot['recording']['status'], 'recording')
                self.assertNotEqual(snapshot['gates']['private_account']['status'], 'ready')
                self.assertNotEqual(snapshot['gates']['financial_model']['status'], 'ready')
            finally:
                service.close()


if __name__ == '__main__':
    unittest.main()

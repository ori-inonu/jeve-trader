import tempfile
import unittest
from decision_store import DecisionStore
from app_store import UserStore


class LedgerTests(unittest.TestCase):
    def test_bootstrap_preserves_legacy_brazilian_amounts_and_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            legacy = UserStore(folder)
            original = {'current': 'R$ 1.200,50', 'peak': '1.400,00', 'workbook': 'Mesa.xlsx'}
            legacy.save_settings(original)
            legacy.close()
            store = DecisionStore(folder)
            self.assertEqual(store.account().equity_brl, '1200.50')
            self.assertEqual(store.account().peak_brl, '1400.00')
            store.close()
            legacy = UserStore(folder)
            self.assertEqual(legacy.settings(), original)
            legacy.close()

    def test_manual_partial_fills_results_idempotent_and_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            store = DecisionStore(folder)
            initial = store.account()
            store.update_account({'equity_brl': '800', 'available_margin_brl': '800'}, initial.revision)
            store.open_position('fill1', 'buy', 2, '100000', '310', '2', 'WINV26')
            store.close_position('fill2', 1, '100100', '1')
            self.assertEqual(store.account().equity_brl, '817.00')  # entry fees proportionally 1 + exit 1; open entry debit 2
            self.assertEqual(store.account().positions[0]['quantity'], 1)
            store.close_position('fill3', 1, '99900', '1')
            self.assertEqual(store.account().equity_brl, '796.00')
            self.assertEqual(store.account().peak_brl, '817.00')
            store.close_position('fill3', 1, '99900', '1')
            self.assertEqual(store.account().equity_brl, '796.00')
            with self.assertRaises(ValueError):
                store.update_account({'equity_brl': '400'}, 0)
            store.record('experiment', {'api_key': 'never-store', 'observation': {'ts_ms': 3}})
            self.assertNotIn('never-store', str(store.history()))
            store.close()
            reopened = DecisionStore(folder)
            self.assertEqual(reopened.account().equity_brl, '796.00')
            reopened.close()

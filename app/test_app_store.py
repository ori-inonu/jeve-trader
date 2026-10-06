import json
from pathlib import Path
import tempfile
import unittest

from app_store import UserStore, resource_path


class StoreTests(unittest.TestCase):
    def test_settings_whitelist_and_journal_do_not_persist_credentials(self):
        with tempfile.TemporaryDirectory() as d:
            store = UserStore(Path(d))
            store.save_settings({"symbol": "WIN_SIM", "api_key": "private-test-value"})
            store.record("jev", {"api_key": "private-test-value", "nested": {"Authorization": "private-test-value"}, "usage": 15})
            target = Path(d) / "export.json"
            store.export(target)
            self.assertEqual(store.settings(), {"symbol": "WIN_SIM"})
            self.assertNotIn("private-test-value", target.read_text())
            self.assertEqual(json.loads(target.read_text())["events"][0]["payload"]["usage"], 15)
            store.close()

    def test_nonfinite_values_are_rejected_and_storage_reopens(self):
        with tempfile.TemporaryDirectory() as d:
            store = UserStore(Path(d))
            with self.assertRaises(ValueError):
                store.record("flow", {"value": float("nan")})
            store.record("trade_manual", {"pnl_brl": "-20", "account_source": "manual"})
            store.close()
            store = UserStore(Path(d))
            self.assertEqual(len(store.recent(kind="trade_manual")), 1)
            store.close()

    def test_resource_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            resource_path("../secret")
        self.assertTrue(resource_path("config.json").exists())


if __name__ == "__main__":
    unittest.main()

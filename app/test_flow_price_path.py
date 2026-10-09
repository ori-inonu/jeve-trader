"""Observed price path is evidence, not an inferred move or prediction."""
import unittest

from context_cycle import build_context
from flow_engine import FlowEngine
from test_context_cycle import row


def snapshot_for(prices, *, complete=False, same_timestamp=False):
    engine = FlowEngine("WIN", tick_points=5)
    if complete:
        engine.set_source_quality({"feed_connected": True, "sequence_ok": True,
                                   "full_tape": True, "data_origin": "live"})
        engine.add_trade({"id": "warm-up", "symbol": "WIN", "ts_ms": 5000,
                          "price_points": "100000", "quantity": 1, "aggressor": "unknown"})
    for index, price in enumerate(prices):
        engine.add_trade({"id": f"trade-{index}", "symbol": "WIN",
                          "ts_ms": 9000 if same_timestamp else 9000 + index,
                          "price_points": str(price), "quantity": 1, "aggressor": "buy"})
    return engine.snapshot(10000)


class ObservedPricePathTests(unittest.TestCase):
    def test_window_boundaries_and_numeric_paths_are_independent(self):
        observations = [(10000, 99900), (10001, 100010), (30000, 100025),
                        (30001, 100000), (32000, 99980), (35000, 99995),
                        (35001, 100005), (38000, 100025), (40000, 100010)]
        expected = {"5s": (35000, 40000, 3, "4", "0", "3", "1"),
                    "previous_5s": (30000, 35000, 3, "0", "4", "1", "3"),
                    "30s": (10000, 40000, 8, "3", "6", "3", "6")}
        for complete in (False, True):
            engine = FlowEngine("WIN", tick_points=5)
            engine.set_source_quality({"feed_connected": True, "sequence_ok": True,
                                       "full_tape": complete, "data_origin": "live"})
            for index, (stamp, price) in enumerate(observations):
                self.assertTrue(engine.add_trade({"id": f"window-{index}", "symbol": "WIN",
                    "ts_ms": stamp, "price_points": str(price), "quantity": 1,
                    "aggressor": "buy"})["accepted"])
            windows = engine.snapshot(40000)["computed_features"]["windows"]
            for name, (start, end, count, upward, downward, buy_return, sell_return) in expected.items():
                with self.subTest(complete=complete, window=name):
                    self.assertEqual(windows[name]["start_exclusive_ms"], start)
                    self.assertEqual(windows[name]["end_inclusive_ms"], end)
                    self.assertEqual(windows[name]["price_path"], {
                        "observation_count": count, "basis": "first_observed_trade",
                        "upward_excursion_ticks": upward, "downward_excursion_ticks": downward,
                        "buy_retracement_ticks": buy_return, "sell_retracement_ticks": sell_return,
                        "scope": "complete" if complete else "partial"})

    def test_same_net_progress_can_preserve_different_excursion_and_retracement(self):
        retained_then_retraced = snapshot_for([100000, 100005, 100010, 100015, 100020, 100005], complete=True)
        direct = snapshot_for([100000, 100005])

        retraced_path = retained_then_retraced["computed_features"]["windows"]["5s"]["price_path"]
        direct_path = direct["computed_features"]["windows"]["5s"]["price_path"]

        self.assertEqual(retained_then_retraced["computed_features"]["price_change_points"], "5")
        self.assertEqual(direct["computed_features"]["price_change_points"], "5")
        self.assertEqual(retraced_path["observation_count"], 6)
        self.assertEqual(retraced_path["basis"], "first_observed_trade")
        self.assertEqual(retraced_path["upward_excursion_ticks"], "4")
        self.assertEqual(retraced_path["buy_retracement_ticks"], "3")
        self.assertEqual(direct_path["upward_excursion_ticks"], "1")
        self.assertEqual(direct_path["buy_retracement_ticks"], "0")
        self.assertEqual(retraced_path["scope"], "complete")
        self.assertEqual(direct_path["scope"], "partial")
        self.assertIn("price_path", retained_then_retraced["computed_features"]["windows"]["previous_5s"])
        self.assertIn("price_path", retained_then_retraced["computed_features"]["windows"]["30s"])

        market = dict(retained_then_retraced, source_generation=1,
                      application_mode="excel_observation")
        candidate = dict(row("path"), hypotheses={"absorption": "Selling aggression fails to advance lower."})
        bundle = build_context(market, [candidate], engine_session_id="engine", market_session_id="session")
        state = bundle["state"]
        self.assertEqual(state["computed_features"]["windows"]["5s"]["price_path"], retraced_path)
        self.assertIn("ordem dos negócios", state["price_path_explanation"])
        self.assertIn("não inferem movimentos", state["price_path_explanation"])
        self.assertIn("price_path", bundle["questions"]["principal_choice"]["instructions"])
        self.assertTrue(all("price_path" in q["instructions"] for q in bundle["questions"].values()
                            if q["type"] == "noul"))

    def test_sell_path_is_mirrored_and_preserves_same_timestamp_order(self):
        market = snapshot_for([100000, 99995, 99990, 99985, 99980, 99995], same_timestamp=True)
        path = market["computed_features"]["windows"]["5s"]["price_path"]

        self.assertEqual(path["observation_count"], 6)
        self.assertEqual(path["downward_excursion_ticks"], "4")
        self.assertEqual(path["upward_excursion_ticks"], "0")
        self.assertEqual(path["sell_retracement_ticks"], "3")
        self.assertEqual(path["buy_retracement_ticks"], "1")

    def test_flat_empty_single_and_partial_windows_are_explicit(self):
        flat = snapshot_for([100000, 100000])["computed_features"]["windows"]["5s"]["price_path"]
        empty = snapshot_for([])["computed_features"]["windows"]["5s"]["price_path"]
        single = snapshot_for([100000])["computed_features"]["windows"]["5s"]["price_path"]

        self.assertEqual(flat["upward_excursion_ticks"], "0")
        self.assertEqual(flat["downward_excursion_ticks"], "0")
        self.assertEqual(flat["buy_retracement_ticks"], "0")
        self.assertEqual(flat["sell_retracement_ticks"], "0")
        self.assertEqual(empty["observation_count"], 0)
        self.assertEqual(single["observation_count"], 1)
        for path in (empty, single):
            self.assertEqual(path["scope"], "partial")
            for key in ("upward_excursion_ticks", "downward_excursion_ticks",
                        "buy_retracement_ticks", "sell_retracement_ticks"):
                self.assertIsNone(path[key])


if __name__ == "__main__":
    unittest.main()

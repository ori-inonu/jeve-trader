import json
import unittest
from dataclasses import dataclass
from copy import deepcopy

from flow_engine import FlowEngine, generate_flow_scenario


class FlowTests(unittest.TestCase):
    def load(self, mode="progression", side="buy"):
        fixture = generate_flow_scenario(mode, side=side)
        engine = FlowEngine(fixture["symbol"])
        engine.set_source_quality(fixture["source_quality"])
        for event in fixture["events"]:
            result = engine.add_trade(event) if event["type"] == "trade" else engine.set_book(event)
            self.assertTrue(result["accepted"], result)
        return engine, fixture

    def hypothesis(self, context, kind, side="buy"):
        return next(h for h in context["hypotheses"] if h["kind"] == kind and h["side"] == side)

    def trade(self, **overrides):
        return {"id": "a", "symbol": "WIN_SIM", "ts_ms": 10000, "price_points": "131000",
                "quantity": 10, "aggressor": "buy", **overrides}

    def book(self, ts=10000, qty=100, depth=2):
        return {"symbol": "WIN_SIM", "ts_ms": ts,
                "bids": [{"price_points": str(131000 - level * 5), "quantity": qty} for level in range(depth)],
                "asks": [{"price_points": str(131005 + level * 5), "quantity": qty} for level in range(depth)]}

    def test_exact_window_and_price_calculation(self):
        engine, fixture = self.load()
        context = engine.snapshot(fixture["now_ms"])
        current = context["computed_features"]
        self.assertEqual(current["trade_count"], 20)
        self.assertEqual(current["total_contracts"], 100)
        self.assertEqual(current["delta_contracts"], 100)
        self.assertEqual(current["contracts_per_second"], "20")
        self.assertEqual(current["price_change_points"], "25")
        self.assertEqual(current["spread_points"], "5")
        self.assertEqual(current["book_imbalance"], "0")
        self.assertTrue(context["evidence_coverage"]["long_window_complete"])
        self.assertEqual(self.hypothesis(context, "progression")["status"], "observed")
        self.assertEqual(self.hypothesis(context, "progression", "sell")["status"], "not_observed")
        json.dumps(context, allow_nan=False)

    def test_four_scenarios_and_symmetric_sell(self):
        for side in ("buy", "sell"):
            for mode, expected in (("progression", "observed"), ("absorption", "potential"), ("exhaustion", "potential")):
                engine, fixture = self.load(mode, side)
                self.assertEqual(self.hypothesis(engine.snapshot(fixture["now_ms"]), mode, side)["status"], expected)
        engine, fixture = self.load("choppy")
        context = engine.snapshot(fixture["now_ms"])
        self.assertEqual(self.hypothesis(context, "progression")["status"], "not_observed")
        self.assertEqual(self.hypothesis(context, "absorption")["status"], "not_observed")

    def test_unknown_aggressor_not_invented(self):
        engine, fixture = self.load()
        engine.add_trade(self.trade(id="unknown", ts_ms=fixture["now_ms"], aggressor="unknown", quantity=7))
        context = engine.snapshot(fixture["now_ms"])
        self.assertEqual(context["computed_features"]["unknown_aggressor_contracts"], 7)
        self.assertEqual(context["computed_features"]["delta_contracts"], 100)
        self.assertEqual(self.hypothesis(context, "progression")["status"], "inconclusive")

    def test_source_coverage_is_explicit(self):
        engine, fixture = self.load()
        engine.set_source_quality({"full_tape": False})
        context = engine.snapshot(fixture["now_ms"])
        self.assertEqual(self.hypothesis(context, "progression")["status"], "inconclusive")
        self.assertEqual(context["computed_features"]["total_contracts"], 100)
        engine.set_source_quality({"sequence_ok": False})
        engine.set_source_quality({"sequence_ok": True, "full_tape": True})
        self.assertFalse(engine.snapshot(fixture["now_ms"])["evidence_coverage"]["integrity_ok"])

    def test_complete_flag_cannot_retroactively_upgrade_sampled_history(self):
        engine, fixture = self.load()
        engine.set_source_quality({"full_tape": False})
        engine.set_source_quality({"full_tape": True})
        context = engine.snapshot(fixture["now_ms"])
        self.assertFalse(context["evidence_coverage"]["short_window_complete"])
        engine.add_trade(self.trade(id="reconnected", ts_ms=fixture["now_ms"] + 1))
        self.assertFalse(engine.snapshot(fixture["now_ms"] + 1)["evidence_coverage"]["short_window_complete"])

    def test_dedup_and_conflicting_duplicate(self):
        engine = FlowEngine("WIN_SIM")
        self.assertTrue(engine.add_trade(self.trade())["accepted"])
        self.assertEqual(engine.add_trade(self.trade())["reason"], "DUPLICATE_TRADE")
        self.assertEqual(engine.snapshot(10000)["computed_features"]["total_contracts"], 10)
        self.assertTrue(engine.snapshot(10000)["evidence_coverage"]["integrity_ok"])
        self.assertEqual(engine.add_trade(self.trade(quantity=11))["reason"], "CONFLICTING_TRADE_ID")
        self.assertFalse(engine.snapshot(10000)["evidence_coverage"]["integrity_ok"])

    def test_bad_financial_data_and_types(self):
        bad = ({"price_points": "NaN"}, {"price_points": "Infinity"}, {"price_points": "1e99999"},
               {"price_points": "131001"}, {"price_points": True}, {"quantity": True}, {"quantity": 0},
               {"quantity": -1}, {"quantity": 1.5}, {"ts_ms": -1}, {"ts_ms": True}, {"id": None}, {"aggressor": "guess"})
        for values in bad:
            engine = FlowEngine("WIN_SIM")
            self.assertEqual(engine.add_trade(self.trade(**values))["reason"], "INVALID_TRADE", values)
            self.assertEqual(len(engine.trades), 0)
        with self.assertRaises(ValueError):
            FlowEngine("WIN_SIM", tick_points="NaN")

    def test_out_of_order_future_and_snapshot_clock(self):
        engine = FlowEngine("WIN_SIM")
        engine.add_trade(self.trade(ts_ms=10000))
        self.assertEqual(engine.add_trade(self.trade(id="b", ts_ms=9999))["reason"], "OUT_OF_ORDER_TRADE")
        context = engine.snapshot(9000)
        self.assertEqual(context["computed_features"]["total_contracts"], 0)
        self.assertIn("STALE_OR_FUTURE_TAPE", context["evidence_coverage"]["reasons"])
        with self.assertRaises(ValueError):
            engine.snapshot(8999)
        for now in (True, -1, "9000"):
            with self.assertRaises(ValueError):
                engine.snapshot(now)

    def test_stale_data_and_symbol_reset(self):
        engine, fixture = self.load()
        context = engine.snapshot(fixture["now_ms"] + 2001)
        self.assertIsNone(context["bid_points"])
        self.assertEqual(self.hypothesis(context, "progression")["status"], "inconclusive")
        engine.reset("WINZ26")
        self.assertFalse(engine.add_trade(self.trade())["accepted"])
        self.assertTrue(engine.add_trade(self.trade(symbol="WINZ26"))["accepted"])
        self.assertEqual(len(engine.trades), 1)
        self.assertTrue(engine.snapshot(10000)["evidence_coverage"]["integrity_ok"])

    def test_memory_bounded_and_truncated_windows(self):
        engine = FlowEngine("WIN_SIM", max_trades=5, max_books=3)
        engine.set_source_quality({"feed_connected": True, "sequence_ok": True, "full_tape": True})
        for index in range(100):
            engine.add_trade(self.trade(id=str(index), ts_ms=index * 100, quantity=1))
            engine.set_book(self.book(index * 100))
        self.assertEqual(len(engine.trades), 5)
        self.assertEqual(len(engine.ids), 5)
        self.assertEqual(len(engine.books), 3)
        self.assertFalse(engine.snapshot(9900)["evidence_coverage"]["short_window_complete"])
        engine.snapshot(80000)
        self.assertEqual(len(engine.trades), 0)
        self.assertEqual(len(engine.ids), 0)
        self.assertEqual(len(engine.books), 0)

    def test_book_validation_and_depth_not_inferred_from_top(self):
        engine = FlowEngine("WIN_SIM")
        engine.set_source_quality({"feed_connected": True, "sequence_ok": True})
        engine.set_book(self.book(10000, 100, 1))
        engine.set_book(self.book(10100, 10, 1))
        context = engine.snapshot(10100)
        self.assertEqual(self.hypothesis(context, "liquidity_withdrawal", "bids")["status"], "inconclusive")
        bad_book = self.book(10200)
        bad_book["asks"][0]["price_points"] = "131000"
        self.assertEqual(engine.set_book(bad_book)["reason"], "INVALID_BOOK")

    def test_depth_reduction_describes_no_identity_or_cause(self):
        engine = FlowEngine("WIN_SIM")
        engine.set_source_quality({"feed_connected": True, "sequence_ok": True})
        engine.set_book(self.book(10000, 100))
        engine.set_book(self.book(10100, 20))
        context = engine.snapshot(10100)
        hypothesis = self.hypothesis(context, "liquidity_withdrawal", "asks")
        self.assertEqual(hypothesis["status"], "potential")
        self.assertEqual(hypothesis["evidence"]["displayed_quantity_reduction_fraction"], "0.8")
        self.assertFalse(context["evidence_coverage"]["cancellation_causes_known"])
        book = self.book(10200, 1)
        for side in ("bids", "asks"):
            for level in book[side]:
                level["price_points"] = str(int(level["price_points"]) + 5)
        engine.set_book(book)
        self.assertEqual(self.hypothesis(engine.snapshot(10200), "liquidity_withdrawal", "asks")["status"], "inconclusive")

    def test_inputs_not_mutated_and_dataclass_bridge(self):
        @dataclass
        class Event:
            trade_id: str = "bridge"
            symbol: str = "WIN_SIM"
            ts_ms: int = 10000
            price_points: float = 131000.0
            quantity: int = 1
            aggressor: str = "BUY"
        event = Event()
        engine = FlowEngine("WIN_SIM")
        self.assertTrue(engine.add_trade(event)["accepted"])
        self.assertEqual(event.aggressor, "BUY")
        book = self.book(10000)
        original = deepcopy(book)
        engine.set_book(book)
        self.assertEqual(book, original)


if __name__ == "__main__":
    unittest.main()

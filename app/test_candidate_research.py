from copy import deepcopy
import json
import unittest

from app_core import DEFAULT_INPUTS, build_risk_study
from candidate_research import build_market_candidates, generate_candidate_scenario
from flow_engine import FlowEngine


class CandidateResearchTests(unittest.TestCase):
    def test_technical_scenario_has_observed_geometry_and_financially_allowed_row(self):
        fixture = generate_candidate_scenario()
        engine = FlowEngine(fixture["symbol"])
        engine.set_source_quality(fixture["source_quality"])
        for event in fixture["events"]:
            outcome = engine.add_trade(event) if event["type"] == "trade" else engine.set_book(event)
            self.assertTrue(outcome["accepted"])
        snapshot = engine.snapshot(fixture["now_ms"])
        study = build_risk_study(DEFAULT_INPUTS, now_ms=fixture["now_ms"])
        result = build_market_candidates(engine, snapshot, study["config"], study["account"], fixture["now_ms"])
        self.assertEqual(len(result["rows"]), 8)
        self.assertTrue(any(row["lots"] >= 1 and row["risk"]["status"] == "ALLOW_SIMULATION" for row in result["rows"]))
        actual_prices = {event["price_points"] for event in fixture["events"] if event["type"] == "trade"}
        self.assertTrue(all(level["price_points"] in actual_prices for level in result["reference_levels"]))
        self.assertTrue(all(level["touches"] >= 2 for level in result["reference_levels"]))
        self.assertTrue(fixture["synthetic"])
        self.assertFalse(fixture["exchange_data"])
        self.assertEqual(fixture, generate_candidate_scenario())

    def fixture(self):
        now = 1801848600000
        engine = FlowEngine("WIN_SIM")
        engine.set_source_quality({"feed_connected": True, "sequence_ok": True, "full_tape": True, "data_origin": "synthetic"})
        # Observed range, then a quote inside that range; no fabricated far levels.
        for index, price in enumerate((130800, 130800, 130900, 130900, 131100, 131100, 131200, 131200)):
            engine.add_trade({"id": str(index), "symbol": "WIN_SIM", "ts_ms": now - 10000 + index * 1000,
                              "price_points": str(price), "quantity": 3, "aggressor": "buy"})
        engine.set_book({"symbol": "WIN_SIM", "ts_ms": now,
                         "bids": [{"price_points": "131000", "quantity": 50}],
                         "asks": [{"price_points": "131005", "quantity": 50}]})
        snapshot = engine.snapshot(now)
        study = build_risk_study(dict(DEFAULT_INPUTS, start="4000", current="4000", peak="4000"), now_ms=now)
        return engine, snapshot, study, now

    def build(self, fixture):
        engine, snapshot, study, now = fixture
        return build_market_candidates(engine, snapshot, study["config"], study["account"], now)

    def test_bounded_pairs_geometry_and_exact_evidence(self):
        fixture = self.fixture()
        result = self.build(fixture)
        self.assertEqual(result["status"], "TECHNICAL_SCENARIOS")
        self.assertEqual(len(result["rows"]), 8)
        self.assertEqual(result["evidence_coverage"]["quote_source"], "retained_book")
        for row in result["rows"]:
            entry, stop, target = (float(row[key]) for key in ("entry_points", "stop_points", "target_points"))
            self.assertTrue(stop < entry < target if row["side"] == "buy" else target < entry < stop)
            self.assertEqual(len(row["reference_levels"]), 2)
            self.assertEqual(row["reference_evidence_ids"], [level["evidence_id"] for level in row["reference_levels"]])
            self.assertFalse(row["actionable_live_signal"])
            self.assertIsNone(row["win_probability"])
        self.assertIsNone(result["ranking"])
        json.dumps(result, allow_nan=False)

    def test_sampled_quote_requires_timestamp_and_is_labeled(self):
        engine, snapshot, study, now = self.fixture()
        engine.books.clear()
        snapshot["last_quote"] = {"symbol": "WIN_SIM", "ts_ms": now, "bid": 131000, "ask": 131005}
        result = self.build((engine, snapshot, study, now))
        self.assertEqual(len(result["rows"]), 8)
        self.assertEqual(result["evidence_coverage"]["quote_source"], "sampled_quote")
        self.assertFalse(result["evidence_coverage"]["sampled_quote_is_authoritative_book"])
        for stamp in (None, now + 1, now - 2001, True):
            snapshot["last_quote"]["ts_ms"] = stamp
            result = self.build((engine, snapshot, study, now))
            self.assertEqual(result["rows"], [])
            self.assertIn("FRESH_TWO_SIDED_QUOTE_REQUIRED", result["reasons"])

    def test_future_and_old_trades_are_never_reference_levels(self):
        engine, snapshot, study, now = self.fixture()
        engine.add_trade({"id": "future", "symbol": "WIN_SIM", "ts_ms": now + 1000,
                          "price_points": "132000", "quantity": 9999, "aggressor": "buy"})
        result = self.build((engine, snapshot, study, now))
        self.assertNotIn("132000", [level["price_points"] for level in result["reference_levels"]])
        self.assertTrue(all(level["asof_ms"] <= now for level in result["reference_levels"]))
        self.assertEqual(result["evidence_coverage"]["future_events_excluded"], 1)
        engine.trades.appendleft({"id": "old", "symbol": "WIN_SIM", "ts_ms": now - 30001,
                                  "price_points": "125000", "quantity": 9999, "aggressor": "sell"})
        result = self.build((engine, snapshot, study, now))
        self.assertNotIn("125000", [level["price_points"] for level in result["reference_levels"]])

    def test_missing_levels_and_same_price_do_not_manufacture_targets(self):
        engine, snapshot, study, now = self.fixture()
        engine.trades.clear()
        result = self.build((engine, snapshot, study, now))
        self.assertEqual(result["rows"], [])
        self.assertIn("OBSERVED_REFERENCE_LEVELS_REQUIRED", result["reasons"])
        for index in range(5):
            engine.trades.append({"id": str(index), "symbol": "WIN_SIM", "ts_ms": now - 500 + index * 100,
                                  "price_points": "131000", "quantity": 10, "aggressor": "buy"})
        result = self.build((engine, snapshot, study, now))
        self.assertEqual(len(result["reference_levels"]), 1)
        self.assertEqual(result["rows"], [])
        self.assertIn("OBSERVED_LEVELS_DO_NOT_FORM_STOP_TARGET_GEOMETRY", result["reasons"])

    def test_structural_geometry_stays_fixed_when_margin_blocks(self):
        fixture = self.fixture()
        baseline = self.build(fixture)
        engine, snapshot, study, now = fixture
        study["account"]["available_margin_brl"] = "1"
        blocked = self.build(fixture)
        self.assertEqual([(r["entry_points"], r["stop_points"], r["target_points"]) for r in baseline["rows"]],
                         [(r["entry_points"], r["stop_points"], r["target_points"]) for r in blocked["rows"]])
        self.assertTrue(all(row["lots"] == 0 for row in blocked["rows"]))
        self.assertTrue(all("INSUFFICIENT_MARGIN_AFTER_BUFFER" in row["reasons"] for row in blocked["rows"]))

    def test_account_is_not_refreshed_or_converted_to_simulated(self):
        engine, snapshot, study, now = self.fixture()
        for changes, reason in (({"asof_ms": now - 2001}, "STALE_OR_FUTURE_ACCOUNT"),
                                ({"environment": "live"}, "SIMULATED_ACCOUNT_REQUIRED")):
            account = {**study["account"], **changes}
            result = build_market_candidates(engine, snapshot, study["config"], account, now)
            self.assertTrue(all(reason in row["reasons"] and row["lots"] == 0 for row in result["rows"]))
            self.assertEqual(account, {**study["account"], **changes})

    def test_partial_capture_stays_explicit_and_inputs_unchanged(self):
        engine, snapshot, study, now = self.fixture()
        snapshot["evidence_coverage"]["source_quality"]["full_tape"] = False
        original = deepcopy((snapshot, study))
        result = self.build((engine, snapshot, study, now))
        self.assertFalse(result["evidence_coverage"]["flow_evidence"]["source_quality"]["full_tape"])
        self.assertFalse(result["evidence_coverage"]["levels_are_validated_support_resistance"])
        self.assertEqual(original, (snapshot, study))

    def test_quote_faults_and_integrity_fail_closed(self):
        engine, snapshot, study, now = self.fixture()
        engine.books.clear()
        for quote in ({"symbol": "OTHER", "ts_ms": now, "bid": 131000, "ask": 131005},
                      {"symbol": "WIN_SIM", "ts_ms": now, "bid": "NaN", "ask": 131005},
                      {"symbol": "WIN_SIM", "ts_ms": now, "bid": 131005, "ask": 131000},
                      {"symbol": "WIN_SIM", "ts_ms": now, "bid": 131001, "ask": 131005}):
            snapshot["last_quote"] = quote
            self.assertEqual(self.build((engine, snapshot, study, now))["rows"], [])
        snapshot["evidence_coverage"]["integrity_ok"] = False
        self.assertIn("MARKET_EVENT_INTEGRITY_REQUIRED", self.build((engine, snapshot, study, now))["reasons"])

    def test_previous_extrema_keep_actual_event_timestamps(self):
        engine, snapshot, study, now = self.fixture()
        result = self.build((engine, snapshot, study, now))
        extrema = [level for level in result["reference_levels"] if "previous_5s_low" in level["roles"] or "previous_5s_high" in level["roles"]]
        self.assertTrue(extrema)
        self.assertTrue(all(level["asof_ms"] < now and level["first_observed_ms"] <= level["asof_ms"] for level in extrema))


if __name__ == "__main__":
    unittest.main()

from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

from candidate_engine import generate_candidates
from copilot import Copilot, ROOT, demo_snapshot, load_json, prepare_batch, profile_config


class CopilotTests(unittest.TestCase):
    def setUp(self):
        self.config = load_json(ROOT / "config.json")
        self.questions = load_json(ROOT / "questions.json")
        self.snapshot = demo_snapshot()
        self.now = self.snapshot["account"]["asof_ms"]

    def engine(self, profile="agressivo_pesquisa"):
        return Copilot(profile_config(self.config, profile), self.questions)

    def test_control_does_not_stretch_stop_to_fit_400(self):
        result = self.engine("controle").process(self.snapshot, self.now)
        self.assertEqual(result["status"], "WAIT")
        self.assertNotIn("model_response", result)
        self.assertFalse(result["actionable_live_signal"])

    def test_aggressive_example_is_still_research_not_a_live_signal(self):
        result = self.engine().process(self.snapshot, self.now)
        self.assertEqual(result["status"], "SIMULATION_REVIEW")
        self.assertEqual(result["provider"], "SYNTHETIC_TEST_FIXTURE")
        self.assertIsNone(result["win_probability"])
        self.assertFalse(result["order_sent"])
        self.assertEqual(result["candidates_for_review"][0]["side"], "buy")

    def test_profile_does_not_increase_size_to_recover_loss(self):
        first = self.engine().process(self.snapshot, self.now)
        after = self.engine().process(demo_snapshot(loss="-20"), self.now)
        self.assertLessEqual(after["candidates_for_review"][0]["contracts"],
                             first["candidates_for_review"][0]["contracts"])

    def test_stale_flow_independently_blocks_fresh_quote(self):
        self.snapshot["flow_ts_ms"] -= 1001
        result = self.engine().process(self.snapshot, self.now)
        self.assertIn("STALE_OR_FUTURE_FLOW_TS_MS", result["reasons"])

    def test_no_live_origin_can_be_enabled_by_config(self):
        self.snapshot["data_origin"] = "live"
        result = self.engine().process(self.snapshot, self.now)
        self.assertIn("OFFLINE_RESEARCH_ONLY", result["reasons"])

    def test_deduplication(self):
        engine = self.engine()
        engine.process(self.snapshot, self.now)
        result = engine.process(self.snapshot, self.now)
        self.assertIn("DUPLICATE_OR_OUT_OF_ORDER_SNAPSHOT", result["reasons"])

    def test_no_account_or_loss_history_in_jev_state(self):
        state, questions = prepare_batch(self.snapshot, self.snapshot["candidates"], self.questions)
        self.assertNotIn("account", state)
        self.assertNotIn("equity_brl", str(state))
        self.assertEqual(len(questions), 5)
        self.assertIn("candidate_setups[1]", str(questions["setup_evidence_support_1"]))

    def test_real_elapsed_time_invalidates_old_inference(self):
        with patch("copilot.time.monotonic", side_effect=[1.0, 3.0]):
            result = self.engine().process(self.snapshot, self.now)
        self.assertEqual(result["status"], "WAIT")
        self.assertIn("INFERENCE_EXPIRED", result["reasons"])

    def test_quote_change_makes_entry_unusable(self):
        for candidate in self.snapshot["candidates"]:
            candidate["entry_points"] += 5
        result = self.engine().process(self.snapshot, self.now)
        self.assertEqual(result["status"], "WAIT")

    def test_missing_observations_fail_closed(self):
        del self.snapshot["observations"]
        result = self.engine().process(self.snapshot, self.now)
        self.assertEqual(result["status"], "WAIT")

    def test_missing_account_and_non_object_root_return_wait(self):
        del self.snapshot["account"]
        self.assertEqual(self.engine().process(self.snapshot, self.now)["status"], "WAIT")
        self.assertEqual(self.engine().process([], self.now)["status"], "WAIT")

    def test_expiration_respects_account_age(self):
        self.snapshot["account"]["asof_ms"] = self.now - 1900
        result = self.engine().process(self.snapshot, self.now)
        self.assertEqual(result["status"], "SIMULATION_REVIEW")
        self.assertEqual(result["expires_at_ms"], self.now + 100)
        self.assertEqual(result["data_origin"], "synthetic")

    def test_level_references_reach_jev(self):
        self.snapshot["reference_levels"] = [
            {"price_points": 130910, "evidence_id": "support-a", "asof_ms": self.now,
             "description": "Synthetic repeated executions without lower price progress"},
            {"price_points": 131210, "evidence_id": "resistance-b", "asof_ms": self.now}
        ]
        candidates = generate_candidates(self.snapshot)
        state, _ = prepare_batch(self.snapshot, candidates, self.questions)
        self.assertEqual(len(state["reference_levels"]), 2)
        self.assertTrue(state["candidate_setups"][0]["premise_is_hypothesis"])

    def test_unknown_event_calendar_is_not_clear(self):
        self.snapshot["event_risk_blocked"] = None
        self.assertIn("EVENT_RISK_OR_UNKNOWN", self.engine().process(self.snapshot, self.now)["reasons"])

    def test_negative_or_nan_nested_features_fail_closed(self):
        self.snapshot["computed_features"]["bad"] = float("nan")
        self.assertEqual(self.engine().process(self.snapshot, self.now)["status"], "WAIT")


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = demo_snapshot()
        self.snapshot["reference_levels"] = [
            {"price_points": price, "evidence_id": f"level-{i}", "asof_ms": self.snapshot["ts_ms"] - 100}
            for i, price in enumerate([130805, 130910, 131095, 131210])
        ]

    def test_finite_comparison_produces_eight_valid_price_pairs(self):
        candidates = generate_candidates(self.snapshot, quantity_requested=2)
        self.assertEqual(len(candidates), 8)
        for candidate in candidates:
            entry, stop, target = (float(candidate[key]) for key in ("entry_points", "stop_points", "target_points"))
            self.assertTrue(stop < entry < target if candidate["side"] == "buy" else target < entry < stop)
            self.assertTrue(all(value % 5 == 0 for value in (entry, stop, target)))

    def test_does_not_use_future_levels(self):
        self.snapshot["reference_levels"][0]["asof_ms"] += 101
        with self.assertRaises(ValueError):
            generate_candidates(self.snapshot)

    def test_does_not_invent_levels_when_absent(self):
        del self.snapshot["reference_levels"]
        self.assertEqual(generate_candidates(self.snapshot), [])

    def test_stops_do_not_depend_on_account_balance(self):
        first = generate_candidates(self.snapshot)
        self.snapshot["account"]["equity_brl"] = "1000000"
        self.assertEqual(first, generate_candidates(self.snapshot))


if __name__ == "__main__":
    unittest.main()

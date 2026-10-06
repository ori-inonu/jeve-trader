from copy import deepcopy
import json
import unittest

from app_core import DEFAULT_INPUTS, build_risk_study, ObservationSession, jev_observation_state
from candidate_research import build_market_candidates, generate_candidate_scenario
from flow_engine import FlowEngine
from recommendation_engine import build_recommendation


class RecommendationTests(unittest.TestCase):
    def fixture(self):
        fixture = generate_candidate_scenario()
        engine = FlowEngine("WIN_SIM")
        engine.set_source_quality(fixture["source_quality"])
        for event in fixture["events"]:
            (engine.add_trade if event["type"] == "trade" else engine.set_book)(event)
        now = fixture["now_ms"]
        snapshot = engine.snapshot(now)
        snapshot.update(application_mode="synthetic", source_generation=1)
        study = build_risk_study(DEFAULT_INPUTS, now_ms=now)
        technical = build_market_candidates(engine, snapshot, study["config"], study["account"], now)
        state = jev_observation_state(snapshot)
        state["source_generation"] = 1
        state["candidate_setups"] = [{key: row[key] for key in ("id", "side", "entry_points", "stop_points", "target_points", "reference_levels")}
                                      for row in technical["rows"] if row["risk"]["status"] == "ALLOW_SIMULATION"]
        answers = {"flow_context": {"type": "choice", "choice": "buy_progression", "confidence": 0.1}}
        for index, setup in enumerate(state["candidate_setups"]):
            answers[f"candidate_{index}_support"] = {"type": "noul", "noul": 0.8}
            answers[f"candidate_{index}_contradiction"] = {"type": "noul", "noul": 0.2}
        model = {"response": {"answers": answers}, "state": state, "source_ts_ms": now, "flow_ts_ms": now, "mode": "synthetic"}
        return snapshot, technical, study, model, now

    def build(self, values):
        snapshot, technical, study, model, now = values
        return build_recommendation(snapshot, technical, study, model, now)

    def test_current_complete_synthetic_evidence_review_without_optimal_claim(self):
        values = self.fixture()
        original = deepcopy(values)
        result = self.build(values)
        self.assertEqual(result["status"], "HIPOTESE_PARA_REVISAO")
        self.assertTrue(result["review_candidate_ids"])
        self.assertTrue(all(option["side"] == "buy" for option in result["options"] if option["status"] == "HIPOTESE_PARA_REVISAO"))
        self.assertFalse(result["actionable_live_signal"])
        self.assertFalse(result["order_sent"])
        self.assertTrue(result["model"]["descriptive_only"])
        self.assertIsNone(result["win_probability"])
        self.assertIsNone(result["optimal_configuration"])
        self.assertIsNone(result["ranking"])
        self.assertEqual(result["model"]["classification_confidence"], 0.1)  # No invented .65 gate.
        self.assertEqual(values, original)
        json.dumps(result, allow_nan=False)

    def test_no_data_invalid_form_and_malformed_inputs_do_not_crash(self):
        result = build_recommendation(None, None, None, None, 1000)
        self.assertEqual(result["status"], "SEM_DADOS")
        snapshot, report, _, model, now = self.fixture()
        result = build_recommendation(snapshot, report, None, model, now)
        self.assertEqual(result["status"], "BLOQUEADO_RISCO")
        self.assertIn("EXPLICIT_MANUAL_SCENARIO_REQUIRED", result["reasons"])
        for changed in ({"evidence_coverage": None}, {"computed_features": None}, {"evidence_coverage": {"source_quality": None}}):
            result = build_recommendation({**snapshot, **changed}, report, None, model, now)
            self.assertNotEqual(result["status"], "HIPOTESE_PARA_REVISAO")

    def test_partial_feed_preserves_descriptive_model_but_waits(self):
        snapshot, report, study, model, now = self.fixture()
        snapshot["evidence_coverage"]["source_quality"]["full_tape"] = False
        result = self.build((snapshot, report, study, model, now))
        self.assertEqual(result["status"], "AGUARDAR")
        self.assertTrue(result["model"]["available"])
        self.assertTrue(result["options"])
        self.assertIn("COMPLETE_TAPE_SOURCE_NOT_VERIFIED", result["missing_evidence"])
        self.assertEqual(result["review_candidate_ids"], [])

    def test_financial_veto_wins_even_when_model_claims_perfect_support(self):
        snapshot, report, study, model, now = self.fixture()
        for changes in ({"available_margin_brl": "1"}, {"asof_ms": now - 2001}, {"environment": "live"},
                        {"reconciled": False}, {"equity_brl": "NaN"}):
            modified = deepcopy(study)
            modified["account"].update(changes)
            result = self.build((snapshot, report, modified, model, now))
            self.assertEqual(result["status"], "BLOQUEADO_RISCO", changes)
            self.assertEqual(result["review_candidate_ids"], [])
            self.assertTrue(all(option["contracts"] == 0 for option in result["options"]))

    def test_risk_recomputed_instead_of_trusting_cached_lots(self):
        snapshot, report, study, model, now = self.fixture()
        for row in report["rows"]:
            row["lots"] = 999999
            row["risk"] = {"status": "ALLOW_SIMULATION", "contracts": 999999}
        result = self.build((snapshot, report, study, model, now))
        self.assertTrue(all(option["contracts"] <= 2 for option in result["options"]))

    def test_original_source_clocks_expire_without_refresh(self):
        snapshot, report, study, model, now = self.fixture()
        # Keep the manual account fresh; expired tape/quote cannot be renewed by
        # an account refresh or a recent model response.
        study["account"]["asof_ms"] = now + 2001
        result = self.build((snapshot, report, study, model, now + 2001))
        self.assertEqual(result["status"], "AGUARDAR")
        self.assertIn("STALE_OR_FUTURE_TAPE", result["missing_evidence"])
        self.assertIn("FRESH_TWO_SIDED_QUOTE_REQUIRED", result["missing_evidence"])
        self.assertFalse(result["model"]["current"])
        self.assertEqual(result["expires_at_ms"], now + 2000)

    def test_old_generation_wrong_mode_wrong_symbol_and_future_model_rejected(self):
        values = self.fixture()
        for update in ({"source_generation": 0}, {"mode": "replay"}, {"flow_ts_ms": values[-1] + 1}):
            model = {**values[3], **update}
            result = self.build((*values[:3], model, values[-1]))
            self.assertFalse(result["model"]["current"])
            self.assertEqual(result["review_candidate_ids"], [])
        model = deepcopy(values[3])
        model["state"]["instrument"] = "OTHER"
        self.assertFalse(self.build((*values[:3], model, values[-1]))["model"]["current"])
        model = deepcopy(values[3])
        model["source_ts_ms"] -= 100
        model["state"]["asof_ms"] -= 100
        result = self.build((*values[:3], model, values[-1]))
        self.assertIn("JEV_SOURCE_AFTER_REFERENCE_CLOCK", result["model"]["reasons"])

    def test_geometry_and_reference_forgery_cannot_become_supported_option(self):
        snapshot, report, study, model, now = self.fixture()
        allowed = next(row for row in report["rows"] if row["side"] == "buy" and row["risk"]["status"] == "ALLOW_SIMULATION")
        identity = allowed["id"]
        allowed["reference_levels"][0]["price_points"] = "120000"
        result = self.build((snapshot, report, study, model, now))
        option = next(option for option in result["options"] if option["id"] == identity)
        self.assertIn("STRUCTURAL_LEVEL_GEOMETRY_MISMATCH", option["reasons"])
        self.assertNotEqual(option["status"], "HIPOTESE_PARA_REVISAO")
        allowed["reference_levels"][0]["asof_ms"] = now + 1
        result = self.build((snapshot, report, study, model, now))
        option = next(option for option in result["options"] if option["id"] == identity)
        self.assertIn("CURRENT_OBSERVED_LEVEL_EVIDENCE_REQUIRED", option["reasons"])

    def test_flow_only_model_is_not_invented_candidate_support(self):
        snapshot, report, study, model, now = self.fixture()
        model["state"]["candidate_setups"] = []
        result = self.build((snapshot, report, study, model, now))
        self.assertEqual(result["status"], "AGUARDAR")
        self.assertTrue(result["model"]["available"])
        self.assertTrue(all(option["model_evidence"] is None for option in result["options"]))

    def test_contradiction_tie_and_mixed_context_are_visible(self):
        snapshot, report, study, model, now = self.fixture()
        for key, value in model["response"]["answers"].items():
            if key.endswith("_contradiction"):
                value["noul"] = 0.8
        result = self.build((snapshot, report, study, model, now))
        self.assertEqual(result["status"], "AGUARDAR")
        self.assertTrue(any(reason.startswith("MODEL_CONTRADICTION_NOT_LESS_THAN_SUPPORT") for reason in result["contradictions"]))
        model["response"]["answers"]["flow_context"]["choice"] = "mixed_or_insufficient"
        result = self.build((snapshot, report, study, model, now))
        self.assertIn("MODEL_CONTEXT_MIXED_OR_INSUFFICIENT", result["contradictions"])

    def test_nans_and_missing_candidate_evidence_fail_closed(self):
        snapshot, report, study, model, now = self.fixture()
        model["response"]["answers"]["flow_context"]["confidence"] = float("nan")
        result = self.build((snapshot, report, study, model, now))
        self.assertFalse(result["model"]["available"])
        json.dumps(result, allow_nan=False)
        result = build_recommendation(snapshot, report, study, None, now)
        self.assertIn("JEV_NOT_EVALUATED", result["reasons"])
        self.assertEqual(result["status"], "AGUARDAR")

    def test_account_expiry_can_be_earlier_than_quote_expiry(self):
        snapshot, report, study, model, now = self.fixture()
        study["account"]["asof_ms"] = now - 1500
        result = self.build((snapshot, report, study, model, now))
        self.assertEqual(result["expires_at_ms"], now + 500)


if __name__ == "__main__":
    unittest.main()

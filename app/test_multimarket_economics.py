import unittest

from multimarket_economics import payoff


class PayoffTests(unittest.TestCase):
    def test_payoff_families_use_exact_decimal_scenarios(self):
        future = payoff(
            "linear_future", quantity="2.5", entry_price="100",
            exit_price="104", side="buy", multiplier="3.2",
        )
        self.assertEqual(future["gross_pnl"], "32")
        self.assertIsNone(future["maximum_loss"])

        back = payoff("back", quantity="100", odds="5", outcome="win")
        self.assertEqual(back["gross_pnl"], "400")
        self.assertEqual(payoff("back", quantity="100", odds="5", outcome="lose")["gross_pnl"], "-100")
        self.assertEqual(payoff("back", quantity="100", odds="5", outcome="void")["gross_pnl"], "0")

        lay = payoff("lay", quantity="100", odds="5", outcome="win")
        self.assertEqual(lay["gross_pnl"], "-400")
        self.assertEqual(lay["liability"], "400")
        self.assertEqual(payoff("lay", quantity="100", odds="5", outcome="lose")["gross_pnl"], "100")

        binary = payoff("binary", quantity="100", net_payout="0.8", outcome="win")
        self.assertEqual(binary["gross_pnl"], "80")
        self.assertEqual(payoff("binary", quantity="100", net_payout="0.8", outcome="lose")["gross_pnl"], "-100")
        self.assertEqual(payoff("binary", quantity="100", net_payout="0.8", outcome="void")["gross_pnl"], "0")

    def test_inverse_payoff_is_explicitly_unsupported(self):
        result = payoff("inverse_future", quantity="1", entry_price="10", exit_price="12")
        self.assertEqual(result["gross_pnl"], None)
        self.assertIn("unsupported", result["missing"])

    def test_future_requires_an_explicit_multiplier(self):
        with self.assertRaises(ValueError):
            payoff("linear_future", quantity="1", entry_price="10", exit_price="12")

    def test_long_decimal_outputs_are_not_rounded_by_decimal_string_formatting(self):
        result = payoff("spot", quantity="10000000000000000000000000000", entry_price="0.1", exit_price="0.2")
        self.assertEqual(result["gross_pnl"], "1000000000000000000000000000")

    def test_decimal_inputs_reject_float_boolean_and_nonfinite_values(self):
        for value in (1.2, True, "NaN", "Infinity", "-1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                payoff("spot", quantity="1", entry_price=value, exit_price="2")


class CandidateAssessmentTests(unittest.TestCase):
    def test_incomplete_candidate_keeps_wait_and_never_invents_probabilities(self):
        from multimarket_economics import assess_candidates

        result = assess_candidates(
            [{"candidate_id": "btc", "instrument": {"settlement_currency": "USD"}, "quantity": "1"}],
            capital="400", currency="BRL", as_of_ms=200,
        )
        self.assertEqual(result["status"], "not_evaluable")
        self.assertEqual(result["wait"]["quantity"], "0")
        self.assertEqual(result["selected"], result["wait"])
        self.assertIsNone(result["profit_probability"])
        self.assertIsNone(result["target_probability"])
        self.assertIsNone(result["ruin_probability"])
        self.assertEqual(result["admissible"], [])
        self.assertIn("costs", result["missing"])
        for gate in ("fx", "executable_quote", "liquidity", "risk_mandate", "product_gate", "authorization_gate", "coverage"):
            self.assertIn(gate, result["missing"])

    def test_complete_synthetic_scenario_is_admissible_but_not_ranked_as_a_bet(self):
        from multimarket_economics import assess_candidates

        candidate = {
            "candidate_id": "fixture-spot",
            "instrument": {"kind": "spot", "settlement_currency": "BRL"},
            "quantity": "1",
            "payoff": payoff("spot", quantity="1", entry_price="10", exit_price="11"),
            "costs": {"amount": "0", "currency": "BRL", "method": "explicit_zero", "base": "one_trade", "as_of_ms": 190, "source": "synthetic_fixture"},
            "fx": None,
            "executable_quote": {"status": "executable", "price": "10", "as_of_ms": 195, "max_age_ms": 20, "source": "synthetic_fixture"},
            "liquidity": {"status": "sufficient", "max_quantity": "2", "as_of_ms": 190, "source": "synthetic_fixture"},
            "risk_mandate": {"status": "approved", "max_loss": "10", "currency": "BRL", "as_of_ms": 190, "source": "synthetic_fixture"},
            "product_gate": {"status": "approved", "as_of_ms": 190, "source": "synthetic_fixture"},
            "authorization_gate": {"status": "approved", "as_of_ms": 190, "source": "synthetic_fixture"},
            "coverage": {"status": "complete", "full_tape": True, "origin": "synthetic", "as_of_ms": 190, "source": "synthetic_fixture"},
            "as_of_ms": 190,
        }
        result = assess_candidates([candidate], capital="400", currency="BRL", as_of_ms=200)
        self.assertEqual(result["status"], "scenario_comparison_only")
        self.assertEqual(result["admissible"], ["fixture-spot"])
        self.assertEqual(result["selected"], result["wait"])
        self.assertEqual(result["wait"]["quantity"], "0")
        self.assertIsNone(result["target_probability"])
        self.assertEqual(result["candidates"][0]["scenario_net_pnl"], "1")
        gate_blocked = {
            **candidate,
            "candidate_id": "blocked-quote",
            "executable_quote": None,
        }
        gate_blocked_result = assess_candidates([gate_blocked], capital="400", currency="BRL", as_of_ms=200)
        self.assertEqual(gate_blocked_result["candidates"][0]["status"], "blocked")
        self.assertIsNone(gate_blocked_result["candidates"][0]["scenario_net_pnl"])
        implicit_zero = {
            **candidate,
            "candidate_id": "implicit-zero",
            "costs": {**candidate["costs"], "method": "unspecified_zero"},
        }
        implicit_zero_result = assess_candidates([implicit_zero], capital="400", currency="BRL", as_of_ms=200)
        self.assertEqual(implicit_zero_result["status"], "not_evaluable")
        self.assertIn("zero_cost_not_explicit", implicit_zero_result["candidates"][0]["missing"])
        historical = {
            **candidate,
            "candidate_id": "fixture-backtest",
            "coverage": {**candidate["coverage"], "origin": "backtest"},
        }
        historical_result = assess_candidates([historical], capital="400", currency="BRL", as_of_ms=200)
        self.assertEqual(historical_result["status"], "not_evaluable")
        self.assertEqual(historical_result["admissible"], [])
        self.assertIsNone(historical_result["candidates"][0]["scenario_net_pnl"])
        self.assertIn("non_synthetic_scenario_comparison_disabled", historical_result["candidates"][0]["missing"])
        self.assertEqual(historical_result["selected"], historical_result["wait"])

    def test_fresh_fx_converts_synthetic_scenario_and_stale_fx_blocks(self):
        from multimarket_economics import assess_candidates

        candidate = {
            "candidate_id": "fx-synthetic", "instrument": {"settlement_currency": "USD"}, "quantity": "1",
            "payoff": payoff("spot", quantity="1", entry_price="10", exit_price="11"),
            "costs": {"amount": "0", "currency": "USD", "method": "explicit_zero", "base": "one_trade", "as_of_ms": 190, "source": "fixture"},
            "fx": {"pair": "USD/BRL", "rate": "5", "as_of_ms": 195, "max_age_ms": 10, "source": "fixture"},
            "executable_quote": {"status": "executable", "price": "10", "as_of_ms": 195, "max_age_ms": 20, "source": "fixture"},
            "liquidity": {"status": "sufficient", "max_quantity": "2", "as_of_ms": 190, "source": "fixture"},
            "risk_mandate": {"status": "approved", "max_loss": "10", "currency": "USD", "as_of_ms": 190, "source": "fixture"},
            "product_gate": {"status": "approved", "as_of_ms": 190, "source": "fixture"},
            "authorization_gate": {"status": "approved", "as_of_ms": 190, "source": "fixture"},
            "coverage": {"status": "complete", "full_tape": True, "origin": "synthetic", "as_of_ms": 190, "source": "fixture"},
            "as_of_ms": 190,
        }
        result = assess_candidates([candidate], capital="400", currency="BRL", as_of_ms=200)
        self.assertEqual(result["status"], "scenario_comparison_only")
        self.assertEqual(result["candidates"][0]["scenario_net_pnl"], "1")
        self.assertEqual(result["candidates"][0]["scenario_net_pnl_capital"], "5")

        stale = {**candidate, "fx": {**candidate["fx"], "as_of_ms": 100, "max_age_ms": 10}}
        stale_result = assess_candidates([stale], capital="400", currency="BRL", as_of_ms=200)
        self.assertEqual(stale_result["status"], "not_evaluable")
        self.assertIn("fx_stale", stale_result["candidates"][0]["missing"])
    def test_negative_payoff_is_a_valid_signed_scenario_not_missing_data(self):
        from multimarket_economics import assess_candidates

        candidate = {
            "candidate_id": "fixture-loss", "instrument": {"settlement_currency": "BRL"}, "quantity": "1",
            "payoff": {"kind": "spot", "currency": None, "gross_pnl": "-1", "maximum_loss": "10", "liability": None, "missing": [], "assumptions": []},
            "costs": {"amount": "0", "currency": "BRL", "method": "explicit_zero", "base": "one_trade", "as_of_ms": 190, "source": "fixture"},
            "executable_quote": {"status": "executable", "price": "10", "as_of_ms": 195, "max_age_ms": 20, "source": "fixture"},
            "liquidity": {"status": "sufficient", "max_quantity": "2", "as_of_ms": 190, "source": "fixture"},
            "risk_mandate": {"status": "approved", "max_loss": "10", "currency": "BRL", "as_of_ms": 190, "source": "fixture"},
            "product_gate": {"status": "approved", "as_of_ms": 190, "source": "fixture"},
            "authorization_gate": {"status": "approved", "as_of_ms": 190, "source": "fixture"},
            "coverage": {"status": "complete", "full_tape": True, "origin": "synthetic", "as_of_ms": 190, "source": "fixture"},
            "as_of_ms": 190,
        }
        result = assess_candidates([candidate], capital="400", currency="BRL", as_of_ms=200)
        self.assertEqual(result["admissible"], ["fixture-loss"])
        self.assertEqual(result["candidates"][0]["scenario_net_pnl"], "-1")
    def test_stale_quote_blocks_candidate_even_when_other_inputs_are_declared(self):
        from multimarket_economics import assess_candidates

        candidate = {
            "candidate_id": "stale",
            "instrument": {"kind": "spot", "settlement_currency": "BRL"},
            "quantity": "1",
            "payoff": payoff("spot", quantity="1", entry_price="10", exit_price="11"),
            "costs": {"amount": "0", "currency": "BRL", "method": "explicit_zero", "base": "one_trade", "as_of_ms": 190, "source": "fixture"},
            "executable_quote": {"status": "executable", "price": "10", "as_of_ms": 100, "max_age_ms": 10, "source": "fixture"},
            "liquidity": {"status": "sufficient", "max_quantity": "2", "as_of_ms": 190, "source": "fixture"},
            "risk_mandate": {"status": "approved", "max_loss": "10", "currency": "BRL", "as_of_ms": 190, "source": "fixture"},
            "product_gate": {"status": "approved", "as_of_ms": 190, "source": "fixture"},
            "authorization_gate": {"status": "approved", "as_of_ms": 190, "source": "fixture"},
            "coverage": {"status": "complete", "full_tape": True, "origin": "synthetic", "as_of_ms": 190, "source": "fixture"},
            "as_of_ms": 190,
        }
        result = assess_candidates([candidate], capital="400", currency="BRL", as_of_ms=200)
        self.assertEqual(result["status"], "not_evaluable")
        self.assertIn("executable_quote_stale", result["candidates"][0]["missing"])
        self.assertEqual(result["admissible"], [])


    def test_only_admissible_origins_control_scenario_comparison_status(self):
        from multimarket_economics import assess_candidates

        synthetic = {
            "candidate_id": "synthetic-valid", "instrument": {"settlement_currency": "BRL"}, "quantity": "1",
            "payoff": payoff("spot", quantity="1", entry_price="10", exit_price="11"),
            "costs": {"amount": "0", "currency": "BRL", "method": "explicit_zero", "base": "one_trade", "as_of_ms": 190, "source": "fixture"},
            "executable_quote": {"status": "executable", "price": "10", "as_of_ms": 195, "max_age_ms": 20, "source": "fixture"},
            "liquidity": {"status": "sufficient", "max_quantity": "2", "as_of_ms": 190, "source": "fixture"},
            "risk_mandate": {"status": "approved", "max_loss": "10", "currency": "BRL", "as_of_ms": 190, "source": "fixture"},
            "product_gate": {"status": "approved", "as_of_ms": 190, "source": "fixture"},
            "authorization_gate": {"status": "approved", "as_of_ms": 190, "source": "fixture"},
            "coverage": {"status": "complete", "full_tape": True, "origin": "synthetic", "as_of_ms": 190, "source": "fixture"},
            "as_of_ms": 190,
        }
        blocked_historical = {
            "candidate_id": "backtest-blocked", "instrument": {"settlement_currency": "BRL"}, "quantity": "1",
            "coverage": {"status": "complete", "full_tape": True, "origin": "backtest", "as_of_ms": 190, "source": "fixture"},
            "as_of_ms": 190,
        }
        result = assess_candidates([synthetic, blocked_historical], capital="400", currency="BRL", as_of_ms=200)
        self.assertEqual(result["status"], "scenario_comparison_only")
        self.assertEqual(result["admissible"], ["synthetic-valid"])
    def test_malformed_cost_object_blocks_without_crashing(self):
        from multimarket_economics import assess_candidates

        result = assess_candidates(
            [{"candidate_id": "malformed-cost", "instrument": {"settlement_currency": "BRL"}, "quantity": "1", "costs": None}],
            capital="400", currency="BRL", as_of_ms=200,
        )
        self.assertEqual(result["status"], "not_evaluable")
        self.assertIn("costs", result["candidates"][0]["missing"])
class EvaluationReportTests(unittest.TestCase):
    def test_default_report_is_pending_and_exposes_required_protocol_gaps(self):
        from multimarket_economics import evaluation_report

        report = evaluation_report()
        self.assertEqual(report["status"], "pending")
        self.assertEqual(report["sample_size"], 0)
        self.assertEqual(report["result_type"], "protocol_only")
        for field in ("chronology", "costs", "calibration", "intervals", "drawdown", "target_probability", "ruin_probability"):
            self.assertIsNone(report[field])
        self.assertEqual(report["ac07_status"], "pending")
        self.assertIn("chronological_split", report["missing"])
        self.assertIn("cost_execution_evidence", report["missing"])

    def test_explicit_result_origins_remain_separate_and_confidence_is_not_probability(self):
        from multimarket_economics import evaluation_report

        for origin in ("synthetic", "backtest", "prospective", "real"):
            with self.subTest(origin=origin):
                report = evaluation_report(
                    dataset={"origin": origin},
                    results={"sample_size": 25, "confidence": 0.99, "target_probability": 0.98, "ruin_probability": 0.01},
                )
                self.assertEqual(report["result_type"], origin)
                self.assertEqual(report["sample_size"], 25)
                self.assertEqual(report["status"], "pending")
                self.assertEqual(report["ac07_status"], "pending")
                self.assertIsNone(report["target_probability"])
                self.assertIsNone(report["ruin_probability"])
                self.assertNotIn("profit_probability", report)

    def test_overlap_assessment_requires_explicit_overlap_presence(self):
        from multimarket_economics import evaluation_report

        report = evaluation_report(method={"overlap_assessed": True})
        self.assertIn("overlap_presence_status", report["missing"])
    def test_conflicting_origin_labels_are_not_silently_reconciled(self):
        from multimarket_economics import evaluation_report

        report = evaluation_report(dataset={"origin": "synthetic"}, results={"result_type": "real"})
        self.assertEqual(report["result_type"], "protocol_only")
        self.assertIn("conflicting_result_origins", report["missing"])
        self.assertEqual(report["status"], "pending")

if __name__ == "__main__":
    unittest.main()

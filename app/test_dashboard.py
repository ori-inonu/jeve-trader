import unittest
from dashboard import example_from_inputs, format_capacity
from capital_planner import project_stop_capacity
from copilot import ROOT, load_json
from risk import evaluate_risk


class DashboardInputTests(unittest.TestCase):
    def setUp(self):
        self.config = load_json(ROOT / "config.json")
        self.inputs = {"start": "400", "current": "400", "peak": "400", "risk_pct": "15",
                       "daily_pct": "50", "drawdown_pct": "50", "stop": "100", "target": "200"}

    def test_growth_keeps_account_reconciled_and_expands_quantity(self):
        cfg, small = example_from_inputs(self.config, self.inputs)
        self.inputs["current"] = "4000"
        cfg, large = example_from_inputs(self.config, self.inputs)
        self.assertEqual(large["account"]["realized_pnl_net_brl"], "3600")
        self.assertEqual(large["account"]["peak_equity_brl"], "4000")
        def q(snapshot):
            return evaluate_risk(cfg, snapshot["account"], snapshot["candidates"][0], snapshot["account"]["asof_ms"])["contracts"]
        self.assertEqual(q(small), 2)
        self.assertEqual(q(large), 22)

    def test_invalid_input_does_not_make_a_scenario(self):
        for key, value in (("current", "NaN"), ("risk_pct", "101"), ("stop", "3")):
            with self.subTest(key=key):
                values = dict(self.inputs)
                values[key] = value
                with self.assertRaises(ValueError):
                    example_from_inputs(self.config, values)

    def test_streak_is_explicit_not_inferred_from_net_profit(self):
        values = dict(self.inputs, current="3800", peak="4000", loss_streak="2")
        cfg, snapshot = example_from_inputs(self.config, values)
        self.assertEqual(snapshot["account"]["consecutive_losses"], 2)
        self.assertIsNotNone(snapshot["account"]["last_loss_ms"])

    def test_truncated_projection_is_identified_in_display(self):
        cfg, snapshot = example_from_inputs(self.config, self.inputs)
        report = project_stop_capacity(cfg, snapshot["account"], snapshot["candidates"][0], snapshot["ts_ms"], max_attempts=1)
        self.assertIn("pelo menos 1", format_capacity(report))
        self.assertIn("projeção truncada", format_capacity(report))


if __name__ == "__main__":
    unittest.main()

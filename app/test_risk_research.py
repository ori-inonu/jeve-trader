from copy import deepcopy
import json
from pathlib import Path
import unittest

from copilot import demo_snapshot, profile_config
from risk import evaluate_risk
from risk_research import compare_risk_policies


class PolicyComparisonTests(unittest.TestCase):
    def setUp(self):
        base = json.loads(Path(__file__).with_name("config.json").read_text())
        self.config = profile_config(base, "agressivo_pesquisa")
        self.snapshot = demo_snapshot("4000")
        self.account = self.snapshot["account"]
        self.candidate = self.snapshot["candidates"][0]
        self.now = self.account["asof_ms"]

    def test_each_row_matches_existing_engine(self):
        original = deepcopy((self.config, self.account, self.candidate))
        comparison = compare_risk_policies(self.config, self.account, self.candidate, self.now)
        self.assertEqual(len(comparison["rows"]), 10)
        for row in comparison["rows"]:
            config = deepcopy(self.config)
            config["risk"]["per_trade_fraction"] = row["per_trade_fraction"]
            config["risk"]["capital_basis"] = row["capital_basis"]
            self.assertEqual(row["sizing"], evaluate_risk(config, self.account, self.candidate, self.now))
            path = row["trajectories"]["real_policy"]
            self.assertEqual(path["attempts"], len(path["contracts_after_each_loss"]))
        self.assertEqual(original, (self.config, self.account, self.candidate))
        self.assertIsNone(comparison["optimal_policy"])
        self.assertIsNone(comparison["future_profit_probability"])
        json.dumps(comparison, allow_nan=False)

    def test_gain_and_loss_adapt_basis_without_recovery_sizing(self):
        self.account.update({"equity_brl": "5000", "realized_pnl_net_brl": "1000",
                             "available_margin_brl": "5000", "peak_equity_brl": "5000"})
        result = compare_risk_policies(self.config, self.account, self.candidate, self.now, fractions=["0.05"])
        capped, adaptive = result["rows"]
        self.assertEqual(capped["sizing"]["risk_budget_brl"], "200")
        self.assertEqual(adaptive["sizing"]["risk_budget_brl"], "250")
        self.assertGreater(adaptive["allowed_contracts"], capped["allowed_contracts"])
        path = adaptive["trajectories"]["real_policy"]["contracts_after_each_loss"]
        self.assertEqual(path, sorted(path, reverse=True))

    def test_400_balance_still_respects_margin_and_stop_costs(self):
        snapshot = demo_snapshot("400")
        comparison = compare_risk_policies(self.config, snapshot["account"], snapshot["candidates"][0], self.now)
        for row in comparison["rows"]:
            self.assertLessEqual(row["allowed_contracts"], 2)
        self.assertEqual(comparison["rows"][0]["allowed_contracts"], 0)
        self.assertEqual(comparison["rows"][-1]["allowed_contracts"], 2)

    def test_live_stale_unreconciled_and_mismatched_account_stay_blocked(self):
        for overrides in ({"environment": "live"}, {"asof_ms": self.now - 2001},
                          {"reconciled": False}, {"equity_brl": "9999"}, {"available_margin_brl": "NaN"}):
            account = {**self.account, **overrides}
            result = compare_risk_policies(self.config, account, self.candidate, self.now, fractions=["0.15"])
            self.assertTrue(all(row["sizing"]["status"] == "BLOCK" for row in result["rows"]))
            self.assertTrue(all(row["allowed_contracts"] == 0 for row in result["rows"]))

    def test_invalid_and_unbounded_requests_rejected(self):
        for fractions in (["NaN"], ["Infinity"], [0], [-1], ["1.01"], [True], ["1e9999"], [],
                          [".1", ".10"], [".01"] * 21):
            with self.assertRaises(ValueError):
                compare_risk_policies(self.config, self.account, self.candidate, self.now, fractions=fractions)
        for limit in (0, 1001, True, 1.1):
            with self.assertRaises(ValueError):
                compare_risk_policies(self.config, self.account, self.candidate, self.now, max_attempts=limit)

    def test_projection_truncation_is_explicit(self):
        result = compare_risk_policies(self.config, self.account, self.candidate, self.now,
                                       fractions=[".01"], max_attempts=1)
        for row in result["rows"]:
            self.assertTrue(row["trajectories"]["real_policy"]["truncated_at_max_attempts"])
            self.assertEqual(row["attempts_until_policy_stop"], 1)


if __name__ == "__main__":
    unittest.main()

"""Financial invariants for hypothetical, synthetic loss trajectories only."""

from copy import deepcopy
from decimal import Decimal
import json
import unittest

from capital_planner import project_stop_capacity


NOW = 1801848600000


def configuration():
    return {
        "mode": "simulation",
        "capital_initial_brl": "400",
        "instrument": {"point_value_brl": "0.20", "tick_points": 5, "exchange_min_margin_brl": "155"},
        "risk": {
            "per_trade_fraction": "0.15", "daily_loss_fraction": "0.50",
            "max_contracts": 100, "max_consecutive_losses": 2,
            "cooldown_after_loss_ms": 300000, "min_net_reward_risk": "1.5",
            "max_account_age_ms": 2000, "cash_buffer_brl": "0",
            "capital_basis": "current_equity", "daily_budget_mode": "equity_floor",
            "reserve_planned_loss_beside_margin": True, "max_peak_drawdown_fraction": "0.50",
        },
        "costs": {"round_trip_fees_brl_per_contract": "1.00", "slippage_points_round_trip": 5, "illustrative_only": True},
    }


def account(equity="400", start="400"):
    return {
        "asof_ms": NOW, "start_equity_brl": start, "equity_brl": equity,
        "peak_equity_brl": equity,
        "realized_pnl_net_brl": str(Decimal(equity) - Decimal(start)),
        "unrealized_pnl_brl": "0", "reserved_risk_brl": "0", "available_margin_brl": equity,
        "broker_margin_brl_per_contract": "155", "open_contracts": 0, "pending_entry_contracts": 0,
        "consecutive_losses": 0, "last_loss_ms": None, "reconciled": True, "environment": "simulated",
    }


def candidate():
    return {"id": "synthetic-capacity", "side": "buy", "entry_points": 131000,
            "stop_points": 130900, "target_points": 131200, "quantity_requested": 100}


class CapitalPlannerTests(unittest.TestCase):
    def test_current_capital_resizes_400_to_4000_without_predicting_growth(self):
        small = project_stop_capacity(configuration(), account(), candidate(), NOW)
        large = project_stop_capacity(configuration(), account("4000"), candidate(), NOW)
        self.assertEqual(small["current_sizing"]["contracts"], 2)
        self.assertEqual(large["current_sizing"]["contracts"], 22)
        self.assertFalse(large["profit_forecast"])
        self.assertTrue(large["simulation_only"])

    def test_losing_trajectories_never_increase_size_or_exceed_available_cash(self):
        config = configuration()
        for capital in ("400", "4000"):
            result = project_stop_capacity(config, account(capital), candidate(), NOW)
            for trajectory in result["trajectories"].values():
                quantities = [step["contracts"] for step in trajectory["steps"]]
                self.assertEqual(quantities, sorted(quantities, reverse=True))
                previous = Decimal(capital)
                for step in trajectory["steps"]:
                    before, after = Decimal(step["equity_before_brl"]), Decimal(step["equity_after_brl"])
                    self.assertEqual(before, previous)
                    self.assertLess(after, before)
                    required_cash = Decimal(step["margin_required_brl"]) + Decimal(step["planned_stop_loss_brl"])
                    available_cash = min(before, Decimal(step["available_margin_before_brl"]))
                    self.assertLessEqual(required_cash, available_cash)
                    self.assertLessEqual(Decimal(step["planned_stop_loss_brl"]), Decimal(step["risk_budget_before_brl"]))
                    self.assertGreaterEqual(after, Decimal(capital) * Decimal("0.50"))
                    self.assertEqual(Decimal(step["peak_equity_brl"]), Decimal(capital))
                    previous = after

    def test_streak_policy_and_financial_budget_are_distinct(self):
        result = project_stop_capacity(configuration(), account(), candidate(), NOW)
        self.assertEqual(result["attempts_until_policy_stop"], 2)
        self.assertGreater(result["attempts_by_financial_budget_ignoring_streak"], 2)
        self.assertIn("CONSECUTIVE_LOSS_LIMIT_REACHED", result["stop_reasons"]["real_policy"])
        diagnostic = result["trajectories"]["budget_only_ignoring_streak_projection"]
        self.assertTrue(diagnostic["ignores_consecutive_loss_limit"])
        self.assertFalse(diagnostic["truncated_at_max_attempts"])
        self.assertNotIn("CONSECUTIVE_LOSS_LIMIT_REACHED", diagnostic["stop_reasons"])

    def test_cooldown_is_waited_but_stale_accounts_remain_blocked(self):
        active = account()
        active.update(consecutive_losses=1, last_loss_ms=NOW - 10)
        result = project_stop_capacity(configuration(), active, candidate(), NOW)
        self.assertIn("LOSS_COOLDOWN_ACTIVE", result["current_sizing"]["reasons"])
        self.assertEqual(result["attempts_until_policy_stop"], 1)
        self.assertGreater(result["trajectories"]["real_policy"]["initial_cooldown_wait_ms"], 0)
        active["asof_ms"] = NOW - 2001
        active["last_loss_ms"] = NOW - 3000
        stale = project_stop_capacity(configuration(), active, candidate(), NOW)
        self.assertEqual(stale["attempts_until_policy_stop"], 0)
        self.assertIn("STALE_OR_FUTURE_ACCOUNT", stale["stop_reasons"]["real_policy"])

    def test_zero_capacity_for_insufficient_capital(self):
        result = project_stop_capacity(configuration(), account("100", "100"), candidate(), NOW)
        self.assertEqual(result["attempts_until_policy_stop"], 0)
        self.assertEqual(result["attempts_by_financial_budget_ignoring_streak"], 0)
        self.assertTrue(result["stop_reasons"]["real_policy"])
        self.assertEqual(result["trajectories"]["real_policy"]["steps"], [])
        self.assertEqual(Decimal(result["trajectories"]["real_policy"]["final_equity_brl"]), Decimal("100"))

    def test_projection_bound_is_not_reported_as_full_capacity(self):
        result = project_stop_capacity(configuration(), account(), candidate(), NOW, max_attempts=1)
        self.assertEqual(result["attempts_until_policy_stop"], 1)
        self.assertTrue(result["trajectories"]["real_policy"]["truncated_at_max_attempts"])
        self.assertIn("PROJECTION_LIMIT_REACHED", result["stop_reasons"]["real_policy"])
        for limit in (0, -1, True, 1.5, 10001):
            invalid = project_stop_capacity(configuration(), account(), candidate(), NOW, max_attempts=limit)
            self.assertEqual(invalid["status"], "INVALID_INPUT")
            self.assertEqual(invalid["attempts_until_policy_stop"], 0)

    def test_inputs_not_mutated_and_results_are_json_serializable(self):
        config, ledger, proposal = configuration(), account("4000"), candidate()
        originals = deepcopy((config, ledger, proposal))
        result = project_stop_capacity(config, ledger, proposal, NOW)
        self.assertEqual((config, ledger, proposal), originals)
        json.dumps(result, allow_nan=False)


if __name__ == "__main__":
    unittest.main()

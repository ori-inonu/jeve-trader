from copy import deepcopy
from decimal import Decimal
import json
import unittest

from risk import evaluate_risk


NOW = 1801848600000


def configuration():
    return {
        "mode": "simulation", "capital_initial_brl": "400",
        "instrument": {"point_value_brl": "0.20", "tick_points": 5,
                       "exchange_min_margin_brl": "155"},
        "risk": {"per_trade_fraction": "0.01", "daily_loss_fraction": "0.03",
                 "max_contracts": 1, "max_consecutive_losses": 2,
                 "cooldown_after_loss_ms": 300000, "min_net_reward_risk": "1.5",
                 "max_account_age_ms": 2000, "cash_buffer_brl": "100"},
        "costs": {"round_trip_fees_brl_per_contract": "1.00",
                  "slippage_points_round_trip": 5, "illustrative_only": True},
    }


def account(capital="2500", pnl="0"):
    equity = str(Decimal(capital) + Decimal(pnl))
    return {
        "asof_ms": NOW, "start_equity_brl": capital, "equity_brl": equity,
        "realized_pnl_net_brl": pnl, "unrealized_pnl_brl": "0",
        "reserved_risk_brl": "0", "available_margin_brl": equity,
        "broker_margin_brl_per_contract": "155", "open_contracts": 0,
        "pending_entry_contracts": 0, "consecutive_losses": int(Decimal(pnl) < 0),
        "last_loss_ms": NOW - 600000 if Decimal(pnl) < 0 else None,
        "reconciled": True, "environment": "simulated",
    }


def candidate():
    return {"id": "synthetic-buy", "side": "buy", "entry_points": 131000,
            "stop_points": 130900, "target_points": 131200, "quantity_requested": 4}


class RiskTests(unittest.TestCase):
    def setUp(self):
        self.config, self.account, self.candidate = configuration(), account(), candidate()

    def evaluate(self):
        return evaluate_risk(self.config, self.account, self.candidate, NOW)

    def assert_blocked(self, reason):
        result = self.evaluate()
        self.assertEqual(result["status"], "BLOCK")
        self.assertEqual(result["contracts"], 0)
        self.assertIn(reason, result["reasons"])
        return result

    def test_2500_risk_includes_fees_and_slippage_in_both_outcomes(self):
        result = self.evaluate()
        self.assertEqual(result["status"], "ALLOW_SIMULATION")
        self.assertEqual(result["contracts"], 1)
        for field, expected in (("risk_budget_brl", "25"), ("risk_per_contract_brl", "22"),
                                ("net_reward_per_contract_brl", "38"), ("margin_per_contract_brl", "155")):
            self.assertEqual(Decimal(result[field]), Decimal(expected))
        self.assertAlmostEqual(float(result["net_reward_risk"]), 38 / 22)
        json.dumps(result, allow_nan=False)

    def test_400_does_not_move_stop_to_fit_risk(self):
        self.account = account("400")
        original = deepcopy(self.candidate)
        result = self.assert_blocked("STOP_RISK_EXCEEDS_BUDGET")
        self.assertEqual(Decimal(result["risk_budget_brl"]), 4)
        self.assertEqual(self.candidate, original)

    def test_twenty_loss_exceeds_example_daily_limit_twelve(self):
        self.account = account("400", "-20")
        result = self.assert_blocked("DAILY_LOSS_LIMIT_REACHED")
        self.assertEqual(Decimal(result["risk_budget_brl"]), 0)

    def test_configurable_aggressive_profile_allows_two_never_four_on_400_margin(self):
        self.account = account("400")
        self.config["risk"].update(per_trade_fraction="0.50", daily_loss_fraction="0.80",
                                   max_contracts=10, cash_buffer_brl="0")
        self.assertEqual(self.evaluate()["contracts"], 2)
        self.config["risk"]["max_contracts"] = 1
        self.assertEqual(self.evaluate()["contracts"], 1)

    def test_loss_does_not_increase_quantity_and_profit_does_not_raise_budget(self):
        self.config["risk"].update(per_trade_fraction="0.15", daily_loss_fraction="0.50",
                                   max_contracts=10, cash_buffer_brl="0")
        self.account = account("400")
        before = self.evaluate()
        self.account = account("400", "-20")
        after = self.evaluate()
        self.assertLessEqual(after["contracts"], before["contracts"])
        self.assertLess(Decimal(after["risk_budget_brl"]), Decimal(before["risk_budget_brl"]))
        self.account = account("400", "100")
        self.assertEqual(self.evaluate()["risk_budget_brl"], before["risk_budget_brl"])

    def test_exchange_margin_floor_and_larger_broker_margin(self):
        self.account["broker_margin_brl_per_contract"] = "100"
        self.assertEqual(Decimal(self.evaluate()["margin_per_contract_brl"]), 155)
        self.account["broker_margin_brl_per_contract"] = "3000"
        self.assert_blocked("INSUFFICIENT_MARGIN_AFTER_BUFFER")

    def test_margin_and_risk_equality_are_admitted(self):
        self.config["risk"]["per_trade_fraction"] = "0.0088"  # 2500 * .0088 = 22
        self.account["available_margin_brl"] = "255"  # Exactly 155 + 100 buffer
        self.assertEqual(self.evaluate()["status"], "ALLOW_SIMULATION")
        self.account["available_margin_brl"] = "254.99"
        self.assert_blocked("INSUFFICIENT_MARGIN_AFTER_BUFFER")

    def test_reserved_risk_consumes_daily_capacity(self):
        self.account["reserved_risk_brl"] = "54"  # 75 - 54 = 21, below 22
        result = self.assert_blocked("STOP_RISK_EXCEEDS_BUDGET")
        self.assertEqual(Decimal(result["risk_budget_brl"]), 21)
        self.account["reserved_risk_brl"] = "75"
        self.assert_blocked("RISK_BUDGET_EXHAUSTED")

    def test_daily_limit_equality_and_unrealized_loss_count(self):
        self.account = account("400", "-12")
        self.assert_blocked("DAILY_LOSS_LIMIT_REACHED")
        self.account = account("400")
        self.account.update(unrealized_pnl_brl="-12", equity_brl="388", available_margin_brl="388")
        self.assert_blocked("DAILY_LOSS_LIMIT_REACHED")

    def test_freshness_boundary_future_and_missing_account(self):
        self.account["asof_ms"] = NOW - 2000
        self.assertEqual(self.evaluate()["status"], "ALLOW_SIMULATION")
        for stamp in (NOW - 2001, NOW + 1):
            self.account["asof_ms"] = stamp
            self.assert_blocked("STALE_OR_FUTURE_ACCOUNT")
        self.account = None
        self.assert_blocked("INVALID_ACCOUNT")

    def test_unreconciled_real_or_unknown_accounts_fail_closed(self):
        for environment in ("live", "unknown", None):
            self.account["environment"] = environment
            self.assert_blocked("SIMULATED_ACCOUNT_REQUIRED")
        self.account = account()
        self.account["reconciled"] = 1
        self.assert_blocked("ACCOUNT_NOT_RECONCILED")
        self.account = account()
        self.account["equity_brl"] = "2501"
        self.assert_blocked("ACCOUNT_EQUITY_MISMATCH")

    def test_existing_position_and_pending_entry_block_new_exposure(self):
        for field in ("open_contracts", "pending_entry_contracts"):
            self.account = account()
            self.account[field] = 1
            self.assert_blocked("EXISTING_POSITION_OR_PENDING_ENTRY")

    def test_consecutive_loss_and_cooldown_boundaries(self):
        self.account = account("2500", "-1")
        self.account["last_loss_ms"] = NOW - 299999
        self.assert_blocked("LOSS_COOLDOWN_ACTIVE")
        self.account["last_loss_ms"] = NOW - 300000
        self.assertEqual(self.evaluate()["status"], "ALLOW_SIMULATION")
        self.account["consecutive_losses"] = 2
        self.assert_blocked("CONSECUTIVE_LOSS_LIMIT_REACHED")
        self.account["last_loss_ms"] = None
        self.assert_blocked("INVALID_ACCOUNT")

    def test_sell_side_and_all_price_ticks_are_checked(self):
        self.candidate.update(side="sell", stop_points=131100, target_points=130800)
        self.assertEqual(self.evaluate()["status"], "ALLOW_SIMULATION")
        self.candidate["stop_points"] = 130900
        self.assert_blocked("INVALID_STOP_OR_TARGET_SIDE")
        for field in ("entry_points", "stop_points", "target_points"):
            self.candidate = candidate()
            self.candidate[field] += 1
            self.assert_blocked("PRICE_NOT_ON_TICK")

    def test_stop_target_zero_distance_and_negative_net_reward_fail_closed(self):
        self.candidate["stop_points"] = self.candidate["entry_points"]
        self.assert_blocked("INVALID_STOP_OR_TARGET_SIDE")
        self.candidate = candidate()
        self.candidate["target_points"] = 131005
        self.assert_blocked("NET_REWARD_RISK_TOO_LOW")

    def test_rr_exact_threshold_accepted_and_below_rejected(self):
        self.config["costs"].update(round_trip_fees_brl_per_contract="0", slippage_points_round_trip=0)
        self.candidate["target_points"] = 131150
        self.assertEqual(self.evaluate()["status"], "ALLOW_SIMULATION")
        self.candidate["target_points"] = 131145
        self.assert_blocked("NET_REWARD_RISK_TOO_LOW")

    def test_quantity_default_caps_and_invalid_integers(self):
        del self.candidate["quantity_requested"]
        self.assertEqual(self.evaluate()["contracts"], 1)
        for quantity in (True, 0, -1, "2", 1.5):
            self.candidate["quantity_requested"] = quantity
            self.assert_blocked("INVALID_CANDIDATE")

    def test_nan_infinity_bool_malformed_and_missing_fields_fail_closed(self):
        for value in ("NaN", "Infinity", "-Infinity", float("nan"), True, [], {}, "oops", "1e999999"):
            self.account = account()
            self.account["equity_brl"] = value
            self.assert_blocked("INVALID_ACCOUNT")
        self.account = account()
        for field in ("id", "side", "entry_points", "stop_points", "target_points"):
            self.candidate = candidate()
            del self.candidate[field]
            self.assert_blocked("INVALID_CANDIDATE")

    def test_invalid_config_and_live_mode_cannot_enable_real_orders(self):
        self.config["mode"] = "live"
        self.assert_blocked("SIMULATION_ONLY")
        self.config = configuration()
        self.config["risk"]["per_trade_fraction"] = True
        self.assert_blocked("INVALID_CONFIG")
        self.config = configuration()
        self.config["costs"]["slippage_points_round_trip"] = -5
        self.assert_blocked("INVALID_CONFIG")

    def test_inputs_are_not_mutated(self):
        before = deepcopy((self.config, self.account, self.candidate))
        self.evaluate()
        self.assertEqual((self.config, self.account, self.candidate), before)


class DynamicCapitalTests(unittest.TestCase):
    def setUp(self):
        self.config = configuration()
        self.config["risk"].update(
            capital_basis="current_equity", daily_budget_mode="equity_floor",
            reserve_planned_loss_beside_margin=True, max_peak_drawdown_fraction="0.50",
            per_trade_fraction="0.15", daily_loss_fraction="0.50",
            max_contracts=100, cash_buffer_brl="0")
        self.candidate = candidate()
        self.candidate["quantity_requested"] = 100
        self.set_account("400")

    def set_account(self, start, pnl="0", peak=None):
        self.account = account(start, pnl)
        self.account["peak_equity_brl"] = peak or str(max(Decimal(start), Decimal(self.account["equity_brl"])))

    def evaluate(self):
        return evaluate_risk(self.config, self.account, self.candidate, NOW)

    def test_current_capital_growth_same_session_and_next_session_scales_size(self):
        initial = self.evaluate()
        self.assertEqual(initial["contracts"], 2)
        self.assertEqual(Decimal(initial["risk_budget_brl"]), 60)
        self.set_account("400", "3600")
        grown = self.evaluate()
        self.assertEqual(grown["status"], "ALLOW_SIMULATION")
        self.assertEqual(grown["contracts"], 22)
        self.assertEqual(Decimal(grown["equity_basis_brl"]), 4000)
        self.assertEqual(Decimal(grown["risk_budget_brl"]), 600)
        self.assertEqual(Decimal(grown["daily_floor_brl"]), 200)
        self.assertEqual(Decimal(grown["drawdown_floor_brl"]), 2000)
        self.assertEqual(Decimal(grown["available_risk_capacity_brl"]), 2000)
        self.assertTrue(grown["margin_sizing_includes_stop_reserve"])
        self.set_account("4000")
        self.assertEqual(self.evaluate()["contracts"], 22)

    def test_loss_reduces_current_risk_budget_without_compulsory_recovery(self):
        self.set_account("400", "-20")
        result = self.evaluate()
        self.assertEqual(result["contracts"], 2)
        self.assertEqual(Decimal(result["equity_basis_brl"]), 380)
        self.assertEqual(Decimal(result["risk_budget_brl"]), 57)
        self.assertEqual(Decimal(result["available_risk_capacity_brl"]), 180)

    def test_daily_mode_independently_controls_profit_reinvestment(self):
        self.set_account("400", "3600")
        self.config["risk"]["daily_budget_mode"] = "loss_only"
        result = self.evaluate()
        self.assertEqual(Decimal(result["risk_budget_brl"]), 200)
        self.assertEqual(result["contracts"], 9)
        self.config["risk"]["daily_budget_mode"] = "equity_floor"
        self.config["risk"]["capital_basis"] = "session_start_cap"
        self.assertEqual(Decimal(self.evaluate()["risk_budget_brl"]), 60)

    def test_joint_margin_reserves_stop_loss_without_double_deducting_existing_risk(self):
        self.set_account("4000")
        self.account["reserved_risk_brl"] = "1450"
        result = self.evaluate()
        self.assertEqual(Decimal(result["available_risk_capacity_brl"]), 550)
        self.assertEqual(result["contracts"], 22)
        self.account["reserved_risk_brl"] = "0"
        self.account["available_margin_brl"] = "353.99"
        self.assertEqual(self.evaluate()["contracts"], 1)
        self.account["available_margin_brl"] = "354"
        self.assertEqual(self.evaluate()["contracts"], 2)

    def test_peak_floor_applies_after_profitable_drawdown_and_at_exact_limit(self):
        self.set_account("400", "150", peak="1000")
        result = self.evaluate()
        self.assertEqual(Decimal(result["daily_floor_brl"]), 200)
        self.assertEqual(Decimal(result["drawdown_floor_brl"]), 500)
        self.assertEqual(Decimal(result["risk_budget_brl"]), 50)
        self.assertEqual(result["contracts"], 2)
        self.set_account("400", "100", peak="1000")
        result = self.evaluate()
        self.assertEqual(result["status"], "BLOCK")
        self.assertEqual(result["contracts"], 0)
        self.assertIn("PEAK_DRAWDOWN_LIMIT_REACHED", result["reasons"])
        self.assertNotIn("DAILY_LOSS_LIMIT_REACHED", result["reasons"])

    def test_daily_floor_exact_boundary_blocks_and_near_floor_caps_risk(self):
        self.set_account("400", "-178")
        result = self.evaluate()
        self.assertEqual(Decimal(result["risk_budget_brl"]), 22)
        self.assertEqual(result["contracts"], 1)
        self.set_account("400", "-200")
        result = self.evaluate()
        self.assertEqual(result["contracts"], 0)
        self.assertIn("DAILY_LOSS_LIMIT_REACHED", result["reasons"])

    def test_drawdown_policy_requires_valid_peak_not_less_than_start_or_current(self):
        for peak in (None, "399", "NaN", "Infinity", True):
            with self.subTest(peak=peak):
                self.account["peak_equity_brl"] = peak
                result = self.evaluate()
                self.assertEqual(result["contracts"], 0)
                self.assertIn("INVALID_PEAK_EQUITY", result["reasons"])
        del self.account["peak_equity_brl"]
        self.assertIn("INVALID_PEAK_EQUITY", self.evaluate()["reasons"])
        self.config["risk"]["max_peak_drawdown_fraction"] = None
        self.assertEqual(self.evaluate()["contracts"], 2)
        self.assertIsNone(self.evaluate()["drawdown_floor_brl"])

    def test_stale_gains_do_not_enable_larger_size(self):
        self.set_account("400", "3600")
        self.account["asof_ms"] = NOW - 2001
        result = self.evaluate()
        self.assertEqual(result["contracts"], 0)
        self.assertIn("STALE_OR_FUTURE_ACCOUNT", result["reasons"])

    def test_invalid_optional_policies_fail_closed(self):
        for key, value in (("capital_basis", "auto"), ("daily_budget_mode", "unbounded"),
                           ("reserve_planned_loss_beside_margin", 1),
                           ("max_peak_drawdown_fraction", "1.01"),
                           ("max_peak_drawdown_fraction", "NaN")):
            with self.subTest(key=key, value=value):
                saved = self.config["risk"][key]
                self.config["risk"][key] = value
                result = self.evaluate()
                self.assertEqual(result["contracts"], 0)
                self.assertIn("INVALID_CONFIG", result["reasons"])
                self.config["risk"][key] = saved


if __name__ == "__main__":
    unittest.main()

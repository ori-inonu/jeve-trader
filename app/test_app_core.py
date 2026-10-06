import tempfile
from pathlib import Path
import unittest
from app_core import DEFAULT_INPUTS, ObservationSession, apply_manual_pnl, build_risk_study, can_classify, jev_observation_state, response_is_current, self_check
from profit_bridge import read_csv_events


class AppCoreTests(unittest.TestCase):
    def test_self_check_and_current_equity_growth(self):
        self.assertEqual(self_check()["status"], "passed")

    def test_manual_loss_streak_and_profit_peak(self):
        values = dict(DEFAULT_INPUTS, current="3800", peak="4000", loss_streak="2")
        result = apply_manual_pnl(values, "-20")
        self.assertEqual((result["current"], result["peak"], result["loss_streak"]), ("3780", "4000", "3"))
        result = apply_manual_pnl(result, "500")
        self.assertEqual((result["current"], result["peak"], result["loss_streak"]), ("4280", "4280", "0"))

    def test_real_margin_and_costs_change_sizing(self):
        basic = build_risk_study(DEFAULT_INPUTS)
        expensive = build_risk_study(dict(DEFAULT_INPUTS, margin="300"))
        self.assertEqual(basic["projection"]["current_sizing"]["contracts"], 2)
        self.assertEqual(expensive["projection"]["current_sizing"]["contracts"], 1)

    def test_jev_context_does_not_include_account_or_force_profit(self):
        snapshot = ObservationSession().demo()
        state = jev_observation_state(snapshot)
        self.assertNotIn("account", state)
        self.assertNotIn("risk", state)
        self.assertTrue(can_classify(snapshot)[0])

    def test_csv_sampling_never_becomes_full_tape(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"sample.csv"
            path.write_text("id,symbol,ts_ms,price_points,quantity,aggressor\n1,WIN_SIM,1801848600000,131000,1,buy\n")
            batch = read_csv_events(path,"WIN_SIM")
            session = ObservationSession()
            snapshot = session.ingest(batch,replay=True)
            self.assertFalse(snapshot["evidence_coverage"]["source_quality"]["full_tape"])
            self.assertTrue(all(h["status"] == "inconclusive" for h in snapshot["hypotheses"]))
            self.assertFalse(can_classify(snapshot)[0])

    def test_nan_and_ruined_scenarios_are_not_repaired(self):
        with self.assertRaises(ValueError):
            build_risk_study(dict(DEFAULT_INPUTS,current="NaN"))
        exhausted = apply_manual_pnl(DEFAULT_INPUTS, "-401")
        self.assertEqual(exhausted["current"], "-1")
        with self.assertRaises(ValueError):
            build_risk_study(exhausted)

    def test_registered_loss_respects_actual_cooldown(self):
        values = apply_manual_pnl(DEFAULT_INPUTS, "-20")
        now = 1801848600000
        fresh = build_risk_study(values, now_ms=now, last_loss_ms=now)
        self.assertIn("LOSS_COOLDOWN_ACTIVE", fresh["projection"]["current_sizing"]["reasons"])
        elapsed = build_risk_study(values, now_ms=now+61000, last_loss_ms=now)
        self.assertNotIn("LOSS_COOLDOWN_ACTIVE", elapsed["projection"]["current_sizing"]["reasons"])

    def test_offline_loss_sequence_keeps_explicit_elapsed_pause_assumption(self):
        values = dict(DEFAULT_INPUTS, current="380", loss_streak="1")
        study = build_risk_study(values, now_ms=1801848600000)
        self.assertEqual(study["account"]["consecutive_losses"], 1)
        self.assertEqual(study["loss_time_assumption"], "manual_scenario_assumes_prior_loss_cooldown_elapsed")
        self.assertEqual(study["projection"]["current_sizing"]["contracts"], 2)

    def test_response_uses_trade_time_not_evaluation_clock(self):
        snapshot = ObservationSession().demo()
        now = snapshot["ts_ms"]
        snapshot["application_mode"] = "excel_observation"
        snapshot["flow_ts_ms"] = now-1900
        self.assertTrue(response_is_current(snapshot, now-1900, now_ms=now))
        self.assertFalse(response_is_current(snapshot, now-1900, now_ms=now+2000))
        snapshot["flow_ts_ms"] = now+2000
        self.assertFalse(response_is_current(snapshot, now-1900, now_ms=now+2000))


if __name__ == "__main__":
    unittest.main()

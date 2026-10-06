import unittest
from stress_lab import scenario_report


class StressTests(unittest.TestCase):
    def test_two_contracts_and_forced_fee(self):
        row = next(x for x in scenario_report()["scenarios"]
                   if x["contracts"] == 2 and x["adverse_move_points"] == 100)
        self.assertEqual(float(row["loss_with_hypothetical_normal_costs_brl"]), 44)
        self.assertEqual(float(row["loss_if_forced_fee_also_applies_brl"]), 114)

    def test_four_contracts_fail_margin(self):
        rows = [x for x in scenario_report()["scenarios"] if x["contracts"] == 4]
        self.assertTrue(all(not x["margin_fits_before_reserves"] for x in rows))

    def test_deposit_is_not_loss_cap(self):
        row = next(x for x in scenario_report()["scenarios"]
                   if x["contracts"] == 2 and x["adverse_move_points"] == 1000)
        self.assertLess(float(row["balance_after_forced_scenario_brl"]), 0)


if __name__ == "__main__":
    unittest.main()

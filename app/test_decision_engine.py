from decimal import Decimal
import unittest
from decision_engine import AccountState, CostSchedule, OutcomeEstimate, compare_plans, select_plan, build_decision_choice


ROW = dict(id='buy', side='buy', entry_points='100000', stop_points='99900', target_points='100200',
           reference_evidence_ids=['a', 'b'], premise='Buying advances')


class FinancialDecisionTests(unittest.TestCase):
    def test_current_equity_quantity_no_loss_recovery_and_drawdown_pause(self):
        costs = CostSchedule()
        capacities = []
        for equity, peak in [('400', '400'), ('800', '800'), ('600', '800')]:
            account = AccountState(equity_brl=equity, peak_brl=peak, available_margin_brl=equity)
            plans = compare_plans([ROW], account, costs, max_quantity=100)
            self.assertEqual(plans[0]['quantity'], 0)
            capacities.append(max(x['quantity'] for x in plans))
            self.assertTrue(all(x['account_equity_brl'] == equity for x in plans))
        self.assertEqual(capacities, [2, 4, 3])
        plans = compare_plans([ROW], AccountState(equity_brl='560', peak_brl='800', available_margin_brl='560'), costs)
        self.assertGreater(max(x['quantity'] for x in plans), 0)
        self.assertFalse(select_plan(plans)['order_sent'])

    def test_costs_each_side_and_margin_plus_loss_reserve(self):
        costs = CostSchedule(b3_entry_brl='0.30', b3_exit_brl='0.40', brokerage_entry_brl='0.10',
                             brokerage_exit_brl='0.20', slippage_points='5')
        plans = compare_plans([ROW], AccountState(equity_brl='400', peak_brl='400', available_margin_brl='400'), costs)
        two = next(p for p in plans if p['quantity'] == 2)
        self.assertEqual(two['costs_brl'], '6.00')  # slip on each leg, no duplicated spread
        self.assertEqual(two['loss_brl'], '46.00')
        self.assertEqual(two['target_net_brl'], '74.00')
        self.assertEqual(two['margin_brl'], '310.00')
        self.assertEqual(select_plan(plans)['action'], 'wait')
        self.assertIsNone(select_plan(plans)['profit_probability'])

    def test_unvalidated_outcomes_do_not_become_profit_recommendation(self):
        plans = compare_plans([ROW], AccountState(), CostSchedule(), estimates={'buy': {'validated': False}})
        self.assertEqual(select_plan(plans)['quantity'], 0)

    def test_validated_distribution_compound_growth_typed_choice_and_smooth_adaptation(self):
        estimate = OutcomeEstimate('unit-test-fixture', [{'probability': .7, 'gross_points': '200'}, {'probability': .3, 'gross_points': '-100'}], probability_interval=[.6, .8], validated=True, validation={'temporal_holdout': True, 'deployment_approved': True, 'synthetic': False})
        plans = compare_plans([ROW], AccountState(equity_brl='10000', peak_brl='10000', available_margin_brl='10000'), CostSchedule(), estimates={'buy': estimate})
        normal = select_plan(plans)
        adapted = select_plan(plans, drawdown=.30)
        self.assertGreater(normal['quantity'], 1)
        self.assertGreater(adapted['quantity'], 0)
        self.assertLess(adapted['quantity'], normal['quantity'])
        self.assertEqual(normal['profit_probability'], .7)
        state, questions = build_decision_choice(plans)
        self.assertIn('wait', questions['decision_plan']['criteria'])
        self.assertEqual(state['compared_plan_count'], len(plans))
        self.assertEqual(select_plan(plans, chosen_id='wait')['action'], 'wait')
        self.assertEqual(select_plan(plans, chosen_id='forged:q999')['quantity'], 0)
        estimate.validation['synthetic'] = True
        self.assertIsNone(build_decision_choice(compare_plans([ROW], AccountState(), CostSchedule(), estimates={'buy': estimate})))

    def test_reconciled_margin_and_open_position_are_not_intentions(self):
        account = AccountState(positions=[dict(quantity=1, reserved_margin_brl='155')], available_margin_brl='245')
        self.assertEqual(len(compare_plans([ROW], account, CostSchedule())), 1)
        for field in ('equity_brl', 'available_margin_brl'):
            with self.assertRaises(ValueError):
                AccountState(**{field: 'NaN'})

import unittest
from decision_lab import label_path, temporal_split, trajectory, risk_quantity, tail_risk, economic_replay, coverage_proof_matches
from decision_engine import CostSchedule


class DecisionLabTests(unittest.TestCase):
    def test_labouchere_restarts_original_sequence_after_completion(self):
        result = trajectory([10, 10, 10], 'labouchere', initial=1000, margin=1, stop_loss=20)
        self.assertEqual(result['realized_net_brl'], ['40.00', '20.00', '40.00'])
        self.assertEqual(risk_quantity('labouchere', equity=1000, initial=1000, stop_loss=20, state={'sequence': []}), 4)

    def test_coverage_is_bound_to_captured_symbol_digest_and_entire_horizon(self):
        proof = dict(full_tape=True, continuity_verified=True, reference='capture audit', symbol='WINV26', events_sha256='abc', start_ms=1000, end_ms=5000)
        args = dict(symbol='WINV26', digest='abc', start_ms=2000, end_ms=4000)
        self.assertTrue(coverage_proof_matches(proof, **args))
        for change in ({'symbol': 'WINZ26'}, {'digest': 'def'}, {'end_ms': 6000}):
            self.assertFalse(coverage_proof_matches(proof, **{**args, **change}))
        self.assertFalse(coverage_proof_matches({'full_tape': True, 'continuity_verified': True, 'reference': 'clock order'}, **args))

    def test_causal_labels_gap_stop_and_partial_coverage(self):
        plan = dict(side='buy', entry_points='100000', stop_points='99900', target_points='100200', entry_ts_ms=1000, horizon_ms=3000)
        events = [dict(ts_ms=1000, price_points=100300), dict(ts_ms=2000, price_points=99850), dict(ts_ms=5000, price_points=100500)]
        label = label_path(plan, events, coverage_verified=True)
        self.assertEqual(label['label'], 'stop')
        self.assertEqual(label['gross_points'], '-150')
        self.assertEqual(label['outcome_ts_ms'], 2000)
        self.assertEqual(label_path(plan, events, coverage_verified=False)['label'], 'censored')
        with self.assertRaises(ValueError):
            label_path(plan, list(reversed(events)), coverage_verified=True)

    def test_sessions_and_outcomes_never_cross_temporal_split(self):
        rows = [dict(session=f'2026-01-{i:02}', entry_ts_ms=i*10000, outcome_ts_ms=i*10000+1000, feature_asof_ms=i*10000) for i in range(1, 11)]
        train, calibration, test = temporal_split(rows)
        self.assertLess(max(x['outcome_ts_ms'] for x in train), min(x['entry_ts_ms'] for x in calibration))
        self.assertLess(max(x['outcome_ts_ms'] for x in calibration), min(x['entry_ts_ms'] for x in test))
        rows[0]['feature_asof_ms'] += 1
        with self.assertRaises(ValueError):
            temporal_split(rows)

    def test_lab_progressions_do_not_enter_live_engine_and_tail_measure(self):
        self.assertEqual(risk_quantity('martingale', equity=400, initial=400, stop_loss=20, state={'loss_streak': 3}), 8)
        self.assertEqual(risk_quantity('paroli', equity=400, initial=400, stop_loss=20, state={'win_streak': 3}), 8)
        self.assertEqual(risk_quantity('current_fraction', equity=800, initial=400, stop_loss=20), 4)
        self.assertEqual(risk_quantity('current_fraction', equity=600, initial=400, stop_loss=20), 3)
        risk = tail_risk([-100, -50, 0, 50, 100], alpha=.8)
        self.assertEqual(risk['var_loss_brl'], 50)
        self.assertEqual(risk['expected_shortfall_brl'], 100)
        result = trajectory([100, -50], 'fixed_lot', initial=400, margin=155)
        self.assertEqual(result['equity_path'], ['400.00', '500.00', '450.00'])
        self.assertGreater(result['max_drawdown'], 0)

    def test_policy_tail_uses_actual_quantity_and_economic_replay_can_wait(self):
        result = trajectory([100, -50], 'fixed_cash', initial=400, margin=50, stop_loss=20)
        self.assertEqual(result['realized_net_brl'], ['200.00', '-100.00'])
        rows = [dict(id='a', entry_ts_ms=1000, outcome_ts_ms=2000, gross_points='200'), dict(id='b', entry_ts_ms=1500, outcome_ts_ms=2500, gross_points='200'), dict(id='c', entry_ts_ms=3000, outcome_ts_ms=4000, gross_points='-100')]
        predictions = [dict(id=r['id'], probabilities={'target': .1, 'stop': .9}) for r in rows]
        report = economic_replay(rows, predictions, {'target': [200], 'stop': [-100]}, CostSchedule(), initial=400)
        self.assertEqual(report['final_equity_brl'], '400.00')
        self.assertEqual([r['quantity'] for r in report['decisions']], [0, 0, 0])
        self.assertFalse(report['deployment_approved'])

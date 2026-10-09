"""Public contextual contract; synthetic facts, no model requests."""
import unittest

from context_cycle import build_context
from flow_engine import FlowEngine


def candidate():
    return dict(id='buy', side='buy', entry_points='100000', stop_points='99900',
                target_points='100200', premise='Observed buying advances price',
                hypothesis_version='continuation-v2',
                hypotheses={'absorption': 'Observed selling fails to advance price'})


def contextual(snapshot):
    return build_context(dict(snapshot, source_generation=1, application_mode='synthetic'),
                         [candidate()], engine_session_id='S', market_session_id='M')


def observed_books(observations):
    engine = FlowEngine('WIN_SIM')
    engine.set_source_quality(dict(feed_connected=True, sequence_ok=True, full_tape=False))
    for stamp, quantity, depth in observations:
        book = dict(symbol='WIN_SIM', ts_ms=stamp,
                    bids=[dict(price_points=str(price), quantity=quantity)
                          for price in (100000, 99995, 99990)[:depth]],
                    asks=[dict(price_points=str(price), quantity=quantity)
                          for price in (100005, 100010, 100015)[:depth]])
        if not engine.set_book(book)['accepted']:
            raise AssertionError('Synthetic book must be accepted')
    return engine


class ContextBookEvidenceTests(unittest.TestCase):
    def test_book_limits_are_shared_by_choice_and_independent_dimensions(self):
        bundle = contextual(dict(symbol='WIN_SIM', ts_ms=11000,
                                 computed_features={}, evidence_coverage={}, hypotheses=[]))
        explanation = bundle['state']['book_comparison_explanation']
        self.assertIn('snapshots observados', explanation)
        self.assertIn('cancelamento', explanation)
        self.assertIn('execução', explanation)
        self.assertIn('absorção', explanation)
        self.assertEqual(bundle['question_version'], 'independent-context-v6-book-evidence')
        self.assertEqual(bundle['state']['context_contract_version'], bundle['question_version'])
        self.assertEqual(len(bundle['questions']), 7)
        self.assertEqual(set(bundle['questions']['principal_choice']['criteria']),
                         {'buy_continuation', 'sell_continuation', 'wait'})
        for question in bundle['questions'].values():
            self.assertIn('evidence.comparison', question['instructions'])
            self.assertIn('book_comparison_explanation', question['instructions'])
            self.assertIn('Other questions have no answers available.', question['instructions'])
        self.assertEqual({binding['dimension'] for binding in bundle['bindings'].values()},
                         {'support', 'contradiction', 'insufficient'})

    def test_latest_shallow_book_and_its_missing_evidence_reach_shared_state(self):
        engine = observed_books([(10000, 100, 3), (10100, 20, 3), (10200, 90, 1)])
        snapshot = engine.snapshot(10200)
        state = contextual(snapshot)['state']
        book_evidence = [h for h in state['observed_phenomena'] if h['kind'] == 'liquidity_withdrawal']
        self.assertEqual(len(book_evidence), 2)
        for hypothesis in book_evidence:
            self.assertEqual(hypothesis['evidence']['comparison'], dict(
                scope='consecutive_observed_snapshots', before_ts_ms=10100, after_ts_ms=10200,
                elapsed_ms=100, before_age_ms=100, after_age_ms=0,
                before_depth_levels=3, after_depth_levels=1))
            self.assertEqual(hypothesis['status'], 'inconclusive')
            self.assertIn('DEPTH_SEQUENCE_REQUIRED', hypothesis['missing'])
            self.assertIsNone(hypothesis['evidence']['displayed_quantity_reduction_fraction'])
            self.assertTrue(hypothesis['descriptive_only'])
            self.assertIsNone(hypothesis['future_profit_probability'])
        self.assertEqual(state['observed_phenomena'], snapshot['hypotheses'])
        self.assertFalse(state['evidence_coverage']['source_quality']['full_tape'])


if __name__ == '__main__':
    unittest.main()

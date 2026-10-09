import unittest
from context_requests import attach_candidates


class ContextContractTests(unittest.TestCase):
    def test_literal_premise_and_independent_dimensions_survive_transport(self):
        row = dict(id='buy_0', side='buy', entry_points='100', stop_points='90',
                   target_points='110', premise='Exact hypothesis supplied by generator',
                   reference_levels=[], reference_evidence_ids=['a', 'b'],
                   hypothesis_version='continuation-v2', hypotheses={'absorption': 'Selling is absorbed'})
        state, questions = {}, {}
        attach_candidates(state, questions, [row])
        self.assertEqual(state['candidate_setups'][0]['premise'], row['premise'])
        self.assertEqual(state['candidate_setups'][0]['hypotheses'], row['hypotheses'])
        self.assertIn('candidate_0_insufficient', questions)
        self.assertIn('candidate_0_absorption_support', questions)
        self.assertNotIn('missing decisive coverage', questions['candidate_0_contradiction']['instructions'])


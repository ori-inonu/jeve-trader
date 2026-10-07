"""Offline annotations test semantics, not the JEV model's predictive quality."""
import json
from pathlib import Path
import unittest

from context_cycle import build_context, interpret_response
from flow_engine import FlowEngine, generate_flow_scenario
from test_context_cycle import row, response


class MesaContextCases(unittest.TestCase):
    def test_material_book_and_broker_changes_are_scheduled_but_capture_clock_is_not(self):
        from copy import deepcopy
        from test_context_cycle import market
        from live_context import relevant_projection
        facts=market()
        facts['order_flow']=dict(book={'bids':[{'price_points':100000,'quantity':5}], 'asks':[{'price_points':100005,'quantity':7}], 'captured_at_ms':30000},
                                brokers=[{'broker':'A','net_contracts':3}],investor_positions_known=False)
        original=relevant_projection(facts,[],1)
        later=deepcopy(facts); later['order_flow']['book']['captured_at_ms']+=250
        self.assertEqual(original,relevant_projection(later,[],1))
        later['order_flow']['book']['bids'][0]['quantity']=10
        self.assertNotEqual(original,relevant_projection(later,[],1))
        later=deepcopy(facts); later['order_flow']['brokers'][0]['net_contracts']=7
        self.assertNotEqual(original,relevant_projection(later,[],1))

    def test_annotated_flow_meanings_and_missing_evidence(self):
        cases=json.loads((Path(__file__).parent/'fixtures/mesa_context_cases.json').read_text(encoding='utf-8'))['cases']
        for case in cases:
            with self.subTest(case=case['id']):
                fixture=generate_flow_scenario(case['mode'],side=case['aggressor'])
                engine=FlowEngine(fixture['symbol'])
                engine.set_source_quality(dict(fixture['source_quality'],full_tape=case['coverage']!='partial'))
                for event in fixture['events']:
                    (engine.add_trade if event['type']=='trade' else engine.set_book)(event)
                if case['coverage']=='unknown_aggressor':
                    engine.add_trade(dict(id='unknown',symbol=fixture['symbol'],ts_ms=fixture['now_ms'],price_points='131175',quantity=8,aggressor='unknown'))
                snapshot=engine.snapshot(fixture['now_ms'])
                hypothesis=next(h for h in snapshot['hypotheses'] if h['kind']==case['mode'] and h['aggressor_side']==case['aggressor'])
                self.assertEqual(hypothesis['status'],case['status'])
                self.assertEqual(hypothesis['scenario_side'],case['scenario'])
                self.assertIsNone(hypothesis['future_profit_probability'])
                self.assertEqual(bool(hypothesis['missing']),case['status']=='inconclusive')

    def test_shared_facts_literal_binding_and_independent_dimensions(self):
        from test_context_cycle import market
        facts=market()
        facts['order_flow']=dict(brokers=[dict(broker='OBSERVADA',net_contracts=4)],broker_scope='observed window only',
                                 broker_identified_trades=2,investor_positions_known=False,source_capabilities={'full_tape':False},
                                 book={'bids':[{'price_points':str(100000-i*5),'quantity':4} for i in range(30)],
                                       'asks':[{'price_points':str(100005+i*5),'quantity':2} for i in range(30)]},
                                 volume_at_price=[{'price_points':100000+i*5,'quantity':5} for i in range(40)],
                                 ocr_text='private pixels',formulas=['private formula'])
        facts['hypotheses']=[dict(kind='absorption',aggressor_side='sell',scenario_side='buy',status='inconclusive',missing=['FULL_TAPE_NOT_VERIFIED'])]
        candidate=dict(row('buy'),hypotheses={'absorption':'Selling aggression fails to advance downward.',
                                            'exhaustion':'Buying weakens; selling is not established.'})
        bundle=build_context(facts,[candidate],engine_session_id='S',market_session_id='M')
        absorption=bundle['absorption_candidates'][0]
        exhaustion=bundle['exhaustion_candidates'][0]
        self.assertEqual((absorption['aggressor_side'],absorption['scenario_side']),('sell','buy'))
        self.assertEqual((exhaustion['aggressor_side'],exhaustion['scenario_side']),('buy',None))
        self.assertEqual(bundle['state']['hypotheses'][absorption['candidate_key']]['literal_premise'],candidate['hypotheses']['absorption'])
        self.assertEqual(bundle['state']['order_flow']['brokers'],facts['order_flow']['brokers'])
        self.assertEqual(len(bundle['state']['order_flow']['book']['bids']),20)
        self.assertEqual(len(bundle['state']['order_flow']['volume_at_price']),32)
        self.assertEqual(bundle['state']['observed_phenomena'],facts['hypotheses'])
        self.assertNotIn('private',json.dumps(bundle['state']))
        answer=response(bundle)
        for qid,binding in bundle['bindings'].items():
            answer['answers'][qid]['noul']={'support':.7,'contradiction':.8,'insufficient':.9}[binding['dimension']]
        interpreted=interpret_response(bundle,answer)
        for dimensions in interpreted['context_by_candidate'].values():
            self.assertEqual(dimensions,dict(support=.7,contradiction=.8,insufficient=.9))
        self.assertIn('state.order_flow',bundle['questions']['principal_choice']['instructions'])

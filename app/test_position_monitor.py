import tempfile
import unittest
from decision_store import DecisionStore
from position_monitor import monitor_position
from decision_engine import CostSchedule

class PositionTests(unittest.TestCase):
    def test_partial_entries_exits_revisions_and_alert_never_executes(self):
        with tempfile.TemporaryDirectory() as d:
            s=DecisionStore(d)
            s.open_position('a','buy',2,'100000','310','2','WINV26',executed_at_ms=1000,hypothesis={'candidate_key':'origin'})
            s.open_position('b','buy',2,'100100','310','2','WINV26',executed_at_ms=2000)
            p=s.account().positions[0]
            self.assertEqual(p['entry_points'],'100050')
            self.assertEqual(p['quantity'],4)
            self.assertTrue(any(x['kind']=='financial_divergence' for x in s.history()))
            s.revise_position(key='r',expected_revision=s.account().revision,stop='99900',target='100200',premise='manual continuation')
            revision=s.account().revision
            before=s.account().to_dict()
            monitor=monitor_position(s.account(),price='100205',price_at_ms=3000,now_ms=3000,costs=CostSchedule(),context_status='incompatible')
            self.assertIn('TARGET_CROSSED_OBSERVED',monitor['alerts'])
            self.assertIn('CONTEXT_INVALIDATED',monitor['alerts'])
            self.assertEqual(before,s.account().to_dict())
            s.close_position('x',1,'100200','1',executed_at_ms=4000)
            s.close_position('x',1,'100200','1',executed_at_ms=4000)
            self.assertEqual(s.account().positions[0]['quantity'],3)
            self.assertEqual(s.account().positions[0]['realized_brl'],'25.00')
            with self.assertRaises(ValueError):s.revise_position(key='r2',expected_revision=revision,stop='99900',target='100200',premise='old draft')
            self.assertEqual(s.account().positions[0]['hypothesis_origin']['candidate_key'],'origin')
            s.close()

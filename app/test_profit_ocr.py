import unittest

from profit_ocr import validate_selection, observation



class ProfitOcrTests(unittest.TestCase):
    def test_region_bounded_and_off_has_no_capture(self):
        selected=dict(handle=42, title='Profit Pro', x=0,y=0,width=640,height=400,region_kind='book')
        self.assertEqual(validate_selection(selected)['region_kind'],'book')
        for change in (dict(handle=True),dict(width=5000),dict(x=-1),dict(title='Other'),dict(region_kind='unknown')):
            with self.assertRaises(ValueError): validate_selection({**selected,**change})

    def test_ocr_never_claims_ids_continuity_or_confidence(self):
        state = observation({'lines':['12:01:02 130000 5 C','ilegível'], 'captured_at_ms':123,'received_at_ms':173,'duration_ms':50,'region_kind':'times_trades'})
        self.assertEqual(state['region_kind'],'times_trades')
        self.assertEqual(state['observation_type'],'ocr_text_snapshot')
        self.assertEqual(state['captured_at_ms'],123)
        self.assertEqual(state['received_at_ms'],173)
        self.assertEqual(state['coverage'],'partial')
        self.assertFalse(state['continuity_verified'])
        self.assertIsNone(state['lost_market_events'])
        self.assertEqual(state['rows'],['12:01:02 130000 5 C','ilegível'])
        self.assertNotIn('events',state)
        self.assertEqual(state['legibility'],'não calibrada; requer conferência visual')

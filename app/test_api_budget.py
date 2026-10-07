from datetime import datetime, timezone
import tempfile
import unittest
from api_budget import ApiBudget

NOW=int(datetime(2026,10,7,12,tzinfo=timezone.utc).timestamp()*1000)
CONFIG=dict(daily_calls=2,daily_spend='1.00',reserve_per_call='0.50',price_per_call='0.20',
            currency='BRL',source='informed test price',effective_from='2026-10-07',effective_until='2026-10-07',
            conservative_basis='Confirmed upper bound for this contract',upper_bound_confirmed=True)

class ApiBudgetTests(unittest.TestCase):
    def test_pending_consumption_survives_restart_and_does_not_reset_on_configure(self):
        with tempfile.TemporaryDirectory() as d:
            b=ApiBudget(d);b.configure(CONFIG,now_ms=NOW)
            b.reserve('one',now_ms=NOW);b.mark_response('one',usage={'input_tokens':1,'output_tokens':2})
            b.close();b=ApiBudget(d);b.configure(CONFIG,now_ms=NOW)
            self.assertEqual(b.snapshot(now_ms=NOW)['reserved'],'0.50')
            self.assertEqual(b.snapshot(now_ms=NOW)['estimated'],'0.20')
            b.reserve('two',now_ms=NOW)
            with self.assertRaises(ValueError):b.reserve('three',now_ms=NOW)
            b.confirm('one','0.10',reference='billing item',now_ms=NOW)
            b.confirm('one','0.10',reference='billing item',now_ms=NOW)
            with self.assertRaises(ValueError): b.confirm('one','0.11',reference='billing item',now_ms=NOW)
            self.assertEqual(b.snapshot(now_ms=NOW)['confirmed'],'0.10')
            self.assertEqual(b.snapshot(now_ms=NOW)['calls'],2)
            b.close()

    def test_two_connections_reserve_atomically_and_missing_or_expired_price_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            b=ApiBudget(d);c=ApiBudget(d)
            with self.assertRaises(ValueError): b.reserve('x',now_ms=NOW)
            bad=dict(CONFIG,upper_bound_confirmed=False)
            with self.assertRaises(ValueError):b.configure(bad,now_ms=NOW)
            b.configure(dict(CONFIG,daily_calls=10,daily_spend='0.50'),now_ms=NOW)
            b.reserve('x',now_ms=NOW)
            with self.assertRaises(ValueError):c.reserve('y',now_ms=NOW)
            with self.assertRaises(ValueError):b.reserve('z',now_ms=NOW+86400000)
            b.close();c.close()

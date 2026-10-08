import json
from contextlib import ExitStack
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from desktop_service import DecisionService
from profit_bridge import QuoteSnapshot, SourceBatch, SourceHealth


class Collector:
    batches = []
    def __init__(self, config): pass
    def poll(self): return self.batches.pop(0) if self.batches else None
    def close(self): return None


PROFILE = dict(symbol='WINV26', workbook='Private.xlsx', quote_sheet='Cotacoes', quote_range='A1:C2', tape_sheet='', tape_range='')


class CapturePilotTests(unittest.TestCase):
    def test_pilot_requires_the_real_capture_mode_and_never_sends_jev(self):
        with tempfile.TemporaryDirectory() as directory:
            service = DecisionService(directory, client_factory=lambda **kw: self.fail('Pilot must not call JEV'))
            try:
                with self.assertRaisesRegex(ValueError, 'Excel'):
                    service.command('pilot.start', {})
                service.command('source.demo', {})
                with self.assertRaisesRegex(ValueError, 'Excel'):
                    service.command('pilot.start', {})
                self.assertEqual(service.snapshot()['pilot']['status'], 'idle')
                self.assertEqual(service.snapshot()['jev']['calls'], 0)
            finally: service.close()

    def test_real_capture_report_has_separate_timings_and_no_private_rows(self):
        wall, mono = 1791293400., 100.
        with tempfile.TemporaryDirectory() as directory, patch('desktop_service.ExcelCollector', Collector), \
             patch('capture_pilot.time.time', side_effect=lambda: wall), \
             patch('capture_pilot.time.monotonic', side_effect=lambda: mono):
            service = DecisionService(directory)
            try:
                service.command('source.excel', PROFILE)
                start = service.command('pilot.start', {})['pilot']
                for offset, quote_age in ((.25, 10), (.5, 25), (.75, 3000)):
                    mono, wall = 100+offset, 1791293400+offset
                    ts = int(wall*1000)
                    Collector.batches = [dict(batch=SourceBatch((), (QuoteSnapshot('WINV26',130000,ts_ms=ts-quote_age),),
                        SourceHealth('EXCEL_COMBINED_SNAPSHOT',True,False,ts-quote_age,ts),
                        capabilities=dict(trade_id=False), evidence=dict(captured_at_ms=ts-5,polling_effective_ms=250,rtd_change_interval_ms=500)).to_dict())]
                    service.tick()
                    service.snapshot()
                    service.snapshot()  # duplicate snapshots must not multiply capture samples
                mono += 1800
                wall += 9999  # the duration must not use the wall clock
                result = service.command('pilot.stop', dict(pilot_id=start['id']))['pilot']
                self.assertEqual(result['duration_ms'], 1800750)
                self.assertEqual(result['capture_samples'], 3)
                self.assertEqual(result['timings']['quote_age_on_receive_ms']['p95_ms'], 3000)
                self.assertEqual(result['timings']['capture_to_receive_ms']['p95_ms'], 5)
                self.assertEqual(result['timings']['visual_after_receive_ms']['count'], 0)
                self.assertEqual(result['coverage']['fresh_quote_samples'], 2)
                self.assertEqual(result['coverage']['full_tape_samples'], 0)
                self.assertEqual(result['acceptance'], 'PENDING_REAL_REVIEW')
                self.assertIn('visual_samples_missing', result['pending'])
                exported = Path(result['report_path']).read_text(encoding='utf-8')
                self.assertNotIn('Private.xlsx', exported)
                self.assertNotIn('130000', exported)
                self.assertNotIn('equity_brl', exported)
                self.assertFalse(service.snapshot()['jev']['enabled'])
                self.assertEqual(json.loads(exported)['id'], start['id'])
            finally: service.close()

    def test_interruption_contract_change_and_restart_cannot_complete_a_pilot(self):
        with tempfile.TemporaryDirectory() as directory, patch('desktop_service.ExcelCollector', Collector), ExitStack() as cleanup:
            service = DecisionService(directory)
            cleanup.callback(lambda: None if service.closed else service.close())
            service.command('source.excel', PROFILE)
            pilot_id = service.command('pilot.start', {})['pilot']['id']
            with self.assertRaises(ValueError): service.command('pilot.start', {})
            service.command('pilot.mark', dict(pilot_id=pilot_id, scenario='scroll'))
            service.command('pilot.mark', dict(pilot_id=pilot_id, scenario='scroll'))
            service.command('source.disconnect', {})
            service.command('source.excel', {**PROFILE,'symbol':'WINZ26'})
            changed = service.snapshot()['pilot']
            self.assertEqual(changed['interruptions'], 1)
            self.assertEqual(changed['contract_changes'], 1)
            self.assertEqual([s['scenario'] for s in changed['scenarios']], ['scroll'])
            self.assertEqual(changed['scenarios'][0]['evidence_kind'], 'operator_declaration')
            with self.assertRaises(ValueError): service.command('pilot.stop', dict(pilot_id='old'))
            with self.assertRaises(ValueError): service.command('pilot.mark', dict(pilot_id=pilot_id, scenario='fabricated'))
            service.close()
            restarted = DecisionService(directory)
            try:
                report = restarted.snapshot()['pilot']
                self.assertEqual(report['status'], 'interrupted')
                self.assertIn('process_interrupted', report['pending'])
                self.assertEqual(report['acceptance'], 'PENDING_REAL_REVIEW')
                self.assertFalse(restarted.snapshot()['jev']['enabled'])
            finally: restarted.close()

    def test_visual_histogram_is_bound_to_the_active_pilot_and_flags_slow_p95(self):
        with tempfile.TemporaryDirectory() as directory, patch('desktop_service.ExcelCollector', Collector):
            service = DecisionService(directory)
            try:
                service.command('source.excel', PROFILE)
                pid = service.command('pilot.start', {})['pilot']['id']
                with self.assertRaises(ValueError):
                    service.command('pilot.stop',dict(pilot_id=pid,visual=dict(buckets=[[100,True]],excluded=0,overflow=0)))
                self.assertEqual(service.snapshot()['pilot']['status'], 'recording')
                visual = dict(buckets=[[100,94],[251,6]],excluded=12,overflow=0)
                report = service.command('pilot.stop',dict(pilot_id=pid,visual=visual))['pilot']
                self.assertEqual(report['timings']['visual_after_receive_ms']['count'], 100)
                self.assertEqual(report['timings']['visual_after_receive_ms']['p95_ms'], 251)
                self.assertEqual(report['timings']['visual_after_receive_ms']['excluded'], 12)
                self.assertIn('visual_p95_above_250ms', report['pending'])
                self.assertEqual(report['acceptance'], 'PENDING_REAL_REVIEW')
            finally: service.close()

    def test_failed_and_off_late_attempts_are_measured_without_reviving_jev(self):
        with tempfile.TemporaryDirectory() as directory, patch('desktop_service.ExcelCollector', Collector):
            service = DecisionService(directory)
            try:
                service.command('source.excel', PROFILE)
                pilot = service.command('pilot.start', {})['pilot']
                base = dict(call_id='failed',submitted_at_ms=pilot['started_at_ms'],mode='excel_observation',
                            control_revision=service.control_revision,latency_ms=3400,status='FAILED_NO_VALID_RESPONSE')
                for call_id, submitted, latency in (('before',pilot['started_at_ms']-1,10),('failed',pilot['started_at_ms'],3400),
                                                    ('failed',pilot['started_at_ms'],3400),('late-off',pilot['started_at_ms']+1,4500)):
                    service.results.put(dict(error='local failed response',attempt={**base,'call_id':call_id,'submitted_at_ms':submitted,'latency_ms':latency}))
                    service.tick()
                result = service.command('pilot.stop',dict(pilot_id=pilot['id']))['pilot']
                self.assertEqual(result['timings']['jev_response_ms']['count'],2)
                self.assertEqual(result['timings']['jev_response_ms']['p95_ms'],4500)
                self.assertEqual(result['jev_attempts']['failed'],2)
                self.assertFalse(service.snapshot()['jev']['enabled'])
                self.assertIsNone(service.snapshot()['directional']['temperature'])
            finally: service.close()

    def test_report_save_failure_is_visible_and_can_be_retried(self):
        with tempfile.TemporaryDirectory() as directory, patch('desktop_service.ExcelCollector', Collector):
            service = DecisionService(directory)
            try:
                service.command('source.excel', PROFILE)
                with patch('capture_pilot.Path.mkdir', side_effect=OSError('disk full')):
                    pilot=service.command('pilot.start', {})['pilot']
                    self.assertTrue(pilot['save_error'])
                    self.assertIn('report_save_failed',pilot['pending'])
                    failed=service.command('pilot.stop',dict(pilot_id=pilot['id']))['pilot']
                    self.assertTrue(failed['save_error'])
                    self.assertIn('report_save_failed',failed['pending'])
                retried=service.command('pilot.save',dict(pilot_id=pilot['id']))['pilot']
                self.assertIsNone(retried['save_error'])
                self.assertNotIn('report_save_failed',retried['pending'])
                self.assertEqual(json.loads(Path(retried['report_path']).read_text(encoding='utf-8'))['id'],pilot['id'])
            finally: service.close()


if __name__ == '__main__': unittest.main()

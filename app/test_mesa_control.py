import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from desktop_service import DecisionService
from candidate_research import generate_candidate_scenario


class MesaControlTests(unittest.TestCase):
    def test_explicit_demo_publishes_its_observed_book_and_chart(self):
        with tempfile.TemporaryDirectory() as directory:
            service = DecisionService(directory)
            try:
                state = service.command('source.demo', {})
                self.assertEqual(state['market']['application_mode'], 'synthetic')
                self.assertEqual(state['market']['order_flow']['book']['kind'], 'synthetic_book_snapshot')
                self.assertGreater(len(state['market']['order_flow']['book_history']), 0)
                self.assertGreater(len(service.session.chart), 0)
                self.assertFalse(state['jev']['enabled'])
            finally: service.close()

    def test_missing_ocr_runtime_is_visible_without_starting_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            service = DecisionService(directory)
            try:
                with patch('desktop_service.runtime_status', return_value=dict(available=False, engine='tesseract', version=None, error='Runtime OCR local ausente')), patch('desktop_service.capture_profit') as capture:
                    service.command('source.ocr', dict(enabled=True, selection=dict(handle=42, title='Profit Pro', x=0, y=0, width=640, height=400, region_kind='book')))
                    service.tick()
                    capture.assert_not_called()
                state=service.snapshot()
                self.assertIn('Runtime OCR local ausente', state['source']['ocr']['error'])
                self.assertFalse(state['source']['ocr']['runtime']['available'])
                self.assertIsNone(state['source']['ocr'].get('observation'))
                self.assertFalse(state['jev']['enabled'])
            finally: service.close()

    def test_ocr_off_discards_a_late_observation(self):
        entered, release=threading.Event(), threading.Event()
        def capture(config):
            entered.set(); release.wait(2)
            return dict(rows=['private OCR text'], coverage='partial')
        with tempfile.TemporaryDirectory() as directory:
            service=DecisionService(directory)
            try:
                self.assertFalse(service.snapshot()['source']['ocr']['enabled'])
                with patch('desktop_service.runtime_status', return_value=dict(available=True, engine='tesseract', version='5.5.3', error=None)), patch('desktop_service.capture_profit', side_effect=capture):
                    service.command('source.ocr', dict(enabled=True, selection=dict(handle=42, title='Profit Pro', x=0, y=0, width=640, height=400, region_kind='book')))
                    service.tick()
                    self.assertTrue(entered.wait(2))
                    service.command('source.ocr', dict(enabled=False))
                    release.set()
                    for _ in range(100):
                        service.tick()
                        if not service.ocr_pending: break
                        time.sleep(.005)
                state=service.snapshot()
                self.assertEqual(state['source']['ocr']['status'], 'off')
                self.assertIsNone(state['source']['ocr'].get('observation'))
                self.assertFalse(state['jev']['enabled'])
                self.assertEqual(state['jev']['calls'], 0)
            finally:
                release.set(); service.close()

    def test_off_during_call_accounts_usage_without_reviving_context_or_backoff(self):
        for failure in (False, True):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                entered, release = threading.Event(), threading.Event()
                calls = []
                class Client:
                    def __init__(self, **kwargs): pass
                    def evaluate(self, state, questions):
                        calls.append(state)
                        entered.set()
                        release.wait(2)
                        if failure: raise ValueError('offline failure')
                        answers = {k:dict(type='noul', noul=.1 if k.endswith(('contradiction','insufficient')) else .9)
                                   for k,q in questions.items() if q['type']=='noul'}
                        answers['principal_choice'] = dict(type='choice', choice='buy_continuation', confidence=.9,
                            probabilities=dict(buy_continuation=.95,sell_continuation=.02,wait=.03))
                        return dict(model='jev-1.13.0', answers=answers, usage=dict(input_tokens=1000,output_tokens=100))
                now = 1791293400000
                with patch('desktop_service.time.time', return_value=now/1000):
                    service = DecisionService(directory, client_factory=Client)
                    try:
                        fixture = generate_candidate_scenario('WINV26', end_ms=now)
                        service.session.reset('WINV26')
                        service.session.mode = 'excel_observation'
                        service.session.engine.set_source_quality(fixture['source_quality'])
                        for event in fixture['events']:
                            (service.session.engine.add_trade if event['type']=='trade' else service.session.engine.set_book)(event)
                        service.api_key = 'offline-fixture'
                        service.command('jev.set_enabled', {'enabled':True})
                        service.command('jev.evaluate', {})
                        self.assertTrue(entered.wait(2))
                        off_started, off_returned = threading.Event(), threading.Event()
                        def turn_off():
                            off_started.set()
                            with patch.object(service, 'snapshot', return_value={}):
                                service.command('jev.set_enabled', {'enabled':False})
                            off_returned.set()
                        off_thread = threading.Thread(target=turn_off)
                        off_thread.start()
                        self.assertTrue(off_started.wait(2))
                        self.assertFalse(off_returned.wait(.05), 'OFF acknowledgement waits for the active API attempt')
                        release.set()
                        self.assertTrue(off_returned.wait(2), 'OFF completes after the active attempt returns')
                        off_thread.join(2)
                        off = service.snapshot()
                        self.assertEqual(off['jev']['status'], 'draining')
                        trade_count = off['market']['computed_features']['trade_count']
                        self.assertGreater(trade_count, 0)
                        with self.assertRaisesRegex(ValueError, 'desligado'): service.request_jev()
                        # ON must wait for the previous call and cannot accept its revision.
                        service.command('jev.set_enabled', {'enabled':True})
                        service.command('context.configure', {'automatic':False})
                        for _ in range(200):
                            service.tick()
                            if not service.pending_jev: break
                            time.sleep(.005)
                        state = service.snapshot()
                        self.assertFalse(state['jev']['pending'])
                        self.assertIsNone(state['directional']['temperature'])
                        self.assertFalse(state['alert']['active'])
                        self.assertEqual(state['jev_retry_in_ms'], 0)
                        self.assertIsNone(state['jev_error'])
                        self.assertEqual(len(calls), 1)
                        self.assertEqual(state['budget']['unknown_attempts'], 1 if failure else 0)
                    finally:
                        release.set()
                        service.close()

    def test_off_cannot_complete_between_final_gate_and_external_invocation(self):
        entered, release = threading.Event(), threading.Event()
        off_started, off_returned = threading.Event(), threading.Event()
        off_threads, off_results, off_returned_before_dispatch, calls = [], [], [], []
        service = None

        class Client:
            def __init__(self, **kwargs):
                pass

            @property
            def evaluate(self):
                def turn_off():
                    off_started.set()
                    # Commands normally run on the desktop/UI thread. Snapshot
                    # is the only part of this command that touches SQLite, so
                    # keep this concurrency test focused on the control gate.
                    with patch.object(service, 'snapshot', return_value={}):
                        off_results.append(service.command('jev.set_enabled', {'enabled': False}))
                    off_returned.set()

                off_thread = threading.Thread(target=turn_off)
                off_threads.append(off_thread)
                off_thread.start()
                # This is the boundary immediately before invoking the fake
                # external API. On the old path, OFF could finish after the
                # worker's check but before this callable was entered.
                off_returned_before_dispatch.append(off_returned.wait(.5))

                def send(state, questions):
                    calls.append((state, questions))
                    entered.set()
                    release.wait(2)
                    answers = {key: dict(type='noul', noul=.1 if key.endswith(('contradiction', 'insufficient')) else .9)
                               for key, question in questions.items() if question['type'] == 'noul'}
                    answers['principal_choice'] = dict(type='choice', choice='buy_continuation', confidence=.9,
                        probabilities=dict(buy_continuation=.95, sell_continuation=.02, wait=.03))
                    return dict(model='jev-1.13.0', answers=answers, usage=dict(input_tokens=1000, output_tokens=100))

                return send

        now = 1791293400000
        with tempfile.TemporaryDirectory() as directory, patch('desktop_service.time.time', return_value=now / 1000):
            service = DecisionService(directory, client_factory=Client)
            try:
                fixture = generate_candidate_scenario('WINV26', end_ms=now)
                service.session.reset('WINV26')
                service.session.mode = 'excel_observation'
                service.session.engine.set_source_quality(fixture['source_quality'])
                for event in fixture['events']:
                    (service.session.engine.add_trade if event['type'] == 'trade' else service.session.engine.set_book)(event)
                service.api_key = 'offline-fixture'
                service.command('jev.set_enabled', {'enabled': True})
                service.command('jev.evaluate', {})

                self.assertTrue(entered.wait(2), 'the fake external API should be invoked')
                self.assertTrue(off_started.is_set(), 'the concurrent OFF command should reach the dispatch boundary')
                self.assertEqual(off_returned_before_dispatch, [False],
                    'OFF must not acknowledge while the dispatch gate is held before API invocation')
                self.assertFalse(off_returned.wait(.05), 'OFF acknowledgment waits for the in-flight dispatch gate')

                release.set()
                self.assertTrue(off_returned.wait(2), 'OFF should complete after the fake API attempt returns')
                for _ in range(200):
                    service.tick()
                    if not service.pending_jev:
                        break
                    time.sleep(.005)
                state = service.snapshot()
                self.assertFalse(state['jev']['enabled'])
                self.assertFalse(state['jev']['current'])
                self.assertEqual(len(calls), 1)
                self.assertEqual(state['budget']['unknown_attempts'], 0)
            finally:
                release.set()
                for off_thread in off_threads:
                    off_thread.join(2)
                service.close()

    def test_off_blocks_manual_and_automatic_calls_and_restart_starts_off(self):
        calls = []
        class Client:
            def __init__(self, **kwargs): calls.append(kwargs)
            def evaluate(self, *args): raise AssertionError('OFF must never send')
        with tempfile.TemporaryDirectory() as directory:
            service = DecisionService(directory, client_factory=Client)
            try:
                service.api_key = 'offline-fixture'
                self.assertFalse(service.snapshot()['jev']['enabled'])
                with self.assertRaisesRegex(ValueError, 'desligado'):
                    service.command('jev.evaluate', {})
                self.assertEqual(service.snapshot()['budget']['unknown_attempts'], 0)
                self.assertTrue(service.command('jev.set_enabled', {'enabled':True})['jev']['enabled'])
                self.assertFalse(service.command('jev.set_enabled', {'enabled':False})['jev']['enabled'])
                service.tick()
                self.assertEqual(calls, [])
            finally: service.close()
            service = DecisionService(directory)
            try: self.assertFalse(service.snapshot()['jev']['enabled'])
            finally: service.close()


if __name__ == '__main__': unittest.main()

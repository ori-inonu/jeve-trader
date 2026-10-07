import tempfile
import unittest
from unittest.mock import patch
import profit_bridge as bridge
from app_core import ObservationSession


class LiveCaptureTests(unittest.TestCase):
    def test_context_failure_backs_off_without_changing_response_validity(self):
        from live_context import ContextCadence
        cadence = ContextCadence()
        self.assertTrue(cadence.start('one', 10000, 1000))
        cadence.fail(11000)
        self.assertFalse(cadence.start('two', 13999, 1000))
        self.assertTrue(cadence.start('two', 14000, 1000))
        cadence.fail(15000)
        self.assertFalse(cadence.start('three', 20999, 1000))
        self.assertTrue(cadence.start('three', 21000, 1000))
        cadence.finish(success=True)
        self.assertEqual(cadence.retry_at_ms, 0)
        self.assertEqual(cadence.retry_delay_ms, 3000)

    def test_excel_discovery_reads_only_metadata_and_balances_com(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        native = SimpleNamespace(CoInitialize=Mock(), CoUninitialize=Mock())
        sheet = SimpleNamespace(Name='Cotacoes')
        sheets = SimpleNamespace(Count=1, Item=Mock(return_value=sheet))
        book = SimpleNamespace(Name='Mesa.xlsx', Worksheets=sheets)
        books = SimpleNamespace(Count=1, Item=Mock(return_value=book))
        client = SimpleNamespace(GetActiveObject=Mock(return_value=SimpleNamespace(Workbooks=books)))
        result = bridge.discover_open_excel(com_modules=(native, client))
        self.assertEqual(result['workbooks'], [dict(workbook='Mesa.xlsx', sheets=['Cotacoes'])])
        self.assertFalse(result['cells_read'])
        client.GetActiveObject.assert_called_once_with('Excel.Application', dynamic=True)
        native.CoUninitialize.assert_called_once_with()
        books.Count = 101
        books.Item.reset_mock()
        with self.assertRaises(bridge.BridgeError):
            bridge.discover_open_excel(com_modules=(native, client))
        books.Item.assert_not_called()

    def test_saved_excel_profile_reconnects_with_new_generation_and_disconnect_persists(self):
        from desktop_service import DecisionService
        configs = []
        class Collector:
            def __init__(self, config): configs.append(dict(config))
            def poll(self): raise ValueError('fixture: Excel ocupado')
            def close(self): pass
        config = dict(symbol='WINV26', workbook='Mesa.xlsx', quote_sheet='Cotacoes', quote_range='A1:F2', tape_sheet='', tape_range='')
        with tempfile.TemporaryDirectory() as directory, patch('desktop_service.ExcelCollector', Collector):
            service = DecisionService(directory)
            try:
                service.command('source.excel', config)
                generation = service.session.source_generation
                service.tick()
                self.assertIsNone(service.collector)
                self.assertGreater(service.session.source_generation, generation)
                self.assertIsNone(service.snapshot()['directional']['temperature'])
            finally: service.close()
            service = DecisionService(directory)
            try:
                service.tick()
                self.assertEqual(configs[-1], config)
                self.assertTrue(service.reconnect_enabled)
                service.command('source.disconnect', {})
            finally: service.close()
            service = DecisionService(directory)
            try:
                self.assertFalse(service.reconnect_enabled)
            finally: service.close()

    def test_corrected_excel_trade_is_not_silently_discarded(self):
        seen = bridge.SeenTradeIds()
        original = bridge.MarketEvent('42', 'WINV26', 1791293400000, 130000, 2, 'buy')
        self.assertTrue(seen.accept(original))
        self.assertFalse(seen.accept(original))
        with self.assertRaises(bridge.BridgeError):
            seen.accept(bridge.MarketEvent('42', 'WINV26', original.ts_ms, original.price_points, 4, 'sell'))

    def test_quote_only_excel_never_manufactures_tape_or_book(self):
        rows = [['symbol', 'last', 'bid', 'ask', 'ts_ms'], ['WINV26', 130000, 129995, 130000, 1791293400000]]
        with patch.object(bridge, '_load_comtypes', return_value=object()), patch.object(bridge, '_read_excel_com_ranges', return_value=[rows]), patch.object(bridge.os, 'name', 'nt'):
            reader = bridge.CombinedExcelBridge('Mesa.xlsx', 'Cotacoes', 'A1:E2', '', '', symbol='WINV26')
            batch = reader.read()
        state = ObservationSession('WINV26').ingest(batch)
        self.assertEqual(batch.events, ())
        self.assertFalse(batch.health.complete)
        self.assertIsNone(batch.health.to_dict()['feed_connected'])
        self.assertEqual(state['computed_features']['trade_count'], 0)
        self.assertFalse(state['evidence_coverage']['book_fresh'])
        self.assertEqual(state['last_quote']['last'], 130000)

    def test_pilot_unknown_attempt_remains_reserved_after_restart(self):
        from live_context import PilotBudget
        with tempfile.TemporaryDirectory() as directory:
            path = directory + '/pilot.sqlite3'
            budget = PilotBudget(path, daily='0.005', total='0.01')
            budget.reserve('first', now_ms=1791293400000)
            budget.close()
            budget = PilotBudget(path, daily='0.005', total='0.01')
            self.assertEqual(budget.snapshot(1791293400000)['reserved_usd'], '0.002688')
            with self.assertRaises(ValueError):
                budget.reserve('second', now_ms=1791293401000)
            budget.settle('first', {'input_tokens': 1000, 'output_tokens': 9000})
            budget.reserve('second', now_ms=1791293402000)
            self.assertEqual(budget.snapshot(1791293402000)['estimated_usd'], '0.000042')
            self.assertIsNone(budget.snapshot(1791293402000)['billed_usd'])
            budget.close()

    def test_scheduler_keeps_only_latest_change_and_does_not_repeat(self):
        from live_context import ContextCadence
        cadence = ContextCadence()
        self.assertTrue(cadence.start('A', 0, 1000))
        self.assertFalse(cadence.start('B', 100, 1000))
        self.assertFalse(cadence.start('C', 1100, 1000))
        cadence.finish()
        self.assertTrue(cadence.start('C', 1100, 1000))
        cadence.finish()
        self.assertFalse(cadence.start('C', 5000, 1000))
        self.assertTrue(cadence.start('D', 5000, 1000))

    def test_alert_requires_valid_live_geometry_and_rearm(self):
        from live_context import ContextAlert
        alert = ContextAlert()
        self.assertIsNone(alert.update(90, valid=False, geometry=True, now_ms=0))
        first = alert.update(85, valid=True, geometry=True, now_ms=1000)
        self.assertEqual(first['side'], 'buy')
        self.assertIsNone(alert.update(95, valid=True, geometry=True, now_ms=20000))
        alert.update(40, valid=True, geometry=True, now_ms=21000)
        self.assertEqual(alert.update(-90, valid=True, geometry=True, now_ms=22000)['side'], 'sell')
        self.assertIsNone(alert.update(None, valid=False, geometry=False, now_ms=23000))

    def test_service_config_is_persistent_secret_is_not_in_snapshot_and_late_result_expires(self):
        from desktop_service import DecisionService
        class Vault:
            key = ''
            def read(self): return self.key
            def write(self, key): self.key = key
            def delete(self): self.key = ''
        vault = Vault()
        with tempfile.TemporaryDirectory() as directory:
            service = DecisionService(directory, credential_vault=vault)
            try:
                service.command('jev.configure', {'api_key': 'test-local-fixture', 'limit': 120})
                data = service.command('context.configure', {'cadence_ms': 1000, 'horizon_seconds': 5})
                self.assertEqual(data['schema_version'], 2)
                self.assertNotIn('test-local-fixture', str(data))
                self.assertEqual(data['context_settings']['horizon_seconds'], 5)
                self.assertIsNone(data['directional']['temperature'])
                result = dict(expires_at_ms=0, parameter_revision=data['context_settings']['revision'],
                              source_generation=service.session.source_generation, account_revision=service.store.account().revision,
                              costs=data['costs'], flow_ts_ms=0)
                self.assertFalse(service.accepts(result))
            finally:
                service.close()

            service = DecisionService(directory, credential_vault=vault)
            try:
                self.assertTrue(service.snapshot()['jev']['configured'])
                self.assertEqual(service.snapshot()['context_settings']['horizon_seconds'], 5)
            finally:
                service.close()

    def test_real_source_cycle_uses_typed_batch_once_and_rejects_late_reply(self):
        import threading
        import time
        from desktop_service import DecisionService
        from candidate_research import generate_candidate_scenario
        now = 1791293400000
        fixture = generate_candidate_scenario('WINV26', end_ms=now)
        trades = tuple(bridge.MarketEvent(e['id'], e['symbol'], e['ts_ms'], float(e['price_points']), e['quantity'], e['aggressor']) for e in fixture['events'] if e['type']=='trade')
        batch = bridge.SourceBatch(trades, (bridge.QuoteSnapshot('WINV26', 131000, 131000, 131005, 50, 50, now),),
                                   bridge.SourceHealth('EXCEL_COMBINED_SNAPSHOT', True, False, now, now, sequence_ok=True), ())
        class Collector:
            def __init__(self, config): self.read = False
            def poll(self):
                if self.read: return None
                self.read = True
                return {'batch': batch.to_dict()}
            def close(self): pass
        finished = threading.Event()
        calls = []
        class Client:
            def __init__(self, **kwargs): pass
            def evaluate(self, state, questions):
                calls.append((state, questions))
                answers = {k:dict(type='noul', noul=.1 if k.endswith(('contradiction', 'insufficient')) else .9) for k,q in questions.items() if q['type']=='noul'}
                answers['principal_choice'] = dict(type='choice', choice='buy_continuation', confidence=.9,
                    probabilities={'buy_continuation':.95,'sell_continuation':.02,'wait':.03})
                finished.set()
                return dict(model='jev-1.13.0', answers=answers, usage=dict(input_tokens=1000, output_tokens=100))
        with tempfile.TemporaryDirectory() as directory, patch('desktop_service.ExcelCollector', Collector), patch('desktop_service.time.time', return_value=now/1000):
            service = DecisionService(directory, client_factory=Client)
            try:
                service.api_key = 'local-fixture-only'
                service.command('source.excel', dict(symbol='WINV26', workbook='Mesa.xlsx', quote_sheet='Cotacoes', quote_range='A1:F2', tape_sheet='Negocios', tape_range='A1:F1000'))
                service.tick()
                self.assertTrue(finished.wait(2))
                for _ in range(100):
                    service.tick()
                    if not service.pending_jev: break
                    time.sleep(.001)
                state = service.snapshot()
                self.assertEqual(len(calls), 1)
                self.assertEqual(state['directional']['temperature'], 93)
                self.assertTrue(state['alert']['active'])
                self.assertFalse(state['source']['capabilities']['full_tape'])
                self.assertNotIn('account', calls[0][0])
                self.assertTrue(any(h['family']=='exhaustion' for h in state['hypothesis_context']))
                for _ in range(10): service.tick()
                self.assertEqual(len(calls), 1)
                service.credential_revision += 1
                self.assertIsNone(service.snapshot()['directional']['temperature'])
                service.command('context.configure', {'validity_ms':500})
                with patch('desktop_service.time.time', return_value=(now+600)/1000):
                    with self.assertRaisesRegex(ValueError, 'validade'):
                        service.request_jev()
                    self.assertEqual(len(calls), 1)
                with patch('desktop_service.time.time', return_value=(now+3000)/1000):
                    self.assertIsNone(service.snapshot()['directional']['temperature'])
                    self.assertFalse(service.snapshot()['alert']['active'])
            finally:
                service.close()

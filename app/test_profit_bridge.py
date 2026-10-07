import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import profit_bridge as bridge


class ProfitBridgeTests(unittest.TestCase):
    def csv(self, text):
        temp = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
        temp.write(text.encode('utf-8-sig'))
        temp.close()
        self.addCleanup(lambda: Path(temp.name).unlink(missing_ok=True))
        return temp.name

    def test_ptbr_tape_explicit_aggression_and_local_date(self):
        path = self.csv('id;ativo;data;hora;preço;quantidade;agressor\n'
                        '101;WINV26;06/10/2026;10:30:00,125;130.000,5;2;Compra\n')
        batch = bridge.read_csv_events(path, 'WINV26')
        event = batch.events[0]
        self.assertEqual(event.price_points, 130000.5)
        self.assertEqual(event.quantity, 2)
        self.assertEqual(event.aggressor, 'BUY')
        self.assertEqual(event.ts_ms, bridge._timestamp('2026-10-06T13:30:00.125Z'))
        self.assertFalse(batch.health.complete)
        self.assertEqual(event.to_dict()['id'], '101')

    def test_missing_ids_preserve_identical_prints(self):
        path = self.csv('symbol,ts_ms,price_points,quantity,aggressor\n'
                        'WINV26,1791293400000,130000,2,buy\n'
                        'WINV26,1791293400000,130000,2,buy\n')
        seen = bridge.SeenTradeIds()
        batch = bridge.read_csv_events(path, 'WINV26', seen_ids=seen)
        self.assertEqual(len(batch.events), 2)
        self.assertIsNone(batch.events[0].trade_id)
        self.assertTrue(any('sem ID' in warning for warning in batch.warnings))

    def test_explicit_ids_dedup_across_polls(self):
        path = self.csv('id,symbol,ts_ms,price_points,quantity,aggressor\n'
                        '10,WINV26,1791293400000,130000,2,buy\n')
        seen = bridge.SeenTradeIds()
        self.assertEqual(len(bridge.read_csv_events(path, 'WINV26', seen_ids=seen).events), 1)
        self.assertEqual(len(bridge.read_csv_events(path, 'WINV26', seen_ids=seen).events), 0)
        repeated = bridge.read_csv_events(path, 'WINV26', seen_ids=seen)
        self.assertTrue(repeated.health.connected)
        self.assertEqual(repeated.health.last_event_ts_ms, 1791293400000)
        self.assertTrue(repeated.health.sequence_ok)

    def test_duplicate_ids_in_one_file(self):
        path = self.csv('id,symbol,ts_ms,price_points,quantity,aggressor\n'
                        '10,WINV26,1791293400000,130000,2,buy\n'
                        '10,WINV26,1791293400000,130000,2,buy\n')
        self.assertEqual(len(bridge.read_csv_events(path, 'WINV26').events), 1)

    def test_excel_serial_date_time(self):
        serial_date = (bridge.datetime(2026, 10, 6) - bridge.datetime(1899, 12, 30)).days
        self.assertEqual(bridge._timestamp(10.5 / 24, date_value=serial_date),
                         bridge._timestamp('2026-10-06T10:30:00-03:00'))
        self.assertEqual(bridge._timestamp(serial_date + 10.5 / 24),
                         bridge._timestamp('2026-10-06T10:30:00-03:00'))

    def test_cache_bounded(self):
        seen = bridge.SeenTradeIds(1)
        for ident in ('a', 'b'):
            seen.accept(bridge.MarketEvent(ident, 'WINV26', 1791293400000, 130000, 1, 'BUY'))
        self.assertEqual(len(seen.ids), 1)
        self.assertEqual(seen.evictions, 1)

    def test_invalid_quantity_and_unknown_aggressor(self):
        path = self.csv('id;ts_ms;preço;quantidade;agressor\n'
                        '1;1791293400000;130000;1,5;Compra\n'
                        '2;1791293400001;130000;2;12\n')
        batch = bridge.read_csv_events(path, 'WINV26')
        self.assertEqual(len(batch.events), 1)
        self.assertEqual(batch.events[0].aggressor, 'UNKNOWN')
        self.assertTrue(any('inválida' in warning for warning in batch.warnings))

    def test_time_without_date_refused(self):
        path = self.csv('id;timestamp;preço;quantidade;agressor\n'
                        '1;10:30:00;130000;2;Compra\n')
        batch = bridge.read_csv_events(path, 'WINV26')
        self.assertFalse(batch.events)
        self.assertFalse(batch.health.connected)

    def test_quote_never_generates_tape_or_timestamp(self):
        path = self.csv('ativo;ULT;OCP;OVD;VOC;VOV;QUL\n'
                        'WINV26;130000;129995;130000;10;12;3\n')
        batch = bridge.read_csv_events(path, 'WINV26', mode='quote')
        self.assertFalse(batch.events)
        self.assertEqual(batch.quotes[0].last, 130000)
        self.assertIsNone(batch.quotes[0].ts_ms)
        self.assertFalse(batch.health.complete)

    def test_partial_final_row(self):
        path = self.csv('id,symbol,ts_ms,price_points,quantity,aggressor\n'
                        '1,WINV26,1791293400000,130000,2,buy\n2,WINV26,')
        batch = bridge.read_csv_events(path, 'WINV26')
        self.assertEqual(len(batch.events), 1)
        self.assertIn('Última linha incompleta ignorada.', batch.warnings)

    def test_limit_and_regressive_timestamps(self):
        path = self.csv('id,ts_ms,price_points,quantity,aggressor\n'
                        '1,1791293400002,130000,2,buy\n'
                        '2,1791293400001,130000,2,sell\n')
        self.assertFalse(bridge.read_csv_events(path, 'WINV26').health.sequence_ok)
        self.assertEqual(len(bridge.read_csv_events(path, 'WINV26', max_events=1).events), 1)

    def test_range_guard_prevents_formula_or_external_reference(self):
        for value in ('A:A', '=RUN()', '[evil.xls]S!A1:C10', 'A1:XFD1000', 'A1:B99999'):
            with self.assertRaises(bridge.BridgeError):
                bridge.ExcelBridge('book.xlsx', 'Planilha1', value)
        self.assertEqual(bridge.ExcelBridge('book.xlsx', 'Planilha1', 'A1:H20').cell_range, 'A1:H20')

    def test_excel_requires_windows(self):
        reader = bridge.ExcelBridge('book.xlsx', 'Planilha1', 'A1:H20')
        with patch.object(bridge.os, 'name', 'posix'):
            with self.assertRaisesRegex(bridge.BridgeError, 'Windows'):
                reader.read()

    def test_excel_config_no_shell_interpolation(self):
        # Patch name after constructing Path instances: POSIX pathlib must remain POSIX.
        reader = bridge.ExcelBridge('book.xlsx', 'Planilha1', 'A1:H20')
        script = Path(bridge.__file__).parent / 'helpers' / 'read_excel.ps1'
        self.assertTrue(script.exists())
        source = script.read_text()
        self.assertIn("GetActiveObject('Excel.Application')", source)
        self.assertNotIn('New-Object -ComObject', source)
        self.assertNotIn('.Open(', source)
        self.assertNotIn('.Save(', source)
        self.assertNotIn('Invoke-Expression', source)

    def test_excel_subprocess_encodes_config_and_reads_values(self):
        workbook = "quotes'; Invoke-Expression('secret').xlsx"
        reader = bridge.ExcelBridge(workbook, 'Planilha1', 'A1:H20', symbol='WINV26')
        fake_result = SimpleNamespace(returncode=0, stdout=json.dumps({
            'ok': True, 'rows': [['symbol', 'last', 'date', 'time'],
                                ['WINV26', 130000, '06/10/2026', '10:30:00']]}))
        fake_os = SimpleNamespace(name='nt', environ={'SystemRoot': r'C:\Windows'})
        reader._com_modules = None
        with patch.object(bridge, 'os', fake_os), patch.object(bridge, '_load_comtypes', return_value=None), patch.object(bridge.subprocess, 'run', return_value=fake_result) as run:
            batch = reader.read()
        args, kwargs = run.call_args
        self.assertFalse(kwargs['shell'])
        self.assertNotIn(workbook, args[0])
        decoded = json.loads(bridge.base64.b64decode(args[0][-1]))
        self.assertEqual(decoded['workbook'], workbook)
        self.assertEqual(batch.health.kind, 'RTD_SNAPSHOT')
        self.assertEqual(batch.quotes[0].last, 130000)
        self.assertFalse(batch.events)

    def test_excel_errors_do_not_expose_shell_messages(self):
        reader = bridge.ExcelBridge('quotes.xlsx', 'Planilha1', 'A1:H20')
        fake_os = SimpleNamespace(name='nt', environ={'SystemRoot': r'C:\Windows'})
        fake_result = SimpleNamespace(returncode=1, stdout='SECRET', stderr='SECRET C:/private/file')
        reader._com_modules = None
        with patch.object(bridge, 'os', fake_os), patch.object(bridge, '_load_comtypes', return_value=None), patch.object(bridge.subprocess, 'run', return_value=fake_result):
            with self.assertRaises(bridge.BridgeError) as raised:
                reader.read()
        self.assertNotIn('SECRET', str(raised.exception))
        self.assertNotIn('private', str(raised.exception))

    def test_excel_timeout_is_sanitized(self):
        reader = bridge.ExcelBridge('quotes.xlsx', 'Planilha1', 'A1:H20')
        fake_os = SimpleNamespace(name='nt', environ={'SystemRoot': r'C:\Windows'})
        reader._com_modules = None
        with patch.object(bridge, 'os', fake_os), patch.object(bridge, '_load_comtypes', return_value=None), patch.object(bridge.subprocess, 'run', side_effect=bridge.subprocess.TimeoutExpired('SECRET', 8)):
            with self.assertRaisesRegex(bridge.BridgeError, 'prazo'):
                reader.read()

    def test_ambiguous_headers_refused(self):
        path = self.csv('id,ts_ms,price,preco,quantity,aggressor\n1,1791293400000,1,1,1,buy\n')
        with self.assertRaisesRegex(bridge.BridgeError, 'ambígua'):
            bridge.read_csv_events(path, 'WINV26')

    def fake_com(self, rows=None, *, count=1):
        native = SimpleNamespace(CoInitialize=Mock(), CoUninitialize=Mock())
        values = rows if rows is not None else (('symbol', 'last', 'date', 'time'),
                                                ('WINV26', 130000, '06/10/2026', '10:30:00'))
        excel_range = SimpleNamespace(Value2=values)
        class RangeAccessor:
            def __getitem__(self, address):
                self.address = address
                return excel_range
        accessor = RangeAccessor()
        worksheets = SimpleNamespace(Item=Mock(return_value=SimpleNamespace(Range=accessor)))
        book = SimpleNamespace(Name='quotes.xlsx', FullName=r'C:\user\quotes.xlsx', Worksheets=worksheets)
        books = SimpleNamespace(Count=count, Item=Mock(return_value=book))
        excel = SimpleNamespace(Workbooks=books)
        client = SimpleNamespace(GetActiveObject=Mock(return_value=excel))
        return native, client, books, worksheets, accessor

    def test_native_com_existing_only_dynamic_and_balanced(self):
        native, client, books, sheets, accessor = self.fake_com()
        rows = bridge._read_excel_com_rows('quotes.xlsx', 'Dados', 'A1:D2', com_modules=(native, client))
        self.assertEqual(rows[1][1], 130000)
        native.CoInitialize.assert_called_once_with()
        native.CoUninitialize.assert_called_once_with()
        client.GetActiveObject.assert_called_once_with('Excel.Application', dynamic=True)
        books.Item.assert_called_once_with(1)
        sheets.Item.assert_called_once_with('Dados')
        self.assertEqual(accessor.address, 'A1:D2')

    def test_native_com_count_bounded_before_enumeration(self):
        native, client, books, _, _ = self.fake_com(count=101)
        with self.assertRaisesRegex(bridge.BridgeError, '100'):
            bridge._read_excel_com_rows('quotes.xlsx', 'Dados', 'A1:D2', com_modules=(native, client))
        books.Item.assert_not_called()
        native.CoUninitialize.assert_called_once_with()

    def test_native_com_missing_workbook_does_not_read_cells(self):
        native, client, books, sheets, _ = self.fake_com()
        with self.assertRaisesRegex(bridge.BridgeError, 'não encontrado'):
            bridge._read_excel_com_rows('other.xlsx', 'Dados', 'A1:D2', com_modules=(native, client))
        sheets.Item.assert_not_called()
        native.CoUninitialize.assert_called_once_with()

    def test_native_com_sanitizes_attach_errors_and_balances(self):
        native, client, _, _, _ = self.fake_com()
        client.GetActiveObject.side_effect = RuntimeError('SECRET privatepath')
        with self.assertRaises(bridge.BridgeError) as raised:
            bridge._read_excel_com_rows('quotes.xlsx', 'Dados', 'A1:D2', com_modules=(native, client))
        self.assertNotIn('SECRET', str(raised.exception))
        native.CoUninitialize.assert_called_once_with()

    def test_native_com_no_uninitialize_when_initialize_failed(self):
        native, client, _, _, _ = self.fake_com()
        native.CoInitialize.side_effect = RuntimeError('SECRET')
        with self.assertRaisesRegex(bridge.BridgeError, 'COM não inicializado'):
            bridge._read_excel_com_rows('quotes.xlsx', 'Dados', 'A1:D2', com_modules=(native, client))
        native.CoUninitialize.assert_not_called()
        client.GetActiveObject.assert_not_called()

    def test_native_is_preferred_and_permission_failure_has_no_shell_fallback(self):
        reader = bridge.ExcelBridge('quotes.xlsx', 'Dados', 'A1:D2', symbol='WINV26')
        native, client, _, _, _ = self.fake_com()
        reader._com_modules = (native, client)
        fake_os = SimpleNamespace(name='nt', environ={})
        with patch.object(bridge, 'os', fake_os), patch.object(bridge.subprocess, 'run') as shell:
            result = reader.read()
            self.assertEqual(result.quotes[0].last, 130000)
            client.GetActiveObject.side_effect = PermissionError('PRIVATE')
            with self.assertRaises(bridge.BridgeError):
                reader.read()
        shell.assert_not_called()

    def test_native_rejects_nonrectangular_and_nonprimitive_value(self):
        for rows in ((('symbol', 'last'), ('WINV26',)),
                     (('symbol', 'last'), ('WINV26', object()))):
            native, client, _, _, _ = self.fake_com(rows)
            with self.assertRaises(bridge.BridgeError):
                bridge._read_excel_com_rows('quotes.xlsx', 'Dados', 'A1:B2', com_modules=(native, client))
            native.CoUninitialize.assert_called_once_with()

    def combined_fixture(self, *, tape_rows=None, quote_rows=None):
        quote = quote_rows if quote_rows is not None else (
            ('symbol', 'last', 'bid', 'ask', 'bidqty', 'askqty', 'ts_ms'),
            ('WINV26', 130000, 129995, 130000, 10, 12, 1791293400250))
        tape = tape_rows if tape_rows is not None else (
            ('id', 'symbol', 'ts_ms', 'price_points', 'quantity', 'aggressor'),
            ('10', 'WINV26', 1791293400000, 130000, 2, 'Compra'))
        native, client, books, sheets, accessor = self.fake_com()
        class RangeAccessor:
            def __init__(self, rows):
                self.rows = rows
            def __getitem__(self, address):
                return SimpleNamespace(Value2=self.rows)
        sheet_map = {'Dados': SimpleNamespace(Range=RangeAccessor(quote)),
                     'Negocios': SimpleNamespace(Range=RangeAccessor(tape))}
        sheets.Item.side_effect = lambda name: sheet_map[name]
        reader = bridge.CombinedExcelBridge('quotes.xlsx', 'Dados', 'A1:G2',
                                            'Negocios', 'A1:F20', symbol='WINV26')
        reader._com_modules = (native, client)
        return reader, native, client, books, sheets

    def test_combined_one_attach_two_tables_source_timestamps(self):
        reader, native, client, books, sheets = self.combined_fixture()
        with patch.object(bridge, 'os', SimpleNamespace(name='nt', environ={})):
            batch = reader.read()
            repeated = reader.read()
        self.assertEqual(len(batch.events), 1)
        self.assertEqual(len(batch.quotes), 1)
        self.assertEqual(batch.quotes[0].ts_ms, 1791293400250)
        self.assertEqual(batch.health.last_event_ts_ms, 1791293400000)
        self.assertIsNone(batch.health.to_dict()['feed_connected'])
        self.assertFalse(batch.health.complete)
        self.assertFalse(repeated.events)
        self.assertEqual(repeated.health.last_event_ts_ms, 1791293400000)
        self.assertEqual(client.GetActiveObject.call_count, 2)
        self.assertEqual(native.CoInitialize.call_count, 2)
        self.assertEqual(native.CoUninitialize.call_count, 2)
        self.assertEqual([call.args[0] for call in sheets.Item.call_args_list],
                         ['Dados', 'Negocios', 'Dados', 'Negocios'])

    def test_combined_invalid_second_table_does_not_consume_ids(self):
        bad = (('id', 'symbol', 'ts_ms', 'price_points', 'quantity', 'aggressor'),
               ('10', 'WINV26', 1791293400000, 130000, 2, 'Compra'),
               ('11', 'WINV26', 1791293400001, 130000, 1.5, 'Compra'))
        reader, _, _, _, _ = self.combined_fixture(tape_rows=bad)
        with patch.object(bridge, 'os', SimpleNamespace(name='nt', environ={})):
            with self.assertRaisesRegex(bridge.BridgeError, 'linha inválida'):
                reader.read()
        self.assertFalse(reader.seen_ids.ids)

    def test_combined_second_com_failure_no_partial_and_balanced(self):
        reader, native, client, _, sheets = self.combined_fixture()
        original = sheets.Item.side_effect
        def fail_second(name):
            if name == 'Negocios':
                raise PermissionError('PRIVATE')
            return original(name)
        sheets.Item.side_effect = fail_second
        with patch.object(bridge, 'os', SimpleNamespace(name='nt', environ={})), patch.object(bridge.subprocess, 'run') as shell:
            with self.assertRaises(bridge.BridgeError) as error:
                reader.read()
        self.assertNotIn('PRIVATE', str(error.exception))
        native.CoUninitialize.assert_called_once_with()
        client.GetActiveObject.assert_called_once()
        shell.assert_not_called()
        self.assertFalse(reader.seen_ids.ids)

    def test_combined_blank_trade_template_is_not_a_trade(self):
        rows = (('id', 'symbol', 'ts_ms', 'price_points', 'quantity', 'aggressor'),
                (None, None, None, None, None, None))
        reader, _, _, _, _ = self.combined_fixture(tape_rows=rows)
        with patch.object(bridge, 'os', SimpleNamespace(name='nt', environ={})):
            with self.assertRaisesRegex(bridge.BridgeError, 'duas tabelas'):
                reader.read()

    def test_combined_no_synthetic_ids_and_unknown_quote_age(self):
        tape = (('symbol', 'ts_ms', 'price_points', 'quantity', 'aggressor'),
                ('WINV26', 1791293400000, 130000, 2, '12'),
                ('WINV26', 1791293400000, 130000, 2, '12'))
        quote = (('symbol', 'last', 'bid', 'ask'), ('WINV26', 130000, 129995, 130000))
        reader, _, _, _, _ = self.combined_fixture(tape_rows=tape, quote_rows=quote)
        with patch.object(bridge, 'os', SimpleNamespace(name='nt', environ={})):
            batch = reader.read()
        self.assertEqual(len(batch.events), 2)
        self.assertTrue(all(event.trade_id is None and event.aggressor == 'UNKNOWN' for event in batch.events))
        self.assertIsNone(batch.quotes[0].ts_ms)

    def test_combined_requires_native_com_without_policy_fallback(self):
        reader = bridge.CombinedExcelBridge('quotes.xlsx', 'Dados', 'A1:H2',
                                            'Negocios', 'A1:F20', symbol='WINV26')
        reader._com_modules = None
        with patch.object(bridge, 'os', SimpleNamespace(name='nt', environ={})), patch.object(bridge, '_load_comtypes', return_value=None), patch.object(bridge.subprocess, 'run') as shell:
            with self.assertRaisesRegex(bridge.BridgeError, 'comtypes'):
                reader.read()
        shell.assert_not_called()

    def test_combined_pipeline_enables_geometry_with_partial_real_shape(self):
        # These normalized records are explicitly fake, not a live Profit test.
        # They exercise the actual bridge/core/candidate seams that previously
        # could not retain both trades and a two-sided quote simultaneously.
        from app_core import DEFAULT_INPUTS, ObservationSession, build_risk_study
        from candidate_research import build_market_candidates, generate_candidate_scenario
        now = 1791293400000
        fixture = generate_candidate_scenario(symbol='WIN_TEST', end_ms=now)
        tape = [('id', 'symbol', 'ts_ms', 'price_points', 'quantity', 'aggressor')]
        for event in fixture['events']:
            if event['type'] == 'trade':
                tape.append((event['id'], event['symbol'], event['ts_ms'],
                             event['price_points'], event['quantity'], event['aggressor']))
        quote = (('symbol', 'last', 'bid', 'ask', 'bidqty', 'askqty', 'ts_ms'),
                 ('WIN_TEST', 131000, 131000, 131005, 80, 80, now))
        reader, _, _, _, _ = self.combined_fixture(tape_rows=tuple(tape), quote_rows=quote)
        reader.symbol = 'WIN_TEST'
        with patch.object(bridge, 'os', SimpleNamespace(name='nt', environ={})), patch.object(bridge.time, 'time', return_value=now / 1000):
            batch = reader.read()
            session = ObservationSession('WIN_TEST')
            state = session.ingest(batch)
            study = build_risk_study(DEFAULT_INPUTS, now_ms=now)
            report = build_market_candidates(session.engine, state, study['config'], study['account'], now)
        self.assertTrue(batch.events and batch.quotes)
        self.assertFalse(batch.health.complete)
        self.assertIsNone(batch.health.to_dict()['feed_connected'])
        self.assertFalse(state['evidence_coverage']['source_quality']['full_tape'])
        self.assertFalse(state['actionable_live_signal'])
        self.assertEqual(report['status'], 'TECHNICAL_SCENARIOS')
        self.assertGreater(len(report['rows']), 0)
        self.assertEqual(report['evidence_coverage']['quote_source'], 'sampled_quote')
        self.assertTrue(all(row['actionable_live_signal'] is False and row['win_probability'] is None for row in report['rows']))

    def test_sep_hint(self):
        path = self.csv('sep=;\nid;ts_ms;price_points;quantity;aggressor\n1;1791293400000;1,5;1;buy\n')
        self.assertEqual(bridge.read_csv_events(path, 'WINV26').events[0].price_points, 1.5)


if __name__ == '__main__':
    unittest.main()

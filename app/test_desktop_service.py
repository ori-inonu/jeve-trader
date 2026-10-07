import tempfile
import unittest
import json
from pathlib import Path
import subprocess
import sys
from app_store import UserStore
from desktop_service import DecisionService


class ServiceTests(unittest.TestCase):
    def test_sidecar_recovers_after_missing_file_and_malformed_json_then_closes(self):
        with tempfile.TemporaryDirectory() as directory:
            process = subprocess.Popen([sys.executable, '-u', str(Path(__file__).with_name('desktop_service.py')), '--data-dir', directory], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            messages = ['[]', '{bad', json.dumps({'schema_version': 1, 'id': 'bad-path', 'method': 'source.replay', 'params': {'path': str(Path(directory)/'missing.csv')}}), json.dumps({'schema_version': 1, 'id': 'alive', 'method': 'snapshot'})]
            output, error = process.communicate('\n'.join(messages)+'\n', timeout=15)
            self.assertEqual(process.returncode, 0, error)
            replies = [json.loads(line) for line in output.splitlines()]
            self.assertTrue(any(r.get('id')=='bad-path' and 'error' in r for r in replies))
            self.assertTrue(any(r.get('id')=='alive' and 'result' in r for r in replies))

    def test_excel_failure_keeps_account_responsive_and_restores_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = UserStore(directory)
            legacy.save_settings({'sheet': 'Quotes', 'cell_range': 'A1:H2', 'workbook': 'Mesa.xlsx'})
            legacy.close()
            service = DecisionService(directory)
            try:
                self.assertEqual(service.source_config['quote_sheet'], 'Quotes')
                class UnavailableCollector:
                    def poll(self): raise ValueError('occupied')
                    def close(self): self.closed = True
                collector = UnavailableCollector()
                service.collector = collector
                self.assertTrue(service.tick())
                self.assertTrue(collector.closed)
                self.assertIsNone(service.collector)
                self.assertIsNotNone(service.snapshot()['source']['error'])
                self.assertEqual(service.command('account.update', {'equity_brl': '600', 'revision': 0})['account']['equity_brl'], '600')
            finally:
                service.close()

    def test_service_import_has_no_tkinter_dependency(self):
        output = subprocess.check_output([sys.executable, '-c', "import desktop_service,sys; print('tkinter' in sys.modules)"], cwd=Path(__file__).parent, text=True)
        self.assertEqual(output.strip(), 'False')

    def test_independent_service_manual_account_and_demo_no_model_fabrication(self):
        with tempfile.TemporaryDirectory() as directory:
            service = DecisionService(directory)
            try:
                demo = service.command('source.demo', {})
                self.assertEqual(demo['market']['application_mode'], 'synthetic')
                self.assertIsNone(demo['decision']['profit_probability'])
                self.assertEqual(demo['decision']['action'], 'wait')
                self.assertTrue(demo['alternatives'])
                changed = service.command('account.update', {'equity_brl': '800', 'available_margin_brl': '800', 'revision': 0})
                self.assertEqual(changed['account']['equity_brl'], '800')
                self.assertFalse(changed['decision']['order_sent'])
                with self.assertRaises(ValueError):
                    service.command('order.send', {})
                old = dict(source_generation=0, account_revision=0, flow_ts_ms=demo['market']['flow_ts_ms'])
                self.assertFalse(service.accepts(old))
            finally:
                service.close()

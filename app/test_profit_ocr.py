import unittest
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

from profit_ocr import validate_selection, observation
import profit_ocr



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


class NativeProfitOcrTests(unittest.TestCase):
    selection = dict(handle=42, title='Profit Pro', x=0, y=0, width=640, height=400, region_kind='book')

    def runtime(self, root):
        folder = root/'ocr_runtime'
        for name in ('profit-capture.exe', 'tesseract.exe', 'tessdata/eng.traineddata'):
            path = folder/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'offline process boundary fixture')
        files = {name:hashlib.sha256((folder/name).read_bytes()).hexdigest()
                 for name in ('profit-capture.exe', 'tesseract.exe', 'tessdata/eng.traineddata')}
        (folder/'manifest.json').write_text(json.dumps(dict(schema_version=1, engine='tesseract', version='5.5.3', model='eng', files=files)), encoding='utf-8')
        return folder

    def test_missing_or_changed_runtime_is_unavailable_before_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('profit_ocr.resource_path', side_effect=lambda name:root/name), patch('profit_ocr.subprocess.run') as run:
                self.assertFalse(profit_ocr.runtime_status()['available'])
                folder = self.runtime(root)
                self.assertTrue(profit_ocr.runtime_status()['available'])
                (folder/'tesseract.exe').write_bytes(b'changed')
                self.assertFalse(profit_ocr.runtime_status()['available'])
                run.assert_not_called()

    def test_malformed_manifest_is_publicly_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = self.runtime(root)
            (folder/'manifest.json').write_text('[]', encoding='utf-8')
            with patch('profit_ocr.resource_path', side_effect=lambda name:root/name):
                self.assertFalse(profit_ocr.runtime_status()['available'])

    def test_capture_uses_bounded_native_processes_and_removes_pixels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.runtime(root)
            calls, images = [], []
            def external(command, **options):
                calls.append((command, options))
                if Path(command[0]).name == 'profit-capture.exe':
                    path = Path(command[-1]); path.write_bytes(b'pixels'); images.append(path)
                    return subprocess.CompletedProcess(command, 0, '1791293400000\n', '')
                self.assertTrue(images[0].is_file())
                return subprocess.CompletedProcess(command, 0, '12:01:02 130000 5 C\n', '')
            with patch('profit_ocr.resource_path', side_effect=lambda name:root/name), patch('profit_ocr.profit_windows', return_value=[dict(handle=42, title='Profit Pro')]), patch('profit_ocr.subprocess.run', side_effect=external):
                result = profit_ocr.capture_profit(self.selection)
            self.assertEqual([Path(c[0][0]).name for c in calls], ['profit-capture.exe', 'tesseract.exe'])
            self.assertTrue(all(0 < options['timeout'] <= 4 for _,options in calls))
            self.assertTrue(all(not options.get('shell', False) for _,options in calls))
            self.assertFalse(images[0].parent.exists())
            self.assertEqual(result['rows'], ['12:01:02 130000 5 C'])
            self.assertEqual(result['engine'], 'tesseract')
            self.assertEqual(result['coverage'], 'partial')
            self.assertFalse(result['continuity_verified'])
            self.assertNotIn('events', result)

    def test_recognition_timeout_removes_pixels_and_does_not_expose_stderr(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.runtime(root)
            images = []
            def external(command, **options):
                if Path(command[0]).name == 'profit-capture.exe':
                    path=Path(command[-1]); path.write_bytes(b'pixels'); images.append(path)
                    return subprocess.CompletedProcess(command, 0, '1791293400000\n', '')
                raise subprocess.TimeoutExpired(command, options['timeout'], stderr=b'private pixels')
            with patch('profit_ocr.resource_path', side_effect=lambda name:root/name), patch('profit_ocr.profit_windows', return_value=[dict(handle=42, title='Profit Pro')]), patch('profit_ocr.subprocess.run', side_effect=external):
                with self.assertRaisesRegex(ValueError, 'tempo') as error:
                    profit_ocr.capture_profit(self.selection)
            self.assertNotIn('private', str(error.exception))
            self.assertFalse(images[0].parent.exists())

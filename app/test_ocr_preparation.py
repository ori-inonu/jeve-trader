"""Source provenance guard at the public local runtime preparation boundary."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1]/'scripts'/'prepare_ocr_runtime.py'
spec = importlib.util.spec_from_file_location('ocr_preparation', SCRIPT)
preparation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparation)


class OcrPreparationTests(unittest.TestCase):
    def test_external_port_or_triplet_overrides_are_rejected_before_side_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)/'checkout'
            for variable in ('VCPKG_OVERLAY_PORTS', 'VCPKG_OVERLAY_TRIPLETS'):
                with self.subTest(variable=variable), patch.dict(os.environ, {variable:'external'}), \
                     patch('subprocess.run', side_effect=AssertionError('must not launch an external command')):
                    with self.assertRaisesRegex(RuntimeError, 'overlay'):
                        preparation.prepare(checkout, Path(directory)/'vcpkg.exe')
                    self.assertFalse(checkout.exists())

import json
from pathlib import Path
import subprocess
import sys
import unittest


class MultimarketCliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] /
            'scripts' / 'observe_multimarket.py'), *args], capture_output=True, text=True,
            encoding='utf-8', timeout=10)

    def test_default_is_synthetic_and_probabilities_are_unknown(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['origin'], 'synthetic')
        self.assertEqual(value['received_trades'], 3)
        self.assertFalse(value['orders_enabled'])
        self.assertFalse(value['retention_enabled'])
        self.assertIsNone(value['target_probability'])
        self.assertEqual(value['evaluation']['status'], 'pending')

    def test_invalid_duration_fails_before_network_or_fixture(self):
        for duration in ('0', '1801', '1.5'):
            result = self.run_cli('--live', '--duration-seconds', duration)
            self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()

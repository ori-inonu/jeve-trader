import json
from pathlib import Path
import unittest
from context_identity import content_hash, canonical_bytes


class IdentityTests(unittest.TestCase):
    def test_documented_vector_and_mutations(self):
        vector = json.loads((Path(__file__).parent/'fixtures/context_identity_v1.json').read_text(encoding='utf-8'))
        self.assertEqual(content_hash('candidate', vector), 'e76a9bc939f018fd8ed4dc451f2026384ef8a1f922227d8a410f7b2c9ea9c38c')
        self.assertEqual(content_hash('candidate', dict(reversed(list(vector.items())))), content_hash('candidate', vector))
        self.assertEqual(content_hash('candidate', dict(vector, stop_ticks='19979')), 'ce81c0317d1527358666cd404875879f923c9c1781ff5caea3488504de1b84b5')
        self.assertEqual(content_hash('candidate', dict(vector, horizon_ms='120000')), '8bc0bd9cd3e9916cdc9821671e5aba8b2b65405feb6d922e68724fcf5eefb15b')

    def test_rejects_noncanonical_numbers_and_invalid_unicode(self):
        for bad in ({'x': float('nan')}, {'x': .1}, {'x': '\ud800'}):
            with self.assertRaises(ValueError):
                canonical_bytes(bad)

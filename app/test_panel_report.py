from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from app_core import DEFAULT_INPUTS, ObservationSession, build_decision_bundle
from candidate_research import generate_candidate_scenario
from panel_report import render_panel_html, export_panel, option_values


def technical_session():
    fixture = generate_candidate_scenario()
    session = ObservationSession()
    session.mode = 'synthetic'
    session.clock_ms = fixture['now_ms']
    session.engine.set_source_quality(fixture['source_quality'])
    for event in fixture['events']:
        if event['type'] == 'trade':
            session.engine.add_trade(event)
            session.chart.append((event['ts_ms'], float(event['price_points'])))
        else:
            session.engine.set_book(event)
    return session


class PanelReportTests(unittest.TestCase):
    def test_same_bundle_contains_geometry_risk_and_explicit_missing_model(self):
        bundle = build_decision_bundle(technical_session(), DEFAULT_INPUTS)
        self.assertEqual(len(bundle['recommendation']['options']), 8)
        self.assertEqual(bundle['recommendation']['status'], 'AGUARDAR')
        self.assertIn('JEV_NOT_EVALUATED', bundle['recommendation']['reasons'])
        self.assertFalse(bundle['actual_broker_connection'])
        self.assertFalse(bundle['recommendation']['actionable_live_signal'])
        self.assertGreater(len(bundle['chart_points']), 2)
        self.assertIsNone(bundle['recommendation']['win_probability'])

    def test_source_disconnected_cannot_keep_old_chart_or_candidate(self):
        previous = build_decision_bundle(technical_session(), DEFAULT_INPUTS)
        current = build_decision_bundle(None, DEFAULT_INPUTS)
        self.assertGreater(len(previous['recommendation']['options']), 0)
        self.assertEqual(current['recommendation']['status'], 'SEM_DADOS')
        self.assertEqual(current['recommendation']['options'], [])
        self.assertEqual(current['chart_points'], [])
        self.assertIsNone(current['snapshot'])

    def test_invalid_manual_capital_has_no_financial_candidate(self):
        bundle = build_decision_bundle(technical_session(), dict(DEFAULT_INPUTS, current='NaN'))
        self.assertIsNone(bundle['study'])
        self.assertTrue(bundle['input_error'])
        self.assertEqual(bundle['recommendation']['status'], 'BLOQUEADO_RISCO')
        self.assertEqual(bundle['recommendation']['options'], [])

    def test_html_escapes_untrusted_values_and_omits_credentials(self):
        bundle = build_decision_bundle(technical_session(), DEFAULT_INPUTS)
        bundle['snapshot']['symbol'] = '<img src=x onerror="bad()">'
        bundle['authorization'] = 'SECRET_AUTH_TOKEN'
        bundle['snapshot']['api_key'] = 'SECRET_API_KEY'
        bundle['study']['config']['secret'] = 'SECRET_CONFIG'
        before = deepcopy(bundle)
        html = render_panel_html(bundle)
        self.assertIn('&lt;img', html)
        self.assertNotIn('<img', html)
        self.assertNotIn('SECRET_', html)
        self.assertNotIn('<script', html.lower())
        self.assertNotIn('fetch(', html)
        self.assertIn('Registro estático', html)
        self.assertIn('Demonstração sintética', html)
        self.assertEqual(bundle, before)

    def test_export_is_self_contained_and_preserves_computed_risk(self):
        bundle = build_decision_bundle(technical_session(), DEFAULT_INPUTS)
        options = bundle['recommendation']['options']
        funded = [o for o in options if o['contracts'] > 0]
        self.assertTrue(funded)
        self.assertNotEqual(option_values(funded[0])[5], '—')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'painel.html'
            export_panel(path, bundle)
            html = path.read_text(encoding='utf-8')
            self.assertIn('<svg', html)
            self.assertIn('<table', html)
            self.assertIn('Chaves e credenciais não são incluídas', html)
            self.assertNotIn('https://', html)
            self.assertNotIn('src=', html)

    def test_higher_margin_recalculates_instead_of_reusing_displayed_lots(self):
        session = technical_session()
        initial = build_decision_bundle(session, DEFAULT_INPUTS)
        changed = build_decision_bundle(session, dict(DEFAULT_INPUTS, margin='1000'))
        self.assertTrue(any(o['contracts'] > 0 for o in initial['recommendation']['options']))
        self.assertTrue(all(o['contracts'] == 0 for o in changed['recommendation']['options']))
        self.assertEqual(changed['recommendation']['status'], 'BLOQUEADO_RISCO')

    def test_export_preserves_the_assumption_about_an_undated_previous_loss(self):
        bundle = build_decision_bundle(technical_session(), dict(DEFAULT_INPUTS, current='380', loss_streak='1'))
        self.assertEqual(bundle['recommendation']['account_assumptions']['loss_time_assumption'],
                         'manual_scenario_assumes_prior_loss_cooldown_elapsed')
        self.assertIn('este cenário assume que a pausa já foi cumprida', render_panel_html(bundle))


if __name__ == '__main__':
    unittest.main()

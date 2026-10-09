"""Controller tests with a fake view, not a native Windows GUI test."""
import contextlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from app_core import DEFAULT_INPUTS
from app_store import UserStore
from desktop_app import JevWINApp
from test_panel_report import technical_session


class Value:
    def __init__(self, value):
        self.value = value
    def get(self):
        return self.value


class DesktopControllerTests(unittest.TestCase):
    def create(self, directory):
        app = JevWINApp.__new__(JevWINApp)
        app.store = UserStore(Path(directory))
        self.addCleanup(app.store.close)
        app.session = technical_session()
        app.snapshot = app.session.snapshot()
        app.risk_inputs = {k: Value(v) for k, v in DEFAULT_INPUTS.items()}
        app.last_loss_ms = None
        app.latest_jev_result = None
        app.last_decision_refresh = 0
        app.last_decision_signature = None
        app.decision_history = []
        app.decision_panel = Mock()
        app.busy = set()
        return app

    def test_risk_transition_is_persisted_even_without_time_between_changes(self):
        # ExitStack closes the SQLite store before Windows tempdir removal.
        with contextlib.ExitStack() as stack, patch('desktop_app.time.monotonic', return_value=100):
            directory = stack.enter_context(tempfile.TemporaryDirectory())
            app = self.create(directory)
            stack.callback(app.store.close)
            app.refresh_decision(force=True)
            app.risk_inputs['margin'].value = '1000'
            app.refresh_decision(force=True)
            events = app.store.recent(kind='recommendation')
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0]['payload']['status'], 'BLOQUEADO_RISCO')
            self.assertEqual(events[1]['payload']['status'], 'AGUARDAR')
            self.assertEqual(app.decision_panel.render.call_count, 2)

    def test_new_source_generation_is_visible_even_with_same_conclusion(self):
        with contextlib.ExitStack() as stack:
            directory = stack.enter_context(tempfile.TemporaryDirectory())
            app = self.create(directory)
            stack.callback(app.store.close)
            app.refresh_decision(force=True)
            first = app.decision_bundle['recommendation']['status']
            app.session.source_generation += 1
            app.refresh_decision(force=True)
            self.assertEqual(app.decision_bundle['recommendation']['status'], first)
            self.assertEqual(len(app.store.recent(kind='recommendation')), 2)
            self.assertEqual(app.store.recent(kind='recommendation')[0]['payload']['origin']['source_generation'], app.session.source_generation)
            app.refresh_decision(force=True)
            self.assertEqual(len(app.store.recent(kind='recommendation')), 2)


if __name__ == '__main__':
    unittest.main()

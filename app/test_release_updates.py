import unittest
import json
import tempfile
import threading
from urllib.error import HTTPError
from unittest.mock import patch
from release_updates import check_for_updates
from desktop_service import DecisionService


def release(version='0.4.10'):
    return {'tag_name': 'v'+version, 'draft': False, 'prerelease': False,
            'html_url': 'https://github.com/ori-inonu/jeve-trader/releases/tag/v'+version,
            'body': 'Melhorias verificadas',
            'assets': [{'name': 'JevWIN_'+version+'_setup.exe', 'size': 100}]}


class ReleaseUpdateTests(unittest.TestCase):
    def test_newer_installer_release_is_available_using_numeric_version(self):
        result = check_for_updates('0.4.9', fetch=lambda path, token: release())
        self.assertEqual(result['status'], 'available')
        self.assertEqual(result['latest_version'], '0.4.10')
        self.assertEqual(result['release_url'], release()['html_url'])

    def test_equal_and_older_releases_do_not_show_an_update(self):
        for tag in ('0.4.9', '0.4.8'):
            self.assertEqual(check_for_updates('0.4.9', fetch=lambda p, t: release(tag))['status'], 'current')

    def test_missing_asset_draft_or_hostile_link_cannot_offer_installation(self):
        for change in ({'assets': []}, {'draft': True}, {'prerelease': True},
                       {'html_url': 'https://github.com.evil.test/ori-inonu/jeve-trader/releases/tag/v0.4.10'},
                       {'tag_name': 'v0.4.10-preview'}):
            result = check_for_updates('0.4.9', fetch=lambda p, t: {**release(), **change})
            self.assertNotEqual(result['status'], 'available')
            self.assertIsNone(result['release_url'])

    def test_private_repo_without_releases_is_distinct_from_missing_access(self):
        def fetch(path, token):
            if path == '' and token == 'private-token':
                return {'private': True}
            raise HTTPError('https://api.github.com', 404, 'Not Found', {}, None)
        result = check_for_updates('0.4.9', fetch=fetch, credential=lambda: 'private-token')
        self.assertEqual(result['status'], 'no_release')
        self.assertNotIn('private-token', json.dumps(result))
        self.assertEqual(check_for_updates('0.4.9', fetch=fetch, credential=lambda: '')['status'], 'auth_required')

    def test_network_failure_is_not_reported_as_up_to_date_or_leaked(self):
        def offline(path, token):
            raise OSError('secret-token')
        result = check_for_updates('0.4.9', fetch=offline)
        self.assertEqual(result['status'], 'unavailable')
        self.assertNotIn('secret-token', json.dumps(result))

    def test_revoked_git_credential_requests_authentication(self):
        def revoked(path, token):
            raise HTTPError('https://api.github.com', 401 if token else 404, 'Denied', {}, None)
        result = check_for_updates('0.4.9', fetch=revoked, credential=lambda: 'revoked-token')
        self.assertEqual(result['status'], 'auth_required')
        self.assertNotIn('revoked-token', json.dumps(result))

    def test_slow_check_does_not_block_account_and_does_not_start_on_snapshot(self):
        started, finish = threading.Event(), threading.Event()
        calls = []
        def fetch(version):
            calls.append(version)
            started.set()
            finish.wait(3)
            return check_for_updates(version, fetch=lambda p, t: release())
        with tempfile.TemporaryDirectory() as directory, patch('desktop_service.current_version', return_value='0.4.9'):
            service = DecisionService(directory, update_checker=fetch)
            try:
                self.assertEqual(service.snapshot()['updates']['status'], 'idle')
                self.assertEqual(calls, [])
                self.assertEqual(service.command('updates.check', {})['updates']['status'], 'checking')
                self.assertTrue(started.wait(1))
                service.command('updates.check', {})
                changed = service.command('account.update', {'equity_brl': '800', 'revision': 0})
                self.assertEqual(changed['account']['equity_brl'], '800')
                self.assertEqual(len(calls), 1)
                finish.set()
                result = service.update_results.get(timeout=2)
                service.update_results.put(result)
                self.assertTrue(service.tick())
                self.assertEqual(service.snapshot()['updates']['status'], 'available')
                self.assertIsNone(service.snapshot()['source']['error'])
            finally:
                finish.set()
                service.close()


if __name__ == '__main__':
    unittest.main()

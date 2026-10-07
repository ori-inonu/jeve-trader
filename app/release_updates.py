"""Check published Windows releases; credentials never cross the UI boundary."""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from app_store import resource_path

REPOSITORY = 'ori-inonu/jeve-trader'
API_ROOT = 'https://api.github.com/repos/'+REPOSITORY


def current_version():
    return json.loads(resource_path('version.json').read_text(encoding='utf-8'))['version']


def update_state(version, status='idle', **fields):
    return dict(current_version=version, status=status, latest_version=None,
                release_url=None, notes='', checked_at_ms=None, **fields)


def trusted_release_url(url):
    if not isinstance(url, str):
        return False
    parsed = urlsplit(url)
    return (parsed.scheme == 'https' and parsed.netloc == 'github.com'
            and parsed.path.startswith('/'+REPOSITORY+'/releases/tag/')
            and not parsed.query and not parsed.fragment
            and len(parsed.path.split('/releases/tag/', 1)[1]) > 0)


def _version(value):
    if not isinstance(value, str) or not re.fullmatch(r'v?\d+\.\d+\.\d+', value):
        raise ValueError('Invalid stable version')
    return tuple(int(part) for part in value.lstrip('v').split('.'))


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def github_fetch(path, token):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Jeve-Trader',
               'X-GitHub-Api-Version': '2022-11-28'}
    if token:
        headers['Authorization'] = 'Bearer '+token
    request = Request(API_ROOT+path, headers=headers)
    with build_opener(_NoRedirect()).open(request, timeout=5) as response:
        content = response.read(1024*1024+1)
        if len(content) > 1024*1024:
            raise ValueError('Release response too large')
        return json.loads(content)


def git_read_credential():
    """Reuse an existing Git credential without prompting, storing or logging it."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
    try:
        result = subprocess.run(['git', 'credential', 'fill'],
                                input='protocol=https\nhost=github.com\npath='+REPOSITORY+'\n\n',
                                capture_output=True, text=True, timeout=5, env=env,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if result.returncode == 0:
            return dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line).get('password', '')
    except (OSError, subprocess.TimeoutExpired):
        pass
    return ''


def check_for_updates(version, *, fetch=github_fetch, credential=git_read_credential):
    result = update_state(version)
    result['checked_at_ms'] = int(time.time()*1000)
    try:
        _version(version)
        token = ''
        try:
            release = fetch('/releases/latest', token)
        except HTTPError as error:
            error.close()
            if error.code not in (401, 404):
                raise
            token = credential()
            try:
                release = fetch('/releases/latest', token)
            except HTTPError as retry:
                retry.close()
                if retry.code == 401:
                    result['status'] = 'auth_required'
                    return result
                if retry.code != 404:
                    raise
                try:
                    fetch('', token)
                except HTTPError as repo_error:
                    repo_error.close()
                    if repo_error.code in (401, 404):
                        result['status'] = 'auth_required'
                        return result
                    raise
                result['status'] = 'no_release'
                return result
        if not isinstance(release, dict) or release.get('draft') or release.get('prerelease'):
            raise ValueError('Not a published stable release')
        tag = release['tag_name']
        target = _version(tag)
        latest = tag.lstrip('v')
        if not trusted_release_url(release.get('html_url')):
            raise ValueError('Untrusted release URL')
        assets = release.get('assets', [])
        if not isinstance(assets, list) or not any(isinstance(asset, dict)
                and asset.get('name') == 'JevWIN_'+latest+'_setup.exe'
                and type(asset.get('size')) is int and asset['size'] > 0 for asset in assets):
            result['status'] = 'no_installer'
            return result
        result.update(status='available' if target > _version(version) else 'current',
                      latest_version=latest, release_url=release['html_url'],
                      notes=str(release.get('body') or '')[:6000])
    except Exception as error:
        if isinstance(error, HTTPError):
            error.close()
        # Raw transport errors can contain credentials or local paths.
        result['status'] = 'unavailable'
    return result

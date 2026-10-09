import json
import tempfile
import unittest
import threading
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from multimarket.service import MultimarketService
from test_multimarket_domain import instrument, source, market_event
from test_multimarket_runtime import _valid_context_response


class Adapter:
    def __init__(self, *, allowed=False):
        self.items = []
        self.spec = instrument()
        self.caps = replace(source(), retention='allowed' if allowed else 'unknown', export='allowed' if allowed else 'unknown')
        self.stopped = False
        self.resyncs = 0

    def discover(self, symbol):
        return self.spec

    def capabilities(self):
        return self.caps

    def start(self, **params):
        return True

    def drain(self, limit=500):
        result, self.items = self.items[:limit], self.items[limit:]
        return result

    def stop(self):
        self.stopped = True

    def request_resync(self):
        self.resyncs += 1


def connected(service, adapter):
    service.discovery_generation['binance_public_spot'] = 1
    service.discovery_connect['binance_public_spot'] = True
    service._admit_discovery(dict(source_id='binance_public_spot', spec=adapter.spec, generation=1))
    workspace_id = service.snapshot()['selected_workspace_id']
    service._ingest(workspace_id, dict(kind='source_status', status='live', epoch=1))
    for kind, payload in [('quote', None), ('trade', {'price':'100', 'quantity':'1', 'aggressor':'buy'})]:
        service._ingest(workspace_id, market_event(kind=kind, event_id=kind+'-1', epoch=1,
            workspace_id=workspace_id, market_ts_ms=None, received_monotonic_ns=service.clock.monotonic_ns(), payload=payload))
    return workspace_id


class Clock:
    def __init__(self):
        self.wall = 10000
        self.mono = 10_000_000_000

    def wall_ms(self):
        return self.wall

    def monotonic_ns(self):
        return self.mono


class MultimarketIntegrationTests(unittest.TestCase):
    def test_owner_stays_live_after_initial_controls_and_rejects_old_epoch_after_disconnect(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = Adapter()
            service = MultimarketService(directory, clock=Clock(), adapters={'binance_public_spot':adapter})
            try:
                workspace_id = connected(service, adapter)
                self.assertEqual(service.snapshot()['selected']['market']['health']['quote']['status'], 'live')
                self.assertIsNone(service.snapshot()['selected']['market']['quote']['market_ts_ms'])
                service.command('multimarket.disconnect', {})
                service._ingest(workspace_id, dict(kind='metadata', spec=adapter.spec, epoch=1))
                snapshot = service.snapshot()['selected']
                self.assertEqual(snapshot['market']['epoch'], 2)
                self.assertNotEqual(snapshot['market']['health']['quote']['status'], 'live')
                self.assertEqual(snapshot['decision']['quantity'], '0')
            finally:
                service.close()

    def test_pending_discovery_cannot_reconnect_after_user_disconnect(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = Adapter()
            service = MultimarketService(directory, clock=Clock(), adapters={'binance_public_spot':adapter})
            try:
                service.discovery_generation['binance_public_spot'] = 1
                service.discovery_pending.add('binance_public_spot')
                service.command('multimarket.disconnect', {})
                service._admit_discovery(dict(source_id='binance_public_spot', spec=adapter.spec, generation=1))
                self.assertEqual(service.snapshot()['workspaces'], [])
            finally:
                service.close()

    def test_source_policy_blocks_payload_persistence_and_jev_egress(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = Adapter()
            service = MultimarketService(directory, clock=Clock(), adapters={'binance_public_spot':adapter})
            try:
                workspace_id = connected(service, adapter)
                calls = []
                service.configure_jev(lambda *_:calls.append('paid'), lambda *_:calls.append('reserve'), lambda *_:None, lambda:(True, 1))
                service.command('multimarket.recording.set', {'enabled':True})
                service.command('multimarket.jev.set_enabled', {'enabled':True})
                service.tick()
                self.assertEqual(calls, [])
                self.assertEqual(list(service.journal.replay(workspace_id)), [])
                self.assertIn('Política', service.snapshot()['scheduler']['error'])
                self.assertIsNone(service.snapshot()['selected']['context'])
            finally:
                service.close()

    def test_credential_revision_and_cost_revision_invalidate_pending_context(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = Adapter(allowed=True)
            clock = Clock()
            service = MultimarketService(directory, clock=clock, adapters={'binance_public_spot':adapter})
            started, released = threading.Event(), threading.Event()
            credential = [1]
            def executor(*_):
                started.set()
                released.wait(1)
                return _valid_context_response()
            try:
                workspace_id = connected(service, adapter)
                service.configure_jev(executor, lambda *_:None, lambda *_:None, lambda:(True, credential[0]))
                service.command('multimarket.jev.set_enabled', {'enabled':True})
                service.tick()
                self.assertTrue(started.wait(1))
                first = service.snapshot()['selected']['evaluation_identity']
                service.command('multimarket.costs.update', {'costs':{'currency':'USDT','verified':True,'fee_rate':'0.001','slippage':'0.01'}})
                self.assertNotEqual(first['cost_revision'], service.snapshot()['selected']['evaluation_identity']['cost_revision'])
                credential[0] += 1
                service.tick()
                self.assertFalse(service.snapshot()['scheduler']['enabled'])
                released.set()
                for _ in range(20):
                    service.tick()
                    if service._inflight is None: break
                    threading.Event().wait(.01)
                self.assertIsNone(service.snapshot()['selected']['context'])
            finally:
                released.set()
                service.close()

    def test_valid_context_is_causal_journaled_and_not_repeated_or_reaged(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter, clock = Adapter(allowed=True), Clock()
            service = MultimarketService(directory, clock=clock, adapters={'binance_public_spot':adapter})
            calls, settlements = [], []
            def executor(state, questions):
                calls.append((state, questions))
                return _valid_context_response()
            try:
                workspace_id = connected(service, adapter)
                service.configure_jev(executor, lambda *_:None, lambda *args:settlements.append(args), lambda:(True, 1))
                service.command('multimarket.recording.set', {'enabled':True})
                service.command('multimarket.jev.set_enabled', {'enabled':True})
                for _ in range(40):
                    service.tick()
                    if service.snapshot()['selected']['context']: break
                    threading.Event().wait(.005)
                current = service.snapshot()['selected']
                self.assertIsNotNone(current['context'])
                self.assertEqual(current['context']['identity'], current['evaluation_identity'])
                self.assertIsNone(current['context']['financial_probability'])
                self.assertEqual(len(settlements), 1)
                rows = list(service.journal.replay(workspace_id))
                self.assertEqual([row['kind'] for row in rows], ['context_request','context_result'])
                self.assertEqual(rows[0]['payload']['identity'], rows[1]['payload']['identity'])
                self.assertTrue(rows[1]['payload']['accepted_current'])
                self.assertNotIn('account', calls[0][0])
                clock.wall -= 50000
                clock.mono += 1_000_000_000
                service.tick()
                self.assertEqual(service.snapshot()['selected']['context']['age_ms'], 1000)
                clock.mono += 1_001_000_000
                for _ in range(5): service.tick()
                self.assertIsNone(service.snapshot()['selected']['context'])
                self.assertEqual(len(calls), 1)
                self.assertEqual(service.snapshot()['selected']['decision']['quantity'], '0')
            finally:
                service.close()

    def test_context_timeouts_recover_with_bounded_workers_and_ignore_late_results(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter, clock = Adapter(allowed=True), Clock()
            service = MultimarketService(directory, clock=clock, adapters={'binance_public_spot':adapter})
            started = [threading.Event() for _ in range(3)]
            released = [threading.Event() for _ in range(3)]
            call_lock = threading.Lock()
            next_call = [0]
            reservations, settlements = [], []

            def executor(_state, _questions):
                with call_lock:
                    index = next_call[0]
                    next_call[0] += 1
                started[index].set()
                released[index].wait(5)
                return _valid_context_response()

            def refresh_market(workspace_id, label):
                for kind, payload in (
                    ('quote', None),
                    ('trade', {'price': '100', 'quantity': '1', 'aggressor': 'buy'}),
                ):
                    service._ingest(workspace_id, market_event(
                        kind=kind,
                        event_id=f'{kind}-{label}',
                        epoch=1,
                        workspace_id=workspace_id,
                        market_ts_ms=None,
                        received_monotonic_ns=clock.monotonic_ns(),
                        payload=payload,
                    ))

            try:
                workspace_id = connected(service, adapter)
                service.configure_jev(
                    executor,
                    lambda call_id: reservations.append(call_id),
                    lambda call_id, usage: settlements.append((call_id, usage)),
                    lambda: (True, 1),
                )
                service.command('multimarket.jev.set_enabled', {'enabled':True})
                service.tick()
                self.assertTrue(started[0].wait(1))
                first_call = service._inflight

                clock.mono += 10_001_000_000
                refresh_market(workspace_id, 'after-timeout-1')
                service.tick()
                self.assertTrue(started[1].wait(1), 'a timeout should release the scheduler for one fresh request')
                second_call = service._inflight
                self.assertNotEqual(first_call, second_call)

                clock.mono += 10_001_000_000
                refresh_market(workspace_id, 'after-timeout-2')
                service.tick()
                self.assertFalse(started[2].is_set(), 'two unresolved workers must apply bounded backpressure')
                self.assertEqual(next_call[0], 2)
                self.assertFalse(service.snapshot()['scheduler']['in_flight'])

                released[0].set()
                for _ in range(100):
                    service.tick()
                    if started[2].is_set():
                        break
                    threading.Event().wait(.005)
                self.assertTrue(started[2].is_set(), 'a completed old worker should free one bounded slot')
                third_call = service._inflight
                self.assertNotIn(third_call, {first_call, second_call})
                self.assertTrue(service.snapshot()['scheduler']['in_flight'])

                released[1].set()
                for _ in range(100):
                    service.tick()
                    if len(settlements) >= 2:
                        break
                    threading.Event().wait(.005)
                self.assertIn((first_call, _valid_context_response()['usage']), settlements)
                self.assertIn((second_call, _valid_context_response()['usage']), settlements)
                self.assertEqual(service._inflight, third_call, 'late responses must not clear the current call identity')
                self.assertTrue(service.snapshot()['scheduler']['in_flight'])

                released[2].set()
                for _ in range(100):
                    service.tick()
                    if service.snapshot()['selected']['context']:
                        break
                    threading.Event().wait(.005)
                current = service.snapshot()['selected']
                self.assertIsNotNone(current['context'])
                self.assertEqual(current['context']['identity'], current['evaluation_identity'])
                self.assertEqual(len(reservations), 3)
                self.assertEqual(len(settlements), 3)
            finally:
                for event in released:
                    event.set()
                service.close()

    def test_sidecar_outer_versions_preserve_legacy_and_separate_inner_multimarket(self):
        with tempfile.TemporaryDirectory() as directory:
            requests = [dict(schema_version=version, id='mm-'+str(version), method='multimarket.snapshot', params={}) for version in (1,2)]
            requests.append(dict(schema_version=1, id='legacy', method='snapshot', params={}))
            process = subprocess.Popen([sys.executable,'-u',str(Path(__file__).with_name('desktop_service.py')),'--data-dir',directory],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            output, error = process.communicate('\n'.join(map(json.dumps, requests))+'\n', timeout=15)
            self.assertEqual(process.returncode, 0, error)
            replies = {row['id']:row for row in map(json.loads, output.splitlines()) if 'id' in row}
            for version in (1,2):
                self.assertEqual(replies['mm-'+str(version)]['schema_version'], version)
                self.assertEqual(replies['mm-'+str(version)]['result']['schema_version'], 3)
            self.assertEqual(replies['legacy']['result']['schema_version'], 2)

    def test_boot_is_offline_versioned_and_separate_from_legacy_storage(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / 'journal.sqlite3'
            legacy.write_bytes(b'legacy storage fixture')
            service = MultimarketService(directory, clock=Clock(), adapters={})
            try:
                snapshot = service.command('multimarket.snapshot', {})
                self.assertEqual(snapshot['schema_version'], 3)
                self.assertFalse(snapshot['orders_enabled'])
                self.assertIsNone(snapshot['selected'])
                self.assertFalse(snapshot['scheduler']['enabled'])
                self.assertEqual(legacy.read_bytes(), b'legacy storage fixture')
                self.assertIn('b3', snapshot['gates'])
                with self.assertRaises(ValueError):
                    service.command('multimarket.order.send', {})
                json.dumps(snapshot, allow_nan=False)
            finally:
                service.close()

    def test_unknown_recording_policy_and_private_account_are_visible_gates(self):
        with tempfile.TemporaryDirectory() as directory:
            service = MultimarketService(directory, clock=Clock(), adapters={})
            try:
                snapshot = service.command('multimarket.snapshot', {})
                self.assertNotEqual(snapshot['recording']['status'], 'recording')
                self.assertNotEqual(snapshot['gates']['private_account']['status'], 'ready')
                self.assertNotEqual(snapshot['gates']['financial_model']['status'], 'ready')
            finally:
                service.close()


if __name__ == '__main__':
    unittest.main()

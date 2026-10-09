import json
import ssl
import sys
import threading
import tempfile
import unittest
import urllib.request
from unittest.mock import patch

from multimarket.adapters import AdapterError, PublicSpotAdapter
from multimarket.contracts import EvaluationIdentity, SystemClock
from multimarket.network import BinancePublicTransport, NetworkError
from multimarket.journal import Journal
from multimarket.scheduler import ContextScheduler, SchedulerConfig, build_questions


class _Response:
    status = 200

    def __init__(self, body, url):
        self._body = body
        self._url = url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self):
        return self._url

    def read(self, size=-1):
        return self._body[:size]


class ContextQuestionTests(unittest.TestCase):
    def test_questions_use_the_supported_context_only_choice_and_noul_contract(self):
        from jev_client import build_payload

        questions = build_questions()
        payload = build_payload({"market": {"spread": "0.01"}}, questions)

        self.assertEqual(set(payload), {"state", "model", "questions"})
        self.assertEqual(
            set(questions),
            {"direction", "context_support", "context_contradiction", "context_insufficient"},
        )
        self.assertEqual(questions["direction"]["type"], "choice")
        self.assertEqual(
            set(questions["direction"]["criteria"]),
            {"wait", "observe_buy", "observe_sell"},
        )
        for name, term in (
            ("context_support", "support"),
            ("context_contradiction", "contradict"),
            ("context_insufficient", "insufficient"),
        ):
            self.assertEqual(questions[name]["type"], "noul")
            guidance = str(questions[name]["instructions"]).lower()
            self.assertIn(term, guidance)
            self.assertIn("context", guidance)
            self.assertNotIn("profit probability", guidance)


class _ManualClock:
    def __init__(self, now_ns):
        self.now_ns = now_ns

    def wall_ms(self):
        return self.now_ns // 1_000_000

    def monotonic_ns(self):
        return self.now_ns

    def advance_ms(self, amount):
        self.now_ns += amount * 1_000_000


def _evaluation_identity(*, account_id="account-a", received_monotonic_ns=9_500_000_000):
    return EvaluationIdentity(
        workspace_id="workspace-a",
        instrument_id="binance:spot:BTCUSDT",
        source_id="binance_public_spot",
        epoch=4,
        metadata_version="sha256:metadata-v1",
        feature_version="mm-features-v1",
        question_version="mm-context-v1",
        cost_revision=2,
        account_id=account_id,
        account_revision=7 if account_id is not None else None,
        selection_revision=3,
        event_range=("trade:41", "trade:44"),
        received_monotonic_ns=received_monotonic_ns,
    )


def _valid_context_response():
    questions = build_questions()
    return {
        "model": "jev-1.13.0",
        "answers": {
            "direction": {
                "type": "choice",
                "choice": "wait",
                "probabilities": {"wait": 0.6, "observe_buy": 0.2, "observe_sell": 0.2},
                "confidence": 0.6,
            },
            "context_support": {"type": "noul", "noul": 0.4},
            "context_contradiction": {"type": "noul", "noul": 0.2},
            "context_insufficient": {"type": "noul", "noul": 0.7},
        },
        "usage": {"input_tokens": 120, "output_tokens": 30},
    }


class ContextSchedulerTests(unittest.TestCase):
    def test_accepted_context_preserves_identity_and_original_monotonic_age(self):
        clock = _ManualClock(10_000_000_000)
        scheduler = ContextScheduler(SchedulerConfig(min_interval_ms=0), clock=clock)
        identity = _evaluation_identity()

        offered = scheduler.offer(identity, build_questions(), "feature:44")
        call = scheduler.take()
        clock.advance_ms(100)
        completed = scheduler.complete(call["call_id"], _valid_context_response(), identity)

        self.assertEqual(offered["status"], "queued")
        self.assertEqual(call["identity"], identity)
        self.assertEqual(completed["status"], "accepted")
        self.assertTrue(completed["accepted"])
        self.assertEqual(completed["identity"], identity)
        self.assertEqual(completed["origin_monotonic_ns"], identity.received_monotonic_ns)
        self.assertEqual(completed["age_ms"], 600)
        self.assertEqual(completed["answers"], _valid_context_response()["answers"])

    def test_account_id_change_invalidates_an_inflight_context_even_when_revision_matches(self):
        clock = _ManualClock(10_000_000_000)
        scheduler = ContextScheduler(SchedulerConfig(min_interval_ms=0), clock=clock)
        original = _evaluation_identity(account_id="account-a")
        selected_elsewhere = _evaluation_identity(account_id="account-b")
        scheduler.offer(original, build_questions(), "feature:44")
        call = scheduler.take()

        completed = scheduler.complete(call["call_id"], _valid_context_response(), selected_elsewhere)

        self.assertFalse(completed["accepted"])
        self.assertEqual((completed["status"], completed["reason"]), ("stale", "identity_changed"))

    def test_context_expiry_uses_origin_monotonic_time_and_never_renews_on_completion(self):
        clock = _ManualClock(10_000_000_000)
        scheduler = ContextScheduler(SchedulerConfig(min_interval_ms=0, validity_ms=2_000), clock=clock)
        identity = _evaluation_identity(received_monotonic_ns=10_000_000_000)
        scheduler.offer(identity, build_questions(), "feature:44")
        call = scheduler.take()
        clock.advance_ms(2_001)

        completed = scheduler.complete(call["call_id"], _valid_context_response(), identity)

        self.assertFalse(completed["accepted"])
        self.assertEqual((completed["status"], completed["reason"]), ("expired", "context_expired"))

    def test_pending_calls_coalesce_and_queue_capacity_is_bounded(self):
        clock = _ManualClock(10_000_000_000)
        scheduler = ContextScheduler(SchedulerConfig(max_pending=2), clock=clock)
        identity = _evaluation_identity()

        first = scheduler.offer(identity, build_questions(), "feature:44")
        duplicate = scheduler.offer(identity, build_questions(), "feature:44")
        second = scheduler.offer(_evaluation_identity(received_monotonic_ns=9_500_000_001), build_questions(), "feature:45")
        overflow = scheduler.offer(_evaluation_identity(received_monotonic_ns=9_500_000_002), build_questions(), "feature:46")

        self.assertEqual(first["status"], "queued")
        self.assertEqual(duplicate["status"], "coalesced")
        self.assertEqual(second["status"], "queued")
        self.assertEqual((overflow["status"], overflow["reason"]), ("rejected", "queue_full"))
        self.assertEqual(scheduler.snapshot()["pending"], 2)

    def test_dispatched_evidence_is_not_called_twice_without_an_identity_or_feature_change(self):
        clock = _ManualClock(10_000_000_000)
        scheduler = ContextScheduler(SchedulerConfig(min_interval_ms=0), clock=clock)
        identity = _evaluation_identity()
        scheduler.offer(identity, build_questions(), "feature:44")
        call = scheduler.take()
        scheduler.complete(call["call_id"], None, identity)

        unchanged = scheduler.offer(identity, build_questions(), "feature:44")
        changed_feature = scheduler.offer(identity, build_questions(), "feature:45")

        self.assertEqual((unchanged["status"], unchanged["reason"]), ("coalesced", "already_evaluated"))
        self.assertEqual(changed_feature["status"], "queued")

    def test_local_failure_envelope_is_visible_but_never_accepted_as_provider_context(self):
        clock = _ManualClock(10_000_000_000)
        scheduler = ContextScheduler(SchedulerConfig(min_interval_ms=0), clock=clock)
        identity = _evaluation_identity()
        scheduler.offer(identity, build_questions(), "feature:44")
        call = scheduler.take()

        result = scheduler.complete(
            call["call_id"],
            {"error": "Política de processamento/exportação negada.\nTente mais tarde."},
            identity,
        )

        self.assertEqual((result["status"], result["reason"]), (
            "unavailable", "Política de processamento/exportação negada. Tente mais tarde."
        ))
        self.assertFalse(result["accepted"])
        self.assertNotIn("answers", result)
        self.assertEqual(scheduler.snapshot()["error"], result["reason"])


class BinancePublicTransportTests(unittest.TestCase):
    def test_metadata_request_uses_only_the_fixed_market_data_url(self):
        expected_url = "https://data-api.binance.vision/api/v3/exchangeInfo?symbol=BTCUSDT"
        payload = {"symbols": [{"symbol": "BTCUSDT"}]}
        response = _Response(json.dumps(payload).encode(), expected_url)
        with patch("multimarket.network.urllib.request.build_opener") as build_opener:
            build_opener.return_value.open.return_value = response
            result = BinancePublicTransport().get_metadata("BTCUSDT")

        request = build_opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, expected_url)
        self.assertEqual(request.method, "GET")
        self.assertEqual(result, payload)
        handler = next(
            item for item in build_opener.call_args.args
            if isinstance(item, urllib.request.HTTPSHandler)
        )
        self.assertEqual(handler._context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(handler._context.check_hostname)

    def test_metadata_rejects_symbols_outside_the_public_pilot_before_network(self):
        with patch("multimarket.network.urllib.request.build_opener") as build_opener:
            with self.assertRaises(NetworkError):
                BinancePublicTransport().get_metadata("ETHUSDT")
        build_opener.assert_not_called()

    def test_metadata_rejects_duplicate_json_keys(self):
        expected_url = "https://data-api.binance.vision/api/v3/exchangeInfo?symbol=BTCUSDT"
        response = _Response(b'{"symbols":[],"symbols":[]}', expected_url)
        with patch("multimarket.network.urllib.request.build_opener") as build_opener:
            build_opener.return_value.open.return_value = response
            with self.assertRaises(NetworkError):
                BinancePublicTransport().get_metadata("BTCUSDT")

    def test_stream_uses_fixed_tls_endpoint_and_delivers_messages(self):
        seen = []
        stop = threading.Event()

        class _Connection:
            def settimeout(self, _timeout):
                pass

            def recv(self):
                return '{"stream":"btcusdt@trade","data":{}}'

            def close(self):
                pass

        class _WebSocket:
            class WebSocketTimeoutException(Exception):
                pass

            @staticmethod
            def create_connection(url, **kwargs):
                seen.append((url, kwargs))
                return _Connection()

        def received(message):
            seen.append(message)
            stop.set()

        with patch.dict(sys.modules, {"websocket": _WebSocket}):
            BinancePublicTransport().consume(
                stop, on_message=received, on_open=lambda: seen.append("open")
            )

        self.assertEqual(seen[0][0], "wss://data-stream.binance.vision/stream?streams=btcusdt@trade/btcusdt@bookTicker")
        tls = seen[0][1]["sslopt"]
        self.assertEqual(tls["cert_reqs"], ssl.CERT_REQUIRED)
        self.assertTrue(tls["check_hostname"])
        self.assertEqual(seen[1], "open")
        self.assertEqual(seen[2], '{"stream":"btcusdt@trade","data":{}}')


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.journal = Journal(self.temp_dir.name + "/journal.sqlite3")

    def tearDown(self):
        self.journal.close()
        self.temp_dir.cleanup()

    def test_unknown_retention_never_persists_market_payload(self):
        result = self.journal.append(
            "trade",
            "workspace-1",
            "trade-1",
            {"price": "100.00", "quantity": "2.0", "aggressor": "buy"},
            policy={"retention": "unknown", "export": "unknown"},
        )

        self.assertFalse(result["stored"])
        self.assertEqual(list(self.journal.replay("workspace-1")), [])

    def test_allowed_retention_replays_causal_record_and_is_idempotent(self):
        policy = {"retention": "allowed", "export": "allowed"}
        payload = {"event_id": "trade-7", "epoch": 3, "price": "101.25"}
        first = self.journal.append("trade", "workspace-1", "trade-7", payload, policy=policy)
        repeated = self.journal.append("trade", "workspace-1", "trade-7", payload, policy=policy)

        replayed = list(self.journal.replay("workspace-1"))
        self.assertTrue(first["stored"])
        self.assertTrue(repeated["duplicate"])
        self.assertEqual(len(replayed), 1)
        self.assertEqual(replayed[0]["payload"], payload)
        self.assertEqual(replayed[0]["sequence"], first["sequence"])

    def test_replay_pages_large_namespace_without_truncating_causal_records(self):
        policy = {"retention": "allowed", "export": "denied"}
        for index in range(600):
            self.journal.append(
                "evaluation",
                "workspace-1",
                f"call-{index}",
                {"call": index, "status": "accepted"},
                policy=policy,
            )

        replayed = list(self.journal.replay("workspace-1"))
        self.assertEqual(len(replayed), 600)
        self.assertEqual([record["payload"]["call"] for record in replayed], list(range(600)))
        self.assertEqual(replayed[-1]["policy"], policy)


class _FixedClock:
    def wall_ms(self):
        return 1_800_000_000_123

    def monotonic_ns(self):
        return 987_654_321


def _exchange_info():
    return {
        "symbols": [{
            "symbol": "BTCUSDT",
            "status": "TRADING",
            "baseAsset": "BTC",
            "quoteAsset": "USDT",
            "filters": [
                {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
                {"filterType": "LOT_SIZE", "stepSize": "0.00001", "minQty": "0.00001"},
                {"filterType": "MIN_NOTIONAL", "minNotional": "5"},
            ],
        }]
    }


class _SpotTransport:
    def __init__(self, metadata=None, messages=()):
        self.metadata = metadata or _exchange_info()
        self.messages = tuple(messages)
        self.closed = threading.Event()

    def get_metadata(self, symbol):
        if symbol != "BTCUSDT":
            raise AssertionError("adapter requested an unexpected symbol")
        return self.metadata

    def consume(self, stop_event, *, on_message, on_open):
        on_open()
        for message in self.messages:
            if stop_event.is_set():
                return
            on_message(message)
        stop_event.wait(0.5)

    def close(self):
        self.closed.set()


class PublicSpotAdapterTests(unittest.TestCase):
    def test_discovery_hashes_metadata_and_exposes_market_only_capabilities(self):
        adapter = PublicSpotAdapter(_SpotTransport(), clock=_FixedClock())
        spec = adapter.discover()
        caps = adapter.capabilities()

        self.assertEqual((spec.symbol, spec.venue, spec.segment), ("BTCUSDT", "binance", "spot"))
        self.assertEqual((str(spec.price_tick), str(spec.quantity_step), str(spec.minimum_notional)), ("0.01", "0.00001", "5"))
        self.assertTrue(spec.constraints_verified)
        self.assertEqual(len(spec.metadata_version.removeprefix("sha256:")), 64)
        self.assertTrue(caps.quote)
        self.assertTrue(caps.trades)
        self.assertFalse(caps.book)
        self.assertFalse(caps.account)
        self.assertFalse(caps.full_tape)
        self.assertEqual((caps.sequence_scope, caps.book_mode, caps.retention, caps.export), ("unknown", "unavailable", "unknown", "unknown"))

    def test_trade_maps_buyer_is_maker_to_sell_aggressor(self):
        adapter = PublicSpotAdapter(_SpotTransport(), clock=_FixedClock())
        spec = adapter.discover()
        event = adapter.normalize(
            '{"stream":"btcusdt@trade","data":{"e":"trade","E":1800000000000,"T":1800000000001,"s":"BTCUSDT","t":77,"p":"60250.50","q":"0.004","m":true}}',
            "workspace-a", 4, spec.metadata_version,
        )[0]

        self.assertEqual(event.kind, "trade")
        self.assertEqual(event.event_id, "trade:77")
        self.assertEqual(event.market_ts_ms, 1_800_000_000_001)
        self.assertEqual(event.payload["aggressor"], "sell")
        self.assertEqual(event.payload["price"], "60250.5")
        self.assertEqual((event.received_at_ms, event.received_monotonic_ns), (1_800_000_000_123, 987_654_321))
        self.assertIsNone(event.sequence_first)

    def test_quote_without_exchange_timestamp_keeps_market_time_unknown(self):
        adapter = PublicSpotAdapter(_SpotTransport(), clock=_FixedClock())
        spec = adapter.discover()
        event = adapter.normalize(
            '{"stream":"btcusdt@bookTicker","data":{"u":91,"s":"BTCUSDT","b":"60250.50","B":"1.25","a":"60250.51","A":"0.75"}}',
            "workspace-a", 4, spec.metadata_version,
        )[0]

        self.assertEqual(event.kind, "quote")
        self.assertIsNone(event.market_ts_ms)
        self.assertEqual(event.payload["bid"], "60250.5")
        self.assertEqual(event.payload["ask_quantity"], "0.75")

    def test_normalization_rejects_wrong_symbol_duplicate_keys_and_nonfinite_values(self):
        adapter = PublicSpotAdapter(_SpotTransport(), clock=_FixedClock())
        spec = adapter.discover()
        messages = (
            '{"e":"trade","s":"ETHUSDT","t":1,"p":"1","q":"1","m":false}',
            '{"e":"trade","s":"BTCUSDT","s":"ETHUSDT","t":1,"p":"1","q":"1","m":false}',
            '{"e":"trade","s":"BTCUSDT","t":1,"p":"1e999","q":"1","m":false}',
            '{"e":"trade","s":"BTCUSDT","t":1,"p":"1","q":"1","m":false,"extra":1e400}',
            '{"e":"trade","s":"BTCUSDT","t":1,"p":"1","q":"1","m":false,"extra":NaN}',
        )
        for message in messages:
            with self.subTest(message=message), self.assertRaises(AdapterError):
                adapter.normalize(message, "workspace-a", 4, spec.metadata_version)

    def test_queue_overflow_surfaces_error_and_resets_epoch_with_diagnostic(self):
        message = '{"e":"trade","E":1800000000000,"s":"BTCUSDT","t":%d,"p":"10","q":"0.5","m":false}'

        class BurstTransport(_SpotTransport):
            def __init__(self):
                super().__init__()
                self.burst_done = threading.Event()

            def consume(self, stop_event, *, on_message, on_open):
                on_open()
                for trade_id in range(2100):
                    on_message(message % trade_id)
                self.burst_done.set()
                stop_event.wait(2)

        transport = BurstTransport()
        adapter = PublicSpotAdapter(transport, clock=_FixedClock())
        spec = adapter.discover()
        self.assertTrue(adapter.start(
            workspace_id="workspace-a", epoch=4, metadata_version=spec.metadata_version
        ))
        self.assertTrue(transport.burst_done.wait(2))

        drained = adapter.drain(limit=500)
        self.assertEqual(adapter.status, "error")
        self.assertEqual(adapter.metrics["overflow"], 1)
        overflow = next(item for item in drained if isinstance(item, dict) and item.get("code") == "queue_overflow")
        self.assertGreater(overflow["dropped_events"], 0)
        self.assertEqual(overflow["epoch"], 5)
        self.assertTrue(any(
            isinstance(item, dict) and item.get("kind") == "metadata" and item.get("epoch") == 5
            for item in drained
        ))
        adapter.stop()

    def test_worker_emits_live_status_and_drains_market_envelopes(self):
        message = '{"e":"trade","E":1800000000000,"s":"BTCUSDT","t":2,"p":"10","q":"0.5","m":false}'
        transport = _SpotTransport(messages=(message,))
        adapter = PublicSpotAdapter(transport, clock=_FixedClock())
        spec = adapter.discover()
        adapter.start(workspace_id="workspace-a", epoch=4, metadata_version=spec.metadata_version)

        drained = []
        for _ in range(100):
            drained.extend(adapter.drain())
            if any(getattr(item, "kind", None) == "trade" for item in drained):
                break
            threading.Event().wait(0.01)
        adapter.stop()
        drained.extend(adapter.drain())

        self.assertTrue(any(isinstance(item, dict) and item.get("status") == "live" for item in drained))
        self.assertTrue(any(getattr(item, "kind", None) == "trade" for item in drained))
        self.assertEqual(adapter.capabilities().source_id, "binance_public_spot")
        metadata_index = next(i for i, item in enumerate(drained) if isinstance(item, dict) and item.get("kind") == "metadata")
        trade_index = next(i for i, item in enumerate(drained) if getattr(item, "kind", None) == "trade")
        self.assertLess(metadata_index, trade_index)

    def test_resync_reconnects_with_new_epoch_and_metadata_before_market_events(self):
        message = '{"e":"trade","E":1800000000000,"s":"BTCUSDT","t":3,"p":"11","q":"0.25","m":true}'

        class ResyncTransport(_SpotTransport):
            def __init__(self):
                super().__init__()
                self.first_consume = threading.Event()
                self.second_consume = threading.Event()
                self.calls = 0

            def consume(self, stop_event, *, on_message, on_open):
                self.calls += 1
                on_open()
                if self.calls == 1:
                    self.first_consume.set()
                    stop_event.wait(2)
                    return
                self.second_consume.set()
                on_message(message)
                stop_event.wait(2)

        transport = ResyncTransport()
        adapter = PublicSpotAdapter(transport, clock=_FixedClock())
        spec = adapter.discover()
        self.assertTrue(adapter.start(
            workspace_id="workspace-a", epoch=4, metadata_version=spec.metadata_version
        ))
        self.assertTrue(transport.first_consume.wait(1))
        self.assertTrue(adapter.request_resync())

        drained = []
        for _ in range(200):
            drained.extend(adapter.drain())
            if any(getattr(item, "kind", None) == "trade" for item in drained):
                break
            threading.Event().wait(0.005)
        adapter.stop()
        drained.extend(adapter.drain())

        metadata = [(i, item) for i, item in enumerate(drained) if isinstance(item, dict) and item.get("kind") == "metadata"]
        trades = [(i, item) for i, item in enumerate(drained) if getattr(item, "kind", None) == "trade"]
        self.assertTrue(transport.second_consume.is_set())
        self.assertGreaterEqual(len(metadata), 2)
        self.assertEqual(metadata[0][1]["epoch"], 4)
        self.assertEqual(metadata[-1][1]["epoch"], 5)
        self.assertEqual(trades[-1][1].epoch, 5)
        self.assertLess(metadata[-1][0], trades[-1][0])

    def test_start_during_slow_stop_returns_safely_without_racing_transport_close(self):
        class SlowCloseTransport(_SpotTransport):
            def __init__(self):
                super().__init__()
                self.consuming = threading.Event()
                self.consume_returned = threading.Event()
                self.close_started = threading.Event()
                self.allow_close = threading.Event()

            def consume(self, stop_event, *, on_message, on_open):
                on_open()
                self.consuming.set()
                stop_event.wait(2)
                self.consume_returned.set()

            def close(self):
                self.close_started.set()
                self.allow_close.wait(2)
                self.closed.set()

        transport = SlowCloseTransport()
        adapter = PublicSpotAdapter(transport, clock=_FixedClock())
        spec = adapter.discover()
        self.assertTrue(adapter.start(
            workspace_id="workspace-a", epoch=4, metadata_version=spec.metadata_version
        ))
        self.assertTrue(transport.consuming.wait(1))
        adapter.stop()
        self.assertTrue(transport.close_started.wait(1))
        self.assertTrue(transport.consume_returned.wait(1))

        premature_restart = False
        try:
            for _ in range(100):
                if adapter.start(
                    workspace_id="workspace-a", epoch=5, metadata_version=spec.metadata_version
                ):
                    premature_restart = True
                    break
                threading.Event().wait(0.005)
            self.assertFalse(premature_restart)
        finally:
            transport.allow_close.set()
        self.assertTrue(transport.closed.wait(1))

        restarted = False
        for _ in range(100):
            if adapter.start(
                workspace_id="workspace-a", epoch=5, metadata_version=spec.metadata_version
            ):
                restarted = True
                break
            threading.Event().wait(0.005)
        self.assertTrue(restarted)
        adapter.stop()


if __name__ == "__main__":
    unittest.main()

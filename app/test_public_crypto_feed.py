import time
import unittest
from collections import deque
from threading import Event

from market_data_contract import DataContractError, canonical_payload_sha256
from public_crypto_feed import (
    BinanceSpotAdapter,
    HttpResponse,
    LocalOrderBook,
    PublicCryptoFeed,
    _Ingress,
)


def rest_exchange_info():
    return {
        "symbols": [{
            "symbol": "BTCUSDT",
            "status": "TRADING",
            "baseAsset": "BTC",
            "quoteAsset": "USDT",
            "filters": [
                {"filterType": "PRICE_FILTER", "tickSize": "0.010000"},
                {"filterType": "LOT_SIZE", "stepSize": "0.00001000"},
            ],
        }]
    }


def snapshot(update_id=10, bids=None, asks=None):
    return {
        "lastUpdateId": update_id,
        "bids": bids or [["100.00", "2.00"]],
        "asks": asks or [["101.00", "3.00"]],
    }


def delta(first=10, last=11, bids=None, asks=None):
    return {
        "e": "depthUpdate", "E": 1700000000001, "s": "BTCUSDT",
        "U": first, "u": last,
        "b": bids or [["100.00", "2.50"]],
        "a": asks or [["101.00", "3.00"]],
    }


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = BinanceSpotAdapter(session_epoch="epoch-1")

    def test_catalog_reads_official_filter_values_without_fixed_tick(self):
        item = self.adapter.instrument_from_exchange_info(rest_exchange_info(), as_of_ms=1700000000000)
        self.assertEqual(item.instrument_id, "binance_spot:BTCUSDT")
        self.assertEqual(item.tick_size, "0.010000")
        self.assertEqual(item.quantity_step, "0.00001000")
        self.assertEqual(item.metadata["coverage"], "partial")

    def test_catalog_rejects_missing_or_invalid_filters(self):
        payload = rest_exchange_info()
        payload["symbols"][0]["filters"] = []
        with self.assertRaises(DataContractError):
            self.adapter.instrument_from_exchange_info(payload, as_of_ms=1)

    def test_trade_uses_lexical_values_and_derives_only_buyer_maker(self):
        event = self.adapter.parse_trade(
            {"stream": "btcusdt@trade", "data": {
                "e": "trade", "E": 1700000000001, "s": "BTCUSDT", "t": 1234,
                "p": "67500.12000000", "q": "0.00125000", "T": 1700000000000,
                "m": True,
            }},
            receive_time_ms=1700000000002,
            receive_monotonic_ns=9000,
        )
        self.assertEqual(event.price, "67500.12000000")
        self.assertEqual(event.quantity, "0.00125000")
        self.assertEqual(event.aggressor, "sell")
        self.assertEqual(event.aggressor_origin, "derived:buyer_is_maker")
        self.assertEqual(event.envelope.origin, "synthetic")

    def test_absent_maker_flag_stays_unknown(self):
        event = self.adapter.parse_trade(
            {"e": "trade", "s": "BTCUSDT", "t": 1234, "p": "1", "q": "1", "T": 1},
            receive_time_ms=2,
            receive_monotonic_ns=3,
        )
        self.assertEqual(event.aggressor, "unknown")
        self.assertEqual(event.aggressor_origin, "unknown")

    def test_wrapped_trade_hash_covers_the_payload_as_received(self):
        received = {"stream": "btcusdt@trade", "data": {
            "e": "trade", "s": "BTCUSDT", "t": 5, "p": "10.00", "q": "0.5", "T": 1,
        }}
        event = self.adapter.parse_trade(received, receive_time_ms=2, receive_monotonic_ns=3)
        self.assertEqual(event.envelope.payload_sha256, canonical_payload_sha256(received))


class LocalOrderBookTests(unittest.TestCase):
    def setUp(self):
        self.adapter = BinanceSpotAdapter(session_epoch="epoch-1")
        self.book = LocalOrderBook("binance_spot:BTCUSDT")

    def make_delta(self, payload):
        return self.adapter.parse_delta(payload, receive_time_ms=2, receive_monotonic_ns=3)

    def make_snapshot(self, payload):
        return self.adapter.parse_snapshot(payload, receive_time_ms=2, receive_monotonic_ns=3)

    def test_cold_to_live_uses_frozen_u_le_s_le_u_bridge_and_overlap(self):
        bridge = self.make_delta(delta(10, 12, bids=[["100.00", "2.50"]]))
        overlap = self.make_delta(delta(12, 14, bids=[["100.00", "3.00"]]))
        self.assertTrue(self.book.buffer_delta(bridge))
        self.assertTrue(self.book.buffer_delta(overlap))
        self.assertTrue(self.book.install_snapshot(self.make_snapshot(snapshot(10))))
        view = self.book.view()
        self.assertTrue(view.valid)
        self.assertEqual(view.state, "live")
        self.assertEqual(view.last_update_id, 14)
        self.assertEqual(view.bids[0], ("100.00", "3.00"))
        self.assertEqual(view.checksum_status, "not_provided")
        self.assertEqual(view.coverage, "partial")

    def test_stale_delta_is_ignored_and_zero_removes_a_price(self):
        self.book.buffer_delta(self.make_delta(delta(10, 11)))
        self.book.install_snapshot(self.make_snapshot(snapshot(10)))
        self.assertTrue(self.book.apply_delta(self.make_delta(delta(8, 10))))
        self.assertTrue(self.book.apply_delta(self.make_delta(delta(12, 12, bids=[["100.00", "0"]]))))
        self.assertTrue(self.book.view().valid)
        self.assertEqual(self.book.view().bids, ())

    def test_snapshot_behind_buffer_and_gap_never_return_valid_book(self):
        first = self.make_delta(delta(12, 13))
        self.book.buffer_delta(first)
        self.assertFalse(self.book.install_snapshot(self.make_snapshot(snapshot(10))))
        self.assertFalse(self.book.view().valid)
        self.assertEqual(self.book.view().reason, "snapshot_behind_buffer")

        self.book = LocalOrderBook("binance_spot:BTCUSDT")
        self.book.buffer_delta(self.make_delta(delta(10, 11)))
        self.book.install_snapshot(self.make_snapshot(snapshot(10)))
        self.assertFalse(self.book.apply_delta(self.make_delta(delta(13, 14))))
        self.assertFalse(self.book.view().valid)
        self.assertEqual(self.book.view().reason, "sequence_gap")

    def test_crossed_update_invalidates_entire_book(self):
        self.book.buffer_delta(self.make_delta(delta(10, 11)))
        self.book.install_snapshot(self.make_snapshot(snapshot(10)))
        self.assertFalse(self.book.apply_delta(
            self.make_delta(delta(12, 12, asks=[["99.00", "1"]]))
        ))
        self.assertFalse(self.book.view().valid)
        self.assertEqual(self.book.view().reason, "crossed_book")

    def test_book_orders_levels_and_can_resync_after_gap(self):
        unsorted = snapshot(10, bids=[["99.00", "1"], ["100.00", "2"]],
                            asks=[["102.00", "1"], ["101.00", "2"]])
        self.book.buffer_delta(self.make_delta(delta(10, 11)))
        self.assertTrue(self.book.install_snapshot(self.make_snapshot(unsorted)))
        self.assertEqual([price for price, _ in self.book.view().bids], ["100.00", "99.00"])
        self.assertEqual([price for price, _ in self.book.view().asks], ["101.00", "102.00"])
        self.assertFalse(self.book.apply_delta(self.make_delta(delta(13, 14))))
        self.assertTrue(self.book.buffer_delta(self.make_delta(delta(20, 21))))
        self.assertTrue(self.book.install_snapshot(self.make_snapshot(snapshot(20))))
        self.assertTrue(self.book.view().valid)

    def test_sync_buffer_overflow_never_exposes_a_valid_book(self):
        result = True
        for sequence in range(2049):
            result = self.book.buffer_delta(self.make_delta(delta(sequence, sequence)))
        self.assertFalse(result)
        self.assertFalse(self.book.view().valid)
        self.assertEqual(self.book.view().reason, "sync_buffer_limit_exceeded")


class FakeWebSocket:
    def __init__(self, messages, *, disconnect_on_empty=False):
        self.messages = deque(messages)
        self.closed = Event()
        self.pongs = []
        self.disconnect_on_empty = disconnect_on_empty

    def recv(self, timeout_s):
        if self.messages:
            return self.messages.popleft()
        if self.disconnect_on_empty:
            raise RuntimeError("remote closed connection")
        self.closed.wait(min(timeout_s, 0.01))
        return None

    def pong(self, payload):
        self.pongs.append(payload)

    def close(self):
        self.closed.set()


class FakeRest:
    def __init__(self, responses):
        self.responses = deque(responses)
        self.calls = []

    def __call__(self, path, params, timeout_s):
        self.calls.append((path, dict(params), timeout_s))
        response = self.responses.popleft()
        if isinstance(response, BaseException):
            raise response
        return response


class PublicFeedTests(unittest.TestCase):
    def test_start_is_nonblocking_connects_before_snapshot_and_stop_owns_transport(self):
        ws = FakeWebSocket([
            {"_control": "ping", "payload": "heartbeat"},
            {"stream": "btcusdt@depth@100ms", "data": delta()},
            {"stream": "btcusdt@trade", "data": {
                "e": "trade", "E": 1700000000001, "s": "BTCUSDT", "t": 99,
                "p": "100.50", "q": "0.25", "T": 1700000000000, "m": False,
            }},
        ])
        rest = FakeRest([
            HttpResponse(200, rest_exchange_info(), {}),
            HttpResponse(200, snapshot(), {"X-MBX-USED-WEIGHT-1M": "70"}),
        ])
        urls = []
        feed = PublicCryptoFeed(
            rest_get=rest,
            ws_factory=lambda url: (urls.append(url) or ws),
            clock_utc_ms=lambda: 1700000000002,
            clock_mono_ns=time.monotonic_ns,
            limits={"poll_timeout_s": 0.01, "backoff_seconds": [0], "max_attempts": 1},
        )
        before = time.monotonic()
        feed.start()
        self.assertLess(time.monotonic() - before, 0.5)
        deadline = time.monotonic() + 2.0
        batch = feed.poll(max_events=1)
        while not batch.trades and time.monotonic() < deadline:
            time.sleep(0.01)
            batch = feed.poll(max_events=1)
        state = feed.status()
        feed.stop()
        self.assertEqual(len(batch.trades), 1)
        self.assertEqual(batch.trades[0].aggressor, "buy")
        self.assertEqual(ws.pongs, ["heartbeat"])
        self.assertEqual(len(rest.calls), 2)
        self.assertIn("btcusdt@depth@100ms", urls[0])
        self.assertEqual(rest.calls[1][0], "/api/v3/depth")
        self.assertEqual(state["retention_enabled"], False)
        self.assertEqual(feed.status()["state"], "stopped")

    def test_permanent_http_status_stops_without_retry_or_fallback(self):
        for http_status in (403, 418, 451):
            with self.subTest(http_status=http_status):
                rest = FakeRest([HttpResponse(200, rest_exchange_info(), {}),
                                 HttpResponse(http_status, {"code": -1}, {})])
                ws = FakeWebSocket([{"stream": "btcusdt@depth@100ms", "data": delta()}])
                feed = PublicCryptoFeed(
                    rest_get=rest,
                    ws_factory=lambda url: ws,
                    clock_utc_ms=lambda: 10,
                    clock_mono_ns=time.monotonic_ns,
                    limits={"poll_timeout_s": 0.01},
                )
                feed.start()
                deadline = time.monotonic() + 2.0
                while feed.status()["state"] not in ("stopped", "error") and time.monotonic() < deadline:
                    time.sleep(0.01)
                status = feed.status()
                feed.stop()
                expected = f"permanent_http_{http_status}"
                self.assertEqual(status["reason"], expected)
                self.assertEqual(status["health"][0]["reason"], expected)
                self.assertEqual(len(rest.calls), 2)
                self.assertTrue(all("api.binance.com" not in url for url in status["endpoints"]))

    def test_http_429_obeys_retry_after_before_snapshot_retry(self):
        ws = FakeWebSocket([{"stream": "btcusdt@depth@100ms", "data": delta()}])
        rest = FakeRest([HttpResponse(200, rest_exchange_info(), {}),
                         HttpResponse(429, {"code": -1003}, {"Retry-After": "0"}),
                         HttpResponse(200, snapshot(), {})])
        feed = PublicCryptoFeed(rest_get=rest, ws_factory=lambda _: ws,
                                clock_utc_ms=lambda: 1700000000002,
                                clock_mono_ns=time.monotonic_ns,
                                limits={"poll_timeout_s": 0.01, "backoff_seconds": [0], "max_attempts": 1})
        feed.start()
        deadline = time.monotonic() + 2.0
        while len(rest.calls) < 3 and time.monotonic() < deadline:
            time.sleep(0.01)
        feed.stop()
        self.assertEqual(len(rest.calls), 3)
        self.assertEqual(rest.calls[1][0], "/api/v3/depth")
        self.assertEqual(rest.calls[2][0], "/api/v3/depth")

    def test_server_shutdown_is_visible_after_attempt_budget(self):
        ws = FakeWebSocket([{"stream": "btcusdt@depth@100ms", "data": delta()},
                            {"stream": "btcusdt@trade", "data": {"e": "serverShutdown"}}])
        rest = FakeRest([HttpResponse(200, rest_exchange_info(), {})])
        feed = PublicCryptoFeed(rest_get=rest, ws_factory=lambda _: ws,
                                clock_utc_ms=lambda: 1, clock_mono_ns=time.monotonic_ns,
                                limits={"poll_timeout_s": 0.01, "backoff_seconds": [0], "max_attempts": 1})
        feed.start()
        deadline = time.monotonic() + 2.0
        while feed.status()["state"] not in ("error", "stopped") and time.monotonic() < deadline:
            time.sleep(0.01)
        status = feed.status()
        feed.stop()
        self.assertEqual(status["reason"], "server_shutdown")

    def test_disconnect_and_sync_timeout_have_distinct_health_reasons(self):
        cases = (
            (FakeWebSocket([], disconnect_on_empty=True), {"sync_timeout_s": 0.5}, "websocket_transport_error"),
            (FakeWebSocket([]), {"sync_timeout_s": 0.03}, "sync_timeout"),
        )
        for ws, extra_limits, expected_reason in cases:
            with self.subTest(expected_reason=expected_reason):
                rest = FakeRest([HttpResponse(200, rest_exchange_info(), {})])
                limits = {"poll_timeout_s": 0.01, "max_attempts": 1, "backoff_seconds": [0]}
                limits.update(extra_limits)
                feed = PublicCryptoFeed(rest_get=rest, ws_factory=lambda _: ws,
                                        clock_utc_ms=lambda: 1, clock_mono_ns=time.monotonic_ns,
                                        limits=limits)
                feed.start()
                deadline = time.monotonic() + 2.0
                while feed.status()["state"] not in ("error", "stopped") and time.monotonic() < deadline:
                    time.sleep(0.005)
                status = feed.status()
                feed.stop()
                self.assertEqual(status["reason"], expected_reason)
                self.assertTrue(status["attempts_exhausted"])

    def test_disconnect_after_live_invalidates_the_book(self):
        fail = Event()

        class ControlledDisconnect(FakeWebSocket):
            def recv(self, timeout_s):
                if self.messages:
                    return self.messages.popleft()
                if fail.wait(timeout_s):
                    raise RuntimeError("remote closed connection")
                return None

        ws = ControlledDisconnect([{"stream": "btcusdt@depth@100ms", "data": delta()}])
        rest = FakeRest([HttpResponse(200, rest_exchange_info(), {}),
                         HttpResponse(200, snapshot(), {})])
        feed = PublicCryptoFeed(rest_get=rest, ws_factory=lambda _: ws,
                                clock_utc_ms=lambda: 1, clock_mono_ns=time.monotonic_ns,
                                limits={"poll_timeout_s": 0.01, "max_attempts": 1})
        feed.start()
        deadline = time.monotonic() + 2.0
        while feed.status()["state"] != "live" and time.monotonic() < deadline:
            time.sleep(0.005)
        self.assertEqual(feed.status()["state"], "live")
        self.assertTrue(feed.poll().book.valid)

        fail.set()
        deadline = time.monotonic() + 2.0
        while feed.status()["state"] not in ("error", "stopped") and time.monotonic() < deadline:
            time.sleep(0.005)
        status = feed.status()
        feed.stop()
        self.assertEqual(status["reason"], "websocket_transport_error")
        self.assertFalse(status["health"][1]["valid"])
        self.assertFalse(status["health"][1]["sequence_ok"])

    def test_injected_limits_cannot_exceed_frozen_caps(self):
        feed = PublicCryptoFeed(limits={
            "rest_timeout_s": 100.0, "poll_timeout_s": 10.0, "sync_timeout_s": 100.0,
            "backoff_seconds": [100.0] * 10, "max_attempts": 100,
            "max_snapshots_per_attempt": 100, "max_snapshots_per_minute": 100,
            "max_rest_weight_per_minute": 10000,
        })
        self.assertEqual(feed._limits["rest_timeout_s"], 10.0)
        self.assertEqual(feed._limits["poll_timeout_s"], 1.0)
        self.assertEqual(feed._limits["sync_timeout_s"], 10.0)
        self.assertEqual(feed._limits["backoff_seconds"], [30.0] * 6)
        self.assertEqual(feed._limits["max_attempts"], 12)
        self.assertEqual(feed._limits["max_snapshots_per_attempt"], 3)
        self.assertEqual(feed._limits["max_snapshots_per_minute"], 6)
        self.assertEqual(feed._limits["max_rest_weight_per_minute"], 500)

    def test_reader_message_and_ingress_caps_count_dropped_bytes(self):
        feed = PublicCryptoFeed(limits={"max_message_bytes": 80, "max_queue_events": 1})
        feed._attempt = 1
        oversized = FakeWebSocket([{"x": "z" * 200}])
        feed._reader_loop(oversized, 1)
        status = feed.status()
        self.assertEqual(status["reason"], "message_too_large")
        self.assertEqual(status["dropped_events"], 1)
        self.assertGreater(status["dropped_bytes"], 0)

        feed = PublicCryptoFeed(limits={"max_queue_events": 1})
        feed._attempt = 1
        ws = FakeWebSocket([delta(), delta(12, 13)])
        feed._reader_loop(ws, 1)
        status = feed.status()
        self.assertEqual(status["reason"], "event_queue_overflow")
        self.assertEqual(status["ingress_events"], 1)
        self.assertEqual(status["dropped_events"], 1)
        self.assertGreater(status["dropped_bytes"], 0)

    def test_trade_queue_and_managed_memory_caps_invalidate_depth(self):
        payload = {"stream": "btcusdt@trade", "data": {
            "e": "trade", "E": 1, "s": "BTCUSDT", "t": 1,
            "p": "10.00", "q": "0.5", "T": 1, "m": False,
        }}
        bounded = PublicCryptoFeed(limits={"max_queue_events": 1})
        self.assertEqual(bounded._process_one(_Ingress(payload, 1)), "")
        next_payload = {"stream": "btcusdt@trade", "data": {**payload["data"], "t": 2}}
        self.assertEqual(bounded._process_one(_Ingress(next_payload, 1)), "event_queue_overflow")
        self.assertFalse(bounded._book.view().valid)

        tiny_memory = PublicCryptoFeed(limits={"max_managed_bytes": 1})
        self.assertEqual(tiny_memory._process_one(_Ingress(payload, 1)), "memory_budget_exceeded")
        self.assertFalse(tiny_memory._book.view().valid)

    def test_health_receive_utc_is_arrival_time_not_read_time(self):
        utc = {"now": 1000}
        ws = FakeWebSocket([
            {"stream": "btcusdt@depth@100ms", "data": delta()},
            {"stream": "btcusdt@trade", "data": {
                "e": "trade", "E": 1700000000001, "s": "BTCUSDT", "t": 99,
                "p": "100.50", "q": "0.25", "T": 1700000000000, "m": False,
            }},
        ])
        rest = FakeRest([HttpResponse(200, rest_exchange_info(), {}),
                         HttpResponse(200, snapshot(), {})])
        feed = PublicCryptoFeed(rest_get=rest, ws_factory=lambda _: ws,
                                clock_utc_ms=lambda: utc["now"], clock_mono_ns=time.monotonic_ns,
                                limits={"poll_timeout_s": 0.01, "backoff_seconds": [0], "max_attempts": 1})
        feed.start()
        deadline = time.monotonic() + 2.0
        while feed.status()["health"][0]["last_receive_time_ms"] is None and time.monotonic() < deadline:
            time.sleep(0.01)
        utc["now"] = 987654
        trade_health = feed.status()["health"][0]
        depth_health = feed.status()["health"][1]
        feed.stop()
        self.assertEqual(trade_health["last_receive_time_ms"], 1000)
        self.assertEqual(depth_health["last_receive_time_ms"], 1000)

    def test_health_records_received_stale_depth_delta_without_validating_book(self):
        utc = {"now": 100}
        feed = PublicCryptoFeed(clock_utc_ms=lambda: utc["now"], clock_mono_ns=time.monotonic_ns)
        adapter = BinanceSpotAdapter()
        initial = adapter.parse_delta(delta(10, 11), receive_time_ms=100,
                                      receive_monotonic_ns=time.monotonic_ns(), origin="live")
        self.assertTrue(feed._book.buffer_delta(initial))
        snapshot_event = adapter.parse_snapshot(snapshot(10), receive_time_ms=101,
                                                receive_monotonic_ns=time.monotonic_ns(), origin="live")
        self.assertTrue(feed._book.install_snapshot(snapshot_event))

        utc["now"] = 200
        stale_payload = {"stream": "btcusdt@depth@100ms", "data": delta(8, 10)}
        self.assertEqual(feed._process_one(_Ingress(stale_payload, 1)), "")
        depth = next(item for item in feed._health_locked() if item.channel == "depth")
        self.assertEqual(depth.last_receive_time_ms, 200)
        self.assertEqual(depth.last_exchange_time_ms, 1700000000001)
        self.assertTrue(feed._book.view().valid)
        self.assertEqual(feed._book.view().last_update_id, 11)

    def test_stop_keeps_reference_to_blocked_rest_call_and_refuses_restart(self):
        entered = Event()
        release = Event()
        calls = []

        def blocked_rest(path, params, timeout_s):
            calls.append(path)
            entered.set()
            release.wait(3.0)
            return HttpResponse(200, rest_exchange_info(), {})

        feed = PublicCryptoFeed(rest_get=blocked_rest, ws_factory=lambda _: FakeWebSocket([]),
                                clock_utc_ms=lambda: 1, clock_mono_ns=time.monotonic_ns,
                                limits={"max_attempts": 1})
        feed.start()
        self.assertTrue(entered.wait(1.0))
        before = time.monotonic()
        feed.stop()
        elapsed = time.monotonic() - before
        status = feed.status()
        self.assertLess(elapsed, 2.0)
        self.assertFalse(status["owner_worker_alive"])
        self.assertTrue(status["rest_request_alive"])
        self.assertTrue(status["worker_alive"])
        self.assertEqual(status["state"], "stopping")
        self.assertEqual(status["reason"], "stop_timeout_rest_alive")
        feed.start()
        self.assertEqual(calls, ["/api/v3/exchangeInfo"])
        self.assertTrue(feed.status()["rest_request_alive"])
        release.set()

    def test_stop_tracks_blocked_transport_close_and_refuses_restart(self):
        entered = Event()
        release = Event()

        class BlockingCloseWebSocket(FakeWebSocket):
            def close(self):
                entered.set()
                release.wait(3.0)
                super().close()

        ws = BlockingCloseWebSocket([{"stream": "btcusdt@depth@100ms", "data": delta()}])
        rest = FakeRest([HttpResponse(200, rest_exchange_info(), {}), HttpResponse(200, snapshot(), {})])
        feed = PublicCryptoFeed(rest_get=rest, ws_factory=lambda _: ws,
                                clock_utc_ms=lambda: 1, clock_mono_ns=time.monotonic_ns,
                                limits={"poll_timeout_s": 0.01, "backoff_seconds": [0], "max_attempts": 1})
        feed.start()
        deadline = time.monotonic() + 2.0
        while feed.status()["state"] != "live" and time.monotonic() < deadline:
            time.sleep(0.005)
        self.assertEqual(feed.status()["state"], "live")

        before = time.monotonic()
        feed.stop()
        elapsed = time.monotonic() - before
        self.assertTrue(entered.is_set())
        self.assertLess(elapsed, 2.0)
        status = feed.status()
        self.assertTrue(status["close_worker_alive"])
        self.assertTrue(status["worker_alive"])
        self.assertEqual(status["state"], "stopping")
        self.assertEqual(status["reason"], "stop_timeout_close_alive")
        feed.start()
        self.assertEqual(len(rest.calls), 2)
        release.set()
        deadline = time.monotonic() + 1.0
        while feed.status()["worker_alive"] and time.monotonic() < deadline:
            time.sleep(0.01)

    def test_stop_reports_worker_that_is_still_blocked(self):
        entered = Event()
        release = Event()

        def blocked_rest(path, params, timeout_s):
            entered.set()
            release.wait(3.0)
            return HttpResponse(200, rest_exchange_info(), {})

        feed = PublicCryptoFeed(rest_get=blocked_rest, ws_factory=lambda _: FakeWebSocket([]),
                                clock_utc_ms=lambda: 1, clock_mono_ns=time.monotonic_ns,
                                limits={"max_attempts": 1})
        feed.start()
        self.assertTrue(entered.wait(1.0))
        before = time.monotonic()
        feed.stop()
        elapsed = time.monotonic() - before
        status = feed.status()
        release.set()
        deadline = time.monotonic() + 1.0
        while feed.status()["worker_alive"] and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertLess(elapsed, 2.0)
        self.assertTrue(status["worker_alive"])
        self.assertEqual(status["state"], "stopping")


if __name__ == "__main__":
    unittest.main()

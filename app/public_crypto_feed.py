"""Public, read-only Binance Spot adapter and bounded feed observer.

Importing this module is inert. Live transport is loaded only after start().
"""
from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass
from decimal import Decimal
import json
import math
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from market_data_contract import (
    SCHEMA_VERSION, BookDelta, BookSnapshot, BookView, DataContractError,
    FeedBatch, InstrumentSpec, MarketEnvelope, SourceDescriptor, SourceHealth,
    TradeEvent, canonical_payload_sha256, decimal_value,
)

REST_BASE = "https://data-api.binance.vision"
WS_URL = "wss://data-stream.binance.vision/stream?streams=btcusdt@trade/btcusdt@depth@100ms"
TERMS_URL = "https://www.binance.com/en/terms"
INSTRUMENT_ID = "binance_spot:BTCUSDT"
MAX_MESSAGE_BYTES = 1_048_576
MAX_QUEUE_EVENTS = 4096
MAX_QUEUE_BYTES = 8 * 1_048_576
MAX_MANAGED_BYTES = 32 * 1_048_576


@dataclass(frozen=True)
class HttpResponse:
    status: int
    data: object
    headers: dict[str, str]


class BinanceSpotAdapter:
    """Strict parser for the public BTCUSDT spot streams."""

    def __init__(self, *, session_epoch: str = "offline") -> None:
        if not isinstance(session_epoch, str) or not session_epoch:
            raise DataContractError("session_epoch is missing")
        self.session_epoch = session_epoch

    @staticmethod
    def _body(payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise DataContractError("market payload must be an object")
        body = payload.get("data", payload)
        if not isinstance(body, dict):
            raise DataContractError("market payload data must be an object")
        return body

    def instrument_from_exchange_info(self, payload: dict, *, as_of_ms: int) -> InstrumentSpec:
        if not isinstance(payload, dict) or not isinstance(payload.get("symbols"), list):
            raise DataContractError("exchange catalog is invalid")
        matches = [s for s in payload["symbols"] if isinstance(s, dict) and s.get("symbol") == "BTCUSDT"]
        if len(matches) != 1:
            raise DataContractError("BTCUSDT catalog entry is missing or ambiguous")
        item = matches[0]
        if (item.get("status") != "TRADING" or item.get("baseAsset") != "BTC"
                or item.get("quoteAsset") != "USDT"):
            raise DataContractError("BTCUSDT catalog assets or status are invalid")
        filters = item.get("filters")
        if not isinstance(filters, list):
            raise DataContractError("exchange filters are invalid")
        price = [f.get("tickSize") for f in filters if isinstance(f, dict) and f.get("filterType") == "PRICE_FILTER"]
        qty = [f.get("stepSize") for f in filters if isinstance(f, dict) and f.get("filterType") == "LOT_SIZE"]
        if len(price) != 1 or len(qty) != 1:
            raise DataContractError("required exchange filters are missing or ambiguous")
        decimal_value(price[0]); decimal_value(qty[0])
        return InstrumentSpec(
            instrument_id=INSTRUMENT_ID, kind="spot", symbol="BTCUSDT", base_asset="BTC",
            quote_asset="USDT", settlement_currency="USDT", tick_size=price[0],
            quantity_step=qty[0], payoff_type="spot", catalog_version="binance-spot-json-v1",
            as_of_ms=as_of_ms,
            metadata={"coverage": "partial", "full_tape": False, "catalog_source": "exchangeInfo",
                      "minimum_order_filters_used": False},
        )

    def _envelope(self, body: dict, *, event_kind: str, exchange_time_ms: int | None,
                  receive_time_ms: int, receive_monotonic_ns: int, origin: str,
                  first: int | None = None, last: int | None = None,
                  received_payload: dict | None = None) -> MarketEnvelope:
        if origin not in ("live", "synthetic", "replay"):
            raise DataContractError("origin must be live, synthetic, or replay")
        return MarketEnvelope(
            schema_version=SCHEMA_VERSION, provider="binance", venue="binance_spot",
            instrument_id=INSTRUMENT_ID, event_kind=event_kind,
            exchange_time_ms=exchange_time_ms, receive_time_ms=receive_time_ms,
            receive_monotonic_ns=receive_monotonic_ns, origin=origin,
            session_epoch=self.session_epoch,
            payload_sha256=canonical_payload_sha256(body if received_payload is None else received_payload),
            sequence_namespace="binance_spot:BTCUSDT:depth" if first is not None else None,
            first_sequence=first, last_sequence=last,
        )

    @staticmethod
    def _int(value: object, field: str) -> int:
        if isinstance(value, bool):
            raise DataContractError(f"{field} must be a non-negative integer")
        if isinstance(value, int) and value >= 0:
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        raise DataContractError(f"{field} must be a non-negative integer")

    def parse_trade(self, payload: dict, *, receive_time_ms: int,
                    receive_monotonic_ns: int, origin: str = "synthetic") -> TradeEvent:
        body = self._body(payload)
        if body.get("e") != "trade" or body.get("s") != "BTCUSDT":
            raise DataContractError("trade event type or symbol is invalid")
        trade_id = self._int(body.get("t"), "trade_id")
        price, quantity = body.get("p"), body.get("q")
        decimal_value(price); decimal_value(quantity)
        trade_time = self._int(body.get("T"), "trade_time_ms")
        if "m" not in body:
            aggressor, aggressor_origin = "unknown", "unknown"
        elif isinstance(body["m"], bool):
            aggressor = "sell" if body["m"] else "buy"
            aggressor_origin = "derived:buyer_is_maker"
        else:
            raise DataContractError("buyer-is-maker flag has invalid type")
        exchange_time = self._int(body["E"], "exchange_time_ms") if "E" in body else None
        envelope = self._envelope(body, event_kind="trade", exchange_time_ms=exchange_time,
                                  receive_time_ms=receive_time_ms, receive_monotonic_ns=receive_monotonic_ns,
                                  origin=origin, received_payload=payload)
        return TradeEvent(INSTRUMENT_ID, str(trade_id), price, quantity, trade_time,
                          aggressor, aggressor_origin, envelope)

    def _levels(self, raw: object, *, allow_zero: bool = False, maximum: int = 1000) -> tuple[tuple[str, str], ...]:
        if not isinstance(raw, list) or len(raw) > maximum:
            raise DataContractError("book levels exceed limit or are invalid")
        levels = []
        for level in raw:
            if not isinstance(level, (list, tuple)) or len(level) != 2:
                raise DataContractError("book level is invalid")
            price, quantity = level
            decimal_value(price); decimal_value(quantity, allow_zero=allow_zero)
            levels.append((price, quantity))
        return tuple(levels)

    def parse_snapshot(self, payload: dict, *, receive_time_ms: int,
                       receive_monotonic_ns: int, origin: str = "synthetic") -> BookSnapshot:
        body = self._body(payload)
        update_id = self._int(body.get("lastUpdateId"), "lastUpdateId")
        bids, asks = self._levels(body.get("bids")), self._levels(body.get("asks"))
        envelope = self._envelope(body, event_kind="book_snapshot", exchange_time_ms=None,
                                  receive_time_ms=receive_time_ms, receive_monotonic_ns=receive_monotonic_ns,
                                  origin=origin, received_payload=payload)
        return BookSnapshot(INSTRUMENT_ID, update_id, bids, asks, envelope)

    def parse_delta(self, payload: dict, *, receive_time_ms: int,
                    receive_monotonic_ns: int, origin: str = "synthetic") -> BookDelta:
        body = self._body(payload)
        if body.get("e") != "depthUpdate" or body.get("s") != "BTCUSDT":
            raise DataContractError("depth event type or symbol is invalid")
        first, last = self._int(body.get("U"), "first_update_id"), self._int(body.get("u"), "last_update_id")
        if first > last:
            raise DataContractError("book delta sequence is reversed")
        exchange_time = self._int(body["E"], "exchange_time_ms") if "E" in body else None
        bids, asks = self._levels(body.get("b"), allow_zero=True), self._levels(body.get("a"), allow_zero=True)
        envelope = self._envelope(body, event_kind="book_delta", exchange_time_ms=exchange_time,
                                  receive_time_ms=receive_time_ms, receive_monotonic_ns=receive_monotonic_ns,
                                  origin=origin, first=first, last=last, received_payload=payload)
        return BookDelta(INSTRUMENT_ID, first, last, bids, asks, envelope)

class LocalOrderBook:
    """Bounded absolute-quantity depth state with conservative sequence bridging."""

    def __init__(self, instrument_id: str, *, max_levels: int = 5000) -> None:
        if not isinstance(max_levels, int) or isinstance(max_levels, bool) or max_levels < 1:
            raise DataContractError("max_levels must be a positive integer")
        self.instrument_id = instrument_id
        self.max_levels = max_levels
        self._bids: dict[Decimal, str] = {}
        self._asks: dict[Decimal, str] = {}
        self._buffer: deque[BookDelta] = deque()
        self._buffer_bytes = 0
        self._state = "cold"
        self._reason = "awaiting_snapshot"
        self._last: int | None = None
        self._dropped_events = 0
        self._dropped_bytes = 0
        self._gaps = 0
        self._resyncs = 0
        self._last_exchange_ms = None
        self._last_receive_ms = None
        self._last_mono_ns = None

    @staticmethod
    def _delta_size(delta: BookDelta) -> int:
        return len(json.dumps(delta.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8"))

    def _note(self, envelope: MarketEnvelope) -> None:
        self._last_exchange_ms = envelope.exchange_time_ms
        self._last_receive_ms = envelope.receive_time_ms
        self._last_mono_ns = envelope.receive_monotonic_ns

    @staticmethod
    def _crossed(bids: dict[Decimal, str], asks: dict[Decimal, str]) -> bool:
        return bool(bids and asks and max(bids) >= min(asks))

    def _valid_levels(self, bids: dict[Decimal, str], asks: dict[Decimal, str]) -> bool:
        return len(bids) <= self.max_levels and len(asks) <= self.max_levels and not self._crossed(bids, asks)

    def _apply_to(self, bids: dict[Decimal, str], asks: dict[Decimal, str], delta: BookDelta) -> tuple[dict, dict]:
        if delta.instrument_id != self.instrument_id:
            raise DataContractError("book delta instrument differs")
        new_bids, new_asks = dict(bids), dict(asks)
        for side, levels in ((new_bids, delta.bids), (new_asks, delta.asks)):
            for price_text, qty_text in levels:
                price = decimal_value(price_text)
                qty = decimal_value(qty_text, allow_zero=True)
                if qty == 0:
                    side.pop(price, None)
                else:
                    side[price] = qty_text
                if len(side) > self.max_levels:
                    raise DataContractError("book_level_limit_exceeded")
        if self._crossed(new_bids, new_asks):
            raise DataContractError("crossed_book")
        return new_bids, new_asks

    def buffer_delta(self, delta: BookDelta) -> bool:
        if not isinstance(delta, BookDelta) or delta.instrument_id != self.instrument_id:
            self.invalidate("invalid_delta")
            return False
        if self._state == "live":
            return self.apply_delta(delta)
        if self._state == "invalid":
            self._state = "syncing"
            self._reason = "awaiting_snapshot"
            self._resyncs += 1
        else:
            self._state = "syncing"
        size = self._delta_size(delta)
        if len(self._buffer) >= 2048 or self._buffer_bytes + size > 4 * 1_048_576:
            self._dropped_events += 1
            self._dropped_bytes += size
            self.invalidate("sync_buffer_limit_exceeded")
            return False
        self._buffer.append(delta)
        self._buffer_bytes += size
        self._note(delta.envelope)
        return True

    def install_snapshot(self, snapshot: BookSnapshot) -> bool:
        if not isinstance(snapshot, BookSnapshot) or snapshot.instrument_id != self.instrument_id:
            self.invalidate("invalid_snapshot")
            return False
        if len(snapshot.bids) > 1000 or len(snapshot.asks) > 1000:
            self.invalidate("snapshot_depth_limit_exceeded")
            return False
        bids, asks = {}, {}
        try:
            for price, qty in snapshot.bids:
                p = decimal_value(price); q = decimal_value(qty)
                bids[p] = qty
            for price, qty in snapshot.asks:
                p = decimal_value(price); q = decimal_value(qty)
                asks[p] = qty
            if not self._valid_levels(bids, asks):
                raise DataContractError("crossed_book")
        except DataContractError as exc:
            self.invalidate(str(exc) if str(exc) in ("crossed_book", "book_level_limit_exceeded") else "invalid_snapshot")
            return False
        bridge_index = None
        for i, delta in enumerate(self._buffer):
            if delta.last_update_id <= snapshot.last_update_id:
                continue
            if delta.first_update_id <= snapshot.last_update_id <= delta.last_update_id:
                bridge_index = i
                break
            if delta.first_update_id > snapshot.last_update_id:
                break
        if bridge_index is None:
            self._state = "syncing"
            self._reason = "snapshot_behind_buffer"
            return False
        pending = list(self._buffer)[bridge_index:]
        last = snapshot.last_update_id
        try:
            for delta in pending:
                if delta.last_update_id <= last:
                    continue
                if delta.first_update_id > last + 1:
                    raise DataContractError("sequence_gap")
                next_bids, next_asks = self._apply_to(bids, asks, delta)
                bids, asks, last = next_bids, next_asks, delta.last_update_id
        except DataContractError as exc:
            self.invalidate(str(exc) if str(exc) in ("sequence_gap", "crossed_book", "book_level_limit_exceeded") else "invalid_delta")
            return False
        self._bids, self._asks, self._last = bids, asks, last
        self._buffer.clear(); self._buffer_bytes = 0
        self._state, self._reason = "live", ""
        self._note(snapshot.envelope)
        if pending:
            self._note(pending[-1].envelope)
        return True

    def apply_delta(self, delta: BookDelta) -> bool:
        if self._state != "live" or self._last is None:
            return self.buffer_delta(delta)
        if not isinstance(delta, BookDelta) or delta.instrument_id != self.instrument_id:
            self.invalidate("invalid_delta")
            return False
        if delta.last_update_id <= self._last:
            return True
        if delta.first_update_id > self._last + 1:
            self._gaps += 1
            self.invalidate("sequence_gap")
            return False
        try:
            bids, asks = self._apply_to(self._bids, self._asks, delta)
        except DataContractError as exc:
            reason = str(exc) if str(exc) in ("crossed_book", "book_level_limit_exceeded") else "invalid_delta"
            self.invalidate(reason)
            return False
        self._bids, self._asks = bids, asks
        self._last = delta.last_update_id
        self._reason = ""
        self._note(delta.envelope)
        return True

    def invalidate(self, reason: str) -> None:
        safe_reasons = {"invalid_delta", "invalid_snapshot", "sequence_gap", "crossed_book",
                        "book_level_limit_exceeded", "book_level_limit_exceeded",
                        "snapshot_depth_limit_exceeded", "sync_buffer_limit_exceeded",
                        "snapshot_behind_buffer", "depth_stale", "disconnected",
                        "memory_budget_exceeded", "sync_timeout", "permanent_http_403",
                        "permanent_http_418", "permanent_http_451", "transport_error",
                        "message_invalid", "event_queue_overflow", "resync_budget_exhausted"}
        self._state = "invalid"
        self._reason = reason if reason in safe_reasons else "invalid_delta"
        self._bids.clear(); self._asks.clear(); self._last = None
        self._buffer.clear(); self._buffer_bytes = 0

    def view(self, *, limit: int = 20) -> BookView:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            raise DataContractError("view limit must be non-negative")
        bids = tuple((str(p), self._bids[p]) for p in sorted(self._bids, reverse=True)[:limit])
        asks = tuple((str(p), self._asks[p]) for p in sorted(self._asks)[:limit])
        return BookView(self.instrument_id, self._state, self._state == "live", self._last,
                        bids, asks, 1000, "partial", "not_provided", self._reason)

# Only these public, documented paths can be called by the live transport.
_ALLOWED_REST_PATHS = {
    "/api/v3/exchangeInfo": 20,
    "/api/v3/depth": 50,
    "/api/v3/trades": 25,
}


def _public_rest_get(path: str, params: dict, timeout_s: float) -> HttpResponse:
    if path not in _ALLOWED_REST_PATHS:
        raise DataContractError("REST path is not allowed")
    url = REST_BASE + path + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "JevTrader-public-observer/1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            raw = response.read(MAX_MESSAGE_BYTES + 1)
            if len(raw) > MAX_MESSAGE_BYTES:
                raise DataContractError("HTTP response exceeds message limit")
            data = json.loads(raw.decode("utf-8"))
            return HttpResponse(response.status, data, dict(response.headers.items()))
    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read(MAX_MESSAGE_BYTES + 1)
            data = json.loads(raw.decode("utf-8")) if len(raw) <= MAX_MESSAGE_BYTES else {"error": "response_too_large"}
        except Exception:
            data = {"error": "invalid_response"}
        return HttpResponse(exc.code, data, dict(exc.headers.items()) if exc.headers else {})
    except DataContractError:
        raise
    except Exception as exc:
        raise RuntimeError("public_rest_transport_error") from exc


class _WebsocketClientTransport:
    """Small lazy wrapper; websocket-client is imported only on explicit start."""
    def __init__(self, url: str) -> None:
        try:
            import websocket
        except ImportError as exc:
            raise RuntimeError("live websocket requires optional websocket-client==1.9.2") from exc
        self._websocket = websocket
        self._ws = websocket.create_connection(url, timeout=1.0, enable_multithread=True,
                                              http_proxy_host=None, http_proxy_port=None)
        self._ws.settimeout(1.0)

    def recv(self, timeout_s: float):
        self._ws.settimeout(max(0.01, timeout_s))
        try:
            opcode, data = self._ws.recv_data(control_frame=True)
        except self._websocket.WebSocketTimeoutException:
            return None
        if opcode == self._websocket.ABNF.OPCODE_PING:
            return {"_control": "ping", "payload": data}
        if opcode == self._websocket.ABNF.OPCODE_PONG:
            return {"_control": "pong", "payload": data}
        if opcode == self._websocket.ABNF.OPCODE_CLOSE:
            raise RuntimeError("websocket_closed")
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return data

    def pong(self, payload) -> None:
        self._ws.pong(payload)

    def close(self) -> None:
        # The websocket-client default waits up to three seconds for the peer's
        # close frame, beyond this feed's two-second shutdown budget.
        self._ws.close(timeout=0)


@dataclass
class _Ingress:
    payload: dict
    size: int
    receive_time_ms: int | None = None
    receive_monotonic_ns: int | None = None


class PublicCryptoFeed:
    """Explicitly started, bounded, read-only public market data observer."""

    def __init__(self, *, rest_get=None, ws_factory=None, clock_utc_ms=None,
                 clock_mono_ns=None, jitter=None, limits=None) -> None:
        self._rest_get = rest_get or _public_rest_get
        self._ws_factory = ws_factory or _WebsocketClientTransport
        self._utc = clock_utc_ms or (lambda: int(time.time() * 1000))
        self._mono = clock_mono_ns or time.monotonic_ns
        self._jitter = jitter or (lambda: random.random() * 0.2)
        self._limits = {
            "rest_timeout_s": 10.0, "poll_timeout_s": 1.0, "sync_timeout_s": 10.0,
            "backoff_seconds": [1, 2, 4, 8, 16, 30], "max_attempts": 12,
            "max_snapshots_per_attempt": 3, "max_snapshots_per_minute": 6,
            "max_rest_weight_per_minute": 500,
            "max_message_bytes": MAX_MESSAGE_BYTES, "max_queue_events": MAX_QUEUE_EVENTS,
            "max_queue_bytes": MAX_QUEUE_BYTES, "max_managed_bytes": MAX_MANAGED_BYTES,
            "max_book_levels": 5000,
        }
        if limits:
            self._limits.update(dict(limits))
        timeout_caps = {"rest_timeout_s": 10.0, "poll_timeout_s": 1.0, "sync_timeout_s": 10.0}
        for name, hard_cap in timeout_caps.items():
            value = self._limits[name]
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or value <= 0):
                raise DataContractError(f"{name} must be a finite positive number")
            self._limits[name] = min(float(value), hard_cap)
        integer_caps = {
            "max_attempts": 12, "max_snapshots_per_attempt": 3,
            "max_snapshots_per_minute": 6, "max_rest_weight_per_minute": 500,
        }
        for name, hard_cap in integer_caps.items():
            value = self._limits[name]
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise DataContractError(f"{name} must be a positive integer")
            self._limits[name] = min(value, hard_cap)
        backoffs = self._limits["backoff_seconds"]
        if not isinstance(backoffs, (list, tuple)) or not backoffs:
            raise DataContractError("backoff_seconds must contain at least one delay")
        normalized_backoffs = []
        for value in backoffs[:6]:
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or value < 0):
                raise DataContractError("backoff_seconds must contain finite non-negative delays")
            normalized_backoffs.append(min(float(value), 30.0))
        self._limits["backoff_seconds"] = normalized_backoffs
        hard_caps = {
            "max_message_bytes": MAX_MESSAGE_BYTES, "max_queue_events": MAX_QUEUE_EVENTS,
            "max_queue_bytes": MAX_QUEUE_BYTES, "max_managed_bytes": MAX_MANAGED_BYTES,
            "max_book_levels": 5000,
        }
        for name, hard_cap in hard_caps.items():
            value = self._limits[name]
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise DataContractError(f"{name} must be a positive integer")
            self._limits[name] = min(value, hard_cap)
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._ingress_event = threading.Event()
        self._ingress: deque[_Ingress] = deque()
        self._ingress_bytes = 0
        self._trades: deque[tuple[TradeEvent, int]] = deque()
        self._trade_ids: OrderedDict[str, None] = OrderedDict()
        self._trade_bytes = 0
        self._adapter = BinanceSpotAdapter(session_epoch="offline")
        self._book = LocalOrderBook(INSTRUMENT_ID, max_levels=self._limits["max_book_levels"])
        self._instrument = self._pending_instrument()
        self._source = self._source_descriptor()
        self._worker: threading.Thread | None = None
        self._reader: threading.Thread | None = None
        self._rest_thread: threading.Thread | None = None
        self._close_thread: threading.Thread | None = None
        self._transport = None
        self._state = "idle"
        self._reason = "not_started"
        self._connected = False
        self._trade_last_mono = None
        self._depth_last_mono = None
        self._trade_last_receive_ms = None
        self._depth_last_receive_ms = None
        self._trade_last_exchange = None
        self._depth_last_exchange = None
        self._gaps = self._resyncs = 0
        self._dropped_events = self._dropped_bytes = 0
        self._rest_weight = 0
        self._rest_requests: deque[tuple[int, int]] = deque()
        self._used_weight_headers: dict[str, str] = {}
        self._snapshot_calls: deque[int] = deque()
        self._managed_bytes = 0
        self._peak_managed_bytes = 0
        self._attempt = 0
        self._closing_attempt: int | None = None
        self._last_backoff = 0.0
        self._worker_alive = False
        self._catalog_ready = False
        self._reader_error = ""
        self._attempts_exhausted = False

    def _pending_instrument(self) -> InstrumentSpec:
        return InstrumentSpec(INSTRUMENT_ID, "spot", "BTCUSDT", "BTC", "USDT", "USDT",
                             None, None, payoff_type="spot", catalog_version="binance-spot-json-v1",
                             as_of_ms=None, metadata={"coverage": "partial", "full_tape": False,
                                                      "catalog_status": "waiting"})

    def _source_descriptor(self) -> SourceDescriptor:
        now = self._utc()
        return SourceDescriptor(
            source_id="binance_spot_public_btcusdt_v1", provider="binance", venue="binance_spot",
            market="spot", endpoint_version="binance-spot-json-v1",
            endpoints=(REST_BASE, WS_URL), auth_required=False, terms_url=TERMS_URL,
            retention_permission="unknown", redistribution_permission="unknown", jurisdiction=None,
            cadence_ms=100, as_of_ms=now, evidence_refs=("docs/specs/Implementacao_Multimercado_2026-10-09.md",),
        )

    def start(self) -> None:
        with self._lock:
            self._refresh_lifecycle_locked()
            if any(thread and thread.is_alive() for thread in
                   (self._worker, self._reader, self._rest_thread, self._close_thread)):
                return
            if self._state not in ("idle", "stopped"):
                return
            self._worker = self._reader = self._rest_thread = None
            self._stop_event.clear()
            self._state, self._reason = "starting", ""
            self._attempts_exhausted = False
            self._worker = threading.Thread(target=self._run, name="public-crypto-feed", daemon=True)
            self._worker.start()

    def _refresh_lifecycle_locked(self) -> None:
        alive = any(thread and thread.is_alive() for thread in
                    (self._worker, self._reader, self._rest_thread, self._close_thread))
        if self._state == "stopping" and self._stop_event.is_set() and not alive:
            self._state = "stopped"
            if self._reason == "stop_requested":
                self._reason = "stopped"

    def _is_stopping(self) -> bool:
        return self._stop_event.is_set()

    def _reader_loop(self, transport, ingress_epoch: int) -> None:
        while not self._stop_event.is_set():
            try:
                message = transport.recv(float(self._limits["poll_timeout_s"]))
            except Exception:
                with self._lock:
                    if ingress_epoch == self._attempt and self._closing_attempt != ingress_epoch:
                        self._reader_error = "websocket_transport_error"
                        self._reason = "websocket_transport_error"
                self._ingress_event.set()
                return
            if message is None:
                continue
            received_utc_ms = self._utc()
            received_monotonic_ns = self._mono()
            raw_size = 0
            try:
                if isinstance(message, str):
                    raw = message.encode("utf-8")
                    raw_size = len(raw)
                    if raw_size > self._limits["max_message_bytes"]:
                        raise DataContractError("message_too_large")
                    message = json.loads(message)
                elif isinstance(message, dict):
                    raw = json.dumps(message, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
                    raw_size = len(raw)
                    if raw_size > self._limits["max_message_bytes"]:
                        raise DataContractError("message_too_large")
                else:
                    raise DataContractError("message_invalid")
                if not isinstance(message, dict):
                    raise DataContractError("message_invalid")
                if message.get("_control") == "ping":
                    if not callable(getattr(transport, "pong", None)):
                        raise DataContractError("websocket_ping_unsupported")
                    transport.pong(message.get("payload", b""))
                    continue
                if message.get("_control") == "pong":
                    continue
                with self._lock:
                    if ingress_epoch != self._attempt:
                        return
                    if (len(self._ingress) >= self._limits["max_queue_events"]
                            or self._ingress_bytes + len(raw) > self._limits["max_queue_bytes"]):
                        self._dropped_events += 1
                        self._dropped_bytes += len(raw)
                        self._reason = "event_queue_overflow"
                        self._reader_error = "event_queue_overflow"
                        self._ingress_event.set()
                        return
                    self._ingress.append(_Ingress(
                        message, len(raw), received_utc_ms, received_monotonic_ns
                    ))
                    self._ingress_bytes += len(raw)
                    self._managed_update_locked()
                self._ingress_event.set()
            except Exception as exc:
                reason = str(exc) if isinstance(exc, DataContractError) and str(exc) in (
                    "message_too_large", "message_invalid"
                ) else "message_invalid"
                with self._lock:
                    self._dropped_events += 1
                    self._dropped_bytes += raw_size
                    self._reason = reason
                    self._reader_error = reason
                self._ingress_event.set()
                return

    def _managed_update_locked(self) -> None:
        trade_size = sum(size for _, size in self._trades)
        ingress_size = self._ingress_bytes
        book_size = sum(len(str(p).encode("utf-8")) + len(q.encode("utf-8")) + 16
                        for side in (self._book._bids, self._book._asks) for p, q in side.items())
        self._managed_bytes = trade_size + ingress_size + book_size
        self._peak_managed_bytes = max(self._peak_managed_bytes, self._managed_bytes)

    def _dequeue_ingress(self) -> _Ingress | None:
        with self._lock:
            if not self._ingress:
                self._ingress_event.clear()
                return None
            item = self._ingress.popleft()
            self._ingress_bytes = max(0, self._ingress_bytes - item.size)
            self._managed_update_locked()
            return item

    def _process_one(self, item: _Ingress) -> str:
        message = item.payload
        receive_time_ms = (item.receive_time_ms if item.receive_time_ms is not None
                           else self._utc())
        receive_monotonic_ns = (item.receive_monotonic_ns if item.receive_monotonic_ns is not None
                                else self._mono())
        body = message.get("data", message)
        if not isinstance(body, dict):
            return "message_invalid"
        if body.get("e") == "serverShutdown":
            return "server_shutdown"
        try:
            if body.get("e") == "trade":
                event = self._adapter.parse_trade(message, receive_time_ms=receive_time_ms,
                                                  receive_monotonic_ns=receive_monotonic_ns, origin="live")
                size = len(json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8"))
                with self._lock:
                    if event.trade_id in self._trade_ids:
                        self._trade_ids.move_to_end(event.trade_id)
                        return ""
                    self._trade_last_mono = event.envelope.receive_monotonic_ns
                    self._trade_last_receive_ms = event.envelope.receive_time_ms
                    self._trade_last_exchange = event.envelope.exchange_time_ms
                    self._trade_ids[event.trade_id] = None
                    if len(self._trade_ids) > 20000:
                        self._trade_ids.popitem(last=False)
                    if (len(self._trades) >= self._limits["max_queue_events"]
                            or self._trade_bytes + size > self._limits["max_queue_bytes"]):
                        self._dropped_events += 1
                        self._dropped_bytes += size
                        self._book.invalidate("event_queue_overflow")
                        return "event_queue_overflow"
                    self._trades.append((event, size))
                    self._trade_bytes += size
                    self._managed_update_locked()
                    if self._managed_bytes > self._limits["max_managed_bytes"]:
                        self._book.invalidate("memory_budget_exceeded")
                        return "memory_budget_exceeded"
                return ""
            if body.get("e") == "depthUpdate":
                delta = self._adapter.parse_delta(message, receive_time_ms=receive_time_ms,
                                                  receive_monotonic_ns=receive_monotonic_ns, origin="live")
                with self._lock:
                    self._depth_last_mono = delta.envelope.receive_monotonic_ns
                    self._depth_last_receive_ms = delta.envelope.receive_time_ms
                    self._depth_last_exchange = delta.envelope.exchange_time_ms
                    before = self._book.view()
                    ok = self._book.buffer_delta(delta) if before.state != "live" else self._book.apply_delta(delta)
                    if not ok:
                        if self._book.view().reason == "sequence_gap":
                            self._gaps += 1
                        return self._book.view().reason or "invalid_delta"
                    self._managed_update_locked()
                    if self._managed_bytes > self._limits["max_managed_bytes"]:
                        self._book.invalidate("memory_budget_exceeded")
                        return "memory_budget_exceeded"
                return ""
            return "message_invalid"
        except DataContractError:
            return "message_invalid"

    def _process_available(self) -> str:
        while not self._stop_event.is_set():
            item = self._dequeue_ingress()
            if item is None:
                return ""
            reason = self._process_one(item)
            if reason:
                with self._lock:
                    self._reason = reason
                return reason
        return ""

    def _rate_wait(self, weight: int) -> bool:
        now = self._mono()
        with self._lock:
            cutoff = now - 60_000_000_000
            while self._rest_requests and self._rest_requests[0][0] <= cutoff:
                self._rest_requests.popleft()
            current = sum(item_weight for _, item_weight in self._rest_requests)
            limit = int(self._limits["max_rest_weight_per_minute"])
            self._rest_weight = current
            if weight > limit or current + weight > limit:
                return False
            self._rest_requests.append((now, weight))
            self._rest_weight = current + weight
            return True

    def _snapshot_budget_wait(self) -> bool:
        now = self._mono()
        with self._lock:
            while self._snapshot_calls and now - self._snapshot_calls[0] >= 60_000_000_000:
                self._snapshot_calls.popleft()
            if len(self._snapshot_calls) < int(self._limits["max_snapshots_per_minute"]):
                self._snapshot_calls.append(now)
                return True
        return False

    def _request(self, path: str, params: dict, weight: int) -> HttpResponse:
        if path not in _ALLOWED_REST_PATHS:
            raise RuntimeError("rest_path_not_allowed")
        retries = 0
        while not self._stop_event.is_set():
            if not self._rate_wait(weight):
                raise RuntimeError("local_rest_weight_budget_exhausted")
            completed = threading.Event()
            result: dict[str, object] = {}

            def invoke() -> None:
                try:
                    result["response"] = self._rest_get(path, dict(params), float(self._limits["rest_timeout_s"]))
                except BaseException as exc:
                    result["error"] = exc
                finally:
                    completed.set()

            with self._lock:
                previous = self._rest_thread
                if previous and previous.is_alive():
                    raise RuntimeError("rest_request_already_active")
                request_thread = threading.Thread(target=invoke, name="public-feed-rest", daemon=True)
                self._rest_thread = request_thread
                request_thread.start()
            while not completed.wait(0.05):
                if self._stop_event.is_set():
                    raise RuntimeError("stopped")
            request_thread.join(0.1)
            with self._lock:
                if self._rest_thread is request_thread and not request_thread.is_alive():
                    self._rest_thread = None
            if "error" in result:
                raise RuntimeError("public_rest_transport_error") from result["error"]
            response = result.get("response")
            if not isinstance(response, HttpResponse):
                raise RuntimeError("invalid_http_response")
            if response.status in (403, 418, 451):
                reason = f"permanent_http_{response.status}"
                with self._lock:
                    self._reason, self._state = reason, "error"
                self._stop_event.set()
                raise RuntimeError(reason)
            try:
                response_size = len(json.dumps(response.data, sort_keys=True, separators=(",", ":"),
                                               allow_nan=False).encode("utf-8"))
            except (TypeError, ValueError) as exc:
                raise RuntimeError("invalid_http_response") from exc
            if response_size > self._limits["max_message_bytes"]:
                raise RuntimeError("message_too_large")
            with self._lock:
                self._used_weight_headers.update({k: v for k, v in response.headers.items()
                                                  if k.lower().startswith("x-mbx-used-weight")})
            if response.status == 429:
                if retries >= 2:
                    raise RuntimeError("http_429_retry_exhausted")
                retries += 1
                headers = {k.lower(): v for k, v in response.headers.items()}
                delay = 1.0
                try:
                    delay = max(0.0, float(headers.get("retry-after", "1")))
                except (ValueError, TypeError):
                    try:
                        from email.utils import parsedate_to_datetime
                        delay = max(0.0, (parsedate_to_datetime(headers["retry-after"]).timestamp() - time.time()))
                    except Exception:
                        delay = 1.0
                if self._stop_event.wait(delay):
                    raise RuntimeError("stopped")
                continue
            if not 200 <= response.status < 300:
                raise RuntimeError(f"http_status_{response.status}")
            return response
        raise RuntimeError("stopped")

    def _await_depth_delta(self, deadline_ns: int) -> bool:
        while not self._stop_event.is_set() and self._mono() < deadline_ns:
            with self._lock:
                reader_error = self._reader_error
            if reader_error:
                raise RuntimeError(reader_error)
            reason = self._process_available()
            if reason:
                raise RuntimeError(reason)
            if self._book._buffer:
                return True
            remaining = max(0.0, min(0.1, (deadline_ns - self._mono()) / 1_000_000_000))
            self._ingress_event.wait(remaining)
        return False

    def _sync_depth(self) -> bool:
        deadline = self._mono() + int(float(self._limits["sync_timeout_s"]) * 1_000_000_000)
        if not self._await_depth_delta(deadline):
            raise RuntimeError("sync_timeout")
        max_snapshots = min(3, int(self._limits["max_snapshots_per_attempt"]))
        for _ in range(max_snapshots):
            if self._stop_event.is_set():
                return False
            if not self._snapshot_budget_wait():
                raise RuntimeError("snapshot_rate_budget_exhausted")
            response = self._request("/api/v3/depth", {"symbol": "BTCUSDT", "limit": 1000}, 50)
            snapshot = self._adapter.parse_snapshot(response.data, receive_time_ms=self._utc(),
                                                    receive_monotonic_ns=self._mono(), origin="live")
            with self._lock:
                # Include deltas accumulated while REST was in flight in the
                # bridge check. Keep the drain and install atomic with respect
                # to reader ingress; later messages apply to the live book.
                ingress_error = self._process_available()
                if ingress_error:
                    raise RuntimeError(ingress_error)
                if self._stop_event.is_set():
                    return False
                ok = self._book.install_snapshot(snapshot)
                if ok:
                    self._depth_last_mono = snapshot.envelope.receive_monotonic_ns
                    self._depth_last_receive_ms = snapshot.envelope.receive_time_ms
                    self._depth_last_exchange = snapshot.envelope.exchange_time_ms
                    return True
                reason = self._book.view().reason
                if reason not in ("snapshot_behind_buffer", "awaiting_snapshot"):
                    raise RuntimeError(reason or "snapshot_invalid")
            # Continue draining deltas between bounded snapshots.
            self._process_available()
            if self._stop_event.is_set():
                return False
        raise RuntimeError("snapshot_bridge_budget_exhausted")


    def _set_permanent_reason(self, reason: str) -> None:
        with self._lock:
            self._reason = reason
            self._state = "error"
            self._book.invalidate(reason)
        self._stop_event.set()

    @staticmethod
    def _safe_failure(exc: BaseException) -> str:
        message = str(exc)
        allowed = {
            "stopped", "sync_timeout", "snapshot_rate_budget_exhausted",
            "snapshot_bridge_budget_exhausted", "sequence_gap", "crossed_book",
            "invalid_snapshot", "invalid_delta", "book_level_limit_exceeded",
            "snapshot_depth_limit_exceeded", "sync_buffer_limit_exceeded",
            "event_queue_overflow", "memory_budget_exceeded", "server_shutdown",
            "websocket_transport_error", "public_rest_transport_error",
            "invalid_http_response", "local_rest_weight_budget_exhausted",
            "http_429_retry_exhausted", "message_invalid", "message_too_large", "depth_stale",
            "transport_error", "rest_path_not_allowed", "snapshot_invalid",
            "resync_budget_exhausted", "websocket_ping_unsupported", "rest_request_already_active",
            "websocket_close_timeout",
        }
        if message in allowed or message in ("permanent_http_403", "permanent_http_418", "permanent_http_451"):
            return message
        if message.startswith("http_status_") and message[12:].isdigit():
            return message
        if message.startswith("live websocket requires optional "):
            return "live_websocket_dependency_missing"
        return "transport_error"

    def _ensure_transport_close(self, transport, *, name: str) -> threading.Thread | None:
        if transport is None or not callable(getattr(transport, "close", None)):
            return None
        with self._lock:
            if transport is self._transport:
                self._closing_attempt = self._attempt
            current = self._close_thread
            if current and current.is_alive():
                return current

            def close_transport() -> None:
                try:
                    transport.close()
                finally:
                    with self._lock:
                        if self._transport is transport:
                            self._transport = None

            closer = threading.Thread(target=close_transport, name=name, daemon=True)
            self._close_thread = closer
            closer.start()
            return closer

    def _close_current_transport(self) -> None:
        with self._lock:
            transport = self._transport
            self._connected = False
        closer = self._ensure_transport_close(transport, name="public-feed-close")
        if closer is not None:
            closer.join(0.1)
        reader = self._reader
        if reader and reader is not threading.current_thread():
            reader.join(0.15)
        with self._lock:
            if self._transport is transport:
                self._transport = None

    def _run(self) -> None:
        with self._lock:
            self._worker_alive = True
        try:
            try:
                response = self._request("/api/v3/exchangeInfo", {"symbol": "BTCUSDT"}, 20)
                instrument = self._adapter.instrument_from_exchange_info(response.data, as_of_ms=self._utc())
                with self._lock:
                    self._instrument = instrument
                    self._catalog_ready = True
                    self._source = self._source_descriptor()
            except Exception as exc:
                reason = self._safe_failure(exc)
                with self._lock:
                    self._reason = reason
                    if reason not in ("stopped",):
                        self._state = "error"
                if reason not in ("stopped",):
                    self._stop_event.set()
                return

            attempts = int(self._limits["max_attempts"])
            if attempts < 1:
                self._set_permanent_reason("resync_budget_exhausted")
                return
            backoffs = list(self._limits["backoff_seconds"])
            for attempt in range(1, attempts + 1):
                if self._stop_event.is_set():
                    break
                with self._lock:
                    self._attempt = attempt
                    self._state = "connecting"
                    self._connected = False
                    self._reason = ""
                    self._reader_error = ""
                    self._closing_attempt = None
                    self._ingress.clear(); self._ingress_bytes = 0
                    self._ingress_event.clear()
                    if attempt > 1:
                        self._resyncs += 1
                    self._adapter = BinanceSpotAdapter(session_epoch=f"{self._utc()}-{attempt}")
                    self._book = LocalOrderBook(INSTRUMENT_ID, max_levels=self._limits["max_book_levels"])
                    self._managed_update_locked()
                try:
                    transport = self._ws_factory(WS_URL)
                    if not callable(getattr(transport, "recv", None)) or not callable(getattr(transport, "close", None)):
                        raise RuntimeError("websocket_transport_error")
                    with self._lock:
                        self._transport = transport
                        self._connected = True
                        self._state = "syncing"
                    self._reader = threading.Thread(target=self._reader_loop, args=(transport, attempt),
                                                    name="public-feed-reader", daemon=True)
                    self._reader.start()
                    if not self._sync_depth():
                        break
                    with self._lock:
                        if self._state != "error":
                            self._state = "live"
                    while not self._stop_event.is_set():
                        with self._lock:
                            reader_error = self._reader_error
                        if reader_error:
                            raise RuntimeError(reader_error)
                        reason = self._process_available()
                        if reason:
                            raise RuntimeError(reason)
                        with self._lock:
                            book_view = self._book.view()
                            depth_last = self._depth_last_mono
                            self._managed_update_locked()
                            managed = self._managed_bytes
                        if managed > self._limits["max_managed_bytes"]:
                            raise RuntimeError("memory_budget_exceeded")
                        if not book_view.valid:
                            raise RuntimeError(book_view.reason or "invalid_delta")
                        if depth_last is not None and self._mono() - depth_last > 2_000_000_000:
                            with self._lock:
                                self._book.invalidate("depth_stale")
                            raise RuntimeError("depth_stale")
                        self._ingress_event.wait(0.05)
                    if self._stop_event.is_set():
                        break
                except Exception as exc:
                    reason = self._safe_failure(exc)
                    if reason in ("permanent_http_403", "permanent_http_418", "permanent_http_451"):
                        self._set_permanent_reason(reason)
                    elif not self._stop_event.is_set():
                        with self._lock:
                            self._reason = reason
                            self._book.invalidate(reason)
                    if reason == "live_websocket_dependency_missing":
                        self._set_permanent_reason(reason)
                finally:
                    self._close_current_transport()
                if self._stop_event.is_set():
                    break
                with self._lock:
                    close_alive = bool(self._close_thread and self._close_thread.is_alive())
                if close_alive:
                    closer = self._close_thread
                    if closer is not None and not self._stop_event.is_set():
                        closer.join(0.75)
                    with self._lock:
                        close_alive = bool(self._close_thread and self._close_thread.is_alive())
                    if close_alive:
                        self._set_permanent_reason("websocket_close_timeout")
                        break
                if attempt >= attempts:
                    with self._lock:
                        if not self._reason:
                            self._reason = "resync_budget_exhausted"
                        self._attempts_exhausted = True
                        self._state = "error"
                    break
                index = min(attempt - 1, len(backoffs) - 1) if backoffs else 0
                delay = float(backoffs[index]) if backoffs else 0.0
                fraction = self._jitter()
                if isinstance(fraction, bool) or not isinstance(fraction, (float, int)) or not 0 <= fraction <= 0.2:
                    self._set_permanent_reason("transport_error")
                    break
                delay *= 1.0 + float(fraction)
                self._last_backoff = delay
                if self._stop_event.wait(delay):
                    break
        finally:
            self._close_current_transport()
            with self._lock:
                self._worker_alive = False
                request_alive = bool(self._rest_thread and self._rest_thread.is_alive())
                reader_alive = bool(self._reader and self._reader.is_alive())
                close_alive = bool(self._close_thread and self._close_thread.is_alive())
                if self._state != "error":
                    if self._stop_event.is_set() and (request_alive or reader_alive or close_alive):
                        self._state = "stopping"
                        self._reason = ("stop_timeout_rest_alive" if request_alive else
                                        "stop_timeout_reader_alive" if reader_alive else
                                        "stop_timeout_close_alive")
                    elif self._stop_event.is_set():
                        self._state = "stopped"
                        if self._reason in ("", "stop_requested"):
                            self._reason = "stopped"
                    else:
                        self._state = "error"
                        if not self._reason:
                            self._reason = "resync_budget_exhausted"

    def poll(self, *, max_events: int = 1000) -> FeedBatch:
        if isinstance(max_events, bool) or not isinstance(max_events, int) or max_events < 0:
            raise DataContractError("max_events must be a non-negative integer")
        selected = []
        with self._lock:
            for _ in range(min(max_events, len(self._trades))):
                event, size = self._trades.popleft()
                self._trade_bytes = max(0, self._trade_bytes - size)
                selected.append(event)
            self._managed_update_locked()
            book = self._book.view()
            health = self._health_locked()
            source, instrument = self._source, self._instrument
            warnings = (self._reason,) if self._reason else ()
        return FeedBatch(source, instrument, tuple(selected), book, health, warnings)

    def _health_locked(self) -> tuple[SourceHealth, ...]:
        now = self._mono()
        trade_stale = self._trade_last_mono is None or now - self._trade_last_mono > 10_000_000_000
        depth_stale = self._depth_last_mono is None or now - self._depth_last_mono > 2_000_000_000
        book = self._book.view()
        common = dict(connected=self._connected, coverage="partial", gaps=self._gaps,
                      resyncs=self._resyncs, dropped_events=self._dropped_events,
                      dropped_bytes=self._dropped_bytes,
                      metrics={"queue_events": len(self._trades), "queue_bytes": self._trade_bytes,
                               "managed_bytes": self._managed_bytes, "peak_managed_bytes": self._peak_managed_bytes,
                               "rest_weight_window": self._rest_weight})
        trade_reason = self._reason or ("no_trade_update" if trade_stale else "")
        trade = SourceHealth("trade", self._connected, "stale" if trade_stale else self._state,
                             self._connected and not trade_stale, trade_stale, "partial",
                             self._trade_last_exchange, self._trade_last_receive_ms,
                             self._trade_last_mono, self._connected, self._gaps, self._resyncs,
                             self._dropped_events, self._dropped_bytes,
                             trade_reason, common["metrics"])
        depth_reason = self._reason or book.reason or ("no_depth_update" if depth_stale else "")
        depth = SourceHealth("depth", self._connected, book.state,
                             self._connected and book.valid and not depth_stale,
                             depth_stale, "partial", self._depth_last_exchange,
                             self._depth_last_receive_ms,
                             self._depth_last_mono, self._connected and book.valid,
                             self._gaps, self._resyncs,
                             self._dropped_events, self._dropped_bytes, depth_reason,
                             common["metrics"])
        return (trade, depth)

    def status(self) -> dict:
        with self._lock:
            self._refresh_lifecycle_locked()
            owner_worker_alive = bool(self._worker and self._worker.is_alive())
            rest_request_alive = bool(self._rest_thread and self._rest_thread.is_alive())
            reader_alive = bool(self._reader and self._reader.is_alive())
            close_worker_alive = bool(self._close_thread and self._close_thread.is_alive())
            worker_alive = owner_worker_alive or rest_request_alive or reader_alive or close_worker_alive
            return {
                "state": self._state, "reason": self._reason, "connected": self._connected,
                "worker_alive": worker_alive, "reader_alive": reader_alive,
                "owner_worker_alive": owner_worker_alive, "rest_request_alive": rest_request_alive,
                "close_worker_alive": close_worker_alive,
                "attempt": self._attempt, "last_backoff_seconds": self._last_backoff,
                "retention_enabled": False, "full_tape": False,
                "endpoints": [REST_BASE, WS_URL], "instrument_id": INSTRUMENT_ID,
                "catalog_ready": self._catalog_ready, "queue_events": len(self._trades),
                "queue_bytes": self._trade_bytes, "ingress_events": len(self._ingress),
                "ingress_bytes": self._ingress_bytes, "managed_bytes": self._managed_bytes,
                "peak_managed_bytes": self._peak_managed_bytes, "dropped_events": self._dropped_events,
                "dropped_bytes": self._dropped_bytes, "gaps": self._gaps, "resyncs": self._resyncs,
                "attempts_exhausted": self._attempts_exhausted,
                "rest_weight_window": self._rest_weight, "used_weight_headers": dict(self._used_weight_headers),
                "health": [item.to_dict() for item in self._health_locked()],
            }

    def stop(self) -> None:
        with self._lock:
            self._refresh_lifecycle_locked()
            if not self._worker:
                self._stop_event.set()
                if self._state != "error":
                    self._state, self._reason = "stopped", "stopped"
                return
            if self._worker.is_alive() and self._state != "error":
                self._state = "stopping"
                self._reason = "stop_requested"
                self._book.invalidate("stopped")
            self._stop_event.set()
            self._ingress_event.set()
            transport = self._transport
            worker = self._worker
        self._ensure_transport_close(transport, name="public-feed-stop-close")
        worker.join(1.8)
        with self._lock:
            request_alive = bool(self._rest_thread and self._rest_thread.is_alive())
            reader_alive = bool(self._reader and self._reader.is_alive())
            close_alive = bool(self._close_thread and self._close_thread.is_alive())
            if worker.is_alive() or request_alive or reader_alive or close_alive:
                self._state = "stopping"
                if request_alive:
                    self._reason = "stop_timeout_rest_alive"
                elif reader_alive:
                    self._reason = "stop_timeout_reader_alive"
                elif close_alive:
                    self._reason = "stop_timeout_close_alive"
                else:
                    self._reason = "stop_timeout_worker_alive"
            elif self._state not in ("error",):
                self._state = "stopped"
                if self._reason == "stop_requested":
                    self._reason = "stopped"

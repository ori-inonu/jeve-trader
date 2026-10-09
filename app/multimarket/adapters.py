"""Normalization and lifecycle for the public Binance Spot BTCUSDT pilot."""

from __future__ import annotations

import hashlib
import json
import math
import queue
import re
import threading
import time
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

from .contracts import EventEnvelope, InstrumentSpec, SourceCapabilities, SystemClock, decimal_text


SOURCE_ID = "binance_public_spot"
MAX_PENDING_EVENTS = 2_000
MAX_DRAIN = 500
_MAX_RECONNECT_SECONDS = 5.0


class AdapterError(RuntimeError):
    """Sanitized adapter validation or lifecycle failure."""


class _DuplicateKey(ValueError):
    pass


class _StopOrResync:
    """Event view that lets a consumer exit without stopping its owner thread."""

    def __init__(self, stop_event: threading.Event, resync_event: threading.Event):
        self._stop_event = stop_event
        self._resync_event = resync_event

    def is_set(self) -> bool:
        return self._stop_event.is_set() or self._resync_event.is_set()

    def wait(self, timeout: float | None = None) -> bool:
        deadline = None if timeout is None else time.monotonic() + max(0.0, timeout)
        while not self.is_set():
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                interval = min(remaining, 0.05)
            else:
                interval = 0.05
            if self._stop_event.wait(interval):
                return True
            if self._resync_event.is_set():
                return True
        return True


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateKey
        value[key] = item
    return value


def _reject_constant(_value: str) -> None:
    raise ValueError("non-finite JSON number")


def _finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("non-finite JSON number")
    return result


def _check_json(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise AdapterError("Market message contains a non-finite number.")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise AdapterError("Market message keys must be text.")
            _check_json(item)
    elif isinstance(value, list):
        for item in value:
            _check_json(item)
    elif value is None or isinstance(value, (str, bool, int, float)):
        return
    else:
        raise AdapterError("Market message contains an unsupported value.")


def _decimal(value: Any, field: str, *, positive: bool = False, nonnegative: bool = False) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"\d+(?:\.\d+)?", value):
        raise AdapterError(f"Market {field} must be a decimal string.")
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError):
        raise AdapterError(f"Market {field} is invalid.") from None
    if not result.is_finite() or (positive and result <= 0) or (nonnegative and result < 0):
        raise AdapterError(f"Market {field} is outside its valid range.")
    return result


def _timestamp(data: dict[str, Any], fields: tuple[str, ...]) -> int | None:
    for field in fields:
        if field not in data:
            continue
        value = data[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise AdapterError("Market timestamp is invalid.")
        return value
    return None


def _json_text(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, OverflowError, RecursionError):
        raise AdapterError("Binance metadata could not be hashed safely.") from None


class PublicSpotAdapter:
    """Single-symbol adapter with bounded handoff and explicit resync controls."""

    def __init__(self, transport: Any, *, clock: Any = None):
        if transport is None:
            raise ValueError("transport is required")
        self._transport = transport
        self._clock = clock or SystemClock()
        self._queue: queue.Queue[Any] = queue.Queue(maxsize=MAX_PENDING_EVENTS)
        self._lock = threading.RLock()
        self._spec: InstrumentSpec | None = None
        self._metadata_version: str | None = None
        self._workspace_id: str | None = None
        self._epoch: int | None = None
        self._status = "disconnected"
        self._worker: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._resync_event = threading.Event()
        self._transport_closed = threading.Event()
        self._transport_closed.set()
        self._generation = 0
        self._overflow_count = 0
        self._rejected_count = 0

    def discover(self, symbol: str = "BTCUSDT") -> InstrumentSpec:
        """Fetch and validate the one supported symbol's public metadata."""
        if symbol != "BTCUSDT":
            raise AdapterError("Only BTCUSDT public spot metadata is supported.")
        try:
            raw = self._transport.get_metadata(symbol)
        except Exception:
            raise AdapterError("Binance public metadata is unavailable.") from None
        spec = self._spec_from_metadata(raw)
        with self._lock:
            self._spec = spec
            self._metadata_version = spec.metadata_version
        return spec

    @staticmethod
    def _spec_from_metadata(raw: Any) -> InstrumentSpec:
        if not isinstance(raw, dict):
            raise AdapterError("Binance metadata schema is invalid.")
        _check_json(raw)
        symbols = raw.get("symbols")
        if not isinstance(symbols, list):
            raise AdapterError("Binance metadata has no symbol list.")
        matches = [item for item in symbols if isinstance(item, dict) and item.get("symbol") == "BTCUSDT"]
        if len(matches) != 1:
            raise AdapterError("Binance metadata does not identify exactly one BTCUSDT symbol.")
        info = matches[0]
        status = info.get("status")
        base = info.get("baseAsset")
        quote = info.get("quoteAsset")
        if not isinstance(status, str) or not status or not isinstance(base, str) or not base or not isinstance(quote, str) or not quote:
            raise AdapterError("Binance symbol identity metadata is incomplete.")
        filters = info.get("filters")
        if not isinstance(filters, list):
            raise AdapterError("Binance symbol filters are invalid.")
        by_type: dict[str, dict[str, Any]] = {}
        for item in filters:
            if not isinstance(item, dict) or not isinstance(item.get("filterType"), str):
                raise AdapterError("Binance symbol filter is malformed.")
            name = item["filterType"]
            if name in by_type:
                raise AdapterError("Binance symbol contains duplicate filters.")
            by_type[name] = item
        price_filter = by_type.get("PRICE_FILTER", {})
        lot_filter = by_type.get("LOT_SIZE", {})
        notional_filter = by_type.get("MIN_NOTIONAL") or by_type.get("NOTIONAL") or {}

        def maybe_decimal(value: Any, field: str, *, positive: bool = False, nonnegative: bool = False) -> Decimal | None:
            if value is None:
                return None
            return _decimal(value, field, positive=positive, nonnegative=nonnegative)

        price_tick = maybe_decimal(price_filter.get("tickSize"), "tick size", positive=True)
        quantity_step = maybe_decimal(lot_filter.get("stepSize"), "quantity step", positive=True)
        quantity_min = maybe_decimal(lot_filter.get("minQty"), "minimum quantity", nonnegative=True)
        minimum_notional = maybe_decimal(
            notional_filter.get("minNotional", notional_filter.get("notional")),
            "minimum notional",
            nonnegative=True,
        )
        verified = (
            status == "TRADING"
            and price_tick is not None
            and quantity_step is not None
            and quantity_min is not None
            and minimum_notional is not None
        )
        # exchangeInfo also carries volatile response-wide fields such as
        # serverTime. Version only the selected instrument's contract inputs.
        canonical_contract = {
            "symbol": "BTCUSDT",
            "status": status,
            "baseAsset": base,
            "quoteAsset": quote,
            "filters": [by_type[name] for name in sorted(by_type)],
        }
        metadata_version = "sha256:" + hashlib.sha256(
            _json_text(canonical_contract).encode("utf-8")
        ).hexdigest()
        return InstrumentSpec(
            instrument_id="binance:spot:BTCUSDT",
            venue="binance",
            segment="spot",
            symbol="BTCUSDT",
            family="crypto_spot",
            metadata_version=metadata_version,
            price_tick=price_tick,
            quantity_step=quantity_step,
            quantity_min=quantity_min,
            minimum_notional=minimum_notional,
            contract_multiplier=Decimal("1"),
            base_asset=base,
            quote_currency=quote,
            settlement_currency=quote,
            expiry_at_ms=None,
            calendar_id=None,
            status=status,
            constraints_verified=verified,
        )

    def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            source_id=SOURCE_ID,
            version="binance_spot_public_v3",
            quote=True,
            trades=True,
            book=False,
            account=False,
            trade_semantics="individual",
            side_semantics="buyer_is_maker_maps_to_sell_aggressor",
            sequence_scope="unknown",
            book_mode="unavailable",
            full_tape=False,
            retention="unknown",
            export="unknown",
        )

    def normalize(
        self,
        message: str | bytes | dict[str, Any],
        workspace_id: str,
        epoch: int,
        metadata_version: str,
    ) -> list[EventEnvelope]:
        """Validate one Binance message and emit an observed quote or trade."""
        with self._lock:
            spec = self._spec
            current_version = self._metadata_version
        if spec is None or current_version is None:
            raise AdapterError("Instrument metadata must be discovered before normalization.")
        if metadata_version != current_version:
            raise AdapterError("Message metadata version is stale.")
        if not isinstance(workspace_id, str) or not workspace_id:
            raise AdapterError("Workspace identity is invalid.")
        if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch <= 0:
            raise AdapterError("Connection epoch is invalid.")
        try:
            if isinstance(message, bytes):
                message = message.decode("utf-8")
            if isinstance(message, str):
                root = json.loads(
                    message,
                    object_pairs_hook=_unique_object,
                    parse_constant=_reject_constant,
                    parse_float=_finite_float,
                )
            else:
                root = message
            if not isinstance(root, dict):
                raise AdapterError("Market message must be an object.")
            _check_json(root)
            wrapper_stream = root.get("stream")
            data = root.get("data", root)
            if not isinstance(data, dict):
                raise AdapterError("Binance market message data is invalid.")
            if data.get("s") != "BTCUSDT":
                raise AdapterError("Market message is outside the BTCUSDT pilot.")
            event_type = data.get("e")
            if wrapper_stream is not None and wrapper_stream not in {"btcusdt@trade", "btcusdt@bookTicker"}:
                raise AdapterError("Binance stream is outside the BTCUSDT pilot.")
            if event_type is None and wrapper_stream == "btcusdt@bookTicker":
                event_type = "bookTicker"
            if event_type == "trade":
                event = self._trade(data, spec, workspace_id, epoch, metadata_version)
            elif event_type == "bookTicker":
                event = self._quote(data, spec, workspace_id, epoch, metadata_version)
            else:
                raise AdapterError("Binance event type is unsupported.")
            if wrapper_stream is not None:
                expected = "btcusdt@trade" if event_type == "trade" else "btcusdt@bookTicker"
                if wrapper_stream != expected:
                    raise AdapterError("Binance stream name does not match its event.")
            return [event]
        except AdapterError:
            raise
        except (UnicodeError, json.JSONDecodeError, _DuplicateKey, TypeError, ValueError, OverflowError, RecursionError):
            raise AdapterError("Binance market message is malformed or non-finite.") from None

    def _trade(
        self, data: dict[str, Any], spec: InstrumentSpec, workspace_id: str, epoch: int, metadata_version: str
    ) -> EventEnvelope:
        trade_id = data.get("t")
        maker = data.get("m")
        if isinstance(trade_id, bool) or not isinstance(trade_id, int) or trade_id < 0 or not isinstance(maker, bool):
            raise AdapterError("Binance individual trade identity is malformed.")
        price = _decimal(data.get("p"), "trade price", positive=True)
        quantity = _decimal(data.get("q"), "trade quantity", positive=True)
        return EventEnvelope(
            workspace_id=workspace_id,
            instrument_id=spec.instrument_id,
            source_id=SOURCE_ID,
            epoch=epoch,
            metadata_version=metadata_version,
            event_id=f"trade:{trade_id}",
            kind="trade",
            market_ts_ms=_timestamp(data, ("T", "E")),
            received_at_ms=self._clock.wall_ms(),
            received_monotonic_ns=self._clock.monotonic_ns(),
            sequence_first=None,
            sequence_last=None,
            payload={
                "price": decimal_text(price),
                "quantity": decimal_text(quantity),
                "aggressor": "sell" if maker else "buy",
            },
        )

    def _quote(
        self, data: dict[str, Any], spec: InstrumentSpec, workspace_id: str, epoch: int, metadata_version: str
    ) -> EventEnvelope:
        bid = _decimal(data.get("b"), "best bid", positive=True)
        bid_quantity = _decimal(data.get("B"), "best bid quantity", nonnegative=True)
        ask = _decimal(data.get("a"), "best ask", positive=True)
        ask_quantity = _decimal(data.get("A"), "best ask quantity", nonnegative=True)
        if ask < bid:
            raise AdapterError("Best ask is below best bid.")
        update_id = data.get("u")
        if update_id is not None and (isinstance(update_id, bool) or not isinstance(update_id, int) or update_id < 0):
            raise AdapterError("Binance quote update identifier is malformed.")
        timestamp = _timestamp(data, ("E",))
        identity_material = {
            "u": update_id,
            "b": decimal_text(bid),
            "B": decimal_text(bid_quantity),
            "a": decimal_text(ask),
            "A": decimal_text(ask_quantity),
            "E": timestamp,
        }
        identity = str(update_id) if update_id is not None else hashlib.sha256(_json_text(identity_material).encode("utf-8")).hexdigest()[:24]
        return EventEnvelope(
            workspace_id=workspace_id,
            instrument_id=spec.instrument_id,
            source_id=SOURCE_ID,
            epoch=epoch,
            metadata_version=metadata_version,
            event_id=f"bookTicker:{identity}",
            kind="quote",
            market_ts_ms=timestamp,
            received_at_ms=self._clock.wall_ms(),
            received_monotonic_ns=self._clock.monotonic_ns(),
            sequence_first=None,
            sequence_last=None,
            payload={
                "bid": decimal_text(bid),
                "ask": decimal_text(ask),
                "bid_quantity": decimal_text(bid_quantity),
                "ask_quantity": decimal_text(ask_quantity),
            },
        )

    def start(self, *, workspace_id: str, epoch: int, metadata_version: str) -> bool:
        """Start metadata refresh and stream consumption on an owned worker."""
        if not isinstance(workspace_id, str) or not workspace_id:
            raise ValueError("workspace_id is required")
        if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch <= 0:
            raise ValueError("epoch must be a positive integer")
        if not isinstance(metadata_version, str) or not metadata_version:
            raise ValueError("metadata_version is required")
        with self._lock:
            if not self._transport_closed.is_set():
                if self._epoch is None:
                    self._status = "error"
                else:
                    self._emit_status_locked("error", "transport_closing")
                return False
            if self._worker is not None and self._worker.is_alive():
                if self._epoch is None:
                    self._status = "error"
                else:
                    self._emit_status_locked("error", "worker_stopping")
                return False
            self._worker = None
            while True:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
            self._generation += 1
            generation = self._generation
            self._workspace_id = workspace_id
            self._epoch = epoch
            self._metadata_version = metadata_version
            self._stop_event.clear()
            self._resync_event.clear()
            self._status = "connecting"
            self._emit_status_locked("connecting", "startup")
            self._worker = threading.Thread(
                target=self._run, args=(generation,), name="binance-spot-adapter", daemon=True
            )
            self._worker.start()
            return True

    def _run(self, generation: int) -> None:
        first_attempt = True
        reconnect_delay = 0.25
        consume_stop = _StopOrResync(self._stop_event, self._resync_event)
        try:
            while not self._stop_event.is_set() and generation == self._generation:
                if not first_attempt:
                    with self._lock:
                        if generation != self._generation or self._stop_event.is_set():
                            break
                        self._resync_event.clear()
                        self._advance_epoch_locked()
                        self._emit_status_locked("retrying", "stream_reconnect")
                try:
                    if self._stop_event.is_set() or generation != self._generation:
                        break
                    with self._lock:
                        prior_metadata_version = self._metadata_version
                    spec = self.discover("BTCUSDT")
                    with self._lock:
                        if generation != self._generation or self._stop_event.is_set():
                            break
                        assert self._epoch is not None
                        metadata_changed = spec.metadata_version != prior_metadata_version
                        if metadata_changed:
                            if first_attempt:
                                self._advance_epoch_locked()
                            self._metadata_version = spec.metadata_version
                        epoch = self._epoch
                        workspace_id = self._workspace_id
                        # Metadata is the reset marker for each epoch, even when its
                        # public exchangeInfo hash is unchanged.
                        self._emit_metadata_locked(spec, epoch)
                        if first_attempt:
                            self._emit_status_locked("connecting", "metadata_ready")

                    def on_open() -> None:
                        with self._lock:
                            if not self._stop_event.is_set() and not self._resync_event.is_set() and generation == self._generation:
                                self._emit_status_locked("live", "stream_open")

                    def on_message(message: str | bytes) -> None:
                        try:
                            with self._lock:
                                if self._stop_event.is_set() or self._resync_event.is_set() or generation != self._generation:
                                    return
                                current_epoch = self._epoch
                                current_version = self._metadata_version
                            if workspace_id is None or current_epoch is None or current_version is None:
                                raise AdapterError("Adapter workspace is unavailable.")
                            envelopes = self.normalize(message, workspace_id, current_epoch, current_version)
                            for envelope in envelopes:
                                if not self._resync_event.is_set() and not self._stop_event.is_set():
                                    self._enqueue_market(envelope)
                        except AdapterError:
                            with self._lock:
                                self._rejected_count += 1
                            self._enqueue_control({
                                "kind": "diagnostic",
                                "code": "message_rejected",
                                "reason": "malformed_or_out_of_scope",
                                "epoch": self._current_epoch(),
                            })

                    self._transport.consume(consume_stop, on_message=on_message, on_open=on_open)
                    if self._stop_event.is_set():
                        break
                    first_attempt = False
                    if self._resync_event.is_set():
                        reconnect_delay = 0.25
                        continue
                    with self._lock:
                        self._emit_status_locked("retrying", "stream_ended")
                    if self._wait_for_retry(reconnect_delay):
                        reconnect_delay = 0.25
                        continue
                    reconnect_delay = min(reconnect_delay * 2, _MAX_RECONNECT_SECONDS)
                except Exception:
                    if self._stop_event.is_set():
                        break
                    first_attempt = False
                    with self._lock:
                        if generation != self._generation:
                            break
                        self._emit_status_locked("retrying", "public_feed_unavailable")
                    if self._resync_event.is_set():
                        reconnect_delay = 0.25
                        continue
                    if self._wait_for_retry(reconnect_delay):
                        reconnect_delay = 0.25
                        continue
                    reconnect_delay = min(reconnect_delay * 2, _MAX_RECONNECT_SECONDS)
        finally:
            with self._lock:
                if generation == self._generation and self._status != "disconnected":
                    self._emit_status_locked("disconnected", "stopped")

    def _wait_for_retry(self, delay_seconds: float) -> bool:
        deadline = time.monotonic() + delay_seconds
        while not self._stop_event.is_set():
            if self._resync_event.is_set():
                return True
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            self._resync_event.wait(min(remaining, 0.05))
        return False

    def request_resync(self) -> bool:
        """Ask the worker to close its current consume pass and reconnect."""
        with self._lock:
            worker = self._worker
            if worker is None or not worker.is_alive() or self._stop_event.is_set():
                return False
            self._resync_event.set()
            return True

    def _current_epoch(self) -> int | None:
        with self._lock:
            return self._epoch

    def _advance_epoch_locked(self) -> None:
        assert self._epoch is not None
        self._epoch += 1

    def _emit_status_locked(self, status: str, reason: str) -> None:
        assert self._epoch is not None
        self._status = status
        self._put_control_locked({"kind": "source_status", "status": status, "reason": reason, "epoch": self._epoch})

    def _emit_metadata_locked(self, spec: InstrumentSpec, epoch: int) -> None:
        self._put_control_locked({"kind": "metadata", "spec": spec, "epoch": epoch})

    def _put_control_locked(self, item: dict[str, Any]) -> None:
        try:
            self._queue.put_nowait(item)
        except queue.Full:
            self._resync_overflow_locked()

    def _enqueue_control(self, item: dict[str, Any]) -> None:
        with self._lock:
            self._put_control_locked(item)

    def _enqueue_market(self, envelope: EventEnvelope) -> None:
        try:
            self._queue.put_nowait(envelope)
        except queue.Full:
            with self._lock:
                self._resync_overflow_locked()

    def _resync_overflow_locked(self) -> None:
        dropped = 0
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            if isinstance(item, EventEnvelope):
                dropped += 1
        self._overflow_count += 1
        if self._epoch is not None:
            self._advance_epoch_locked()
            epoch = self._epoch
            self._emit_status_locked("error", "queue_overflow_resync")
            self._queue.put_nowait({
                "kind": "diagnostic", "code": "queue_overflow", "dropped_events": dropped,
                "overflow_count": self._overflow_count, "epoch": epoch,
            })
            if self._spec is not None:
                self._queue.put_nowait({"kind": "metadata", "spec": self._spec, "epoch": epoch})

    def drain(self, limit: int = MAX_DRAIN) -> list[Any]:
        """Return at most 500 queued market or control items without blocking."""
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("drain limit must be a positive integer")
        maximum = min(limit, MAX_DRAIN)
        result = []
        for _ in range(maximum):
            try:
                result.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return result

    def stop(self) -> None:
        """Signal shutdown without waiting on network or worker completion."""
        with self._lock:
            worker = self._worker
            start_close = not self._stop_event.is_set()
            self._stop_event.set()
            self._resync_event.set()
            if self._epoch is not None and self._status != "disconnected":
                self._emit_status_locked("disconnected", "stopped")
            if start_close:
                self._transport_closed.clear()

        def close_transport() -> None:
            try:
                self._transport.close()
            except Exception:
                pass
            finally:
                self._transport_closed.set()

        if start_close:
            threading.Thread(target=close_transport, name="binance-spot-close", daemon=True).start()
        if worker is None or not worker.is_alive():
            with self._lock:
                if self._worker is worker:
                    self._worker = None

    @property
    def status(self) -> str:
        with self._lock:
            return self._status

    @property
    def metrics(self) -> dict[str, int]:
        with self._lock:
            return {"overflow": self._overflow_count, "rejected": self._rejected_count}

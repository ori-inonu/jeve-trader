"""Typed, JSON-safe contracts for observed multimarket data.

Financial values stay as lexical decimal strings. Importing this module performs
no network access and has no dependency on the WIN/Profit adapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import re
from typing import Any


SCHEMA_VERSION = "multimarket.v1"
MAX_DECIMAL_CHARS = 128
_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ORIGINS = {"live", "synthetic", "replay"}
_AGGRESSORS = {"buy", "sell", "unknown"}


class DataContractError(ValueError):
    """A sanitized validation error for malformed market data."""


def decimal_value(value: str, *, allow_zero: bool = False) -> Decimal:
    """Parse an exact decimal from a bounded string; never coerce a float."""
    if not isinstance(value, str) or not value or len(value) > MAX_DECIMAL_CHARS:
        raise DataContractError("decimal must be a non-empty string of at most 128 characters")
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError):
        raise DataContractError("invalid decimal") from None
    if not result.is_finite():
        raise DataContractError("decimal must be finite")
    if result < 0 or (result == 0 and not allow_zero):
        raise DataContractError("decimal must be positive")
    return result


def canonical_payload_sha256(payload: object) -> str:
    """Hash received JSON using the canonical representation in the contract."""
    try:
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        raise DataContractError("payload is not finite JSON data") from None
    return hashlib.sha256(encoded).hexdigest()


def _identifier(value: object, label: str) -> None:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise DataContractError(f"{label} is missing or invalid")


def _text(value: object, label: str, *, allow_empty: bool = False) -> None:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise DataContractError(f"{label} is missing or invalid")


def _timestamp(value: object, label: str, *, optional: bool = False) -> None:
    if value is None and optional:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DataContractError(f"{label} must be a non-negative integer")


def _sequence(value: object, label: str, *, optional: bool = False) -> None:
    if value is None and optional:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DataContractError(f"{label} must be a non-negative integer")


def _finite_json(value: Any, path: str = "value") -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DataContractError(f"{path} must be finite JSON data")
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise DataContractError(f"{path} must be finite JSON data")
        return str(value)
    if is_dataclass(value):
        return _to_json_dict(value)
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise DataContractError(f"{path} keys must be strings")
        return {key: _finite_json(item, path) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_finite_json(item, path) for item in value]
    raise DataContractError(f"{path} is not JSON-safe")


def _to_json_dict(instance: object) -> dict[str, Any]:
    if not is_dataclass(instance):
        raise DataContractError("value is not a contract")
    result = {
        descriptor.name: _finite_json(getattr(instance, descriptor.name), descriptor.name)
        for descriptor in fields(instance)
    }
    try:
        json.dumps(result, allow_nan=False, separators=(",", ":"))
    except (TypeError, ValueError):
        raise DataContractError("contract is not finite JSON data") from None
    return result


def _validate_levels(levels: object, *, allow_zero: bool) -> None:
    if not isinstance(levels, tuple):
        raise DataContractError("book levels must be tuples")
    for level in levels:
        if not isinstance(level, tuple) or len(level) != 2:
            raise DataContractError("book level must contain price and quantity")
        decimal_value(level[0])
        decimal_value(level[1], allow_zero=allow_zero)


@dataclass(frozen=True)
class InstrumentSpec:
    instrument_id: str
    kind: str
    symbol: str
    base_asset: str | None
    quote_asset: str | None
    settlement_currency: str
    tick_size: str | None
    quantity_step: str | None
    multiplier: str | None = None
    expiry: str | None = None
    payoff_type: str = "spot"
    catalog_version: str = "1"
    as_of_ms: int | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        _identifier(self.instrument_id, "instrument_id")
        _identifier(self.kind, "kind")
        _text(self.symbol, "symbol")
        _identifier(self.settlement_currency, "settlement_currency")
        for name in ("base_asset", "quote_asset"):
            value = getattr(self, name)
            if value is not None:
                _identifier(value, name)
        for name in ("tick_size", "quantity_step", "multiplier"):
            value = getattr(self, name)
            if value is not None:
                decimal_value(value)
        _identifier(self.payoff_type, "payoff_type")
        _identifier(self.catalog_version, "catalog_version")
        _timestamp(self.as_of_ms, "as_of_ms", optional=True)
        if not isinstance(self.metadata, dict):
            raise DataContractError("metadata must be an object")
        _finite_json(self.metadata, "metadata")

    def to_dict(self) -> dict[str, Any]:
        return _to_json_dict(self)


@dataclass(frozen=True)
class SourceDescriptor:
    source_id: str
    provider: str
    venue: str
    market: str
    endpoint_version: str
    endpoints: tuple[str, ...]
    auth_required: bool
    terms_url: str
    retention_permission: str
    redistribution_permission: str
    jurisdiction: str | None
    cadence_ms: int | None
    as_of_ms: int
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("source_id", "provider", "venue", "market", "endpoint_version"):
            _identifier(getattr(self, name), name)
        if not isinstance(self.endpoints, tuple):
            raise DataContractError("endpoints must be a tuple")
        for endpoint in self.endpoints:
            _text(endpoint, "endpoint")
        if not isinstance(self.auth_required, bool):
            raise DataContractError("auth_required must be boolean")
        for name in ("terms_url", "retention_permission", "redistribution_permission"):
            _text(getattr(self, name), name)
        if self.jurisdiction is not None:
            _text(self.jurisdiction, "jurisdiction")
        if self.cadence_ms is not None:
            _timestamp(self.cadence_ms, "cadence_ms")
        _timestamp(self.as_of_ms, "as_of_ms")
        if not isinstance(self.evidence_refs, tuple):
            raise DataContractError("evidence_refs must be a tuple")
        for ref in self.evidence_refs:
            _text(ref, "evidence_ref")

    def to_dict(self) -> dict[str, Any]:
        return _to_json_dict(self)


@dataclass(frozen=True)
class MarketEnvelope:
    schema_version: str
    provider: str
    venue: str
    instrument_id: str
    event_kind: str
    exchange_time_ms: int | None
    receive_time_ms: int
    receive_monotonic_ns: int
    origin: str
    session_epoch: str
    payload_sha256: str
    sequence_namespace: str | None = None
    first_sequence: int | None = None
    last_sequence: int | None = None

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise DataContractError("unsupported schema_version")
        for name in ("provider", "venue", "instrument_id", "event_kind", "session_epoch"):
            _identifier(getattr(self, name), name)
        _timestamp(self.exchange_time_ms, "exchange_time_ms", optional=True)
        _timestamp(self.receive_time_ms, "receive_time_ms")
        _timestamp(self.receive_monotonic_ns, "receive_monotonic_ns")
        if self.origin not in _ORIGINS:
            raise DataContractError("origin must be live, synthetic, or replay")
        if not isinstance(self.payload_sha256, str) or not _SHA256_RE.fullmatch(self.payload_sha256):
            raise DataContractError("payload_sha256 must be a SHA-256 hex digest")
        if self.sequence_namespace is not None:
            _identifier(self.sequence_namespace, "sequence_namespace")
        _sequence(self.first_sequence, "first_sequence", optional=True)
        _sequence(self.last_sequence, "last_sequence", optional=True)
        if (self.first_sequence is None) != (self.last_sequence is None):
            raise DataContractError("sequence endpoints must both be present or absent")
        if self.first_sequence is not None and self.first_sequence > self.last_sequence:
            raise DataContractError("sequence interval is reversed")

    def to_dict(self) -> dict[str, Any]:
        return _to_json_dict(self)


@dataclass(frozen=True)
class TradeEvent:
    instrument_id: str
    trade_id: str
    price: str
    quantity: str
    trade_time_ms: int
    aggressor: str
    aggressor_origin: str
    envelope: MarketEnvelope

    def __post_init__(self) -> None:
        _identifier(self.instrument_id, "instrument_id")
        _identifier(self.trade_id, "trade_id")
        decimal_value(self.price)
        decimal_value(self.quantity)
        _timestamp(self.trade_time_ms, "trade_time_ms")
        if self.aggressor not in _AGGRESSORS:
            raise DataContractError("aggressor is invalid")
        _text(self.aggressor_origin, "aggressor_origin")
        if not isinstance(self.envelope, MarketEnvelope):
            raise DataContractError("envelope is invalid")
        if self.envelope.instrument_id != self.instrument_id:
            raise DataContractError("trade and envelope instrument differ")
        if self.envelope.event_kind != "trade":
            raise DataContractError("trade envelope event_kind is invalid")

    def to_dict(self) -> dict[str, Any]:
        return _to_json_dict(self)


@dataclass(frozen=True)
class BookSnapshot:
    instrument_id: str
    last_update_id: int
    bids: tuple[tuple[str, str], ...]
    asks: tuple[tuple[str, str], ...]
    envelope: MarketEnvelope

    def __post_init__(self) -> None:
        _identifier(self.instrument_id, "instrument_id")
        _sequence(self.last_update_id, "last_update_id")
        _validate_levels(self.bids, allow_zero=False)
        _validate_levels(self.asks, allow_zero=False)
        if not isinstance(self.envelope, MarketEnvelope):
            raise DataContractError("envelope is invalid")
        if self.envelope.instrument_id != self.instrument_id:
            raise DataContractError("snapshot and envelope instrument differ")
        if self.envelope.event_kind != "book_snapshot":
            raise DataContractError("snapshot envelope event_kind is invalid")

    def to_dict(self) -> dict[str, Any]:
        return _to_json_dict(self)


@dataclass(frozen=True)
class BookDelta:
    instrument_id: str
    first_update_id: int
    last_update_id: int
    bids: tuple[tuple[str, str], ...]
    asks: tuple[tuple[str, str], ...]
    envelope: MarketEnvelope

    def __post_init__(self) -> None:
        _identifier(self.instrument_id, "instrument_id")
        _sequence(self.first_update_id, "first_update_id")
        _sequence(self.last_update_id, "last_update_id")
        if self.first_update_id > self.last_update_id:
            raise DataContractError("book delta sequence is reversed")
        _validate_levels(self.bids, allow_zero=True)
        _validate_levels(self.asks, allow_zero=True)
        if not isinstance(self.envelope, MarketEnvelope):
            raise DataContractError("envelope is invalid")
        if self.envelope.instrument_id != self.instrument_id:
            raise DataContractError("delta and envelope instrument differ")
        if self.envelope.event_kind != "book_delta":
            raise DataContractError("delta envelope event_kind is invalid")
        if (self.envelope.first_sequence, self.envelope.last_sequence) != (
            self.first_update_id, self.last_update_id
        ):
            raise DataContractError("delta sequence differs from envelope")

    def to_dict(self) -> dict[str, Any]:
        return _to_json_dict(self)


@dataclass(frozen=True)
class BookView:
    instrument_id: str
    state: str
    valid: bool
    last_update_id: int | None
    bids: tuple[tuple[str, str], ...]
    asks: tuple[tuple[str, str], ...]
    depth_limit: int
    coverage: str
    checksum_status: str
    reason: str = ""

    def __post_init__(self) -> None:
        _identifier(self.instrument_id, "instrument_id")
        _identifier(self.state, "state")
        if not isinstance(self.valid, bool):
            raise DataContractError("valid must be boolean")
        _sequence(self.last_update_id, "last_update_id", optional=True)
        _validate_levels(self.bids, allow_zero=False)
        _validate_levels(self.asks, allow_zero=False)
        _sequence(self.depth_limit, "depth_limit")
        _identifier(self.coverage, "coverage")
        _identifier(self.checksum_status, "checksum_status")
        _text(self.reason, "reason", allow_empty=True)
        if self.valid and self.last_update_id is None:
            raise DataContractError("valid book requires a sequence")

    def to_dict(self) -> dict[str, Any]:
        return _to_json_dict(self)


@dataclass(frozen=True)
class SourceHealth:
    channel: str
    connected: bool
    state: str
    valid: bool
    stale: bool
    coverage: str
    last_exchange_time_ms: int | None
    last_receive_time_ms: int | None
    last_receive_monotonic_ns: int | None
    sequence_ok: bool
    gaps: int
    resyncs: int
    dropped_events: int
    dropped_bytes: int
    reason: str
    metrics: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        _identifier(self.channel, "channel")
        for name in ("connected", "valid", "stale", "sequence_ok"):
            if not isinstance(getattr(self, name), bool):
                raise DataContractError(f"{name} must be boolean")
        _identifier(self.state, "state")
        _identifier(self.coverage, "coverage")
        for name in ("last_exchange_time_ms", "last_receive_time_ms", "last_receive_monotonic_ns"):
            _timestamp(getattr(self, name), name, optional=True)
        for name in ("gaps", "resyncs", "dropped_events", "dropped_bytes"):
            _sequence(getattr(self, name), name)
        _text(self.reason, "reason", allow_empty=True)
        if not isinstance(self.metrics, dict):
            raise DataContractError("metrics must be an object")
        _finite_json(self.metrics, "metrics")

    def to_dict(self) -> dict[str, Any]:
        return _to_json_dict(self)


@dataclass(frozen=True)
class FeedBatch:
    source: SourceDescriptor
    instrument: InstrumentSpec
    trades: tuple[TradeEvent, ...]
    book: BookView | None
    health: tuple[SourceHealth, ...]
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source, SourceDescriptor):
            raise DataContractError("source is invalid")
        if not isinstance(self.instrument, InstrumentSpec):
            raise DataContractError("instrument is invalid")
        if not isinstance(self.trades, tuple) or any(not isinstance(item, TradeEvent) for item in self.trades):
            raise DataContractError("trades must be a tuple of TradeEvent")
        if any(item.instrument_id != self.instrument.instrument_id for item in self.trades):
            raise DataContractError("trade instrument differs from batch instrument")
        if self.book is not None:
            if not isinstance(self.book, BookView) or self.book.instrument_id != self.instrument.instrument_id:
                raise DataContractError("book instrument differs from batch instrument")
        if not isinstance(self.health, tuple) or any(not isinstance(item, SourceHealth) for item in self.health):
            raise DataContractError("health must be a tuple of SourceHealth")
        if not isinstance(self.warnings, tuple):
            raise DataContractError("warnings must be a tuple")
        for warning in self.warnings:
            _text(warning, "warning")

    def to_dict(self) -> dict[str, Any]:
        return _to_json_dict(self)
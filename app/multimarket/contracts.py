from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_required")
    return value.strip()


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field)


def _domain_decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, (bool, float)) or not isinstance(value, Decimal):
        raise TypeError(f"{field}_must_be_decimal")
    if not value.is_finite():
        raise ValueError(f"{field}_must_be_finite")
    return value


def _wire_decimal(value: Any, field: str) -> Decimal:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{field}_must_be_decimal_string")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field}_invalid_decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{field}_must_be_finite")
    return result


def decimal_text(value: Decimal) -> str:
    """Serialize a finite domain Decimal as plain, canonical text."""
    value = _domain_decimal(value, "value")
    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _number(value: Any, field: str, *, optional: bool = False, positive: bool = False, nonnegative: bool = False) -> Decimal | None:
    if value is None and optional:
        return None
    result = _domain_decimal(value, field)
    if positive and result <= 0:
        raise ValueError(f"{field}_must_be_positive")
    if nonnegative and result < 0:
        raise ValueError(f"{field}_must_be_nonnegative")
    return result


def _integer(value: Any, field: str, *, optional: bool = False, positive: bool = False) -> int | None:
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field}_must_be_integer")
    if value < (1 if positive else 0):
        raise ValueError(f"{field}_out_of_range")
    return value


class SystemClock:
    """Clock seam used for age calculations; wall and monotonic time stay separate."""

    def wall_ms(self) -> int:
        return int(time.time() * 1000)

    def monotonic_ns(self) -> int:
        return time.monotonic_ns()


@dataclass(frozen=True)
class InstrumentSpec:
    instrument_id: str
    venue: str
    segment: str
    symbol: str
    family: str
    metadata_version: str
    price_tick: Decimal | None
    quantity_step: Decimal | None
    quantity_min: Decimal | None
    minimum_notional: Decimal | None
    contract_multiplier: Decimal | None
    base_asset: str | None
    quote_currency: str | None
    settlement_currency: str | None
    expiry_at_ms: int | None
    calendar_id: str | None
    status: str
    constraints_verified: bool

    def __post_init__(self) -> None:
        for name in ("instrument_id", "venue", "segment", "symbol", "family", "metadata_version", "status"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        for name in ("base_asset", "quote_currency", "settlement_currency", "calendar_id"):
            object.__setattr__(self, name, _optional_text(getattr(self, name), name))
        positive = {"price_tick", "quantity_step", "contract_multiplier"}
        nonnegative = {"quantity_min", "minimum_notional"}
        for name in positive | nonnegative:
            value = _number(getattr(self, name), name, optional=True, positive=name in positive, nonnegative=name in nonnegative)
            object.__setattr__(self, name, value)
        if self.expiry_at_ms is not None:
            object.__setattr__(self, "expiry_at_ms", _integer(self.expiry_at_ms, "expiry_at_ms"))
        if not isinstance(self.constraints_verified, bool):
            raise TypeError("constraints_verified_must_be_bool")
        if self.constraints_verified:
            required = ("price_tick", "quantity_step", "quantity_min", "minimum_notional", "contract_multiplier", "quote_currency", "settlement_currency")
            if any(getattr(self, name) is None for name in required):
                raise ValueError("verified_constraints_incomplete")

    def to_wire(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            result[name] = decimal_text(value) if isinstance(value, Decimal) else value
        return result

    @classmethod
    def from_wire(cls, value: Mapping[str, Any]) -> "InstrumentSpec":
        _require_mapping(value, "instrument")
        _only_keys(value, cls.__dataclass_fields__, "instrument")
        decimals = {"price_tick", "quantity_step", "quantity_min", "minimum_notional", "contract_multiplier"}
        values = {name: (_wire_decimal(raw, name) if name in decimals and raw is not None else raw) for name, raw in value.items()}
        return cls(**values)


@dataclass(frozen=True)
class SourceCapabilities:
    source_id: str
    version: str
    quote: bool
    trades: bool
    book: bool
    account: bool
    trade_semantics: str
    side_semantics: str
    sequence_scope: str
    book_mode: str
    full_tape: bool
    retention: str
    export: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _text(self.source_id, "source_id"))
        object.__setattr__(self, "version", _text(self.version, "version"))
        for name in ("quote", "trades", "book", "account", "full_tape"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name}_must_be_bool")
        for name in ("trade_semantics", "side_semantics", "sequence_scope", "book_mode", "retention", "export"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.book_mode not in {"l1", "l2", "unavailable", "unknown"}:
            raise ValueError("invalid_book_mode")
        if self.retention not in {"allowed", "denied", "unknown"} or self.export not in {"allowed", "denied", "unknown"}:
            raise ValueError("invalid_retention_policy")
        if self.book_mode == "unavailable" and self.book:
            raise ValueError("book_mode_conflict")

    def to_wire(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}

    @classmethod
    def from_wire(cls, value: Mapping[str, Any]) -> "SourceCapabilities":
        _require_mapping(value, "source")
        _only_keys(value, cls.__dataclass_fields__, "source")
        return cls(**dict(value))


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if isinstance(value, Decimal):
        return decimal_text(value)
    if isinstance(value, float):
        raise TypeError("float_not_allowed_in_payload")
    if value is None or isinstance(value, (str, bool, int)):
        return value
    raise TypeError("unsupported_payload_value")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


@dataclass(frozen=True)
class EventEnvelope:
    workspace_id: str
    instrument_id: str
    source_id: str
    epoch: int
    metadata_version: str
    event_id: str
    kind: str
    market_ts_ms: int
    received_at_ms: int
    received_monotonic_ns: int
    sequence_first: int | None
    sequence_last: int | None
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        for name in ("workspace_id", "instrument_id", "source_id", "metadata_version", "event_id"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.kind not in {"quote", "trade", "book"}:
            raise ValueError("invalid_event_kind")
        object.__setattr__(self, "epoch", _integer(self.epoch, "epoch", positive=True))
        for name in ("market_ts_ms", "received_at_ms", "received_monotonic_ns"):
            object.__setattr__(self, name, _integer(getattr(self, name), name))
        first = _integer(self.sequence_first, "sequence_first", optional=True)
        last = _integer(self.sequence_last, "sequence_last", optional=True)
        if (first is None) != (last is None):
            raise ValueError("sequence_bounds_incomplete")
        if first is not None and first > last:
            raise ValueError("sequence_bounds_reversed")
        object.__setattr__(self, "sequence_first", first)
        object.__setattr__(self, "sequence_last", last)
        _require_mapping(self.payload, "payload")
        payload = dict(self.payload)
        if self.kind == "quote":
            _require_keys(payload, {"bid", "ask", "bid_quantity", "ask_quantity"}, "quote_payload")
            bid = _wire_decimal(payload["bid"], "bid")
            ask = _wire_decimal(payload["ask"], "ask")
            bid_qty = _wire_decimal(payload["bid_quantity"], "bid_quantity")
            ask_qty = _wire_decimal(payload["ask_quantity"], "ask_quantity")
            if bid <= 0 or ask < bid or bid_qty < 0 or ask_qty < 0:
                raise ValueError("invalid_quote_values")
            payload.update({"bid": decimal_text(bid), "ask": decimal_text(ask), "bid_quantity": decimal_text(bid_qty), "ask_quantity": decimal_text(ask_qty)})
        elif self.kind == "trade":
            _require_keys(payload, {"price", "quantity", "aggressor"}, "trade_payload")
            price = _wire_decimal(payload["price"], "price")
            quantity = _wire_decimal(payload["quantity"], "quantity")
            if price <= 0 or quantity <= 0 or payload["aggressor"] not in {"buy", "sell", "unknown"}:
                raise ValueError("invalid_trade_values")
            payload.update({"price": decimal_text(price), "quantity": decimal_text(quantity)})
        object.__setattr__(self, "payload", _freeze_json(payload))

    def to_wire(self) -> dict[str, Any]:
        return {
            "schema_version": 3,
            "workspace_id": self.workspace_id,
            "instrument_id": self.instrument_id,
            "source_id": self.source_id,
            "epoch": self.epoch,
            "metadata_version": self.metadata_version,
            "event_id": self.event_id,
            "kind": self.kind,
            "market_ts_ms": self.market_ts_ms,
            "received_at_ms": self.received_at_ms,
            "received_monotonic_ns": self.received_monotonic_ns,
            "sequence_first": self.sequence_first,
            "sequence_last": self.sequence_last,
            "payload": _thaw_json(self.payload),
        }

    @classmethod
    def from_wire(cls, value: Mapping[str, Any]) -> "EventEnvelope":
        _require_mapping(value, "event")
        if value.get("schema_version") != 3:
            raise ValueError("unsupported_event_schema")
        names = set(cls.__dataclass_fields__)
        _only_keys(value, names | {"schema_version"}, "event")
        return cls(**{name: value[name] for name in names})


@dataclass(frozen=True)
class EvaluationIdentity:
    workspace_id: str
    instrument_id: str
    source_id: str
    epoch: int
    metadata_version: str
    feature_version: str
    question_version: str
    cost_revision: int
    account_id: str | None
    account_revision: int | None
    selection_revision: int
    event_range: tuple[str, str] | None
    received_monotonic_ns: int

    def __post_init__(self) -> None:
        for name in ("workspace_id", "instrument_id", "source_id", "metadata_version", "feature_version", "question_version"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "account_id", _optional_text(self.account_id, "account_id"))
        for name in ("epoch", "cost_revision", "selection_revision", "received_monotonic_ns"):
            object.__setattr__(self, name, _integer(getattr(self, name), name))
        revision = _integer(self.account_revision, "account_revision", optional=True)
        if (self.account_id is None) != (revision is None):
            raise ValueError("account_identity_revision_mismatch")
        object.__setattr__(self, "account_revision", revision)
        if self.event_range is not None:
            if not isinstance(self.event_range, (tuple, list)) or len(self.event_range) != 2:
                raise ValueError("invalid_event_range")
            object.__setattr__(self, "event_range", (_text(self.event_range[0], "event_range_start"), _text(self.event_range[1], "event_range_end")))

    def to_wire(self) -> dict[str, Any]:
        result = {name: getattr(self, name) for name in self.__dataclass_fields__}
        if self.event_range is not None:
            result["event_range"] = list(self.event_range)
        return result

    @classmethod
    def from_wire(cls, value: Mapping[str, Any]) -> "EvaluationIdentity":
        _require_mapping(value, "evaluation_identity")
        _only_keys(value, cls.__dataclass_fields__, "evaluation_identity")
        return cls(**dict(value))


@dataclass(frozen=True)
class WorkspaceSpec:
    workspace_id: str
    instrument_id: str
    source_id: str
    account_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("workspace_id", "instrument_id", "source_id"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "account_id", _optional_text(self.account_id, "account_id"))

    def to_wire(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


class Registry:
    def __init__(self, *, clock: Any = None, max_workspaces: int = 8):
        if isinstance(max_workspaces, bool) or not isinstance(max_workspaces, int) or max_workspaces < 1:
            raise ValueError("max_workspaces_must_be_positive")
        self.clock = clock or SystemClock()
        self.max_workspaces = max_workspaces
        self.revision = 0
        self.selection_revision = 0
        self._instruments: dict[str, InstrumentSpec] = {}
        self._sources: dict[str, SourceCapabilities] = {}
        self._workspaces: dict[str, WorkspaceSpec] = {}
        self._selected_workspace_id: str | None = None

    def register_instrument(self, spec: InstrumentSpec) -> InstrumentSpec:
        if not isinstance(spec, InstrumentSpec):
            raise TypeError("instrument_spec_required")
        current = self._instruments.get(spec.instrument_id)
        if current is not None and current != spec:
            raise ValueError("instrument_identity_conflict")
        if current is None:
            self._instruments[spec.instrument_id] = spec
            self.revision += 1
        return spec

    def register_source(self, caps: SourceCapabilities) -> SourceCapabilities:
        if not isinstance(caps, SourceCapabilities):
            raise TypeError("source_capabilities_required")
        current = self._sources.get(caps.source_id)
        if current is not None and current != caps:
            raise ValueError("source_identity_conflict")
        if current is None:
            self._sources[caps.source_id] = caps
            self.revision += 1
        return caps

    def open_workspace(self, *, source_id: str, instrument_id: str, account_id: str | None = None, workspace_id: str | None = None) -> WorkspaceSpec:
        source_id = _text(source_id, "source_id")
        instrument_id = _text(instrument_id, "instrument_id")
        account_id = _optional_text(account_id, "account_id")
        if source_id not in self._sources:
            raise KeyError("source_not_registered")
        if instrument_id not in self._instruments:
            raise KeyError("instrument_not_registered")
        if len(self._workspaces) >= self.max_workspaces and workspace_id not in self._workspaces:
            raise OverflowError("workspace_limit")
        workspace = WorkspaceSpec(workspace_id or uuid4().hex, instrument_id, source_id, account_id)
        current = self._workspaces.get(workspace.workspace_id)
        if current is not None:
            if current != workspace:
                raise ValueError("workspace_identity_conflict")
            return current
        self._workspaces[workspace.workspace_id] = workspace
        self.revision += 1
        return workspace

    def select(self, workspace_id: str) -> WorkspaceSpec:
        workspace_id = _text(workspace_id, "workspace_id")
        workspace = self.get_workspace(workspace_id)
        if self._selected_workspace_id != workspace_id:
            self._selected_workspace_id = workspace_id
            self.selection_revision += 1
            self.revision += 1
        return workspace

    def get_workspace(self, workspace_id: str) -> WorkspaceSpec:
        return self._workspaces[workspace_id]

    def get_instrument(self, instrument_id: str) -> InstrumentSpec:
        return self._instruments[instrument_id]

    def get_source(self, source_id: str) -> SourceCapabilities:
        return self._sources[source_id]

    def snapshot(self) -> dict[str, Any]:
        workspaces = []
        for workspace in self._workspaces.values():
            spec = self._instruments[workspace.instrument_id]
            workspaces.append({**workspace.to_wire(), "symbol": spec.symbol, "venue": spec.venue, "segment": spec.segment, "status": "ready" if spec.constraints_verified else "waiting", "reason": None if spec.constraints_verified else "metadata_unverified"})
        return {
            "revision": self.revision,
            "selection_revision": self.selection_revision,
            "selected_workspace_id": self._selected_workspace_id,
            "workspaces": workspaces,
        }


def _require_mapping(value: Any, field: str) -> None:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field}_must_be_object")


def _only_keys(value: Mapping[str, Any], allowed: Any, field: str) -> None:
    extras = set(value) - set(allowed)
    missing = set(allowed) - set(value)
    if extras or missing:
        raise ValueError(f"{field}_keys_invalid:missing={sorted(missing)}:extra={sorted(extras)}")


def _require_keys(value: Mapping[str, Any], required: set[str], field: str) -> None:
    missing = required - set(value)
    if missing:
        raise ValueError(f"{field}_keys_missing:{','.join(sorted(missing))}")

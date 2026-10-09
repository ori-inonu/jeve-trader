"""Pure, sanitized context assembly for multimarket observation."""
from __future__ import annotations

import json
import math
import re
from decimal import Decimal
from typing import Any

from market_data_contract import DataContractError, FeedBatch, SCHEMA_VERSION


MAX_CONTEXT_BYTES = 64 * 1024
MAX_BOOK_LEVELS = 20
MAX_VAP_LEVELS = 20
_SAFE_REF = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
_BLOCKED_KEY_PARTS = {
    "account", "apikey", "authorization", "cookie", "credential", "password",
    "payload", "private", "raw", "secret", "token", "transcript", "wallet",
}


def build_multimarket_context(
    batch: FeedBatch,
    *,
    features: dict | None = None,
    economics: dict | None = None,
    as_of_ms: int,
) -> dict:
    """Build JSON-safe observational context without network or JEV calls."""
    if not isinstance(batch, FeedBatch):
        raise DataContractError("context requires a FeedBatch")
    if isinstance(as_of_ms, bool) or not isinstance(as_of_ms, int) or as_of_ms < 0:
        raise DataContractError("as_of_ms must be a non-negative integer")
    state = {"truncated": False, "redacted": False}
    missing: list[str] = []
    if features is not None and not isinstance(features, dict):
        missing.append("features_invalid")
        raw_features: dict = {}
    else:
        raw_features = features or {}
    if economics is not None and not isinstance(economics, dict):
        missing.append("economics_invalid")
        raw_economics: dict = {}
    else:
        raw_economics = economics or {}

    safe_features: dict[str, Any] = {}
    for key, value in list(raw_features.items())[:80]:
        if not isinstance(key, str):
            state["truncated"] = True
            continue
        if _blocked_key(key):
            state["redacted"] = True
            continue
        if key in {"book", "volume_at_price", "missing", "evidence_refs"}:
            continue
        clean_key = _safe_string(key, state, max_chars=96)
        if clean_key:
            safe_features[clean_key] = _safe_value(value, state)
    if len(raw_features) > 80:
        state["truncated"] = True

    book = _book_projection(batch.book, state, missing)
    safe_features["book"] = book
    if batch.book is None:
        missing.append("book_missing")

    vap, vap_missing = _vap_projection(raw_features.get("volume_at_price"), state)
    if vap is not None:
        safe_features["volume_at_price"] = vap
        missing.extend(vap_missing)

    for source_map in (raw_features, raw_economics):
        provided_missing = source_map.get("missing")
        if isinstance(provided_missing, (tuple, list)):
            for item in provided_missing[:100]:
                if isinstance(item, str):
                    clean = _safe_string(item, state, max_chars=128)
                    if clean:
                        missing.append(clean)

    safe_economics = _safe_mapping(raw_economics, state, limit=80, exclude={"missing", "evidence_refs"})
    source = _source_projection(batch.source, state)
    instrument = _instrument_projection(batch.instrument, state)
    health = [_health_projection(item, state) for item in batch.health[:8]]
    if not health:
        missing.append("health_missing")
    if len(batch.health) > 8:
        state["truncated"] = True
        missing.append("health_entries_truncated")

    evidence_refs = [f"source:{batch.source.source_id}", f"instrument:{batch.instrument.instrument_id}"]
    for source_map in (raw_features, raw_economics):
        refs = source_map.get("evidence_refs")
        if isinstance(refs, (tuple, list)):
            evidence_refs.extend(ref for ref in refs[:100] if _valid_reference(ref))
    if vap is not None:
        evidence_refs.extend(ref for ref in vap.get("evidence_refs", []) if _valid_reference(ref))
    evidence_refs = list(dict.fromkeys(evidence_refs))[:100]

    context = {
        "schema_version": SCHEMA_VERSION,
        "as_of_ms": as_of_ms,
        "objective": "multimarket_observation_and_evidence_for_decision_support",
        "source": source,
        "instrument": instrument,
        "health": health,
        "features": safe_features,
        "economics": safe_economics,
        "missing": _unique_strings(missing),
        "evidence_refs": evidence_refs,
        "allowed_actions": ["wait", "observe"],
        "jev_comment": None,
        "profit_probability": None,
        "target_probability": None,
        "truncated": state["truncated"],
    }
    if state["redacted"]:
        context["missing"].append("sensitive_fields_removed")
        context["missing"] = _unique_strings(context["missing"])
    if context["truncated"]:
        context["missing"].append("context_truncated")
        context["missing"] = _unique_strings(context["missing"])
    _fit_context(context)
    return context


def _blocked_key(value: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", value.lower())
    return any(part in normalized for part in _BLOCKED_KEY_PARTS)


def _safe_string(value: str, state: dict, *, max_chars: int = 1024) -> str:
    if len(value) > max_chars:
        state["truncated"] = True
        return value[:max_chars]
    return value


def _safe_value(value: Any, state: dict, *, depth: int = 0) -> Any:
    if depth > 8:
        state["truncated"] = True
        return None
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        return _safe_string(value, state)
    if isinstance(value, int):
        if value.bit_length() > 420:
            state["truncated"] = True
            if value.bit_length() > 13_000:
                return "[oversized integer omitted]"
            return str(value)[:128]
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            state["truncated"] = True
            return None
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            state["truncated"] = True
            return None
        return _safe_string(str(value), state, max_chars=128)
    if isinstance(value, dict):
        return _safe_mapping(value, state, limit=64, depth=depth + 1)
    if isinstance(value, (tuple, list)):
        result = [_safe_value(item, state, depth=depth + 1) for item in value[:64]]
        if len(value) > 64:
            state["truncated"] = True
        return result
    if hasattr(value, "to_dict"):
        try:
            return _safe_mapping(value.to_dict(), state, limit=64, depth=depth + 1)
        except Exception:
            state["truncated"] = True
            return None
    state["truncated"] = True
    return None


def _safe_mapping(
    value: dict,
    state: dict,
    *,
    limit: int = 64,
    depth: int = 0,
    exclude: set[str] | None = None,
) -> dict:
    result: dict[str, Any] = {}
    exclude = exclude or set()
    try:
        items = list(value.items())
    except Exception:
        state["truncated"] = True
        return result
    if len(items) > limit:
        state["truncated"] = True
    for key, item in items[:limit]:
        if not isinstance(key, str):
            state["truncated"] = True
            continue
        if key in exclude:
            continue
        if _blocked_key(key):
            state["redacted"] = True
            continue
        clean_key = _safe_string(key, state, max_chars=96)
        if clean_key:
            result[clean_key] = _safe_value(item, state, depth=depth)
    return result


def _source_projection(source: Any, state: dict) -> dict:
    fields = (
        "source_id", "provider", "venue", "market", "endpoint_version", "auth_required",
        "retention_permission", "redistribution_permission", "jurisdiction", "cadence_ms", "as_of_ms",
    )
    return {name: _safe_value(getattr(source, name), state) for name in fields}


def _instrument_projection(instrument: Any, state: dict) -> dict:
    fields = (
        "instrument_id", "kind", "symbol", "base_asset", "quote_asset", "settlement_currency",
        "tick_size", "quantity_step", "multiplier", "expiry", "payoff_type", "catalog_version", "as_of_ms",
    )
    return {name: _safe_value(getattr(instrument, name), state) for name in fields}


def _health_projection(health: Any, state: dict) -> dict:
    fields = (
        "channel", "connected", "state", "valid", "stale", "coverage", "last_exchange_time_ms",
        "last_receive_time_ms", "last_receive_monotonic_ns", "sequence_ok", "gaps", "resyncs",
        "dropped_events", "dropped_bytes", "reason",
    )
    return {name: _safe_value(getattr(health, name), state) for name in fields}


def _book_projection(book: Any, state: dict, missing: list[str]) -> dict | None:
    if book is None:
        return None
    bids = list(book.bids[:MAX_BOOK_LEVELS])
    asks = list(book.asks[:MAX_BOOK_LEVELS])
    if len(book.bids) > MAX_BOOK_LEVELS or len(book.asks) > MAX_BOOK_LEVELS:
        state["truncated"] = True
        missing.append("book_levels_truncated")
    return {
        "state": _safe_value(book.state, state),
        "valid": book.valid,
        "last_update_id": book.last_update_id,
        "bids": [[_safe_value(price, state), _safe_value(quantity, state)] for price, quantity in bids],
        "asks": [[_safe_value(price, state), _safe_value(quantity, state)] for price, quantity in asks],
        "depth_limit": book.depth_limit,
        "coverage": _safe_value(book.coverage, state),
        "checksum_status": _safe_value(book.checksum_status, state),
        "reason": _safe_string(book.reason, state, max_chars=256),
    }


def _vap_projection(value: Any, state: dict) -> tuple[dict | None, list[str]]:
    if value is None:
        return None, []
    if not isinstance(value, dict):
        state["truncated"] = True
        return None, ["volume_at_price_invalid"]
    result: dict[str, Any] = {"schema_version": SCHEMA_VERSION}
    fields = (
        "instrument_id", "venue", "start_ms", "end_ms", "unit", "total_quantity", "total_notional",
        "trade_count", "coverage", "duplicates", "conflicts", "evictions", "missing", "evidence_refs",
    )
    for name in fields:
        if name in value:
            item = value[name]
            if name == "evidence_refs" and isinstance(item, (tuple, list)):
                result[name] = [ref for ref in item[:100] if _valid_reference(ref)]
                if len(item) > 100:
                    state["truncated"] = True
            elif name == "missing" and isinstance(item, (tuple, list)):
                result[name] = [_safe_string(entry, state, max_chars=128) for entry in item[:50] if isinstance(entry, str)]
            else:
                result[name] = _safe_value(item, state)
    raw_levels = value.get("levels", [])
    levels: list[dict] = []
    if isinstance(raw_levels, (tuple, list)):
        for raw_level in raw_levels[:MAX_VAP_LEVELS]:
            if not isinstance(raw_level, dict):
                state["truncated"] = True
                continue
            clean = {
                key: _safe_value(raw_level[key], state)
                for key in ("price", "quantity", "notional", "trade_count")
                if key in raw_level
            }
            aggressors = raw_level.get("aggressor_counts")
            if isinstance(aggressors, dict):
                clean["aggressor_counts"] = {
                    name: _safe_value(aggressors.get(name, 0), state)
                    for name in ("buy", "sell", "unknown")
                }
            levels.append(clean)
        if len(raw_levels) > MAX_VAP_LEVELS:
            state["truncated"] = True
    else:
        state["truncated"] = True
    result["levels"] = levels
    result["full_tape"] = False
    local_missing = result.get("missing", [])
    if len(raw_levels) > MAX_VAP_LEVELS:
        local_missing = [*local_missing, "volume_at_price_levels_truncated"]
    result["missing"] = _unique_strings(local_missing)
    return result, result["missing"]


def _valid_reference(value: Any) -> bool:
    return isinstance(value, str) and bool(_SAFE_REF.fullmatch(value))


def _unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in result:
            result.append(value[:128])
        if len(result) >= 100:
            break
    return result


def _encoded_size(value: dict) -> int:
    try:
        return len(json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8"))
    except (TypeError, ValueError, UnicodeError):
        raise DataContractError("context is not finite JSON data") from None


def _fit_context(context: dict) -> None:
    if _encoded_size(context) <= MAX_CONTEXT_BYTES:
        return
    context["truncated"] = True
    context["missing"] = _unique_strings([*context["missing"], "context_truncated"])
    features = context["features"]
    economics = context["economics"]
    candidates = []
    for section_name, section in (("features", features), ("economics", economics)):
        for key, value in section.items():
            if section_name == "features" and key in {"book", "volume_at_price"}:
                continue
            candidates.append((_encoded_size({key: value}), section_name, key))
    for _size, section_name, key in sorted(candidates, reverse=True):
        section = context[section_name]
        if key in section:
            del section[key]
            section["truncated"] = True
            if _encoded_size(context) <= MAX_CONTEXT_BYTES:
                return
    vap = context["features"].get("volume_at_price")
    while isinstance(vap, dict) and vap.get("levels") and _encoded_size(context) > MAX_CONTEXT_BYTES:
        vap["levels"].pop()
        vap["missing"] = _unique_strings([*vap.get("missing", []), "context_truncated"])
    book = context["features"].get("book")
    while isinstance(book, dict) and _encoded_size(context) > MAX_CONTEXT_BYTES and (book["bids"] or book["asks"]):
        if book["bids"]:
            book["bids"].pop()
        if book["asks"]:
            book["asks"].pop()
        context["missing"] = _unique_strings([*context["missing"], "context_truncated"])
    if _encoded_size(context) > MAX_CONTEXT_BYTES:
        context["health"] = []
        context["features"] = {"book": None, "truncated": True}
        context["economics"] = {"truncated": True}
        context["evidence_refs"] = context["evidence_refs"][:10]
        context["missing"] = _unique_strings([*context["missing"][:20], "context_truncated"])
    if _encoded_size(context) > MAX_CONTEXT_BYTES:
        raise DataContractError("context cannot fit the 64 KiB budget")

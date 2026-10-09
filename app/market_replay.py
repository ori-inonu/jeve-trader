"""Bounded, opt-in market journal and deterministic local replay helpers."""
from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import dataclass
from decimal import Decimal, DecimalException, MAX_EMAX, MIN_EMIN, localcontext
from pathlib import Path
import re
import time
from typing import Any, Iterable, Iterator

from market_data_contract import (
    DataContractError,
    InstrumentSpec,
    SCHEMA_VERSION,
    TradeEvent,
    canonical_payload_sha256,
    decimal_value,
)


MAX_JOURNAL_BYTES = 64 * 1024 * 1024
MAX_CHUNK_BYTES = 8 * 1024 * 1024
MAX_RECORD_BYTES = 1024 * 1024
MAX_MANAGED_BYTES = 32 * 1024 * 1024
_MAX_EXACT_DECIMAL_DIGITS = 4096
_HEADER_FIELDS = {
    "schema_version", "adapter_version", "source", "instrument", "origin",
    "permission_ref", "created_at_ms",
}

@dataclass(frozen=True)
class RetentionPolicy:
    enabled: bool = False
    permission_ref: str | None = None
    max_bytes: int = 64 * 1024 * 1024
    max_age_seconds: int = 24 * 60 * 60
    max_chunk_bytes: int = 8 * 1024 * 1024

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise DataContractError("retention enabled must be boolean")
        if self.permission_ref is not None and (
            not isinstance(self.permission_ref, str) or not self.permission_ref.strip()
        ):
            raise DataContractError("permission_ref must be non-empty text")
        for name in ("max_bytes", "max_age_seconds", "max_chunk_bytes"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise DataContractError(f"{name} must be a positive integer")
        if self.max_bytes > MAX_JOURNAL_BYTES:
            raise DataContractError("max_bytes exceeds the 64 MiB retention ceiling")
        if self.max_age_seconds > 24 * 60 * 60:
            raise DataContractError("max_age_seconds exceeds the 24 hour retention ceiling")
        if self.max_chunk_bytes > MAX_CHUNK_BYTES:
            raise DataContractError("max_chunk_bytes exceeds the 8 MiB chunk ceiling")


class JournalWriter:
    """Opt-in journal writer. The default policy has no filesystem effects."""

    def __init__(self, path: str | Path | None = None, *, policy: RetentionPolicy = RetentionPolicy()) -> None:
        self._path = Path(path) if path is not None else None
        self._policy = policy
        self._state = "disabled" if not policy.enabled else "ready"
        self._reason: str | None = "disabled" if not policy.enabled else None
        self._bytes_written = 0
        self._records_written = 0
        self._chunks: list[Path] = []
        self._header: dict | None = None
        self._header_line: bytes | None = None
        self._chunk_bytes = 0
        self._handle = None
        self._closed = False
        self._started_monotonic = time.monotonic()
        if policy.enabled:
            if self._path is None:
                raise DataContractError("enabled retention requires an explicit path")
            self._validate_location()

    def append(self, record: dict) -> bool:
        if not self._policy.enabled:
            return False
        if self._closed:
            raise DataContractError("journal is closed")
        if self._state in {"budget_reached", "invalid"}:
            return False
        if time.monotonic() - self._started_monotonic >= self._policy.max_age_seconds:
            self._stop_at_budget("max_age_seconds")
            return False
        if not isinstance(record, dict):
            raise DataContractError("journal entry must be an object")
        if self._header is None:
            return self._append_header(record)
        return self._append_record(record)

    def _validate_location(self) -> None:
        assert self._path is not None
        if not self._path.name or self._path.name in {".", ".."}:
            raise DataContractError("journal path must name a file")
        try:
            parent = self._path.parent.resolve(strict=True)
        except OSError:
            raise DataContractError("journal parent directory must already exist") from None
        if not parent.is_dir():
            raise DataContractError("journal parent must be a directory")
        target = parent / self._path.name
        if target.exists() or target.is_symlink():
            raise DataContractError("journal target must not already exist")
        repo_root = Path(__file__).resolve().parent.parent
        try:
            target.relative_to(repo_root)
        except ValueError:
            pass
        else:
            raise DataContractError("journal path must be outside the repository")
        self._path = target

    def _append_header(self, record: dict) -> bool:
        if set(record) != _HEADER_FIELDS:
            raise DataContractError("first journal entry must be a complete header")
        if record.get("schema_version") != SCHEMA_VERSION:
            raise DataContractError("unsupported journal schema_version")
        if not isinstance(record.get("adapter_version"), str) or not record["adapter_version"].strip():
            raise DataContractError("journal adapter_version is required")
        if not isinstance(record.get("source"), dict) or not isinstance(record.get("instrument"), dict):
            raise DataContractError("journal source and instrument must be objects")
        origin = record.get("origin")
        if origin not in {"synthetic", "live", "replay"}:
            raise DataContractError("journal origin is invalid")
        permission_ref = record.get("permission_ref")
        if origin == "live" and (
            not isinstance(permission_ref, str)
            or not permission_ref.strip()
            or not isinstance(self._policy.permission_ref, str)
            or not self._policy.permission_ref.strip()
            or permission_ref != self._policy.permission_ref
        ):
            raise DataContractError("live retention requires a matching policy permission_ref")
        if permission_ref is not None and (
            not isinstance(permission_ref, str) or not permission_ref.strip()
        ):
            raise DataContractError("permission_ref must be non-empty text")
        created_at_ms = record.get("created_at_ms")
        if isinstance(created_at_ms, bool) or not isinstance(created_at_ms, int) or created_at_ms < 0:
            raise DataContractError("created_at_ms must be a non-negative integer")
        line = self._json_line(record)
        if len(line) > MAX_RECORD_BYTES:
            raise DataContractError("journal header exceeds the 1 MiB message limit")
        self._ensure_empty_directory()
        if len(line) > self._policy.max_chunk_bytes or len(line) > self._policy.max_bytes:
            self._stop_at_budget("header_exceeds_disk_budget")
            return False
        self._header = dict(record)
        self._header_line = line
        if not self._create_chunk(0, line):
            return False
        self._state = "recording"
        self._reason = None
        return True

    def _append_record(self, record: dict) -> bool:
        allowed = {"record_kind", "payload", "record_index", "payload_sha256"}
        if set(record) - allowed or "record_kind" not in record or "payload" not in record:
            raise DataContractError("journal record must contain record_kind and payload only")
        kind = record.get("record_kind")
        if not isinstance(kind, str) or not kind.strip():
            raise DataContractError("record_kind must be non-empty text")
        payload = record["payload"]
        digest = canonical_payload_sha256(payload)
        expected_index = self._records_written
        if "record_index" in record and record["record_index"] != expected_index:
            raise DataContractError("record_index is not the next journal index")
        if "payload_sha256" in record and record["payload_sha256"] != digest:
            raise DataContractError("payload_sha256 does not match the canonical payload")
        encoded = self._json_line({
            "record_index": expected_index,
            "record_kind": kind,
            "payload": payload,
            "payload_sha256": digest,
        })
        if len(encoded) > MAX_RECORD_BYTES:
            raise DataContractError("journal record exceeds the 1 MiB message limit")
        assert self._header_line is not None
        needs_new_chunk = self._chunk_bytes + len(encoded) > self._policy.max_chunk_bytes
        next_chunk_index = len(self._chunks) if needs_new_chunk else len(self._chunks) - 1
        repeated_header_bytes = len(self._header_line) if needs_new_chunk else 0
        if needs_new_chunk and repeated_header_bytes + len(encoded) > self._policy.max_chunk_bytes:
            self._stop_at_budget("record_exceeds_chunk_budget")
            return False
        if self._bytes_written + repeated_header_bytes + len(encoded) > self._policy.max_bytes:
            self._stop_at_budget("max_bytes")
            return False
        if needs_new_chunk:
            if not self._create_chunk(next_chunk_index, self._header_line):
                return False
        if self._handle is None:
            raise DataContractError("journal has no open chunk")
        try:
            self._handle.write(encoded)
            self._handle.flush()
        except OSError:
            self._state = "invalid"
            self._reason = "disk_write_failed"
            raise DataContractError("journal disk write failed") from None
        self._bytes_written += len(encoded)
        self._chunk_bytes += len(encoded)
        self._records_written += 1
        return True

    @staticmethod
    def _json_line(value: dict) -> bytes:
        try:
            return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
        except (TypeError, ValueError, UnicodeError):
            raise DataContractError("journal entry is not finite JSON data") from None

    def _ensure_empty_directory(self) -> None:
        assert self._path is not None
        try:
            if next(self._path.parent.iterdir(), None) is not None:
                raise DataContractError("journal directory must be exclusive and empty")
        except OSError:
            raise DataContractError("journal directory could not be inspected") from None

    def _chunk_path(self, index: int) -> Path:
        assert self._path is not None
        if index == 0:
            return self._path
        suffix = self._path.suffix or ".jsonl"
        stem = self._path.name[:-len(self._path.suffix)] if self._path.suffix else self._path.name
        return self._path.with_name(f"{stem}.{index:04d}{suffix}")

    def _create_chunk(self, index: int, header_line: bytes) -> bool:
        path = self._chunk_path(index)
        try:
            handle = path.open("xb")
            handle.write(header_line)
            handle.flush()
        except FileExistsError:
            self._state = "invalid"
            self._reason = "chunk_path_exists"
            raise DataContractError("journal chunk path already exists") from None
        except OSError:
            self._state = "invalid"
            self._reason = "disk_write_failed"
            raise DataContractError("journal chunk could not be created") from None
        if self._handle is not None:
            self._handle.close()
        self._handle = handle
        self._chunks.append(path)
        self._chunk_bytes = len(header_line)
        self._bytes_written += len(header_line)
        return True

    def _stop_at_budget(self, reason: str) -> None:
        self._state = "budget_reached"
        self._reason = reason
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None
        self._closed = True
        if self._state not in {"disabled", "budget_reached", "invalid"}:
            self._state = "closed"

    def status(self) -> dict:
        return {
            "state": self._state,
            "recording": self._state == "recording" and self._handle is not None,
            "bytes_written": self._bytes_written,
            "records_written": self._records_written,
            "chunks": len(self._chunks),
            "chunk_bytes": self._chunk_bytes,
            "max_bytes": self._policy.max_bytes,
            "max_chunk_bytes": self._policy.max_chunk_bytes,
            "max_age_seconds": self._policy.max_age_seconds,
            "reason": self._reason,
        }


class ReplaySession:
    """Validating, order-preserving reader for a journal stream."""

    def __init__(self, records: str | Path | Iterable[dict], *, verify_hashes: bool = True) -> None:
        self._records = records
        self._verify_hashes = verify_hashes
        self._state = "not_started"
        self._valid: bool | None = None
        self._gaps = 0
        self._records_read = 0
        self._bytes_read = 0
        self._reason: str | None = None
        self._consumed = False

    def events(self) -> Iterator[dict]:
        if self._consumed:
            raise DataContractError("replay stream is single-use")
        self._consumed = True
        return self._iterate()

    def _iterate(self) -> Iterator[dict]:
        self._state = "replaying"
        header: dict | None = None
        expected_index = 0
        try:
            for row, chunk_header in self._raw_rows():
                if chunk_header:
                    if header is None:
                        self._validate_header(row)
                        header = row
                        continue
                    if row != header:
                        raise DataContractError("journal chunk header does not match the first header")
                    continue
                if header is None:
                    self._validate_header(row)
                    header = row
                    continue
                record = self._validate_record(row, expected_index)
                expected_index += 1
                self._records_read += 1
                if record["record_kind"] == "gap":
                    self._gaps += 1
                yield record
            if header is None:
                raise DataContractError("journal is missing its header")
            self._valid = self._gaps == 0
            self._state = "degraded" if self._gaps else "complete"
            self._reason = "gap_records_present" if self._gaps else None
        except DataContractError as exc:
            self._valid = False
            self._state = "invalid"
            self._reason = str(exc)
            raise
        except OSError:
            self._valid = False
            self._state = "invalid"
            self._reason = "journal_read_failed"
            raise DataContractError("journal could not be read") from None

    def _raw_rows(self) -> Iterator[tuple[dict, bool]]:
        source = self._records
        if isinstance(source, (str, Path)):
            base = Path(source)
            paths = [base]
            suffix = base.suffix or ".jsonl"
            stem = base.name[:-len(base.suffix)] if base.suffix else base.name
            index = 1
            while True:
                next_path = base.with_name(f"{stem}.{index:04d}{suffix}")
                if not next_path.exists():
                    break
                paths.append(next_path)
                index += 1
            total = 0
            for path in paths:
                if not path.is_file():
                    raise DataContractError("journal path is not a regular file")
                with path.open("rb") as handle:
                    first_line = True
                    while True:
                        raw = handle.readline(MAX_RECORD_BYTES + 1)
                        if not raw:
                            break
                        total += len(raw)
                        self._bytes_read += len(raw)
                        if len(raw) > MAX_RECORD_BYTES:
                            raise DataContractError("journal line exceeds the 1 MiB message limit")
                        if total > MAX_MANAGED_BYTES:
                            raise DataContractError("journal exceeds the 32 MiB replay budget")
                        try:
                            row = json.loads(
                                raw.decode("utf-8"),
                                parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("non-finite JSON")),
                            )
                        except (UnicodeError, ValueError, json.JSONDecodeError):
                            raise DataContractError("journal contains invalid JSON") from None
                        if not isinstance(row, dict):
                            raise DataContractError("journal line must be an object")
                        yield row, first_line
                        first_line = False
            return
        if isinstance(source, dict):
            raise DataContractError("replay records must be a path or an iterable of objects")
        try:
            iterator = iter(source)
        except TypeError:
            raise DataContractError("replay records must be a path or an iterable of objects") from None
        total = 0
        for row in iterator:
            if not isinstance(row, dict):
                raise DataContractError("journal entry must be an object")
            encoded = JournalWriter._json_line(row)
            total += len(encoded)
            self._bytes_read += len(encoded)
            if len(encoded) > MAX_RECORD_BYTES:
                raise DataContractError("journal line exceeds the 1 MiB message limit")
            if total > MAX_MANAGED_BYTES:
                raise DataContractError("journal exceeds the 32 MiB replay budget")
            yield row, False

    @staticmethod
    def _validate_header(header: dict) -> None:
        if set(header) != _HEADER_FIELDS:
            raise DataContractError("journal header is missing or has unknown fields")
        if header.get("schema_version") != SCHEMA_VERSION:
            raise DataContractError("unsupported journal schema_version")
        if not isinstance(header.get("adapter_version"), str) or not header["adapter_version"].strip():
            raise DataContractError("journal adapter_version is required")
        if not isinstance(header.get("source"), dict) or not isinstance(header.get("instrument"), dict):
            raise DataContractError("journal source and instrument must be objects")
        if header.get("origin") not in {"synthetic", "live", "replay"}:
            raise DataContractError("journal origin is invalid")
        permission_ref = header.get("permission_ref")
        if header["origin"] == "live" and (not isinstance(permission_ref, str) or not permission_ref.strip()):
            raise DataContractError("live replay is missing a permission_ref")
        if permission_ref is not None and (
            not isinstance(permission_ref, str) or not permission_ref.strip()
        ):
            raise DataContractError("permission_ref must be non-empty text")
        created_at_ms = header.get("created_at_ms")
        if isinstance(created_at_ms, bool) or not isinstance(created_at_ms, int) or created_at_ms < 0:
            raise DataContractError("created_at_ms must be a non-negative integer")

    def _validate_record(self, row: dict, expected_index: int) -> dict:
        required = {"record_index", "record_kind", "payload", "payload_sha256"}
        if set(row) != required:
            raise DataContractError("journal record is missing or has unknown fields")
        index = row.get("record_index")
        if isinstance(index, bool) or not isinstance(index, int) or index != expected_index:
            raise DataContractError("journal record_index is missing or out of order")
        kind = row.get("record_kind")
        if not isinstance(kind, str) or not kind.strip():
            raise DataContractError("record_kind must be non-empty text")
        digest = row.get("payload_sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise DataContractError("payload_sha256 must be a SHA-256 hex digest")
        if self._verify_hashes and canonical_payload_sha256(row["payload"]) != digest:
            raise DataContractError("journal payload hash mismatch")
        return row

    def status(self) -> dict:
        return {
            "state": self._state,
            "valid": self._valid,
            "gaps": self._gaps,
            "records_read": self._records_read,
            "bytes_read": self._bytes_read,
            "reason": self._reason,
            "missing": ["journal_gap"] if self._gaps else [],
        }


class VolumeAtPrice:
    """Exact-decimal volume-at-price accumulator for individual trades."""

    def __init__(self, instrument: InstrumentSpec, *, max_trades: int = 20000, max_levels: int = 5000) -> None:
        if not isinstance(instrument, InstrumentSpec):
            raise DataContractError("VAP requires an InstrumentSpec")
        if isinstance(max_trades, bool) or not isinstance(max_trades, int) or not 1 <= max_trades <= 20000:
            raise DataContractError("max_trades must be between 1 and 20000")
        if isinstance(max_levels, bool) or not isinstance(max_levels, int) or not 1 <= max_levels <= 5000:
            raise DataContractError("max_levels must be between 1 and 5000")
        self._instrument = instrument
        self._max_trades = max_trades
        self._max_levels = max_levels
        self._trades: OrderedDict[tuple[str, str, str], dict] = OrderedDict()
        self._levels: dict[Decimal, dict] = {}
        self._duplicates = 0
        self._conflicts = 0
        self._evictions = 0
        self._resource_rejections = 0
        self._invalid = False

    def accept(self, trade: TradeEvent) -> bool:
        if self._invalid:
            raise DataContractError("VAP was invalidated by a conflicting duplicate")
        if not isinstance(trade, TradeEvent):
            raise DataContractError("VAP accepts TradeEvent instances")
        if trade.instrument_id != self._instrument.instrument_id:
            raise DataContractError("trade instrument does not match VAP instrument")
        price = decimal_value(trade.price)
        quantity = decimal_value(trade.quantity)
        event = trade.envelope
        key = (event.venue, trade.instrument_id, trade.trade_id)
        candidate = {
            "price": price,
            "quantity": quantity,
            "trade_time_ms": trade.trade_time_ms,
            "aggressor": trade.aggressor,
            "origin": event.origin,
        }
        previous = self._trades.get(key)
        if previous is not None:
            semantic_fields = ("price", "quantity", "trade_time_ms", "aggressor")
            if all(previous[field] == candidate[field] for field in semantic_fields):
                self._duplicates += 1
                self._trades.move_to_end(key)
                return False
            self._conflicts += 1
            self._invalid = True
            raise DataContractError("conflicting duplicate trade invalidated VAP")
        if event.origin not in {"live", "synthetic", "replay"}:
            raise DataContractError("trade origin is invalid")
        # Preflight bounded exact arithmetic before any eviction or mutation.
        # The lexical contract permits exponent notation, so reject a result
        # whose exact fixed-point representation would exceed our resource cap.
        try:
            _validate_decimal_output(price)
            _validate_decimal_output(quantity)
            product = _decimal_multiply(price, quantity)
            current = self._levels.get(price)
            _decimal_add(current["quantity"] if current else Decimal(0), quantity)
            _decimal_add(current["notional"] if current else Decimal(0), product)
        except DataContractError:
            self._resource_rejections += 1
            raise
        if len(self._trades) >= self._max_trades:
            self._evict_oldest()
        if price not in self._levels:
            while len(self._levels) >= self._max_levels:
                self._evict_oldest()
        self._trades[key] = candidate
        level = self._levels.setdefault(price, {
            "quantity": Decimal(0),
            "notional": Decimal(0),
            "trade_count": 0,
            "aggressor_counts": {"buy": 0, "sell": 0, "unknown": 0},
        })
        level["quantity"] = _decimal_add(level["quantity"], quantity)
        level["notional"] = _decimal_add(level["notional"], product)
        level["trade_count"] += 1
        level["aggressor_counts"][trade.aggressor] += 1
        return True

    def _evict_oldest(self) -> None:
        key, record = self._trades.popitem(last=False)
        price = record["price"]
        level = self._levels[price]
        level["quantity"] = _decimal_subtract(level["quantity"], record["quantity"])
        level["notional"] = _decimal_subtract(
            level["notional"], _decimal_multiply(price, record["quantity"])
        )
        level["trade_count"] -= 1
        level["aggressor_counts"][record["aggressor"]] -= 1
        if level["trade_count"] == 0:
            del self._levels[price]
        self._evictions += 1

    def snapshot(self, *, start_ms: int, end_ms: int) -> dict:
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (start_ms, end_ms)):
            raise DataContractError("snapshot bounds must be non-negative integer milliseconds")
        if end_ms <= start_ms:
            raise DataContractError("snapshot end_ms must be after start_ms")
        if end_ms - start_ms > 300_000:
            raise DataContractError("snapshot window must not exceed 300 seconds")
        totals: dict[Decimal, dict] = {}
        evidence_refs: list[str] = []
        origins: set[str] = set()
        venues: set[str] = set()
        for key, record in self._trades.items():
            timestamp = record["trade_time_ms"]
            if not start_ms <= timestamp < end_ms:
                continue
            price = record["price"]
            level = totals.setdefault(price, {
                "quantity": Decimal(0),
                "notional": Decimal(0),
                "trade_count": 0,
                "aggressor_counts": {"buy": 0, "sell": 0, "unknown": 0},
            })
            level["quantity"] = _decimal_add(level["quantity"], record["quantity"])
            level["notional"] = _decimal_add(
                level["notional"], _decimal_multiply(price, record["quantity"])
            )
            level["trade_count"] += 1
            level["aggressor_counts"][record["aggressor"]] += 1
            origins.add(record["origin"])
            venues.add(key[0])
            if len(evidence_refs) < 200:
                evidence_refs.append(f"{key[0]}:{key[2]}")
        ordered_prices = sorted(totals)
        quantity_total = Decimal(0)
        notional_total = Decimal(0)
        for price in ordered_prices:
            quantity_total = _decimal_add(quantity_total, totals[price]["quantity"])
            notional_total = _decimal_add(notional_total, totals[price]["notional"])
        trade_count = sum(totals[price]["trade_count"] for price in ordered_prices)
        missing: list[str] = []
        if trade_count == 0:
            missing.append("no_trades_in_interval")
        if self._evictions:
            missing.append("evictions")
        if self._conflicts:
            missing.append("conflicting_duplicate")
        if self._resource_rejections:
            missing.append("decimal_resource_budget")
        if "live" in origins or "replay" in origins:
            missing.append("live_partial_tape" if "live" in origins else "replay_provenance_partial")
        if self._conflicts:
            coverage = "invalid"
        elif not missing:
            coverage = "bounded_complete"
        else:
            coverage = "partial"
        levels = [{
            "price": _decimal_string(price),
            "quantity": _decimal_string(totals[price]["quantity"]),
            "notional": _decimal_string(totals[price]["notional"]),
            "trade_count": totals[price]["trade_count"],
            "aggressor_counts": dict(totals[price]["aggressor_counts"]),
        } for price in ordered_prices]
        unit = self._instrument.base_asset or (
            "contracts" if self._instrument.kind in {"future", "linear_future"}
            else self._instrument.settlement_currency
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "instrument_id": self._instrument.instrument_id,
            "venue": next(iter(venues)) if len(venues) == 1 else None,
            "venues": sorted(venues),
            "start_ms": start_ms,
            "end_ms": end_ms,
            "unit": unit,
            "levels": levels,
            "total_quantity": _decimal_string(quantity_total),
            "total_notional": _decimal_string(notional_total),
            "trade_count": trade_count,
            "coverage": coverage,
            "full_tape": False,
            "duplicates": self._duplicates,
            "conflicts": self._conflicts,
            "evictions": self._evictions,
            "resource_rejections": self._resource_rejections,
            "missing": missing,
            "evidence_refs": evidence_refs,
        }

    def status(self) -> dict:
        return {
            "state": "invalid" if self._invalid else (
                "partial" if self._evictions or self._resource_rejections else "ready"
            ),
            "valid": not self._invalid,
            "trade_count": len(self._trades),
            "level_count": len(self._levels),
            "duplicates": self._duplicates,
            "conflicts": self._conflicts,
            "evictions": self._evictions,
            "resource_rejections": self._resource_rejections,
            "coverage": "invalid" if self._invalid else (
                "partial" if self._evictions or self._resource_rejections else "bounded"
            ),
            "missing": ["decimal_resource_budget"] if self._resource_rejections else [],
        }


def _decimal_string(value: Decimal) -> str:
    if value == 0:
        return "0"
    _validate_decimal_output(value)
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _decimal_add(left: Decimal, right: Decimal) -> Decimal:
    return _decimal_operation(left, right, _addition_precision(left, right), lambda: left + right)


def _decimal_subtract(left: Decimal, right: Decimal) -> Decimal:
    return _decimal_operation(left, right, _addition_precision(left, right), lambda: left - right)


def _decimal_multiply(left: Decimal, right: Decimal) -> Decimal:
    precision = len(left.as_tuple().digits) + len(right.as_tuple().digits)
    if precision > _MAX_EXACT_DECIMAL_DIGITS:
        raise DataContractError("exact decimal arithmetic exceeds the VAP resource budget")
    return _decimal_operation(left, right, precision, lambda: left * right)


def _addition_precision(left: Decimal, right: Decimal) -> int:
    if left == 0:
        return max(1, len(right.as_tuple().digits))
    if right == 0:
        return max(1, len(left.as_tuple().digits))
    high_exponent = max(left.adjusted(), right.adjusted())
    low_exponent = min(left.as_tuple().exponent, right.as_tuple().exponent)
    precision = high_exponent - low_exponent + 1
    if precision > _MAX_EXACT_DECIMAL_DIGITS:
        raise DataContractError("exact decimal arithmetic exceeds the VAP resource budget")
    return max(1, precision)


def _decimal_operation(left: Decimal, right: Decimal, precision: int, operation) -> Decimal:
    with localcontext() as context:
        context.prec = precision
        context.Emax = MAX_EMAX
        context.Emin = MIN_EMIN
        try:
            result = operation()
        except DecimalException:
            raise DataContractError("exact decimal arithmetic is outside the VAP resource budget") from None
    if result.is_finite() and _decimal_expanded_length(result) <= _MAX_EXACT_DECIMAL_DIGITS:
        return result
    raise DataContractError("exact decimal arithmetic exceeds the VAP resource budget")


def _decimal_expanded_length(value: Decimal) -> int:
    """Return the fixed-point string length without expanding large exponents."""
    sign, digits, exponent = value.as_tuple()
    digit_count = len(digits)
    if exponent >= 0:
        length = digit_count + exponent
    elif digit_count > -exponent:
        length = digit_count + 1  # decimal point
    else:
        length = 2 - exponent  # ``0.`` plus leading fractional zeroes
    return length + int(bool(sign))


def _validate_decimal_output(value: Decimal) -> None:
    if _decimal_expanded_length(value) > _MAX_EXACT_DECIMAL_DIGITS:
        raise DataContractError("exact decimal output exceeds the VAP resource budget")

from __future__ import annotations

import json
import sqlite3
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from .contracts import SystemClock


_ACCOUNT_TTL_MS = 60_000
_ACCOUNT_MODES = {"manual", "imported", "read_only"}
_ACCOUNT_STATUSES = {"reconciled", "stale", "conflicted"}


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_required")
    return value.strip()


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field}_must_be_nonnegative_integer")
    return value


def _decimal(value: Any, field: str) -> Decimal:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{field}_must_be_decimal_string")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field}_invalid_decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{field}_must_be_finite")
    return result


def _decimal_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    result = format(value, "f")
    return result.rstrip("0").rstrip(".") if "." in result else result


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class AccountLedger:
    """SQLite-backed manual/imported/read-only account snapshots and fill log."""

    def __init__(self, path: str | Path, *, clock: Any = None) -> None:
        self.path = Path(path) if str(path) != ":memory:" else ":memory:"
        if isinstance(self.path, Path):
            self.path.parent.mkdir(parents=True, exist_ok=True)
            db_path = str(self.path)
        else:
            db_path = self.path
        self.clock = clock or SystemClock()
        self._closed = False
        self._db = sqlite3.connect(db_path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("PRAGMA busy_timeout=5000")
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                revision INTEGER NOT NULL,
                snapshot_revision INTEGER NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                asof_ms INTEGER NOT NULL,
                received_monotonic_ns INTEGER NOT NULL,
                balances_json TEXT NOT NULL,
                positions_json TEXT NOT NULL,
                content_json TEXT NOT NULL,
                reason TEXT
            );
            CREATE TABLE IF NOT EXISTS fills (
                account_id TEXT NOT NULL,
                fill_id TEXT NOT NULL,
                revision INTEGER NOT NULL,
                instrument_id TEXT NOT NULL,
                quantity TEXT NOT NULL,
                price TEXT NOT NULL,
                side TEXT NOT NULL,
                currency TEXT NOT NULL,
                occurred_at_ms INTEGER NOT NULL,
                received_monotonic_ns INTEGER NOT NULL,
                content_json TEXT NOT NULL,
                disposition TEXT NOT NULL,
                reason TEXT,
                PRIMARY KEY (account_id, fill_id),
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            );
            CREATE INDEX IF NOT EXISTS fills_by_revision ON fills(account_id, revision);
            """
        )

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("account_ledger_closed")

    @staticmethod
    def _normalize_balances(value: Any) -> dict[str, str]:
        if not isinstance(value, Mapping):
            raise TypeError("balances_must_be_object")
        result: dict[str, str] = {}
        for raw_currency, raw_amount in value.items():
            currency = _required_text(raw_currency, "currency").upper()
            if currency in result:
                raise ValueError("duplicate_currency")
            result[currency] = _decimal_text(_decimal(raw_amount, f"balance_{currency}"))
        return result

    @staticmethod
    def _normalize_positions(value: Any) -> dict[str, dict[str, str | None]]:
        if not isinstance(value, Mapping):
            raise TypeError("positions_must_be_object")
        result: dict[str, dict[str, str | None]] = {}
        for raw_instrument_id, raw_position in value.items():
            instrument_id = _required_text(raw_instrument_id, "instrument_id")
            if instrument_id in result:
                raise ValueError("duplicate_instrument_position")
            if isinstance(raw_position, str):
                quantity_raw, average_raw = raw_position, None
            elif isinstance(raw_position, Mapping):
                extra = set(raw_position) - {"quantity", "average_price"}
                if extra or "quantity" not in raw_position:
                    raise ValueError("position_keys_invalid")
                quantity_raw = raw_position["quantity"]
                average_raw = raw_position.get("average_price")
            else:
                raise TypeError("position_must_be_decimal_string_or_object")
            quantity = _decimal_text(_decimal(quantity_raw, "position_quantity"))
            average = None if average_raw is None else _decimal_text(_decimal(average_raw, "position_average_price"))
            result[instrument_id] = {"quantity": quantity, "average_price": average}
        return result

    def _normalize_snapshot(self, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(snapshot, Mapping):
            raise TypeError("account_snapshot_must_be_object")
        account_id = _required_text(snapshot.get("account_id"), "account_id")
        revision = _integer(snapshot.get("revision"), "revision")
        mode = _required_text(snapshot.get("mode"), "mode")
        status = _required_text(snapshot.get("status"), "status")
        if mode not in _ACCOUNT_MODES:
            raise ValueError("invalid_account_mode")
        if status not in _ACCOUNT_STATUSES:
            raise ValueError("invalid_account_status")
        asof_ms = _integer(snapshot.get("asof_ms"), "asof_ms")
        received_ns = _integer(snapshot.get("received_monotonic_ns"), "received_monotonic_ns")
        if received_ns > self.clock.monotonic_ns():
            raise ValueError("receive_clock_in_future")
        balances = self._normalize_balances(snapshot.get("balances"))
        positions = self._normalize_positions(snapshot.get("positions"))
        content = {"account_id": account_id, "revision": revision, "mode": mode, "balances": balances, "positions": positions}
        return {
            **content,
            "status": status,
            "asof_ms": asof_ms,
            "received_monotonic_ns": received_ns,
            "balances_json": _json(balances),
            "positions_json": _json(positions),
            "content_json": _json(content),
        }

    @staticmethod
    def _result(status: str, account_id: str, revision: int | None, reason: str | None, *, applied: bool = False, duplicate: bool = False) -> dict[str, Any]:
        return {
            "status": status,
            "account_id": account_id,
            "revision": revision,
            "reason": reason,
            "applied": applied,
            "duplicate": duplicate,
        }

    def reconcile(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        self._ensure_open()
        normalized = self._normalize_snapshot(snapshot)
        account_id = normalized["account_id"]
        current = self._db.execute("SELECT * FROM accounts WHERE account_id=?", (account_id,)).fetchone()
        if current is None:
            reason = "source_marked_stale" if normalized["status"] == "stale" else "source_marked_conflicted" if normalized["status"] == "conflicted" else None
            with self._db:
                self._db.execute(
                    "INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (account_id, normalized["revision"], normalized["revision"], normalized["mode"], normalized["status"], normalized["asof_ms"], normalized["received_monotonic_ns"], normalized["balances_json"], normalized["positions_json"], normalized["content_json"], reason),
                )
            return self._result(normalized["status"], account_id, normalized["revision"], reason, applied=True)

        current_revision = current["revision"]
        if normalized["revision"] < current_revision:
            with self._db:
                self._db.execute("UPDATE accounts SET status='stale', reason='out_of_order_snapshot' WHERE account_id=?", (account_id,))
            return self._result("stale", account_id, current_revision, "out_of_order_snapshot")

        current_snapshot_revision = current["snapshot_revision"]
        if normalized["revision"] == current_revision:
            covers_new_fills = current_revision > current_snapshot_revision
            if normalized["content_json"] != current["content_json"] and not covers_new_fills:
                with self._db:
                    self._db.execute("UPDATE accounts SET status='conflicted', reason='revision_conflict' WHERE account_id=?", (account_id,))
                return self._result("conflicted", account_id, current_revision, "revision_conflict")
            if normalized["received_monotonic_ns"] < current["received_monotonic_ns"]:
                with self._db:
                    self._db.execute("UPDATE accounts SET status='stale', reason='out_of_order_snapshot' WHERE account_id=?", (account_id,))
                return self._result("stale", account_id, current_revision, "out_of_order_snapshot")
            if normalized["content_json"] == current["content_json"] and normalized["asof_ms"] == current["asof_ms"] and normalized["status"] == current["status"]:
                return self._result("duplicate", account_id, current_revision, current["reason"], duplicate=True)

        reason = "source_marked_stale" if normalized["status"] == "stale" else "source_marked_conflicted" if normalized["status"] == "conflicted" else None
        with self._db:
            self._db.execute(
                "UPDATE accounts SET revision=?, snapshot_revision=?, mode=?, status=?, asof_ms=?, received_monotonic_ns=?, balances_json=?, positions_json=?, content_json=?, reason=? WHERE account_id=?",
                (normalized["revision"], normalized["revision"], normalized["mode"], normalized["status"], normalized["asof_ms"], normalized["received_monotonic_ns"], normalized["balances_json"], normalized["positions_json"], normalized["content_json"], reason, account_id),
            )
        return self._result(normalized["status"], account_id, normalized["revision"], reason, applied=True)

    def _normalize_fill(self, fill: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(fill, Mapping):
            raise TypeError("fill_must_be_object")
        account_id = _required_text(fill.get("account_id"), "account_id")
        fill_id = _required_text(fill.get("fill_id"), "fill_id")
        revision = _integer(fill.get("revision"), "revision")
        instrument_id = _required_text(fill.get("instrument_id"), "instrument_id")
        quantity = _decimal(_required_text(fill.get("quantity"), "quantity"), "quantity")
        price = _decimal(_required_text(fill.get("price"), "price"), "price")
        if quantity <= 0 or price <= 0:
            raise ValueError("fill_quantity_and_price_must_be_positive")
        side = _required_text(fill.get("side"), "side").casefold()
        if side not in {"buy", "sell"}:
            raise ValueError("invalid_fill_side")
        currency = _required_text(fill.get("currency"), "currency").upper()
        occurred_at_ms = _integer(fill.get("occurred_at_ms"), "occurred_at_ms")
        received_ns = _integer(fill.get("received_monotonic_ns"), "received_monotonic_ns")
        if received_ns > self.clock.monotonic_ns():
            raise ValueError("receive_clock_in_future")
        normalized = {
            "account_id": account_id,
            "fill_id": fill_id,
            "revision": revision,
            "instrument_id": instrument_id,
            "quantity": _decimal_text(quantity),
            "price": _decimal_text(price),
            "side": side,
            "currency": currency,
            "occurred_at_ms": occurred_at_ms,
            "received_monotonic_ns": received_ns,
        }
        normalized["content_json"] = _json(normalized)
        return normalized

    def ingest_fill(self, fill: dict[str, Any]) -> dict[str, Any]:
        self._ensure_open()
        normalized = self._normalize_fill(fill)
        account_id = normalized["account_id"]
        fill_id = normalized["fill_id"]
        current_fill = self._db.execute("SELECT * FROM fills WHERE account_id=? AND fill_id=?", (account_id, fill_id)).fetchone()
        if current_fill is not None:
            if current_fill["content_json"] == normalized["content_json"]:
                return self._result("duplicate", account_id, current_fill["revision"], current_fill["reason"] or "duplicate_fill", duplicate=True)
            with self._db:
                self._db.execute("UPDATE accounts SET status='conflicted', reason='fill_identity_conflict' WHERE account_id=?", (account_id,))
            return self._result("conflicted", account_id, current_fill["revision"], "fill_identity_conflict")

        account = self._db.execute("SELECT * FROM accounts WHERE account_id=?", (account_id,)).fetchone()
        if account is None:
            return self._result("rejected", account_id, None, "account_not_reconciled")
        if account["status"] == "conflicted":
            return self._result("conflicted", account_id, account["revision"], account["reason"] or "account_conflicted")
        age_ms = max(0, (self.clock.monotonic_ns() - account["received_monotonic_ns"]) // 1_000_000)
        if age_ms > _ACCOUNT_TTL_MS:
            with self._db:
                self._db.execute("UPDATE accounts SET status='stale', reason='account_snapshot_expired' WHERE account_id=?", (account_id,))
            return self._result("stale", account_id, account["revision"], "account_snapshot_expired")
        if account["status"] == "stale" and account["reason"] != "fill_requires_reconciliation":
            return self._result("stale", account_id, account["revision"], account["reason"] or "account_not_reconciled")
        if normalized["received_monotonic_ns"] < account["received_monotonic_ns"]:
            with self._db:
                self._db.execute("UPDATE accounts SET status='stale', reason='out_of_order_fill' WHERE account_id=?", (account_id,))
            return self._result("stale", account_id, account["revision"], "out_of_order_fill")
        if normalized["revision"] <= account["revision"]:
            if normalized["revision"] < account["revision"]:
                reason, status = "out_of_order_fill", "stale"
            else:
                reason, status = "fill_revision_conflict", "conflicted"
            with self._db:
                self._db.execute("UPDATE accounts SET status=?, reason=? WHERE account_id=?", (status, reason, account_id))
            return self._result(status, account_id, account["revision"], reason)

        with self._db:
            self._db.execute(
                "INSERT INTO fills VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (account_id, fill_id, normalized["revision"], normalized["instrument_id"], normalized["quantity"], normalized["price"], normalized["side"], normalized["currency"], normalized["occurred_at_ms"], normalized["received_monotonic_ns"], normalized["content_json"], "applied", None),
            )
            self._db.execute(
                "UPDATE accounts SET revision=?, status='stale', reason='fill_requires_reconciliation' WHERE account_id=?",
                (normalized["revision"], account_id),
            )
        return self._result("stale", account_id, normalized["revision"], "fill_requires_reconciliation", applied=True)

    @staticmethod
    def _apply_fill(position: dict[str, str | None] | None, fill: sqlite3.Row) -> dict[str, str | None] | None:
        quantity = Decimal(position["quantity"]) if position is not None else Decimal(0)
        average = Decimal(position["average_price"]) if position is not None and position["average_price"] is not None else None
        fill_quantity = Decimal(fill["quantity"])
        signed = fill_quantity if fill["side"] == "buy" else -fill_quantity
        price = Decimal(fill["price"])
        updated = quantity + signed
        if updated == 0:
            return None
        if quantity == 0 or (quantity > 0) != (updated > 0):
            average = price
        elif (quantity > 0) == (signed > 0):
            average = (abs(quantity) * average + abs(signed) * price) / abs(updated) if average is not None else None
        return {"quantity": _decimal_text(updated), "average_price": _decimal_text(average) if average is not None else None}

    def _effective_positions(self, account: sqlite3.Row) -> dict[str, dict[str, str | None]]:
        positions = json.loads(account["positions_json"])
        rows = self._db.execute(
            "SELECT * FROM fills WHERE account_id=? AND disposition='applied' AND revision>? ORDER BY revision, fill_id",
            (account["account_id"], account["snapshot_revision"]),
        )
        for fill in rows:
            updated = self._apply_fill(positions.get(fill["instrument_id"]), fill)
            if updated is None:
                positions.pop(fill["instrument_id"], None)
            else:
                positions[fill["instrument_id"]] = updated
        return positions

    def view(self, account_id: str) -> dict[str, Any]:
        self._ensure_open()
        account_id = _required_text(account_id, "account_id")
        account = self._db.execute("SELECT * FROM accounts WHERE account_id=?", (account_id,)).fetchone()
        if account is None:
            return {
                "account_id": account_id,
                "revision": None,
                "mode": None,
                "status": "unavailable",
                "asof_ms": None,
                "received_monotonic_ns": None,
                "balances": {},
                "positions": {},
                "age_ms": None,
                "reason": "account_missing",
            }
        now_ns = self.clock.monotonic_ns()
        clock_reset = now_ns < account["received_monotonic_ns"]
        age_ms = None if clock_reset else (now_ns - account["received_monotonic_ns"]) // 1_000_000
        status, reason = account["status"], account["reason"]
        if status == "reconciled" and clock_reset:
            status, reason = "stale", "monotonic_clock_reset"
            with self._db:
                self._db.execute("UPDATE accounts SET status=?, reason=? WHERE account_id=?", (status, reason, account_id))
        elif status == "reconciled" and age_ms > _ACCOUNT_TTL_MS:
            status, reason = "stale", "account_snapshot_expired"
            with self._db:
                self._db.execute("UPDATE accounts SET status=?, reason=? WHERE account_id=?", (status, reason, account_id))
        return {
            "account_id": account_id,
            "revision": account["revision"],
            "mode": account["mode"],
            "status": status,
            "asof_ms": account["asof_ms"],
            "received_monotonic_ns": account["received_monotonic_ns"],
            "balances": json.loads(account["balances_json"]),
            "positions": self._effective_positions(account),
            "age_ms": age_ms,
            "reason": reason,
        }

    def close(self) -> None:
        if not self._closed:
            self._db.close()
            self._closed = True

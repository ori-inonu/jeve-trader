"""Policy-gated, idempotent local journal for multimarket event replay."""

from __future__ import annotations

import json
import re
import sqlite3
import threading
import time
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any


_POLICY_VALUES = {"allowed", "denied", "unknown"}
_SAFE_DIAGNOSTIC_FIELDS = {
    "code", "status", "reason", "count", "events", "duplicates", "rejected", "overflow"
}
_SAFE_TOKEN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class Journal:
    """SQLite event journal that requires explicit retention permission.

    With unknown or denied retention, only tightly filtered counters and
    categorical diagnostics can be persisted. Market payloads are discarded.
    """

    def __init__(self, path: str | Path):
        self._path = str(path)
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._closed = False
        self._db = sqlite3.connect(
            self._path, timeout=5.0, isolation_level=None, check_same_thread=False
        )
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS journal (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                namespace TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                kind TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                policy_json TEXT NOT NULL,
                created_at_ms INTEGER NOT NULL,
                UNIQUE(namespace, idempotency_key)
            )"""
        )
        self._db.execute(
            "CREATE INDEX IF NOT EXISTS journal_namespace_sequence "
            "ON journal(namespace, sequence)"
        )

    @staticmethod
    def _policy(policy: Any) -> dict[str, str]:
        if isinstance(policy, str):
            normalized = {"retention": policy, "export": "unknown"}
        elif isinstance(policy, Mapping):
            if set(policy) != {"retention", "export"}:
                raise ValueError("Journal policy must specify retention and export.")
            normalized = dict(policy)
        else:
            raise ValueError("Journal policy must specify retention and export.")
        if any(value not in _POLICY_VALUES for value in normalized.values()):
            raise ValueError("Journal policy values must be allowed, denied, or unknown.")
        return normalized

    @staticmethod
    def _safe_diagnostic(kind: str, payload: Mapping[str, Any]) -> dict[str, Any] | None:
        if kind not in {"counter", "diagnostic"}:
            return None
        sanitized: dict[str, Any] = {}
        for key, value in payload.items():
            if key not in _SAFE_DIAGNOSTIC_FIELDS:
                continue
            if key in {"count", "events", "duplicates", "rejected", "overflow"}:
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    sanitized[key] = value
            elif isinstance(value, str) and _SAFE_TOKEN.fullmatch(value):
                sanitized[key] = value
        return sanitized

    def append(
        self,
        kind: str,
        namespace: str,
        idempotency_key: str,
        payload: dict,
        *,
        policy: Any,
    ) -> dict:
        """Append one record, or report why policy prevented persistence."""
        if not isinstance(kind, str) or not kind or len(kind) > 64:
            raise ValueError("Journal kind must be nonempty text up to 64 characters.")
        if not isinstance(namespace, str) or not namespace or len(namespace) > 256:
            raise ValueError("Journal namespace must be nonempty text up to 256 characters.")
        if not isinstance(idempotency_key, str) or not idempotency_key or len(idempotency_key) > 256:
            raise ValueError("Journal idempotency key must be nonempty text up to 256 characters.")
        if not isinstance(payload, dict):
            raise ValueError("Journal payload must be an object.")
        consent = self._policy(policy)
        stored_payload = payload
        stored_kind = kind
        if consent["retention"] != "allowed":
            stored_payload = self._safe_diagnostic(kind, payload)
            if stored_payload is None:
                return {"stored": False, "duplicate": False, "sequence": None, "reason": "retention_not_allowed"}

        try:
            payload_json = json.dumps(
                stored_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
            )
            policy_json = json.dumps(consent, sort_keys=True, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError, OverflowError, RecursionError):
            raise ValueError("Journal record must contain finite JSON values.") from None

        with self._lock:
            if self._closed:
                raise RuntimeError("Journal is closed.")
            self._db.execute("BEGIN IMMEDIATE")
            try:
                existing = self._db.execute(
                    "SELECT sequence, kind, payload_json, policy_json FROM journal "
                    "WHERE namespace = ? AND idempotency_key = ?",
                    (namespace, idempotency_key),
                ).fetchone()
                if existing is not None:
                    same = existing[1:] == (stored_kind, payload_json, policy_json)
                    self._db.execute("COMMIT")
                    if same:
                        return {"stored": True, "duplicate": True, "sequence": existing[0], "reason": "already_present"}
                    return {"stored": False, "duplicate": False, "sequence": existing[0], "reason": "idempotency_conflict"}
                cursor = self._db.execute(
                    "INSERT INTO journal(namespace, idempotency_key, kind, payload_json, policy_json, created_at_ms) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (namespace, idempotency_key, stored_kind, payload_json, policy_json, time.time_ns() // 1_000_000),
                )
                sequence = cursor.lastrowid
                self._db.execute("COMMIT")
                return {"stored": True, "duplicate": False, "sequence": sequence, "reason": "stored"}
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    def replay(self, namespace: str) -> Iterator[dict]:
        """Yield stored records in causal append order for one namespace."""
        if not isinstance(namespace, str) or not namespace:
            raise ValueError("Journal namespace must be nonempty text.")
        with self._lock:
            if self._closed:
                raise RuntimeError("Journal is closed.")
            fence = self._db.execute(
                "SELECT COALESCE(MAX(sequence), 0) FROM journal WHERE namespace = ?", (namespace,)
            ).fetchone()[0]
        after = 0
        while after < fence:
            with self._lock:
                if self._closed:
                    raise RuntimeError("Journal is closed.")
                rows = self._db.execute(
                    "SELECT sequence, idempotency_key, kind, payload_json, policy_json, created_at_ms "
                    "FROM journal WHERE namespace = ? AND sequence > ? AND sequence <= ? "
                    "ORDER BY sequence LIMIT 256",
                    (namespace, after, fence),
                ).fetchall()
            if not rows:
                return
            for sequence, key, kind, payload, policy, created_at_ms in rows:
                after = sequence
                yield {
                    "sequence": sequence,
                    "namespace": namespace,
                    "idempotency_key": key,
                    "kind": kind,
                    "payload": json.loads(payload),
                    "policy": json.loads(policy),
                    "created_at_ms": created_at_ms,
                    "mode": "replay",
                }

    def status(self) -> dict:
        with self._lock:
            if self._closed:
                return {"status": "closed", "records": 0, "namespaces": 0}
            records, namespaces = self._db.execute(
                "SELECT COUNT(*), COUNT(DISTINCT namespace) FROM journal"
            ).fetchone()
            return {"status": "ready", "records": records, "namespaces": namespaces}

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._db.close()
                self._closed = True

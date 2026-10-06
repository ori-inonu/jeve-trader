"""Local settings and research journal. API keys are deliberately not persisted."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import sys
import time


VERSION = "0.3.0"
SETTING_KEYS = frozenset({"symbol", "workbook", "sheet", "cell_range", "excel_mode", "csv_path", "tape_sheet", "tape_range",
                         "start", "current", "peak", "risk_pct", "daily_pct", "drawdown_pct",
                         "stop", "target", "loss_streak", "fees", "slippage", "margin", "contract_cap", "last_loss_ms", "api_call_limit"})


def resource_path(name: str) -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    path = (root / name).resolve()
    if root.resolve() not in path.parents:
        raise ValueError("Invalid resource path")
    return path


def data_directory() -> Path:
    if sys.platform == "win32":
        parent = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    else:
        parent = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    return parent / "JevWIN"


def _safe_payload(value):
    if isinstance(value, dict):
        return {k: _safe_payload(v) for k, v in value.items()
                if isinstance(k, str) and not any(x in k.lower() for x in ("api_key", "password", "authorization", "secret"))}
    if isinstance(value, (list, tuple)):
        return [_safe_payload(x) for x in value]
    return value


class UserStore:
    def __init__(self, directory: Path | None = None):
        self.directory = Path(directory) if directory is not None else data_directory()
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = self.directory / "journal.sqlite3"
        self.db = sqlite3.connect(self.path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, ts_ms INTEGER NOT NULL,
            kind TEXT NOT NULL, payload TEXT NOT NULL);
        """)

    def settings(self) -> dict:
        return {key: value for key, value in self.db.execute("SELECT key,value FROM settings") if key in SETTING_KEYS}

    def save_settings(self, values: dict) -> None:
        entries = [(key, str(value)) for key, value in values.items() if key in SETTING_KEYS]
        with self.db:
            self.db.executemany("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", entries)

    def record(self, kind: str, payload: dict, *, ts_ms: int | None = None) -> None:
        if kind not in {"flow", "jev", "risk", "trade_manual", "source", "error", "recommendation"}:
            raise ValueError("Unknown journal event")
        body = json.dumps(_safe_payload(payload), ensure_ascii=False, allow_nan=False)
        if len(body) > 200_000:
            raise ValueError("Journal event too large")
        stamp = int(time.time() * 1000) if ts_ms is None else ts_ms
        if type(stamp) is not int or stamp < 0:
            raise ValueError("Invalid journal time")
        with self.db:
            self.db.execute("INSERT INTO events(ts_ms,kind,payload) VALUES(?,?,?)", (stamp, kind, body))
            self.db.execute("DELETE FROM events WHERE id <= (SELECT COALESCE(MAX(id),0)-10000 FROM events)")

    def recent(self, limit: int = 200, *, kind: str | None = None) -> list[dict]:
        if type(limit) is not int or not 1 <= limit <= 10000:
            raise ValueError("Invalid journal limit")
        if kind is None:
            rows = self.db.execute("SELECT id,ts_ms,kind,payload FROM events ORDER BY id DESC LIMIT ?", (limit,))
        else:
            rows = self.db.execute("SELECT id,ts_ms,kind,payload FROM events WHERE kind=? ORDER BY id DESC LIMIT ?", (kind, limit))
        return [{"id": i, "ts_ms": ts, "kind": k, "payload": json.loads(p)} for i, ts, k, p in rows]

    def export(self, path: Path) -> None:
        data = {"app_version": VERSION, "exported_at_ms": int(time.time() * 1000),
                "purpose": "research_journal_not_broker_statement", "events": self.recent(10000)}
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")

    def close(self) -> None:
        self.db.close()

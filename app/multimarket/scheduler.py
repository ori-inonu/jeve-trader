"""Bounded, identity-aware orchestration for contextual Jev evaluations."""

from __future__ import annotations

import json
import hashlib
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from .contracts import EvaluationIdentity, SystemClock


@dataclass(frozen=True)
class SchedulerConfig:
    max_pending: int = 8
    min_interval_ms: int = 2_000
    timeout_ms: int = 10_000
    validity_ms: int = 2_000
    model: str = "jev-1.13.0"
    question_version: str = "mm-context-v1"

    def __post_init__(self) -> None:
        for name in ("max_pending", "timeout_ms", "validity_ms"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        value = self.min_interval_ms
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("min_interval_ms must be a nonnegative integer")
        if self.max_pending > 256:
            raise ValueError("max_pending exceeds the safe queue bound")
        if self.model != "jev-1.13.0":
            raise ValueError("Only the pinned Jev model is supported")
        if not isinstance(self.question_version, str) or not self.question_version or len(self.question_version) > 64:
            raise ValueError("question_version is invalid")


@dataclass
class _Call:
    call_id: str
    identity: EvaluationIdentity
    questions: dict[str, dict[str, Any]]
    feature_key: str
    evidence_key: str
    priority: int
    order: int
    dispatched_ns: int | None = None


class ContextScheduler:
    """Bounded single-flight scheduler with exact identity and monotonic expiry."""

    def __init__(self, config: SchedulerConfig | Mapping[str, Any], *, clock: Any = None):
        if isinstance(config, Mapping):
            allowed = set(SchedulerConfig.__dataclass_fields__)
            if set(config) - allowed:
                raise ValueError("scheduler config contains unsupported fields")
            try:
                config = SchedulerConfig(**dict(config))
            except TypeError:
                raise ValueError("scheduler config is invalid") from None
        if not isinstance(config, SchedulerConfig):
            raise ValueError("config must be a SchedulerConfig or field mapping")
        self.config = config
        self._clock = clock or SystemClock()
        self._lock = threading.RLock()
        self._enabled = True
        self._pending: list[_Call] = []
        self._inflight: _Call | None = None
        self._last_dispatched_ns: int | None = None
        self._order = 0
        self._settled: dict[str, str] = {}
        self._settled_evidence: dict[str, None] = {}
        self._last_error: str | None = None

    @staticmethod
    def _safe_questions(questions: Any, model: str) -> dict[str, dict[str, Any]]:
        if not isinstance(questions, dict):
            raise ValueError("context questions are invalid")
        try:
            raw = json.dumps(questions, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
            normalized = json.loads(raw, parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()))
            from jev_client import build_payload

            build_payload({}, normalized, model)
            return normalized
        except Exception:
            raise ValueError("context questions do not match the Jev Choice/Noul schema") from None

    def _now_ns(self) -> int:
        value = self._clock.monotonic_ns()
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise RuntimeError("monotonic clock returned an invalid value")
        return value

    def _age_ms(self, identity: EvaluationIdentity, now_ns: int) -> int:
        return (now_ns - identity.received_monotonic_ns) // 1_000_000

    def _fresh_reason(self, identity: EvaluationIdentity, now_ns: int) -> str | None:
        age_ns = now_ns - identity.received_monotonic_ns
        if age_ns < 0:
            return "clock_regressed"
        if age_ns > self.config.validity_ms * 1_000_000:
            return "context_expired"
        return None

    @staticmethod
    def _evidence_key(
        identity: EvaluationIdentity, feature_key: str, questions: dict[str, dict[str, Any]]
    ) -> str:
        material = json.dumps(
            {"identity": identity.to_wire(), "feature_key": feature_key, "questions": questions},
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def _remember_locked(self, call_id: str, status: str) -> None:
        self._settled[call_id] = status
        while len(self._settled) > 64:
            self._settled.pop(next(iter(self._settled)))

    def _reap_locked(self, now_ns: int) -> None:
        remaining: list[_Call] = []
        for call in self._pending:
            reason = self._fresh_reason(call.identity, now_ns)
            if reason is None:
                remaining.append(call)
            else:
                self._remember_locked(call.call_id, "expired")
                self._last_error = reason
        self._pending = remaining
        call = self._inflight
        if call is not None and call.dispatched_ns is not None:
            if now_ns - call.dispatched_ns > self.config.timeout_ms * 1_000_000:
                self._inflight = None
                self._remember_locked(call.call_id, "timed_out")
                self._last_error = "timeout"

    def offer(
        self,
        identity: EvaluationIdentity,
        questions: dict,
        feature_key: str,
        priority: int = 0,
    ) -> dict:
        """Queue current evidence once; old, disabled, or malformed offers fail closed."""
        if not isinstance(identity, EvaluationIdentity):
            raise ValueError("identity must be an EvaluationIdentity")
        if identity.question_version != self.config.question_version:
            return {"status": "rejected", "reason": "question_version_mismatch"}
        if not isinstance(feature_key, str) or not feature_key or len(feature_key) > 256:
            raise ValueError("feature_key must be nonempty text up to 256 characters")
        if isinstance(priority, bool) or not isinstance(priority, int) or not -100 <= priority <= 100:
            raise ValueError("priority must be an integer from -100 to 100")
        safe_questions = self._safe_questions(questions, self.config.model)
        with self._lock:
            now_ns = self._now_ns()
            self._reap_locked(now_ns)
            if not self._enabled:
                return {"status": "disabled", "reason": "scheduler_disabled"}
            reason = self._fresh_reason(identity, now_ns)
            if reason is not None:
                return {"status": "expired", "reason": reason}
            evidence_key = self._evidence_key(identity, feature_key, safe_questions)
            existing = self._pending + ([self._inflight] if self._inflight is not None else [])
            for call in existing:
                if call is not None and call.evidence_key == evidence_key:
                    return {"status": "coalesced", "call_id": call.call_id, "queued": len(self._pending)}
            if evidence_key in self._settled_evidence:
                return {"status": "coalesced", "reason": "already_evaluated", "queued": len(self._pending)}
            if len(self._pending) >= self.config.max_pending:
                return {"status": "rejected", "reason": "queue_full", "queued": len(self._pending)}
            self._order += 1
            call = _Call(
                call_id=str(uuid4()),
                identity=identity,
                questions=safe_questions,
                feature_key=feature_key,
                evidence_key=evidence_key,
                priority=priority,
                order=self._order,
            )
            self._pending.append(call)
            return {"status": "queued", "call_id": call.call_id, "queued": len(self._pending)}

    def take(self) -> dict | None:
        """Take one fresh evaluation when single-flight and rate limits permit."""
        with self._lock:
            now_ns = self._now_ns()
            self._reap_locked(now_ns)
            if not self._enabled or self._inflight is not None or not self._pending:
                return None
            if (
                self._last_dispatched_ns is not None
                and now_ns - self._last_dispatched_ns < self.config.min_interval_ms * 1_000_000
            ):
                return None
            eligible: list[tuple[int, _Call]] = []
            for index, call in enumerate(self._pending):
                if self._fresh_reason(call.identity, now_ns) is None:
                    eligible.append((index, call))
            if not eligible:
                self._reap_locked(now_ns)
                return None
            index, call = min(eligible, key=lambda pair: (-pair[1].priority, pair[1].order))
            self._pending.pop(index)
            call.dispatched_ns = now_ns
            self._inflight = call
            self._last_dispatched_ns = now_ns
            self._settled_evidence[call.evidence_key] = None
            while len(self._settled_evidence) > 64:
                self._settled_evidence.pop(next(iter(self._settled_evidence)))
            return {
                "call_id": call.call_id,
                "identity": call.identity,
                "questions": json.loads(json.dumps(call.questions, ensure_ascii=False, allow_nan=False)),
                "feature_key": call.feature_key,
                "model": self.config.model,
                "question_version": self.config.question_version,
                "origin_monotonic_ns": call.identity.received_monotonic_ns,
                "deadline_monotonic_ns": now_ns + self.config.timeout_ms * 1_000_000,
            }

    def complete(self, call_id: str, response: dict | None, current_identity: EvaluationIdentity) -> dict:
        """Accept only a valid response for the still-current, still-fresh identity."""
        if not isinstance(call_id, str) or not call_id:
            raise ValueError("call_id is required")
        with self._lock:
            now_ns = self._now_ns()
            self._reap_locked(now_ns)
            call = self._inflight
            if call is None or call.call_id != call_id:
                status = self._settled.get(call_id, "unknown_call")
                return {"accepted": False, "status": status, "reason": status}
            reason = self._fresh_reason(call.identity, now_ns)
            if reason is not None:
                self._inflight = None
                self._remember_locked(call_id, "expired")
                self._last_error = reason
                return {"accepted": False, "status": "expired", "reason": reason}
            if not self._enabled:
                self._inflight = None
                self._remember_locked(call_id, "disabled")
                return {"accepted": False, "status": "disabled", "reason": "scheduler_disabled"}
            if current_identity != call.identity:
                self._inflight = None
                self._remember_locked(call_id, "stale")
                self._last_error = "identity_changed"
                return {"accepted": False, "status": "stale", "reason": "identity_changed"}
            if response is None:
                self._inflight = None
                self._remember_locked(call_id, "abstained")
                self._last_error = "abstained"
                return {"accepted": False, "status": "abstained", "reason": "no_response"}
            if isinstance(response, dict) and set(response) == {"error"} and isinstance(response["error"], str):
                visible_reason = " ".join(
                    "".join(character if character.isprintable() else " " for character in response["error"]).split()
                )[:160]
                if visible_reason:
                    self._inflight = None
                    self._remember_locked(call_id, "unavailable")
                    self._last_error = visible_reason
                    return {"accepted": False, "status": "unavailable", "reason": visible_reason}
            try:
                from jev_client import validate_response

                valid = validate_response(response, call.questions, self.config.model)
                normalized = json.loads(json.dumps(valid, ensure_ascii=False, allow_nan=False))
            except Exception:
                self._inflight = None
                self._remember_locked(call_id, "unavailable")
                self._last_error = "invalid_response"
                return {"accepted": False, "status": "unavailable", "reason": "invalid_response"}
            self._inflight = None
            self._remember_locked(call_id, "accepted")
            self._last_error = None
            return {
                "accepted": True,
                "status": "accepted",
                "identity": call.identity,
                "origin_monotonic_ns": call.identity.received_monotonic_ns,
                "age_ms": self._age_ms(call.identity, now_ns),
                "valid_until_monotonic_ns": call.identity.received_monotonic_ns + self.config.validity_ms * 1_000_000,
                "answers": normalized["answers"],
                "usage": normalized["usage"],
                "model": normalized["model"],
                "question_version": self.config.question_version,
                "financial_probability": None,
            }

    def set_enabled(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise ValueError("enabled must be boolean")
        with self._lock:
            if self._enabled == enabled:
                return
            self._enabled = enabled
            if not enabled:
                for call in self._pending:
                    self._remember_locked(call.call_id, "disabled")
                self._pending.clear()
                if self._inflight is not None:
                    self._remember_locked(self._inflight.call_id, "disabled")
                    self._inflight = None
                self._last_error = "scheduler_disabled"
            else:
                self._last_error = None

    def snapshot(self) -> dict:
        with self._lock:
            now_ns = self._now_ns()
            self._reap_locked(now_ns)
            if not self._enabled:
                status = "disabled"
            elif self._inflight is not None:
                status = "in_flight"
            elif self._pending:
                status = "queued"
            else:
                status = "ready"
            return {
                "enabled": self._enabled,
                "status": status,
                "pending": len(self._pending),
                "queued": len(self._pending),
                "in_flight": self._inflight is not None,
                "model": self.config.model,
                "question_version": self.config.question_version,
                "error": self._last_error,
            }


def build_questions() -> dict[str, dict[str, Any]]:
    """Return the fixed directional and contextual-consistency question set."""
    return {
        "direction": {
            "type": "choice",
            "instructions": (
                "Using only the supplied bounded market observations, choose the immediate "
                "contextual reading. Choose wait when evidence is mixed, stale, or insufficient. "
                "This is not a financial recommendation or an estimate of future profit."
            ),
            "criteria": {
                "wait": "Evidence is mixed, stale, or insufficient for a directional observation.",
                "observe_buy": "The bounded evidence contextually favors observing buy-side pressure.",
                "observe_sell": "The bounded evidence contextually favors observing sell-side pressure.",
            },
        },
        "context_support": {
            "type": "noul",
            "instructions": "Is the supplied context consistent with and supportive of the supplied market observations? Assess contextual support only; do not estimate financial outcomes.",
            "criteria": None,
        },
        "context_contradiction": {
            "type": "noul",
            "instructions": "Does the supplied context contradict the supplied market observations? Assess contextual contradiction only; do not estimate financial outcomes.",
            "criteria": None,
        },
        "context_insufficient": {
            "type": "noul",
            "instructions": "Is the supplied context insufficient to assess the supplied market observations? Assess evidence sufficiency only; do not estimate financial outcomes.",
            "criteria": None,
        },
    }

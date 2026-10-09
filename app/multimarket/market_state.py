from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable

from .contracts import EventEnvelope, InstrumentSpec, SourceCapabilities, SystemClock


_SUPPORTED_DOMAINS = ("quote", "trades", "book")
_MAX_RECENT_TRADES = 500
_FRESHNESS_LIMITS_MS = {"quote": 5_000, "trades": 30_000, "book": 2_000}


@dataclass(frozen=True)
class IngestResult:
    applied: bool
    duplicate: bool
    resync_required: bool
    reasons: tuple[str, ...]
    epoch: int


class MarketState:
    """Per-workspace market state with conservative quality and freshness gates."""

    def __init__(
        self,
        spec: InstrumentSpec,
        caps: SourceCapabilities,
        *,
        clock: Any = None,
        workspace_id: str = "",
        epoch: int = 1,
    ) -> None:
        if not isinstance(spec, InstrumentSpec):
            raise TypeError("instrument_spec_required")
        if not isinstance(caps, SourceCapabilities):
            raise TypeError("source_capabilities_required")
        if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch < 1:
            raise ValueError("epoch_must_be_positive")
        if not isinstance(workspace_id, str):
            raise TypeError("workspace_id_must_be_text")
        self.spec = spec
        self.caps = caps
        self.clock = clock or SystemClock()
        self.workspace_id = workspace_id.strip()
        self.epoch = epoch
        self._quote: EventEnvelope | None = None
        self._trades: deque[EventEnvelope] = deque(maxlen=_MAX_RECENT_TRADES)
        self._book: EventEnvelope | None = None
        self._seen: set[tuple[int, str, str]] = set()
        self._last_sequence: dict[str, int] = {}
        self._last_by_domain: dict[str, EventEnvelope | None] = {name: None for name in _SUPPORTED_DOMAINS}
        self._health: dict[str, dict[str, Any]] = {}
        for domain in _SUPPORTED_DOMAINS:
            supported = self._domain_supported(domain)
            self._health[domain] = {
                "status": "waiting" if supported else "unavailable",
                "reason": "awaiting_evidence" if supported else "source_capability_absent",
            }

    def _domain_supported(self, domain: str) -> bool:
        if domain == "quote":
            return self.caps.quote
        if domain == "trades":
            return self.caps.trades
        if domain == "book":
            # An L1 quote is not an L2 book. Require an explicit L2 capability.
            return self.caps.book and self.caps.book_mode == "l2"
        return False

    @staticmethod
    def _domain_for(kind: str) -> str:
        return "trades" if kind == "trade" else kind

    def _result(self, *, applied: bool = False, duplicate: bool = False, resync: bool = False, reasons: Iterable[str] = ()) -> IngestResult:
        return IngestResult(applied, duplicate, resync, tuple(reasons), self.epoch)

    def ingest(self, event: EventEnvelope) -> IngestResult:
        if not isinstance(event, EventEnvelope):
            raise TypeError("event_envelope_required")
        domain = self._domain_for(event.kind)
        if event.instrument_id != self.spec.instrument_id or event.source_id != self.caps.source_id:
            return self._result(reasons=("identity_mismatch",))
        if self.workspace_id and event.workspace_id != self.workspace_id:
            return self._result(reasons=("workspace_mismatch",))
        if not self._domain_supported(domain):
            reason = "book_unavailable" if domain == "book" else f"{domain}_unsupported"
            return self._result(reasons=(reason,))
        if event.epoch != self.epoch:
            return self._result(reasons=("epoch_mismatch",))
        if event.metadata_version != self.spec.metadata_version:
            return self.invalidate("metadata_version_changed")

        event_key = (event.epoch, domain, event.event_id)
        if event_key in self._seen:
            return self._result(duplicate=True, reasons=("duplicate_event",))
        self._seen.add(event_key)

        now_ns = self.clock.monotonic_ns()
        if event.received_monotonic_ns > now_ns:
            return self.invalidate("receive_clock_in_future", domains=(domain,))

        previous = self._last_by_domain[domain]
        if (
            previous is not None
            and event.market_ts_ms is not None
            and previous.market_ts_ms is not None
            and event.market_ts_ms < previous.market_ts_ms
        ):
            return self.invalidate("delayed_event", domains=(domain,))

        sequence_problem = self._sequence_problem(domain, event)
        if sequence_problem is not None:
            scope = self.caps.sequence_scope.casefold()
            affected = _SUPPORTED_DOMAINS if scope in {"global", "stream", "source"} else (domain,)
            return self.invalidate(sequence_problem, domains=affected)

        self._store(event, domain)
        return self._result(applied=True)

    def _sequence_problem(self, domain: str, event: EventEnvelope) -> str | None:
        scope = self.caps.sequence_scope.casefold()
        if scope not in {"per_domain", "domain", "by_domain", "kind", "global", "stream", "source"}:
            return None
        if event.sequence_first is None or event.sequence_last is None:
            return None
        key = "*" if scope in {"global", "stream", "source"} else domain
        previous = self._last_sequence.get(key)
        if previous is None:
            return None
        if event.sequence_last <= previous:
            return "sequence_regression"
        if event.sequence_first > previous + 1:
            return "sequence_gap"
        return None

    def _store(self, event: EventEnvelope, domain: str) -> None:
        if domain == "quote":
            self._quote = event
        elif domain == "trades":
            self._trades.append(event)
        else:
            self._book = event
        self._last_by_domain[domain] = event
        if event.sequence_last is not None:
            scope = self.caps.sequence_scope.casefold()
            if scope in {"per_domain", "domain", "by_domain", "kind"}:
                self._last_sequence[domain] = event.sequence_last
            elif scope in {"global", "stream", "source"}:
                self._last_sequence["*"] = event.sequence_last
        self._health[domain] = {"status": "live", "reason": None}

    def invalidate(self, reason: str, domains: Iterable[str] = _SUPPORTED_DOMAINS) -> IngestResult:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("invalidation_reason_required")
        selected = tuple(dict.fromkeys(domains))
        if not selected or any(domain not in _SUPPORTED_DOMAINS for domain in selected):
            raise ValueError("invalid_invalidation_domains")
        self.epoch += 1
        for domain in selected:
            if domain == "quote":
                self._quote = None
            elif domain == "trades":
                self._trades.clear()
            else:
                self._book = None
            self._last_by_domain[domain] = None
            self._health[domain] = (
                {"status": "stale", "reason": reason.strip()}
                if self._domain_supported(domain)
                else {"status": "unavailable", "reason": "source_capability_absent"}
            )
        # Epoch is workspace-wide, so retained data from other domains can no
        # longer be used as current-epoch evidence. A fresh event restores it.
        for domain in _SUPPORTED_DOMAINS:
            self._last_by_domain[domain] = None
            if domain not in selected and self._domain_supported(domain):
                retained = {
                    "quote": self._quote,
                    "trades": self._trades[-1] if self._trades else None,
                    "book": self._book,
                }[domain]
                if retained is not None:
                    self._health[domain] = {"status": "stale", "reason": "epoch_changed"}
        self._last_sequence.clear()
        return self._result(resync=True, reasons=(reason.strip(),))

    def _event_age_ms(self, event: EventEnvelope | None) -> int | None:
        if event is None:
            return None
        return max(0, (self.clock.monotonic_ns() - event.received_monotonic_ns) // 1_000_000)

    @staticmethod
    def _wire_event(event: EventEnvelope, age_ms: int) -> dict[str, Any]:
        return {
            **dict(event.payload),
            "event_id": event.event_id,
            "market_ts_ms": event.market_ts_ms,
            "received_at_ms": event.received_at_ms,
            "received_monotonic_ns": event.received_monotonic_ns,
            "age_ms": age_ms,
        }

    def _domain_snapshot(self, domain: str, event: EventEnvelope | None) -> tuple[dict[str, Any], bool]:
        state = dict(self._health[domain])
        if not self._domain_supported(domain):
            return {"status": "unavailable", "reason": "source_capability_absent", "age_ms": None}, False
        age = self._event_age_ms(event)
        if event is None:
            state["age_ms"] = None
            return state, False
        if event.epoch != self.epoch:
            return {"status": "stale", "reason": "epoch_changed", "age_ms": age}, False
        state["age_ms"] = age
        if age is not None and age > _FRESHNESS_LIMITS_MS[domain]:
            state = {"status": "stale", "reason": f"{domain}_stale", "age_ms": age}
            return state, False
        state.update({"status": "live", "reason": None})
        return state, True

    def snapshot(self) -> dict[str, Any]:
        quote_health, quote_fresh = self._domain_snapshot("quote", self._quote)
        trade_event = self._trades[-1] if self._trades else None
        trades_health, trades_fresh = self._domain_snapshot("trades", trade_event)
        book_health, book_fresh = self._domain_snapshot("book", self._book)
        quote = self._wire_event(self._quote, quote_health["age_ms"]) if self._quote and quote_fresh else None
        recent_trades = [
            self._wire_event(event, self._event_age_ms(event) or 0)
            for event in self._trades
            if (self._event_age_ms(event) or 0) <= _FRESHNESS_LIMITS_MS["trades"]
        ] if trades_fresh else []
        book = self._wire_event(self._book, book_health["age_ms"]) if self._book and book_fresh else None
        buy_quantity = sum((Decimal(str(event.payload["quantity"])) for event in self._trades if event.payload.get("aggressor") == "buy" and (self._event_age_ms(event) or 0) <= _FRESHNESS_LIMITS_MS["trades"]), Decimal(0))
        sell_quantity = sum((Decimal(str(event.payload["quantity"])) for event in self._trades if event.payload.get("aggressor") == "sell" and (self._event_age_ms(event) or 0) <= _FRESHNESS_LIMITS_MS["trades"]), Decimal(0))
        observed_trades = [event for event in self._trades if (self._event_age_ms(event) or 0) <= _FRESHNESS_LIMITS_MS["trades"]] if trades_fresh else []
        spread = None
        if quote_fresh and self._quote is not None:
            spread = str(Decimal(str(self._quote.payload["ask"])) - Decimal(str(self._quote.payload["bid"])))
            spread = spread.rstrip("0").rstrip(".") if "." in spread else spread
            if spread in {"", "-0"}:
                spread = "0"
        delta_quantity = buy_quantity - sell_quantity
        features = {
            "version": "mm-features-v1",
            "trade_count": len(observed_trades),
            "buy_quantity": self._decimal_text(buy_quantity),
            "sell_quantity": self._decimal_text(sell_quantity),
            "delta_quantity": self._decimal_text(delta_quantity),
            "spread": spread,
            "event_range": [observed_trades[0].event_id, observed_trades[-1].event_id] if observed_trades else None,
        }
        warnings = []
        for domain, health in (("quote", quote_health), ("trades", trades_health), ("book", book_health)):
            if health["status"] in {"stale", "unavailable"}:
                warnings.append({"domain": domain, "reason": health["reason"]})
        if not self.caps.full_tape:
            warnings.append({"domain": "trades", "reason": "full_tape_unverified"})
        return {
            "epoch": self.epoch,
            "quote": quote,
            "recent_trades": recent_trades,
            "book": book,
            "health": {"quote": quote_health, "trades": trades_health, "book": book_health},
            "features": features,
            "warnings": warnings,
            "full_tape": bool(self.caps.full_tape),
        }

    @staticmethod
    def _decimal_text(value: Decimal) -> str:
        if value == 0:
            return "0"
        text = format(value, "f")
        return text.rstrip("0").rstrip(".") if "." in text else text

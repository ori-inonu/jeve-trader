"""Observed price geometry for technical research; never a trade instruction.

Levels are repeated executed prices or observed previous-window extrema, not
validated support/resistance. No far target or tighter stop is manufactured to
fit a balance or reward/risk requirement. The existing risk engine sizes each
fixed geometry against the supplied manual simulation account.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, DecimalException

from candidate_engine import generate_candidates
from risk import evaluate_risk


LEVEL_WINDOW_MS = 30000
PREVIOUS_WINDOW_MS = 5000
QUOTE_MAX_AGE_MS = 2000
MAX_LEVELS = 100
MAX_TRADES = 100000


def generate_candidate_scenario(symbol="WIN_SIM", end_ms=1801848600000):
    """Synthetic observed range with the final quote inside that prior range.

    This fixture demonstrates geometry and risk comparison, separately from the
    four flow-pattern fixtures. Its prices and aggression are invented examples,
    not an exchange feed or a tested prediction.
    """
    if not isinstance(symbol, str) or not symbol.strip() or len(symbol) > 64:
        raise ValueError("Invalid synthetic symbol")
    if type(end_ms) is not int or not 35000 <= end_ms <= 10**15:
        raise ValueError("Invalid synthetic clock")
    cycle = (130800, 130900, 131000, 131100, 131200, 131100, 131000, 130900)
    events = []
    for index in range(141):
        ts = end_ms - 35000 + index * 250
        price = 131000 if index == 140 else cycle[index % len(cycle)]
        events.append({"type": "trade", "id": f"technical-range-{index}", "symbol": symbol, "ts_ms": ts,
                       "price_points": str(price), "quantity": 5,
                       "aggressor": "buy" if index % 2 else "sell"})
        if index % 4 == 0:
            events.append({"type": "book", "symbol": symbol, "ts_ms": ts,
                           "bids": [{"price_points": str(price - level * 5), "quantity": 50} for level in range(3)],
                           "asks": [{"price_points": str(price + 5 + level * 5), "quantity": 50} for level in range(3)]})
    return {"events": events, "now_ms": end_ms, "symbol": symbol, "mode": "technical_range",
            "label": "SYNTHETIC TECHNICAL COMPARISON FIXTURE, NOT B3 MARKET DATA",
            "synthetic": True, "exchange_data": False,
            "source_quality": {"feed_connected": True, "sequence_ok": True, "full_tape": True, "data_origin": "synthetic"}}


def _price(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)) or len(str(value)) > 64:
        raise ValueError("Invalid price")
    price = Decimal(str(value))
    if not price.is_finite() or price <= 0 or abs(price.adjusted()) > 12:
        raise ValueError("Invalid price")
    return price


def _text(value):
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _quote(engine, snapshot, now_ms, tick):
    """Prefer actual normalized book events over separately sampled RTD quotes."""
    if getattr(engine, "books", None):
        book = engine.books[-1]
        ts = book["ts_ms"]
        if type(ts) is int and 0 <= now_ms - ts <= QUOTE_MAX_AGE_MS:
            bid, ask = _price(book["bids"][0][0]), _price(book["asks"][0][0])
            if ask > bid and not bid % tick and not ask % tick:
                return bid, ask, ts, "retained_book"
    quote = snapshot.get("last_quote")
    if isinstance(quote, dict) and quote.get("symbol") == snapshot["symbol"]:
        ts = quote.get("ts_ms")
        if type(ts) is int and 0 <= now_ms - ts <= QUOTE_MAX_AGE_MS:
            bid, ask = _price(quote.get("bid")), _price(quote.get("ask"))
            if ask > bid and not bid % tick and not ask % tick:
                return bid, ask, ts, "sampled_quote"
    return None, None, None, "unavailable"


def build_market_candidates(flow_engine, snapshot, config, account, now_ms):
    """At most eight unranked geometries, each with an independent risk result.

    No account timestamp is refreshed and no live account is converted into a
    simulation. A missing/stale account remains blocked by evaluate_risk. Empty
    results explain missing market geometry instead of inventing reference data.
    """
    result = {"schema_version": 1, "status": "UNAVAILABLE", "rows": [], "reference_levels": [],
              "reasons": [], "evaluated_at_ms": now_ms, "account_source": "manual_scenario",
              "simulation_only": True, "actionable_live_signal": False, "order_sent": False,
              "strategy_validated": False, "win_probability": None, "future_profit_probability": None,
              "ranking": None, "expected_return": None,
              "evidence_coverage": {"level_window_ms": LEVEL_WINDOW_MS, "level_count": 0,
                                    "quote_source": "unavailable", "quote_fresh": False,
                                    "levels_are_validated_support_resistance": False,
                                    "sampled_levels_can_miss_market_activity": True},
              "interpretation": "Cenários técnicos com preços observados; não são entradas, recomendações ou probabilidades de lucro."}
    try:
        if type(now_ms) is not int or not 0 <= now_ms <= 10**15:
            raise ValueError("Invalid clock")
        if not isinstance(snapshot, dict) or snapshot.get("symbol") != getattr(flow_engine, "symbol", None):
            raise ValueError("Symbol mismatch")
        if not isinstance(config, dict) or not isinstance(config.get("risk"), dict):
            raise ValueError("Missing configuration")
        tick = _price(config["instrument"]["tick_points"])
        if tick != getattr(flow_engine, "tick", tick):
            raise ValueError("Tick mismatch")
        symbol = snapshot["symbol"]
        coverage = deepcopy(snapshot.get("evidence_coverage", {}))
        result["evidence_coverage"]["flow_evidence"] = coverage
        if coverage.get("integrity_ok") is not True or getattr(flow_engine, "faults", None):
            result["reasons"].append("MARKET_EVENT_INTEGRITY_REQUIRED")
            return result
        groups, previous, total, future_count = {}, [], 0, 0
        trades = getattr(flow_engine, "trades", ())
        if len(trades) > MAX_TRADES:
            raise ValueError("Trade buffer exceeds research bound")
        for event in trades:
            ts = event["ts_ms"]
            if type(ts) is not int or ts < 0 or event.get("symbol", symbol) != symbol:
                raise ValueError("Invalid retained event")
            if ts > now_ms:
                future_count += 1
                continue
            if not now_ms - LEVEL_WINDOW_MS < ts <= now_ms:
                continue
            price = _price(event["price_points"])
            quantity = event["quantity"]
            if price % tick or type(quantity) is not int or not 1 <= quantity <= 10**9:
                raise ValueError("Invalid retained price or volume")
            entry = groups.setdefault(price, {"touches": 0, "volume": 0, "last_ms": ts, "first_ms": ts, "roles": []})
            entry["touches"] += 1
            entry["volume"] += quantity
            entry["last_ms"] = max(entry["last_ms"], ts)
            entry["first_ms"] = min(entry["first_ms"], ts)
            total += quantity
            if now_ms - 2 * PREVIOUS_WINDOW_MS < ts <= now_ms - PREVIOUS_WINDOW_MS:
                previous.append(price)
        if previous:
            groups[min(previous)]["roles"].append("previous_5s_low")
            groups[max(previous)]["roles"].append("previous_5s_high")
        selected = [(price, group) for price, group in groups.items() if group["touches"] >= 2 or group["roles"]]
        # Previous-window extrema survive truncation; repeated prices are ordered
        # by actually captured volume. This is an extraction bound, not a signal rank.
        selected.sort(key=lambda item: (not bool(item[1]["roles"]), -item[1]["volume"], -item[1]["touches"], item[0]))
        levels = []
        for price, group in selected[:MAX_LEVELS]:
            roles = list(group["roles"])
            if group["touches"] >= 2:
                roles.append("repeated_executed_price")
            identity = f"observed:{symbol}:{_text(price)}:{group['first_ms']}:{group['last_ms']}"
            levels.append({"price_points": _text(price), "evidence_id": identity, "asof_ms": group["last_ms"],
                           "first_observed_ms": group["first_ms"], "touches": group["touches"],
                           "observed_contracts": group["volume"], "roles": roles,
                           "captured_volume_fraction": _text(Decimal(group["volume"]) / total),
                           "description": "Preço executado observado: " + ", ".join(roles) + "; relevância preditiva não validada."})
        result["reference_levels"] = levels
        result["evidence_coverage"].update({"level_count": len(levels), "captured_window_contracts": total,
                                           "future_events_excluded": future_count,
                                           "level_selection_truncated": len(selected) > MAX_LEVELS,
                                           "level_source": "normalized_retained_trades"})
        if future_count:
            result["reasons"].append("FUTURE_TRADES_EXCLUDED")
        if not levels:
            result["reasons"].append("OBSERVED_REFERENCE_LEVELS_REQUIRED")
        try:
            bid, ask, quote_ts, quote_source = _quote(flow_engine, snapshot, now_ms, tick)
        except (KeyError, TypeError, ValueError, DecimalException, IndexError):
            bid, ask, quote_ts, quote_source = None, None, None, "unavailable"
        result["evidence_coverage"].update({"quote_source": quote_source, "quote_fresh": bid is not None,
                                           "quote_ts_ms": quote_ts, "sampled_quote_is_authoritative_book": False,
                                           "entry_quote_bid_points": _text(bid) if bid is not None else None,
                                           "entry_quote_ask_points": _text(ask) if ask is not None else None})
        if bid is None:
            result["reasons"].append("FRESH_TWO_SIDED_QUOTE_REQUIRED")
        if not levels or bid is None:
            return result
        requested = config["risk"].get("max_contracts", 1)
        if type(requested) is not int or not 1 <= requested <= 10**18:
            raise ValueError("Invalid contract cap")
        candidates = generate_candidates({"ts_ms": now_ms, "bid_points": _text(bid), "ask_points": _text(ask),
                                          "reference_levels": levels}, tick_points=_text(tick), quantity_requested=requested)
        by_id = {level["evidence_id"]: level for level in levels}
        for candidate in candidates:
            risk = evaluate_risk(config, account, candidate, now_ms)
            entry, stop, target = (_price(candidate[key]) for key in ("entry_points", "stop_points", "target_points"))
            result["rows"].append({"id": candidate["id"], "side": candidate["side"],
                                   "entry_points": _text(entry), "stop_points": _text(stop), "target_points": _text(target),
                                   "stop_distance_points": _text(abs(entry - stop)), "target_distance_points": _text(abs(target - entry)),
                                   "lots": risk["contracts"], "contracts": risk["contracts"], "risk": risk,
                                   "reasons": list(risk["reasons"]), "premise": candidate["premise"],
                                   "reference_evidence_ids": list(candidate["reference_evidence_ids"]),
                                   "reference_levels": [deepcopy(by_id[identity]) for identity in candidate["reference_evidence_ids"]],
                                   "recipe": candidate["recipe"], "quote_source": quote_source,
                                   "simulation_only": True, "actionable_live_signal": False,
                                   "win_probability": None, "expected_return": None,
                                   "evidence_note": "Preço repetido/extremo observado não comprova suporte, resistência ou resultado futuro."})
        if result["rows"]:
            result["status"] = "TECHNICAL_SCENARIOS"
        else:
            result["reasons"].append("OBSERVED_LEVELS_DO_NOT_FORM_STOP_TARGET_GEOMETRY")
        return result
    except (KeyError, TypeError, ValueError, DecimalException, OverflowError, IndexError):
        result["reasons"].append("INVALID_CANDIDATE_RESEARCH_INPUT")
        result["rows"] = []
        return result

"""Bounded descriptive tape calculations. No predictive probabilities or orders.

All thresholds are research definitions, not evidence of profitability. Unknown
aggressors stay unknown; missing tape/depth cannot establish hidden liquidity,
player identity, order cancellation, or a reversal. Money/price output is text.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from decimal import Decimal, DecimalException
import json
from pathlib import Path


DEFAULT_RULES = json.loads(Path(__file__).with_name("flow_rules.json").read_text())


def _decimal(value, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)) or len(str(value)) > 64:
        raise ValueError("Invalid finite decimal")
    try:
        number = Decimal(str(value))
    except DecimalException as exc:
        raise ValueError("Invalid finite decimal") from exc
    if not number.is_finite() or abs(number.adjusted()) > 12 or (positive and number <= 0):
        raise ValueError("Invalid finite decimal")
    return number


def _integer(value, minimum=0, maximum=10**15):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("Invalid integer")
    return value


def _text(value):
    if value is None:
        return None
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _mapping(event):
    if is_dataclass(event) and not isinstance(event, type):
        return asdict(event)
    if not isinstance(event, dict):
        raise ValueError("Event must be a mapping or dataclass")
    return event


class FlowEngine:
    """Normalized trades and book snapshots, bounded by time and item count.

    Each stream must be chronological; same-time trades require distinct IDs.
    Duplicate IDs never double-count. Conflicting duplicate IDs, invalid events,
    and order violations latch an integrity fault until reset. A symbol rollover
    requires explicit reset; it never mixes contracts. No clock is synthesized.
    """

    def __init__(self, symbol, tick_points=5, *, rules=None, max_trades=10000, max_books=256):
        self.tick = _decimal(tick_points, positive=True)
        self.rules = deepcopy(DEFAULT_RULES)
        if rules is not None:
            if not isinstance(rules, dict) or set(rules) - set(DEFAULT_RULES):
                raise ValueError("Unknown flow rules")
            self.rules.update(rules)
        for key in ("short_window_ms", "long_window_ms", "retention_ms", "max_age_ms", "minimum_trades", "maximum_depth_levels"):
            _integer(self.rules[key], 1, 10**7)
        _integer(self.rules["absorption_min_aggressed_contracts"], 1)
        if not 2 * self.rules["short_window_ms"] <= self.rules["long_window_ms"] <= self.rules["retention_ms"] <= 600000:
            raise ValueError("Invalid rolling windows")
        for key in ("dominance_fraction", "exhaustion_intensity_ratio_max", "depth_reduction_fraction_min"):
            if not 0 < _decimal(self.rules[key]) <= 1:
                raise ValueError("Invalid fraction rule")
        if _decimal(self.rules["dominance_fraction"]) <= Decimal("0.5"):
            raise ValueError("Dominance must exceed one half")
        for key in ("progression_min_ticks", "no_follow_max_ticks"):
            if _decimal(self.rules[key]) < 0:
                raise ValueError("Invalid price rule")
        self.max_trades = _integer(max_trades, 2, 100000)
        self.max_books = _integer(max_books, 2, 10000)
        self.reset(symbol)

    def reset(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        if not isinstance(symbol, str) or not symbol.strip() or len(symbol) > 64:
            raise ValueError("Invalid symbol")
        self.symbol = symbol
        self.trades = deque()
        self.books = deque()
        self.ids = {}
        self.first_trade_ms = None
        self.tape_coverage_start_ms = None
        self.last_trade_ms = None
        self.last_book_ms = None
        self.latest_ms = None
        self.last_snapshot_ms = None
        self.truncated_trade_through_ms = None
        self.faults = set()
        self.rejections = {"duplicates": 0, "invalid": 0, "out_of_order": 0, "symbol_mismatch": 0}
        self.source_quality = {"feed_connected": None, "sequence_ok": None, "full_tape": None, "data_origin": "unknown"}

    def set_source_quality(self, quality):
        if not isinstance(quality, dict):
            raise ValueError("Invalid source quality")
        for key in ("feed_connected", "sequence_ok", "full_tape"):
            if key in quality and quality[key] is not None and type(quality[key]) is not bool:
                raise ValueError("Source quality flags must be boolean or unknown")
        if "data_origin" in quality and quality["data_origin"] not in ("synthetic", "replay", "live", "unknown"):
            raise ValueError("Invalid data origin")
        previous_complete = all(self.source_quality[key] is True for key in ("feed_connected", "sequence_ok", "full_tape"))
        self.source_quality.update({key: quality[key] for key in self.source_quality if key in quality})
        current_complete = all(self.source_quality[key] is True for key in ("feed_connected", "sequence_ok", "full_tape"))
        if not current_complete or not previous_complete:
            # A fresh complete stream must warm up again. Changing a flag cannot
            # retroactively upgrade an incomplete history into a complete tape.
            self.tape_coverage_start_ms = None
        if quality.get("sequence_ok") is False:
            self.faults.add("SOURCE_SEQUENCE_GAP_RESET_REQUIRED")

    def _reject(self, reason, counter="invalid", fault=True):
        self.rejections[counter] = min(10**15, self.rejections[counter] + 1)
        if fault:
            self.faults.add(reason)
        return {"accepted": False, "reason": reason}

    def _event(self, event):
        event = _mapping(event)
        if event.get("symbol") != self.symbol:
            return event, None
        ts = _integer(event["ts_ms"])
        if "source_quality" in event:
            self.set_source_quality(event["source_quality"])
        return event, ts

    def _prune(self, stamp):
        self.latest_ms = max(stamp, self.latest_ms or stamp)
        cutoff = self.latest_ms - self.rules["retention_ms"]
        while self.trades and self.trades[0]["ts_ms"] < cutoff:
            self.ids.pop(self.trades.popleft()["id"], None)
        while self.books and self.books[0]["ts_ms"] < cutoff:
            self.books.popleft()

    def add_trade(self, event):
        try:
            event, ts = self._event(event)
            if ts is None:
                return self._reject("SYMBOL_MISMATCH", "symbol_mismatch", fault=False)
            identity = event.get("id", event.get("trade_id"))
            if not isinstance(identity, str) or not identity.strip() or len(identity) > 128:
                raise ValueError("Stable trade ID required")
            price = _decimal(event["price_points"], positive=True)
            if price % self.tick:
                raise ValueError("Price off tick")
            quantity = _integer(event["quantity"], 1, 10**9)
            aggressor = event["aggressor"]
            if not isinstance(aggressor, str) or aggressor.lower() not in ("buy", "sell", "unknown"):
                raise ValueError("Invalid aggressor")
            trade = {"id": identity, "symbol": self.symbol, "ts_ms": ts, "price_points": price,
                     "quantity": quantity, "aggressor": aggressor.lower()}
            if identity in self.ids:
                conflict = trade != self.ids[identity]
                return self._reject("CONFLICTING_TRADE_ID" if conflict else "DUPLICATE_TRADE", "duplicates", conflict)
            if self.last_trade_ms is not None and ts < self.last_trade_ms:
                return self._reject("OUT_OF_ORDER_TRADE", "out_of_order")
            self._prune(ts)
            self.trades.append(trade)
            self.ids[identity] = trade
            self.first_trade_ms = ts if self.first_trade_ms is None else self.first_trade_ms
            if self.tape_coverage_start_ms is None and all(self.source_quality[key] is True for key in ("feed_connected", "sequence_ok", "full_tape")):
                self.tape_coverage_start_ms = ts
            self.last_trade_ms = ts
            while len(self.trades) > self.max_trades:
                dropped = self.trades.popleft()
                self.ids.pop(dropped["id"], None)
                self.truncated_trade_through_ms = dropped["ts_ms"]
            return {"accepted": True, "reason": "ACCEPTED"}
        except (KeyError, TypeError, ValueError, DecimalException, OverflowError):
            return self._reject("INVALID_TRADE")

    def set_book(self, event):
        try:
            event, ts = self._event(event)
            if ts is None:
                return self._reject("SYMBOL_MISMATCH", "symbol_mismatch", fault=False)
            sides = {}
            for side in ("bids", "asks"):
                levels = event[side]
                if not isinstance(levels, (list, tuple)) or not 1 <= len(levels) <= self.rules["maximum_depth_levels"]:
                    raise ValueError("Invalid depth levels")
                parsed = []
                for level in levels:
                    price = _decimal(level["price_points"], positive=True)
                    if price % self.tick:
                        raise ValueError("Depth price off tick")
                    parsed.append((price, _integer(level["quantity"], 1, 10**9)))
                prices = [price for price, _ in parsed]
                if prices != sorted(set(prices), reverse=side == "bids"):
                    raise ValueError("Unsorted or duplicate depth")
                sides[side] = parsed
            if sides["asks"][0][0] <= sides["bids"][0][0]:
                raise ValueError("Crossed or locked book")
            book = {"ts_ms": ts, **sides}
            if self.last_book_ms is not None and ts <= self.last_book_ms:
                if ts == self.last_book_ms and self.books and book == self.books[-1]:
                    return self._reject("DUPLICATE_BOOK", "duplicates", fault=False)
                return self._reject("OUT_OF_ORDER_OR_CONFLICTING_BOOK", "out_of_order")
            self._prune(ts)
            self.books.append(book)
            self.last_book_ms = ts
            while len(self.books) > self.max_books:
                self.books.popleft()
            return {"accepted": True, "reason": "ACCEPTED"}
        except (KeyError, TypeError, ValueError, DecimalException, OverflowError):
            return self._reject("INVALID_BOOK")

    def _window(self, end_ms, duration_ms):
        start = end_ms - duration_ms
        trades = [trade for trade in self.trades if start < trade["ts_ms"] <= end_ms]
        buy = sum(t["quantity"] for t in trades if t["aggressor"] == "buy")
        sell = sum(t["quantity"] for t in trades if t["aggressor"] == "sell")
        unknown = sum(t["quantity"] for t in trades if t["aggressor"] == "unknown")
        prices = [t["price_points"] for t in trades]
        progress = prices[-1] - prices[0] if prices else None
        span = max(prices) - min(prices) if prices else None
        total = buy + sell + unknown
        complete = (self.tape_coverage_start_ms is not None and self.tape_coverage_start_ms <= start
                    and (self.truncated_trade_through_ms is None or self.truncated_trade_through_ms <= start)
                    and self.source_quality["full_tape"] is True)
        return {"window_ms": duration_ms, "start_exclusive_ms": start, "end_inclusive_ms": end_ms,
                "trade_count": len(trades), "buy_aggressed_contracts": buy, "sell_aggressed_contracts": sell,
                "unknown_aggressor_contracts": unknown, "total_contracts": total, "delta_contracts": buy - sell,
                "price_change_points": _text(progress), "price_range_points": _text(span),
                "first_price_points": _text(prices[0]) if prices else None,
                "last_price_points": _text(prices[-1]) if prices else None,
                "contracts_per_second": _text(Decimal(total) * 1000 / duration_ms),
                "trades_per_second": _text(Decimal(len(trades)) * 1000 / duration_ms),
                "buy_dominance_fraction": _text(Decimal(buy) / (buy + sell)) if buy + sell else None,
                "signed_points_per_100_aggressed_contracts": _text(progress * 100 / (buy + sell)) if progress is not None and buy + sell else None,
                "complete_window": bool(complete), "aggressor_coverage_complete": unknown == 0 and total > 0}

    def snapshot(self, now_ms):
        now_ms = _integer(now_ms)
        if self.last_snapshot_ms is not None and now_ms < self.last_snapshot_ms:
            raise ValueError("Snapshot clock cannot move backwards; reset for replay")
        self.last_snapshot_ms = now_ms
        self._prune(now_ms)
        short = self.rules["short_window_ms"]
        windows = {"5s": self._window(now_ms, short), "30s": self._window(now_ms, self.rules["long_window_ms"]),
                   "previous_5s": self._window(now_ms - short, short)}
        current, previous = windows["5s"], windows["previous_5s"]
        reasons = sorted(self.faults)
        for key in ("feed_connected", "sequence_ok", "full_tape"):
            if self.source_quality[key] is not True:
                reasons.append(key.upper() + "_NOT_VERIFIED")
        if self.last_trade_ms is None or not 0 <= now_ms - self.last_trade_ms <= self.rules["max_age_ms"]:
            reasons.append("STALE_OR_FUTURE_TAPE")
        if not current["complete_window"]:
            reasons.append("SHORT_WINDOW_INCOMPLETE")
        if not current["aggressor_coverage_complete"]:
            reasons.append("AGGRESSOR_COVERAGE_INCOMPLETE")
        if current["trade_count"] < self.rules["minimum_trades"]:
            reasons.append("INSUFFICIENT_TRADES")
        book = self.books[-1] if self.books else None
        book_fresh = book is not None and 0 <= now_ms - book["ts_ms"] <= self.rules["max_age_ms"]
        bid = book["bids"][0][0] if book_fresh else None
        ask = book["asks"][0][0] if book_fresh else None
        visible_bid = sum(q for _, q in book["bids"]) if book_fresh else None
        visible_ask = sum(q for _, q in book["asks"]) if book_fresh else None
        features = {**current, "windows": windows, "source": "normalized_event_calculation",
                    "spread_points": _text(ask - bid) if book_fresh else None,
                    "visible_bid_contracts": visible_bid, "visible_ask_contracts": visible_ask,
                    "book_imbalance": _text(Decimal(visible_bid - visible_ask) / (visible_bid + visible_ask)) if book_fresh else None,
                    "book_imbalance_scope": "visible_levels_only" if book_fresh else "unavailable",
                    "intensity_ratio_to_previous_5s": _text(Decimal(current["total_contracts"]) / previous["total_contracts"]) if previous["total_contracts"] else None}
        hypotheses = self._hypotheses(current, previous, reasons, book_fresh, now_ms)
        coverage = {"source_quality": deepcopy(self.source_quality), "tape_fresh": "STALE_OR_FUTURE_TAPE" not in reasons,
                    "short_window_complete": current["complete_window"], "long_window_complete": windows["30s"]["complete_window"],
                    "previous_window_complete": previous["complete_window"], "book_fresh": book_fresh,
                    "complete_tape_observation_start_ms": self.tape_coverage_start_ms,
                    "depth_levels": {side: len(book[side]) if book_fresh else 0 for side in ("bids", "asks")},
                    "integrity_ok": not self.faults, "reasons": list(dict.fromkeys(reasons)),
                    "rejected_events": dict(self.rejections), "retained_trades": len(self.trades), "retained_books": len(self.books),
                    "deduplication_scope": "retained event IDs; older replay timestamps rejected", "participant_identity": False,
                    "order_identity": False, "cancellation_causes_known": False,
                    "aggressor_definition": "reported by source; never inferred from price alone"}
        return {"schema_version": 1, "symbol": self.symbol, "ts_ms": now_ms,
                "flow_ts_ms": self.last_trade_ms, "quote_ts_ms": book["ts_ms"] if book else None,
                "bid_points": _text(bid), "ask_points": _text(ask),
                "observations": {"hypotheses": hypotheses, "description": "Observed flow patterns; no future outcome estimate.",
                                 "rule_status": self.rules["status"]},
                "computed_features": features, "evidence_coverage": coverage, "hypotheses": hypotheses,
                "actionable_live_signal": False, "strategy_validated": False, "win_probability": None}

    def _hypotheses(self, current, previous, reasons, book_fresh, now_ms):
        result = []
        progression = _decimal(self.rules["progression_min_ticks"]) * self.tick
        no_follow = _decimal(self.rules["no_follow_max_ticks"]) * self.tick
        dominance = _decimal(self.rules["dominance_fraction"])
        progress = _decimal(current["price_change_points"]) if current["price_change_points"] is not None else Decimal(0)
        total_known = current["buy_aggressed_contracts"] + current["sell_aggressed_contracts"]

        def record(kind, side, condition, missing, evidence, description):
            status = "inconclusive" if missing else ("observed" if kind == "progression" else "potential") if condition else "not_observed"
            result.append({"id": f"{kind}_{side}", "kind": kind, "side": side, "status": status,
                           "description": description, "evidence": evidence, "missing": list(dict.fromkeys(missing)),
                           "descriptive_only": True, "future_profit_probability": None})

        for side, direction in (("buy", 1), ("sell", -1)):
            volume = current[f"{side}_aggressed_contracts"]
            prev_volume = previous[f"{side}_aggressed_contracts"]
            share = Decimal(volume) / total_known if total_known else Decimal(0)
            directional = progress * direction
            evidence = {"window_ms": current["window_ms"], "aggressed_contracts": volume,
                        "known_aggressor_share": _text(share), "directional_price_progress_points": _text(directional)}
            record("progression", side, share >= dominance and directional >= progression, reasons, evidence,
                   "Agressão dominante acompanhada por avanço observado de preço na mesma direção.")
            record("absorption", side, share >= dominance and volume >= self.rules["absorption_min_aggressed_contracts"] and directional <= no_follow,
                   reasons, evidence, "Agressão sem avanço proporcional: compatível com absorção potencial; não identifica contraparte ou liquidez oculta.")
            exhaustion_missing = list(reasons)
            if not previous["complete_window"] or not previous["aggressor_coverage_complete"] or previous["trade_count"] < self.rules["minimum_trades"]:
                exhaustion_missing.append("PREVIOUS_WINDOW_INCOMPLETE")
            ratio = Decimal(volume) / prev_volume if prev_volume else None
            prev_known = previous["buy_aggressed_contracts"] + previous["sell_aggressed_contracts"]
            prev_share = Decimal(prev_volume) / prev_known if prev_known else Decimal(0)
            prev_progress = _decimal(previous["price_change_points"]) * direction if previous["price_change_points"] is not None else Decimal(0)
            record("exhaustion", side, prev_share >= dominance and prev_progress >= progression and ratio is not None
                   and ratio <= _decimal(self.rules["exhaustion_intensity_ratio_max"]) and directional <= no_follow,
                   exhaustion_missing, {**evidence, "previous_aggressed_contracts": prev_volume, "side_intensity_ratio": _text(ratio),
                                        "previous_directional_progress_points": _text(prev_progress)},
                   "Desaceleração da agressão após avanço, sem continuação observada; hipótese de exaustão, sem previsão de reversão.")
        for side in ("bids", "asks"):
            depth = [book for book in self.books if now_ms - self.rules["short_window_ms"] < book["ts_ms"] <= now_ms and len(book[side]) > 1]
            missing = sorted(self.faults)
            if not book_fresh or len(depth) < 2:
                missing.append("DEPTH_SEQUENCE_REQUIRED")
            if self.source_quality["feed_connected"] is not True or self.source_quality["sequence_ok"] is not True:
                missing.append("SOURCE_INTEGRITY_NOT_VERIFIED")
            fraction = None
            if len(depth) >= 2:
                first, last = depth[-2], depth[-1]
                if [p for p, _ in first[side]] != [p for p, _ in last[side]]:
                    missing.append("DEPTH_PRICE_GRID_CHANGED")
                else:
                    before, after = sum(q for _, q in first[side]), sum(q for _, q in last[side])
                    fraction = Decimal(before - after) / before
            record("liquidity_withdrawal", side, fraction is not None and fraction >= _decimal(self.rules["depth_reduction_fraction_min"]), missing,
                   {"displayed_quantity_reduction_fraction": _text(fraction), "cause": "unknown; execution, cancellation or refresh may explain reduction"},
                   "Redução da liquidez exibida nos mesmos níveis entre snapshots de profundidade; não comprova cancelamento ou identidade.")
        return result


EventEngine = FlowEngine


def generate_flow_scenario(mode, symbol="WIN_SIM", end_ms=1801848600000, side="buy"):
    """Deterministic normalized fixture; it is never actual exchange data."""
    if mode not in ("progression", "absorption", "exhaustion", "choppy") or side not in ("buy", "sell"):
        raise ValueError("Unknown synthetic scenario")
    _integer(end_ms, 35000)
    direction = 1 if side == "buy" else -1
    events = []
    for index in range(141):
        ts = end_ms - 35000 + index * 250
        remaining = end_ms - ts
        if mode == "progression":
            offset, qty, aggressor = direction * (index // 4) * 5, 5, side
        elif mode == "absorption":
            offset, qty, aggressor = direction * (index % 2) * 5, 8, side
        elif mode == "exhaustion":
            offset = direction * (min(index, 120) // 4) * 5
            qty, aggressor = (1 if remaining < 5000 else 10), side
        else:
            offset, qty = (index % 3 - 1) * 5, 3
            aggressor = "buy" if index % 2 else "sell"
        price = 131000 + offset
        events.append({"type": "trade", "id": f"{mode}-{side}-{index}", "symbol": symbol, "ts_ms": ts,
                       "price_points": str(price), "quantity": qty, "aggressor": aggressor})
        if index % 4 == 0:
            events.append({"type": "book", "symbol": symbol, "ts_ms": ts,
                           "bids": [{"price_points": str(price - 5 - level * 5), "quantity": 80} for level in range(3)],
                           "asks": [{"price_points": str(price + level * 5), "quantity": 80} for level in range(3)]})
    return {"events": events, "now_ms": end_ms, "symbol": symbol, "mode": mode,
            "label": "SYNTHETIC FIXTURE, NOT B3 MARKET DATA",
            "source_quality": {"feed_connected": True, "sequence_ok": True, "full_tape": True, "data_origin": "synthetic"}}

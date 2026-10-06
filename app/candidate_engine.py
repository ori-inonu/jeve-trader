"""Finite, deterministic price candidates from observed reference levels.

Research recipe only. Detecting reliable levels and a predictive edge is outside
this generator. It does not manufacture a tighter stop to fit an account balance.
"""
from decimal import Decimal, InvalidOperation


def _number(value):
    if type(value) not in (int, float, str):
        raise ValueError("Invalid price")
    number = Decimal(str(value))
    if not number.is_finite() or number <= 0:
        raise ValueError("Invalid price")
    return number


def generate_candidates(snapshot: dict, tick_points=5, quantity_requested=1) -> list[dict]:
    """At most 8 pairs: 2 sides x 2 structural stops x 2 structural targets.

    reference_levels entries: {price_points, evidence_id, asof_ms}. These must
    already have been observed at/before the snapshot; no future extrema allowed.
    Missing levels yield no candidates. Wrongly typed inputs raise ValueError.
    """
    try:
        tick = _number(tick_points)
        bid, ask = _number(snapshot["bid_points"]), _number(snapshot["ask_points"])
        stamp = snapshot["ts_ms"]
        if type(stamp) is not int or type(quantity_requested) is not int or quantity_requested < 1:
            raise ValueError("Invalid generation context")
        if ask <= bid or bid % tick or ask % tick:
            raise ValueError("Invalid quote")
        levels = snapshot.get("reference_levels", [])
        if not isinstance(levels, list) or len(levels) > 100:
            raise ValueError("Invalid levels")
        unique = {}
        for level in levels:
            price = _number(level["price_points"])
            observed = level["asof_ms"]
            evidence = level["evidence_id"]
            if price % tick or type(observed) is not int or not 0 <= stamp - observed <= 120000:
                raise ValueError("Off-grid, stale, or future level")
            if not isinstance(evidence, str) or not evidence:
                raise ValueError("Missing evidence identity")
            unique[price] = evidence
        result = []
        for side, entry in (("buy", ask), ("sell", bid)):
            below = sorted((x for x in unique if x < entry - tick), reverse=True)
            above = sorted(x for x in unique if x > entry + tick)
            stop_levels = below[:2] if side == "buy" else above[:2]
            target_levels = above[:2] if side == "buy" else below[:2]
            for i, structural_stop in enumerate(stop_levels):
                for j, target_reference in enumerate(target_levels):
                    stop = structural_stop - tick if side == "buy" else structural_stop + tick
                    target = target_reference - tick if side == "buy" else target_reference + tick
                    if stop <= 0 or target <= 0:
                        continue
                    result.append({
                        "id": f"{side}_stop{i}_target{j}", "side": side,
                        "entry_points": str(entry), "stop_points": str(stop), "target_points": str(target),
                        "quantity_requested": quantity_requested,
                        "premise": (
                            "Hypothesis to test: recent aggressive buying is accepted at higher prices, or recent selling is absorbed."
                            if side == "buy" else
                            "Hypothesis to test: recent aggressive selling is accepted at lower prices, or recent buying is absorbed."
                        ),
                        "reference_evidence_ids": [unique[structural_stop], unique[target_reference]],
                        "recipe": "experimental_two_structural_levels_one_tick_buffer"
                    })
        return result
    except (KeyError, TypeError, InvalidOperation) as exc:
        raise ValueError("Invalid reference levels") from exc

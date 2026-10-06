"""Finite comparisons of capital policy. No optimizer, orders or profit forecast."""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, DecimalException

from capital_planner import project_stop_capacity
from risk import evaluate_risk


DEFAULT_FRACTIONS = ("0.01", "0.03", "0.05", "0.10", "0.15")
DEFAULT_CAPITAL_BASES = ("session_start_cap", "current_equity")


def _fraction(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)) or len(str(value)) > 64:
        raise ValueError("Invalid risk fraction")
    try:
        fraction = Decimal(str(value))
    except DecimalException as exc:
        raise ValueError("Invalid risk fraction") from exc
    if not fraction.is_finite() or not 0 < fraction <= 1 or abs(fraction.adjusted()) > 12:
        raise ValueError("Risk fraction must be finite and between zero and one")
    return format(fraction, "f")


def compare_risk_policies(config, account, candidate, now_ms, fractions=None,
                          max_attempts=200, *, capital_bases=None):
    """Keep stop/target/costs fixed, compare configured risk fractions and bases.

    Each row calls the existing risk and capital engines. Remaining daily risk,
    drawdown, margin, configured quantity and requested quantity still constrain
    contracts. This does not select an optimal policy, recommend a larger risk,
    or estimate future returns. A live account remains blocked by risk.py.
    """
    if not isinstance(config, dict) or not isinstance(config.get("risk"), dict):
        raise ValueError("Risk configuration required")
    fractions = DEFAULT_FRACTIONS if fractions is None else fractions
    capital_bases = DEFAULT_CAPITAL_BASES if capital_bases is None else capital_bases
    if not isinstance(fractions, (tuple, list)) or not 1 <= len(fractions) <= 20:
        raise ValueError("Provide one to twenty risk fractions")
    if not isinstance(capital_bases, (tuple, list)) or not 1 <= len(capital_bases) <= 2 or any(
        basis not in DEFAULT_CAPITAL_BASES for basis in capital_bases
    ) or len(set(capital_bases)) != len(capital_bases):
        raise ValueError("Invalid capital bases")
    if type(max_attempts) is not int or not 1 <= max_attempts <= 1000:
        raise ValueError("Projection work must be bounded to 1–1000 attempts")
    validated_fractions = [_fraction(fraction) for fraction in fractions]
    if len({Decimal(fraction) for fraction in validated_fractions}) != len(validated_fractions):
        raise ValueError("Duplicate risk fractions")
    rows = []
    for fraction in validated_fractions:
        for basis in capital_bases:
            policy = deepcopy(config)
            policy["risk"].update({"per_trade_fraction": fraction, "capital_basis": basis})
            sizing = evaluate_risk(policy, account, candidate, now_ms)
            projection = project_stop_capacity(policy, account, candidate, now_ms, max_attempts=max_attempts)
            trajectories = {}
            for name, path in projection["trajectories"].items():
                trajectories[name] = {key: deepcopy(path[key]) for key in (
                    "attempts", "initial_equity_brl", "final_equity_brl", "total_planned_loss_brl",
                    "truncated_at_max_attempts", "stop_reasons", "initial_cooldown_wait_ms")}
                trajectories[name]["contracts_after_each_loss"] = [step["contracts"] for step in path["steps"]]
                trajectories[name]["equity_after_each_loss_brl"] = [step["equity_after_brl"] for step in path["steps"]]
            rows.append({"per_trade_fraction": fraction, "capital_basis": basis,
                         "sizing": sizing, "allowed_contracts": sizing["contracts"],
                         "attempts_until_policy_stop": projection["attempts_until_policy_stop"],
                         "attempts_by_financial_budget_ignoring_streak": projection["attempts_by_financial_budget_ignoring_streak"],
                         "trajectories": trajectories})
    return {"schema_version": 1, "status": "POLICY_COMPARISON_RESEARCH", "simulation_only": True,
            "candidate_id": candidate.get("id") if isinstance(candidate, dict) else None,
            "evaluated_at_ms": now_ms, "rows": rows, "ranking": None, "optimal_policy": None,
            "profit_forecast": False, "future_profit_probability": None,
            "projection_max_attempts": max_attempts,
            "fixed_assumptions": {
                "stop_target_and_costs": "unchanged across rows",
                "other_risk_limits": "unchanged; daily risk, drawdown, streak, cooldown, margin and quantity caps still apply",
                "capital_basis": "session_start_cap caps reinvestment at initial session equity; current_equity adapts to realized and unrealized equity",
                "loss_trajectory": "identical planned stop loss each attempt; account and allowed quantity recalculated after losses",
                "larger_risk_fraction": "changes exposure budget; no evidence that it improves expected profit",
                "data": "no empirical trading outcomes supplied; Kelly sizing or expected return cannot be estimated"},
            "caveats": list(projection["caveats"])}

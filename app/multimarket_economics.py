"""Deterministic, gross payoff scenarios and evidence gates for multimarket candidates.

This module does not estimate probabilities, choose position sizes, or place orders.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any


_DECIMAL_TEXT = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
_ALLOWED_ORIGINS = {"synthetic", "backtest", "prospective", "real"}


def _decimal(value: Any, name: str, *, allow_zero: bool = False, allow_negative: bool = False) -> Decimal:
    if not isinstance(value, str) or len(value) > 128 or not _DECIMAL_TEXT.fullmatch(value):
        raise ValueError(f"{name} must be a decimal string of at most 128 characters")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} is not a valid decimal") from exc
    if not number.is_finite() or (number < 0 and not allow_negative) or (number == 0 and not allow_zero):
        raise ValueError(f"{name} must be {'nonnegative' if allow_zero else 'positive'} and finite")
    return number


def _decimal_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _precision(*values: Decimal) -> int:
    significant_digits = sum(len(value.as_tuple().digits) for value in values)
    scale_span = max(value.adjusted() for value in values) - min(value.as_tuple().exponent for value in values) + 1
    return max(64, significant_digits + max(0, scale_span) + 32)


def _empty_payoff(kind: str, missing: list[str], assumptions: list[str]) -> dict[str, Any]:
    return {
        "kind": kind,
        "currency": None,
        "gross_pnl": None,
        "maximum_loss": None,
        "liability": None,
        "missing": missing,
        "assumptions": assumptions,
    }


def payoff(
    kind: str,
    *,
    quantity: str,
    entry_price: str | None = None,
    exit_price: str | None = None,
    side: str = "buy",
    multiplier: str | None = None,
    odds: str | None = None,
    net_payout: str | None = None,
    outcome: str | None = None,
) -> dict[str, Any]:
    """Calculate one gross outcome using exact decimal-string inputs."""
    if not isinstance(kind, str) or not kind:
        raise ValueError("kind is required")
    if kind == "inverse_future":
        return _empty_payoff(
            kind,
            ["unsupported"],
            ["Inverse payoff structure is unsupported; no linear approximation was applied."],
        )
    if kind not in {"spot", "linear_future", "back", "lay", "binary"}:
        raise ValueError("unsupported payoff kind")

    q = _decimal(quantity, "quantity")
    assumptions = ["Scenario gross only; fees, slippage, funding, and probability are not included."]

    if kind in {"spot", "linear_future"}:
        if side not in {"buy", "sell"}:
            raise ValueError("side must be 'buy' or 'sell'")
        if entry_price is None or exit_price is None:
            raise ValueError("entry_price and exit_price are required")
        entry = _decimal(entry_price, "entry_price")
        exit_ = _decimal(exit_price, "exit_price")
        if kind == "linear_future":
            if multiplier is None:
                raise ValueError("linear_future requires an explicit multiplier")
            mult = _decimal(multiplier, "multiplier")
        else:
            mult = _decimal(multiplier, "multiplier") if multiplier is not None else Decimal("1")
        with localcontext() as ctx:
            ctx.prec = _precision(q, entry, exit_, mult)
            gross = q * (exit_ - entry) * mult
            if side == "sell":
                gross = -gross
            maximum_loss = q * entry * mult if kind == "spot" and side == "buy" else None
        if kind == "linear_future":
            assumptions.append("Maximum loss is unknown without an explicit stop or payoff structure.")
        elif side == "sell":
            assumptions.append("Short spot maximum loss is unknown without an inventory and close-out constraint.")
        return {
            "kind": kind,
            "currency": None,
            "gross_pnl": _decimal_text(gross),
            "maximum_loss": _decimal_text(maximum_loss) if maximum_loss is not None else None,
            "liability": None,
            "missing": [],
            "assumptions": assumptions,
        }

    if kind in {"back", "lay"}:
        if odds is None:
            raise ValueError(f"{kind} requires odds")
        odd = _decimal(odds, "odds")
        if odd < 1:
            raise ValueError("odds must be at least 1")
        if outcome not in {"win", "lose", "void"}:
            raise ValueError("outcome must be 'win', 'lose', or 'void'")
        with localcontext() as ctx:
            ctx.prec = _precision(q, odd)
            liability = q * (odd - Decimal("1"))
            if outcome == "void":
                gross = Decimal("0")
            elif kind == "back":
                gross = q * (odd - Decimal("1")) if outcome == "win" else -q
            else:
                gross = -liability if outcome == "win" else q
        maximum_loss = q if kind == "back" else liability
        return {
            "kind": kind,
            "currency": None,
            "gross_pnl": _decimal_text(gross),
            "maximum_loss": _decimal_text(maximum_loss),
            "liability": _decimal_text(liability) if kind == "lay" else None,
            "missing": [],
            "assumptions": assumptions,
        }

    if net_payout is None:
        raise ValueError("binary requires the contracted net_payout")
    payout = _decimal(net_payout, "net_payout", allow_zero=True)
    if outcome not in {"win", "lose", "void"}:
        raise ValueError("outcome must be 'win', 'lose', or 'void'")
    with localcontext() as ctx:
        ctx.prec = _precision(q, payout)
        gross = q * payout if outcome == "win" else (-q if outcome == "lose" else Decimal("0"))
    assumptions.append("net_payout is the contracted net gain per stake unit on win, not a total-return percentage.")
    return {
        "kind": kind,
        "currency": None,
        "gross_pnl": _decimal_text(gross),
        "maximum_loss": _decimal_text(q),
        "liability": None,
        "missing": [],
        "assumptions": assumptions,
    }


def _valid_timestamp(value: Any, as_of_ms: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= as_of_ms


def _valid_source(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 512


def _evidence_gate(
    value: Any,
    *,
    field: str,
    required_status: str,
    as_of_ms: int,
    missing: list[str],
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        missing.append(field)
        return None
    if value.get("status") != required_status:
        missing.append(f"{field}_not_{required_status}")
    if not _valid_source(value.get("source")):
        missing.append(f"{field}_source_missing")
    if not _valid_timestamp(value.get("as_of_ms"), as_of_ms):
        missing.append(f"{field}_timestamp_invalid")
    return value


def _missing_once(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def assess_candidates(candidates: list[dict], *, capital: str, currency: str, as_of_ms: int) -> dict[str, Any]:
    """Apply explicit evidence gates; never rank an unvalidated scenario as a bet."""
    capital_value = _decimal(capital, "capital")
    if not isinstance(currency, str) or not re.fullmatch(r"[A-Z0-9]{3,12}", currency):
        raise ValueError("currency must be an uppercase currency or settlement code")
    if not isinstance(as_of_ms, int) or isinstance(as_of_ms, bool) or as_of_ms < 0:
        raise ValueError("as_of_ms must be a nonnegative integer")
    if not isinstance(candidates, list):
        raise ValueError("candidates must be a list")

    evaluated: list[dict[str, Any]] = []
    admissible: list[str] = []
    global_missing: list[str] = []
    origins: list[str] = []

    for index, candidate in enumerate(candidates):
        missing: list[str] = []
        if not isinstance(candidate, dict):
            evaluated.append({"candidate_id": None, "status": "blocked", "missing": ["candidate_invalid"]})
            global_missing.append("candidate_invalid")
            continue
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id.strip() or len(candidate_id) > 128:
            candidate_id = None
            missing.append("candidate_id_invalid")
        if not _valid_timestamp(candidate.get("as_of_ms"), as_of_ms):
            missing.append("candidate_timestamp_invalid")

        instrument = candidate.get("instrument")
        settlement = instrument.get("settlement_currency") if isinstance(instrument, dict) else None
        if not isinstance(settlement, str) or not re.fullmatch(r"[A-Z0-9]{3,12}", settlement):
            missing.append("settlement_currency_missing")
            settlement = None

        try:
            quantity = _decimal(candidate.get("quantity"), "quantity")
        except ValueError:
            quantity = None
            missing.append("quantity_invalid")

        scenario = candidate.get("payoff")
        gross: Decimal | None = None
        maximum_loss: Decimal | None = None
        if not isinstance(scenario, dict):
            missing.append("payoff_missing")
        else:
            if scenario.get("missing"):
                missing.append("payoff_unsupported")
            try:
                gross = _decimal(scenario.get("gross_pnl"), "gross_pnl", allow_zero=True, allow_negative=True)
            except ValueError:
                missing.append("gross_pnl_missing")
            try:
                maximum_loss = _decimal(scenario.get("maximum_loss"), "maximum_loss", allow_zero=True)
            except ValueError:
                missing.append("maximum_loss_unknown")

        costs = candidate.get("costs")
        if not isinstance(costs, dict):
            missing.append("costs")
            cost_amount = None
        else:
            try:
                cost_amount = _decimal(costs.get("amount"), "costs.amount", allow_zero=True)
            except ValueError:
                cost_amount = None
                missing.append("cost_amount_missing")
            if cost_amount == 0 and costs.get("method") != "explicit_zero":
                missing.append("zero_cost_not_explicit")
            if settlement and costs.get("currency") != settlement:
                missing.append("cost_currency_mismatch")
            for key in ("method", "base"):
                if not _valid_source(costs.get(key)):
                    missing.append(f"cost_{key}_missing")
            if not _valid_source(costs.get("source")):
                missing.append("cost_source_missing")
            if not _valid_timestamp(costs.get("as_of_ms"), as_of_ms):
                missing.append("cost_timestamp_invalid")

        quote = _evidence_gate(candidate.get("executable_quote"), field="executable_quote", required_status="executable", as_of_ms=as_of_ms, missing=missing)
        if quote is not None:
            try:
                _decimal(quote.get("price"), "executable_quote.price")
            except ValueError:
                missing.append("executable_quote_price_missing")
            quote_time = quote.get("as_of_ms")
            max_age = quote.get("max_age_ms")
            if not isinstance(max_age, int) or isinstance(max_age, bool) or max_age < 0:
                missing.append("executable_quote_age_policy_missing")
            elif _valid_timestamp(quote_time, as_of_ms) and as_of_ms - quote_time > max_age:
                missing.append("executable_quote_stale")

        liquidity = _evidence_gate(candidate.get("liquidity"), field="liquidity", required_status="sufficient", as_of_ms=as_of_ms, missing=missing)
        if liquidity is not None:
            try:
                liquid_quantity = _decimal(liquidity.get("max_quantity"), "liquidity.max_quantity")
                if quantity is not None and liquid_quantity < quantity:
                    missing.append("liquidity_below_quantity")
            except ValueError:
                missing.append("liquidity_quantity_missing")

        risk = _evidence_gate(candidate.get("risk_mandate"), field="risk_mandate", required_status="approved", as_of_ms=as_of_ms, missing=missing)
        fx_rate: Decimal | None = None
        if settlement and settlement != currency:
            fx = candidate.get("fx")
            if not isinstance(fx, dict):
                missing.append("fx")
            else:
                if fx.get("pair") != f"{settlement}/{currency}":
                    missing.append("fx_pair_mismatch")
                if not _valid_source(fx.get("source")):
                    missing.append("fx_source_missing")
                fx_time = fx.get("as_of_ms")
                if not _valid_timestamp(fx_time, as_of_ms):
                    missing.append("fx_timestamp_invalid")
                try:
                    fx_rate = _decimal(fx.get("rate"), "fx.rate")
                except ValueError:
                    missing.append("fx_rate_missing")
                max_age = fx.get("max_age_ms")
                if not isinstance(max_age, int) or isinstance(max_age, bool) or max_age < 0:
                    missing.append("fx_age_policy_missing")
                elif _valid_timestamp(fx_time, as_of_ms) and as_of_ms - fx_time > max_age:
                    missing.append("fx_stale")
        if risk is not None:
            try:
                mandate_loss = _decimal(risk.get("max_loss"), "risk_mandate.max_loss", allow_zero=True)
                if settlement and risk.get("currency") != settlement:
                    missing.append("risk_currency_mismatch")
                if maximum_loss is not None and maximum_loss > mandate_loss:
                    missing.append("risk_mandate_exceeded")
                if fx_rate is not None:
                    with localcontext() as ctx:
                        ctx.prec = _precision(capital_value, fx_rate, mandate_loss)
                        if mandate_loss * fx_rate > capital_value:
                            missing.append("capital_limit_exceeded")
                elif settlement == currency and mandate_loss > capital_value:
                    missing.append("capital_limit_exceeded")
            except ValueError:
                missing.append("risk_limit_missing")

        _evidence_gate(candidate.get("product_gate"), field="product_gate", required_status="approved", as_of_ms=as_of_ms, missing=missing)
        _evidence_gate(candidate.get("authorization_gate"), field="authorization_gate", required_status="approved", as_of_ms=as_of_ms, missing=missing)

        coverage = candidate.get("coverage")
        coverage_value = _evidence_gate(coverage, field="coverage", required_status="complete", as_of_ms=as_of_ms, missing=missing)
        origin = coverage_value.get("origin") if coverage_value else None
        if origin not in _ALLOWED_ORIGINS:
            missing.append("coverage_origin_unknown")
        elif origin != "synthetic":
            missing.append("non_synthetic_scenario_comparison_disabled")

        if coverage_value is not None and coverage_value.get("full_tape") is not True:
            missing.append("coverage_partial")

        if not missing and origin == "synthetic" and settlement and isinstance(costs, dict) and costs.get("currency") == settlement and gross is not None and cost_amount is not None:
            with localcontext() as ctx:
                ctx.prec = _precision(gross, cost_amount, fx_rate or Decimal("1"))
                scenario_net = gross - cost_amount
                net_capital = scenario_net * fx_rate if fx_rate is not None else scenario_net
        else:
            scenario_net = None
            net_capital = None

        missing = _missing_once(missing)
        status = "blocked" if missing else "admissible_scenario"
        evaluated.append({
            "candidate_id": candidate_id,
            "status": status,
            "origin": origin if origin in _ALLOWED_ORIGINS else None,
            "currency": settlement,
            "scenario_net_pnl": _decimal_text(scenario_net) if scenario_net is not None else None,
            "scenario_net_pnl_capital": _decimal_text(net_capital) if net_capital is not None else None,
            "missing": missing,
        })
        if not missing and candidate_id is not None:
            admissible.append(candidate_id)
            origins.append(origin)
        else:
            global_missing.extend(missing)

    global_missing = _missing_once(global_missing)
    if not admissible:
        status = "not_evaluable"
    elif all(origin == "synthetic" for origin in origins) and len(admissible) == len(origins):
        status = "scenario_comparison_only"
    else:
        status = "admissible_unranked"
        global_missing.append("statistical_validation_pending")
    wait = {"candidate_id": None, "quantity": "0", "action": "wait", "always_available": True}
    return {
        "status": status,
        "candidates": evaluated,
        "admissible": admissible,
        "missing": _missing_once(global_missing),
        "wait": wait,
        "selected": wait.copy(),
        "profit_probability": None,
        "target_probability": None,
        "ruin_probability": None,
    }


def _has_reference(value: Any) -> bool:
    return isinstance(value, dict) and _valid_source(value.get("source")) and _valid_timestamp(value.get("as_of_ms"), 2**63 - 1)


def evaluation_report(*, dataset: dict | None = None, method: dict | None = None, results: dict | None = None) -> dict[str, Any]:
    """Describe evaluation evidence while keeping AC-07 pending until independent acceptance."""
    missing: list[str] = []
    if dataset is not None and not isinstance(dataset, dict):
        missing.append("dataset_invalid")
        dataset = None
    if method is not None and not isinstance(method, dict):
        missing.append("method_invalid")
        method = None
    if results is not None and not isinstance(results, dict):
        missing.append("results_invalid")
        results = None

    dataset = dataset or {}
    method = method or {}
    results = results or {}
    declared_origins = [
        value for value in (dataset.get("origin"), method.get("result_type"), results.get("result_type"))
        if value is not None
    ]
    recognized = [value for value in declared_origins if isinstance(value, str) and value in _ALLOWED_ORIGINS]
    if len(recognized) != len(declared_origins) and declared_origins:
        missing.append("result_origin_unknown")
    if len(set(recognized)) > 1:
        result_type = "protocol_only"
        missing.append("conflicting_result_origins")
    else:
        result_type = recognized[0] if recognized and len(recognized) == len(declared_origins) else "protocol_only"

    sample_size = results.get("sample_size", 0)
    if not isinstance(sample_size, int) or isinstance(sample_size, bool) or sample_size < 0:
        sample_size = 0
        missing.append("sample_size_invalid")
    if sample_size == 0:
        missing.append("minimum_sample_evidence")

    chronology = None
    if method.get("chronological_split") is True and _valid_source(method.get("split_reference")):
        chronology = {"status": "declared"}
    else:
        missing.append("chronological_split")

    overlap = method.get("overlap_assessed")
    if overlap is not True:
        missing.append("overlap_assessment")
    elif not isinstance(method.get("overlap_exists"), bool):
        missing.append("overlap_presence_status")
    elif method.get("overlap_exists") and method.get("purge_embargo") is not True:
        missing.append("purge_embargo")

    if method.get("multiple_comparisons_addressed") is not True:
        missing.append("multiple_comparisons")

    costs = None
    if not (_has_reference(method.get("cost_evidence")) and _has_reference(method.get("execution_evidence"))):
        missing.append("cost_execution_evidence")
    else:
        costs = {"status": "declared"}

    calibration_data = results.get("calibration")
    calibration = None
    if isinstance(calibration_data, dict) and all(key in calibration_data for key in ("brier", "logloss")):
        try:
            _decimal(calibration_data["brier"], "calibration.brier", allow_zero=True)
            _decimal(calibration_data["logloss"], "calibration.logloss", allow_zero=True)
            calibration = {"status": "declared"}
        except ValueError:
            missing.append("calibration_metrics_invalid")
    else:
        missing.append("calibration_brier_logloss")

    interval_evidence = results.get("interval_evidence")
    intervals = {"status": "declared"} if _has_reference(interval_evidence) and _valid_source(interval_evidence.get("method")) else None
    if intervals is None:
        missing.append("temporal_uncertainty_intervals")

    drawdown_data = results.get("drawdown_evidence")
    drawdown = {"status": "declared"} if _has_reference(drawdown_data) and "maximum_drawdown" in drawdown_data else None
    if drawdown is None:
        missing.append("bankroll_drawdown_evidence")

    if not _valid_source(method.get("acceptance_criteria_ref")):
        missing.append("independent_acceptance_criteria")
    # Supplied probabilities and contextual/JEV confidence are deliberately not consumed.
    missing.append("AC-07_pending")
    return {
        "status": "pending",
        "sample_size": sample_size,
        "chronology": chronology,
        "costs": costs,
        "calibration": calibration,
        "intervals": intervals,
        "drawdown": drawdown,
        "target_probability": None,
        "ruin_probability": None,
        "missing": _missing_once(missing),
        "result_type": result_type,
        "ac07_status": "pending",
        "protocol": [
            "causal_chronological_split",
            "purge_and_embargo_overlapping_samples",
            "account_for_multiple_comparisons",
            "brier_and_logloss_calibration",
            "include_fees_slippage_funding_and_execution",
            "measure_bankroll_drawdown_target_and_ruin",
            "temporal_uncertainty_intervals",
            "independent_acceptance_criteria",
        ],
    }

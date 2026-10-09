from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR
from typing import Any, Mapping, Sequence

from .contracts import InstrumentSpec


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_required")
    return value.strip()


def _decimal(value: Any, field: str, *, positive: bool = False, nonnegative: bool = False) -> Decimal:
    if isinstance(value, (bool, float)) or not isinstance(value, Decimal):
        raise TypeError(f"{field}_must_be_decimal")
    if not value.is_finite():
        raise ValueError(f"{field}_must_be_finite")
    if positive and value <= 0:
        raise ValueError(f"{field}_must_be_positive")
    if nonnegative and value < 0:
        raise ValueError(f"{field}_must_be_nonnegative")
    return value


def _decimal_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    rendered = format(value, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


@dataclass(frozen=True, kw_only=True)
class RiskPolicy:
    currency: str
    max_quantity: Decimal
    max_cash_risk: Decimal
    max_candidates: int = 256
    version: str = "mm-risk-v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "currency", _text(self.currency, "currency").upper())
        object.__setattr__(self, "max_quantity", _decimal(self.max_quantity, "max_quantity", positive=True))
        object.__setattr__(self, "max_cash_risk", _decimal(self.max_cash_risk, "max_cash_risk", nonnegative=True))
        if isinstance(self.max_candidates, bool) or not isinstance(self.max_candidates, int) or self.max_candidates < 1:
            raise ValueError("max_candidates_must_be_positive_integer")
        object.__setattr__(self, "version", _text(self.version, "version"))


def _zero(reason: str, policy: RiskPolicy) -> dict[str, Any]:
    return {
        "action": "wait",
        "reason": reason,
        "quantity": "0",
        "quantity_recommended": False,
        "policy_version": policy.version,
        "profit_probability": None,
        "estimated_cost": None,
        "max_loss": None,
        "gross_profit": None,
        "net_profit": None,
    }


def _tick_aligned(value: Decimal, tick: Decimal) -> bool:
    return value % tick == 0


def _floor_step(value: Decimal, step: Decimal) -> Decimal:
    return (value / step).to_integral_value(rounding=ROUND_FLOOR) * step


def _ceil_step(value: Decimal, step: Decimal) -> Decimal:
    return (value / step).to_integral_value(rounding=ROUND_CEILING) * step


def _account_blocker(account: Any, currency: str, *, require_currency_balance: bool) -> str | None:
    if not isinstance(account, Mapping) or not isinstance(account.get("account_id"), str) or not account.get("account_id", "").strip():
        return "account_unavailable"
    if account.get("status") != "reconciled":
        return "account_not_reconciled"
    revision = account.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        return "account_revision_unavailable"
    age = account.get("age_ms")
    if age is not None and (isinstance(age, bool) or not isinstance(age, int) or age < 0 or age > 60_000):
        return "account_not_reconciled"
    balances = account.get("balances")
    positions = account.get("positions")
    if not isinstance(balances, Mapping) or not isinstance(positions, Mapping):
        return "account_unavailable"
    if require_currency_balance and currency not in balances:
        return "account_currency_unavailable"
    if currency in balances:
        try:
            balance = Decimal(balances[currency])
        except (InvalidOperation, TypeError, ValueError):
            return "account_balance_invalid"
        if not balance.is_finite() or balance < 0:
            return "account_balance_invalid"
    return None


def _cost_values(costs: Any, currency: str) -> tuple[Decimal, Decimal] | str:
    if not isinstance(costs, Mapping):
        return "costs_unavailable"
    if costs.get("verified") is not True:
        return "costs_unverified"
    cost_currency = costs.get("currency")
    if not isinstance(cost_currency, str) or not cost_currency.strip():
        return "costs_unavailable"
    if cost_currency.strip().upper() != currency:
        return "currency_mismatch"
    try:
        fee_rate = _decimal(costs.get("fee_rate"), "fee_rate", nonnegative=True)
        slippage = _decimal(costs.get("slippage"), "slippage", nonnegative=True)
    except (TypeError, ValueError):
        return "costs_unavailable"
    return fee_rate, slippage


def _model_gate(gate: Any, spec: InstrumentSpec) -> tuple[Decimal | None, str]:
    if not isinstance(gate, Mapping) or gate.get("approved") is not True:
        return None, "model_not_approved"
    if any(
        gate.get(field) != expected
        for field, expected in (
            ("instrument_id", spec.instrument_id),
            ("venue", spec.venue),
            ("metadata_version", spec.metadata_version),
        )
    ):
        return None, "model_scope_mismatch"
    for field in ("horizon", "origin", "evidence_id"):
        if not isinstance(gate.get(field), str) or not gate[field].strip():
            return None, "model_evidence_incomplete"
    evaluation = gate.get("temporal_evaluation")
    if not isinstance(evaluation, Mapping) or evaluation.get("no_leakage") is not True:
        return None, "model_evidence_incomplete"
    comparators = evaluation.get("comparators")
    required = {"rules", "context", "quantitative", "jev"}
    if not isinstance(comparators, (list, tuple, set)) or not required.issubset(comparators):
        return None, "model_evidence_incomplete"
    try:
        probability = _decimal(gate.get("profit_probability"), "profit_probability", nonnegative=True)
    except (TypeError, ValueError):
        return None, "model_evidence_incomplete"
    if probability > 1:
        return None, "model_evidence_incomplete"
    return probability, "approved_model"


def _position_quantity(account: Mapping[str, Any], instrument_id: str) -> Decimal | None:
    positions = account.get("positions")
    if not isinstance(positions, Mapping):
        return None
    position = positions.get(instrument_id)
    if position is None:
        return Decimal(0)
    raw_quantity = position.get("quantity") if isinstance(position, Mapping) else position
    try:
        result = Decimal(raw_quantity)
    except (InvalidOperation, TypeError, ValueError):
        return None
    return result if result.is_finite() else None


def _candidate_result(
    quantity: Decimal,
    *,
    reason: str,
    policy: RiskPolicy,
    probability: Decimal | None,
    estimated_cost: Decimal | None,
    max_loss: Decimal | None,
    gross_profit: Decimal | None,
    net_profit: Decimal | None,
    recommended: bool = False,
) -> dict[str, Any]:
    return {
        "action": "candidate" if recommended else "wait",
        "reason": reason,
        "quantity": _decimal_text(quantity),
        "quantity_recommended": recommended,
        "policy_version": policy.version,
        "profit_probability": _decimal_text(probability) if probability is not None else None,
        "estimated_cost": _decimal_text(estimated_cost) if estimated_cost is not None else None,
        "max_loss": _decimal_text(max_loss) if max_loss is not None else None,
        "gross_profit": _decimal_text(gross_profit) if gross_profit is not None else None,
        "net_profit": _decimal_text(net_profit) if net_profit is not None else None,
    }


def evaluate_quantities(
    spec: InstrumentSpec,
    account: Mapping[str, Any] | None,
    costs: Mapping[str, Any] | None,
    *,
    policy: RiskPolicy,
    entry_price: Decimal,
    stop_price: Decimal,
    target_price: Decimal | None = None,
    side: str = "buy",
    quantities: Sequence[Decimal] | None = None,
    model_gate: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Evaluate spot quantities without assuming unknown costs, funding, or model quality.

    Costs use per-side `fee_rate` and absolute per-unit `slippage`, both verified
    Decimal values. A model gate is accepted only for an exact instrument, venue,
    and metadata version with an identified horizon/origin/evidence and temporal
    evaluation that includes all four frozen comparators.
    """
    if not isinstance(spec, InstrumentSpec):
        raise TypeError("instrument_spec_required")
    if not isinstance(policy, RiskPolicy):
        raise TypeError("risk_policy_required")
    entry = _decimal(entry_price, "entry_price", positive=True)
    stop = _decimal(stop_price, "stop_price", positive=True)
    target = None if target_price is None else _decimal(target_price, "target_price", positive=True)
    normalized_side = _text(side, "side").casefold()
    if normalized_side not in {"buy", "sell"}:
        raise ValueError("invalid_side")

    if not spec.constraints_verified or any(
        getattr(spec, name) is None
        for name in ("price_tick", "quantity_step", "quantity_min", "minimum_notional", "contract_multiplier", "quote_currency", "settlement_currency")
    ):
        return [_zero("instrument_constraints_unverified", policy)]
    if spec.segment.casefold() != "spot":
        return [_zero("segment_not_supported", policy)]
    if spec.quote_currency.upper() != policy.currency or spec.settlement_currency.upper() != policy.currency:
        return [_zero("currency_mismatch", policy)]
    if not _tick_aligned(entry, spec.price_tick) or not _tick_aligned(stop, spec.price_tick) or (target is not None and not _tick_aligned(target, spec.price_tick)):
        return [_zero("price_tick_mismatch", policy)]
    if normalized_side == "buy" and stop >= entry:
        return [_zero("stop_not_loss_side", policy)]
    if normalized_side == "sell" and stop <= entry:
        return [_zero("stop_not_loss_side", policy)]
    if target is not None and ((normalized_side == "buy" and target <= entry) or (normalized_side == "sell" and target >= entry)):
        return [_zero("target_not_profit_side", policy)]

    account_reason = _account_blocker(account, policy.currency, require_currency_balance=normalized_side == "buy")
    if account_reason is not None:
        return [_zero(account_reason, policy)]
    cost_values = _cost_values(costs, policy.currency)
    if isinstance(cost_values, str):
        return [_zero(cost_values, policy)]
    fee_rate, slippage = cost_values
    assert account is not None  # established by _account_blocker
    balance = Decimal(account["balances"].get(policy.currency, "0"))

    multiplier = spec.contract_multiplier
    step = spec.quantity_step
    minimum_quantity = spec.quantity_min
    minimum_notional = spec.minimum_notional
    loss_per_unit = abs(entry - stop) * multiplier + (entry + stop) * multiplier * fee_rate + (Decimal(2) * slippage * multiplier)
    entry_cash_per_unit = entry * multiplier * (Decimal(1) + fee_rate) + slippage * multiplier
    max_by_risk = _floor_step(policy.max_cash_risk / loss_per_unit, step) if loss_per_unit > 0 else Decimal(0)
    max_by_cash = (
        _floor_step(balance / entry_cash_per_unit, step)
        if normalized_side == "buy" and entry_cash_per_unit > 0
        else policy.max_quantity
    )
    max_allowed = min(policy.max_quantity, max_by_risk, max_by_cash)
    position_quantity = _position_quantity(account, spec.instrument_id) if normalized_side == "sell" else None
    if normalized_side == "sell":
        if position_quantity is None or position_quantity < 0:
            return [_zero("account_position_invalid", policy)]
        max_allowed = min(max_allowed, _floor_step(position_quantity, step))

    probability, model_reason = _model_gate(model_gate, spec)
    results = [_zero("zero_quantity_baseline", policy)]

    if quantities is None:
        min_notional_quantity = minimum_notional / (entry * multiplier)
        lower = max(_ceil_step(minimum_quantity, step), _ceil_step(min_notional_quantity, step))
        if lower <= 0:
            lower = step
        if max_allowed < lower:
            return results
        count = int(((max_allowed - lower) / step).to_integral_value(rounding=ROUND_FLOOR)) + 1
        candidate_values = [lower + (step * index) for index in range(min(count, policy.max_candidates))]
    else:
        if isinstance(quantities, (str, bytes)) or not isinstance(quantities, Sequence):
            raise TypeError("quantities_must_be_sequence")
        candidate_values = []
        for quantity in quantities:
            candidate = _decimal(quantity, "quantity", positive=True)
            candidate_values.append(candidate)
        if len(candidate_values) > policy.max_candidates:
            candidate_values = candidate_values[:policy.max_candidates]

    for quantity in candidate_values:
        reason: str | None = None
        if quantity % step != 0:
            reason = "quantity_step_mismatch"
        elif quantity < minimum_quantity:
            reason = "quantity_below_minimum"
        elif quantity > policy.max_quantity:
            reason = "quantity_limit"
        elif quantity > max_by_risk:
            reason = "cash_risk_limit"
        elif quantity > max_by_cash:
            reason = "insufficient_balance"
        elif entry * multiplier * quantity < minimum_notional:
            reason = "minimum_notional"
        elif normalized_side == "sell" and (position_quantity is None or quantity > position_quantity):
            reason = "position_limit"

        if reason is not None:
            results.append(_candidate_result(quantity, reason=reason, policy=policy, probability=None, estimated_cost=None, max_loss=None, gross_profit=None, net_profit=None))
            continue

        total_cost = ((entry + stop) * multiplier * fee_rate + Decimal(2) * slippage * multiplier) * quantity
        max_loss = abs(entry - stop) * multiplier * quantity + total_cost
        gross_profit = abs(target - entry) * multiplier * quantity if target is not None else None
        net_profit: Decimal | None = None
        recommended = False
        if probability is None:
            reason = model_reason
        elif target is None:
            reason = "target_unavailable"
        else:
            expected_gross = (probability * gross_profit) - ((Decimal(1) - probability) * (abs(entry - stop) * multiplier * quantity))
            net_profit = expected_gross - total_cost
            recommended = net_profit > 0
            reason = "positive_expected_value" if recommended else "expected_value_nonpositive"
        results.append(
            _candidate_result(
                quantity,
                reason=reason,
                policy=policy,
                probability=probability,
                estimated_cost=total_cost,
                max_loss=max_loss,
                gross_profit=gross_profit,
                net_profit=net_profit,
                recommended=recommended,
            )
        )
    return results

"""Deterministic risk filter for offline simulation; never sends orders.

Decimal results are returned as strings (unknown calculations as None).
The account represents one session without deposits/withdrawals: current equity
must equal session-start equity plus realized net PnL plus unrealized PnL.
Config limits are research inputs, not recommendations or a predictive edge.
"""
from __future__ import annotations

from decimal import Decimal, DecimalException, localcontext
from typing import Any


ZERO = Decimal("0")


def _number(value: Any, *, minimum: Decimal | None = None,
            positive: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("Expected a finite number")
    # Bound input size/exponents so malformed snapshots cannot exhaust arithmetic.
    if len(str(value)) > 128:
        raise ValueError("Numeric input too large")
    answer = Decimal(str(value))
    if not answer.is_finite() or abs(answer.adjusted()) > 30:
        raise ValueError("Expected a finite number of supported magnitude")
    if positive and answer <= 0:
        raise ValueError("Expected a positive number")
    if minimum is not None and answer < minimum:
        raise ValueError("Number below minimum")
    return answer


def _integer(value: Any, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum or value > 10**18:
        raise ValueError("Expected an integer in range")
    return value


def _text(value: Decimal) -> str:
    result = format(value, "f")
    return result.rstrip("0").rstrip(".") if "." in result else result


def evaluate_risk(config: dict, account: dict, candidate: dict, now_ms: int) -> dict:
    """Return ALLOW_SIMULATION or BLOCK; no input is mutated.

    Quantity is the minimum of the requested quantity, configured cap, affordable
    stop risk and available margin. Stops are never moved to fit an account.
    The default capital basis caps reinvestment at session-start equity. The
    optional current_equity basis reinvests gains and reduces size after losses.
    Daily equity floors and peak drawdown floors can further constrain the size.
    """
    result = {
        "status": "BLOCK", "reasons": [], "contracts": 0,
        "risk_budget_brl": "0", "risk_per_contract_brl": None,
        "net_reward_per_contract_brl": None, "net_reward_risk": None,
        "margin_per_contract_brl": None,
        "equity_basis_brl": None, "daily_floor_brl": None,
        "drawdown_floor_brl": None,
        "margin_sizing_includes_stop_reserve": False,
        "available_risk_capacity_brl": "0",
    }

    def block(code: str) -> dict:
        result["reasons"].append(code)
        return result

    if not isinstance(config, dict) or config.get("mode") != "simulation":
        return block("SIMULATION_ONLY")
    try:
        _integer(now_ms)
    except ValueError:
        return block("INVALID_CLOCK")

    try:
        instrument, policy, costs = config["instrument"], config["risk"], config["costs"]
        _number(config["capital_initial_brl"], positive=True)
        point_value = _number(instrument["point_value_brl"], positive=True)
        tick = _number(instrument["tick_points"], positive=True)
        exchange_margin = _number(instrument["exchange_min_margin_brl"], positive=True)
        fraction = _number(policy["per_trade_fraction"], positive=True)
        daily_fraction = _number(policy["daily_loss_fraction"], positive=True)
        if fraction > 1 or daily_fraction > 1:
            raise ValueError("Risk fractions must not exceed one")
        max_contracts = _integer(policy["max_contracts"], 1)
        max_losses = _integer(policy["max_consecutive_losses"], 1)
        cooldown = _integer(policy["cooldown_after_loss_ms"])
        max_age = _integer(policy["max_account_age_ms"])
        minimum_rr = _number(policy["min_net_reward_risk"], positive=True)
        buffer = _number(policy["cash_buffer_brl"], minimum=ZERO)
        capital_basis = policy.get("capital_basis", "session_start_cap")
        daily_mode = policy.get("daily_budget_mode", "loss_only")
        joint_margin = policy.get("reserve_planned_loss_beside_margin", False)
        max_drawdown = policy.get("max_peak_drawdown_fraction")
        if capital_basis not in ("session_start_cap", "current_equity"):
            raise ValueError("Invalid capital basis")
        if daily_mode not in ("loss_only", "equity_floor") or type(joint_margin) is not bool:
            raise ValueError("Invalid daily budget or margin mode")
        if max_drawdown is not None:
            max_drawdown = _number(max_drawdown, positive=True)
            if max_drawdown > 1:
                raise ValueError("Drawdown fraction must not exceed one")
        fees = _number(costs["round_trip_fees_brl_per_contract"], minimum=ZERO)
        slippage_points = _number(costs["slippage_points_round_trip"], minimum=ZERO)
        if type(costs["illustrative_only"]) is not bool:
            raise ValueError("Cost provenance must be explicit")
    except (KeyError, TypeError, ValueError, DecimalException):
        return block("INVALID_CONFIG")
    result["margin_sizing_includes_stop_reserve"] = joint_margin

    if not isinstance(account, dict):
        return block("INVALID_ACCOUNT")
    if account.get("environment") != "simulated":
        return block("SIMULATED_ACCOUNT_REQUIRED")
    if account.get("reconciled") is not True:
        return block("ACCOUNT_NOT_RECONCILED")
    try:
        asof = _integer(account["asof_ms"])
        start = _number(account["start_equity_brl"], positive=True)
        equity = _number(account["equity_brl"])
        realized = _number(account["realized_pnl_net_brl"])
        unrealized = _number(account["unrealized_pnl_brl"])
        reserved = _number(account["reserved_risk_brl"], minimum=ZERO)
        available_margin = _number(account["available_margin_brl"], minimum=ZERO)
        broker_margin = _number(account["broker_margin_brl_per_contract"], positive=True)
        open_contracts = _integer(account["open_contracts"])
        pending = _integer(account["pending_entry_contracts"])
        losses = _integer(account["consecutive_losses"])
        last_loss = account["last_loss_ms"]
        if last_loss is not None:
            _integer(last_loss)
            if last_loss > now_ms or last_loss > asof:
                raise ValueError("Loss timestamp is in the future")
        elif losses:
            raise ValueError("Missing last-loss timestamp")
    except (KeyError, TypeError, ValueError, DecimalException):
        return block("INVALID_ACCOUNT")

    if not 0 <= now_ms - asof <= max_age:
        return block("STALE_OR_FUTURE_ACCOUNT")
    peak = None
    if max_drawdown is not None:
        try:
            peak = _number(account["peak_equity_brl"], positive=True)
            if peak < max(start, equity):
                raise ValueError("Peak is below observed equity")
        except (KeyError, TypeError, ValueError, DecimalException):
            return block("INVALID_PEAK_EQUITY")

    try:
        if not isinstance(candidate, dict) or not isinstance(candidate["id"], str) or not candidate["id"].strip():
            raise ValueError("Missing candidate ID")
        side = candidate["side"]
        if side not in ("buy", "sell"):
            raise ValueError("Invalid side")
        entry = _number(candidate["entry_points"], positive=True)
        stop = _number(candidate["stop_points"], positive=True)
        target = _number(candidate["target_points"], positive=True)
        requested = _integer(candidate.get("quantity_requested", 1), 1)
    except (KeyError, TypeError, ValueError, DecimalException):
        return block("INVALID_CANDIDATE")

    try:
        with localcontext() as context:
            context.prec = 512
            if equity != start + realized + unrealized:
                return block("ACCOUNT_EQUITY_MISMATCH")
            if any(price % tick != 0 for price in (entry, stop, target)):
                return block("PRICE_NOT_ON_TICK")
            if not (stop < entry < target if side == "buy" else target < entry < stop):
                return block("INVALID_STOP_OR_TARGET_SIDE")

            equity_basis = max(ZERO, equity if capital_basis == "current_equity" else min(start, equity))
            per_trade = equity_basis * fraction
            loss_limit = start * daily_fraction
            daily_floor = start - loss_limit
            net_loss = max(ZERO, -(realized + unrealized))
            if daily_mode == "equity_floor":
                daily_remaining = max(ZERO, equity - daily_floor - reserved)
            else:
                daily_remaining = max(ZERO, loss_limit - net_loss - reserved)
            drawdown_floor = None
            capacity = daily_remaining
            if max_drawdown is not None:
                drawdown_floor = peak * (1 - max_drawdown)
                drawdown_remaining = max(ZERO, equity - drawdown_floor - reserved)
                # The same reserved risk is deducted within each alternative cap,
                # never added twice when selecting the tightest available cap.
                capacity = min(capacity, drawdown_remaining)
            budget = min(per_trade, capacity)
            transaction_cost = fees + slippage_points * point_value
            unit_risk = abs(entry - stop) * point_value + transaction_cost
            net_reward = abs(target - entry) * point_value - transaction_cost
            # Ratio is informational. Admission compares exact cross-products.
            with localcontext() as display_context:
                display_context.prec = 28
                ratio = net_reward / unit_risk
            margin = max(exchange_margin, broker_margin)
            margin_budget = max(ZERO, min(available_margin, equity) - buffer)

            result.update({
                "risk_budget_brl": _text(budget),
                "risk_per_contract_brl": _text(unit_risk),
                "net_reward_per_contract_brl": _text(net_reward),
                "net_reward_risk": _text(ratio),
                "margin_per_contract_brl": _text(margin),
                "equity_basis_brl": _text(equity_basis),
                "daily_floor_brl": _text(daily_floor),
                "drawdown_floor_brl": _text(drawdown_floor) if drawdown_floor is not None else None,
                "available_risk_capacity_brl": _text(capacity),
            })
            if equity <= 0:
                block("CAPITAL_EXHAUSTED")
            if open_contracts or pending:
                block("EXISTING_POSITION_OR_PENDING_ENTRY")
            if equity <= daily_floor:
                block("DAILY_LOSS_LIMIT_REACHED")
            if drawdown_floor is not None and equity <= drawdown_floor:
                block("PEAK_DRAWDOWN_LIMIT_REACHED")
            if losses >= max_losses:
                block("CONSECUTIVE_LOSS_LIMIT_REACHED")
            if last_loss is not None and now_ms - last_loss < cooldown:
                block("LOSS_COOLDOWN_ACTIVE")
            if budget <= 0:
                block("RISK_BUDGET_EXHAUSTED")
            if net_reward <= 0 or net_reward < minimum_rr * unit_risk:
                block("NET_REWARD_RISK_TOO_LOW")

            risk_quantity = int(budget // unit_risk)
            margin_requirement = margin + unit_risk if joint_margin else margin
            margin_quantity = int(margin_budget // margin_requirement)
            if risk_quantity == 0 and budget > 0:
                block("STOP_RISK_EXCEEDS_BUDGET")
            if margin_quantity == 0:
                block("INSUFFICIENT_MARGIN_AFTER_BUFFER")
            if not result["reasons"]:
                result["contracts"] = min(requested, max_contracts, risk_quantity, margin_quantity)
                result["status"] = "ALLOW_SIMULATION"
            return result
    except (DecimalException, ValueError, OverflowError):
        return block("INVALID_ARITHMETIC")

"""Hypothetical capacity for repeated, identical planned stops.

This is an accounting projection using the deterministic risk engine, not a
forecast, win probability, recovery plan, or assurance that capital lasts this
long in a real market. The candidate's price geometry and configured costs stay
constant. Only the simulated account and reference clock change after a loss.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, DecimalException, localcontext

from risk import evaluate_risk


ZERO = Decimal("0")
MAX_PROJECTION_ATTEMPTS = 10_000

CAVEATS = [
    "Projeção hipotética de stops consecutivos planejados; não prevê resultados, taxa de acerto, lucro ou recuperação de perdas.",
    "Cada tentativa pressupõe novamente a mesma distância de stop e os mesmos custos. A existência de novas oportunidades não foi prevista.",
    "O lote é recalculado pelo motor de risco após cada perda; não aumenta para recuperar prejuízo.",
    "A trajetória real_policy respeita todos os limites configurados. A trajetória budget_only_ignoring_streak_projection ignora somente o limite de perdas consecutivas e serve apenas para diagnóstico.",
    "O relógio é hipotético: os intervalos de cooldown são respeitados como pausas, sem prever duração de operações, horários de novos sinais ou término do pregão.",
    "Slippage, gaps, liquidez, custos reais, margens adicionais e zeragem compulsória podem reduzir a capacidade projetada. O stop e o depósito não garantem um limite máximo de perda.",
    "As contagens são específicas deste candidato e desta política, com margem liberada após cada encerramento, sem depósitos, retiradas ou novas posições simultâneas.",
    "Quando truncated_at_max_attempts é verdadeiro, a contagem é somente o trecho calculado, não a capacidade total.",
]


def _money(value: Decimal) -> str:
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _empty_trajectory(label: str, sizing: dict, reason: str | None = None) -> dict:
    return {
        "label": label,
        "ignores_consecutive_loss_limit": label == "budget_only_ignoring_streak_projection",
        "attempts": 0,
        "total_planned_loss_brl": "0",
        "initial_equity_brl": None,
        "final_equity_brl": None,
        "final_available_margin_brl": None,
        "initial_cooldown_wait_ms": 0,
        "reference_clock_end_ms": None,
        "truncated_at_max_attempts": False,
        "stop_reasons": [reason] if reason else list(sizing.get("reasons", [])),
        "next_sizing": deepcopy(sizing),
        "steps": [],
    }


def _project(config: dict, account: dict, candidate: dict, now_ms: int,
             max_attempts: int, *, ignore_streak: bool) -> dict:
    label = "budget_only_ignoring_streak_projection" if ignore_streak else "real_policy"
    policy_config = deepcopy(config)
    simulated = deepcopy(account)
    if ignore_streak and isinstance(policy_config, dict) and isinstance(policy_config.get("risk"), dict):
        policy_config["risk"]["max_consecutive_losses"] = 10**9
    sizing = evaluate_risk(policy_config, simulated, candidate, now_ms)
    trajectory = _empty_trajectory(label, sizing)
    if sizing["status"] != "ALLOW_SIMULATION" and set(sizing.get("reasons", [])) != {"LOSS_COOLDOWN_ACTIVE"}:
        # The risk engine exposes this field only after validating account
        # arithmetic. A financial block leaves the known balance unchanged.
        if sizing.get("equity_basis_brl") is not None:
            trajectory["initial_equity_brl"] = _money(Decimal(str(simulated["equity_brl"])))
            trajectory["final_equity_brl"] = trajectory["initial_equity_brl"]
            trajectory["final_available_margin_brl"] = _money(Decimal(str(simulated["available_margin_brl"])))
            trajectory["reference_clock_end_ms"] = now_ms
        return trajectory

    try:
        with localcontext() as context:
            context.prec = 512
            clock = now_ms
            cooldown = policy_config["risk"]["cooldown_after_loss_ms"]
            initial_equity = Decimal(str(simulated["equity_brl"]))
            trajectory["initial_equity_brl"] = _money(initial_equity)
            trajectory["final_equity_brl"] = _money(initial_equity)
            trajectory["final_available_margin_brl"] = _money(Decimal(str(simulated["available_margin_brl"])))
            trajectory["reference_clock_end_ms"] = clock
            # Waiting is permitted only after a valid account has been checked
            # and cooldown is its sole blocker. Stale snapshots are never healed.
            if set(sizing.get("reasons", [])) == {"LOSS_COOLDOWN_ACTIVE"}:
                next_clock = max(clock, simulated["last_loss_ms"] + cooldown + 1)
                trajectory["initial_cooldown_wait_ms"] = next_clock - clock
                clock = next_clock
                simulated["asof_ms"] = clock
                sizing = evaluate_risk(policy_config, simulated, candidate, clock)

            total_loss = ZERO
            for attempt in range(1, max_attempts + 1):
                if sizing["status"] != "ALLOW_SIMULATION":
                    break
                quantity = sizing["contracts"]
                unit_risk = Decimal(sizing["risk_per_contract_brl"])
                planned_loss = quantity * unit_risk
                before_equity = Decimal(str(simulated["equity_brl"]))
                before_margin = Decimal(str(simulated["available_margin_brl"]))
                after_equity = before_equity - planned_loss
                after_margin = min(max(ZERO, before_margin - planned_loss), after_equity)
                if quantity <= 0 or planned_loss <= 0 or after_equity < 0 or after_margin < 0:
                    trajectory["stop_reasons"] = ["INVALID_PROJECTION_ARITHMETIC"]
                    trajectory["next_sizing"] = deepcopy(sizing)
                    return trajectory

                simulated["equity_brl"] = _money(after_equity)
                simulated["realized_pnl_net_brl"] = _money(Decimal(str(simulated["realized_pnl_net_brl"])) - planned_loss)
                simulated["available_margin_brl"] = _money(after_margin)
                simulated["consecutive_losses"] += 1
                simulated["last_loss_ms"] = clock
                # A losing path cannot increase its high-water mark. Keep the
                # original peak_equity_brl untouched, as well as session start.
                next_clock = clock + cooldown + 1
                simulated["asof_ms"] = next_clock
                total_loss += planned_loss
                step = {
                    "attempt": attempt,
                    "reference_now_ms": clock,
                    "next_reference_now_ms": next_clock,
                    "cooldown_wait_after_ms": cooldown + 1,
                    "contracts": quantity,
                    "equity_before_brl": _money(before_equity),
                    "equity_after_brl": _money(after_equity),
                    "available_margin_before_brl": _money(before_margin),
                    "available_margin_after_brl": _money(after_margin),
                    "risk_per_contract_brl": _money(unit_risk),
                    "planned_stop_loss_brl": _money(planned_loss),
                    "risk_budget_before_brl": sizing["risk_budget_brl"],
                    "margin_per_contract_brl": sizing["margin_per_contract_brl"],
                    "margin_required_brl": _money(quantity * Decimal(sizing["margin_per_contract_brl"])),
                    "margin_sizing_includes_stop_reserve": bool(sizing.get("margin_sizing_includes_stop_reserve", False)),
                    "consecutive_losses_after": simulated["consecutive_losses"],
                    "peak_equity_brl": (
                        _money(Decimal(str(simulated["peak_equity_brl"])))
                        if simulated.get("peak_equity_brl") is not None else None
                    ),
                }
                trajectory["steps"].append(step)
                trajectory["attempts"] = attempt
                trajectory["total_planned_loss_brl"] = _money(total_loss)
                trajectory["final_equity_brl"] = _money(after_equity)
                trajectory["final_available_margin_brl"] = _money(after_margin)
                clock = next_clock
                sizing = evaluate_risk(policy_config, simulated, candidate, clock)

            trajectory["reference_clock_end_ms"] = clock
            trajectory["next_sizing"] = deepcopy(sizing)
            if sizing["status"] == "ALLOW_SIMULATION":
                trajectory["truncated_at_max_attempts"] = True
                trajectory["stop_reasons"] = ["PROJECTION_LIMIT_REACHED"]
            else:
                trajectory["stop_reasons"] = list(sizing["reasons"])
            return trajectory
    except (KeyError, TypeError, ValueError, DecimalException, OverflowError):
        trajectory["stop_reasons"] = ["INVALID_PROJECTION_ARITHMETIC"]
        trajectory["truncated_at_max_attempts"] = False
        return trajectory


def project_stop_capacity(config: dict, account: dict, candidate: dict,
                          now_ms: int, max_attempts: int = 1000) -> dict:
    """Count hypothetical planned stops until risk policy blocks another attempt.

    ``current_sizing`` describes the supplied account *now*, including any active
    cooldown. Both trajectories allow hypothetical waiting, never a relaxation
    of a financial limit. ``max_attempts`` bounds work; truncated results are not
    complete capacity estimates. All inputs remain unchanged.
    """
    current = evaluate_risk(config, account, candidate, now_ms)
    result = {
        "status": "HYPOTHETICAL_PROJECTION",
        "simulation_only": True,
        "profit_forecast": False,
        "current_sizing": current,
        "attempts_until_policy_stop": 0,
        "attempts_by_financial_budget_ignoring_streak": 0,
        "trajectories": {},
        "stop_reasons": {},
        "caveats": list(CAVEATS),
    }
    invalid_limit = type(max_attempts) is not int or not 1 <= max_attempts <= MAX_PROJECTION_ATTEMPTS
    for key, ignore in (("real_policy", False), ("budget_only_ignoring_streak_projection", True)):
        trajectory = (
            _empty_trajectory(key, current, "INVALID_PROJECTION_LIMIT")
            if invalid_limit else _project(config, account, candidate, now_ms, max_attempts, ignore_streak=ignore)
        )
        result["trajectories"][key] = trajectory
        result["stop_reasons"][key] = list(trajectory["stop_reasons"])
    if invalid_limit:
        result["status"] = "INVALID_INPUT"
    result["attempts_until_policy_stop"] = result["trajectories"]["real_policy"]["attempts"]
    result["attempts_by_financial_budget_ignoring_streak"] = result["trajectories"]["budget_only_ignoring_streak_projection"]["attempts"]
    return result

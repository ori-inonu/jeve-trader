"""Scenario arithmetic, without probabilities or live prices. No order functions."""
from decimal import Decimal
import json


def scenario_report(capital="400"):
    equity = Decimal(str(capital))
    if not equity.is_finite() or equity <= 0:
        raise ValueError("Capital must be finite and positive")
    point, margin = Decimal("0.20"), Decimal("155")
    # Normal cost is a FICTIONAL test assumption. Forced fee is the public Toro
    # amount consulted 2026-10-06; taxes/other fees and account conditions may differ.
    normal_roundtrip = Decimal("2")
    forced_fee = Decimal("35")
    scenarios = []
    for contracts in (1, 2, 4):
        for adverse_points in (100, 200, 500, 1000):
            normal_loss = contracts * (adverse_points * point + normal_roundtrip)
            forced_loss = normal_loss + contracts * forced_fee
            scenarios.append({
                "contracts": contracts, "adverse_move_points": adverse_points,
                "minimum_margin_brl": str(contracts * margin),
                "margin_fits_before_reserves": contracts * margin <= equity,
                "loss_with_hypothetical_normal_costs_brl": str(normal_loss),
                "loss_if_forced_fee_also_applies_brl": str(forced_loss),
                "forced_loss_percent_of_initial": str((forced_loss / equity * 100).quantize(Decimal("0.01"))),
                "balance_after_forced_scenario_brl": str(equity - forced_loss)
            })
    return {
        "type": "ILLUSTRATIVE_STRESS_ARITHMETIC",
        "current_market_data": False, "probabilities_estimated": False,
        "capital_brl": str(equity),
        "notes": [
            "Scenarios are not predictions and do not estimate maximum loss.",
            "Four WIN do not fit BRL400 at BRL155 minimum margin per contract.",
            "Broker liquidation thresholds, extra fees and real slippage must be confirmed.",
            "A negative scenario balance is possible; deposited capital is not a guaranteed loss cap."
        ],
        "scenarios": scenarios
    }


if __name__ == "__main__":
    print(json.dumps(scenario_report(), indent=2, ensure_ascii=False))

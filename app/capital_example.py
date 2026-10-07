"""Pure legacy capital scenario, shared by both desktop frontends."""
from copilot import profile_config, finite, demo_snapshot


def example_from_inputs(config: dict, values: dict) -> tuple[dict, dict]:
    """Pure function for the adjustable synthetic capital scenario."""
    output = profile_config(config, "agressivo_pesquisa")
    start, current = finite(values["start"]), finite(values["current"])
    peak = max(finite(values["peak"]), start, current)
    risk_pct, daily_pct, dd_pct = (finite(values[x]) for x in ("risk_pct", "daily_pct", "drawdown_pct"))
    stop_distance, target_distance = finite(values["stop"]), finite(values["target"])
    streak_text = str(values.get("loss_streak", "0"))
    if not streak_text.isdigit() or not 0 <= int(streak_text) <= 1000:
        raise ValueError("Sequência de perdas inválida")
    streak = int(streak_text)
    if start <= 0 or current <= 0 or any(not 0 < x <= 100 for x in (risk_pct, daily_pct, dd_pct)):
        raise ValueError("Capital e percentuais inválidos")
    if stop_distance <= 0 or target_distance <= 0 or stop_distance % 5 or target_distance % 5:
        raise ValueError("Distâncias devem ser positivas e múltiplas de cinco pontos")
    output["risk"].update({"per_trade_fraction": str(risk_pct / 100),
                           "daily_loss_fraction": str(daily_pct / 100),
                           "max_peak_drawdown_fraction": str(dd_pct / 100)})
    snapshot = demo_snapshot(capital=str(start))
    snapshot["snapshot_id"] = f"panel-synthetic-{start}-{current}-{peak}-{stop_distance}-{target_distance}"
    snapshot["account"].update({"equity_brl": str(current), "peak_equity_brl": str(peak),
                                "realized_pnl_net_brl": str(current - start),
                                "available_margin_brl": str(current)})
    snapshot["account"]["consecutive_losses"] = streak
    snapshot["account"]["last_loss_ms"] = None
    if streak:
        snapshot["account"]["last_loss_ms"] = snapshot["account"]["asof_ms"] - 600001
    for candidate in snapshot["candidates"]:
        entry = finite(candidate["entry_points"])
        sign = 1 if candidate["side"] == "buy" else -1
        candidate["stop_points"] = str(entry - sign * stop_distance)
        candidate["target_points"] = str(entry + sign * target_distance)
        candidate["quantity_requested"] = output["risk"]["max_contracts"]
    return output, snapshot


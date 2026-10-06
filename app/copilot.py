"""Offline research harness. No live feed, no brokerage API, no order routing.

All prices and model outputs in --demo are synthetic. User-supplied replay
snapshots may be classified through the real JEV API with explicit --provider jev.
An allowed risk calculation is never represented as a proven profitable trade.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from risk import evaluate_risk
from jev_client import JevClient, JevError, validate_response
from candidate_engine import generate_candidates

ROOT = Path(__file__).resolve().parent


def load_json(path: Path) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError("Non-finite JSON number")
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":"))


def finite(value: Any) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("Invalid numeric value")
    answer = Decimal(str(value))
    if not answer.is_finite():
        raise ValueError("Invalid numeric value")
    return answer


def profile_config(config: dict, profile: str) -> dict:
    result = deepcopy(config)
    profiles = result["simulation_profiles"]
    if profile not in profiles:
        raise ValueError("Unknown simulation profile")
    result["risk"].update(profiles[profile]["overrides"])
    result["active_simulation_profile"] = profile
    return result


def quality_reasons(config: dict, snapshot: dict, now_ms: int) -> list[str]:
    reasons: list[str] = []
    try:
        if config.get("mode") != "simulation" or config.get("live_signals_enabled") is not False:
            reasons.append("SIMULATION_ONLY")
        if config.get("order_execution_enabled") is not False:
            reasons.append("ORDER_EXECUTION_NOT_IMPLEMENTED")
        if snapshot["schema_version"] != 1:
            reasons.append("SCHEMA_VERSION")
        if not isinstance(snapshot["snapshot_id"], str) or not snapshot["snapshot_id"]:
            reasons.append("SNAPSHOT_ID")
        # Hard boundary: changing a config cannot make this an operational live bot.
        if snapshot["data_origin"] not in {"synthetic", "replay"}:
            reasons.append("OFFLINE_RESEARCH_ONLY")
        if snapshot["symbol"] != config["market_data"]["expected_symbol"]:
            reasons.append("SYMBOL_MISMATCH")
        if snapshot["session_status"] != config["market_data"]["required_session_status"]:
            reasons.append("SESSION_NOT_CONTINUOUS")
        for name in ("feed_connected", "sequence_ok", "warmup_complete", "calendar_verified"):
            if snapshot[name] is not True:
                reasons.append(name.upper() + "_REQUIRED")
        if config["market_data"]["require_profit_open"] and snapshot["profit_open"] is not True:
            reasons.append("PROFIT_NOT_OPEN")
        if snapshot["event_risk_blocked"] is not False:
            reasons.append("EVENT_RISK_OR_UNKNOWN")
        maximum_age = int(config["market_data"]["max_age_ms"])
        if type(now_ms) is not int or maximum_age <= 0:
            raise ValueError("Invalid clock configuration")
        for field in ("ts_ms", "exchange_ts_ms", "quote_ts_ms", "flow_ts_ms"):
            stamp = snapshot[field]
            if type(stamp) is not int or not 0 <= now_ms - stamp <= maximum_age:
                reasons.append("STALE_OR_FUTURE_" + field.upper())
        bid, ask = finite(snapshot["bid_points"]), finite(snapshot["ask_points"])
        tick = finite(config["instrument"]["tick_points"])
        if tick <= 0 or bid <= 0 or ask <= bid or bid % tick or ask % tick:
            reasons.append("INVALID_QUOTE")
        elif ask - bid > finite(config["market_data"]["max_spread_points"]):
            reasons.append("SPREAD_TOO_WIDE")
        candidates = snapshot["candidates"]
        if not isinstance(candidates, list) or not 1 <= len(candidates) <= config["market_data"]["max_candidates"]:
            reasons.append("CANDIDATE_COVERAGE")
        elif any(not isinstance(c, dict) or not isinstance(c.get("id"), str) or not c["id"] for c in candidates):
            reasons.append("INVALID_CANDIDATE_ID")
        elif len({c["id"] for c in candidates}) != len(candidates):
            reasons.append("DUPLICATE_CANDIDATE_ID")
        if not isinstance(snapshot["observations"], dict) or not snapshot["observations"]:
            reasons.append("MISSING_OBSERVATIONS")
        if not isinstance(snapshot["computed_features"], dict) or not snapshot["computed_features"]:
            reasons.append("MISSING_COMPUTED_FEATURES")
        if not isinstance(snapshot["account"], dict):
            reasons.append("INVALID_ACCOUNT")
        # Validate serialization, rejecting NaN in nested observations as well.
        canonical(snapshot)
    except (KeyError, TypeError, ValueError, InvalidOperation, OverflowError):
        reasons.append("INVALID_OR_INCOMPLETE_SNAPSHOT")
    return list(dict.fromkeys(reasons))


def _replace_path(value: Any, path: str) -> Any:
    if isinstance(value, str):
        return value.replace("candidate_setup", path)
    if isinstance(value, dict):
        return {key: _replace_path(item, path) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_path(item, path) for item in value]
    return value


def prepare_batch(snapshot: dict, eligible: list[dict], base_questions: dict) -> tuple[dict, dict]:
    # No account balance, personal identifiers, past losses or API secrets are sent.
    setups = []
    for candidate in eligible:
        setup = {key: candidate[key] for key in
                 ("id", "side", "entry_points", "stop_points", "target_points", "premise")}
        setup["premise_is_hypothesis"] = True
        setup["reference_evidence_ids"] = candidate.get("reference_evidence_ids", [])
        setup["level_evidence_supplied"] = bool(setup["reference_evidence_ids"])
        setups.append(setup)
    used_ids = {identity for setup in setups for identity in setup["reference_evidence_ids"]}
    used_levels = [level for level in snapshot.get("reference_levels", [])
                   if level.get("evidence_id") in used_ids]
    found_ids = {level["evidence_id"] for level in used_levels}
    for setup in setups:
        setup["level_evidence_supplied"] = bool(setup["reference_evidence_ids"]) and all(
            identity in found_ids for identity in setup["reference_evidence_ids"])
    state = {
        "mode": "offline_research",
        "symbol": snapshot["symbol"],
        "observations": snapshot["observations"],
        "computed_features": snapshot["computed_features"],
        "candidate_setups": setups,
        "reference_levels": used_levels,
        "level_evidence_note": "An ID and price alone do not establish a level's predictive significance. Missing descriptions remain unknown.",
        "evidence_coverage": snapshot.get("evidence_coverage", {}),
        "instructions_for_data": "Evaluate observations only; these are not future outcomes."
    }
    questions = {"flow_interpretation": deepcopy(base_questions["flow_interpretation"])}
    for i, _ in enumerate(setups):
        for kind in ("setup_evidence_support", "contradictory_evidence"):
            questions[f"{kind}_{i}"] = _replace_path(base_questions[kind], f"candidate_setups[{i}]")
    return state, questions


def synthetic_response(questions: dict, model: str) -> dict:
    """Test fixture, never a JEV observation or empirical estimate."""
    answers = {}
    for name, question in questions.items():
        if question["type"] == "choice":
            options = list(question["criteria"])
            selected = "buying_with_price_acceptance"
            if selected not in options:
                raise ValueError("Synthetic fixture and question rubric differ")
            peak = 0.90
            answers[name] = {
                "type": "choice", "choice": selected,
                "probabilities": {key: peak if key == selected else (1 - peak) / (len(options) - 1)
                                  for key in options},
                "confidence": (peak - 1 / len(options)) / (1 - 1 / len(options))
            }
        else:
            answers[name] = {"type": "noul", "noul": 0.05 if name.startswith("contradictory") else 0.90}
    return {"model": model, "answers": answers, "usage": {"input_tokens": 0, "output_tokens": 0}}


class Copilot:
    def __init__(self, config: dict, questions: dict, provider: str = "mock"):
        if provider not in {"mock", "jev"}:
            raise ValueError("Unknown provider")
        self.config = config
        self.questions = questions
        self.provider = provider
        self.seen: set[str] = set()
        self.latest_stamp: int | None = None

    def process(self, snapshot: dict, now_ms: int) -> dict:
        if not isinstance(snapshot, dict):
            snapshot = {}
        snapshot = deepcopy(snapshot)
        if not snapshot.get("candidates") and snapshot.get("reference_levels"):
            try:
                snapshot["candidates"] = generate_candidates(
                    snapshot, self.config["instrument"]["tick_points"],
                    self.config["risk"]["max_contracts"])
            except (KeyError, ValueError, TypeError):
                snapshot["candidates"] = []
        decision: dict = {
            "snapshot_id": snapshot.get("snapshot_id"),
            "status": "WAIT",
            "simulation_only": True,
            "actionable_live_signal": False,
            "order_sent": False,
            "provider": "SYNTHETIC_TEST_FIXTURE" if self.provider == "mock" else "JEV_API",
            "data_origin": snapshot.get("data_origin", "unknown"),
            "clock_basis": "offline_reference_plus_measured_inference_elapsed",
            "strategy_validated": False,
            "win_probability": None,
            "risk_profile": self.config.get("active_simulation_profile"),
            "evaluated_at_ms": now_ms,
            "reasons": [],
            "risk_assessments": []
        }
        reasons = quality_reasons(self.config, snapshot, now_ms)
        if reasons:
            decision["reasons"] = reasons
            return decision
        sid = snapshot["snapshot_id"]
        if sid in self.seen or (self.latest_stamp is not None and snapshot["ts_ms"] < self.latest_stamp):
            decision["reasons"] = ["DUPLICATE_OR_OUT_OF_ORDER_SNAPSHOT"]
            return decision
        self.seen.add(sid)
        # This CLI is short-lived offline research; persist identities in a real service.
        if len(self.seen) > 100000:
            decision["reasons"] = ["RESEARCH_SESSION_LIMIT"]
            return decision
        self.latest_stamp = snapshot["ts_ms"]
        eligible: list[dict] = []
        for candidate in snapshot["candidates"]:
            risk = evaluate_risk(self.config, snapshot["account"], candidate, now_ms)
            # Only immediately observable quoted entries are evaluated in this MVP.
            # Future stop entries and pullback triggers require a separate lifecycle.
            try:
                expected_entry = snapshot["ask_points"] if candidate["side"] == "buy" else snapshot["bid_points"]
                current_entry = finite(candidate["entry_points"]) == finite(expected_entry)
                premise = isinstance(candidate.get("premise"), str) and bool(candidate["premise"].strip())
            except (KeyError, ValueError, InvalidOperation):
                current_entry = premise = False
            if not current_entry or not premise:
                risk["status"] = "BLOCK"
                risk["contracts"] = 0
                risk["reasons"] = list(dict.fromkeys(risk.get("reasons", []) + ["ENTRY_OR_PREMISE_NOT_VALID"]))
            decision["risk_assessments"].append({"candidate_id": candidate["id"], **risk})
            if risk["status"] == "ALLOW_SIMULATION":
                eligible.append(candidate)
        if not eligible:
            decision["reasons"] = ["NO_CANDIDATE_WITHIN_RISK_BUDGET"]
            return decision
        state, questions = prepare_batch(snapshot, eligible, self.questions)
        decision["state_sha256"] = hashlib.sha256(canonical(state).encode()).hexdigest()
        decision["questions_sha256"] = hashlib.sha256(canonical(questions).encode()).hexdigest()
        started = time.monotonic()
        try:
            if self.provider == "mock":
                response = synthetic_response(questions, self.config["jev"]["model"])
                response = validate_response(response, questions, self.config["jev"]["model"])
            else:
                response = JevClient(model=self.config["jev"]["model"],
                                     timeout_seconds=self.config["jev"]["timeout_seconds"]).evaluate(state, questions)
        except (JevError, ValueError, KeyError, TypeError):
            decision["reasons"] = ["JEV_UNAVAILABLE_OR_RESPONSE_INVALID"]
            return decision
        elapsed = int((time.monotonic() - started) * 1000)
        after_ms = now_ms + elapsed
        decision["inference_elapsed_ms"] = elapsed
        decision["evaluated_at_ms"] = after_ms
        # Repeat freshness and risk gates after the remote request.
        post_reasons = quality_reasons(self.config, snapshot, after_ms)
        if elapsed > self.config["jev"]["max_inference_age_ms"]:
            post_reasons.append("INFERENCE_EXPIRED")
        if post_reasons:
            decision["reasons"] = post_reasons
            return decision
        decision["model_response"] = response
        flow = response["answers"]["flow_interpretation"]
        if flow["choice"] == "inconclusive" or flow["confidence"] < self.config["jev"]["confidence_min_example"]:
            decision["reasons"] = ["FLOW_INCONCLUSIVE"]
            return decision
        matching = {"buy": {"buying_with_price_acceptance", "selling_absorbed"},
                    "sell": {"selling_with_price_acceptance", "buying_absorbed"}}
        reviews = []
        for i, candidate in enumerate(eligible):
            support = response["answers"][f"setup_evidence_support_{i}"]["noul"]
            contradiction = response["answers"][f"contradictory_evidence_{i}"]["noul"]
            fresh_risk = evaluate_risk(self.config, snapshot["account"], candidate, after_ms)
            if (fresh_risk["status"] == "ALLOW_SIMULATION"
                and support >= self.config["jev"]["setup_support_min_example"]
                and contradiction <= self.config["jev"]["contradiction_max_example"]
                and flow["choice"] in matching[candidate["side"]]):
                reviews.append({"candidate_id": candidate["id"], "side": candidate["side"],
                                "entry_points": candidate["entry_points"], "stop_points": candidate["stop_points"],
                                "target_points": candidate["target_points"], "contracts": fresh_risk["contracts"],
                                "risk": fresh_risk, "evidence_support": support,
                                "contradictory_evidence": contradiction})
        if reviews:
            # A ranking for RESEARCH review, not maximization of expected profit.
            reviews.sort(key=lambda x: (-x["evidence_support"], x["contradictory_evidence"], x["candidate_id"]))
            decision["status"] = "SIMULATION_REVIEW"
            decision["candidates_for_review"] = reviews
            expirations = [snapshot[field] + self.config["market_data"]["max_age_ms"]
                           for field in ("ts_ms", "exchange_ts_ms", "quote_ts_ms", "flow_ts_ms")]
            expirations.append(snapshot["account"]["asof_ms"] + self.config["risk"]["max_account_age_ms"])
            decision["expires_at_ms"] = min(expirations)
            decision["reasons"] = ["RESEARCH_ONLY_NO_VALIDATED_PREDICTIVE_EDGE"]
        else:
            decision["reasons"] = ["NO_SUPPORTED_CANDIDATE"]
        return decision


def demo_snapshot(capital: str = "400", loss: str = "0", age_ms: int = 0) -> dict:
    now = 1801848600000  # Fixed synthetic research clock, never a current quote.
    pnl = finite(loss)
    equity = finite(capital) + pnl
    return {
        "schema_version": 1, "snapshot_id": f"synthetic-{capital}-{loss}-{age_ms}",
        "ts_ms": now - age_ms, "exchange_ts_ms": now - age_ms,
        "quote_ts_ms": now - age_ms, "flow_ts_ms": now - age_ms,
        "data_origin": "synthetic", "symbol": "WIN_SIM", "session_status": "CONTINUOUS",
        "profit_open": True, "feed_connected": True, "sequence_ok": True,
        "warmup_complete": True, "calendar_verified": True, "event_risk_blocked": False,
        "bid_points": 131000, "ask_points": 131005,
        "account": {
            "asof_ms": now, "start_equity_brl": capital, "equity_brl": str(equity),
            "peak_equity_brl": str(max(finite(capital), equity)),
            "realized_pnl_net_brl": str(pnl), "unrealized_pnl_brl": "0", "reserved_risk_brl": "0",
            "available_margin_brl": str(equity), "broker_margin_brl_per_contract": "155",
            "open_contracts": 0, "pending_entry_contracts": 0,
            "consecutive_losses": 1 if pnl < 0 else 0,
            "last_loss_ms": now - 600001 if pnl < 0 else None,
            "reconciled": True, "environment": "simulated"
        },
        "observations": {
            "label": "SYNTHETIC FIXTURE, NOT B3 MARKET DATA",
            "recent_tape_summary": "Synthetic buy aggressions with higher traded prices.",
            "book_replenishment": "No opposing replenishment represented in this fixture."
        },
        "computed_features": {
            "window_ms": 5000, "buy_aggressed_contracts": 180, "sell_aggressed_contracts": 70,
            "delta_contracts": 110, "price_change_points": 35,
            "source": "synthetic_values_not_a_feature_calculation"
        },
        "evidence_coverage": {"complete_for_fixture": True, "exchange_data": False},
        "candidates": [
            {"id": "buy_example", "side": "buy", "entry_points": 131005,
             "stop_points": 130905, "target_points": 131205, "quantity_requested": 100,
             "premise": "Recent observed aggressive buying is accepted at higher prices."},
            {"id": "sell_example", "side": "sell", "entry_points": 131000,
             "stop_points": 131100, "target_points": 130800, "quantity_requested": 100,
             "premise": "Recent observed aggressive selling is accepted at lower prices."}
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Run synthetic offline scenarios; never contacts JEV")
    parser.add_argument("--input", type=Path, help="JSON snapshot from offline replay or synthetic research")
    parser.add_argument("--profile", choices=("controle", "agressivo_pesquisa"))
    parser.add_argument("--provider", choices=("mock", "jev"), default="mock")
    parser.add_argument("--config", type=Path, default=ROOT / "config.json")
    parser.add_argument("--write-example", type=Path)
    args = parser.parse_args()
    config, questions = load_json(args.config), load_json(ROOT / "questions.json")
    if args.write_example:
        args.write_example.write_text(json.dumps(demo_snapshot(), indent=2, ensure_ascii=False), encoding="utf-8")
        return 0
    if args.demo:
        scenarios = [("controle", "400", "0", 0), ("controle", "400", "-20", 0),
                     ("agressivo_pesquisa", "400", "0", 0),
                     ("agressivo_pesquisa", "400", "-20", 0),
                     ("agressivo_pesquisa", "4000", "0", 0),
                     ("agressivo_pesquisa", "400", "0", 2001)]
        for profile, capital, loss, age in scenarios:
            snapshot = demo_snapshot(capital, loss, age)
            engine = Copilot(profile_config(config, profile), questions, "mock")
            result = engine.process(snapshot, snapshot["account"]["asof_ms"])
            print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    if not args.input or not args.profile:
        parser.error("Use --demo or --input FILE --profile NAME. All modes are offline simulation.")
    try:
        snapshot = load_json(args.input)
    except (ValueError, OSError):
        print(json.dumps({"status": "WAIT", "actionable_live_signal": False,
                          "reasons": ["INVALID_INPUT_FILE"]}))
        return 1
    # Offline replay uses a fixed reference clock; real inference elapsed time is still checked.
    try:
        stamps = [snapshot["ts_ms"], snapshot["account"]["asof_ms"]]
        if any(type(stamp) is not int for stamp in stamps):
            raise ValueError("Invalid offline clock")
        now_ms = max(stamps)
    except (KeyError, TypeError, ValueError):
        now_ms = 0  # Invalid structure is reported by the validation gate below.
    engine = Copilot(profile_config(config, args.profile), questions, args.provider)
    print(json.dumps(engine.process(snapshot, now_ms), ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

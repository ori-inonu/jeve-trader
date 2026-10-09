"""Pure synthesis of observed data, contextual JEV evidence and manual risk.

This is an explanation engine: no orders, optimal policy, expected return or win
probability. Original source clocks and financial constraints veto before model
support is considered. Contextual scores remain descriptive and uncalibrated.
"""
from __future__ import annotations

from decimal import Decimal, DecimalException

from risk import evaluate_risk


MAX_OPTIONS = 8
SOURCE_MAX_AGE_MS = 2000
FLOW_CHOICES = {
    "buy_progression", "sell_progression", "possible_buy_absorption",
    "possible_sell_absorption", "possible_exhaustion", "mixed_or_insufficient",
}
GLOBAL_RISK_VETOES = {
    "SIMULATION_ONLY", "INVALID_CLOCK", "INVALID_CONFIG", "SIMULATED_ACCOUNT_REQUIRED",
    "ACCOUNT_NOT_RECONCILED", "INVALID_ACCOUNT", "STALE_OR_FUTURE_ACCOUNT", "INVALID_PEAK_EQUITY",
    "ACCOUNT_EQUITY_MISMATCH", "CAPITAL_EXHAUSTED", "EXISTING_POSITION_OR_PENDING_ENTRY",
    "DAILY_LOSS_LIMIT_REACHED", "PEAK_DRAWDOWN_LIMIT_REACHED", "CONSECUTIVE_LOSS_LIMIT_REACHED",
    "LOSS_COOLDOWN_ACTIVE", "RISK_BUDGET_EXHAUSTED", "INVALID_ARITHMETIC",
}


def _clock(value):
    return type(value) is int and 0 <= value <= 10**15


def _decimal(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)) or len(str(value)) > 128:
        raise ValueError("Invalid decimal")
    result = Decimal(str(value))
    if not result.is_finite() or abs(result.adjusted()) > 30:
        raise ValueError("Invalid decimal")
    return result


def _unit(value):
    if type(value) not in (int, float, Decimal):
        raise ValueError("Invalid contextual score")
    score = _decimal(value)
    if not 0 <= score <= 1:
        raise ValueError("Invalid contextual score")
    return float(score)


def _geometry(candidate):
    if not isinstance(candidate, dict):
        raise ValueError("Missing candidate")
    identity, side = candidate["id"], candidate["side"]
    if not isinstance(identity, str) or not identity.strip() or len(identity) > 128 or side not in ("buy", "sell"):
        raise ValueError("Invalid candidate identity")
    prices = tuple(_decimal(candidate[key]) for key in ("entry_points", "stop_points", "target_points"))
    if any(price <= 0 for price in prices):
        raise ValueError("Invalid candidate price")
    entry, stop, target = prices
    if not (stop < entry < target if side == "buy" else target < entry < stop):
        raise ValueError("Invalid geometry")
    return identity, side, prices


def _same_geometry(left, right):
    try:
        return _geometry(left) == _geometry(right)
    except (KeyError, TypeError, ValueError, DecimalException):
        return False


def _model(result, snapshot, now_ms):
    view = {"available": False, "current": False, "descriptive_only": True,
            "choice": None, "classification_confidence": None, "reasons": [],
            "score_interpretation": "Apoio/contradição contextuais; sem calibração de resultado financeiro.",
            "win_probability": None}
    if not isinstance(result, dict):
        view["reasons"].append("JEV_NOT_EVALUATED")
        return view, {}, []
    try:
        state, response = result["state"], result["response"]
        if not isinstance(state, dict) or not isinstance(response, dict):
            raise ValueError("Invalid model envelope")
        flow = response["answers"]["flow_context"]
        choice = flow["choice"]
        if choice not in FLOW_CHOICES or flow.get("type") != "choice":
            raise ValueError("Unsupported contextual choice")
        confidence = _unit(flow["confidence"])
        insuff = response['answers']['evidence_insufficient']
        if insuff.get('type') != 'noul':
            raise ValueError('Missing insufficiency')
        view['insufficiency'] = _unit(insuff['noul'])
        view['review_policy_version'] = 'context-dimensions-v2'
        if view['insufficiency'] >= 0.5:
            view['reasons'].append('JEV_EVIDENCE_INSUFFICIENT')
        view.update(available=True, choice=choice, classification_confidence=confidence)
        ts, flow_ts = result.get("source_ts_ms"), result.get("flow_ts_ms")
        mode = snapshot.get("application_mode")
        if result.get("mode") != mode or state.get("instrument") != snapshot.get("symbol"):
            view["reasons"].append("JEV_SOURCE_MISMATCH")
        if not _clock(ts) or not _clock(flow_ts) or not 0 <= now_ms - flow_ts <= SOURCE_MAX_AGE_MS or ts > now_ms:
            view["reasons"].append("JEV_STALE_OR_FUTURE_SOURCE")
        if _clock(ts) and _clock(flow_ts) and flow_ts > ts:
            view["reasons"].append("JEV_SOURCE_AFTER_REFERENCE_CLOCK")
        if state.get("asof_ms") != ts:
            view["reasons"].append("JEV_REFERENCE_CLOCK_MISMATCH")
        generation = result.get("source_generation", state.get("source_generation"))
        if generation is not None and (type(generation) is not int or generation != snapshot.get("source_generation")):
            view["reasons"].append("JEV_SOURCE_GENERATION_MISMATCH")
        view["source_ts_ms"], view["flow_ts_ms"] = ts, flow_ts
        setups = state.get("candidate_setups", [])
        if not isinstance(setups, list) or len(setups) > MAX_OPTIONS:
            raise ValueError("Invalid setup coverage")
        setup_scores = {}
        for index, setup in enumerate(setups):
            identity, _, _ = _geometry(setup)
            if identity in setup_scores:
                raise ValueError("Duplicate model setup")
            support = response["answers"].get(f"candidate_{index}_support")
            contradiction = response["answers"].get(f"candidate_{index}_contradiction")
            insufficient = response['answers'].get(f'candidate_{index}_insufficient')
            if not isinstance(insufficient, dict) or insufficient.get('type') != 'noul':
                raise ValueError('Candidate insufficiency missing')
            if not isinstance(support, dict) or not isinstance(contradiction, dict) or support.get("type") != "noul" or contradiction.get("type") != "noul":
                raise ValueError("Candidate model evidence missing")
            setup_scores[identity] = {"setup": setup, "support": _unit(support["noul"]),
                                      "contradiction": _unit(contradiction["noul"]), 'insufficiency': _unit(insufficient['noul'])}
        view["current"] = not view["reasons"]
        return view, setup_scores, setups
    except (KeyError, TypeError, ValueError, DecimalException, OverflowError):
        view.update(available=False, current=False)
        view["reasons"].append("JEV_RESULT_INVALID_OR_INCOMPLETE")
        return view, {}, []


def build_recommendation(snapshot, candidate_report, risk_study, latest_jev_result=None, now_ms=None):
    """Return one non-executing review state and preserve every veto/reason.

    For a static replay/demo, explicitly pass its original reference clock to
    review that historical instant. Live callers pass current time. This module
    never changes timestamps or account balances. Candidate risk is recalculated
    against the supplied current manual account instead of trusting cached lots.
    """
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    report = candidate_report if isinstance(candidate_report, dict) else {}
    study = risk_study if isinstance(risk_study, dict) else {}
    if now_ms is None:
        now_ms = snapshot.get("ts_ms")
    initial_coverage = snapshot.get("evidence_coverage")
    initial_coverage = initial_coverage if isinstance(initial_coverage, dict) else {}
    initial_quality = initial_coverage.get("source_quality")
    initial_quality = initial_quality if isinstance(initial_quality, dict) else {}
    result = {"schema_version": 1, "status": "SEM_DADOS", "action": "Carregar dados identificados antes de avaliar hipóteses.",
              "origin": {"mode": snapshot.get("application_mode", "unknown"), "symbol": snapshot.get("symbol"),
                         "data_origin": initial_quality.get("data_origin", "unknown")},
              "evaluated_at_ms": now_ms, "expires_at_ms": None, "reasons": [], "missing_evidence": [],
              "contradictions": [], "options": [], "review_candidate_ids": [],
              "account_assumptions": {"account_source": study.get("account_source", "unknown"),
                                      "broker_connected": study.get("broker_connected") is True,
                                      "loss_time_assumption": study.get("loss_time_assumption"),
                                      "positions_margin_and_equity": "Valores/ausência de posições são pressupostos do cenário manual; não são consulta à corretora."},
              "model": {"available": False, "current": False, "descriptive_only": True, "choice": None},
              "simulation_only": True, "actionable_live_signal": False, "order_sent": False,
              "win_probability": None, "optimal_configuration": None, "ranking": None, "expected_return": None,
              "configuration_note": "Melhor configuração de lucro não foi estimada; compare hipóteses e limites sem ordenar retorno futuro."}
    if not _clock(now_ms) or not isinstance(snapshot.get("symbol"), str) or not snapshot.get("symbol"):
        result["reasons"].append("SOURCE_AND_VALID_CLOCK_REQUIRED")
        return result
    try:
        coverage = snapshot.get("evidence_coverage", {})
        features = snapshot.get("computed_features", {})
        quality = coverage.get("source_quality", {})
        mode = snapshot.get("application_mode")
        data_origin = quality.get("data_origin")
        if mode not in ("synthetic", "replay", "excel_observation") or data_origin not in ("synthetic", "replay", "live"):
            result["reasons"].append("IDENTIFIED_DATA_ORIGIN_REQUIRED")
            return result
        expected_origin = {"synthetic": "synthetic", "replay": "replay", "excel_observation": "live"}[mode]
        if data_origin != expected_origin:
            result["reasons"].append("DATA_ORIGIN_MODE_MISMATCH")
            return result
        result["origin"]["historical_or_synthetic"] = mode != "excel_observation"
        result["origin"]["clock_basis"] = "original_historical_reference" if mode != "excel_observation" else "current_clock_with_original_source_timestamps"
        tape_ts = snapshot.get("flow_ts_ms")
        if not _clock(tape_ts) or features.get("trade_count", 0) <= 0:
            result["reasons"].append("EXECUTED_TRADE_DATA_REQUIRED")
            return result
        result["status"] = "AGUARDAR"
        result["action"] = "Aguardar evidência atual e completa para revisar uma hipótese."
        data_vetoes = []
        if not 0 <= now_ms - tape_ts <= SOURCE_MAX_AGE_MS:
            data_vetoes.append("STALE_OR_FUTURE_TAPE")
        if coverage.get("integrity_ok") is not True:
            data_vetoes.append("SOURCE_INTEGRITY_REQUIRED")
        if coverage.get("tape_fresh") is not True:
            data_vetoes.append("TAPE_MEASUREMENT_NOT_FRESH")
        if not _clock(snapshot.get("ts_ms")) or snapshot["ts_ms"] > now_ms:
            data_vetoes.append("STALE_OR_FUTURE_REFERENCE_CLOCK")
        report_coverage = report.get("evidence_coverage", {})
        quote_ts = report_coverage.get("quote_ts_ms")
        if not _clock(quote_ts) or not 0 <= now_ms - quote_ts <= SOURCE_MAX_AGE_MS:
            data_vetoes.append("FRESH_TWO_SIDED_QUOTE_REQUIRED")
        if report_coverage.get("quote_fresh") is not True:
            data_vetoes.append("QUOTE_COVERAGE_UNAVAILABLE")
        if _clock(tape_ts) and _clock(quote_ts):
            result["expires_at_ms"] = min(tape_ts, quote_ts) + SOURCE_MAX_AGE_MS
        result["missing_evidence"].extend(data_vetoes)
        full_coverage = all(quality.get(key) is True for key in ("feed_connected", "sequence_ok", "full_tape"))
        if not full_coverage:
            result["missing_evidence"].append("COMPLETE_TAPE_SOURCE_NOT_VERIFIED")
        if coverage.get("short_window_complete") is not True:
            result["missing_evidence"].append("SHORT_WINDOW_INCOMPLETE")
        if features.get("unknown_aggressor_contracts", 0) != 0:
            result["missing_evidence"].append("UNKNOWN_AGGRESSOR_COVERAGE")
        config, account = study.get("config"), study.get("account")
        if study.get("account_source") != "manual_scenario" or study.get("broker_connected") is True:
            result["status"] = "BLOQUEADO_RISCO"
            result["action"] = "Bloquear revisão financeira: a conta deve ser um cenário manual explicitamente identificado."
            result["reasons"].append("EXPLICIT_MANUAL_SCENARIO_REQUIRED")
            return result
        if isinstance(account, dict) and isinstance(config, dict):
            account_ts = account.get("asof_ms")
            account_max_age = config.get("risk", {}).get("max_account_age_ms")
            if _clock(account_ts) and type(account_max_age) is int and account_max_age >= 0:
                account_expiry = account_ts + account_max_age
                result["expires_at_ms"] = min(result["expires_at_ms"], account_expiry) if result["expires_at_ms"] is not None else account_expiry
        rows = report.get("rows", [])
        if not isinstance(rows, list) or len(rows) > MAX_OPTIONS:
            raise ValueError("Invalid technical candidate list")
        identities = set()
        global_vetoes = set()
        # The generic laboratory proposal checks account/policy vetoes even when
        # no observed geometry is available. Geometry-specific blocks do not veto
        # a different candidate with a smaller observed stop.
        generic = evaluate_risk(config, account, study.get("candidate", {}), now_ms)
        global_vetoes.update(set(generic.get("reasons", [])) & GLOBAL_RISK_VETOES)
        for row in rows:
            identity, side, _ = _geometry(row)
            if identity in identities:
                raise ValueError("Duplicate candidate identity")
            identities.add(identity)
            candidate = {key: row[key] for key in ("id", "side", "entry_points", "stop_points", "target_points")}
            candidate["quantity_requested"] = config.get("risk", {}).get("max_contracts", 1) if isinstance(config, dict) else 1
            risk = evaluate_risk(config, account, candidate, now_ms)
            global_vetoes.update(set(risk.get("reasons", [])) & GLOBAL_RISK_VETOES)
            levels = row.get("reference_levels", [])
            references_valid = isinstance(levels, list) and len(levels) == 2
            reference_ids = []
            if references_valid:
                for level in levels:
                    ts = level.get("asof_ms")
                    identity_level = level.get("evidence_id")
                    if not _clock(ts) or not 0 <= now_ms - ts <= 30000 or not isinstance(identity_level, str) or not identity_level:
                        references_valid = False
                        break
                    _decimal(level.get("price_points"))
                    reference_ids.append(identity_level)
            option_reasons = list(risk["reasons"])
            if not references_valid:
                option_reasons.append("CURRENT_OBSERVED_LEVEL_EVIDENCE_REQUIRED")
            else:
                tick = _decimal(config["instrument"]["tick_points"])
                direction = 1 if side == "buy" else -1
                expected_stop = _decimal(levels[0]["price_points"]) - direction * tick
                expected_target = _decimal(levels[1]["price_points"]) - direction * tick
                if (_decimal(row["stop_points"]) != expected_stop or _decimal(row["target_points"]) != expected_target
                        or row.get("reference_evidence_ids") != reference_ids):
                    option_reasons.append("STRUCTURAL_LEVEL_GEOMETRY_MISMATCH")
            quote_entry = report_coverage.get("entry_quote_ask_points" if side == "buy" else "entry_quote_bid_points")
            if quote_entry is None or _decimal(row["entry_points"]) != _decimal(quote_entry):
                option_reasons.append("ENTRY_NOT_CURRENT_QUOTE")
            option_reasons.extend(data_vetoes)
            result["options"].append({"candidate_id": row["id"], "id": row["id"], "side": side,
                                      "entry_points": row["entry_points"], "stop_points": row["stop_points"], "target_points": row["target_points"],
                                      "contracts": risk["contracts"], "lots": risk["contracts"], "risk": risk,
                                      "status": "BLOQUEADO_RISCO" if risk["status"] != "ALLOW_SIMULATION" else "AGUARDAR",
                                      "reasons": option_reasons, "reference_evidence_ids": reference_ids,
                                      "model_evidence": None, "actionable_live_signal": False})
            result['options'][-1]['premise'] = row.get('premise')
            result['options'][-1]['hypothesis_version'] = row.get('hypothesis_version')
        if global_vetoes or result["options"] and all(option["risk"]["status"] != "ALLOW_SIMULATION" for option in result["options"]):
            result["status"] = "BLOQUEADO_RISCO"
            result["action"] = "Manter propostas bloqueadas pelos limites do cenário manual."
            result["reasons"].extend(sorted(global_vetoes) or ["NO_CANDIDATE_WITHIN_RISK_BUDGET"])
            # No model score can relax a deterministic financial veto.
            result["model"]["reasons"] = ["FINANCIAL_VETO_PRECEDES_MODEL"]
            return result
        if not result["options"]:
            result["reasons"].append("OBSERVED_STOP_TARGET_GEOMETRY_REQUIRED")
        model, scores, _ = _model(latest_jev_result, snapshot, now_ms)
        result["model"] = model
        result["reasons"].extend(model["reasons"])
        if model.get("choice") == "possible_exhaustion" and coverage.get("previous_window_complete") is not True:
            result["missing_evidence"].append("PREVIOUS_WINDOW_REQUIRED_FOR_EXHAUSTION")
        if model.get("choice") == "mixed_or_insufficient":
            result["contradictions"].append("MODEL_CONTEXT_MIXED_OR_INSUFFICIENT")
        if model.get("choice") in ("possible_buy_absorption", "possible_sell_absorption", "possible_exhaustion"):
            result["contradictions"].append("ABSORPTION_OR_EXHAUSTION_DOES_NOT_CONFIRM_REVERSAL")
        for option in result["options"]:
            evidence = scores.get(option["id"])
            if (evidence is None or not _same_geometry(evidence["setup"], option)
                    or not option.get('premise') or evidence['setup'].get('premise') != option['premise']
                    or evidence['setup'].get('hypothesis_version') != option['hypothesis_version']):
                option["reasons"].append("JEV_CANDIDATE_GEOMETRY_NOT_EVALUATED")
                continue
            support, contradiction = evidence["support"], evidence["contradiction"]
            option["model_evidence"] = {"support": support, "contradiction": contradiction,
                                         'insufficiency': evidence['insufficiency'],
                                         "support_exceeds_contradiction": support > contradiction,
                                         "scores_calibrated_on_WIN": False, "win_probability": None}
            if contradiction >= support:
                result["contradictions"].append("MODEL_CONTRADICTION_NOT_LESS_THAN_SUPPORT:" + option["id"])
            if model.get("choice") == "buy_progression" and option["side"] == "sell" or model.get("choice") == "sell_progression" and option["side"] == "buy":
                option["reasons"].append("MODEL_FLOW_DIRECTION_CONTRADICTS_OPTION")
            if (model["current"] and not result["missing_evidence"] and not option["reasons"]
                    and model.get("choice") != "mixed_or_insufficient" and support > contradiction and evidence['insufficiency'] < 0.5):
                option["status"] = "HIPOTESE_PARA_REVISAO"
                result["review_candidate_ids"].append(option["id"])
        if result["review_candidate_ids"]:
            result["status"] = "HIPOTESE_PARA_REVISAO"
            sides = {option["side"] for option in result["options"] if option["id"] in result["review_candidate_ids"]}
            label = "compradoras" if sides == {"buy"} else "vendedoras" if sides == {"sell"} else "dos dois lados"
            result["action"] = f"Observar hipóteses {label} para revisão humana, com stops/alvos e lote limitados pelo cenário manual."
            result["model"]["review_supported"] = True
            result["reasons"].append("CONTEXTUAL_EVIDENCE_REVIEW_NOT_VALIDATED_TRADING_EDGE")
        else:
            result["reasons"].append("NO_HYPOTHESIS_WITH_COMPLETE_CURRENT_EVIDENCE")
        result["reasons"] = list(dict.fromkeys(result["reasons"]))
        result["missing_evidence"] = list(dict.fromkeys(result["missing_evidence"]))
        result["contradictions"] = list(dict.fromkeys(result["contradictions"]))
        return result
    except (KeyError, TypeError, ValueError, DecimalException, OverflowError, AttributeError):
        result["status"] = "AGUARDAR"
        result["action"] = "Aguardar dados estruturados válidos; avaliação incompleta."
        result["reasons"].append("INVALID_OR_INCOMPLETE_RECOMMENDATION_INPUT")
        result["review_candidate_ids"] = []
        for option in result["options"]:
            option["status"] = "AGUARDAR"
        return result


recommend = build_recommendation

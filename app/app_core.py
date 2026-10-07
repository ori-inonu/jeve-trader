"""Desktop application seams: source observations and explicitly manual risk studies."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import json
import time

from app_store import resource_path
from capital_planner import project_stop_capacity
from copilot import load_json
from capital_example import example_from_inputs
from flow_engine import FlowEngine, generate_flow_scenario
from risk_research import compare_risk_policies


DEFAULT_INPUTS = {"start": "400", "current": "400", "peak": "400", "risk_pct": "15", "daily_pct": "50",
                  "drawdown_pct": "50", "stop": "100", "target": "200", "loss_streak": "0",
                  "fees": "1", "slippage": "5", "margin": "155", "contract_cap": "100"}


def number(value) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("Valor numérico inválido")
    text = str(value).strip().replace("R$", "").replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        result = Decimal(text)
    except InvalidOperation:
        raise ValueError("Informe um número válido") from None
    if not result.is_finite() or abs(result) > Decimal("1000000000000"):
        raise ValueError("Número fora do intervalo permitido")
    return result


def money(value) -> str:
    if value is None:
        return "—"
    return "R$ " + f"{number(value):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def build_risk_study(values: dict, *, now_ms: int | None = None, last_loss_ms: int | None = None) -> dict:
    clean = {key: str(number(values.get(key, default))) for key, default in DEFAULT_INPUTS.items()}
    for key in ("loss_streak", "slippage", "contract_cap"):
        value = number(clean[key])
        if value != value.to_integral_value() or value < 0:
            raise ValueError("Sequência, slippage e teto devem ser inteiros não negativos")
        clean[key] = str(int(value))
    if not 1 <= int(clean["contract_cap"]) <= 10000 or number(clean["fees"]) < 0 or number(clean["margin"]) <= 0:
        raise ValueError("Confira custos, margem e teto de contratos")
    config, snapshot = example_from_inputs(load_json(resource_path("config.json")), clean)
    config["risk"]["max_contracts"] = int(clean["contract_cap"])
    config["costs"]["round_trip_fees_brl_per_contract"] = clean["fees"]
    config["costs"]["slippage_points_round_trip"] = int(clean["slippage"])
    snapshot["account"]["broker_margin_brl_per_contract"] = clean["margin"]
    loss_time_assumption = None
    if now_ms is not None:
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("Horário de cálculo inválido")
        snapshot["ts_ms"] = now_ms
        snapshot["account"]["asof_ms"] = now_ms
        if last_loss_ms is None and int(clean["loss_streak"]) > 0:
            last_loss_ms = max(0, now_ms - config["risk"]["cooldown_after_loss_ms"] - 1)
            loss_time_assumption = "manual_scenario_assumes_prior_loss_cooldown_elapsed"
        snapshot["account"]["last_loss_ms"] = last_loss_ms
    candidate = snapshot["candidates"][0]
    candidate["quantity_requested"] = int(clean["contract_cap"])
    now = snapshot["ts_ms"]
    projection = project_stop_capacity(config, snapshot["account"], candidate, now, max_attempts=200)
    comparisons = compare_risk_policies(config, snapshot["account"], candidate, now, max_attempts=200)
    return {"config": config, "account": snapshot["account"], "candidate": candidate,
            "projection": projection, "comparisons": comparisons, "inputs": clean,
            "account_source": "manual_scenario", "broker_connected": False, "loss_time_assumption": loss_time_assumption,
            "actionable_live_signal": False, "win_probability": None}


def apply_manual_pnl(values: dict, pnl) -> dict:
    study = build_risk_study(values)
    result = dict(study["inputs"])
    change = number(pnl)
    current = number(result["current"]) + change
    # Preserve a loss that exhausts the scenario instead of leaving the old
    # balance on screen. Subsequent risk studies reject nonpositive equity.
    result["current"] = str(current)
    result["peak"] = str(max(number(result["peak"]), number(result["start"]), current))
    losses = int(result["loss_streak"])
    result["loss_streak"] = str(losses + 1 if change < 0 else 0 if change > 0 else losses)
    return result


class ObservationSession:
    def __init__(self, symbol="WIN_SIM"):
        self.symbol = symbol
        self.engine = FlowEngine(symbol, rules=load_json(resource_path("flow_rules.json")))
        self.mode = "idle"
        self.clock_ms = None
        self.source_generation = 0
        self.chart = deque(maxlen=500)
        self.warnings = []
        self.last_quote = None
        self.last_book = None
        self.book_history = deque(maxlen=64)
        self.volume_at_price = []
        self.source_capabilities = {}
        self.capture_evidence = {}

    def reset(self, symbol=None):
        if symbol:
            self.symbol = symbol
        self.engine = FlowEngine(self.symbol, rules=load_json(resource_path("flow_rules.json")))
        self.clock_ms = None
        self.chart.clear()
        self.warnings = []
        self.last_quote = None
        self.last_book = None
        self.book_history.clear()
        self.volume_at_price = []
        self.source_capabilities = {}
        self.capture_evidence = {}
        self.source_generation += 1

    def demo(self, mode="progression", side="buy") -> dict:
        self.reset("WIN_SIM")
        fixture = generate_flow_scenario(mode, side=side, end_ms=int(time.time() * 1000))
        self.mode = "synthetic"
        self.engine.set_source_quality(fixture["source_quality"])
        for event in fixture["events"]:
            if event["type"] == "book":
                self.engine.set_book(event)
                self.last_book = {**event, 'market_ts_ms':event['ts_ms'], 'captured_at_ms':event['ts_ms'], 'kind':'synthetic_book_snapshot'}
                self.book_history.append(deepcopy(self.last_book))
            elif self.engine.add_trade(event)["accepted"]:
                self.chart.append((event["ts_ms"], float(event["price_points"])))
        self.clock_ms = fixture["now_ms"]
        self.warnings = ["Demonstração gerada localmente. Não são preços atuais da B3."]
        return self.snapshot()

    def ingest(self, batch, *, replay=False) -> dict:
        if replay:
            self.reset(self.symbol)
        self.mode = "replay" if replay else "excel_observation"
        quality = batch.health.to_dict()
        quality["data_origin"] = "replay" if replay else "live"
        if not replay:
            # Successful Excel reads do not prove a Nelogica market connection.
            quality["feed_connected"] = None
        self.engine.set_source_quality(quality)
        self.warnings = list(batch.warnings)
        for event in batch.events:
            data = event.to_dict()
            if not data.get("id"):
                self.warnings.append("Negócios sem ID não alimentam o acumulador: repetição entre leituras não é verificável.")
                continue
            data["aggressor"] = data["aggressor"].lower()
            result = self.engine.add_trade(data)
            if result["accepted"]:
                self.chart.append((data["ts_ms"], float(data["price_points"])))
            elif result["reason"] not in ("DUPLICATE_ID", "DUPLICATE_TRADE"):
                self.warnings.append("Evento rejeitado: " + result["reason"])
        self.source_capabilities = dict(batch.capabilities)
        self.capture_evidence = {**batch.evidence, "received_at_ms": int(time.time() * 1000)}
        self.volume_at_price = list(batch.aggregates)
        for book in batch.books:
            if book.get("market_ts_ms") is not None:
                result = self.engine.set_book({**book, "ts_ms": book["market_ts_ms"]})
                if not result["accepted"] and result["reason"] != "DUPLICATE_BOOK":
                    self.warnings.append("Snapshot do livro rejeitado: " + result["reason"])
                    continue
            self.last_book = deepcopy(book)
            self.book_history.append(deepcopy(book))
        for quote in batch.quotes:
            self.last_quote = quote
            # RTD DAT/HOR is not established as each book update's timestamp.
            # Keep sampled quote values distinct from authoritative depth events.
            self.warnings.append("Ofertas RTD são valores amostrados; DAT/HOR não confirma a sequência do livro.")
            if quote.bid is not None and quote.ask is not None and quote.ask <= quote.bid:
                self.warnings.append("Ofertas travadas ou cruzadas: spread da amostra indisponível.")
            if quote.ts_ms is not None:
                point = (quote.ts_ms, quote.last)
                if not self.chart or point[0] > self.chart[-1][0]:
                    self.chart.append(point)
        if replay:
            stamps = [x.ts_ms for x in batch.events] + [x.ts_ms for x in batch.quotes if x.ts_ms is not None]
            if not stamps:
                raise ValueError("Replay sem horário de origem utilizável")
            self.clock_ms = max(stamps)
        else:
            self.clock_ms = None
        self.warnings = list(dict.fromkeys(self.warnings))[:30]
        return self.snapshot()

    def snapshot(self) -> dict:
        now = self.clock_ms if self.clock_ms is not None else int(time.time() * 1000)
        state = self.engine.snapshot(now)
        state["application_mode"] = self.mode
        state["source_generation"] = self.source_generation
        state["warnings"] = list(self.warnings)
        state["last_quote"] = vars(self.last_quote) if self.last_quote is not None else None
        state["order_flow"].update({"book": deepcopy(self.last_book), "book_history": list(self.book_history),
                                    "volume_at_price": list(self.volume_at_price),
                                    "source_capabilities": dict(self.source_capabilities),
                                    "capture_evidence": dict(self.capture_evidence)})
        return state


def jev_observation_state(snapshot: dict) -> dict:
    return {"instrument": snapshot["symbol"], "asof_ms": snapshot["ts_ms"],
            "source_generation": snapshot["source_generation"],
            "mode": snapshot["application_mode"], "task": "Classify observed tape context only. No trade instruction or future win probability.",
            "computed_features": deepcopy(snapshot["computed_features"]),
            "evidence_coverage": deepcopy(snapshot["evidence_coverage"]),
            "measurement_limits": list(snapshot.get("warnings", [])),
            "definitions": {"progression": "Price advanced with dominant executed aggression during the measured window.",
                            "absorption": "Aggression occurred without comparable price progress; passive absorption remains a hypothesis.",
                            "exhaustion": "Previously advancing aggression decelerated and failed to continue. This does not predict reversal.",
                            "book": "Visible quantities only. Order identity, hidden volume and reasons for changes are unknown."}}


PREMISE_TEXT_LIMIT = 300


def premise_questions() -> dict:
    """Independent judgments about the user's declared reading of the market.

    Support, contradiction and evaluability stay separate dimensions: absent
    support is not contradiction, and insufficient evidence remains explicit.
    """
    return {
        "premise_evidence_support": {
            "type": "noul",
            "instructions": ("Does state.computed_features with state.evidence_coverage support the market expectation "
                             "the user declared in state.user_premise.text? Judge observed evidential support only; "
                             "this is not a profit probability or a recommendation. Partial or stale coverage weakens support.")},
        "premise_evidence_contradiction": {
            "type": "noul",
            "instructions": ("Does the observed evidence directly contradict the user's declared expectation in "
                             "state.user_premise.text? Absence of support is not contradiction; answer yes only for "
                             "actively conflicting observed evidence.")},
        "premise_evaluable": {
            "type": "noul",
            "instructions": ("Is the observed evidence sufficient to evaluate the user's declared expectation in "
                             "state.user_premise.text at all? Answer no when coverage limits, stale data or missing "
                             "aggression prevent judging support or contradiction for what the text describes.")},
    }


def declared_premise(text: str, *, asof_ms: int) -> dict | None:
    """Bounded user-authored expectation carried verbatim into the JEV state."""
    text = " ".join(str(text or "").split())
    if not text:
        return None
    return {"text": text[:PREMISE_TEXT_LIMIT], "declared_at_ms": asof_ms}


def can_classify(snapshot: dict, *, now_ms: int | None = None) -> tuple[bool, str]:
    features, coverage = snapshot["computed_features"], snapshot["evidence_coverage"]
    if snapshot.get("application_mode") == "excel_observation":
        now = int(time.time()*1000) if now_ms is None else now_ms
        stamp = snapshot.get("flow_ts_ms")
        if type(stamp) is not int or not 0 <= now-stamp <= 2000:
            return False, "Os negócios de origem estão ausentes ou atrasados para uma nova classificação."
    if not coverage.get("integrity_ok"):
        return False, "Integridade dos eventos não confirmada; reconecte a fonte."
    if not coverage.get("tape_fresh") or features.get("trade_count", 0) < 5:
        return False, "São necessários negócios recentes com horário e ID; cotação isolada não permite leitura de fluxo."
    if features.get("unknown_aggressor_contracts", 0) == features.get("total_contracts", 0):
        return False, "Agressor desconhecido em todos os negócios recebidos."
    return True, "Classificação descritiva; cobertura parcial continua explícita."


def response_is_current(current_snapshot: dict | None, request_flow_ts_ms: int | None, *, now_ms: int) -> bool:
    if current_snapshot is None:
        return False
    if current_snapshot.get("application_mode") != "excel_observation":
        return True  # Its fixed replay/demo reference is explicitly historical.
    return (type(request_flow_ts_ms) is int and 0 <= now_ms-request_flow_ts_ms <= 2000
            and can_classify(current_snapshot, now_ms=now_ms)[0])


def build_decision_bundle(session: ObservationSession | None, values: dict, *,
                          last_loss_ms: int | None = None, latest_jev_result: dict | None = None) -> dict:
    """Build the same explicit evidence view for the desktop and HTML report."""
    from candidate_research import build_market_candidates
    from recommendation_engine import build_recommendation
    snapshot = session.snapshot() if session is not None else None
    now = snapshot["ts_ms"] if snapshot is not None else int(time.time() * 1000)
    study, error = None, None
    try:
        study = build_risk_study(values, now_ms=now,
                                 last_loss_ms=last_loss_ms if snapshot is None or snapshot["application_mode"] == "excel_observation" else None)
    except (ValueError, KeyError) as exc:
        error = str(exc)
    technical = {"rows": [], "reference_levels": [], "reasons": [], "evidence_coverage": {}}
    if snapshot is not None and study is not None:
        technical = build_market_candidates(session.engine, snapshot, study["config"], study["account"], now)
    recommendation = build_recommendation(snapshot, technical, study, latest_jev_result, now_ms=now)
    recommendation["origin"]["source_generation"] = snapshot.get("source_generation") if snapshot is not None else None
    return {"snapshot": snapshot, "study": study, "technical": technical,
            "recommendation": recommendation, "input_error": error, "evaluated_at_ms": now,
            "chart_points": list(session.chart) if session is not None else [],
            "purpose": "evidence_and_manual_risk_review", "actual_broker_connection": False}


def self_check() -> dict:
    from candidate_research import build_market_candidates, generate_candidate_scenario
    from recommendation_engine import build_recommendation
    checks = {}
    for mode in ("progression", "absorption", "exhaustion", "choppy"):
        session = ObservationSession()
        snapshot = session.demo(mode)
        assert snapshot["computed_features"]["trade_count"] > 0
        assert snapshot["actionable_live_signal"] is False
        assert "account" not in jev_observation_state(snapshot)
        checks[mode] = [h["id"] for h in snapshot["hypotheses"] if h["status"] in {"potential", "observed"}]
    small = build_risk_study(DEFAULT_INPUTS)
    large = build_risk_study(dict(DEFAULT_INPUTS, current="4000", peak="4000"))
    assert small["projection"]["current_sizing"]["contracts"] == 2
    assert large["projection"]["current_sizing"]["contracts"] == 22
    assert apply_manual_pnl(DEFAULT_INPUTS, "-20")["current"] == "380"
    fixture = generate_candidate_scenario()
    engine = FlowEngine(fixture["symbol"])
    engine.set_source_quality(fixture["source_quality"])
    for event in fixture["events"]:
        outcome = engine.add_trade(event) if event["type"] == "trade" else engine.set_book(event)
        assert outcome["accepted"]
    technical_study = build_risk_study(DEFAULT_INPUTS, now_ms=fixture["now_ms"])
    technical = build_market_candidates(engine, engine.snapshot(fixture["now_ms"]),
                                        technical_study["config"], technical_study["account"], fixture["now_ms"])
    assert len(technical["rows"]) == 8
    assert any(row["risk"]["status"] == "ALLOW_SIMULATION" for row in technical["rows"])
    state = engine.snapshot(fixture["now_ms"])
    state.update(application_mode="synthetic", source_generation=0)
    decision = build_recommendation(state, technical, technical_study, now_ms=fixture["now_ms"])
    assert decision["status"] == "AGUARDAR"
    assert len(decision["options"]) == 8
    assert decision["order_sent"] is False
    return {"status": "passed", "demo_checks": checks, "capital_400_contracts": 2,
            "capital_4000_contracts": 22, "synthetic_technical_candidates": len(technical["rows"]),
            "decision_state_without_jev": decision["status"], "decision_options": len(decision["options"]), "actual_jev_api_tested": False,
            "actual_profit_connection_tested": False, "order_execution": False}

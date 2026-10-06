"""Readable evidence projection and self-contained HTML report, without API keys."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from html import escape
from pathlib import Path

from app_core import money, number
from app_store import VERSION

STATUS_LABELS = {"SEM_DADOS": "SEM DADOS SUFICIENTES", "AGUARDAR": "AGUARDAR CONFIRMAÇÃO",
                 "BLOQUEADO_RISCO": "BLOQUEADO PELO RISCO", "HIPOTESE_PARA_REVISAO": "HIPÓTESE PARA REVISÃO"}
MODE_LABELS = {"synthetic": "Demonstração sintética", "replay": "Replay histórico", "excel_observation": "Excel · amostra de mercado"}
CHOICE_LABELS = {"buy_progression": "Progressão compradora", "sell_progression": "Progressão vendedora",
                 "possible_buy_absorption": "Possível absorção de compras", "possible_sell_absorption": "Possível absorção de vendas",
                 "possible_exhaustion": "Possível exaustão", "mixed_or_insufficient": "Contexto misto ou insuficiente"}
REASONS = {
    "SOURCE_AND_VALID_CLOCK_REQUIRED": "Carregar uma fonte identificada com horário válido.",
    "EXECUTED_TRADE_DATA_REQUIRED": "Faltam negócios individuais; cotação isolada não permite análise do fluxo.",
    "IDENTIFIED_DATA_ORIGIN_REQUIRED": "A origem dos dados precisa estar identificada.",
    "DATA_ORIGIN_MODE_MISMATCH": "A origem declarada não corresponde ao modo selecionado.",
    "STALE_OR_FUTURE_TAPE": "Os negócios de origem estão atrasados ou com horário futuro.",
    "SOURCE_INTEGRITY_REQUIRED": "A sequência observada apresentou falha de integridade.",
    "FRESH_TWO_SIDED_QUOTE_REQUIRED": "Faltam ofertas de compra e venda com horário recente.",
    "QUOTE_COVERAGE_UNAVAILABLE": "A cobertura das ofertas não está disponível.",
    "COMPLETE_TAPE_SOURCE_NOT_VERIFIED": "A captura integral do tape não foi comprovada; as medidas descrevem a amostra.",
    "SHORT_WINDOW_INCOMPLETE": "A janela curta ainda não possui cobertura suficiente.",
    "UNKNOWN_AGGRESSOR_COVERAGE": "Parte dos negócios não possui agressor identificado.",
    "EXPLICIT_MANUAL_SCENARIO_REQUIRED": "Confira os valores do cenário de capital manual.",
    "OBSERVED_STOP_TARGET_GEOMETRY_REQUIRED": "Não há referências observadas suficientes para stop e alvo.",
    "OBSERVED_REFERENCE_LEVELS_REQUIRED": "Ainda faltam níveis de preço observados nos negócios.",
    "JEV_NOT_EVALUATED": "O JEV ainda não avaliou este contexto.",
    "JEV_STALE_OR_FUTURE_SOURCE": "A resposta do JEV refere-se a dados que já venceram o prazo da avaliação.",
    "JEV_SOURCE_MISMATCH": "A resposta do JEV pertence a outra fonte ou contrato.",
    "JEV_SOURCE_GENERATION_MISMATCH": "A resposta do JEV pertence a uma conexão anterior.",
    "JEV_REFERENCE_CLOCK_MISMATCH": "O horário da resposta não corresponde ao contexto enviado.",
    "JEV_RESULT_INVALID_OR_INCOMPLETE": "A resposta do JEV está incompleta ou não respeitou o formato esperado.",
    "MODEL_CONTEXT_MIXED_OR_INSUFFICIENT": "O modelo classificou o contexto como misto ou insuficiente.",
    "FINANCIAL_VETO_PRECEDES_MODEL": "Um limite financeiro bloqueou a proposta antes da avaliação contextual.",
    "LOSS_COOLDOWN_ACTIVE": "A pausa após a perda registrada ainda está ativa.",
    "CONSECUTIVE_LOSS_LIMIT_REACHED": "O limite de perdas consecutivas foi atingido.",
    "DAILY_LOSS_LIMIT_REACHED": "O limite de perda diária foi atingido.",
    "PEAK_DRAWDOWN_LIMIT_REACHED": "O limite de devolução desde o pico foi atingido.",
    "CAPITAL_EXHAUSTED": "O capital do cenário está esgotado.",
    "RISK_BUDGET_EXHAUSTED": "Não há orçamento de risco restante.",
    "INSUFFICIENT_RISK_BUDGET": "O risco de um contrato não cabe no orçamento restante.",
    "INSUFFICIENT_MARGIN_AFTER_BUFFER": "A margem disponível não comporta o cenário e sua reserva.",
    "NET_REWARD_RISK_BELOW_MINIMUM": "A relação entre ganho e risco após custos não atende à regra informada.",
    "NO_CANDIDATE_WITHIN_RISK_BUDGET": "Nenhum cenário calculado cabe no orçamento de risco.",
    "CURRENT_OBSERVED_LEVEL_EVIDENCE_REQUIRED": "As referências de preço precisam de evidência atual.",
    "PREVIOUS_WINDOW_REQUIRED_FOR_EXHAUSTION": "A exaustão exige comparação com uma janela anterior completa.",
    "EXISTING_POSITION_OR_PENDING_ENTRY": "Há posição ou entrada pendente informada no estado da conta.",
    "STALE_OR_FUTURE_ACCOUNT": "O estado de conta fornecido está fora do prazo de validade.",
    "INVALID_ACCOUNT": "Os campos do cenário de conta são inválidos ou incoerentes.",
}


def reason_text(code):
    return REASONS.get(str(code), str(code).replace("_", " ").capitalize())


def timestamp_text(stamp):
    try:
        if type(stamp) is not int or not 0 <= stamp <= 32503680000000:
            return "Horário indisponível"
        return datetime.fromtimestamp(stamp / 1000, timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M:%S BRT")
    except (ValueError, OSError, OverflowError):
        return "Horário indisponível"


def financial_text(value):
    try:
        return money(value)
    except (ValueError, ArithmeticError):
        return "—"


def evidence_lines(bundle):
    rec = bundle.get("recommendation") or {}
    lines = []
    if bundle.get("input_error"):
        lines.extend(["CONFERIR CAPITAL", str(bundle["input_error"]), ""])
    for key, title in (("reasons", "POR QUE ESTE ESTADO"), ("missing_evidence", "O QUE FALTA CONFIRMAR"),
                       ("contradictions", "EVIDÊNCIAS CONTRÁRIAS")):
        items = list(dict.fromkeys(rec.get(key, [])))
        if items:
            lines += [title] + ["• " + reason_text(item) for item in items] + [""]
    model = rec.get("model") or {}
    if model.get("available"):
        lines += ["LEITURA DO JEV", CHOICE_LABELS.get(model.get("choice"), str(model.get("choice"))),
                  "Avaliação atual na referência do painel." if model.get("current") else "Avaliação histórica ou fora do prazo.",
                  f"Confiança na classificação: {model.get('classification_confidence', '—')}. Não é probabilidade de lucro.", ""]
    lines += ["PRESSUPOSTOS DO CÁLCULO", "Capital, margem e ausência de posições são informados manualmente. A conta Toro não está conectada.",
              "Os cenários não foram classificados por lucro esperado. Nenhuma ordem é enviada."]
    if rec.get("account_assumptions", {}).get("loss_time_assumption"):
        lines.append("Sem horário registrado para a perda anterior: este cenário assume que a pausa já foi cumprida. A sequência de perdas continua sendo considerada.")
    return "\n".join(lines)


def option_values(option):
    risk = option.get("risk") or {}
    contracts = option.get("contracts", 0)
    try:
        total = number(risk["risk_per_contract_brl"]) * number(contracts)
        risk_text = money(total)
    except (KeyError, ValueError, ArithmeticError):
        risk_text = "—"
    evidence = option.get("model_evidence") or {}
    def score(key):
        value = evidence.get(key)
        return f"{value:.3f}" if isinstance(value, (float, int)) and not isinstance(value, bool) else "—"
    return ("Compra" if option.get("side") == "buy" else "Venda", option.get("entry_points", "—"),
            option.get("stop_points", "—"), option.get("target_points", "—"), contracts,
            risk_text, score("support"), score("contradiction"), STATUS_LABELS.get(option.get("status"), str(option.get("status", "—"))))


def _sparkline(points):
    values = []
    for point in list(points or [])[-500:]:
        try:
            value = float(number(point[1]))
            values.append(value)
        except (ValueError, TypeError, IndexError, ArithmeticError):
            continue
    if len(values) < 2:
        return '<p class="muted">Sem amostras suficientes para o gráfico.</p>'
    low, high = min(values), max(values)
    span = max(high-low, 5)
    coords = " ".join(f"{15+i/(len(values)-1)*930:.1f},{165-(v-low)/span*125:.1f}" for i, v in enumerate(values))
    return f'<svg viewBox="0 0 960 185" role="img" aria-label="Preços capturados; dados do registro"><line x1="15" y1="166" x2="945" y2="166" stroke="#334b60"/><polyline points="{coords}" fill="none" stroke="#63d4b5" stroke-width="2.5"/></svg>'


def render_panel_html(bundle):
    """A static record of the actual view-model, not a browser market connection."""
    rec = bundle.get("recommendation") or {}
    snapshot = bundle.get("snapshot") or {}
    study = bundle.get("study") or {}
    inputs = study.get("inputs") or {}
    features = snapshot.get("computed_features") or {}
    model = rec.get("model") or {}
    e = lambda value: escape(str(value), quote=True)
    origin = MODE_LABELS.get(snapshot.get("application_mode"), "Sem fonte")
    rows = []
    for option in rec.get("options", [])[:8]:
        rows.append('<tr>' + ''.join('<td>'+e(v)+'</td>' for v in option_values(option)) + '</tr>')
    if not rows:
        rows = ['<tr><td colspan="9">Nenhum cenário utilizável neste registro.</td></tr>']
    cards = [("Fonte", origin), ("Contrato", snapshot.get("symbol", "—")),
             ("Capital manual", financial_text(inputs.get("current"))),
             ("JEV", "Avaliação na referência" if model.get("current") else "Sem avaliação atual")]
    card_html = ''.join(f'<div class="card"><small>{e(k)}</small><strong>{e(v)}</strong></div>' for k,v in cards)
    hypotheses = []
    names = {"progression": "Progressão", "absorption": "Absorção potencial", "exhaustion": "Exaustão potencial", "liquidity_withdrawal": "Redução de liquidez"}
    statuses = {"observed": "Observado", "potential": "Hipótese", "inconclusive": "Dados insuficientes", "not_observed": "Não observado"}
    for item in snapshot.get("hypotheses", []):
        hypotheses.append(f'<li>{e(names.get(item.get("kind"),item.get("kind")))} · {e(item.get("side"))}: <b>{e(statuses.get(item.get("status"),item.get("status")))}</b></li>')
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>JEV WIN — registro visual da avaliação</title><style>
:root{{color-scheme:dark}}*{{box-sizing:border-box}}body{{margin:0;background:#0d1723;color:#e5eff6;font:16px/1.5 system-ui,"Segoe UI",sans-serif}}main{{max-width:1250px;margin:auto;padding:34px 28px}}header{{display:flex;gap:20px;justify-content:space-between;align-items:end}}h1{{font-size:30px;margin:0}}h2{{font-size:20px;margin:0 0 14px}}small,.muted{{color:#9fb3c6}}.eyebrow{{color:#6ed5b8;font-weight:700;letter-spacing:2px}}.notice{{background:#283125;border:1px solid #8b7948;color:#eed9a1;border-radius:12px;padding:12px 16px;margin:22px 0}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.card,section{{background:#162638;border:1px solid #2a4156;border-radius:14px;padding:20px}}.card small,.card strong{{display:block}}.card strong{{font-size:20px;margin-top:8px}}.hero{{margin:18px 0;border-left:4px solid #e2bd72}}.hero .status{{color:#f2ce8b;font-size:25px;font-weight:800;margin-bottom:8px}}.hero p{{margin:0}}.split{{display:grid;grid-template-columns:1.2fr 1fr;gap:16px;margin:16px 0}}pre{{white-space:pre-wrap;font:14px/1.6 system-ui,sans-serif;margin:0}}ul{{padding-left:20px;font-size:14px}}table{{border-collapse:collapse;width:100%;font-size:13px;white-space:nowrap}}th,td{{padding:11px 9px;border-bottom:1px solid #2a4156;text-align:left}}th{{color:#9fb3c6;font-weight:500}}.tablewrap{{overflow:auto}}svg{{width:100%;height:auto}}footer{{margin:22px 0 0;color:#9fb3c6;font-size:13px}}@media(max-width:760px){{main{{padding:20px 12px}}.cards{{grid-template-columns:repeat(2,1fr)}}.split{{grid-template-columns:1fr}}header{{display:block}}.hero .status{{font-size:21px}}}}@media print{{body{{background:white;color:#172536}}.card,section{{break-inside:avoid;background:white;border-color:#9fb3c6}}.muted,small,th,footer{{color:#465969}}.hero .status{{color:#634812}}}}
</style></head><body><main><header><div><div class="eyebrow">FLUXO · EVIDÊNCIA · CAPITAL</div><h1>JEV WIN <small>v{VERSION}</small></h1></div><div class="muted">{e(timestamp_text(bundle.get("evaluated_at_ms")))}</div></header>
<div class="notice"><b>Registro estático da Central de decisão.</b> Origem: {e(origin)}. Este arquivo não acompanha o mercado, não consulta a API e não envia ordens. Nenhuma rentabilidade foi validada.</div>
<div class="cards">{card_html}</div><section class="hero"><div class="status">{e(STATUS_LABELS.get(rec.get("status"),rec.get("status","SEM DADOS")))}</div><p>{e(rec.get("action","Carregar uma fonte para avaliar."))}</p></section>
<section><h2>Preços capturados</h2>{_sparkline(bundle.get("chart_points"))}<div class="muted">Delta capturado em 5 s: {e(features.get("delta_contracts","—"))} · Contratos: {e(features.get("total_contracts","—"))} · O gráfico mostra amostras recebidas, sem previsão.</div></section>
<div class="split"><section><h2>Evidências e impedimentos</h2><pre>{e(evidence_lines(bundle))}</pre></section><section><h2>Hipóteses de fluxo</h2><ul>{''.join(hypotheses) or '<li>Sem dados para comparar.</li>'}</ul><p class="muted">Absorção e exaustão são hipóteses sobre os eventos observados. Não identificam intenção, ordens ocultas ou reversão futura.</p></section></div>
<section><h2>Cenários calculados</h2><p class="muted">Capital manual; risco recalculado por geometria. Apoio e contradição são avaliações contextuais, quando disponíveis. Não há ranking de lucro esperado.</p><div class="tablewrap"><table><thead><tr>{''.join('<th>'+e(h)+'</th>' for h in ('Direção','Entrada','Stop','Alvo','Contratos','Perda planejada','Apoio','Contradição','Estado'))}</tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>
<footer>Fonte e critérios são os mesmos usados pela interface desktop. Este relatório tem apresentação própria; não é uma captura da janela Windows. Chaves e credenciais não são incluídas. Campos de conta são informados manualmente.</footer></main></body></html>'''


def export_panel(path: str | Path, bundle: dict) -> None:
    Path(path).write_text(render_panel_html(bundle), encoding="utf-8")

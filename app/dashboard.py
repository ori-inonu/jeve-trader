"""Desktop research panel for Windows. No Profit connection or order functions.

Run: python dashboard.py
API classification happens only when the user explicitly presses its button.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from capital_planner import project_stop_capacity
from copilot import Copilot, ROOT, demo_snapshot, finite, load_json, profile_config, quality_reasons


REASON_LABELS = {
    "CONSECUTIVE_LOSS_LIMIT_REACHED": "limite de perdas consecutivas atingido",
    "DAILY_LOSS_LIMIT_REACHED": "limite de perda diária atingido",
    "PEAK_DRAWDOWN_LIMIT_REACHED": "limite de queda desde o pico atingido",
    "STOP_RISK_EXCEEDS_BUDGET": "o stop necessário excede o orçamento restante",
    "RISK_BUDGET_EXHAUSTED": "orçamento de risco esgotado",
    "INSUFFICIENT_MARGIN_AFTER_BUFFER": "margem insuficiente após as reservas",
    "NET_REWARD_RISK_TOO_LOW": "relação líquida entre ganho e risco insuficiente",
    "NO_CANDIDATE_WITHIN_RISK_BUDGET": "nenhuma hipótese cabe no orçamento de risco",
    "RESEARCH_ONLY_NO_VALIDATED_PREDICTIVE_EDGE": "hipótese de pesquisa; rentabilidade ainda não validada",
    "LOSS_COOLDOWN_ACTIVE": "pausa após perda ainda em andamento",
    "JEV_UNAVAILABLE_OR_RESPONSE_INVALID": "JEV indisponível ou resposta não utilizável",
    "NO_SUPPORTED_CANDIDATE": "nenhuma hipótese com evidência suficiente",
    "FLOW_INCONCLUSIVE": "leitura do fluxo inconclusiva",
    "INFERENCE_EXPIRED": "a análise terminou depois do prazo de validade",
    "INVALID_PEAK_EQUITY": "pico de patrimônio ausente ou inconsistente",
    "INVALID_ACCOUNT": "dados de conta incompletos",
    "ACCOUNT_EQUITY_MISMATCH": "o saldo não confere com os resultados informados",
    "ACCOUNT_NOT_RECONCILED": "conta ainda não conciliada",
    "EXISTING_POSITION_OR_PENDING_ENTRY": "já existe posição ou entrada pendente",
    "STALE_OR_FUTURE_ACCOUNT": "dados de conta fora da validade",
    "PROJECTION_LIMIT_REACHED": "limite de cálculo da projeção atingido"
}


def human_reasons(reasons):
    return "; ".join(REASON_LABELS.get(reason, "dados insuficientes ou fora da validade") for reason in reasons)


def format_capacity(report: dict) -> str:
    trajectory = report["trajectories"]["real_policy"]
    diagnostic = report["trajectories"]["budget_only_ignoring_streak_projection"]
    sizing = report["current_sizing"]
    policy_count = (f"pelo menos {trajectory['attempts']} calculadas; projeção truncada"
                    if trajectory["truncated_at_max_attempts"] else str(trajectory["attempts"]))
    diagnostic_count = (f"pelo menos {diagnostic['attempts']} calculadas; projeção truncada"
                        if diagnostic["truncated_at_max_attempts"] else str(diagnostic["attempts"]))
    rows = [
        "CENÁRIO DE STOPS CONSECUTIVOS",
        "Pressupõe repetir a mesma estrutura de stop.",
        "Não prevê que novas oportunidades aparecerão.", "",
        f"Tentativas na projeção da política: {policy_count}",
        f"Capacidade financeira sem a trava de sequência: {diagnostic_count}",
        "A segunda contagem é somente diagnóstico.", "",
        f"Risco por contrato: R$ {sizing.get('risk_per_contract_brl', '—')}",
        f"Margem por contrato: R$ {sizing.get('margin_per_contract_brl', '—')}",
        "Margem e perda planejada são consideradas juntas.", ""
    ]
    for step in trajectory["steps"][:30]:
        rows += [f"Tentativa {step['attempt']} · {step['contracts']} contrato(s)",
                 f"  Capital: R$ {step['equity_before_brl']} → R$ {step['equity_after_brl']}",
                 f"  Perda planejada: R$ {step['planned_stop_loss_brl']}"]
    rows += ["", "Interrupção: " + human_reasons(trajectory["stop_reasons"]), "",
             "Slippage, gaps, liquidez e custos reais podem reduzir esta capacidade.",
             "O depósito não é garantia de perda máxima."]
    return "\n".join(rows)


def format_decision(result: dict) -> str:
    rows = ["ANÁLISE PARA PESQUISA", f"Resultado: {result['status']}",
            f"Origem: {result.get('data_origin', 'desconhecida')}",
            "Sinal para conta real: desabilitado", "Chance de lucro: não estimada", ""]
    response = result.get("model_response", {})
    flow = response.get("answers", {}).get("flow_interpretation", {})
    names = {"buying_with_price_acceptance": "Compras agressoras com aceitação de preços mais altos",
             "selling_with_price_acceptance": "Vendas agressoras com aceitação de preços mais baixos",
             "buying_absorbed": "Compras agressoras aparentemente absorvidas",
             "selling_absorbed": "Vendas agressoras aparentemente absorvidas", "inconclusive": "Fluxo inconclusivo"}
    if flow:
        rows += ["Interpretação: " + names.get(flow.get("choice"), "indisponível"), ""]
    for candidate in result.get("candidates_for_review", []):
        rows += [f"Hipótese de {'compra' if candidate['side'] == 'buy' else 'venda'}",
                 f"  Entrada do exemplo: {candidate['entry_points']}",
                 f"  Stop: {candidate['stop_points']} · Alvo: {candidate['target_points']}",
                 f"  Quantidade calculada: {candidate['contracts']}",
                 f"  Risco por contrato: R$ {candidate['risk']['risk_per_contract_brl']}", ""]
    rows += ["Motivos: " + human_reasons(result.get("reasons", [])), "",
             "Uma interpretação favorável do fluxo não garante a direção futura."]
    return "\n".join(rows)


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


class Dashboard:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.base_config = load_json(ROOT / "config.json")
        self.questions = load_json(ROOT / "questions.json")
        self.config = profile_config(self.base_config, "agressivo_pesquisa")
        self.snapshot = demo_snapshot()
        self.results: queue.Queue = queue.Queue()
        self.busy = False
        self.generation = 0
        self.closed = False
        self.replay_path: Path | None = None
        self.replay_mtime = None
        self.selected_candidate_id = self.snapshot["candidates"][0]["id"]
        self.watch_file = tk.BooleanVar(value=False)
        root.title("JEV • WIN | Laboratório de capital e fluxo")
        root.geometry("1220x900")
        root.minsize(1050, 760)
        root.configure(background="#101923")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background="#101923")
        style.configure("TLabel", background="#101923", foreground="#e4eef7", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Muted.TLabel", foreground="#98b1c7")
        style.configure("Warn.TLabel", foreground="#efc16b")
        style.configure("Value.TLabel", font=("Segoe UI", 18, "bold"), foreground="#69d5b2")
        style.configure("TLabelframe", background="#101923", bordercolor="#314458")
        style.configure("TLabelframe.Label", background="#101923", foreground="#d9e6f1", font=("Segoe UI", 11, "bold"))
        style.configure("TButton", padding=(9, 6), font=("Segoe UI", 10))
        container = ttk.Frame(root, padding=18)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(4, weight=1)
        ttk.Label(container, text="JEV / WIN", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        self.status = ttk.Label(container, text="PESQUISA OFFLINE • Profit/Toro não conectados • Nenhuma ordem", style="Warn.TLabel")
        self.status.grid(row=1, column=0, sticky="w", pady=(2, 12))
        form = ttk.LabelFrame(container, text="Cenário sintético — capital e gerenciamento configuráveis", padding=12)
        form.grid(row=2, column=0, sticky="ew")
        fields = [("start", "Capital no início (R$)", "400"), ("current", "Capital atual (R$)", "400"),
                  ("peak", "Pico da sessão (R$)", "400"), ("risk_pct", "Risco por proposta (%)", "15"),
                  ("daily_pct", "Perda diária inicial (%)", "50"), ("drawdown_pct", "Queda máxima do pico (%)", "50"),
                  ("stop", "Stop do exemplo (pontos)", "100"), ("target", "Alvo do exemplo (pontos)", "200"),
                  ("loss_streak", "Perdas consecutivas", "0")]
        self.inputs = {}
        for i, (name, label, default) in enumerate(fields):
            column, row = i % 4, (i // 4) * 2
            form.columnconfigure(column, weight=1)
            ttk.Label(form, text=label).grid(row=row, column=column, sticky="w", padx=6)
            entry = ttk.Entry(form, width=20)
            entry.insert(0, default)
            entry.grid(row=row + 1, column=column, sticky="ew", padx=6, pady=(3, 10))
            self.inputs[name] = entry
        actions = ttk.Frame(form)
        actions.grid(row=6, column=0, columnspan=4, sticky="ew")
        ttk.Button(actions, text="Recalcular cenário", command=self.apply_scenario).pack(side="left", padx=4)
        ttk.Button(actions, text="Carregar replay JSON", command=self.load_replay).pack(side="left", padx=4)
        ttk.Checkbutton(actions, text="Acompanhar arquivo de replay", variable=self.watch_file).pack(side="left", padx=8)
        ttk.Label(form, text="Exemplos de pesquisa. Sequência de perdas informada manualmente; pausa após perda assumida já cumprida.", style="Muted.TLabel").grid(row=7, column=0, columnspan=4, sticky="w", pady=(9, 0))
        cards = ttk.Frame(container, padding=(0, 14))
        cards.grid(row=3, column=0, sticky="ew")
        self.cards = {}
        for i, (key, label) in enumerate([("equity", "Capital do cenário"), ("margin", "Margem informada"), ("budget", "Risco permitido"),
                                          ("contracts", "Lote calculado"), ("attempts", "Stops até bloqueio")]):
            box = ttk.LabelFrame(cards, text=label, padding=12)
            box.grid(row=0, column=i, padx=4, sticky="nsew")
            cards.columnconfigure(i, weight=1)
            value = ttk.Label(box, text="—", style="Value.TLabel")
            value.pack(anchor="w")
            self.cards[key] = value
        self.sizing_label = ttk.Label(cards, text="", style="Muted.TLabel")
        self.sizing_label.grid(row=1, column=0, columnspan=5, sticky="w", pady=(8, 0))
        lower = ttk.PanedWindow(container, orient="horizontal")
        lower.grid(row=4, column=0, sticky="nsew")
        capacity = ttk.LabelFrame(lower, text="Capacidade após cada stop planejado", padding=10)
        reasoning = ttk.LabelFrame(lower, text="Dados e análise contextual", padding=10)
        lower.add(capacity, weight=1)
        lower.add(reasoning, weight=1)
        self.capacity_text = tk.Text(capacity, width=55, height=20, bg="#172536", fg="#dbe8f4",
                                     insertbackground="#e4eef7", relief="flat", font=("Consolas", 10), wrap="word")
        self.capacity_text.pack(fill="both", expand=True)
        self.reason_text = tk.Text(reasoning, width=58, height=20, bg="#172536", fg="#dbe8f4",
                                   insertbackground="#e4eef7", relief="flat", font=("Consolas", 10), wrap="word")
        self.reason_text.pack(fill="both", expand=True)
        footer = ttk.Frame(container, padding=(0, 12, 0, 0))
        footer.grid(row=5, column=0, sticky="ew")
        ttk.Button(footer, text="Testar resposta sintética", command=lambda: self.classify("mock")).pack(side="left", padx=4)
        ttk.Button(footer, text="Classificar com API JEV", command=lambda: self.classify("jev")).pack(side="left", padx=4)
        ttk.Label(footer, text="API usa sua chave local e pode consumir créditos. Nenhum dado de conta é enviado.", style="Muted.TLabel").pack(side="left", padx=12)
        ttk.Label(container, text="Feed real e conciliação da conta ainda requerem integração ProfitDLL/Toro. Probabilidade de lucro: não estimada.", style="Warn.TLabel").grid(row=6, column=0, sticky="w")
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.apply_scenario()
        self.poll()

    @staticmethod
    def write_text(widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def apply_scenario(self):
        try:
            values = {key: entry.get().replace(",", ".") for key, entry in self.inputs.items()}
            self.config, self.snapshot = example_from_inputs(self.base_config, values)
            self.selected_candidate_id = self.snapshot["candidates"][0]["id"]
            self.replay_path = None
            self.watch_file.set(False)
            self.generation += 1
            self.refresh_capacity()
        except (ValueError, KeyError, ArithmeticError):
            messagebox.showerror("Cenário inválido", "Verifique capital, percentuais e distâncias em múltiplos de cinco pontos.")

    def load_replay(self):
        name = filedialog.askopenfilename(title="Snapshot offline de pesquisa", filetypes=[("JSON", "*.json")])
        if not name:
            return
        try:
            self.read_replay(Path(name))
        except (ValueError, OSError, KeyError, TypeError, ArithmeticError):
            messagebox.showerror("Arquivo inválido", "Use um snapshot completo sintético/replay conforme example_snapshot.json.")

    def read_replay(self, path):
        snapshot = load_json(path)
        if not isinstance(snapshot, dict) or snapshot.get("data_origin") not in {"synthetic", "replay"}:
            raise ValueError("Offline snapshot required")
        if not snapshot.get("candidates") or not isinstance(snapshot.get("account"), dict):
            raise ValueError("Account and candidates required")
        account = snapshot["account"]
        for field in ("equity_brl", "available_margin_brl"):
            finite(account[field])
        now = max(snapshot["ts_ms"], account["asof_ms"])
        if quality_reasons(self.config, snapshot, now):
            raise ValueError("Invalid snapshot")
        candidate = snapshot["candidates"][0]
        candidate["side"], candidate["entry_points"], candidate["stop_points"], candidate["target_points"]
        preview = project_stop_capacity(self.config, account, candidate, now)
        format_capacity(preview)
        stamp = path.stat().st_mtime_ns
        self.snapshot = snapshot
        self.selected_candidate_id = candidate["id"]
        self.replay_path = path
        self.replay_mtime = stamp
        self.generation += 1
        self.refresh_capacity(report=preview)

    def refresh_capacity(self, report=None):
        account = self.snapshot["account"]
        candidate = next((x for x in self.snapshot["candidates"] if x["id"] == self.selected_candidate_id), self.snapshot["candidates"][0])
        now = max(self.snapshot["ts_ms"], account["asof_ms"])
        if report is None:
            report = project_stop_capacity(self.config, account, candidate, now)
        sizing = report["current_sizing"]
        self.cards["equity"].configure(text="R$ " + str(account["equity_brl"]))
        self.cards["margin"].configure(text="R$ " + str(account["available_margin_brl"]))
        self.cards["budget"].configure(text="R$ " + str(sizing.get("risk_budget_brl", "0")))
        self.cards["contracts"].configure(text=str(sizing["contracts"]))
        suffix = "+" if report["trajectories"]["real_policy"]["truncated_at_max_attempts"] else ""
        self.cards["attempts"].configure(text=str(report["attempts_until_policy_stop"]) + suffix)
        self.sizing_label.configure(text=f"Dimensionamento da hipótese: {candidate['id']} • Exposição máxima pelo risco; não é previsão de lucro.")
        self.write_text(self.capacity_text, format_capacity(report))
        lines = ["CENÁRIO CARREGADO", "Origem: " + self.snapshot["data_origin"],
                 "Contrato de pesquisa: " + self.snapshot["symbol"], "",
                 "A classificação contextual ainda não foi solicitada.",
                 "Use o botão de resposta sintética para testar a interface,",
                 "ou a API JEV para avaliar estas observações offline.", ""]
        for candidate in self.snapshot["candidates"]:
            lines += [f"{'Compra' if candidate.get('side') == 'buy' else 'Venda'}: entrada {candidate.get('entry_points', 'ausente')}",
                      f"Stop {candidate.get('stop_points', 'ausente')} · alvo {candidate.get('target_points', 'ausente')}", ""]
        self.write_text(self.reason_text, "\n".join(lines))
        self.status.configure(text=f"PESQUISA OFFLINE • Origem: {self.snapshot['data_origin']} • Profit/Toro não conectados")

    def classify(self, provider):
        if self.busy:
            return
        self.busy = True
        generation, config, snapshot = self.generation, deepcopy(self.config), deepcopy(self.snapshot)
        self.status.configure(text="Analisando exemplo offline…")
        def run():
            try:
                now = max(snapshot["ts_ms"], snapshot["account"]["asof_ms"])
                result = Copilot(config, self.questions, provider).process(snapshot, now)
            except Exception:
                result = {"status": "WAIT", "reasons": ["INPUT_OR_SERVICE_FAILURE"], "actionable_live_signal": False}
            self.results.put((generation, result))
        threading.Thread(target=run, daemon=True).start()

    def poll(self):
        if self.closed:
            return
        try:
            while True:
                generation, result = self.results.get_nowait()
                self.busy = False
                if generation == self.generation:
                    reviews = result.get("candidates_for_review", [])
                    if reviews:
                        self.selected_candidate_id = reviews[0]["candidate_id"]
                        self.refresh_capacity()
                    self.write_text(self.reason_text, format_decision(result))
                    self.status.configure(text=f"PESQUISA OFFLINE • {result['status']} • Nenhuma ordem")
        except queue.Empty:
            pass
        if self.watch_file.get() and self.replay_path is not None:
            try:
                if self.replay_path.stat().st_mtime_ns != self.replay_mtime:
                    self.read_replay(self.replay_path)
            except (OSError, ValueError, TypeError, KeyError, ArithmeticError):
                self.watch_file.set(False)
                self.generation += 1
                self.status.configure(text="Replay inválido ou indisponível • acompanhamento suspenso")
                for card in self.cards.values():
                    card.configure(text="—")
                self.write_text(self.reason_text, "Dados indisponíveis. A análise anterior foi invalidada.\nCarregue um snapshot válido para continuar a pesquisa.")
        self.root.after(250, self.poll)

    def close(self):
        self.closed = True
        self.root.destroy()


def main():
    root = tk.Tk()
    Dashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()

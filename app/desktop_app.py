"""JEV WIN desktop observer and capital research application, Windows portable build."""
from __future__ import annotations
from context_requests import attach_candidates

import argparse
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import queue
import shutil
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app_core import (DEFAULT_INPUTS, ObservationSession, apply_manual_pnl, build_risk_study,
                      build_decision_bundle, can_classify, declared_premise, jev_observation_state, money, number,
                      premise_questions, response_is_current, self_check)
from app_store import UserStore, VERSION, resource_path
from copilot import load_json
from candidate_research import build_market_candidates, generate_candidate_scenario
from dashboard import format_capacity
from jev_client import JevClient, JevError
from profit_bridge import BridgeError, ExcelBridge, CombinedExcelBridge, read_csv_events
from decision_view import DecisionPanel
from copilot_view import CopilotPanel
from panel_report import export_panel


BG, PANEL, LINE = "#101923", "#172536", "#314558"
FG, MUTED, GREEN, AMBER = "#e4edf6", "#9db0c4", "#6cd9b0", "#f0c575"
STATUS_NAMES = {"observed": "Observado", "potential": "Hipótese", "inconclusive": "Dados insuficientes", "not_observed": "Não observado"}
KIND_NAMES = {"progression": "Progressão", "absorption": "Absorção potencial", "exhaustion": "Exaustão potencial", "liquidity_withdrawal": "Redução da liquidez"}
SIDE_NAMES = {"buy": "compradora", "sell": "vendedora", "bids": "na compra", "asks": "na venda"}
FLOW_NAMES = {"buy_progression": "Compras acompanhadas por avanço do preço", "sell_progression": "Vendas acompanhadas por queda do preço",
              "possible_buy_absorption": "Possível absorção de compras", "possible_sell_absorption": "Possível absorção de vendas",
              "possible_exhaustion": "Possível exaustão do movimento", "mixed_or_insufficient": "Contexto misto ou dados insuficientes"}


def local_time(stamp):
    if stamp is None:
        return "horário indisponível"
    return datetime.fromtimestamp(stamp / 1000, timezone(timedelta(hours=-3))).strftime("%d/%m %H:%M:%S") + " BRT"


def text_box(parent, height=8):
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True)
    value = tk.Text(frame, height=height, bg=PANEL, fg=FG, insertbackground=FG,
                    relief="flat", wrap="word", font=("Segoe UI", 10), padx=12, pady=10)
    bar = ttk.Scrollbar(frame, orient="vertical", command=value.yview)
    value.configure(yscrollcommand=bar.set)
    bar.pack(side="right", fill="y")
    value.pack(side="left", fill="both", expand=True)
    value.configure(state="disabled")
    return value


def put_text(widget, text):
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", str(text))
    widget.configure(state="disabled")


class JevWINApp:
    def __init__(self, root):
        self.root = root
        self.store = UserStore()
        self.saved = self.store.settings()
        self.session = ObservationSession()
        self.snapshot = None
        self.study = None
        self.jobs = queue.Queue()
        self.busy = set()
        self.generation = 0
        self.closing = False
        self.excel_bridge = None
        self.excel_active = False
        self.next_poll = 0.0
        self.api_calls = 0
        self.api_tokens = 0
        self.next_jev = 0.0
        self.last_model_at = None
        self.model_deadline_ms = None
        self.candidate_deadline_ms = None
        self.candidate_basis = None
        self.last_flow_log = 0.0
        self.last_watch_refresh = 0.0
        saved_loss = self.saved.get("last_loss_ms", "")
        self.last_loss_ms = int(saved_loss) if saved_loss.isdigit() else None
        self.next_risk_refresh = (self.last_loss_ms + 61000) if self.last_loss_ms is not None else None
        self.api_limit = 120
        self.latest_jev_result = None
        self.decision_bundle = None
        self.decision_history = []
        self.last_decision_refresh = 0.0
        self.last_decision_signature = None
        self._build()
        self.load_demo()
        self.calculate_risk()
        self.refresh_journal()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(150, self.poll)

    def _build(self):
        self.root.title("JEV WIN — Fluxo e capital")
        self.root.configure(bg=BG)
        width = min(1320, max(960, self.root.winfo_screenwidth() - 70))
        height = min(900, max(620, self.root.winfo_screenheight() - 90))
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(960, 620)
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Warn.TLabel", foreground=AMBER)
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Value.TLabel", font=("Segoe UI", 17, "bold"), foreground=GREEN)
        style.configure("TLabelframe", background=BG, bordercolor=LINE)
        style.configure("TLabelframe.Label", background=BG, foreground=FG, font=("Segoe UI", 11, "bold"))
        style.configure("TButton", padding=(10, 7), font=("Segoe UI", 10))
        style.configure("TCheckbutton", background=BG, foreground=FG)
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(10, 9), font=("Segoe UI", 10))
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=FG, rowheight=29, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=LINE, foreground=FG, font=("Segoe UI", 10, "bold"))
        shell = ttk.Frame(self.root, padding=18)
        shell.pack(fill="both", expand=True)
        head = ttk.Frame(shell)
        head.pack(fill="x")
        ttk.Label(head, text="JEV WIN", style="Title.TLabel").pack(side="left")
        ttk.Label(head, text=f"v{VERSION}  •  Fluxo, hipóteses e capital", style="Muted.TLabel").pack(side="left", padx=18)
        self.source_badge = ttk.Label(shell, text="Demonstração", style="Warn.TLabel")
        self.source_badge.pack(fill="x", pady=(5, 10))
        self.tabs = ttk.Notebook(shell)
        self.tabs.pack(fill="both", expand=True)
        self.pages = {}
        for key, label in (("copilot", "Copiloto"), ("monitor", "Fluxo"), ("candidates", "Cenários"), ("risk", "Conta"),
                           ("config", "Configuração"), ("journal", "Diário"), ("guide", "Guia")):
            page = ttk.Frame(self.tabs, padding=12)
            self.tabs.add(page, text=label)
            self.pages[key] = page
        self.premise = tk.StringVar()
        self.copilot = CopilotPanel(self.pages["copilot"], refresh=lambda: self.refresh_decision(force=True),
                                    classify=self.request_jev, demonstrate=self.demo_candidates,
                                    export=self.export_decision, premise_var=self.premise)
        self.decision_panel = self.copilot.decision
        self._monitor()
        self._candidates()
        self._risk()
        self._config()
        self._journal()
        self._guide()
        self.tabs.bind("<<NotebookTabChanged>>", lambda _event: self.refresh_journal()
                       if self.tabs.select() == str(self.pages["journal"]) else None)
        self.footer = ttk.Label(shell, text="Conta informada manualmente • Análises experimentais • Sem envio de ordens", style="Muted.TLabel")
        self.footer.pack(fill="x", pady=(9, 0))

    def _monitor(self):
        page = self.pages["monitor"]
        tools = ttk.Frame(page)
        tools.pack(fill="x", pady=(0, 10))
        self.demo_mode = tk.StringVar(value="progression")
        ttk.Label(tools, text="Cenário local").pack(side="left")
        ttk.Combobox(tools, textvariable=self.demo_mode, values=("progression", "absorption", "exhaustion", "choppy"), state="readonly", width=15).pack(side="left", padx=8)
        self.demo_side = tk.StringVar(value="buy")
        ttk.Combobox(tools, textvariable=self.demo_side, values=("buy", "sell"), state="readonly", width=7).pack(side="left")
        ttk.Button(tools, text="Carregar demonstração", command=self.load_demo).pack(side="left", padx=8)
        ttk.Button(tools, text="Analisar contexto com JEV", command=self.request_jev).pack(side="right")
        row = ttk.Frame(page)
        row.pack(fill="x", pady=(0, 10))
        self.flow_cards = {}
        for index, (key, label) in enumerate((("last", "Último preço"), ("delta", "Delta capturado · 5 s"),
                                            ("volume", "Contratos capturados · 5 s"), ("spread", "Spread"), ("age", "Idade da origem"))):
            box = ttk.LabelFrame(row, text=label, padding=9)
            box.grid(row=0, column=index, padx=3, sticky="ew")
            row.columnconfigure(index, weight=1)
            value = ttk.Label(box, text="—", style="Value.TLabel")
            value.pack(anchor="w")
            self.flow_cards[key] = value
        self.chart = tk.Canvas(page, height=125, bg=PANEL, highlightthickness=0)
        self.chart.pack(fill="x", pady=(0, 10))
        self.chart.bind("<Configure>", lambda event: self.draw_chart())
        columns = ("pattern", "status", "basis")
        self.patterns = ttk.Treeview(page, columns=columns, show="headings", height=8)
        for name, title, width in (("pattern", "Hipótese observada", 220), ("status", "Estado", 165), ("basis", "Evidência / condição", 650)):
            self.patterns.heading(name, text=title)
            self.patterns.column(name, width=width, minwidth=100)
        self.patterns.pack(fill="both", expand=True)
        self.coverage = ttk.Label(page, text="", style="Warn.TLabel", wraplength=1130)
        self.coverage.pack(fill="x", pady=(8, 4))
        self.model_summary = ttk.Label(page, text="JEV ainda não consultado. A classificação local é uma hipótese de pesquisa.", wraplength=1130)
        self.model_summary.pack(fill="x")

    def refresh_decision(self, force=False):
        if not hasattr(self, "decision_panel") or not hasattr(self, "risk_inputs"):
            return
        now = time.monotonic()
        if not force and now - self.last_decision_refresh < 1:
            return
        self.last_decision_refresh = now
        bundle = build_decision_bundle(self.session if self.snapshot is not None else None, self.values(),
                                       last_loss_ms=self.last_loss_ms, latest_jev_result=self.latest_jev_result)
        bundle["model_request_inflight"] = "jev" in self.busy
        self.decision_bundle = bundle
        rec = bundle["recommendation"]
        signature_fields = {key: rec.get(key) for key in ("status", "action", "origin", "reasons", "missing_evidence", "contradictions", "review_candidate_ids")}
        signature_fields["source_generation"] = (bundle.get("snapshot") or {}).get("source_generation")
        signature_fields["model_context"] = {key: rec.get("model", {}).get(key) for key in ("choice", "available", "current")}
        signature = json.dumps(signature_fields, sort_keys=True)
        if signature != self.last_decision_signature:
            self.last_decision_signature = signature
            item = {"ts_ms": bundle["evaluated_at_ms"], "status": rec["status"], "action": rec["action"],
                    "symbol": rec.get("origin", {}).get("symbol"), "mode": rec.get("origin", {}).get("mode")}
            self.decision_history.append(item)
            self.decision_history = self.decision_history[-50:]
            self.store.record("recommendation", rec, ts_ms=bundle["evaluated_at_ms"])
        self.decision_panel.render(bundle, self.decision_history)

    def export_decision(self):
        self.refresh_decision(force=True)
        filename = filedialog.asksaveasfilename(title="Exportar registro visual da avaliação", defaultextension=".html",
                                               initialfile="JevWIN_painel.html", filetypes=[("HTML", "*.html")])
        if not filename:
            return
        try:
            export_panel(filename, self.decision_bundle)
            messagebox.showinfo("Painel exportado", "Abra o HTML em seu navegador. Ele registra a avaliação deste instante; não continua recebendo dados de mercado.")
        except OSError:
            messagebox.showerror("Falha ao exportar", "Não foi possível gravar o painel na pasta escolhida.")

    def _risk(self):
        page = self.pages["risk"]
        ttk.Label(page, text="Estudo de capital informado — os valores não são lidos da Toro", style="Warn.TLabel").pack(anchor="w")
        form = ttk.Frame(page, padding=(0, 10))
        form.pack(fill="x")
        labels = (("start", "Início da sessão (R$)"), ("current", "Capital atual (R$)"), ("peak", "Pico (R$)"),
                  ("risk_pct", "Risco por proposta (%)"), ("daily_pct", "Perda diária inicial (%)"),
                  ("drawdown_pct", "Queda máxima do pico (%)"), ("stop", "Stop estudado (pontos)"),
                  ("target", "Alvo estudado (pontos)"), ("loss_streak", "Perdas consecutivas"),
                  ("fees", "Taxas ida/volta (R$/contrato)"), ("slippage", "Slippage total (pontos)"),
                  ("margin", "Margem/contrato (R$)"), ("contract_cap", "Teto técnico de contratos"))
        self.risk_inputs = {}
        for index, (key, title) in enumerate(labels):
            row, column = (index // 5) * 2, index % 5
            form.columnconfigure(column, weight=1)
            ttk.Label(form, text=title).grid(row=row, column=column, sticky="w", padx=4)
            value = tk.StringVar(value=self.saved.get(key, DEFAULT_INPUTS[key]))
            self.risk_inputs[key] = value
            ttk.Entry(form, textvariable=value, width=20).grid(row=row+1, column=column, sticky="ew", padx=4, pady=(2, 7))
        actions = ttk.Frame(page)
        actions.pack(fill="x")
        ttk.Button(actions, text="Recalcular e comparar políticas", command=self.calculate_risk).pack(side="left")
        self.risk_summary = ttk.Label(actions, text="", style="Value.TLabel")
        self.risk_summary.pack(side="left", padx=14)
        ttk.Label(page, text="Parâmetros de laboratório. Sequência digitada pressupõe pausa cumprida; resultados novos no diário respeitam a pausa de 60 s.", style="Muted.TLabel", wraplength=1120).pack(anchor="w", pady=(7, 8))
        lower = ttk.PanedWindow(page, orient="horizontal")
        lower.pack(fill="both", expand=True)
        a = ttk.LabelFrame(lower, text="Capacidade da política escolhida", padding=6)
        b = ttk.LabelFrame(lower, text="Comparação com o mesmo stop e custos", padding=6)
        lower.add(a, weight=1)
        lower.add(b, weight=1)
        self.capacity_text = text_box(a, height=10)
        cols = ("fraction", "basis", "lot", "stops")
        self.policy_tree = ttk.Treeview(b, columns=cols, show="headings", height=10)
        for name, title, width in (("fraction", "Risco", 65), ("basis", "Base de capital", 165), ("lot", "Lote", 60), ("stops", "Stops pela política", 130)):
            self.policy_tree.heading(name, text=title)
            self.policy_tree.column(name, width=width, minwidth=55)
        self.policy_tree.pack(fill="both", expand=True)
        ttk.Label(b, text="Maior lote permitido não identifica a política com maior lucro esperado.", style="Warn.TLabel", wraplength=480).pack(fill="x", pady=(8, 0))

    def _candidates(self):
        page = self.pages["candidates"]
        ttk.Label(page, text="Comparação de entrada, invalidação e alvo pelos níveis observados", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(page, text="Cenários experimentais com capital manual. Alvos precisam de referência nos dados; nenhuma operação é executada.", style="Warn.TLabel", wraplength=1100).pack(anchor="w", pady=(5, 12))
        actions = ttk.Frame(page)
        actions.pack(fill="x", pady=(0, 12))
        ttk.Button(actions, text="Comparar dados carregados", command=self.compare_candidates).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Demonstrar comparação técnica", command=self.demo_candidates).pack(side="left")
        self.candidate_status = ttk.Label(page, text="Carregue uma fonte e compare os níveis disponíveis.", style="Muted.TLabel", wraplength=1100)
        self.candidate_status.pack(anchor="w", pady=(0, 10))
        columns = ("side", "entry", "stop", "target", "lot", "risk", "rr", "state")
        self.candidate_tree = ttk.Treeview(page, columns=columns, show="headings", height=9)
        for name, title, width in (("side", "Direção", 80), ("entry", "Entrada", 100), ("stop", "Stop", 100),
                                   ("target", "Alvo", 100), ("lot", "Lote", 60), ("risk", "Risco total", 115),
                                   ("rr", "Ganho/risco líquido", 135), ("state", "Cálculo", 190)):
            self.candidate_tree.heading(name, text=title)
            self.candidate_tree.column(name, width=width, minwidth=50)
        self.candidate_tree.pack(fill="both", expand=True)
        self.candidate_details = text_box(page, height=7)
        self.candidate_rows = {}
        self.candidate_tree.bind("<<TreeviewSelect>>", self.show_candidate)

    def clear_candidates(self):
        self.candidate_deadline_ms = None
        self.candidate_basis = None
        if not hasattr(self, "candidate_tree"):
            return
        self.candidate_tree.delete(*self.candidate_tree.get_children())
        self.candidate_rows = {}
        self.candidate_status.configure(text="Fonte alterada. Recalcule os cenários com os dados disponíveis.")
        put_text(self.candidate_details, "Nenhum cenário financeiro atual para a fonte selecionada.")

    def demo_candidates(self):
        self.stop_excel(quiet=True)
        self.generation += 1
        self.invalidate_model()
        self.session.reset("WIN_SIM")
        fixture = generate_candidate_scenario(end_ms=int(time.time()*1000))
        self.session.mode = "synthetic"
        self.session.engine.set_source_quality(fixture["source_quality"])
        for event in fixture["events"]:
            if event["type"] == "trade":
                self.session.engine.add_trade(event)
                self.session.chart.append((event["ts_ms"], float(event["price_points"])))
            else:
                self.session.engine.set_book(event)
        self.session.clock_ms = fixture["now_ms"]
        self.session.warnings = ["Faixa de preços sintética criada para testar comparação técnica."]
        self.snapshot = self.session.snapshot()
        self.render_snapshot()
        self.compare_candidates()

    def compare_candidates(self):
        if self.snapshot is None:
            self.candidate_status.configure(text="Nenhum dado carregado para comparação.")
            return
        try:
            state = self.session.snapshot()
            clock = state["ts_ms"]
            last_loss = self.last_loss_ms if state["application_mode"] == "excel_observation" else None
            study = build_risk_study(self.values(), now_ms=clock, last_loss_ms=last_loss)
            report = build_market_candidates(self.session.engine, state, study["config"], study["account"], clock)
            self.clear_candidates()
            self.candidate_status.configure(text=f"{len(report['rows'])} cenários • {len(report['reference_levels'])} níveis observados • referência {local_time(clock)} • sem previsão de lucro")
            for index, row in enumerate(report["rows"]):
                sizing = row["risk"]
                unit = sizing.get("risk_per_contract_brl")
                total_risk = number(unit)*row["lots"] if unit is not None else None
                rr = sizing.get("net_reward_risk")
                status = "Cabe no estudo" if sizing.get("status") == "ALLOW_SIMULATION" else "Bloqueado"
                item = str(index)
                self.candidate_rows[item] = row
                self.candidate_tree.insert("", "end", iid=item, values=("Compra" if row["side"] == "buy" else "Venda", row["entry_points"], row["stop_points"], row["target_points"], row["lots"], money(total_risk), f"{number(rr):.2f}" if rr is not None else "—", status))
            notes = ["Os preços são referências para pesquisa, não instruções de entrada.",
                     "Todos os candidatos mantêm a mesma informação de conta manual e as mesmas regras de risco.",
                     "O maior ganho/risco não identifica a maior probabilidade nem o melhor valor esperado."]
            if report.get("reasons"):
                notes += ["", "Condições: " + ", ".join(report["reasons"])]
            if not report["rows"]:
                notes += ["", "Não há níveis suficientes nos dois lados do preço para formar os pares. O sistema não inventa um alvo distante para melhorar a relação."]
            put_text(self.candidate_details, "\n".join(notes))
            self.candidate_basis = self.values()
            quote_stamp = report["evidence_coverage"].get("quote_ts_ms")
            self.candidate_deadline_ms = quote_stamp + 2000 if state["application_mode"] == "excel_observation" and type(quote_stamp) is int else None
            self.store.record("risk", {"candidate_report": report, "account_source": "manual_scenario"}, ts_ms=clock)
        except (ValueError, KeyError) as error:
            self.clear_candidates()
            self.candidate_status.configure(text="Comparação indisponível: " + str(error))

    def show_candidate(self, _event=None):
        selection = self.candidate_tree.selection()
        if not selection:
            return
        row = self.candidate_rows.get(selection[0])
        if row is None:
            return
        lines = ["CENÁRIO TÉCNICO PARA PESQUISA", "", f"ID: {row['id']}",
                 f"Distância do stop: {row['stop_distance_points']} pontos; alvo: {row['target_distance_points']} pontos.",
                 "Referências: " + ", ".join(row.get("reference_evidence_ids", [])),
                 "Restrições: " + (", ".join(row.get("reasons", [])) or "Nenhum bloqueio no cálculo do cenário."),
                 "", "A conta continua informada manualmente. Essa combinação não foi validada como estratégia lucrativa."]
        put_text(self.candidate_details, "\n".join(lines))

    def _config(self):
        page = self.pages["config"]
        source_box = ttk.LabelFrame(page, text="Fonte de dados — Profit → exportação RTD → Excel já aberto", padding=10)
        source_box.pack(fill="x", pady=(0, 12))
        ttk.Label(source_box, text="O Excel e o Profit precisam estar configurados na mesma sessão do Windows. A leitura não altera o arquivo.", style="Muted.TLabel", wraplength=1120).pack(anchor="w", pady=(0, 10))
        self.connection_inputs = {}
        form = ttk.Frame(source_box)
        form.pack(fill="x")
        settings = (("symbol", "Contrato exato", "WIN_SIM"), ("workbook", "Arquivo já aberto no Excel", "Profit_RTD_Modelo.xlsx"),
                    ("sheet", "Planilha principal / cotações", "Dados"), ("cell_range", "Intervalo principal com cabeçalho", "A1:I2"),
                    ("tape_sheet", "Planilha de negócios (combined)", "Negocios"), ("tape_range", "Intervalo de negócios (combined)", "A1:F501"))
        for index, (key, title, default) in enumerate(settings):
            ttk.Label(form, text=title).grid(row=index, column=0, sticky="w", padx=(0, 18), pady=4)
            var = tk.StringVar(value=self.saved.get(key, default))
            self.connection_inputs[key] = var
            ttk.Entry(form, textvariable=var, width=55).grid(row=index, column=1, sticky="ew", pady=4)
        self.excel_mode = tk.StringVar(value=self.saved.get("excel_mode", "quote"))
        ttk.Label(form, text="Modo: quote / tape / combined").grid(row=6, column=0, sticky="w", pady=4)
        ttk.Combobox(form, textvariable=self.excel_mode, values=("quote", "tape", "combined"), state="readonly", width=18).grid(row=6, column=1, sticky="w")
        form.columnconfigure(1, weight=1)
        row = ttk.Frame(source_box)
        row.pack(fill="x", pady=(10, 8))
        ttk.Button(row, text="Conectar leitura Excel", command=self.start_excel).pack(side="left", padx=(0, 8))
        ttk.Button(row, text="Parar leitura", command=self.stop_excel).pack(side="left", padx=4)
        ttk.Button(row, text="Carregar negócios CSV", command=self.load_csv).pack(side="left", padx=4)
        ttk.Button(row, text="Salvar modelos de exportação", command=self.save_templates).pack(side="left", padx=4)
        self.connection_status = ttk.Label(source_box, text="Profit/Toro não conectados. O monitor iniciou em demonstração local.", style="Warn.TLabel", wraplength=1120)
        self.connection_status.pack(fill="x", pady=(0, 6))
        guide = text_box(source_box, height=6)
        put_text(guide, "COMO PREPARAR\n1. No Profit: Arquivo → Exportar em Tempo Real (RTD/DDE). Habilite a transferência e selecione os dados.\n2. Salve os modelos por este aplicativo. Abra Profit_RTD_Modelo.xlsx e preencha o contrato em Dados!A2.\n3. quote lê cotações; tape lê uma tabela de negócios; combined lê as duas (Negocios / A1:F501 precisa receber eventos reais com id, symbol, ts_ms, price_points, quantity, aggressor).\n\nLIMITES: o modelo não exporta Times & Trades sozinho; tabela vazia bloqueia combined. QUL é quantidade do último negócio, não uma sequência integral. Leitura Excel não comprova conexão do feed, e dados de janelas vinculadas podem pausar com a aba inativa. Saldo, margem e posições da Toro não são consultados. CSV é replay, com relógio do arquivo.")

        jev_box = ttk.LabelFrame(page, text="TypeSafe JEV — interpretação estruturada do contexto", padding=10)
        jev_box.pack(fill="x")
        ttk.Label(jev_box, text="Modelo fixado: jev-1.13.0 • Uma chamada reúne as perguntas independentes", style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        row = ttk.Frame(jev_box)
        row.pack(fill="x")
        ttk.Label(row, text="Chave da API").pack(side="left")
        self.key = tk.StringVar(value=os.environ.get("TYPESAFE_API_KEY", ""))
        ttk.Entry(row, textvariable=self.key, show="•", width=65).pack(side="left", padx=10, fill="x", expand=True)
        ttk.Label(jev_box, text="A chave fica na memória desta execução. Não é salva no diário nem nas configurações.", style="Muted.TLabel").pack(anchor="w", pady=(6, 6))
        self.auto_jev = tk.BooleanVar(value=False)
        ttk.Checkbutton(jev_box, text="Consultar automaticamente enquanto a leitura Excel estiver ativa (mínimo 10 s entre chamadas)", variable=self.auto_jev).pack(anchor="w")
        budget_row = ttk.Frame(jev_box)
        budget_row.pack(fill="x", pady=(7, 5))
        ttk.Label(budget_row, text="Limite de consultas nesta execução").pack(side="left")
        self.api_budget = tk.StringVar(value=self.saved.get("api_call_limit", "120"))
        ttk.Entry(budget_row, textvariable=self.api_budget, width=9).pack(side="left", padx=9)
        ttk.Label(budget_row, text="1 a 10.000 • contador reinicia ao abrir o aplicativo • consultas usam sua conta TypeSafe", style="Muted.TLabel").pack(side="left")
        self.api_status = ttk.Label(jev_box, text="Nenhuma chamada realizada nesta execução", style="Warn.TLabel")
        self.api_status.pack(anchor="w", pady=(6, 0))

    def _journal(self):
        page = self.pages["journal"]
        row = ttk.Frame(page)
        row.pack(fill="x", pady=(0, 10))
        ttk.Label(row, text="Resultado líquido manual (R$)").pack(side="left")
        self.manual_pnl = tk.StringVar(value="0")
        ttk.Entry(row, textvariable=self.manual_pnl, width=16).pack(side="left", padx=8)
        ttk.Button(row, text="Registrar e atualizar capital", command=self.record_trade).pack(side="left", padx=4)
        ttk.Button(row, text="Exportar diário JSON", command=self.export_journal).pack(side="right")
        ttk.Label(page, text="Informe o resultado já líquido de custos. Este diário é seu registro manual e não substitui o extrato da corretora.", style="Warn.TLabel", wraplength=1100).pack(anchor="w", pady=(0, 12))
        self.journal_text = text_box(page, height=18)

    def _guide(self):
        page = self.pages["guide"]
        box = text_box(page, height=25)
        put_text(box, "COMECE AQUI\n\nCOPILOTO\nTela principal centrada no JEV: estado da fonte, medidas capturadas, classificação do contexto e conclusão com evidências e impedimentos. Escreva sua leitura do mercado em \"Sua leitura\": a próxima consulta avalia apoio, contradição e suficiência da evidência observada sobre a sua frase — dimensões separadas, nunca recomendação. Dados parciais mantêm a conclusão em aguardar; o lote calculado não é ordem ou probabilidade de lucro. Exportar painel HTML salva um registro visual estático.\n\n1. FLUXO\nExplore os quatro cenários locais: progression (progressão), absorption (absorção), exhaustion (exaustão) e choppy (alternância). buy/sell invertem o lado. Esses dados são sintéticos e não representam o pregão. Mostra preços, delta/contratos capturados, hipóteses, idade e cobertura.\n\n2. CENÁRIOS\nComparação de entrada, invalidação e alvo pelos níveis observados. Cenários experimentais com capital manual; nenhuma operação é executada.\n\n3. CONTA\nInforme patrimônio, pico, custo, margem, stop e limite por proposta. O cálculo acompanha ganhos e perdas e compara dez combinações de fração/base patrimonial. Não estima um lote de lucro máximo. O patrimônio é manual e a conta é assumida sem posição no cenário. Pausas projetadas são hipotéticas; perdas registradas respeitam 60 s.\n\n4. CONFIGURAÇÃO\nFonte de dados (RTD/Excel e replay CSV) e chave TypeSafe JEV no mesmo lugar. A exportação RTD/Excel permite observar o que seu Profit disponibiliza sem a DLL Feed: cotações ou uma amostra do tape. A consulta automática do JEV é opcional, funciona enquanto o aplicativo estiver aberto e a fonte Excel estiver ativa. Se faltar evidência ou houver atraso, a avaliação é limitada ou bloqueada.\n\n5. DIÁRIO\nRegistre resultados líquidos e exporte o histórico. O aplicativo guarda configurações e eventos no diretório de dados do seu usuário. Chaves não são persistidas.\n\nLEITURA DE FLUXO\nProgressão: agressão acompanhada de avanço observado do preço.\nAbsorção potencial: agressão sem avanço proporcional; não identifica intenção ou ordem oculta.\nExaustão potencial: perda de intensidade após avanço e falta de continuação; não prevê reversão.\nRedução de liquidez: quantidade visível diminuiu nos mesmos níveis; a causa pode ser execução, cancelamento ou atualização.\n\nESTADO DESTA VERSÃO\nColetor Excel implementado, mas ainda não validado na sua instalação. Conta Toro, envio de ordens, detector de notícias e gestão de posição aberta não estão conectados. O JEV classifica contexto observado — não acompanha suas ações no Profit nem prevê lucro. Nenhuma rentabilidade foi comprovada. Margem e stop não garantem perda máxima.\n\nFONTES\nSkill TypeSafe: github.com/typesafe-ai/skills\nAPI e modelos: docs.typesafe.ai\nRTD/ProfitDLL: ajuda.nelogica.com.br\nContrato WIN e margem: b3.com.br\n\nO ZIP do projeto contém a documentação completa, fontes e testes para auditoria.")

    def values(self):
        return {key: value.get() for key, value in self.risk_inputs.items()}

    def invalidate_model(self):
        self.latest_jev_result = None
        self.last_model_at = None
        self.model_deadline_ms = None
        self.clear_candidates()
        self.model_summary.configure(text="Contexto alterado. JEV ainda não consultado para esta fonte.")
        self.copilot.render_jev_pending("Contexto alterado. JEV ainda não consultado para esta fonte.")
        self.copilot.render_premise_pending("Fonte alterada; sua leitura será reavaliada na próxima consulta.")
        put_text(self.copilot.jev_details, "Nenhuma análise atual para a fonte selecionada. Resultados anteriores permanecem no diário.")

    def load_demo(self):
        self.stop_excel(quiet=True)
        self.generation += 1
        self.invalidate_model()
        self.snapshot = self.session.demo(self.demo_mode.get(), self.demo_side.get())
        self.render_snapshot()

    def calculate_risk(self):
        self.clear_candidates()
        try:
            result = build_risk_study(self.values(), now_ms=int(time.time()*1000), last_loss_ms=self.last_loss_ms)
            self.study = result
            self.store.save_settings(result["inputs"])
            sizing = result["projection"]["current_sizing"]
            self.risk_summary.configure(text=f"Lote calculado: {sizing['contracts']}  •  Orçamento: {money(sizing['risk_budget_brl'])}")
            put_text(self.capacity_text, format_capacity(result["projection"]))
            self.policy_tree.delete(*self.policy_tree.get_children())
            for row in result["comparisons"]["rows"]:
                fraction = f"{number(row['per_trade_fraction'])*100:g}%"
                basis = "Patrimônio atual" if row["capital_basis"] == "current_equity" else "Limitada ao início"
                self.policy_tree.insert("", "end", values=(fraction, basis, row["allowed_contracts"], row["attempts_until_policy_stop"]))
            self.store.record("risk", {"inputs": result["inputs"], "sizing": sizing, "account_source": "manual_scenario"})
        except (ValueError, KeyError) as error:
            self.study = None
            self.risk_summary.configure(text="Cálculo indisponível")
            put_text(self.capacity_text, str(error))
            self.policy_tree.delete(*self.policy_tree.get_children())
        self.refresh_decision(force=True)

    def run_job(self, kind, function):
        if kind in self.busy:
            return
        self.busy.add(kind)
        generation = self.generation
        def work():
            started = time.monotonic()
            try:
                result = function()
                self.jobs.put((kind, generation, result, None, time.monotonic()-started))
            except (BridgeError, JevError, ValueError, OSError, KeyError) as error:
                self.jobs.put((kind, generation, None, str(error), time.monotonic()-started))
            except Exception:
                self.jobs.put((kind, generation, None, "Falha interna na operação; verifique a fonte e tente novamente.", time.monotonic()-started))
        threading.Thread(target=work, daemon=True).start()

    def start_excel(self):
        try:
            values = {key: field.get().strip() for key, field in self.connection_inputs.items()}
            symbol = values["symbol"].upper()
            if not symbol or symbol == "WIN_SIM":
                raise ValueError("Informe o contrato usado no Profit; WIN_SIM é reservado à demonstração.")
            if self.excel_mode.get() == "combined":
                bridge = CombinedExcelBridge(values["workbook"], values["sheet"], values["cell_range"],
                                             values["tape_sheet"], values["tape_range"], symbol=symbol)
            else:
                bridge = ExcelBridge(values["workbook"], values["sheet"], values["cell_range"], self.excel_mode.get(), symbol)
            self.stop_excel(quiet=True)
            self.generation += 1
            self.session.reset(symbol)
            self.session.mode = "excel_observation"
            self.snapshot = None
            self.invalidate_model()
            self.excel_bridge = bridge
            self.excel_active = True
            self.next_poll = 0
            self.store.save_settings(dict(values, excel_mode=self.excel_mode.get()))
            self.connection_status.configure(text="Conferindo o arquivo Excel informado…")
            self.source_badge.configure(text="EXCEL • aguardando primeira leitura • Conta Toro não conectada")
            self.clear_monitor()
        except (ValueError, BridgeError) as error:
            self.connection_status.configure(text=str(error))

    def stop_excel(self, quiet=False):
        self.excel_active = False
        self.excel_bridge = None
        self.generation += 1
        if not quiet:
            self.connection_status.configure(text="Leitura interrompida. Nenhuma nova consulta será iniciada.")
            self.source_badge.configure(text="LEITURA PARADA • consulte o diário para resultados anteriores")
            self.snapshot = None
            self.invalidate_model()
            self.clear_monitor()

    def load_csv(self):
        if "csv" in self.busy:
            self.connection_status.configure(text="Aguarde a leitura CSV em andamento antes de selecionar outro arquivo.")
            return
        filename = filedialog.askopenfilename(title="Negócios de replay", filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if not filename:
            return
        symbol = self.connection_inputs["symbol"].get().strip().upper() or "WIN_SIM"
        self.stop_excel(quiet=True)
        self.generation += 1
        self.session.reset(symbol)
        self.invalidate_model()
        self.snapshot = None
        self.clear_monitor()
        self.source_badge.configure(text="CARREGANDO REPLAY • aguardando validação do arquivo")
        self.connection_status.configure(text="Lendo replay CSV…")
        self.store.save_settings({"csv_path": filename})
        self.run_job("csv", lambda: read_csv_events(filename, symbol))

    def request_jev(self):
        if self.snapshot is None:
            self.api_status.configure(text="Carregue uma fonte antes de consultar o JEV.")
            return
        allowed, explanation = can_classify(self.snapshot)
        if not allowed:
            self.api_status.configure(text=explanation)
            return
        key = self.key.get().strip()
        if not key:
            self.tabs.select(self.pages["config"])
            self.api_status.configure(text="Insira sua chave TypeSafe. Ela será usada somente nesta execução.")
            return
        if "jev" in self.busy:
            return
        try:
            self.api_limit = int(self.api_budget.get().strip())
            if not 1 <= self.api_limit <= 10000:
                raise ValueError
        except ValueError:
            self.api_status.configure(text="Informe um limite inteiro entre 1 e 10.000 consultas.")
            self.auto_jev.set(False)
            return
        self.store.save_settings({"api_call_limit": self.api_limit})
        if self.api_calls >= self.api_limit:
            self.api_status.configure(text=f"Limite desta execução atingido: {self.api_limit} consultas. Ajuste o orçamento para continuar.")
            self.auto_jev.set(False)
            return
        snapshot = json.loads(json.dumps(self.snapshot, allow_nan=False))
        self.api_calls += 1
        self.next_jev = time.monotonic() + 10
        self.api_status.configure(text=f"Consultando JEV… chamada {self.api_calls}/{self.api_limit}")
        questions = load_json(resource_path("observer_questions.json"))
        state = jev_observation_state(snapshot)
        try:
            clock = snapshot["ts_ms"]
            study = build_risk_study(self.values(), now_ms=clock, last_loss_ms=self.last_loss_ms if snapshot["application_mode"] == "excel_observation" else None)
            technical = build_market_candidates(self.session.engine, snapshot, study["config"], study["account"], clock)
            attach_candidates(state, questions, [row for row in technical['rows'] if row['risk']['status'] == 'ALLOW_SIMULATION'])
        except (ValueError, KeyError):
            state["candidate_setups"] = []
        premise = declared_premise(self.premise.get(), asof_ms=snapshot["ts_ms"])
        if premise is not None:
            state["user_premise"] = premise
            questions.update(premise_questions())
            self.copilot.render_premise_pending("Sua leitura será avaliada junto à próxima resposta JEV…")
        def evaluate():
            response = JevClient(timeout_seconds=3, api_key=key).evaluate(state, questions)
            return {"response": response, "state": state, 'questions': questions, "source_ts_ms": snapshot["ts_ms"],
                    "flow_ts_ms": snapshot.get("flow_ts_ms"), "mode": snapshot["application_mode"],
                    "source_generation": snapshot["source_generation"]}
        self.run_job("jev", evaluate)

    def handle_jev(self, result, elapsed):
        self.latest_jev_result = result
        response = result["response"]
        self.api_tokens += response["usage"]["input_tokens"]
        self.store.record("jev", dict(result, latency_ms=round(elapsed*1000)))
        context = response["answers"]["flow_context"]
        name = FLOW_NAMES[context["choice"]]
        late = elapsed > 3 or not response_is_current(self.snapshot, result.get("flow_ts_ms"), now_ms=int(time.time()*1000))
        self.last_model_at = time.monotonic() if not late else None
        self.model_deadline_ms = (result["flow_ts_ms"]+2000) if not late and result["mode"] == "excel_observation" else None
        self.api_status.configure(text=f"{self.api_calls} chamadas • {self.api_tokens:,} tokens de entrada • {elapsed*1000:.0f} ms na última chamada")
        lines = ["ANÁLISE DESCRITIVA DO JEV", "", name, f"Referência: {local_time(result['source_ts_ms'])}",
                 f"Origem: {result['mode']}", f"Confiança na classificação: {context['confidence']:.3f} — não é chance de lucro.", ""]
        names = {"buy_progression_supported": "Progressão compradora", "sell_progression_supported": "Progressão vendedora",
                 "buy_absorption_supported": "Absorção de compras", "sell_absorption_supported": "Absorção de vendas",
                 "exhaustion_supported": "Exaustão", "evidence_insufficient": "Insuficiência de evidência"}
        for key, label in names.items():
            lines.append(f"{label}: apoio contextual {response['answers'][key]['noul']:.3f}")
        setups = result["state"].get("candidate_setups", [])
        if setups:
            lines += ["", "EVIDÊNCIAS DOS CENÁRIOS TÉCNICOS"]
            for index, setup in enumerate(setups):
                support = response["answers"][f"candidate_{index}_support"]["noul"]
                contrary = response["answers"][f"candidate_{index}_contradiction"]["noul"]
                lines.append(f"{setup['id']}: apoio {support:.3f}; contradição {contrary:.3f}.")
        answers = response["answers"]
        if "premise_evidence_support" in answers:
            premise = result["state"].get("user_premise", {})
            sup, con = answers["premise_evidence_support"]["noul"], answers["premise_evidence_contradiction"]["noul"]
            evl = answers["premise_evaluable"]["noul"]
            lines += ["", f"SUA LEITURA «{premise.get('text', '')}»",
                      f"Apoio {sup:.3f} · contradição {con:.3f} · evidência avaliável {evl:.3f} — dimensões separadas, sem recomendação."]
            self.copilot.render_premise(support=sup, contradiction=con, evaluable=evl,
                                        premise=premise.get("text", ""), late=late)
        partial = result["state"]["evidence_coverage"]["source_quality"].get("full_tape") is not True
        if partial:
            lines += ["", "COBERTURA PARCIAL: a classificação se refere somente aos negócios capturados; não confirma o fluxo integral."]
        lines += ["", "Resultado histórico: prazo excedido." if late else "Esta leitura descreve o instante informado. Mudanças do mercado podem invalidá-la.",
                  "Nenhuma instrução de entrada ou ordem foi gerada."]
        put_text(self.copilot.jev_details, "\n".join(lines))
        dims = " · ".join(f"{short} {answers[key]['noul']:.2f}" for key, short in
                          (("buy_progression_supported", "prog.compra"), ("sell_progression_supported", "prog.venda"),
                           ("buy_absorption_supported", "abs.compra"), ("sell_absorption_supported", "abs.venda"),
                           ("exhaustion_supported", "exaustão"), ("evidence_insufficient", "insuficiência")))
        self.copilot.render_jev(
            context=name,
            dimensions=f"Confiança {context['confidence']:.2f} na classificação (não é chance de lucro) · {dims}",
            validity=(f"Referência {local_time(result['source_ts_ms'])} · "
                      + ("expirada — leitura histórica" if late else "válida para o instante informado")),
            late=late)
        self.model_summary.configure(text=("JEV histórico: " if late else "JEV: ") + name + (" • amostra parcial" if partial else "") + " • " + local_time(result["source_ts_ms"]))
        self.refresh_decision(force=True)

    def poll(self):
        if self.closing:
            return
        while True:
            try:
                kind, generation, result, error, elapsed = self.jobs.get_nowait()
            except queue.Empty:
                break
            self.busy.discard(kind)
            if generation != self.generation:
                continue
            if error:
                self.store.record("error", {"component": kind, "message": error})
                if kind == "jev":
                    self.latest_jev_result = None
                    self.last_model_at = None
                    self.model_deadline_ms = None
                    self.api_status.configure(text=error)
                    self.model_summary.configure(text="JEV indisponível nesta avaliação.")
                    self.copilot.render_jev_pending("JEV indisponível nesta avaliação.")
                else:
                    self.generation += 1
                    self.connection_status.configure(text=error)
                    self.source_badge.configure(text="FONTE INDISPONÍVEL • nenhuma análise atual")
                    self.snapshot = None
                    self.invalidate_model()
                    self.clear_monitor()
                    if kind == "excel":
                        self.excel_active = False
                continue
            try:
                if kind in {"excel", "csv"}:
                    self.snapshot = self.session.ingest(result, replay=kind == "csv")
                    self.connection_status.configure(text=("Excel acessível; confira a idade e a cobertura dos dados." if kind == "excel" else "Replay CSV carregado com relógio histórico."))
                    self.render_snapshot()
                elif kind == "jev":
                    self.handle_jev(result, elapsed)
            except (ValueError, KeyError) as error:
                self.generation += 1
                self.excel_active = False
                self.connection_status.configure(text="Não foi possível utilizar a leitura: " + str(error))
                self.snapshot = None
                self.clear_monitor()
                self.invalidate_model()
        now = time.monotonic()
        if self.candidate_basis is not None and (self.candidate_basis != self.values()
            or self.candidate_deadline_ms is not None and int(time.time()*1000) > self.candidate_deadline_ms):
            self.clear_candidates()
            self.candidate_status.configure(text="Comparação expirada: o capital/parâmetro mudou ou as ofertas de origem ultrapassaram 2 s. Recalcule com os dados atuais.")
        if self.next_risk_refresh is not None and int(time.time()*1000) >= self.next_risk_refresh:
            self.next_risk_refresh = None
            self.calculate_risk()
        if self.excel_active and self.excel_bridge is not None and now >= self.next_poll and "excel" not in self.busy:
            self.next_poll = now + 2
            self.run_job("excel", self.excel_bridge.read)
        if self.excel_active and self.snapshot is not None and now-self.last_watch_refresh >= 1:
            self.last_watch_refresh = now
            self.snapshot = self.session.snapshot()
            self.render_snapshot(log=False)
        if self.excel_active and self.auto_jev.get() and now >= self.next_jev and "jev" not in self.busy and self.snapshot is not None and can_classify(self.snapshot)[0]:
            self.next_jev = now + 2
            self.request_jev()
        if self.last_model_at is not None and self.session.mode == "excel_observation" and (self.model_deadline_ms is None
            or int(time.time()*1000) > self.model_deadline_ms or self.snapshot is None or not can_classify(self.snapshot)[0]):
            self.model_summary.configure(text="A última avaliação JEV expirou para acompanhamento atual. Consulte o registro no diário.")
            self.copilot.render_jev_pending("A última avaliação JEV expirou para acompanhamento atual.")
            self.last_model_at = None
            self.model_deadline_ms = None
        self.refresh_decision()
        self.root.after(150, self.poll)

    def clear_monitor(self):
        for card in self.flow_cards.values():
            card.configure(text="—")
        self.copilot.clear_market()
        self.patterns.delete(*self.patterns.get_children())
        self.chart.delete("all")
        self.coverage.configure(text="Aguardando dados válidos da fonte selecionada.")

    def render_snapshot(self, log=True):
        state = self.snapshot
        if state is None:
            return
        features = state["computed_features"]
        quote = state.get("last_quote")
        last = features.get("last_price_points") or (quote.get("last") if quote else None)
        last_text = f"{number(last):,.0f}".replace(",", ".") if last is not None else "—"
        delta_text = str(features["delta_contracts"]) if features["trade_count"] else "—"
        volume_text = str(features["total_contracts"]) if features["trade_count"] else "—"
        spread = features.get("spread_points")
        if spread is None and quote and quote.get("bid") is not None and quote.get("ask") is not None and quote["ask"] > quote["bid"]:
            spread = str(number(quote["ask"])-number(quote["bid"])) + " *"
        stamp = state.get("flow_ts_ms") or state.get("quote_ts_ms") or (quote.get("ts_ms") if quote else None)
        age = state["ts_ms"]-stamp if stamp is not None else None
        age_text = f"{age/1000:.1f} s" if age is not None and age >= 0 else "Desconhecida"
        mode = {"synthetic": "DEMONSTRAÇÃO LOCAL", "replay": "REPLAY CSV", "excel_observation": "OBSERVAÇÃO EXCEL"}.get(state["application_mode"], "SEM FONTE")
        self.flow_cards["last"].configure(text=last_text)
        self.flow_cards["delta"].configure(text=delta_text)
        self.flow_cards["volume"].configure(text=volume_text)
        self.flow_cards["spread"].configure(text=str(spread or "—"))
        self.flow_cards["age"].configure(text=age_text)
        self.source_badge.configure(text=f"{mode} • {state['symbol']} • {local_time(state['ts_ms'])} • Conta Toro não conectada")
        self.copilot.render_source({"mode": mode, "symbol": state["symbol"], "ref": local_time(state["ts_ms"]),
                                    "last": last_text, "delta": delta_text, "volume": volume_text,
                                    "spread": str(spread or "—"), "age": age_text})
        self.patterns.delete(*self.patterns.get_children())
        for hypothesis in state["hypotheses"]:
            name = KIND_NAMES[hypothesis["kind"]] + " " + SIDE_NAMES[hypothesis["side"]]
            evidence = hypothesis["evidence"]
            if hypothesis["missing"]:
                detail = "Cobertura insuficiente: " + ", ".join(hypothesis["missing"][:2])
            elif "aggressed_contracts" in evidence:
                detail = f"{evidence['aggressed_contracts']} contratos agressores; avanço direcional {evidence['directional_price_progress_points']} pontos"
            else:
                detail = "Comparação das quantidades visíveis nos mesmos níveis"
            self.patterns.insert("", "end", values=(name, STATUS_NAMES[hypothesis["status"]], detail))
        if state["application_mode"] == "synthetic":
            description = "Dados sintéticos completos apenas para testar o cálculo. Os limiares não foram calibrados no WIN."
        else:
            description = "Amostra de dados: não comprova tape integral. Medidas refletem apenas os eventos recebidos."
        if not state["evidence_coverage"].get("tape_fresh"):
            description += " Negócios ausentes ou atrasados."
        if state.get("warnings"):
            description += " " + state["warnings"][0]
        if isinstance(spread, str) and spread.endswith(" *"):
            description += " * Spread da amostra RTD; não comprova sequência nem horário de cada oferta."
        self.coverage.configure(text=description)
        self.draw_chart()
        if log and time.monotonic()-self.last_flow_log > 5:
            self.last_flow_log = time.monotonic()
            self.store.record("flow", {"symbol": state["symbol"], "application_mode": state["application_mode"],
                                       "computed_features": features, "evidence_coverage": state["evidence_coverage"]}, ts_ms=state["ts_ms"])

    def draw_chart(self):
        if not hasattr(self, "chart"):
            return
        self.chart.delete("all")
        points = list(self.session.chart)
        width, height = self.chart.winfo_width(), self.chart.winfo_height()
        self.chart.create_text(12, 12, anchor="nw", text="Preços capturados · sem previsão", fill=MUTED, font=("Segoe UI", 10))
        if len(points) < 2 or width < 50:
            return
        low, high = min(p[1] for p in points), max(p[1] for p in points)
        span = max(high-low, 5)
        coordinates = []
        for index, (_, price) in enumerate(points):
            coordinates.extend((15 + index/max(len(points)-1,1)*(width-30), height-12-(price-low)/span*(height-48)))
        self.chart.create_line(*coordinates, fill=GREEN, width=2)
        self.chart.create_text(width-12, 12, anchor="ne", text=f"{low:,.0f} — {high:,.0f}".replace(",", "."), fill=MUTED)

    def record_trade(self):
        try:
            before = self.values()
            pnl = str(number(self.manual_pnl.get()))
            after = apply_manual_pnl(before, pnl)
            if number(pnl) < 0:
                self.last_loss_ms = int(time.time()*1000)
                self.next_risk_refresh = self.last_loss_ms + 61000
                self.store.save_settings({"last_loss_ms": self.last_loss_ms})
            self.store.record("trade_manual", {"pnl_net_brl": pnl, "equity_before_brl": before["current"],
                                              "equity_after_brl": after["current"], "account_source": "manual"})
            for key, value in after.items():
                self.risk_inputs[key].set(value)
            self.store.save_settings(after)
            self.calculate_risk()
            self.refresh_journal()
            self.manual_pnl.set("0")
            if number(after["current"]) <= 0:
                messagebox.showinfo("Capital do cenário esgotado", "A perda foi registrada integralmente. O capital ficou não positivo e novos cálculos de risco estão bloqueados. Confira o saldo real na corretora antes de iniciar outro estudo.")
        except ValueError as error:
            messagebox.showerror("Resultado não registrado", str(error))

    def refresh_journal(self):
        lines = ["ÚLTIMOS REGISTROS LOCAIS", ""]
        for item in self.store.recent(150):
            payload = item["payload"]
            text = item["kind"]
            if item["kind"] == "trade_manual":
                text = f"Resultado manual: {money(payload.get('pnl_net_brl'))} → capital {money(payload.get('equity_after_brl'))}"
            elif item["kind"] == "flow":
                text = f"Fluxo {payload.get('symbol','')} · {payload.get('application_mode','')}"
            elif item["kind"] == "risk":
                text = f"Estudo de risco · lote {payload.get('sizing',{}).get('contracts','—')}"
            elif item["kind"] == "jev":
                text = "Classificação JEV registrada"
            elif item["kind"] == "recommendation":
                text = f"Conclusão: {payload.get('status', '')} · {payload.get('action', '')}"
            elif item["kind"] == "error":
                text = f"Falha em {payload.get('component','fonte')}: {payload.get('message','')}"
            lines.append(f"{local_time(item['ts_ms'])}  |  {text}")
        put_text(self.journal_text, "\n".join(lines))

    def export_journal(self):
        path = filedialog.asksaveasfilename(title="Exportar diário", defaultextension=".json", initialfile="JevWIN_diario.json", filetypes=[("JSON", "*.json")])
        if path:
            self.store.export(Path(path))
            self.refresh_journal()
            messagebox.showinfo("Diário exportado", "O arquivo contém registros locais de pesquisa e resultados informados manualmente.")

    def save_templates(self):
        directory = filedialog.askdirectory(title="Pasta para os modelos do Profit")
        if not directory:
            return
        source = resource_path("templates")
        copied = []
        if not source.is_dir():
            messagebox.showerror("Modelos indisponíveis", "Esta cópia não contém a pasta de modelos. Use o pacote completo do aplicativo.")
            return
        if source.is_dir():
            for path in source.iterdir():
                if path.is_file():
                    target = Path(directory)/path.name
                    if target.exists() and not messagebox.askyesno("Arquivo existente", f"Substituir {path.name}?"):
                        continue
                    shutil.copyfile(path, target)
                    copied.append(path.name)
        messagebox.showinfo("Modelos", "Arquivos salvos:\n"+"\n".join(copied) if copied else "Nenhum arquivo foi substituído.")

    def close(self):
        self.closing = True
        self.excel_active = False
        self.key.set("")
        self.store.close()
        self.root.destroy()


def main(argv=None):
    parser = argparse.ArgumentParser(description="JEV WIN observer and capital laboratory")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--smoke-ui", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    if args.self_test:
        result = self_check()
        result.update(app_version=VERSION, runtime=sys.version, platform=sys.platform)
        output = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        if args.report:
            args.report.write_text(output, encoding="utf-8")
        if sys.stdout is not None:
            print(output)
        return 0
    root = tk.Tk()
    app = JevWINApp(root)
    if args.smoke_ui:
        def finish():
            result = {"status": "ui_created", "tabs": len(app.tabs.tabs()), "width": root.winfo_width(), "height": root.winfo_height()}
            if args.report:
                args.report.write_text(json.dumps(result), encoding="utf-8")
            app.close()
        root.after(1500, finish)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Native Tk evidence panel; presentation only, calculations remain in core."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from panel_report import STATUS_LABELS, MODE_LABELS, CHOICE_LABELS, evidence_lines, financial_text, option_values, timestamp_text


class DecisionPanel(ttk.Frame):
    def __init__(self, parent, *, refresh, classify, demonstrate, export, actions=True):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        if actions:
            row = ttk.Frame(self)
            row.pack(fill="x", pady=(0, 10))
            for title, command in (("Atualizar avaliação", refresh), ("Consultar JEV", classify),
                                   ("Demonstrar cenários", demonstrate), ("Exportar painel HTML", export)):
                ttk.Button(row, text=title, command=command).pack(side="left", padx=(0, 7))
        self.status = ttk.Label(self, text="SEM DADOS SUFICIENTES", foreground="#f0c575", font=("Segoe UI", 22, "bold"))
        self.status.pack(anchor="w")
        self.action = ttk.Label(self, text="Carregue uma fonte para avaliar.", wraplength=1050, font=("Segoe UI", 11))
        self.action.pack(fill="x", pady=(3, 10))
        cards = ttk.Frame(self)
        cards.pack(fill="x", pady=(0, 12))
        self.cards = {}
        for index, (key, label) in enumerate((("source", "Dados"), ("capital", "Capital manual"), ("model", "JEV"))):
            card = ttk.LabelFrame(cards, text=label, padding=10)
            card.grid(row=0, column=index, sticky="nsew", padx=(0, 8))
            cards.columnconfigure(index, weight=1, uniform="cards")
            value = ttk.Label(card, text="—", wraplength=310, font=("Segoe UI", 11, "bold"))
            value.pack(anchor="w")
            self.cards[key] = value
        self.reference = ttk.Label(self, text="", style="Muted.TLabel")
        self.reference.pack(anchor="w", pady=(0, 7))
        body = ttk.Notebook(self)
        body.pack(fill="both", expand=True)
        evidence_page, options_page, history_page = (ttk.Frame(body, padding=10) for _ in range(3))
        body.add(evidence_page, text="Evidências e impedimentos")
        body.add(options_page, text="Cenários calculados")
        body.add(history_page, text="Histórico de estados")
        self.evidence = tk.Text(evidence_page, bg="#172536", fg="#e4edf6", relief="flat", wrap="word", font=("Segoe UI", 11), padx=10, pady=8)
        scrollbar = ttk.Scrollbar(evidence_page, orient="vertical", command=self.evidence.yview)
        self.evidence.configure(yscrollcommand=scrollbar.set, state="disabled")
        scrollbar.pack(side="right", fill="y")
        self.evidence.pack(fill="both", expand=True)
        ttk.Label(options_page, text="Comparação de pesquisa. Apoio contextual não é chance de lucro; não há ordenação por retorno esperado.", wraplength=1050, style="Warn.TLabel").pack(anchor="w", pady=(0, 8))
        cols = ("side", "entry", "stop", "target", "contracts", "risk", "support", "contrary", "status")
        self.options = ttk.Treeview(options_page, columns=cols, show="headings", height=8)
        headers = ("Direção", "Entrada", "Stop", "Alvo", "Contratos", "Perda planejada", "Apoio", "Contradição", "Estado")
        widths = (75, 90, 90, 90, 70, 125, 70, 85, 200)
        for col, header, width in zip(cols, headers, widths):
            self.options.heading(col, text=header)
            self.options.column(col, width=width, minwidth=50)
        horizontal = ttk.Scrollbar(options_page, orient="horizontal", command=self.options.xview)
        self.options.configure(xscrollcommand=horizontal.set)
        self.options.pack(fill="both", expand=True)
        horizontal.pack(fill="x")
        self.history = ttk.Treeview(history_page, columns=("time", "state", "action"), show="headings", height=8)
        for col, title, width in (("time", "Referência", 175), ("state", "Conclusão", 220), ("action", "Motivo / próximo passo", 590)):
            self.history.heading(col, text=title)
            self.history.column(col, width=width, minwidth=90)
        self.history.pack(fill="both", expand=True)

    def render(self, bundle, history):
        rec = bundle.get("recommendation") or {}
        snapshot = bundle.get("snapshot") or {}
        study = bundle.get("study") or {}
        model = rec.get("model") or {}
        self.status.configure(text=STATUS_LABELS.get(rec.get("status"), str(rec.get("status", "SEM_DADOS"))))
        self.action.configure(text=rec.get("action", "Carregue uma fonte para avaliar."))
        self.cards["source"].configure(text=MODE_LABELS.get(snapshot.get("application_mode"), "Sem fonte") + " · " + str(snapshot.get("symbol") or "—"))
        self.cards["capital"].configure(text=financial_text(study.get("inputs", {}).get("current")) + " · conta não conectada")
        if "FINANCIAL_VETO_PRECEDES_MODEL" in model.get("reasons", []):
            model_text = "Limite financeiro aplicado antes do JEV"
        elif bundle.get("model_request_inflight"):
            model_text = "Consulta em andamento"
        elif model.get("current"):
            model_text = CHOICE_LABELS.get(model.get("choice"), "Contexto avaliado")
        else:
            model_text = "Sem avaliação atual"
        self.cards["model"].configure(text=model_text)
        self.reference.configure(text="Referência: " + timestamp_text(bundle.get("evaluated_at_ms")) + " · avaliação experimental · nenhuma ordem enviada")
        self.evidence.configure(state="normal")
        self.evidence.delete("1.0", "end")
        self.evidence.insert("1.0", evidence_lines(bundle))
        self.evidence.configure(state="disabled")
        self.options.delete(*self.options.get_children())
        for option in rec.get("options", [])[:8]:
            self.options.insert("", "end", values=option_values(option))
        self.history.delete(*self.history.get_children())
        for item in list(history)[-50:][::-1]:
            description = f"{item.get('symbol') or '—'} · {MODE_LABELS.get(item.get('mode'), 'Sem fonte')} · {item['action']}"
            self.history.insert("", "end", values=(timestamp_text(item["ts_ms"]), STATUS_LABELS.get(item["status"], item["status"]), description))

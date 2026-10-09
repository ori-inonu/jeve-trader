"""Copilot home panel: source status, JEV context strip and declared premise.

Presentation only; all computation stays in core modules and desktop_app.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from decision_view import DecisionPanel


PANEL, FG, MUTED, GREEN, AMBER = "#172536", "#e4edf6", "#9db0c4", "#6cd9b0", "#f0c575"


class CopilotPanel(ttk.Frame):
    def __init__(self, parent, *, refresh, classify, demonstrate, export, premise_var):
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(0, 8))
        for title, command in (("Atualizar avaliação", refresh), ("Consultar JEV", classify),
                               ("Demonstrar cenários", demonstrate), ("Exportar painel HTML", export)):
            ttk.Button(actions, text=title, command=command).pack(side="left", padx=(0, 7))

        self.source = ttk.Label(self, text="SEM FONTE • carregue demonstração, Excel ou replay", style="Warn.TLabel")
        self.source.pack(fill="x", pady=(0, 7))

        market = ttk.Frame(self)
        market.pack(fill="x", pady=(0, 10))
        self.market_cards = {}
        for index, (key, label) in enumerate((("last", "Último preço"), ("delta", "Delta · 5 s"),
                                              ("volume", "Contratos · 5 s"), ("spread", "Spread"), ("age", "Idade"))):
            box = ttk.LabelFrame(market, text=label, padding=8)
            box.grid(row=0, column=index, padx=(0, 6), sticky="ew")
            market.columnconfigure(index, weight=1, uniform="copilot_cards")
            value = ttk.Label(box, text="—", font=("Segoe UI", 13, "bold"), foreground=GREEN)
            value.pack(anchor="w")
            self.market_cards[key] = value

        jev = ttk.LabelFrame(self, text="JEV — leitura do contexto observado", padding=10)
        jev.pack(fill="x", pady=(0, 10))
        self.jev_context = ttk.Label(jev, text="Ainda não consultado nesta execução", font=("Segoe UI", 14, "bold"))
        self.jev_context.pack(anchor="w")
        self.jev_dimensions = ttk.Label(jev, text="", style="Muted.TLabel", wraplength=1060)
        self.jev_dimensions.pack(fill="x", pady=(3, 0))
        self.jev_validity = ttk.Label(jev, text="", style="Muted.TLabel")
        self.jev_validity.pack(anchor="w")
        self.jev_details = tk.Text(jev, height=4, bg=PANEL, fg=FG, insertbackground=FG,
                                   relief="flat", wrap="word", font=("Segoe UI", 9), padx=8, pady=6)
        self.jev_details.pack(fill="x", pady=(7, 0))
        self.jev_details.configure(state="disabled")

        premise = ttk.LabelFrame(self, text="Sua leitura — o JEV avalia se a evidência observada apoia ou contradiz", padding=10)
        premise.pack(fill="x", pady=(0, 10))
        row = ttk.Frame(premise)
        row.pack(fill="x")
        ttk.Entry(row, textvariable=premise_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(row, text="Avaliar com JEV", command=classify).pack(side="left")
        ttk.Label(premise, style="Muted.TLabel", wraplength=1060,
                  text='Ex.: "vejo compra forte; penso em entrar se segurar acima de 130.200". Até 300 caracteres; '
                       "sua frase vai junto da próxima consulta.").pack(anchor="w", pady=(6, 0))
        self.premise_result = ttk.Label(premise, style="Muted.TLabel", wraplength=1060,
                                        text="Apoio, contradição e suficiência são dimensões separadas — "
                                             "ausência de apoio não é contradição e nenhuma é recomendação.")
        self.premise_result.pack(fill="x", pady=(5, 0))

        self.decision = DecisionPanel(self, refresh=refresh, classify=classify,
                                      demonstrate=demonstrate, export=export, actions=False)

    def render_source(self, display):
        self.source.configure(text=f"{display['mode']} • {display['symbol']} • {display['ref']} • Conta Toro não conectada")
        for key, card in self.market_cards.items():
            card.configure(text=display.get(key, "—"))

    def clear_market(self):
        self.source.configure(text="SEM FONTE • carregue demonstração, Excel ou replay")
        for card in self.market_cards.values():
            card.configure(text="—")

    def render_jev_pending(self, text):
        self.jev_context.configure(text=text, foreground=FG)
        self.jev_dimensions.configure(text="")
        self.jev_validity.configure(text="")

    def render_jev(self, *, context, dimensions, validity, late):
        self.jev_context.configure(text=context, foreground=AMBER if late else FG)
        self.jev_dimensions.configure(text=dimensions)
        self.jev_validity.configure(text=validity)

    def render_premise_pending(self, text):
        self.premise_result.configure(text=text, foreground=MUTED)

    def render_premise(self, *, support, contradiction, evaluable, premise, late):
        verdict = "leitura histórica (contexto mudou)" if late else "descreve o instante avaliado"
        self.premise_result.configure(
            text=f"«{premise}» — apoio {support:.3f} · contradição {contradiction:.3f} · "
                 f"evidência avaliável {evaluable:.3f}. {verdict}; não é recomendação.",
            foreground=AMBER if late else FG)

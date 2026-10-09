# Frontend multimercado centrado na decisão e saúde dos dados

Type: grilling
Label: wayfinder:grilling
Status: open
Assignee:
Blocked by: 03

## Question

❓ **Q4** - **Frontend multimercado centrado na decisão e saúde dos dados**: Como acomodar mercados e conexões sem multiplicar formulários ou esconder incerteza?

Alternativas reais: Duplicação de abas por provedor; 3D como navegação principal; cockpit orientado à decisão.

➡️ Recomendação JEV proposta: Workspace por venue/instrumento com decisão principal, conexões guiadas, estados de saúde/conta/evidência e detalhes progressivos.

## Stress cases

Trocar instrumento com JEV pendente deve preservar seleção atual e descartar resposta antiga; fonte ausente deve explicar por que a decisão aguarda.

## Dependencies and unresolved evidence

Orçamento de p95/memória/GPU e benchmark antes do incremento; visual 3D opcional conforme capacidades atuais.

## Comments

2026-10-09: receipt `707233ee-33cb-4bc2-9d53-22492f038f8a`, pergunta `ui_delivery`, recommendation `selected_snapshot`, confiança contextual 0.99. Projeção limitada do workspace selecionado com registry resumido dos demais, isolamento de namespaces e epoch na troca. Alternativas próximas: subscriptions filtradas ou snapshot agregado limitado. Múltiplos painéis não são requisito observado; workloads e budget seguem pendentes. [Recibo complementar](../jev-supplement.json).

2026-10-09: consulta independente da primeira fronteira, receipt `9cfb6ee1-26a5-4f2f-a44a-6b6b81bda599`, modelo `jev-1.13.0`, rubric `batch-2026-09-26.2`, pergunta `frontend_journey`, disposition `recommendation`, recommendation `workspace_decision_center`. Confiança contextual do conselho: 0.97; não é probabilidade de ganho nem autorização. [Entrada/saída sanitizadas](../jev-receipt.json).

Charting não encerra tickets grilling. Ainda não há Answer aceita ou ADR accepted; confrontar a recomendação com os relatórios finais, completar o contrato deste ticket e registrar a resolução em rodada própria.

# Fronteira de processamento: evolução modular ou migração

Type: grilling
Label: wayfinder:grilling
Status: open
Assignee:
Blocked by: 03

## Question

❓ **Q1** - **Fronteira de processamento: evolução modular ou migração**: Qual fronteira de processamento reduz o custo de evolução e mantém verificabilidade?

Alternativas reais: Cloud distribuída antecipada; reescrita integral Rust; evolução modular local.

➡️ Recomendação JEV proposta: Evoluir core Python modular com adaptadores por fonte, normalização/capacidades e motores por instrumento; preservar sidecar local e React/Tauri.

## Stress cases

O custo de operação cloud e a revalidação financeira da reescrita não removem a lacuna de dados. Reavaliar se um piloto medido demonstrar limite técnico local.

## Dependencies and unresolved evidence

Manter o core local pode limitar concorrência; validar ingestão, backlog e p95 real antes de fixar orçamento.

## Comments

2026-10-09: refinamento após pesquisas finais, receipt `707233ee-33cb-4bc2-9d53-22492f038f8a`, pergunta `local_isolation`, recommendation `modular_reuse_isolation`, confiança contextual 0.96. Preservar isolamento já existente de aquisição/subprocessos e workers, com buffers limitados; extrair outro processo somente diante de limite medido. Alternativas próximas: supervisor de dados compartilhado ou processo por provedor. [Recibo complementar](../jev-supplement.json). Continua proposto/open.

2026-10-09: consulta independente da primeira fronteira, receipt `9cfb6ee1-26a5-4f2f-a44a-6b6b81bda599`, modelo `jev-1.13.0`, rubric `batch-2026-09-26.2`, pergunta `processing_boundary`, disposition `recommendation`, recommendation `modular_local`. Confiança contextual do conselho: 1; não é probabilidade de ganho nem autorização. [Entrada/saída sanitizadas](../jev-receipt.json).

Charting não encerra tickets grilling. Ainda não há Answer aceita ou ADR accepted; confrontar a recomendação com os relatórios finais, completar o contrato deste ticket e registrar a resolução em rodada própria.

# Inteligência JEV: evidência causal, cadência e aprendizagem

Type: grilling
Label: wayfinder:grilling
Status: open
Assignee:
Blocked by: 03

## Question

❓ **Q3** - **Inteligência JEV: evidência causal, cadência e aprendizagem**: Como dar mais autonomia à inteligência sem entregar ao modelo regras financeiras ou inferir sucesso?

Alternativas reais: Consulta livre a cada tick; consulta exclusivamente manual; scheduler tipado por evidência.

➡️ Recomendação JEV proposta: Scheduler por mudança relevante com perguntas tipadas e versionadas, orçamento, backpressure e cache exato; avaliação contextual separada da financeira.

## Stress cases

Tratar gap como novo epoch e invalidar JEV pendente; evidência enriquecida deve competir contra baseline em avaliação temporal. Contexto vencedor não demonstra edge.

## Dependencies and unresolved evidence

Desfechos/revisões podem alimentar pesquisa offline; autoaprendizagem online e promoção automática permanecem fora da proposta.

## Comments

2026-10-09: receipt `707233ee-33cb-4bc2-9d53-22492f038f8a`, pergunta `scheduler_policy`, recommendation `severity_priority_aging`, confiança contextual 0.84. Prioridade por relevância/severidade de eventos elegíveis com aging; comparar com prioridade do workspace ativo/max-wait e round-robin justo. Definir fairness, coalescência, limites e critérios antes do código. Gap invalida localmente; não cria uma consulta JEV elegível por urgência. [Recibo complementar](../jev-supplement.json).

2026-10-09: consulta independente da primeira fronteira, receipt `9cfb6ee1-26a5-4f2f-a44a-6b6b81bda599`, modelo `jev-1.13.0`, rubric `batch-2026-09-26.2`, pergunta `jev_intelligence`, disposition `recommendation`, recommendation `typed_evidence_scheduler`. Confiança contextual do conselho: 1; não é probabilidade de ganho nem autorização. [Entrada/saída sanitizadas](../jev-receipt.json).

Charting não encerra tickets grilling. Ainda não há Answer aceita ou ADR accepted; confrontar a recomendação com os relatórios finais, completar o contrato deste ticket e registrar a resolução em rodada própria.

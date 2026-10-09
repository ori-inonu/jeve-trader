# Menos etapas manuais com reconciliação de conta e ledger

Type: grilling
Label: wayfinder:grilling
Status: open
Assignee:
Blocked by: 01, 02, 03

## Question

❓ **Q5** - **Menos etapas manuais com reconciliação de conta e ledger**: Quais etapas podem ser automatizadas sem fabricar saldo, posição ou permissão?

Alternativas reais: Inferir conta do mercado; manter tudo manual indefinidamente; adaptadores read-only reconciliados.

➡️ Recomendação JEV proposta: Autodescoberta de metadata, reconexão e sincronização read-only com ledger idempotente e revisões; modo manual declarado onde API faltar.

## Stress cases

Uma API de dados não fornece conta. Reconnect exige reconciliar saldo, posições e execuções; eventos duplicados ou fora de ordem não podem aumentar capital.

## Dependencies and unresolved evidence

APIs de conta B3 e escopos privados/credenciais dependem de evidência e autorização externa; o manual só deixa de ser autoridade após conciliação.

## Comments

2026-10-09: consulta independente da primeira fronteira, receipt `9cfb6ee1-26a5-4f2f-a44a-6b6b81bda599`, modelo `jev-1.13.0`, rubric `batch-2026-09-26.2`, pergunta `manual_reduction`, disposition `recommendation`, recommendation `read_only_reconciliation`. Confiança contextual do conselho: 0.99; não é probabilidade de ganho nem autorização. [Entrada/saída sanitizadas](../jev-receipt.json).

Charting não encerra tickets grilling. Ainda não há Answer aceita ou ADR accepted; confrontar a recomendação com os relatórios finais, completar o contrato deste ticket e registrar a resolução em rodada própria.


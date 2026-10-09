# Validade da evidência de liquidez quando a profundidade muda

Label: wayfinder:research
Parent: ../map.md
Status: closed (pesquisa resolvida; implementação depende do contrato ready)
Assignee: root-[identidade privada omitida]
Claimed: 2026-10-08
Tracker: local-markdown

## Question

Como manter a hipótese de redução de liquidez vinculada ao livro atual quando a fonte passa de profundidade para apenas topo, perde níveis ou muda a grade de preços? Quais limites e evidências temporais devem acompanhar a comparação entregue ao JEV?

## Context pointer

Derivado dos aceites congelados FW-07/FW-08 e do pedido de melhorar a interpretação de fluxo WIN. Reprodutor público `FlowEngine.set_book` → `FlowEngine.snapshot`: três níveis de 100 contratos às 10.000 ms, três de 20 às 10.100 ms e um de 90 às 10.200 ms. A baseline 6839d9c entrega `potential`, fração `0.8` e nenhum dado ausente, apesar de declarar apenas um nível no livro atual. Cenário sintético prova o defeito de coerência, sem provar fluxo B3, cancelamento ou lucro.

Pesquisa em cópia isolada: `.artifacts/flow-book-research-20261008/research/workspace/`. O principal conserva este ticket e a integração. Nenhuma mudança no ticket canônico de captura real nem nos documentos mantidos por outro chat.

## Resolution comments

2026-10-08: pesquisa independente concluiu o reprodutor e os casos de topo intercalado, assimetria, extremos vencidos, grade e integridade. Decisão: comparar os dois últimos snapshots observados, sem saltar topo, por lado e com grade idêntica; exigir validade de ambos os extremos no limite existente de 2000 ms. Expor intervalo, idades e níveis; não inferir a causa da redução nem integridade histórica por flags atuais. [Síntese com fontes primárias e hashes](../book-validity-research.md) e [contrato do incremento](../book-validity-contract.md). Não altera limiares de mercado, cobertura da fonte, regras financeiras ou execução de ordens. A resolução da pesquisa não prova implementação ou os aceites reais FW-06/FW-11/FW-12.

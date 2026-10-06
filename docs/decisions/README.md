# Decisões e contratos do projeto

Este índice é a entrada mínima para escolhas que não podem ficar implícitas no próximo ciclo. A aplicação entregue permanece v0.3.0. Os registros ADR abaixo estão **propostos**, sem afirmar implementação, experimento executado ou aprovação empírica.

## Restrições já documentadas a preservar

- Saída descritiva de pesquisa; sem sinal acionável de mercado ou envio de ordens. Vetos determinísticos de qualidade e risco prevalecem sobre JEV.
- Observação, cálculo, inferência contextual e estimativa de desfecho são objetos distintos. Noul/Choice/confidence não são, por seu tipo, probabilidade financeira calibrada.
- Resposta deve corresponder a fonte, geração, contrato, hipótese e geometria; inferência/cache não renova a idade dos dados.
- O objetivo de pesquisa admite esperar/`q=0`, custos, atraso e risco explícito. Margem é teto; recuperação não justifica martingale ou aumento por prejuízo.
- Mocks, exemplos matemáticos, testes de software e build não são avaliação empírica JEV/WIN nem validação nativa Windows.

Fontes: [desenho atual](../../app/DECISION_DESIGN.md), [validação v0.3](../../app/VALIDATION.md), [pesquisa §§1–3, 6–9 e 12](../research/Pesquisa_Decisao_JEV_WIN_2026-10-06.md) e [plano E01–E10](../research/Plano_Experimentos_JEV.json).

## Fila de decisões propostas

| Registro a criar | Questão / decisão proposta | Backlog | Evidência necessária para fechar |
|---|---|---|---|
| ADR-0001 | Contrato de hipótese: premissa literal e famílias progressão/absorção/exaustão, sem disjunção implícita ou reversão automática | JT-002 | Schema, payload real local, fixtures rotuladas e política de compatibilidade/versionamento. |
| ADR-0002 | Composição independente de apoio/contradição/insuficiência; comportamento de ausência, estado misto e resposta inválida | JT-003, JT-008 | Tabela de casos e política versionada; distinguir segurança de software de seletor empírico. Sem limiar financeiro arbitrário. |
| ADR-0003 | Registro experimental separado do diário visual, com schema, versões, hashes, retenção e outcomes anexados | JT-004 | Reconstrução de avaliação, migração/leitura de versões e verificação de ausência de segredos. |
| ADR-0004 | Relógios, fonte/capacidades e validade: idade de evidência separada de HTTP, heartbeat e continuidade | JT-005, JT-007 | Fixtures de clock/atraso e contrato real da fonte; TTL/horizonte não ampliados para acomodar lentidão. |
| ADR-0005 | Semântica causal de entrada, saída, empate, irresolução e custos nos cenários ideal/plausível/adverso | JT-010 | Replay congelado com eventos resolvidos, regras pré-definidas e resultados reprodutíveis. |
| ADR-0006 | Avaliação incremental e promoção: baseline pareada, divisões temporais, registro de tentativas e incerteza por sessão | JT-008, JT-009, JT-011, JT-016 | Protocolo antes do teste; resultados futuros com custos/cobertura e conclusão passou/falhou/inconclusivo. |
| ADR-0007 | Calibração/adaptação só com outcomes maduros e versões reproduzíveis | JT-013 | Manifesto temporal, confiabilidade/contagens, comparação estável e rollback. |
| ADR-0008 | Conta reconciliada antes de sizing; utilidade líquida, `q=0`, custos por quantidade e limites de trajetória | JT-014, JT-015 | Conciliação de exposição e evidência econômica fora da amostra; não recomendar lote real. |
| ADR-0009 | Gate de distribuição Windows: instalação, janela nativa, diagnóstico, dados persistentes e Excel/RTD reais | JT-006 | Relatório Windows sanitizado; lógica Linux/PE/HTML não substitui o gate. |

## Formato de cada ADR futuro

Criar `NNNN-titulo-curto.md` somente quando houver conteúdo concreto. Usar:

1. **Status e data:** proposto, aceito, substituído ou rejeitado; incluir revisão de código e escopo.
2. **Problema e evidência:** links para código/documento/dataset; separar observado, calculado, inferido e proposto.
3. **Decisão:** contrato/regra literal, sem pressuposto oculto; incluir alternativas relevantes e razão da escolha.
4. **Consequências:** compatibilidade, limitações, migração e casos de falha.
5. **Validação e gate:** comandos/artefatos e o que demonstram; pendências empíricas ou de ambiente continuam explícitas.
6. **Vínculos:** itens JT, experimentos E e eventual ADR substituído.

Aceitar uma decisão de engenharia não prova benefício econômico. Para E01–E10, conservar dependências/critério do [JSON original](../research/Plano_Experimentos_JEV.json) e atualizar o [backlog](../BACKLOG.md) apenas com evidência. Não há meta universal de amostra, lucro ou número de verificações que transforme proposta em vantagem validada.

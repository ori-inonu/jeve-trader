# Utilidade após latência e execução

ID: WF-03
Type: research
Label: wayfinder:research
Status: resolved
Parent: [Mapa](../map.md)
Created: 2026-10-07
Blocked by: 01

## Question

Qual informação e qual oportunidade ainda são utilizáveis quando a decisão chega à pessoa, considerando captura, consulta, apresentação e execução manual?

## Alternativas

| Alternativa | Consequência |
|---|---|
| Replay pelo timestamp do negócio com preenchimento imediato | Simples, mas concede informação ou execução antes de estarem disponíveis. |
| Replay com um atraso fixo e preenchimento integral | Permite um comparador inicial; não representa variação de latência, ausência de entrada ou execução parcial. |
| Replay por disponibilidade, com estados de execução e limites de observação | Mantém a causalidade; exige relógios, hipóteses de execução e identificação explícita do que não é observável. |

## Evidência

**Observado:** o laboratório atual já faz junção contextual por disponibilidade e separação temporal com maturidade do rótulo. O proxy de execução por preços não comprova fila, execução humana ou preenchimento parcial. Há trabalho existente a estender, não um replay a presumir inexistente.

**Princípio externo:** a documentação de [junções point-in-time do Feast](https://docs.feast.dev/getting-started/concepts/point-in-time-joins) distingue tempo do evento de disponibilidade: sem filtro adicional pelo momento de criação, correções posteriores ainda podem entrar na recuperação histórica. O replay deverá controlar disponibilidade, chegada e apresentação ao usuário, não somente o timestamp do negócio.

**Custos:** a tabela educativa da [B3](https://edu.b3.com.br/pt/day-trade) informa R$0,50 para entrada e saída do WIN; o comparador experimental inspecionado aplica R$0,50 em cada lado. A página educativa não determina a tarifa aplicável à conta. A diferença exige reconciliação documental antes de qualquer uso operacional.

## Direção recomendada

Especificar um registro de oportunidade e um relógio causal:

1. Timestamp do evento e da captura, chegada ao motor e correção posterior, quando conhecidos.
2. Corte das informações usadas, envio da consulta, chegada da resposta, composição do plano e apresentação.
3. Instante da decisão humana e chegada da ordem manual, quando observáveis; execução de cada parcela e encerramento.
4. Relógio de referência, desvio conhecido e tratamento de relógios ausentes ou incompatíveis.

Um evento só pode influenciar uma decisão depois de estar disponível. Uma correção tardia é visível a decisões posteriores; não reescreve silenciosamente o conjunto conhecido no passado. Sem relógio confiável, o cenário deve declarar a limitação em vez de produzir precisão artificial.

Definir estados distintos de execução: não submetida, submetida sem entrada, integral, parcial, cancelada e desconhecida. Desconhecido ou censurado não equivale a resultado zero. Para ausência de entrada comprovada, o PnL de negociação pode ser zero; eventuais despesas de pesquisa pertencem ao registro de despesas da política.

Separar `P(resultado líquido positivo | entrada executada)` de `P(resultado líquido positivo | oportunidade)`. Definir o denominador, a maturidade do rótulo e a massa desconhecida de cada estimativa. Não renormalizar casos desconhecidos como se não existissem.

O contrato de `OutcomeEstimate` deverá identificar evento financeiro, oportunidade, candidato, horizonte, quantidade, premissas de execução, distribuição de resultados e incerteza, cobertura, versões e registro de validação. Distribuição por quantidade pode diferir com preenchimento, liquidez e custos; não será automaticamente uma multiplicação do resultado de um contrato.

Comparar cadência fixa com gatilhos de mudança material na mesma sequência de oportunidades. Definir previamente o que é mudança material: premissa, geometria, cobertura, conta, custos ou passagem da validade. Registrar consultas vencidas, descartadas, reutilizadas e oportunidades que deixaram de ser aproveitáveis antes da resposta. Os defaults atuais de cadência e timeout são apenas comparadores.

Separar custos por origem: tarifa B3, corretagem, spread, slippage, tributos quando aplicáveis ao estudo e despesas de consulta. Documentar unidade, moeda, vigência e quantidade. Se o preço executado já incorpora um componente, não descontá-lo novamente. Não inferir fila ou liquidez completa a partir do Excel parcial.

Reconciliar a tabela aplicável à conta com evidência datada. Margem da corretora, margem educativa, reserva interna e perda de estresse são conceitos diferentes; nenhuma página educativa altera automaticamente os defaults do aplicativo.

## Dependências e escopo

A [identidade causal](01-identidade-causal.md) fornece referências e versões. Este contrato fundamenta o [dimensionamento incerto](04-dimensionamento-incerto.md) e os relógios da [interface](05-interface-verificavel.md).

Estende E01, E05 e E06. O [protocolo de evidência](06-evidencia-promocao.md) deve ser fechado antes dos experimentos confirmatórios. Não exige acesso real, feed pago ou envio de ordens.

## Critérios de aceite — próxima etapa

Entregar a máquina de estados da oportunidade e da execução; a tabela de relógios e disponibilidade; as regras de resultado desconhecido; um contrato de custos reconciliável por conta; e um desenho pareado para comparar cadências. A documentação deve identificar quais cenários são mensuráveis com cada fonte e quais permanecem apenas simulações.

### Cenários de verificação futura

| Caso | Resultado exigido |
|---|---|
| Negócio chega depois do momento histórico da decisão | Não aparece nos atributos daquela decisão. |
| Correção tardia de preço ou volume | Mantém trilha da informação originalmente disponível. |
| Resposta correta chega após a janela útil | Histórico com motivo de descarte; não conta como decisão disponível a tempo. |
| Ordem não entra | Evento sem execução separado de perda, censura e desconhecimento. |
| Apenas parte da quantidade entra | Custos e patrimônio usam as parcelas efetivamente modeladas ou observadas. |
| Gap e cobertura perdida | Sem inventar preenchimento no stop ou continuidade da fita. |
| Custos não lineares por quantidade | Distribuição líquida e admissibilidade recalculadas por quantidade. |
| Cadência por evento deixa uma oportunidade passar | Oportunidade permanece no denominador; ausência de consulta é registrada. |
| Fonte não mede a chegada à ordem manual | Latência de execução é hipótese, com análise de sensibilidade. |

## Answer

Resolvido pelo [contrato causal-execution-v1](../contracts/03-tempo-execucao.md): relógios com domínio/erro, corte e disponibilidade dos atributos, máquinas separadas de oportunidade e execução, parcelas/resultado desconhecido, OutcomeEstimate e custos reconciliáveis. O desenho pareado distingue orçamento igual e gasto natural, preserva oportunidades perdidas e não inventa respostas contrafactuais. A tabela de fontes identifica o que Excel, fixtures, livro manual e SDK podem sustentar.

Os nove cenários futuros têm resultados exigidos; o exemplo de probabilidade mostra limites lógicos sem eliminar desconhecidos. A reconciliação operacional de tarifa/margem e as medições reais continuam pendentes. Isso resolve o desenho documental, sem validar execução ou modificar defaults.

## Comments

2026-10-07 — Revisão dos relógios, estados, custos, comparação e limites de fonte concluída; aceite documental resolvido. Testes e medições ficam na implementação futura.

2026-10-07 — Reivindicado após a resolução de WF-01; revisão do contrato de relógios, execução, custos e cadência em andamento.

2026-10-07 — Direção registrada. Nenhuma hipótese de execução foi validada nesta entrega; a divergência de custos permanece uma pendência documental.

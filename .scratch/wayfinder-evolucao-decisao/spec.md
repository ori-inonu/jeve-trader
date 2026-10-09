# Especificação transversal — planejamento Wayfinder

Status: contracts_resolved_implementation_pending
Date: 2026-10-07
Parent: [Evolução da inteligência e da interface](map.md)

## Uso e alcance

Este documento organiza os contratos internos resolvidos e aponta para sua fonte de verdade em `contracts/`; os tickets preservam a pergunta e a resolução. Não muda schemas, endpoints ou parâmetros do aplicativo. O complemento de pesquisa identifica o checkout observado; a próxima sessão deve conferir novamente os fontes antes de converter especificações em tarefas de implementação.

Os seis tickets e as decisões do mapa foram resolvidos documentalmente, com registro de parâmetros, vínculos e [auditoria de aceite](acceptance-audit.md). Esse fechamento não comprova os aceites futuros de software, interface ou economia. A [sequência de implementação](implementation-plan.md) define incrementos e verificações necessários.

## Vocabulário

| Termo | Significado nesta especificação |
|---|---|
| Observado | Dado recebido de fonte identificada, com cobertura e horários disponíveis. |
| Calculado | Resultado determinístico, com fórmula, unidade e entradas versionadas. |
| Contextual JEV | Julgamento tipado sobre uma proposição, ligado às evidências do candidato. |
| Estimado financeiro | Distribuição de desfechos definidos, avaliada em resultados posteriores e ligada a registro de validação. |
| Candidato | Hipótese com premissa, lado, geometria, janela observada e horizonte definidos. |
| Avaliação | Instância imutável que associa candidato e versões às entradas e respostas usadas. |
| Oportunidade / episódio | Unidade comum para comparação; candidatos simultâneos e consultas repetidas não multiplicam a amostra financeira. |
| Validade | Intervalo e condições em que a avaliação pode orientar uma decisão atual. |
| Horizonte | Intervalo futuro no qual o desfecho será apurado; não prolonga a validade da informação. |
| Cobertura desconhecida | Fonte sem prova suficiente para o evento; distinta de resultado econômico zero. |
| Capacidade | Restrição de margem, exposição e reserva; distinta da quantidade economicamente preferida. |

## Contratos internos e fonte de verdade

| Contrato | Especificação responsável |
|---|---|
| `MarketSnapshot`, identidade da sessão e referência às evidências | [Identidade causal da decisão](contracts/01-identidade.md) |
| `DecisionPlan`, identidade do candidato e avaliação imutável | [Identidade causal da decisão](contracts/01-identidade.md) |
| Catálogo de hipóteses e avaliações por candidato/horizonte | [Contratos das hipóteses JEV](contracts/02-hipoteses.md) |
| Disponibilidade, execução e `OutcomeEstimate` | [Utilidade após latência e execução](contracts/03-tempo-execucao.md) |
| Distribuição por quantidade e trajetória da política | [Dimensionamento sobre distribuições incertas](contracts/04-dimensionamento.md) |
| Estados visuais e inspeção histórica | [Interface verificável e estável](contracts/05-interface.md) |
| Registro de validação, comparação e promoção | [Evidência incremental e promoção](contracts/06-protocolo.md) |

## Registro de parâmetros

Cada parâmetro deverá carregar: nome e unidade; valor ou `não definido`; escopo (fonte, conta, contrato, candidato, política); origem; vigência; versão; responsável; regra de seleção; dados de desenvolvimento; registro de validação; condição de invalidação. Distinguir `observado`, `manual não conferido`, `comparador experimental`, `em seleção` e `confirmado no escopo`.

| Grupo | Itens | Regra de escolha | Estado desta rodada |
|---|---|---|---|
| Fonte e conta | Capacidades, resolução, timestamps, continuidade, patrimônio, exposição, margem, custos, reconciliação e vigência | Contrato da fonte e evidência da conta; valores ausentes conservam motivo e origem | Excel parcial e conta manual; tarifa aplicável pendente |
| Hipóteses JEV | Catálogo, perguntas, opções, categorias calculadas, requisitos de cobertura e tolerâncias | Casos anotados; fórmulas determinísticas versionadas; modelo congelado na comparação | Direção especificada; robustez remota não demonstrada |
| Tempo | Janela observada, horizonte futuro, cadência, validade, timeout, gatilho material e atraso humano | Resolução dos dados e utilidade disponível após atraso; desenvolvimento separado da confirmação | Defaults atuais servem de comparador, sem otimização alegada |
| Economia | Reserva interna, função de custo por quantidade, fração de Kelly, conjunto de incerteza, adaptação ao drawdown | Trajetórias de patrimônio próprias e comparação com zero; tolerância de perda explicitada antes do teste | Nenhuma nova fração ou lote aprovado para conta real |
| Evidência | Datas das divisões, maturidade dos rótulos, agrupamento, métricas, precisão, critérios de confirmação e orçamento | Protocolo congelado antes do período confirmatório | Dados, orçamento e limiares confirmatórios ainda não definidos |

Valores encontrados no comparador em 07/10/2026: fração 0,25; referência de drawdown 0,30; validade contextual de 2.000 ms; intervalo mínimo JEV de 10 s; timeout de 3 s; horizonte padrão do plano de 60 s; janela de features do laboratório de 30 s. São decisões existentes a avaliar, não parâmetros escolhidos por esta pesquisa. A tolerância documental não será ampliada apenas para acomodar consultas lentas.

A tabela educativa da B3 e o default experimental divergem no custo de entrada e saída. A reconciliação, a fonte e a vigência pertencem a [Utilidade após latência e execução](issues/03-latencia-execucao.md); este registro não atribui tarifa operacional.

## Rastreabilidade, sem duplicar pesquisas

O catálogo [E01–E10](../../docs/research/Plano_Experimentos_JEV.json) conserva os IDs e os status de experimentos. Os tickets complementam seus contratos, sem criar resultados novos.

| Decisão | Experimentos estendidos | Backlog relacionado |
|---|---|---|
| [Identidade causal da decisão](issues/01-identidade-causal.md) | E01, E02, E04, E05, E09 | JT-004, JT-005, JT-009, JT-013 |
| [Contratos das hipóteses JEV](issues/02-contratos-hipoteses.md) | E02, E03, E04, E08, E09 | JT-002, JT-003, JT-008, JT-009, JT-012, JT-016 |
| [Utilidade após latência e execução](issues/03-latencia-execucao.md) | E01, E05, E06 | JT-005, JT-007, JT-010, JT-014 |
| [Dimensionamento sobre distribuições incertas](issues/04-dimensionamento-incerto.md) | E06, E09, E10 | JT-010, JT-013, JT-014, JT-015 |
| [Interface verificável e estável](issues/05-interface-verificavel.md) | Exposição verificável dos resultados E01–E10 | JT-005, JT-006, JT-014, JT-015 |
| [Evidência incremental e promoção](issues/06-evidencia-promocao.md) | E02–E10; requisitos de fonte E01 | JT-004, JT-011, JT-012, JT-013, JT-015, JT-016 |

## Ordem da próxima etapa

Os contratos foram resolvidos na ordem de dependência. Implementar primeiro identidade e vínculos, depois semântica JEV e disponibilidade/execução, seguidos de dimensionamento e interface; o protocolo já definido orienta o laboratório. A sequência e o escopo de cada incremento estão no [plano](implementation-plan.md). Congelar o manifesto e cumprir G1 antes de qualquer confirmação econômica. Resolução documental e demonstração empírica têm registros distintos.

Antes de começar uma implementação, consultar o status atual, reivindicar o trabalho no tracker e recapturar o trecho relevante do checkout. Converter somente contratos resolvidos em tarefas de código; separar explicitamente qualquer preferência humana ainda necessária.

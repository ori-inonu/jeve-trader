# Roteiro do Jeve Trader

**Referência:** 06/10/2026. **Estado entregue:** v0.3.0. **Próximo ciclo proposto:** v0.4, ainda não implementado por este roteiro.

## Entrada rápida para o próximo ciclo no Codex

1. Leia [BACKLOG.md](BACKLOG.md), começando por JT-001 a JT-006, e [decisões](decisions/README.md).
2. Reproduza a linha de base antes de alterar o comportamento. Preserve o modo de pesquisa, os vetos determinísticos e a correspondência entre resposta, fonte, geração e geometria.
3. Corrija o contrato de hipótese e a composição da revisão; depois acrescente registro experimental e relógios. A interface e o HTML devem explicar a mesma decisão.
4. Execute os testes relevantes e registre resultados atuais. A evidência de v0.3 não substitui execução na revisão modificada.
5. Não declare integração Windows validada sem testar instalação e abertura nativa. Não declare E01–E10 concluídos a partir de fixtures locais.

O detalhamento auditado está em [Pesquisa_Decisao_JEV_WIN_2026-10-06.md](research/Pesquisa_Decisao_JEV_WIN_2026-10-06.md); dependências, braços e critérios originais em [Plano_Experimentos_JEV.json](research/Plano_Experimentos_JEV.json). O desenho existente está em [DECISION_DESIGN.md](../app/DECISION_DESIGN.md) e o alcance da validação entregue em [VALIDATION.md](../app/VALIDATION.md).

## Objetivo e limites permanentes

O objetivo de pesquisa é maximizar utilidade líquida sustentável, considerando custos, atraso, incerteza, perda extrema e limites explícitos de risco. Esperar e `q=0` são alternativas válidas. Margem determina um teto admissível; não determina a melhor quantidade. Recuperar uma perda não cria evidência nem justifica martingale ou aumento de lote motivado pela recuperação.

A v0.3 é um aplicativo descritivo de pesquisa. Este plano não habilita mercado ao vivo, sinal acionável ou envio de ordens. Apoio contextual JEV não é probabilidade de lucro ou de alvo antes do stop. As geometrias e medidas atuais permanecem hipóteses de engenharia, sem vantagem econômica demonstrada.

## O que a evidência atual permite afirmar

| Evidência | Alcance | Limite |
|---|---|---|
| Validação v0.3 documentada | 166 testes de software em Python/Linux e autoteste sintético | Não são operações, chamadas reais JEV ou validação nativa Windows. |
| Auditoria e script de pesquisa | Projeção perde `premise`; exemplos matemáticos e de expiração reproduzíveis | Não medem respostas do JEV, latência real ou rentabilidade. |
| Relatórios de build | Empacotamento, recursos, hashes e verificações especificadas nos relatórios | Não demonstram instalação, janela, COM/RTD real ou desempenho no computador do usuário. |
| Plano E01–E10 | Desenho de experimentos propostos | Nenhum experimento empírico executado; orçamento API e tamanho de amostra não definidos. |

Fontes: [pesquisa, §§2 e 12](research/Pesquisa_Decisao_JEV_WIN_2026-10-06.md), [plano JSON](research/Plano_Experimentos_JEV.json), [validação v0.3](../app/VALIDATION.md). Registre separadamente o que foi observado, calculado, inferido e proposto.

## Ciclo imediato: v0.4 — contrato e rastreabilidade

| Entrega | Itens | Gate finito de software |
|---|---|---|
| Linha de base reproduzível e regressões robustas | JT-001 | Registrar comandos, ambiente, versão e resultados atuais; fixtures adversariais cobrem omissão de premissa, ausência/contradição, resposta vencida, fonte trocada e veto financeiro. |
| Premissa preservada e famílias distintas | JT-002 | A proposição exata chega ao payload; progressão, absorção e exaustão têm confirmação, invalidação e horizonte próprios; absorção não implica automaticamente reversão. |
| Suficiência consumida explicitamente | JT-003 | Apoio, contradição e insuficiência são independentes; insuficiência, resposta ausente ou inconsistência têm estado/motivo explícito e não promovem revisão silenciosamente. Sem limiar escolhido para parecer rentável. |
| Registro completo e versionado | JT-004 | Reconstituir uma avaliação a partir de estado, perguntas exatas/ordem, versões, hashes, resposta e regra aplicada, sem segredo; retenção independente do diário visual. |
| Qualidade e idade por etapa | JT-005 | Relógios de origem, recebimento, processamento, submissão, resposta e tela; latência HTTP separada de idade da evidência; cobertura desconhecida e relógio não confiável explícitos. |
| Validação Windows real | JT-006 | Instalar, abrir, diagnosticar e desinstalar em Windows x64; validar Excel/COM e perfil RTD real, com evidência sanitizada. |

**Gate de fechamento do ciclo:** JT-001–JT-005 com critérios verificados e relatório atualizado. **Gate adicional para anunciar distribuição Windows validada:** JT-006. Quando Windows/Excel não estiverem disponíveis, documentar o bloqueio e manter a validação pendente; inspeção de PE ou teste Linux não o satisfaz. Estes gates não concluem a parte remota de E02, nem os experimentos de integridade/latência E01/E05. A v0.3 continua sendo a versão entregue até uma implementação e validação futuras.

Não ampliar TTL para acomodar chamada lenta, converter confiança contextual em probabilidade financeira ou alterar parâmetros de risco para melhorar uma demonstração. Qualquer seletor numérico futuro requer protocolo e validação separados do teste final.

## Ciclos posteriores e seus gates

| Ciclo proposto | Trabalho | Condição para avançar |
|---|---|---|
| Fonte e protocolo | JT-007, JT-016; instrumentação JT-005 | Perfil de fonte real identificado, eventos/correções/sessões reconciliáveis e lacunas explicitadas; protocolo JEV congelado e orçamento definido antes de chamadas. Sem denominador confiável, cobertura continua desconhecida. |
| Interpretação robusta | JT-008, JT-009, JT-016 | Casos e rótulos congelados; fidelidade, erro/cobertura e perturbações medidos com repetição e incerteza. Chamadas correlacionadas não viram observações independentes. |
| Replay causal e desfechos | JT-010 | Entrada e saída respeitam disponibilidade temporal; não entrada, timeout e irresolução separados; custos e cenários ideal/plausível/adverso reproduzíveis. |
| Valor incremental | JT-011 | Mesmas oportunidades para regras, baseline quantitativa, baseline+JEV e JEV seletivo; comparação pareada líquida e incerteza por sessão em blocos futuros intocados. |
| Refinamento e calibração | JT-012, JT-013 | Features e episódios acrescentam contribuição fora da amostra; probabilidades de desfecho calibradas sobre resultados maduros, sem vazamento. Resultado negativo também encerra uma hipótese. |
| Conta e dimensionamento | JT-014, JT-015 | Conta/exposição conciliadas, vantagem econômica e execução avaliadas; comparação inclui `q=0`, custos por quantidade e limites de trajetória. Nenhuma quantidade é recomendação para conta real. |

## Mapa exato dos experimentos E01–E10

A coluna de dependências abaixo reproduz o JSON. Dependências adicionais de engenharia ficam no backlog; instrumentação local não substitui o gate empírico.

| ID | Prioridade / título original | Dependências originais | Trabalho correspondente | Gate de promoção original operacionalizado |
|---|---|---|---|---|
| E01 | P0 — Contrato da fonte e integridade | — | JT-007 | Prova da fonte e reconciliação antes de declarar tape completo; distinguir duplicata, correção e tipo especial. |
| E02 | P0 — Premissa explícita e dimensões independentes | — | JT-002, JT-003, JT-016 | Premissa exata no payload; ausência distinta de contradição; validação remota somente com casos e orçamento API. |
| E03 | P1 — Abstenção e inconsistência | E02 | JT-003, JT-008 | Relatar erro e cobertura; não obter precisão apenas recusando quase tudo; nenhum limiar escolhido no teste externo. |
| E04 | P1 — Perturbações sem mudança de sentido | E02 | JT-009 | Repetição e incerteza para ordem, nomes e simetria; correlação entre chamadas explicitada. |
| E05 | P0 — Orçamento de tempo útil | E01 | JT-005, JT-007, JT-010 | Medir percurso e respostas vencidas; horizonte/validade definidos em experimento causal, sem aumentar validade para ocultar lentidão. |
| E06 | P0 — Desfechos e execução causal | E01, E05 | JT-010 | Sem preços anteriores à chegada, futuro no estado ou desempate favorável inventado. |
| E07 | P1 — Valor incremental do JEV | E02, E03, E04, E06 | JT-011 | Benefício após custos persiste em blocos futuros e execução adversa; tentativas registradas e incerteza por sessão. |
| E08 | P2 — Ablação de microestrutura | E07 | JT-012 | OFI exige eventos adequados; ajuste contemporâneo não é previsão; conservar apenas contribuição adicional. |
| E09 | P2 — Calibração e mudança de regime | E07 | JT-013 | Não renomear Noul contextual como probabilidade financeira; atualizações usam somente outcomes disponíveis naquele instante. |
| E10 | P3 — Quantidade e crescimento de patrimônio | E06, E07, E09 | JT-014, JT-015 | Margem é restrição; vantagem, custos por quantidade, conta conciliada e tolerância explícita precedem sizing; sem recomendação real. |

## Regra para resultados e promoção

Cada experimento deve encerrar com protocolo versionado, dataset/manifesto, comandos reprodutíveis, relatório de resultados e conclusão **passou / falhou / inconclusivo** frente a critérios pré-especificados. Definir precisão desejada e unidade efetiva por sessão antes de calcular amostra; não adotar número universal de trades, lucro arbitrário ou quantidade de testes como prova de vantagem. Qualquer execução empírica futura requer dados e acesso apropriados; este roteiro não autoriza conexão ou operação real.

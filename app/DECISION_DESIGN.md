# Projeto do motor de decisão de tape reading

Este é um desenho de pesquisa para WIN/B3. Os sinais microestruturais abaixo são hipóteses a testar no feed disponível e não regras comprovadas de lucro. As capacidades do JEV e da ProfitDLL estão documentadas nas fontes do README; a seleção de features e políticas a seguir é proposta de engenharia.

## Implementação v0.3.0

O aplicativo `desktop_app.py` implementa leitura de Excel existente por COM, importação de negócios CSV, acumulador de eventos, medidas em janelas de 5 e 30 segundos, classificação local de hipóteses, extração de níveis observados, comparação de até oito geometrias, consultas estruturadas ao JEV e diário SQLite. A Central de decisão reúne conclusão, evidências, impedimentos, alternativas e histórico. Há instalador por usuário e pacote portátil Windows x64 com runtime incluído e diagnóstico. A integração no computador do usuário e a abertura nativa da janela ainda precisam de validação.

O modo `combined` lê a tabela de cotações e a tabela de negócios do mesmo arquivo Excel aberto, em um ciclo. Qualquer falha em uma tabela invalida o ciclo inteiro; a deduplicação só é confirmada depois de validar ambas. Essa combinação corrige a limitação anterior de escolher apenas uma fonte, mas as leituras continuam sequenciais e a captura parcial. A aba de negócios do modelo começa vazia e depende de uma exportação real compatível; não há coleta automática de Times & Trades.

O Excel é consultado em intervalos de aproximadamente dois segundos, sem sobreposição de leituras. A consulta automática ao JEV tem intervalo mínimo de dez segundos e orçamento de chamadas configurável. Esses intervalos definem um observador amostrado; não equivalem a captura integral de cada negócio ou latência garantida para scalping.

O arquivo de cotações RTD não fornece agressor ou histórico integral de trades. A aplicação mantém esse limite explícito, bloqueia análise de fluxo quando não há negócios suficientes e não converte valores amostrados em eventos autoritativos de livro. Dados sintéticos completos existem apenas para verificar os cálculos.

## 1. O evento recente e o contexto

Toda observação de mercado já ocorreu quando chega ao sistema. A escolha útil é quanto atraso tolerar e qual informação ainda ajuda a decidir. O projeto prioriza eventos recentes de negociação e ofertas, com contexto curto, sem usar cruzamentos de médias ou osciladores como condição central.

Uma agressão compradora elevada, isoladamente, não distingue continuidade de absorção. O sistema precisa comparar fluxo executado, resposta do preço e comportamento da liquidez. Retirada de oferta não prova manipulação; uma oferta grande não garante que permanecerá; uma corretora visível não identifica necessariamente um único investidor.

Há pesquisa sobre relação de eventos do livro e variações de preço de curto prazo: [Cont, Kukanov e Stoikov — The Price Impact of Order Book Events](https://arxiv.org/abs/1011.6402) e [Gould e Bonart — Queue Imbalance as a One-Tick-Ahead Price Predictor](https://arxiv.org/abs/1512.03492). São estudos em ações americanas; apoiam investigar essas variáveis, não comprovam vantagem no WIN nem desempenho do JEV. A adaptação proposta precisa de teste próprio no mercado e horizonte escolhidos.

## 2. Mapa de dados e decisões

| Bloco | Dados/medidas calculadas em código | Pergunta contextual e limitação |
|---|---|---|
| Negócios executados | Preço, quantidade, agressor quando informado, frequência, tamanho relativo, sequência de execuções | Há iniciativa persistente ou apenas evento isolado? Agressão desconhecida não pode ser inventada. |
| Volume e intensidade | Contratos por segundo, desequilíbrio comprador/vendedor, aceleração, concentração por preço | O fluxo recente está crescendo, desacelerando ou alternando? Limiar fixo deve ser testado por horário/regime. |
| Resposta do preço | Deslocamento, permanência fora de nível, retorno após rompimento, avanço por unidade de volume | O mercado aceita o preço ou o movimento falhou? Classificar observação não garante continuação futura. |
| Livro de ofertas | Spread, profundidade, desequilíbrio por faixa, reposição, consumo e cancelamentos quando acessíveis | A liquidez absorve ou cede? Snapshot raso não reconstitui a fila ou ordens ocultas. |
| Absorção | Volume executado repetido contra região sem avanço proporcional, com reposição observável | Há evidência compatível com absorção? Não declarar iceberg ou intenção do participante como fato. |
| Exaustão | Desaceleração de agressões e perda de progressão, comparadas à janela anterior | Falta iniciativa nova ou existe apenas pausa? Exige comparação temporal. |
| Rompimento/falha | Negócios além de nível, manutenção/retorno, consumo de ofertas e resposta oposta | O rompimento está sustentado pelas observações? Definir duração e invalidação antes do teste. |
| Contexto da sessão | Abertura, ajuste anterior, máximas/mínimas observadas, volume por preço e áreas de negociação | Onde a hipótese deixa de fazer sentido? Referências contextualizam; não são barreiras garantidas. |
| Eventos externos | Calendário oficial, anúncio conhecido, status de leilão e interrupções | A volatilidade esperada permite o setup? Notícia não conhecida não pode ser antecipada. |
| Instrumentos relacionados | IND, WDO e outros dados licenciados e sincronizados, se usados | Há confirmação ou divergência útil? Adicionar somente se provar ganho incremental. |
| Conta e execução | Saldo líquido, margem, risco já comprometido, posição e ordens confirmadas | A proposta cabe na exposição? Essa decisão é determinística, não delegada ao JEV. |
| Qualidade do sistema | Perdas de sequência, atraso de cada canal, relógio, latência e reconciliação | Ainda há informação suficiente para um sinal utilizável? Dado ausente não significa ausência de risco. |

"Volume financeiro" no futuro é notional negociado, calculável por preço × multiplicador × quantidade. Não equivale ao dinheiro novo depositado por um participante nem revela sua riqueza. O modelo deve receber o nome correto da métrica. Evite tratar agressão como prova de posição direcional líquida de um agente.

## 3. Features e memória

A implementação usa janela curta de 5 s, comparação com os 5 s anteriores e contexto de 30 s, com retenção de até 60 s. Os valores em `flow_rules.json` são hipóteses de engenharia sem calibração no WIN. A quantidade de ticks pode variar muito entre regimes; não assumir que igual número de mensagens corresponde a igual duração ou informação.

Calcule numericamente volume, deltas, spread, volatilidade local, posição relativa a níveis, intensidade e diferenças entre janelas. Envie ao JEV os números e relações já computadas, acompanhados de definições e indicadores de cobertura. Não peça ao modelo para calcular somas, distâncias ou vencimentos.

Mantenha quatro tipos de memória separadamente: eventos observados; estado atual reconstruído; hipóteses e sinais emitidos; resultados observados posteriormente. Não insira resultados futuros no estado usado para uma decisão histórica. A memória pertence ao aplicativo, e não a uma suposta conversa persistente no endpoint JEV.

## 4. Comparar entradas, stops, alvos e espera

O estado atual permite gerar candidatos finitos. Cada candidato carrega: lado, condição de entrada, preço ou faixa admitida, referência de invalidação, stop técnico, referência de alvo, limite de duração, evidências necessárias, evidências contrárias e metadados temporais.

O aplicativo extrai preços executados repetidos e extremos da janela anterior dos eventos retidos. A entrada usa a melhor oferta disponível, identificando quando ela é apenas uma amostra RTD. `candidate_research.py` combina até oito pares de stop e alvo a partir dos níveis observados; não inventa um nível distante para fazer o resultado caber no capital. Esses níveis não são suportes/resistências validados. A confirmação de rompimento/pullback permanece futura. A matriz finita não abrange todas as situações possíveis do mercado.

O motor deve primeiro eliminar: stop/alvo incorretos, preço fora do tick, referência sem evidência, dados insuficientes, custo inviável, margem insuficiente, risco excedido e sessão imprópria. O JEV pode avaliar apoio e contradição contextual das propostas que cabem no estudo financeiro. Nesta versão desktop, a saída é descritiva e sem ordem ou sinal de compra/venda acionável. Se faltam dados, a análise fica indisponível; não há seleção de operação por valor esperado.

Uma relação ganho/risco alta pode decorrer de um alvo distante e improvável. A probabilidade do evento “alvo antes do stop dentro de um horizonte definido” depende de dados de resultados. Só depois dessa calibração pode haver cálculo de valor esperado, comparação econômica de candidatos e dimensionamento dependente de vantagem estimada.

## 5. Fórmulas do motor monetário

Para quantidade `q`, valor por ponto `v`, distância até o stop `d_stop`, distância até o alvo `d_target`, taxas por contrato `c` e slippage total em pontos `s`:

```text
risco_por_contrato = d_stop × v + c + s × v
ganho_liquido_se_alvo = d_target × v − c − s × v
relacao_liquida = ganho_liquido_se_alvo / risco_por_contrato
lote_por_risco = floor(orcamento_restante / risco_por_contrato)
margem_por_contrato = max(margem_B3, margem_corretora)
lote_por_margem = floor(margem_utilizavel / margem_por_contrato)
lote = min(lote_por_risco, lote_por_margem, limite_do_perfil, quantidade_candidata)
```

No perfil com reserva conjunta, `margem_utilizavel = min(margem_disponivel, patrimonio) − reserva_caixa` e o denominador do lote por margem passa a `margem_por_contrato + risco_por_contrato`. A reserva de perda é uma decisão da política; não altera a exigência da B3 nem garante cobertura de gaps.

Com base dinâmica e pisos ativados, o motor também calcula:

```text
piso_diario = capital_inicio × (1 − fracao_perda_diaria)
piso_do_pico = pico_patrimonial × (1 − fracao_drawdown)
capacidade = min(patrimonio − piso_diario, patrimonio − piso_do_pico) − risco_reservado
orcamento_da_proposta = min(fracao_por_operacao × patrimonio, capacidade)
```

Capacidade não positiva bloqueia a proposta. O pico precisa vir da conta/histórico conciliado, ser finito e não inferior ao capital inicial nem ao atual. Na configuração de controle, a base proporcional continua limitada ao menor valor entre patrimônio atual e inicial. O painel só fornece contas fictícias para explorar essas fórmulas.

O slippage simétrico usado nos testes é uma aproximação. Um modelo de execução mais realista deve ter distribuições distintas para entrada, alvo, stop, liquidez e zeragem compulsória. O risco de estresse deve ser analisado separadamente do risco planejado.

Com probabilidade validada `p`, ganho líquido médio condicional `G` e perda líquida média condicional `L`, a expressão simplificada `p × G − (1−p) × L` permite estimar valor esperado. Essa fórmula pressupõe que esses termos capturem os resultados e custos relevantes. No sistema entregue, `p` não existe: a confiança do JEV não a substitui.

## 6. Alavancagem agressiva e crescimento

Alavancagem modifica o tamanho dos resultados e a vulnerabilidade da conta; não produz uma vantagem estatística por si só. Para capital pequeno, granularidade de um contrato, margem, spread e custos tornam algumas combinações inviáveis mesmo quando o sinal parece bom.

O motor amplia a quantidade calculada após lucro informado e a reduz quando o orçamento cai, no perfil de capital atual. No desktop, o capital é manual e a conta sem posição é uma hipótese do estudo, sem conciliação com a Toro. O núcleo de risco rejeita estados de conta ausentes, vencidos, não conciliados ou com exposição pendente quando esses campos são fornecidos. Isso permite estudar crescimento entre operações encerradas. Realização parcial, manutenção de posição, stop móvel e adição a posição aberta exigem estados de execução e risco agregado que ainda não existem neste protótipo.

O planejador projeta perdas consecutivas e recalcula a quantidade a cada passo; não estima probabilidade nem futuras oportunidades. Mantém trajetória que respeita a política e diagnóstico que ignora exclusivamente a trava por sequência. A comparação de políticas está em `RISK_MANAGEMENT.md`. Uma camada econômica futura precisará comparar quantidades menores que o teto admissível, considerando distribuição líquida de resultados, liquidez, impacto e incerteza. O máximo admissível é apenas um limite de exposição.

Pirâmide em posição vencedora deve recalcular a perda total caso todos os stops sejam atingidos, o lucro já garantido somente quando houver proteção válida e o risco de gap. Lucro não realizado não deve ser tratado como dinheiro livre sem considerar a posição existente. O protótipo não faz pirâmide, preço médio ou gerenciamento de posição aberta.

Sem meta fixa de lucro, ainda são necessárias regras de saída por invalidação, custo de permanência, horário e risco. Uma tese invalidada deve poder encerrar a avaliação mesmo que o objetivo financeiro do dia não tenha sido alcançado.

## 7. Avaliação do valor do JEV

Crie três versões comparáveis: regras determinísticas, modelo quantitativo apropriado aos dados e a mesma base acrescida dos julgamentos JEV. Mantenha custo, feed, período, execução e conjunto de oportunidades comparáveis. Alterar várias partes simultaneamente impede atribuir um resultado ao JEV.

Avalie separadamente precisão de classificação do contexto, calibração do evento financeiro e desempenho da estratégia completa. Inclua dias negativos, trades rejeitados e intervalos sem operação. A taxa de acerto sozinha não determina lucro; ganhos pequenos e perdas grandes podem produzir prejuízo com maioria de acertos.

Use divisões temporais, controle de vazamento entre janelas sobrepostas e testes fora da amostra. Registre cada tentativa de ajuste para reduzir seleção retrospectiva. Varie custos e slippage; teste latência e indisponibilidade. Métricas de cauda e drawdown devem acompanhar retorno.

“Melhor que qualquer especialista” não é um benchmark definido. Uma hipótese verificável é: superar uma baseline especificada em retorno líquido ajustado ao risco, em períodos não usados para ajuste, com incerteza quantificada. Sem essa definição, o projeto mede ambição em vez de capacidade.

## 8. O que falta implementar

Continuam pendentes: feed integral com sequência verificável, adaptador ProfitDLL licenciado, calendário/notícias, integração e conciliação da conta real, simulador de fila/execução, gestão de posição aberta e avaliação estatística fora da amostra. O coletor Excel, cálculo de medidas, níveis observados, diário e empacotamento Windows foram implementados, mas a coleta na instalação do usuário ainda não foi validada. A chave JEV deve ser informada localmente; nenhuma chamada autenticada foi realizada nesta entrega.

O código entregue deliberadamente sinaliza `research_only`, origem sintética/replay e ausência de probabilidade de lucro. Modificar um JSON para `live` não transforma o laboratório em um serviço de pregão.

## 9. Validade e rastreabilidade na interface

Cada fonte recebe uma geração: respostas de trabalhos anteriores são descartadas quando ela muda. No Excel, a idade do negócio original continua contando durante a inferência; receber uma resposta não renova o evento. Cenários técnicos expiram após dois segundos desde a referência de cotação e são descartados ao editar capital, custos ou demais parâmetros. O diário preserva os registros anteriores como histórico.

Uma perda informada atualiza patrimônio, pico e sequência; perdas que esgotam ou ultrapassam o capital são registradas integralmente e deixam novos cálculos bloqueados. Uma sequência digitada sem horário é uma hipótese explícita de estudo com pausa já transcorrida; uma perda registrada no diário usa seu horário real para a pausa. Nenhuma dessas regras bloqueia operações feitas diretamente no Profit.

## 10. Como a Central chega à conclusão

`build_decision_bundle` produz uma visão comum para a janela e o relatório HTML. `recommendation_engine.py` verifica a fonte e sua idade, a validade dos dados financeiros, a geometria observada e o risco recalculado de cada alternativa. O veto financeiro prevalece sobre qualquer apoio do JEV. Respostas do modelo precisam corresponder à geração, modo, símbolo e geometria; uma análise de fluxo isolada não vira confirmação de entrada.

Os estados são `SEM_DADOS`, `AGUARDAR`, `BLOQUEADO_RISCO` e `HIPOTESE_PARA_REVISAO`. Cobertura parcial mantém a confirmação pendente, mesmo quando existem medidas, geometrias e interpretação do modelo. A hipótese para revisão exige evidência compatível e continua sem ordem ou sinal operacional validado. O motor não contém probabilidade de lucro, seleção por valor esperado ou configuração ótima. Apoio maior que contradição é apenas uma comparação contextual do modelo.

Cada mudança relevante de conclusão é registrada com a origem e geração dos dados, inclusive transições rápidas. A interface preserva as últimas 50 mudanças da execução e o diário mantém os registros persistidos. O botão de exportação gera HTML estático com a mesma conclusão, gráfico amostrado, impedimentos e alternativas. O HTML não recebe dados novos e não é uma captura da janela Windows.

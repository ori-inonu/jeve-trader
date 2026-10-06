# Pesquisa aprofundada: como melhorar as decisões do JEV no WIN

**Data:** 6 de outubro de 2026, referência America/Sao_Paulo.  
**Aplicativo auditado:** JEV WIN v0.3.0.  
**Escopo realizado:** documentação oficial, artigos primários, auditoria do código, demonstrações matemáticas e desenho de experimentos.  
**Estado empírico:** nenhuma chamada autenticada ao JEV, nenhuma amostra nova de mercado, nenhuma ordem e nenhuma estimativa de rentabilidade do WIN nesta pesquisa.

## 1. Conclusão e critério de melhoria

A oportunidade prioritária é construir uma avaliação capaz de mostrar quando o JEV acrescenta informação útil e quando não acrescenta. O código já calcula fluxo e limites financeiros; falta relacionar os julgamentos do modelo a resultados observados posteriormente, com custo, execução e atraso tratados de forma coerente.

A pesquisa também encontrou problemas concretos de especificação: a interface descarta a premissa do cenário antes de perguntar sobre ela; a pergunta dinâmica de contradição mistura observação contrária com falta de dados; e a revisão contextual não utiliza a resposta de insuficiência de evidência. Esses achados podem ser investigados sem esperar um backtest de rentabilidade.

O objetivo operacional proposto é **melhorar a qualidade das decisões após custos e atrasos, respeitando limites explícitos de perda e admitindo não operar**. A quantidade máxima que cabe na margem continua sendo uma restrição. Para escolher uma quantidade por benefício econômico é necessário estimar resultados e incerteza, algo ainda ausente no aplicativo.

Neste documento:

- **Fato de código** significa comportamento inspecionado nos fontes v0.3.0.
- **Fato de documentação** significa capacidade ou restrição declarada por uma fonte primária, sujeita à versão e ao escopo dessa fonte.
- **Resultado publicado** significa achado de um estudo no mercado e desenho investigados pelos autores.
- **Proposta** significa uma alteração ou experiência ainda sem validação no WIN.
- **Demonstração matemática** usa parâmetros hipotéticos explicitamente assumidos; não descreve desempenho de mercado.

## 2. Auditoria: as oportunidades mais concretas

### 2.1 A premissa existe, mas é retirada antes da consulta

**Fato de código.** `candidate_engine.py`, linha 62, cria `premise`. `candidate_research.py`, linha 196, a conserva na linha do cenário. `desktop_app.py`, linha 603, seleciona apenas `id`, `side`, entrada, stop, alvo e níveis de referência para o estado enviado ao modelo. A pergunta seguinte pede apoio à hipótese técnica, sem transportar sua formulação.

O script `reproduce_examples.py` lê a expressão real do arquivo auditado, extrai suas chaves por AST e reproduz a projeção: `premise` está presente antes e ausente depois. Isso demonstra a perda do campo, sem afirmar como o JEV responderia a uma chamada real.

**Inferência.** O modelo pode reconstruir uma hipótese a partir do lado, nome do candidato ou geometria, em vez de julgar a proposição desejada.

**Proposta E02.** Transportar a premissa explícita e comparar três braços: payload atual; premissa preservada; famílias de hipóteses separadas. A premissa atual contém uma disjunção: continuidade de um lado **ou** absorção da agressão oposta. Preservar o campo, sozinho, não resolve essa mistura.

Cada família deve ter descrição do contexto observado, condição de confirmação, invalidação e horizonte. Uma hipótese de absorção observada não deve implicar automaticamente uma entrada de reversão. A orientação da TypeSafe é compor julgamentos estreitos e literais, mantendo cálculos e fluxo de controle no código. [S01][S02]

### 2.2 Apoio, contradição e informação insuficiente são dimensões distintas

**Fato de código.** A pergunta dinâmica em `desktop_app.py`, linha 605, inclui falta de cobertura decisiva como algo a considerar ao julgar contradição. O arquivo `questions.json` distingue esses conceitos, mas não é o conjunto carregado por esse caminho da interface: a UI lê `observer_questions.json` e acrescenta perguntas dinamicamente.

**Proposta E02/E03.** Separar:

1. Os fatos observados apoiam a premissa explícita?
2. Existe observação que contradiz diretamente essa premissa?
3. Há informação suficiente para distinguir a premissa da explicação alternativa relevante?

É possível haver pouco apoio e pouca contradição porque faltam dados. Também é possível haver apoio e contradição fortes porque o estado é misto. Não forçar as duas probabilidades a somar um nem subtrair/multiplicar respostas para fabricar uma probabilidade financeira.

O pacote inclui `proposed_questions.json`, um rascunho de três perguntas independentes. Ele não é uma configuração instalada nem contém limiar de entrada. As verificações determinísticas de qualidade e risco permanecem externas ao JEV.

### 2.3 A composição da revisão precisa ser avaliada

**Fato de código.** `recommendation_engine.py`, linha 302, usa apoio maior que contradição como uma condição de hipótese para revisão. O motor preserva a confiança da classificação, mas não a utiliza como gate; tampouco usa o Noul `evidence_insufficient` na composição dessa decisão. Uma diferença pequena entre apoio e contradição pode satisfazer a desigualdade quando as outras condições passam.

Isso não envia ordem: `actionable_live_signal` continua falso, e os bloqueios financeiros, de idade e cobertura permanecem. A questão de pesquisa é se a etiqueta visual de revisão representa sustentação suficiente para o usuário, especialmente diante de respostas do modelo que discordam entre si.

**Proposta E03.** Medir consistência e curvas de erro versus cobertura para diferentes seletores. Não fixar agora um número como 0,65 ou 0,80 por aparência de rigor. O erro aceitável depende do evento avaliado, dos custos e dos dados de validação.

### 2.4 Viés de ordem e nomes das alternativas

**Fato de documentação.** A TypeSafe reconhece que a ordem de opções `Choice` pode influenciar o Jev 1.13, com inclinação para a primeira opção. Também relata dificuldades com literalidade, matemática e estado irrelevante. A página foi revisada em 02/10/2026. [S02]

**Fato de código.** A primeira opção de `flow_context` é sempre `buy_progression`. Isso não demonstra viés comprador nas respostas reais deste aplicativo; identifica um teste necessário.

**Proposta E04.** Balancear a posição das opções, permutar a ordem dos candidatos com mapeamento reversível, comparar nomes equivalentes e testar espelhamento compra/venda em casos sintéticos simétricos. Medir troca de classe e variação da distribuição. Usar repetições para distinguir sensibilidade sistemática de variação de resposta. Não criar um comitê de chamadas correlacionadas e tratar seus votos como evidência independente.

### 2.5 O diário não é ainda um dataset experimental completo

**Fato de código.** `desktop_app.py`, linha 619, registra estado, resposta e latência. O caminho não persiste as perguntas dinâmicas exatas e todos os hashes/versões necessários para reconstituir o experimento. `app_store.py`, linha 75, mantém somente os últimos 10 mil eventos, considerando todos os tipos.

**Proposta.** Criar um registro experimental separado do diário visual, com: estado efetivamente disponível; perguntas exatas e sua ordem; resposta validada; versão resolvida do modelo; versões de features, hipótese e composição; hashes; origem e relógios; custo da consulta; resultado posterior e seu método de apuração. Não incluir chaves ou credenciais. Falha de feed, falha de API, interpretação e decisão devem ter categorias diferentes.

## 3. Qual deve ser o papel do JEV

As primitivas têm semânticas diferentes. Noul representa a probabilidade de uma proposição ser verdadeira segundo o modelo; Choice distribui probabilidade sobre alternativas; confidence resume concentração dessa distribuição. Nenhuma delas, por seu tipo, é uma frequência de operações lucrativas no WIN. [S03]

A organização proposta tem três níveis:

| Nível | Pergunta | Responsabilidade |
|---|---|---|
| Observação e contexto | O que os dados disponíveis sustentam? | Medidas determinísticas e julgamentos contextuais JEV. |
| Previsão do desfecho | O que aconteceu depois em situações comparáveis, neste horizonte e geometria? | Modelo supervisionado de resultados, avaliado e calibrado em dados separados. |
| Decisão e tamanho | A alternativa oferece benefício líquido compatível com a incerteza e os limites? | Comparação econômica e motor determinístico de risco, incluindo esperar. |

Transformar um Noul contextual em probabilidade de alvo não é apenas uma troca de rótulo. A camada de desfecho precisa aprender uma relação com resultados financeiros definidos. Depois, a calibração dessa previsão deve ser avaliada fora do material usado para ajustar o modelo. O alvo, stop, horizonte, custo e condição de execução fazem parte desse problema.

A TypeSafe apresenta um padrão em que julgamentos JEV viram variáveis de um modelo supervisionado posterior. Seu exemplo público usa avaliações de vinhos; ele demonstra o padrão técnico, não vantagem no WIN. [S04]

**Proposta E07.** Comparar, sob a mesma informação e oportunidades:

- A: regras determinísticas atuais, com seus filtros de qualidade.
- B: modelo quantitativo básico usando preço, spread e features de fluxo disponíveis.
- C: o mesmo modelo B, acrescido das respostas do JEV.
- D: uma variante que consulta JEV somente em ambiguidades definidas previamente.

O comparador relevante de C é B. Se a melhora desaparecer ao incluir custo, atraso e seleção das oportunidades, não há base para atribuir ganho econômico ao JEV. Resultado negativo é útil: indica perguntas ou componentes a remover.

## 4. Dados de fluxo: o que vale melhorar antes de ampliar as hipóteses

### 4.1 RTD é uma possibilidade real, com contrato incompleto para este caso

**Fato de documentação.** A Nelogica menciona exportação RTD vinculada a janelas Times & Trades/Livro, identificador de ferramenta, aba ativa e intervalo permitido do parâmetro de linha. Logo, não é correto afirmar que esse tipo de vínculo não existe. As páginas examinadas não estabeleceram a assinatura completa necessária ao nosso adaptador, retenção, ID estável de cada execução e recuperação íntegra de eventos. [S05]

O catálogo distingue último negócio, cotação e atributos acumulados. Quantidade do último negócio não reconstitui a lista de negócios ocorridos entre consultas. [S06]

**Proposta E01.** Registrar o contrato real gerado pelo Profit: janela/aba, filtros, campos, ID, horários, forma de atualização e comportamento quando a tabela enche. Comparar a captura com uma referência reconciliável do mesmo contrato, período e unidade. Se o denominador confiável não existe, cobertura quantitativa permanece desconhecida.

### 4.2 A visualização pode mudar a unidade estatística

**Fato de documentação.** A aba Negócios discrimina execuções; Ordem Original agrupa pela ordem originalmente encaminhada. A ferramenta também admite filtros e seleção de período. [S07]

**Implicação.** Frequência de execuções e frequência de ordens agrupadas não são a mesma variável. Misturar essas representações pode produzir uma falsa aceleração/desaceleração. O perfil da fonte deve acompanhar cada observação e os dados históricos precisam conservar essa configuração.

### 4.3 Duplicata, correção e sequência não são equivalentes

**Fato de código.** `SeenTradeIds`, em `profit_bridge.py`, linha 103, deduplica por chave. Uma fonte que reapresente uma edição com o mesmo ID precisará de tratamento distinto antes dessa deduplicação. No parser atual, `sequence_ok` deriva da ordem dos timestamps; isso não prova ausência de eventos perdidos no feed.

**Fato de documentação.** A DLL documenta tipos de negócio e identificador sequencial da sessão; também diferencia canais de negócios, topo, profundidade e ofertas individuais. Essa documentação não permite presumir incremento contíguo de +1 por ativo sem confirmar o escopo do identificador. [S08][S09]

**Proposta E01.** Preservar tipo do evento, referência de edição, sessão, origem da agressão, instante de recebimento e informação de perda/recuperação. Testar duplicata idêntica, correção, empate de horário, reconexão, reset de sessão e overflow. Distinguir ordem temporal verificada de continuidade não verificada. Excluir ou tratar separadamente leilão e tipos que não sustentam interpretação de agressão contínua.

### 4.4 Topo, profundidade e ofertas individuais sustentam análises diferentes

A documentação Nelogica separa profundidade agregada por preço de ofertas individuais. O PriceDepth tem eventos de atualização completa, início/fim de lote e preço teórico de leilão. [S08][S10]

**Proposta.** Usar capacidades declaradas pela fonte: cotação amostrada, tape parcial, tape reconciliado, profundidade ou oferta individual. Cada feature declara seus requisitos. A ausência de uma capacidade torna aquela feature indisponível. Captura por DLL também requer controle de filas, latência e recuperação; licença não demonstra integridade do consumidor.

A integração da conta é outro requisito antes de recomendações operacionais: patrimônio, margem livre, posição, ordens pendentes e custos precisam estar conciliados. O estudo manual atual não conhece automaticamente mudanças ocorridas diretamente no Profit.

## 5. Microestrutura: quatro linhas de pesquisa justificadas

Os trabalhos abaixo justificam investigar variáveis; não comprovam que a implementação atual gera lucro.

| Linha | Evidência primária | Experimento proposto e limitação |
|---|---|---|
| OFI: desequilíbrio dos eventos no livro | Cont, Kukanov e Stoikov estudam ordens limite, negócios e cancelamentos em 50 ações dos EUA. [S11] | Acrescentar OFI quando a fonte suporta eventos adequados. Delta executado do aplicativo não é OFI. Avaliar previsão posterior à decisão. |
| Desequilíbrio do topo | Gould e Bonart encontram poder preditivo para o próximo movimento do preço médio em dez ações Nasdaq, com diferenças por estrutura de tick. [S12] | Comparar contra preço/spread e medir se o horizonte ainda é utilizável depois do atraso local. |
| Vários níveis do livro | Xu, Gould e Howison estudam MLOFI em seis ações Nasdaq e ajuste da mudança contemporânea do preço médio. [S13] | Fixar níveis/faixa e regularizar. Ajuste contemporâneo fora da amostra não é backtest de previsão negociável. |
| Execução dependente do estado | Huang, Lehalle e Rosenbaum modelam intensidades de eventos condicionadas ao estado do livro. [S14] | Separar previsão direcional de fila, preenchimento e custo. Não reconstruir posição exata na fila a partir de snapshots insuficientes. |

### Episódios localizados de progressão, absorção e exaustão

**Fato de código.** O motor atual usa volumes e deslocamento first-to-last em janelas curtas. Seus limiares são explicitamente experimentais. O book imbalance soma níveis presentes; alterar a profundidade disponível muda a medida.

**Propostas E08:**

- **Progressão:** investigar agressão do mesmo lado acompanhada por deslocamento e aceitação observável além de uma referência. Diferenciar consumo de liquidez de mera coincidência entre volume e preço.
- **Absorção possível:** localizar volume agressor numa faixa de preço, pouco avanço e reposição observável. Testar explicações alternativas, como fluxo oposto e agregação temporal. Sem evidência apropriada, não atribuir iceberg ou identidade/intenção a um participante.
- **Exaustão possível:** comparar desaceleração depois de avanço com a atividade anterior e o regime. Uma pausa sem reação oposta ainda pode preceder continuação. Falha de captura também pode aparentar desaparecimento de agressão.
- **Liquidez e impacto:** padronizar profundidade, spread e distância em ticks; estudar custos condicionados à quantidade e ao estado observado.

Normalização por horário/atividade deve usar somente o passado disponível. Se um limiar é escolhido olhando o dia inteiro, seu uso nas primeiras horas daquele dia vaza futuro. Delta, dominância e saldo agressor são relacionados: três variáveis derivadas do mesmo fluxo não equivalem a três confirmações independentes.

Começar com poucos incrementos sobre uma base simples. Cada feature precisa demonstrar contribuição fora da amostra; retirar as que apenas aumentam complexidade. Contratos e rolagens devem ser identificados explicitamente, com resets de sessão e sem misturar preços de série contínua ajustada ao tape executável.

## 6. Uma conclusão pode estar correta e chegar tarde

**Fatos de código auditados:** polling Excel de aproximadamente 2 s; intervalo automático JEV mínimo de 10 s; timeout da chamada de 3 s; validade contextual de 2 s desde a origem. O aplicativo invalida respostas antigas. Esses números são configuração, não latência medida no computador do usuário.

**Demonstração:** origem já com 1.900 ms de idade + 300 ms de consulta = 2.200 ms. Mesmo uma consulta de 300 ms chegaria vencida sob a regra atual. Nenhum desses tempos do exemplo foi medido remotamente.

**Proposta E05.** Medir o percurso completo: evento na fonte; recebimento; processamento; submissão; resposta; exibição; confirmação humana, se mensurável. Separar duração HTTP da idade do dado. Relatar p50/p95/p99, fila, perda, clock skew e fração de respostas ainda utilizáveis. Idade do último negócio não substitui heartbeat/conexão verificada.

O horizonte da previsão e a validade do cenário precisam ser coerentes com esse percurso. Aumentar o TTL para acomodar respostas lentas não comprova que a informação conserva valor. Consultar mais rápido sem dados novos apenas aumenta custo.

O aplicativo já agrupa sete perguntas gerais e duas por candidato: até 23 numa chamada. O cookbook de batching do fornecedor usa outro modelo e domínio, com cinco repetições e comparação contra soma serial; não fornece SLA de WIN ou latência do nosso ambiente. [S15]

Testar gatilhos por mudança material de evidência, agrupamento e JEV seletivo em ambiguidades. Cache em replay deve usar estado, perguntas e versões; em mercado acompanhado, cache nunca renova a idade da evidência. Medir custo por avaliação útil e benefício incremental, não apenas tokens por resposta.

## 7. Definir o resultado antes de avaliar a previsão

**Proposta E06.** Congelar candidato, geometria, horizonte, regra de entrada, regra de saída, estado disponível e relógios. Depois apurar:

| Desfecho | Definição experimental |
|---|---|
| Não entrou | A proposta não foi preenchida dentro da validade. |
| Saída por alvo | Entrada e saída por alvo foram preenchidas conforme o modelo de execução. |
| Saída por stop | Entrada e saída de proteção foram preenchidas, incluindo desvio de preço. |
| Saída por tempo | A regra determina encerrar no horizonte, a preço/custo identificável. |
| Saída de sessão/forçada | Aplica-se uma regra previamente especificada. |
| Dados irresolúveis | A fonte não permite determinar a ordem ou o resultado. |

Toque de preço e execução são dois objetos. Uma barra com alvo e stop na mesma janela não informa qual veio primeiro; uma amostra RTD também não resolve tudo que aconteceu entre leituras. Marcar ambiguidade ou apresentar limites sob pressupostos explícitos. Nunca escolher a sequência favorável depois de olhar o resultado.

Um timeout com saída observada é um resultado econômico; perda de feed é ausência de observação. Não descartar ambos como se fossem a mesma coisa. Stop e alvo competem pelo primeiro evento: a probabilidade desejada depende de geometria e horizonte, e não apenas da direção.

A execução simulada deve respeitar a disponibilidade temporal: não preencher uma oferta em cotação anterior à chegada. Custos de entrada, alvo, stop e zeragem podem diferir. Profundidade, quantidade, fila, rota e tipo de oferta condicionam preenchimento; validar as regras efetivamente utilizadas antes de construir um simulador específico. A literatura de modelos do livro distingue esse problema da previsão de direção. [S14]

Se retornos já são líquidos de fills e custos, não descontar spread/slippage novamente. Comparar cenários ideal, plausível e adverso predefinidos. Um resultado que depende de execução ideal permanece hipótese não validada.

## 8. Como demonstrar valor incremental sem enganar o experimento

### 8.1 Separação temporal e previsões que amadurecem depois

**Proposta E07/E09.** Separar treino, escolha/calibração e teste futuro intocado. Transformações, normalizações, descoberta de features, prompts e seletores devem usar apenas os períodos autorizados de desenvolvimento. O resultado futuro precisa estar maduro antes de entrar no treino.

Exemplo com evidência `[t-L,t]` e resultado até `t+H`: se o treino fecha em T, uma observação anterior a T cujo resultado só aparece depois de T não está disponível para treinamento naquele corte. Purga deve remover esses casos. Em walk-forward estritamente para frente, um embargo posterior ao teste pode ser irrelevante se nenhuma observação posterior entra no treino daquele fold; exclusões devem decorrer dos intervalos efetivos e do desenho, não de um percentual arbitrário.

Oito candidatos derivados do mesmo instante compartilham a trajetória seguinte. Não são oito observações independentes. Agrupar por oportunidade e usar blocos de sessão ao quantificar incerteza; explicitar a limitação de poucos pregões. Uma política com posição aberta também não pode executar todas as oportunidades sobrepostas como se o capital estivesse sempre livre.

### 8.2 Medidas distintas para perguntas distintas

Para previsão probabilística de um evento definido, usar Brier/log loss e curvas de confiabilidade com contagem e incerteza; essas medidas avaliam distribuição contra resultado. [S16]

Acrescentar:

- Resultado líquido por oportunidade e por tempo, incluindo períodos sem operar.
- Taxas de não entrada, timeout e ambiguidade.
- Ganho incremental pareado entre B e C, com os mesmos custos e limites.
- Cobertura de dados, cobertura do seletor e motivos de rejeição.
- Drawdown e perdas extremas por sessão, duração sob o pico e custos de API/dados atribuíveis.

Uma previsão constante pode ser bem calibrada e pouco informativa. Uma boa acurácia de contexto também pode não produzir benefício econômico. O resultado principal deve demonstrar utilidade adicional e estabilidade; métricas auxiliares explicam o mecanismo.

### 8.3 Abstenção também tem custo

A literatura de classificação seletiva estuda a troca entre erro e cobertura. Seus resultados em classificação de imagens justificam estudar essa troca; não estabelecem garantia financeira. [S17]

**Proposta E03.** Separar cobertura do feed da fração de oportunidades aceitas. Mostrar o resultado dos rejeitados em replay sob o mesmo modelo de execução, identificado como contrafactual. Um seletor que quase nunca aceita pode parecer preciso sem ser útil. Não escolher seu limiar no teste externo.

### 8.4 A busca por melhorias pode sobreajustar a própria avaliação

Registrar todas as tentativas: prompts, ordem, thresholds, features, horizontes, políticas e experiências descartadas. A literatura de PBO e Deflated Sharpe trata seleção entre muitas alternativas e inflação de desempenho aparente. São diagnósticos complementares, com pressupostos; não corrigem um feed incompleto ou uma execução fictícia. [S18][S19]

Usar critérios de passagem pré-especificados e um bloco final que não participa da seleção. Não declarar evidência por atingir um número arbitrário de decisões. A quantidade necessária depende da precisão buscada, do efeito, da dependência temporal e da diversidade de regimes.

### 8.5 Adaptação e memória

**Proposta posterior.** Manter memória de episódios e resultados com versões e horários de disponibilidade. Buscar casos passados comparáveis somente quando sua informação já existia; medir se essa recuperação acrescenta algo ao modelo básico. Atualização deve ser versionada e comparada com uma versão estável, permitindo retorno à anterior.

Conformal adaptativo pode ser investigado para incerteza sob mudança de distribuição. Cobertura ao longo do tempo não é probabilidade individual de lucro nem proteção da conta, e falhas podem se concentrar em regimes desfavoráveis. [S20] A prioridade continua sendo obter desfechos identificáveis e testar modelos simples.

## 9. Alavancagem: distinguir teto, benefício e crescimento

O motor atual responde: qual lote inteiro cabe no orçamento e na margem sob a perda planejada? O problema econômico é diferente: entre esperar e as quantidades admissíveis, qual alternativa oferece utilidade líquida compatível com sua incerteza e os limites de trajetória?

**Proposta E10.** Somente depois de validar dados, execução e previsão, comparar `q=0`, lotes menores e o teto. Incluir margem, exposição já comprometida, custo dependente de quantidade, queda do pico e possibilidade de não conseguir operar o tamanho mínimo. A tolerância financeira precisa ser explícita; a palavra agressivo não a determina.

### 9.1 Maior relação ganho/perda pode ter pior expectativa

No exemplo binário, com ganho e perda já líquidos, `EV=pG-(1-p)L`. Os valores de p abaixo são assumidos apenas para demonstração, sem dados WIN, timeout ou falha de entrada.

| Alternativa hipotética | Ganho líquido | Perda líquida | Relação G/L | p assumido | EV por tentativa |
|---|---:|---:|---:|---:|---:|
| A | R$58 | R$22 | 2,64 | 25% | −R$2 |
| B | R$38 | R$22 | 1,73 | 45% | +R$5 |

A tem maior relação ganho/perda e expectativa negativa sob suas hipóteses. B tem relação menor e expectativa positiva. Sem estimar o evento financeiro, escolher pelo alvo mais distante ou pelo maior apoio contextual é insuficiente.

### 9.2 Mais retorno aritmético pode reduzir crescimento composto

Outro exemplo puramente matemático assume G=38, L=22 e p=40%, tentativas IID, entrada certa e ausência de margem, granularidade, impacto, gaps e timeout. Se f é a fração do patrimônio perdida no stop, então:

`g(f)=0,4 ln(1+(38/22)f)+0,6 ln(1-f)`.

| f hipotético | Retorno aritmético esperado por passo | Crescimento log esperado por passo |
|---|---:|---:|
| 1% | 0,0909% | 0,00081990 |
| 5% | 0,4545% | 0,00235843 |
| 10% | 0,9091% | 0,00051651 |
| 15% | 1,3636% | −0,00535537 |

O retorno aritmético aumenta com f, mas o crescimento log torna-se negativo no último caso. A fração ótima desse brinquedo binário seria aproximadamente 5,263%; ela **não é recomendação para o aplicativo ou para uma conta de R$400**. A probabilidade foi inventada como hipótese didática, não estimada.

Kelly com restrições de drawdown é uma linha de pesquisa, mas depende de distribuição e pressupostos como os explicitados no paper de Busseti, Ryu e Boyd. Suas garantias não passam automaticamente a futuros com perdas além da reserva e distribuição desconhecida. [S21]

Recuperar R$20 não cria evidência direcional. Se o retorno líquido condicional por unidade é não positivo, aumentar uma quantidade não negativa escolhida com a informação passada não muda seu sinal esperado sob horizonte finito e integrabilidade. A recuperação pode ser resultado de decisões futuras; não serve como argumento de mercado.

## 10. Como a interface deveria tornar a decisão verificável

**Proposta de evolução visual:**

| Camada exibida | Exemplo de conteúdo |
|---|---|
| Observado | Fonte, contrato, horário, negócios capturados, bid/ask e cobertura. |
| Calculado | Delta, deslocamento, spread, intensidade e custo estimado. |
| Inferido pelo JEV | Premissa avaliada, apoio, contradição e explicação alternativa não resolvida. |
| Estimado por resultados | Probabilidade/intervalo do evento, somente depois de validação supervisionada. |
| Decisão permitida | Esperar ou revisar um cenário; motivo de veto, validade e quantidade admissível. |

Acrescentar comparação com a base sem JEV, motivo pelo qual a resposta mudou a seleção e identificação das informações que fariam a hipótese deixar de valer. Explicações textuais devem ser montadas a partir dessas evidências e regras; não inventar acesso ao raciocínio interno do modelo.

Quando não houver estimativa financeira validada, a interface deve dizer isso explicitamente. Uma cor forte, uma pontuação decimal ou uma frase confiante não deve preencher essa lacuna.

## 11. Plano priorizado de experimentos

O JSON acompanhante detalha dependências, braços, métricas e critérios. Todos os experimentos empíricos constam como propostos, ainda não executados.

| ID | Prioridade | Entrega verificável | Condição para avançar |
|---|---|---|---|
| E01 | P0 | Contrato da fonte, eventos/correções e reconciliação | Saber o que foi recebido, perdido e permanece desconhecido. |
| E02 | P0 | Premissa explícita, famílias e dimensões separadas | Perguntas correspondem à proposição pretendida; casos de ausência e contradição distintos. |
| E05 | P0 | Relógios e orçamento de tempo útil | Medir atraso total e utilidade remanescente por horizonte. |
| E06 | P0 | Apuração de resultados e execução causal | Resultados reproduzíveis, ambiguidades visíveis, custos coerentes. |
| E03 | P1 | Seletores de abstenção | Melhorar a troca entre erro/cobertura sem ocultar inatividade. |
| E04 | P1 | Testes de ordem, nomes e simetria | Identificar sensibilidade que não decorre de mudança de evidência. |
| E07 | P1 | Regras, quantitativo e quantitativo+JEV | Benefício incremental em períodos futuros, após custos e atrasos. |
| E08 | P2 | Features e episódios localizados | Contribuição adicional estável, com dados adequados. |
| E09 | P2 | Calibração, versões e regimes | Erros e mudanças mensurados; atualização sem resultados futuros. |
| E10 | P3 | Quantidade condicionada à vantagem | Comparar tamanhos e esperar com conta conciliada e limites explícitos. |

P0 indica fundamento para uma avaliação válida, não promessa de lucro. P1 mede o papel do modelo. P2 refina apenas o que já mostrou utilidade. P3 trata alavancagem dependente de vantagem; não deve compensar ausência das etapas anteriores.

## 12. Entrega, reprodução e limites

O pacote de pesquisa contém este relatório, `Plano_Experimentos_JEV.json`, rascunho de perguntas, script de reprodução, resultados JSON, notas de fontes e cópias dos arquivos auditados com hashes. Execute `python reproduce_examples.py` na pasta extraída para reproduzir a projeção sem premissa e os exemplos matemáticos. O script não consulta modelos nem mercado.

Foram verificados: expressão real de projeção do candidato, primeiro critério do Choice, contagem máxima de perguntas, contas de expectativa e crescimento, e o exemplo de vencimento por atraso. Esses checks não são testes de rentabilidade, de acurácia JEV ou da interface Windows. As 166 verificações da versão anterior continuam sendo testes de software; não são 166 operações observadas.

**Estado da aplicação:** o executável permanece na v0.3.0. As mudanças descritas são propostas de pesquisa; nenhum threshold, parâmetro de risco ou comportamento de produção foi alterado nesta etapa. A assinatura específica do RTD de negócios, condições efetivas de acesso, conta real, dados completos e desempenho continuam pendentes de verificação no ambiente correspondente.

## Fontes primárias

| ID | Fonte | Escopo utilizado |
|---|---|---|
| S01 | [Skill oficial TypeSafe][S01] | Composição de julgamentos, premissas e responsabilidade do código. |
| S02 | [Jev 1.13 jaggedness][S02] | Falhas reconhecidas, revisão em 02/10/2026. |
| S03 | [TypeSafe Confidence][S03] | Probabilidades das respostas e concentração. |
| S04 | [Autoresearch feature discovery][S04] | Julgamentos como features; exemplo fora de finanças. |
| S05 | [Nelogica — configurar RTD/DDE][S05] | Exportação e vínculos a janelas. |
| S06 | [Nelogica — sintaxe RTD][S06] | Significado dos atributos. |
| S07 | [Nelogica — Times & Trades][S07] | Negócios, Ordem Original e filtros. |
| S08 | [Nelogica — funções Real Time DLL][S08] | Tipos de feed e callbacks. |
| S09 | [Nelogica — trades históricos][S09] | Identificação, tipos e callbacks de negócios. |
| S10 | [Nelogica — PriceDepth][S10] | Profundidade, lotes e leilão. |
| S11 | [Cont, Kukanov e Stoikov][S11] | OFI em ações americanas. |
| S12 | [Gould e Bonart][S12] | Desequilíbrio e próximo movimento do mid. |
| S13 | [Xu, Gould e Howison][S13] | MLOFI e ajuste contemporâneo. |
| S14 | [Huang, Lehalle e Rosenbaum][S14] | Modelo de eventos e execução do livro. |
| S15 | [TypeSafe — parallel questions][S15] | Batching; benchmark restrito ao seu desenho. |
| S16 | [Gneiting e Raftery][S16] | Avaliação de previsões probabilísticas. |
| S17 | [Geifman e El-Yaniv][S17] | Classificação seletiva e cobertura. |
| S18 | [Bailey et al. — PBO][S18] | Seleção e sobreajuste de backtests. |
| S19 | [Bailey e López de Prado — DSR][S19] | Inflação de Sharpe por seleção e não normalidade. |
| S20 | [Gibbs e Candès — ACI][S20] | Incerteza sob mudança de distribuição. |
| S21 | [Busseti, Ryu e Boyd][S21] | Kelly com restrição de risco e pressupostos. |

[S01]: https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md
[S02]: https://docs.typesafe.ai/model-jaggedness/jev-1.13
[S03]: https://docs.typesafe.ai/confidence
[S04]: https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery
[S05]: https://ajuda.nelogica.com.br/hc/pt-br/articles/360044293432-Como-configurar-RTD-DDE-no-Profit
[S06]: https://ajuda.nelogica.com.br/hc/pt-br/articles/7834206674075-Significados-e-sintaxe-do-RTD
[S07]: https://ajuda.nelogica.com.br/hc/pt-br/articles/360054569632-Times-Trades
[S08]: https://ajuda.nelogica.com.br/hc/pt-br/articles/11168755650459-Fun%C3%A7%C3%B5es-Real-Time-DLL
[S09]: https://ajuda.nelogica.com.br/hc/pt-br/articles/11973319153563-Como-requisitar-trades-hist%C3%B3ricos-com-a-ProfitDLL
[S10]: https://ajuda.nelogica.com.br/hc/pt-br/articles/50587290263835-Como-utilizar-o-Livro-de-Profundidade-Price-Depth-via-DLL-Real-Time
[S11]: https://arxiv.org/abs/1011.6402
[S12]: https://arxiv.org/abs/1512.03492
[S13]: https://arxiv.org/abs/1907.06230
[S14]: https://arxiv.org/abs/1312.0563
[S15]: https://docs.typesafe.ai/cookbooks/parallel_questions
[S16]: https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf
[S17]: https://papers.neurips.cc/paper_files/paper/2017/file/4a8423d5e91fda00bb7e46540e2b0cf1-Paper.pdf
[S18]: https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf
[S19]: https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf
[S20]: https://arxiv.org/abs/2106.00170
[S21]: https://arxiv.org/pdf/1603.06183

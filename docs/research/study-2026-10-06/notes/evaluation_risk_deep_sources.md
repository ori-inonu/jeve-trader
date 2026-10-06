# Avaliação de decisões e risco econômico — pesquisa JEV/WIN v0.3.0

Data: 2026-10-06. Escopo: leitura de código e fontes primárias, sem mudança de produção, contas, ordens ou parâmetros. Esta nota é insumo de pesquisa para o relatório principal. As experiências abaixo ainda não foram executadas em dados de mercado.

## Conclusão e prioridades

O sistema calcula admissibilidade contábil e interpreta evidência contextual; ainda não mede uma vantagem econômica. A melhoria de maior valor é construir uma avaliação que possa descobrir **ausência** de vantagem do JEV. Mais alternativas de stop/alvo, maior fração ou uma interpretação mais convincente não resolvem a falta de resultados identificáveis, execução simulada e teste temporal independente. O limite financeiro deve continuar externo ao modelo.

Prioridade recomendada, como julgamento de engenharia:

1. Definição operacional de resultado, coleta temporal e replay sem vazamento.
2. Modelo de execução e custos condicionais compatível com a resolução dos dados.
3. Comparação pareada de regras, modelo quantitativo e modelo acrescido do JEV; abstenção e calibração fora da amostra.
4. Registro de todas as tentativas e controle de seleção; distribuição de retorno líquido e risco de trajetória.
5. Somente após evidência de vantagem: pesquisa de quantidade menor que o teto, Kelly robusto/fracionado e restrições de cauda. Não escolher percentuais atuais pelo número de stops suportados.

## 1. O que o código já demonstra e o que não demonstra

Referências de código relativas à raiz `/workspace/scratch/e769fda15fc1/jev_profit_copilot`:

| Evidência local | Fato observado | Implicação para a pesquisa |
|---|---|---|
| `recommendation_engine.py:73–77,144–156` | Confiança e apoio são descritivos; `win_probability`, ranking, retorno esperado e configuração ótima permanecem ausentes. | Preservar isso até calibrar resultados econômicos. Não renomear apoio contextual para probabilidade. |
| `recommendation_engine.py:293–304` | Apoio maior que contradição é uma condição de revisão, com `scores_calibrated_on_WIN=False`. | A regra ainda precisa ser comparada com nenhuma seleção e com uma base sem JEV. Diferença dos dois scores não é odds, probabilidade ou medida calibrada de incerteza. |
| `recommendation_engine.py:182–205,241–262` | Veto por idade/qualidade, checagem de referências e entrada no bid/ask corrente. | Admissão no instante observado é diferente de preço executável após inferência e reação humana. |
| `risk.py:174–198,230–239` | Quantidade decorre de orçamento, margem e teto; custos e slippage são escalares por contrato. | Resultado é máximo admissível sob hipótese de perda planejada, não ótimo de crescimento; impacto/latência/custos de stop não dependem do lote ou regime. |
| `risk_research.py:11–12,51–81` | Dez políticas usam mesma geometria e custos, sem ranking ou previsão. | Comparação determinística é válida para contabilidade; não estima desempenho, risco probabilístico ou preferência econômica. |
| `capital_planner.py:93–147` | Aplica sempre a perda unitária planejada, recalcula conta/lote e avança relógio pelo cooldown. | Não há duração aleatória, novas oportunidades, ganhos, gaps ou distribuição de preenchimento. Contar tentativas até trava não é calcular probabilidade de ruína. |
| `capital_planner.py:20–28` | Limitações de gaps, liquidez, zeragem e tempo já são explícitas. | Lacuna reconhecida, não defeito oculto que deva ser corrigido mudando parâmetros agora. |
| `stress_lab.py:10–26` | Grade fixa de adversidades e tarifas hipotéticas, sem probabilidade. | Dá exposição a cenários definidos; não autoriza afirmar percentil de perda ou estresse máximo. |
| `questions.json:3–26` | Perguntas definem interpretação atual e apoio/contradição de premissa. | Ground truth de contexto e ground truth financeiro são objetos distintos. Perguntas não pedem previsão de lucro. |
| `DECISION_DESIGN.md:44–48,103–117` | Janelas de 5/5/30 segundos; avaliação temporal e execução estão pendentes. | Repetir decisões por segundo pode criar milhares de linhas fortemente correlacionadas. Número de decisões não é número de experimentos independentes. |

## 2. Labels: especificar o evento antes de avaliar o modelo

**Proposta de desenho experimental**, derivada do objetivo e das limitações locais, não um padrão que prove rentabilidade:

Para cada oportunidade, congelar decisão, versão do gerador de candidatos e geometria no instante `t_decision`. Guardar `t_source`, instante de disponibilidade para o programa, término da inferência, reação humana hipotética e chegada hipotética da oferta ao ambiente de execução. Reconstituir apenas o prefixo de eventos disponível naquele instante. Eventos posteriores pertencem exclusivamente à apuração.

Separar os estados:

- `not_entered`: proposta nunca executada dentro da validade; inclui fila, expiração, rejeição e falta de liquidez.
- `target_exit`: entrada confirmada e saída por alvo efetivamente preenchida.
- `stop_exit`: entrada confirmada e saída por stop efetivamente preenchida, potencialmente fora do disparo.
- `timeout_exit`: posição encerrada por horizonte temporal fixado anteriormente, com preço/custo executável.
- `forced_or_session_exit`: leilão, término de sessão, zeragem ou outra regra previamente definida.
- `unresolved_data`: ordem temporal, sequência ou continuidade insuficiente para resolver o resultado; não converter em timeout ou perda por conveniência.

Há dois experimentos distintos: prever **toque em barreira** e prever **PnL executável**. É possível acertar o toque e errar a execução. Para o primeiro, definir alvo-antes-do-stop **dentro de H**, lado de preço utilizado e regra para empates. Para o segundo, começar a contagem depois de entrada preenchida e usar fills, fees, quantidades e saídas. Guardar tempo até evento, MAE/MFE apenas retrospectivos, número de contratos e PnL líquido.

Timeout operacional não é dado censurado: há saída observada se a política manda encerrar em H. Perda de feed antes de H é censura de observação, cuja causa pode coincidir com turbulência; não presumir censura independente. Alvo e stop são eventos concorrentes: estimar cada um isoladamente como se o outro não existisse distorce o evento desejado. Um modelo multiclasses por horizonte, ou análise de incidência de eventos concorrentes quando houver dados suficientes, é um experimento mais coerente que descartar timeouts.

Barra OHLC que inclui alvo e stop não informa a ordem. Amostra RTD tampouco identifica todos os eventos entre leituras. Reportar limites otimista/pessimista ou marcar ambiguidade; não criar sequência intrabar com interpolação para obter resultado favorável. A incapacidade de resolver uma parcela material dos labels interrompe a avaliação econômica de scalping naquele horizonte.

**Critério de passagem P0:** qualquer resultado deve ser reproduzível por outro leitor do log, da política e do código de apuração. Relatório informa taxa de entrada, não execução, timeout, ambiguidade e dados irresolúveis por dia/regime. O resultado principal não pode depender de desempate escolhido depois de olhar PnL.

## 3. Execução: touch não é fill

Fato oficial: a versão de manual B3 consultada descreve oferta stop registrada após disparo e convertida em limitada; não admite stop durante leilão. A seção de mercado descreve execução no melhor preço disponível do lado oposto, com tratamento do saldo. A fonte também documenta RLP e prioridades especiais entre intermediários. Portanto, extrapolar uma fila FIFO genérica a toda execução do cliente, sem conhecer roteamento/tipo de oferta, é inadequado. Fonte [S5], seções 4.3.1 e 4.3.4, páginas impressas 39–49. O PDF está identificado como versão com marcas; conferir a versão consolidada vigente antes de uma integração real.

**Proposta para replay offline:** motor de eventos com chegada, aceite, colocação em fila, negociação parcial, cancelamento, disparo do stop, tentativa de saída, timeout e zeragem. Exigir causalidade: nunca preencher em cotação anterior à chegada da ordem. Consumir profundidade disponível para entrada agressora e considerar volume à frente para alvo passivo. Cancelamento de oferta à frente não pode ser identificado exatamente com agregado de nível: nesse caso modelar uma faixa ou hipóteses conservadoras explicitamente.

Separar distribuições de slippage/custo para entrada, alvo, stop e zeragem; condicioná-las, quando empiricamente identificáveis, a spread, profundidade, volatilidade, horário, quantidade e atraso. Aumentar contratos não deve produzir retorno por contrato invariável se a liquidez impõe impacto. RTD não suporta alegação de fila precisa. Pode servir para validar cronologia/interface ou um estudo de horizonte suficientemente largo, limitado pela amostragem.

**Critério de passagem P1:** comparar resultado sob execução ideal, plausível e adversa previamente especificadas; divulgar diferença de PnL e proporção de propostas que perdem vantagem. Se só o toque ideal torna o resultado positivo, a hipótese econômica falhou no modelo executável. Validar tipos de oferta e roteamento como pressupostos, sem ligar corretora nesta pesquisa.

## 4. Calibração probabilística e valor incremental do JEV

Fato metodológico: regras estritamente próprias incentivam previsão da distribuição correta; Brier e log score são exemplos. Fonte [S1], especialmente Tabela 1. Acurácia de classe, calibração e desempenho financeiro medem propriedades diferentes.

**Proposta:** três braços recebem exatamente oportunidades, informação temporal, custos e execução comparáveis: (A) regras observadas; (B) modelo quantitativo parcimonioso; (C) B mais scores JEV. Uma quarta comparação, mesma regra com abstenção de qualidade mas sem JEV, evita atribuir ao modelo o ganho causado por filtrar dados ruins. Informações financeiras destinadas apenas a risco não entram na pergunta contextual nem em um treino que aprenda a justificar recuperação.

Converter score em probabilidade requer calibrador aprendido em dados de resultados **anteriores**, com prompt/modelo/versão congelados. Não impor que apoio e contradição somem um; representam perguntas distintas. Calibração precisa considerar geometria e H: o mesmo fluxo pode apoiar direção sem tornar alcançável um alvo distante. Começar com base-rate temporal e uma transformação simples; só aumentar complexidade se melhora fora da amostra.

Medir Brier multiclasses ou binário para evento exatamente definido, log loss, curvas de confiabilidade com contagens/incerteza, discriminação e distribuição de resíduos. Bin vazio não demonstra boa calibração. Evitar um único ECE sem contagens, já que binning pode esconder erros. Mostrar desempenho por lado, sessão, spread, volatilidade e distância de barreiras, usando apenas estratos pré-fixados ou declarando exploração. Probabilidade bem calibrada globalmente pode ser ruim no subconjunto selecionado para operar.

**Critério de passagem P2:** melhora pareada em Brier/log loss contra base temporal, intervalo por blocos de sessão e ausência de deterioração material nos estratos pré-fixados. Para promover relevância econômica, melhora adicional no PnL executável líquido por oportunidade disponível e por unidade de tempo, com mesma restrição de risco. Acertar contexto ou melhorar Brier sozinho não prova lucro.

## 5. Validação temporal, janelas sobrepostas e seleção

Fato metodológico: otimizar o próprio critério de seleção pode sobreajustá-lo; avaliar depois no mesmo material produz viés. Fonte [S2]. Fato específico de backtests: PBO estuda deterioração da alternativa escolhida IS e DSR corrige inflação de Sharpe associada à seleção e não normalidade. Fontes [S3–S4]. Esses diagnósticos não substituem execução nem segurança temporal.

**Proposta concreta de divisão:** treino histórico, validação interna posterior para escolher features/calibrador/política e teste externo futuro intocado. Repetir blocos walk-forward, deixando registrado quando houve re-treino. Normalização, limites de intensidade, descoberta de nível, features, seleção e calibrador usam somente informação anterior ao bloco avaliado. Reservar bloco final intocado antes de começar a olhar resultados de qualquer candidato.

Cada exemplo possui intervalo de evidência `[t-L,t]` e intervalo de resultado `[t_entry,t_exit]`. Purga remove exemplos de treino cujo resultado intersecta o teste ou ainda não estava disponível no corte de treino. Na validação estritamente para frente, maturação dos labels exige distância antes do corte; não aplicar mecanicamente um embargo posterior em uma região que nunca é usada para treino. Se usar folds que treinam também depois do teste, acrescentar exclusão após o bloco compatível com lookback e dependência operacional. Derivar tamanho de H, atraso e retenção reais; um percentual arbitrário do dataset não justifica segurança. Isso é raciocínio de causalidade do desenho, não garantia de independência estatística.

Agrupar oportunidades simultâneas do mesmo estado: oito geometrias compartilham trajetória e não são oito trades independentes. Uma política executa no máximo as oportunidades permitidas pelo seu estado de posição. Oportunidades da mesma sessão podem compartilhar regime; usar sessão ou blocos temporais no intervalo de comparação, explicar limitação quando há poucos dias. PnL por trade não descreve o processo completo com tempos sem posição, cooldown e custos de consulta.

Manter inventário de todas as experiências: prompts, features, H, stops/alvos, políticas, faixas de scores e exclusões. O número de tentativas inclui análises descartadas. Não tratar as dez políticas como dez testes independentes nem presumir independência dos oito candidatos. Aplicar PBO somente quando houver matriz temporal de desempenho comparável de alternativas; estudar limitações de forte autocorrelação explicitadas em [S3], seção 5. DSR exige contabilidade de tentativas e pressupostos de retornos, inclusive momentos finitos; não é certificado de edge nem correção automática de séries intraday dependentes.

**Critério de passagem P3:** nenhum resultado externo é usado para escolher prompt, calibrador ou política. A melhora sobre baseline se mantém em vários blocos externos e cenário de execução/custo adverso predefinido; não depende de poucos trades. Tamanho de amostra resulta da precisão pretendida e unidade efetiva de independência, não de uma meta arbitrária como 1.000 decisões.

## 6. Abstenção: medir benefício e preço

Fato: classificação seletiva estuda troca entre cobertura e erro. [S6] é um paper original sobre DNNs em classificação de imagens; não contém garantia financeira para WIN.

**Proposta:** registrar toda oportunidade elegível e separar rejeição por dado incompleto, veto financeiro, suporte contextual e incerteza econômica. Cobertura = fração de oportunidades elegíveis aceitas por cada filtro; cobertura dos dados = fração do tempo com dados suficientes. Essas medidas são diferentes. Curvas risco/cobertura mostram erro preditivo e PnL líquido, não só taxa de acerto dos aceitos. Avaliar custo por decisão, atividade por hora e resultados dos rejeitados em replay para verificar o que se perde.

Abstenção econômica candidata: limite inferior de vantagem líquida conservador não supera zero ou execução não é identificável. Não escolher esse limiar no teste. Selecionar trades e depois anunciar boa calibração global pode esconder o grupo de maior erro. Threshold ótimo em retorno bruto pode ser péssimo após atraso/custos.

**Critério de passagem P4:** seletor mantém ganho líquido incremental em uma faixa de cobertura pré-especificada; não obter aparente excelência aceitando quase nada. Veto de risco permanece absoluto, sem exceção por confiança.

## 7. Conformal e incerteza: útil, mas posterior aos labels

Fatos: ACI busca frequência de cobertura em intervalos longos sob distribuição variável [S7]. Conformal além de exchangeability explicita limites de cobertura que dependem de distância entre distribuições e permite pesos; o limite pode ser pouco informativo quando a mudança/dependência é grande [S8]. Cobertura marginal de intervalos não é probabilidade calibrada individual de alvo nem limite de perda de conta.

**Proposta:** investigar intervalos para resultado executável, erro de previsão ou custos somente após obter labels maduros. Calibração adaptativa atualiza com resultados já disponíveis; latência de maturação impede alimentar resultados futuros. Reportar cobertura global, local por janela/estado e largura dos intervalos, com atenção a sequências de falha. Uma garantia de frequência longa pode coexistir com falhas concentradas num regime perigoso. Um conjunto conformal pode ser largo demais para decidir; isto é informação para abstenção, não motivo para estreitá-lo sem validação.

Não priorizar biblioteca conformal para corrigir feed parcial, score sem target ou retorno executável desconhecido. Experimento posterior compara incerteza simples por blocos com método adaptativo, sob mudança de regime simulada e replay real identificado. Não anunciar garantia exata sob dependência não estudada.

## 8. Valor esperado, crescimento e riscos de trajetória

No modelo binário ideal, `EV = p G - (1-p)L` e `p_break_even = L/(G+L)`. Na presença de timeout, não execução e zeragem, estimar soma das probabilidades de cada resultado multiplicadas por seus retornos condicionais. Não descartar timeouts para aumentar taxa de acerto. Ao usar retornos líquidos já provenientes de fills, não descontar spread/slippage novamente. Risco/retorno condicional alto não informa p nem chance de entrada.

Kelly maximiza crescimento logarítmico sob distribuição especificada; [S9] estuda restrição probabilística de drawdown sob seu modelo, incluindo retornos IID e riqueza não negativa. Não transportar garantia para futuros com perda além da reserva, dependência e distribuição desconhecida. Fractional Kelly reduz exposição relativa a um estimador; se estimador de edge está errado, multiplicá-lo por 0,5 não prova segurança. Pesquisa futura pode comparar pior caso numa região de incerteza da distribuição e impor risco de trajetória; nenhuma fórmula recupera uma distribuição não observada.

**Demonstração matemática própria, não dado WIN:** payoff líquido hipotético por contrato `G=38`, `L=22`, p assumido **0,40 apenas para ilustração**, sem timeout, custos já inclusos, IID, sem margem/granularidade/impacto/gaps. O break-even é 36,67%; EV é R$2 por contrato. Se f é fração do patrimônio perdida num stop, ganho proporcional é `(38/22)f`. Crescimento log esperado é `g(f)=.4 log(1+(38/22)f)+.6 log(1-f)`.

| f hipotético | Retorno aritmético esperado por passo | g log por passo |
|---:|---:|---:|
| 0% | 0% | 0 |
| 1% | 0,0909% | 0,00081990 |
| 5% | 0,4545% | 0,00235843 |
| 10% | 0,9091% | 0,00051651 |
| 15% | 1,3636% | **−0,00535537** |

Mesmo com vantagem positiva suposta, 15% pode produzir crescimento log negativo; a fração ótima **nesse brinquedo** é 5,263%. Isso não valida 5% no aplicativo. Se p real for abaixo do break-even, ótimo no modelo sem short é f=0. Fração admissível de 15% tampouco é fração efetivamente usada devido aos tetos/margem. Quatro perdas a 15% preservariam `0,85^4≈52,20%` do capital **nesse modelo contínuo**, sem garantir que o limite de pico pare a posição antes de um gap.

Reprodução usada:

```python
from math import log
p, G, L = .4, 38, 22  # pressupostos ilustrativos; nunca estimação do mercado
b = G/L
for f in (0, .01, .05, .10, .15):
    print(f, f*(p*b-(1-p)), p*log(1+b*f)+(1-p)*log(1-f))
```

Recuperação não é feature de mercado. Pela linearidade da esperança, se em cada instante o payoff por unidade tem esperança condicional líquida ≤0 e o tamanho é escolhido com informação passada, a esperança condicional do próximo PnL também é ≤0 para lote não negativo, nos casos integráveis e de horizonte finito. Aumentar lote após perda muda distribuição/tail exposure, não o sinal da vantagem. Falta de limites de capital/integrabilidade é justamente o que invalida a aparente promessa de martingale infinito; no sistema finito, limites de margem, contratos e bloqueios encerram a sequência.

**Métricas posteriores de trajetória:** chance de atingir piso de patrimônio antes do fim de H de sessão, máximo drawdown do pico, tempo sob pico, expected shortfall de PnL de sessão e de stop, saldo negativo, tempo e probabilidade até interrupção. Definir ruína operacional como incapacidade de negociar tamanho mínimo/margem, separada de insolvência. Modelar pausa por sequência como evento concorrente com piso/encerramento de sessão; sua probabilidade exige distribuição conjunta de ganhos/perdas e oportunidades, ausente no planejador. Testar clusters de perdas, overshoot do stop, dados indisponíveis e liquidez degradada; não inferir Gaussianidade a partir de perdas planejadas iguais.

**Critério de passagem P5:** só comparar otimização de lotes depois de P0–P4; incluir q=0 e quantidades menores que máximo permitido. Distribuição calibrada/execução plausível deve fornecer vantagem incremental conservadora, estável por blocos e sob estresse. Escolher tolerância de perda é decisão explícita do usuário posteriormente, não inferida da palavra “agressivo”.

## Fontes primárias consultadas

- **S1.** Gneiting e Raftery (2007), *Strictly Proper Scoring Rules, Prediction, and Estimation*, JASA. [Manuscrito dos autores](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf). Base para scores; não comprova calibração do JEV.
- **S2.** Cawley e Talbot (2010), *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*, JMLR. [Paper oficial](https://jmlr.csail.mit.edu/papers/volume11/cawley10a/cawley10a.pdf). Seleção e avaliação separadas.
- **S3.** Bailey, Borwein, López de Prado e Zhu (2015), *The Probability of Backtest Overfitting*. [PDF do autor](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf), seções 2 e 5. PBO/CSCV e limitações.
- **S4.** Bailey e López de Prado (2014), *The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality*. [PDF do autor](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf), seções sobre PSR/DSR, p. 8–11 do PDF. Número de experimentos e não normalidade.
- **S5.** B3, *Manual de Procedimentos Operacionais de Negociação*, versão pública com marcas consultada. [PDF oficial](https://www.b3.com.br/data/files/59/E3/E7/1F/2EDFA9105B12E5A9AC094EA8/MPO%20de%20Negociacao%20da%20B3%20-%20Com%20marcas.pdf), seção 4.3.1, páginas impressas 39–40; RLP seção 4.3.4, páginas 47–49. Fonte operacional, não estudo de vantagem.
- **S6.** Geifman e El-Yaniv (2017), *Selective Classification for Deep Neural Networks*. [Paper NeurIPS oficial](https://papers.neurips.cc/paper_files/paper/2017/file/4a8423d5e91fda00bb7e46540e2b0cf1-Paper.pdf). Classificação de imagens, extrapolação financeira somente como hipótese.
- **S7.** Gibbs e Candès (2021), *Adaptive Conformal Inference Under Distribution Shift*. [Paper original](https://arxiv.org/abs/2106.00170). Cobertura no tempo não é lucro ou garantia individual.
- **S8.** Barber, Candès, Ramdas e Tibshirani (2023), *Conformal Prediction Beyond Exchangeability*. [Manuscrito dos autores](https://www.stat.cmu.edu/~ryantibs/papers/nexcp.pdf), especialmente seções 2.2 e 5. Quantificação de lacunas sob não permutabilidade.
- **S9.** Busseti, Ryu e Boyd (2016), *Risk-Constrained Kelly Gambling*. [Paper original](https://arxiv.org/pdf/1603.06183), seções 2–4. Modelo idealizado com distribuição especificada; não escolhe lote atual do WIN.

## Limites desta pesquisa

Não foram coletados resultados WIN, estimadas probabilidades reais ou conferidas condições individuais de conta/corretora. Não houve execução de ordens ou consulta autenticada ao JEV. Os critérios acima são propostas de passagem de fase para pesquisa; valores numéricos de aceitação, horizonte operacional e tolerância econômica ainda precisam ser pré-fixados com o objetivo concreto de Gabriel. A nota distingue fatos locais, resultados publicados e derivação/recomendação própria.

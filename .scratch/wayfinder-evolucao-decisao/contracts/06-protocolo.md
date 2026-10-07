# Protocolo resolvido — evidência incremental e promoção

Date: 2026-10-07
Version: incremental-evidence-v1
State: specified; not_ready_for_confirmation
Ticket: [Evidência incremental e promoção](../issues/06-evidencia-promocao.md)
Depends on: [Identidade](01-identidade.md), [Hipóteses](02-hipoteses.md), [Tempo](03-tempo-execucao.md), [Dimensionamento](04-dimensionamento.md)

## Perguntas e braços predefinidos

O protocolo resolve o desenho. Datas, dataset autorizado, orçamento e limites pessoais de risco ainda não foram fornecidos; o manifesto não está congelado e nenhuma confirmação foi executada. O método proposto não é evidência de benefício no WIN. A [descoberta de atributos TypeSafe](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery) inspira desenvolvimento; [Cawley e Talbot](https://www.jmlr.org/papers/v11/cawley10a.html) fundamentam o controle de seleção/overfitting.

| Hipótese primária | Comparação | Constantes e efeito isolado |
|---|---|---|
| H1 — previsão | A quantitativo versus B quantitativo+atributos JEV | Mesmo universo/rótulo, família logística, calibração, disponibilidade e orçamento de ajuste; coeficientes diferem. Mede previsão, não ganho financeiro |
| H2 — utilidade integrada de atributos | B versus A no replay econômico | Gerador, selecionador determinístico, quantidade/regra, execução e calendário iguais. Custos/latência de JEV reais entram no braço B; mede benefício líquido integrado |
| H3 — seleção | C Choice tipada versus selecionador determinístico usando B | Exatamente estimativas/candidatos/quantidade admissível/horizonte comuns; C escolhe ID permitido ou espera, sem mudar geometria ou lote |
| H4 — dimensionamento | S1 domínio fracionário discreto versus S0 comparador atual | Modelo/atributos, seleção determinística, cadência e execução congelados; patrimônio/quantidades próprios. Mede crescimento e risco da política |

A baseline permanece logística, com parâmetros/normalização/calibrador e versões concretos no manifesto. Preservar o pipeline existente como comparador; uma proposta de laboratório usa C=1, max_iter=1000, seed=7 e calibração sigmoid, sujeita à conferência de implementação e versão antes de congelar. Não dizer que esses defaults já estão confirmados. B acrescenta inicialmente S/C/I por candidato e janela do contrato; outras transformações/atributos são desenvolvimento separado.

JEV `jev-1.13.0` fica fixado para comparação; modelo retornado diferente invalida o uso daquela resposta. S_discrete, S_robust, regras de fluxo e outras cadências são diagnósticos secundários predeclarados, sem substituir H4 depois de conhecer resultados.

H3 usa q=1 exclusivamente como controle de estudo, em oportunidades não sobrepostas e num cenário de conta comum congelado. Se um contrato não é admissível para ambos, ambos esperam e o caso permanece registrado. Não usar patrimônio específico de um braço para alterar o conjunto oferecido ao outro nesse contraste de seleção. A comparação de seleção usa apresentação/execução no mesmo instante causal, após a resposta C: se a janela venceu, ambos esperam. C arca com sua despesa de Choice; reportar o contraste bruto de seleção e o líquido separadamente. Uma apresentação determinística antecipada é outro contraste integrado de latência, não H3. Efeitos de posição/patrimônio integrados são estudados separadamente; q=1 não vira mínimo do produto. Choice atual pode selecionar qualquer ID da lista admissível, não apenas empates. Respostas fora da lista/quantidade/geometria são violações, sem atribuir ganho.

Se Choice termina sem resposta válida, o instante comum é o primeiro término registrado: timeout/deadline, cancelamento ou detecção de incompatibilidade. Se a validade efetiva acaba antes desse término, ambos esperam desde o vencimento. Na versão primária H3, sem resposta válida ambos esperam, preservando a oportunidade e a despesa da tentativa C; não há fallback seletivo para um braço. O determinístico não recebe uma apresentação antecipada nesse caso. Uma variante com fallback comum exige regra e versão congeladas antes da coleta. Ausência de término observável torna o caso temporalmente desconhecido; não fabricar timestamp ou excluir a oportunidade.

Para H2, atributos ausentes/vencidos em B acionam fallback A já calculado e disponível no mesmo corte. Falta de cobertura obrigatória bloqueia ambos. Custos de consultas tentadas por B continuam contabilizados. Esse fallback é regra de pesquisa versionada; não imputa S/C/I nem mistura avaliações. H2/H4 usam trajetórias próprias com posição, margem e despesas próprias.

## Universo, rótulos e unidade de análise

Congelar gerador de oportunidades/candidatos, calendário e requisitos antes de observar os braços. Candidatos simultâneos, horizontes sobrepostos e repetidas respostas pertencem ao mesmo episódio; sessões preservam dependência entre episódios. Um seletor não recupera candidatos ausentes do gerador. Uma política bloqueada/atrasada conserva a oportunidade no denominador.

H1 usa `net_opportunity_sign_v1`: negativo, zero e positivo do resultado líquido de negociação por oportunidade/candidato, em q=1 admissível no cenário comum e no horizonte/execução/custo congelados. Não entrada comprovada é zero; desconhecido/censurado não recebe classe. Estimativa positiva corresponde a P(X>0|oportunidade), sem confundir com P(X>0|entrada). Se a execução é simulada, o rótulo e a conclusão permanecem condicionados a esse cenário, sem alegação de lucro real. Trata-se de uma versão futura do estudo, não de uma mudança já implementada na baseline.

O rótulo existente stop/alvo/fim de horizonte é preservado como comparador diagnóstico separado, com seu próprio modelo calibrado; não o renomear como sinal líquido nem reutilizar seus coeficientes para o novo alvo. Stop e alvo no mesmo intervalo sem ordem conhecida produzem desconhecido/censurado; não escolher o mais favorável. Rótulos financeiros de H2–H4 usam resultado líquido e execução do contrato temporal, com quantidade/custos/horizonte identificados. Correção tardia cria revisão; maturidade exige disponibilidade efetiva do rótulo.

Publicar H1 no subconjunto pareado com rótulo e atributos válidos para A/B, junto de contagens e motivos de exclusão/viés de cobertura. Métricas dos candidatos agregam primeiro por episódio, depois por sessão, dando peso igual a sessões no contraste primário. H2/H3 mantêm todas as oportunidades oferecidas e resultados conhecidos/desconhecidos, com limites quando identificáveis. Não reutilizar muitas respostas de um episódio como N financeiro adicional.

## Divisões temporais e manifesto

Três períodos globais por datas/sessões: desenvolvimento, calibração/seleção e confirmação futura intocada. Datas concretas estão pendentes; não escolher percentuais distintos por braço. Excluir episódios cuja janela de informação/rótulo/horizonte atravessa a fronteira. Oportunidades/pós-correções só entram depois de disponíveis. Ajustes internos respeitam a mesma causalidade.

Qualquer dado inspecionado enquanto se ajusta catálogo, perguntas, features, política ou protocolo pertence a desenvolvimento. Calibração ajusta probabilidades e seleciona uma configuração segundo regra previamente definida. Abrir confirmação uma única vez depois de congelar; alterá-la após resultado transforma a tentativa em exploração e exige outro período intocado. Não selecionar α, modelo, prompt ou cadência pelo teste final.

O manifesto imutável terá ID/hash e instante de congelamento **anterior** ao acesso confirmatório, com:

- Dataset, direito de uso, hashes/revisões, datas, sessões, instrumentos, cobertura e regras de correção.
- Gerador/episódios, janelas/horizontes, atributos/projeções, catálogo/perguntas/opções/ordem, modelos solicitados/retornados, baseline/calibrador, dependencies e versões de código.
- Seeds, espaços e orçamento de busca, configuração selecionada, número/regras de tentativas, cadência/cache/timeout/validade, clocks e atrasos observados ou assumidos.
- Custos por conta/quantidade/vigência, despesas de API, margem/reserva, execução/parcelas/gaps/desconhecidos, fluxos externos e políticas S0/S1/P.
- Contrastes primários/secundários, unidade, métricas, método de incerteza, tamanho/precisão/efeito, limites de risco, calendário/regra de parada, responsável e condições de invalidação.

Política proposta de coleta: nenhuma repetição semântica para escolher a resposta mais favorável; zero retries automáticos no primeiro desenho. Retry de transporte, se necessário, recebe regra/limite novo antes da coleta, deadline e tentativa separados. Cache preserva idade. Nenhum número de sessões herdado do código é prova suficiente.

## Métricas sem dupla cobrança

| Dimensão | Definição primária e diagnósticos |
|---|---|
| H1 previsão | Brier multiclasses=Σ_k(p_k−1[y=k])², sem dividir por dois, faixa0–2; Δ_F=Brier_A−Brier_B. Log loss=−log(p_y), calibração por classe e contagens são secundárias |
| H2 utilidade | U_s=Σ X_negociação_líquido−despesas_da_política_ainda_não_incluídas por sessão; Δ_B=média_s(U_B−U_A) |
| H3 seleção | Mesma definição U; Δ_C=média_s(U_C−U_determinístico), com q e cenários comuns |
| H4 quantidade | g_π=log(v_final/v_inicial), com cota ajustada a fluxos; Δ_G=(g_S1−g_S0)/S nas mesmas sessões |
| Risco/uso | PnL, DD por cota desde pico, duração/recuperação, perdas de cauda, saldo<=0, incapacidade de admitir q mínimo, entrada/parcial, cobertura, idade/latência, descarte, consultas e custo total |

X líquido já desconta negociação; não subtrair execução novamente em U. Despesas de API incluem falhas/vencimentos e ficam uma vez no ledger. Diferentes volumes de políticas usam seus próprios custos quando a tarifa depende deles. Resultado antes de tributos recebe esse nome; se o objetivo exigir após tributos, sua regra e evidência são indispensáveis.

Para log loss, usar epsilon1e−15 somente como convenção numérica versionada e registrar contagem de clipping. ECE com dez bins fixos é diagnóstico secundário, com contagens/bins vazios; não substituir a distribuição inteira por confidence. A definição do Brier segue [documentação scikit-learn](https://scikit-learn.org/stable/modules/model_evaluation.html#brier-score-loss); versão/API e opções do código devem ser fixadas para evitar mudança de escala.

Cauda: perda média nos piores5% de resultados líquidos por sessão, com ponderação fracionária na fronteira quando necessário; declarar sinal/unidade/N. Poucas sessões não estimam cauda com precisão. W<=0 termina aquela trajetória e é reportado, sem eliminar o braço ou atribuir log finito artificial. Uma política sem entrada não apresenta risco observado zero como garantia de segurança.

Atrasos hipotéticos são sensibilidade separada de latência medida. Publicar oportunidades perdidas, consultas inúteis, gastos por resposta útil e denominadores completos. Custos desconhecidos impedem afirmar utilidade líquida. Massa desconhecida permanece; limites lógicos não são intervalos estatísticos. Perda desconhecida sem limite torna expectativa/crescimento não identificáveis.

## Incerteza, tamanho e multiplicidade

Método de laboratório proposto: stationary bootstrap pareado de **blocos de sessões completas**, 10.000 reamostragens, seed7. Comprimento esperado L=max(2,ceil(S_dev^(1/3))), escolhido com desenvolvimento e congelado; sensibilidade em max(1,L/2) e2L, com convenção inteira registrada. Mesmos índices/sessões para todos os braços. Preservar episódios e posições que cruzam sessões como unidade indivisível. Não reamostrar candidatos/respostas como eventos independentes.

Para H4, executar as políticas inteiras novamente em cada sequência reamostrada a partir das suas bancas iniciais, incluindo capacidade/custos/fluxos e término de trajetória. Não apenas reamostrar retornos calculados com patrimônio original. Modelos/calibradores permanecem fixos: inferência é condicional ao pipeline congelado. Reconstrução de desenvolvimento/treino completo constitui estudo diferente. Reportar também a trajetória cronológica original.

Toda réplica que termina com W<=0 permanece entre as 10.000 tentativas. Registrar por braço o término, suas causas e as contagens de nenhum, um ou ambos os braços com saldo não positivo. No relatório de crescimento, o braço encerrado recebe a convenção de falha logarítmica −∞, sem substituir log de saldo negativo por um valor numérico. Se apenas S1 falha, Δ_G é −∞; se apenas S0 falha, é +∞; se ambos falham, a diferença é indefinida. Não descartar réplicas, limitar perdas artificialmente ou calcular um intervalo confirmatório só entre sobreviventes. A presença de réplicas não finitas/indefinidas impede a conclusão favorável por intervalo de crescimento neste desenho; reportar frequências com denominador completo e classificar H4 como inconclusivo quanto ao contraste de crescimento, salvo regra desfavorável de risco previamente violada. Essas frequências são diagnóstico da reamostragem, não probabilidade operacional de ruína. Um estimando limitado alternativo exige novo protocolo predeclarado, sem reparar o holdout já aberto. Saldo não positivo na trajetória original impede aprovar a política afetada.

No contraste primário H4, não há aporte/retirada durante a confirmação simulada: banca inicial e nenhum fluxo externo são comuns. Trajetórias com fluxos do livro real ou fixtures são diagnósticos separados, preservando cota e calendário. Isso evita reamostrar aportes como se fossem oportunidades de mercado. Qualquer variante com fluxos recebe regras de replay próprias no manifesto.

A referência [Politis e Romano](https://www.tandfonline.com/doi/abs/10.1080/01621459.1994.10476870) trata stationary bootstrap para dependência; a [revisão de Politis](https://math.ucsd.edu/~politis/impactBOOT.pdf) explicita limitações de reamostragem. O método não torna regimes não estacionários representativos. Dependência de bloco/regime incompatível ou resultado sensível de forma decisiva gera inconclusão e revisão de desenho, sem garantia estatística automática.

Família primária H1–H4 com erro familiar5%: intervalos bilaterais individuais98,75%, quantis0,00625/0,99375, por Bonferroni. Secundários podem usar95% identificados como exploratórios, sem promoção posterior a primários. Não escolher o melhor de muitas políticas e citar só seu intervalo.

Planejar N/calendário a partir da variância em desenvolvimento por blocos, frequência/agrupamento de oportunidades, precisão e efeito mínimo relevante. Número de sessões, datas, largura máxima dos intervalos e avaliação de poder permanecem pendentes. 10.000 reamostragens não criam 10.000 sessões. Congelar parada por calendário/N/limites de dados, sem parar quando resultado se tornar favorável. Inadequação de amostra pode encerrar como inconclusivo.

## Critérios de resultado

| Resultado | Regra prévia |
|---|---|
| Confirmação inválida — precedência 1 | Leakage, ajuste no holdout, violação de braço, versão/manifesto incompatível; registrar como tentativa contaminada/exploratória, sem promoção |
| Desfavorável — precedência 2 | Limite superior<0 ou risco observado excede limite previamente definido; preservar resultado e alcance |
| Favorável em previsão | Limite inferior de Δ_F>0, precisão planejada, cobertura/labels válidos e robustez ao desenho; só autoriza conclusão de previsão |
| Favorável em H2/H3/H4 | Limite inferior da diferença>efeito mínimo δ_j e largura<=w_j, custos/execução identificados, massa desconhecida controlada e limites de DD/cauda/incapacidade previamente aprovados satisfeitos |
| Inconclusivo — todos os demais casos | Intervalo cruza/toca efeito relevante, ganho inteiramente positivo mas abaixo de δ_j, precisão insuficiente, réplicas de crescimento não finitas/indefinidas, sensibilidade/dependência incompatível, custo ausente, massa desconhecida não delimitada ou cobertura inadequada |

Aplicar as regras nessa precedência: validade da confirmação, risco/efeito desfavorável demonstrado, todos os requisitos favoráveis, demais casos inconclusivos. Igualdade no limiar não satisfaz a condição estrita de benefício. Um intervalo [0,1;0,2] com δ=0,5 é inconclusivo para a promoção por benefício relevante; não demonstra efeito negativo. Falta de informação de risco não equivale a violação demonstrada, nem permite conclusão favorável.

δ_j, w_j e limites de risco econômicos estão **pendentes**, pois dependem do objetivo/prévia tolerância de perda e dados. Não escolher valores pessoais automaticamente. Sem eles o protocolo não está pronto. Brier melhor com perda depois de custos é sucesso de previsão e resultado econômico desfavorável/inconclusivo, conforme seu intervalo; não é ganho financeiro. Um saldo não positivo impede aprovar essa política naquele caso; ausência de ruína observada não prova probabilidade zero.

## Tentativas, registro de evidência e invalidação

Ledger append-only: attempt_id, protocolo/manifesto, data, partições tocadas, versões/perguntas/atributos/parâmetros, motivos das mudanças, resultados inclusive negativos, chamadas/falhas/descartes e despesas. Tentativas remotas repetidas do mesmo episódio continuam uma oportunidade financeira. Não gravar credenciais ou publicar dados privados/mercado sem direito de redistribuição; usar refs/hashes permitidos.

Registro de validação contém identidade dos dados/direitos, período/cobertura, versões completas, comparadores, availability/execução/custos, tentativas, métricas/intervalos/limites, exceções, cenário validado, responsável, vigência e invalidações. Separar `evidence_state`, `approved_use_scope` e autorização operacional. `validated=true` ou `deployment_approved` isolados não suprem esse registro. Artefato sintético não vira confirmado ao mudar flag.

| Mudança | Tratamento da evidência |
|---|---|
| Modelo/pergunta/opções/features/calibrador/política | Nova versão e revisão; não herdar confirmação automaticamente |
| Fonte/cobertura/clock/execução | Reavaliar validade causal e utilidade; fora do cenário estudado exige evidência própria |
| Tarifa/margem/conta/patrimônio fora de cenários estudados | Recalcular custo/admissibilidade; confirmação nova se mudança material segundo regra congelada |
| Horizonte/cadência/gerador/população | Novo experimento ou revisão previamente definida; preservar histórico |
| Correção do dataset | Nova revisão/hash; identificar conclusões afetadas, sem reescrever acesso histórico |
| Apenas visualização | Testar interface Windows; não requer automaticamente novo treino financeiro |

Variação normal de preço/tempo dentro do cenário gera novas decisões com suas identidades; não confere validade universal ao estudo anterior. Regras de materialidade também são parte do manifesto, definidas antes de ver resultados.

## Gates e pendências para confirmação

| Gate | Evidência necessária | Estado nesta rodada |
|---|---|---|
| G0 — desenho documental | Contratos resolvidos e aceite rastreável | Resolvido documentalmente; ver [auditoria](../acceptance-audit.md) |
| G1 — pronto para coleta/confirmação | Dataset/direitos, datas/N, custos/margem, clocks/execução, orçamento autorizado, precisão/efeito/risco e manifesto congelado | Não pronto |
| G2 — integridade técnica | Implementação causal, rótulos e ledger testados no escopo | Não executado nesta rodada |
| G3 — resultado temporal | Confirmação intocada com resultados/intervalos/risco e limitações | Não executado |
| G4 — revisão de uso | Aprovação explícita do uso no cenário validado | Pendente; nenhuma flag concede permissão |
| G5 — interface Windows | Sessão nativa e correções do contrato visual | Não realizada |
| G6 — execução de ordens | Escopo e autorização próprios | Fora desta rodada; aplicativo não envia ordens |

Pendências concretas de G1: direito de uso e resolução dos dados; tarifa/margem vigentes da conta; conciliação e política de fluxos; timestamps e execução observáveis; custos/limite de consultas e autorização de orçamento; períodos intocados; N/precisão/poder; efeito mínimo e limites de perda; versão definitiva do manifesto/responsável. Estes itens bloqueiam coleta/confirmar benefício, não a resolução dos tickets de planejamento.

ProfitDLL depende de SDK/ABI e contrato autorizado. Registrar licença, versão e vigência: [Nelogica](https://ajuda.nelogica.com.br/hc/pt-br/articles/51583791325211-Como-obter-acesso-%C3%A0-ProfitDLL) e [B3 políticas de dados](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/distribuidores/politica-comercial-e-contratos/) são referências para conferir regras até31/10/2026 e desde01/11/2026. Nenhuma licença operacional foi conferida ou adquirida nesta rodada.

## Casos de aceite e conclusão documental

| Caso do ticket | Aplicação do protocolo |
|---|---|
| Repetir respostas | Ledger com várias tentativas; episódio financeiro único |
| Melhorar Brier e perder líquido | H1 e H2 separados, com despesas e cobertura |
| C alterar q/eligibilidade | Violação de H3 e confirmação inválida |
| Políticas divergem no início | Bancas próprias, sem reset/compartilhamento |
| Mudar prompt após confirmação | Contaminação registrada e novo período intocado necessário |
| Desconhecido/cobertura perdida | Denominador/massa preservados; limites ou inconclusão |
| Flag sem registro | G3/G4 recusados por evidência insuficiente |
| Resultado negativo/inconclusivo | Preservado no ledger e no relatório |
| Modelo/fonte/custo novo | Matriz de invalidação aplicada, histórico preservado |

Braços, unidade, divisões, manifesto, métricas, incerteza, critérios, tentativas e gates satisfazem o aceite documental. Os campos indispensáveis ausentes permanecem nomeados e impedem `ready_for_confirmation`. Resolver este ticket não executa experimento, aprova rentabilidade ou amplia o escopo de ordens.

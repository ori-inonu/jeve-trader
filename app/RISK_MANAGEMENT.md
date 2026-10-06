# Gerenciamento de risco para crescimento agressivo

Este documento descreve a política implementada em `config.json`, `risk.py` e `capital_planner.py`. O sistema trabalha com contas de estudo informadas manualmente; os dados de mercado podem vir de demonstração, replay ou observação parcial do Excel. Não há leitura de saldo/posição da Toro. Os lotes abaixo são resultados de exemplos contábeis reproduzíveis, sem recomendação de operação, previsão de lucro ou validação de desempenho.

## Objetivo e restrições

O objetivo de pesquisa é crescer o capital com leitura de fluxo, permitindo recalcular a exposição quando o patrimônio variar. Não há meta nem teto obrigatório de lucro diário. Ainda assim, o problema exige orçamento de perda: sem ele, “maximizar lucro” não determina uma política finita de exposição.

**Máximo lote admissível e lote economicamente ótimo são decisões diferentes.** O primeiro cabe nas restrições de margem e perda planejada. O segundo depende da distribuição dos resultados, custos, liquidez, probabilidade de execução e perdas extremas. O motor calcula o primeiro; ainda não estima o segundo.

Cada hipótese precisa de entrada, invalidação e alvo sustentados pelas observações. O JEV pode apoiar ou contrariar hipóteses, mas sua confiança de classificação não equivale à probabilidade de lucro. Todas as alternativas podem terminar em abstenção. Uma relação ganho/risco atraente, isoladamente, não demonstra vantagem.

## Matriz de políticas

| Política | Situação atual | Papel e condição de uso |
|---|---|---|
| Risco fixo em reais | Não implementado como limite independente | Permite comparar propostas com orçamento monetário constante; não acompanha automaticamente o capital. |
| Fração do patrimônio | Implementada | O perfil agressivo usa patrimônio corrente; o perfil de controle limita a base ao menor entre patrimônio inicial e atual. |
| Stop e volatilidade | Parcial | A distância do stop determina risco monetário. Níveis repetidos e extremos observados são extraídos em `candidate_research.py`; a relevância preditiva e a adaptação à volatilidade permanecem sem validação. |
| Perda diária e drawdown | Implementados | Pisos de patrimônio limitam novas propostas; o pico informado restringe devolução de ganhos. |
| Sequência de perdas | Bloqueio e pausa implementados | A quantidade cai quando o capital diminui. Redução progressiva específica por sequência ainda não existe. |
| Kelly fracionado | Não implementado | Exige distribuição de resultados estimada e calibrada fora da amostra. Scores brutos do JEV não atendem a esse requisito. |
| Pirâmide, saídas parciais, trailing e hedge | Não implementados | Exigem posição conciliada, risco agregado, custos e tratamento de execuções parciais antes de modificar exposição. |
| Martingale e aumento para recuperar | Não escolhidos | O prejuízo anterior não autoriza aumentar lote, afastar stop ou fabricar alvo de compensação. |

## Comparação implementada no painel

`risk_research.py` compara dez combinações: frações de 1%, 3%, 5%, 10% e 15% em duas bases, patrimônio atual e base limitada ao início. Cada combinação usa a mesma geometria, custos, margem e restrições de perda, para que a comparação seja coerente. A tabela mostra lote permitido e stops projetados até a trava da política. Não escolhe uma vencedora por lucro esperado, porque essa distribuição não foi estimada.

A aba Cenários técnicos permite comparar até oito geometrias de entrada/stop/alvo extraídas dos dados, cada uma com sua própria conta de risco. Ordenar por relação ganho/risco não transforma um alvo em provável. A aba Capital permite estudar um stop/alvo digitado, separado desses níveis técnicos.

## Política agressiva disponível

`agressivo_pesquisa` usa **15% do patrimônio por proposta**, piso diário correspondente a **50% do capital inicial** e tolerância de **50% de queda do pico**. São parâmetros arbitrários de laboratório, não calibrados nem escolhidos pelo usuário para operação real.

O perfil bloqueia novas propostas após quatro perdas consecutivas e aplica pausa de um minuto após perda. `max_contracts: 100` é um teto técnico configurável, não um lote desejado. O tamanho resulta do menor limite entre quantidade solicitada, teto técnico, orçamento dividido pelo risco unitário e margem disponível.

A margem considera uma reserva para a perda planejada ao lado da garantia. O orçamento de uma nova proposta é o menor entre:

- 15% do patrimônio corrente;
- patrimônio disponível acima do piso diário, descontado risco reservado;
- patrimônio disponível acima do piso de drawdown, descontado risco reservado.

Os pisos são restrições alternativas: seleciona-se a mais apertada, sem somar as reservas duas vezes. Ganhos podem ampliar o orçamento; perdas o reduzem. Posições abertas ou entradas pendentes bloqueiam novas propostas nesta implementação.

## Exemplos: R$ 400 e R$ 4.000

O [WIN vale R$ 0,20 por ponto](https://www.b3.com.br/en_us/products-and-services/trading/equities/mini-ibovespa-futures.htm). A [margem mínima publicada pela B3](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-participantes-e-traders/regras-e-parametros-de-negociacao/margem-minima-requerida-e-guia-educacional-para-minicontratos/) é R$ 155 por contrato; a corretora pode exigir mais.

Considere stop de 100 pontos e alvo de 200 pontos. A configuração acrescenta R$ 1 de tarifas hipotéticas e cinco pontos de slippage total, equivalentes a R$ 1: **R$ 2 de custos modelados**, não uma tabela real da corretora.

O risco unitário é R$ 22 e o ganho líquido condicionado ao alvo é R$ 38. Para dimensionar, cada contrato exige R$ 155 de margem mais R$ 22 de reserva: **R$ 177**.

| Cenário | Patrimônio R$ 400 | Patrimônio R$ 4.000 |
|---|---:|---:|
| Capital inicial da sessão | R$ 400 | R$ 400 |
| Pico informado | R$ 400 | R$ 4.000 |
| Orçamento de 15% | R$ 60 | R$ 600 |
| Piso diário / piso do pico | R$ 200 / R$ 200 | R$ 200 / R$ 2.000 |
| Lote admissível calculado | 2 | 22 |
| Perda planejada desse lote | R$ 44 | R$ 484 |
| Stops consecutivos até bloqueio da política | 4 | 4 |
| Contagem diagnóstica ignorando somente a trava de sequência | 7 | 6 |

Pressupostos: nenhuma perda consecutiva inicial, nenhuma posição pendente, toda a margem informada disponível e repetição da mesma geometria. A projeção recalcula o lote após cada stop e mantém o pico original. Lotes maiores explicam a menor contagem em R$ 4.000. As contagens não preveem oportunidades, duração dos trades ou quantas operações cabem no pregão. O cálculo é limitado em iterações; resultados truncados representam apenas o trecho calculado.

Após perder R$ 20, R$ 400 viram R$ 380 e o orçamento de 15% cai de R$ 60 para R$ 57. Recuperar R$ 20 é um objetivo do operador, não uma informação que aumenta a vantagem da próxima entrada.

## Resultados e pausa

O diário atualiza o capital a partir do resultado líquido digitado. Ganho aumenta o patrimônio; prejuízo diminui. Uma perda registrada inicia a pausa de 60 s do perfil de pesquisa. Um valor que esgote o patrimônio é preservado, inclusive saldo negativo; novos cálculos ficam indisponíveis. Reiniciar o aplicativo não restaura o capital anterior.

Uma sequência de perdas digitada no formulário, sem horário registrado, é assumida como cenário com a pausa já transcorrida; o sistema informa essa hipótese e mantém a contagem. Projeções de stops usam pausas hipotéticas entre tentativas. Nenhuma contagem representa número garantido de oportunidades ou capacidade real de sobreviver ao mercado.

## Execução e limites pendentes

A [Toro publica R$ 35 por contrato WIN em zeragem compulsória](https://www.toroinvestimentos.com.br/info/custos?hsLang=pt-br). Esse custo de estresse não está embutido nos R$ 2 ilustrativos. A [Nelogica documenta o pulo de ordens](https://ajuda.nelogica.com.br/hc/pt-br/articles/360053623191-Compreendendo-o-Pulo-de-Ordens); um stop planejado não garante execução pelo preço desejado. Perdas reais podem ultrapassar a reserva e o depósito.

Permanecem não implementados: calibração de lucro e valor esperado, escolha economicamente ótima de lote, gerenciamento de posição aberta, pirâmides, saídas dinâmicas, hedge e detecção automática do capital real. Saldos, pico, sequência e margem recebidos são pressupostos do cenário; sua obtenção e conciliação com Profit/Toro ainda exigem integração.

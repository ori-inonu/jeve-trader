# Percurso observado e interpretação do fluxo WIN

Pesquisa concluída em 2026-10-08 para `.scratch/wayfinder-live-windows/issues/06-contexto-fluxo.md`. Produto somente lido. Este relatório prepara evidência e casos para o coordenador e a revisão independente; não certifica implementação, inferência real, continuidade do feed, desempenho ou rentabilidade. Nenhuma API paga foi consultada.

## Recomendação dentro do objetivo autorizado

Acrescentar primeiro as distâncias observadas entre o primeiro negócio, extremos e último negócio de cada janela. A mudança enriquece o estado comum do JEV sem introduzir Scores, novos thresholds ou outro feed. A evidência permite distinguir uma subida de quatro ticks com devolução de três de uma subida direta de um tick. Ambas têm progressão líquida de um tick, mas o comportamento observado até o último negócio difere.

Os extremos são estatísticas da sequência aceita, não reconstrução de cada movimento entre negócios, nem causa do preço, posição de investidores ou sinal suficiente para operar. Se houver somente snapshots, linhas perdidas, filtros, empates de horário ou cobertura parcial, essa limitação acompanha os números. Esta recomendação corresponde ao contrato FD-01/02/03 já preparado pelo coordenador; não muda seus aceites.

## Evidência do projeto e hashes anteriores à alteração

| Fonte local | SHA-256 | Evidência literal e alcance |
| --- | --- | --- |
| `app/flow_engine.py` | `9e3b804ac365e4ae9d99b4285f7ddf2eeed3e6e962e5d6cc50521a63d84d8ead` | Linhas 232–233: `progress = prices[-1] - prices[0] if prices else None` e `span = max(prices) - min(prices) if prices else None`. `_window` retorna primeiro/último, amplitude e progressão, mas não distâncias dos extremos ao primeiro e ao último. |
| `app/context_cycle.py` | `52a2410e8560e6167cda48d895625c021838853299f64cf8444fdce7a441fe6d` | Linha 87: `Absorbed selling can support buying; exhausted buying does not prove selling. Broker balances describe only observed trades, never investor positions.` O contrato contextual já distingue os fenômenos e seus lados. |
| `.scratch/wayfinder-live-windows/flow-depth-contract.md` | `a2518a56c2d94a46c3c8da1eebb1fb1b62f2911fc94593ef377bfe2c496f9d2a` | `Menos de dois negócios deixa métricas nulas; quantidade de observações e escopo parcial são explícitos.` FD-01 também exige preservar a ordem aceita de IDs diferentes com horários empatados. |

O seam público é `FlowEngine.snapshot` → `build_context`. O código lido usa janelas `(início, fim]`: `5s`, `previous_5s` e `30s`. A flag `complete_window` depende da cobertura, truncamento e `full_tape=True`; a nova estatística não pode promovê-la. Os hashes descrevem a baseline pesquisada, não uma revisão do candidato posterior.

## Fontes primárias, bytes e trechos literais

Os hashes abaixo são SHA-256 dos bytes HTTP efetivamente obtidos em 2026-10-08. Cópias estão em `.artifacts/flow-visual-research-20261008/flow-source-bytes/`, diretório ignorado; não incluir em commit. Um hash de página HTML pode mudar por metadados do site sem mudança semântica. A evidência literal identifica o conteúdo utilizado.

| Fonte | Arquivo / bytes / SHA-256 | Evidência literal curta |
| --- | --- | --- |
| [B3 — Futuro Mini de Ibovespa](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/futuro-mini-de-ibovespa.htm) | `b3-win.html` / 43.491 / `140ae1cf4c6b150dc3f2b3cdec7449b50560a406ef9c0f5e8e6112c79ec81224` | Características técnicas: `5 pontos de índice.` |
| [B3 — Binary UMDF Message Reference 2.3.1](https://www.b3.com.br/data/files/5C/B7/2E/07/C706F910CEC024F9AC094EA8/BinaryUMDF-MessageReference-v.2.3.1-enUS.pdf) | `b3-umdf-2.3.1.pdf` / 2.518.809 / `b16db9e1be05628d46aa4f0ee93a5a17ddeb47f7b42bf78116a0d56d11358513` | Página impressa 102, `aggressorSide`: `Which side is aggressor of all fills.` Página 97, firma compradora: `For reporting trades (buying party).` |
| [TypeSafe — índice vivo](https://docs.typesafe.ai/llms.txt) | `typesafe-index.txt` / 16.132 / `4151e8fd18e5494580571957beff0933e18aecbea2ac7826d3bf53184e8a6a40` | `# TypeSafe AI` |
| [TypeSafe — State](https://docs.typesafe.ai/concepts/state) | `typesafe-state.md` / 3.669 / `8ed5a4e719cf2414759fed92463c203855f1fb4bf02b685746cd4858481375a5` | Linha Markdown 11: `All questions see the same state and are evaluated independently.` |
| [TypeSafe — Choice](https://docs.typesafe.ai/primitives/choice) | `typesafe-choice.md` / 26.907 / `ae9c49b815ee30b28ed851e22b63041130fba50ae41368d41a5d80b571f383bb` | Linha Markdown 346: `The sum of all values is 1.` |
| [TypeSafe — Noul](https://docs.typesafe.ai/primitives/noul) | `typesafe-noul.md` / 26.498 / `bf5d8c6700fbd9272ce27b53a6439d598e7915cdf505704ac7c827c6175ecb88` | Linha 339: `A value near 0.5 means the model gives yes and no similar probability.` Linha 369: `not a scale of the thing you asked about.` |
| [TypeSafe — Confidence](https://docs.typesafe.ai/confidence) | `typesafe-confidence.md` / 24.090 / `5c325ec0c0b69e78129406ca7c5d3aef113bce365abd34985b8674cd278c81be` | Linha 299: `concentrated on one outcome means a confident answer` |
| [Cont, Kukanov e Stoikov — The Price Impact of Order Book Events, v3](https://arxiv.org/abs/1011.6402v3) | `cont-orderbook.html` / 41.977 / `d5ac7212f18f68b510127280f79ae83e47ad98a444ed2b9bc72cfff06e5d5a20` | Abstract: `using the NYSE TAQ data for 50 U.S. stocks.` |

Recuperação: a primeira abertura UMDF pelo web retornou `(400) Timeout fetching`; HTTP direto obteve o PDF e a abertura seguinte do web permitiu ler suas tabelas. As páginas TypeSafe `.md` inicialmente retornaram `URL ... is not accessible via this tool.`; as páginas sem extensão foram lidas pelo web e os bytes Markdown foram obtidos por HTTP. Não se utilizou documentação inventada para suprir essas falhas.

## O que as fontes sustentam

A B3 documenta WIN em pontos de índice, com variação mínima de cinco pontos. Usar o tick validado do contrato como denominador mantém as distâncias comparáveis; não converter automaticamente uma distância em capital disponível, margem ou lote. A página não comprova que nosso perfil Excel captura negócios completos. [B3 — WIN](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/futuro-mini-de-ibovespa.htm).

O UMDF distingue `Trade_53`, `ExecutionSummary_55`, ordens e exclusões. `Trade_53` define `tradeID` por instrumento/data e firmas compradora/vendedora opcionais. Agressor aparece no resumo de execução; seu vínculo aos negócios precisa ser demonstrado pelo adaptador. `transactTime`, `rptSeq` e sequência do canal têm funções próprias. Logo, snapshot, horário crescente ou firma identificada não comprovam tape completo, posição individual ou evento causal de cancelamento. Essa é uma inferência de engenharia apoiada nas tabelas, não garantia da cobertura oferecida pelo Profit/Excel. [UMDF, seções 5.1, 9.2.20–27](https://www.b3.com.br/data/files/5C/B7/2E/07/C706F910CEC024F9AC094EA8/BinaryUMDF-MessageReference-v.2.3.1-enUS.pdf).

O estudo de Cont/Kukanov/Stoikov relaciona alterações de preço com desequilíbrio dos eventos no melhor bid/ask e profundidade. Seu universo empírico são ações americanas; não valida thresholds, absorção, rentabilidade ou transferibilidade para WIN. Ele sustenta pesquisar informação de livro além de volume negociado e medir a resposta do preço, mantendo testes específicos do mercado e da captura disponível. [Artigo original](https://arxiv.org/abs/1011.6402v3).

TypeSafe permite reunir fatos relacionados em um estado JSON comum e avaliar perguntas independentes sobre ele. Portanto, fornecer percurso, agressão, cobertura e premissas lado a lado é coerente com o contrato atual; os Nouls não precisam depender da resposta de outro Noul. [State](https://docs.typesafe.ai/concepts/state).

Choice compara alternativas mutuamente selecionáveis. Noul mede a probabilidade de uma afirmação ser verdadeira, não a força física de absorção ou intensidade do mercado. Confidence resume a distribuição do modelo; não mede chance de lucro nem valida a qualidade da fonte. Preservar apoio, contradição e insuficiência separadamente evita transformar uma soma de probabilidades em um medidor falso. [Choice](https://docs.typesafe.ai/primitives/choice), [Noul](https://docs.typesafe.ai/primitives/noul), [Confidence](https://docs.typesafe.ai/confidence).

## Requisitos de interpretação e não objetivos

- Descrever as quatro distâncias de cada janela como observações calculadas, com contagem, referência no primeiro negócio e flag de cobertura existente. Valores ausentes permanecem nulos.
- Preservar `aggressor_side`, `scenario_side`, família do fenômeno e premissa literal. Absorção de vendas pode apoiar uma hipótese compradora; exaustão compradora enfraquece continuação da compra e não confirma venda.
- Não chamar as devoluções de rejeição comprovada, defesa institucional, encerramento de posição ou intenção. Preços negociados e firmas não revelam esses fatos.
- Usar o mesmo estado atualizado para Choice e Nouls independentes; código local mantém cálculo, frescor, orçamento, ON/OFF e regras financeiras. Nenhuma nova política de risco, envio ou retry é necessária para acrescentar a evidência.
- Não atribuir aprendizado ao modelo por atualizar o estado. Evolução contextual, avaliação anotada e treinamento são processos distintos. Não há neste incremento treinamento, upload de diário, imagens ao JEV, novos Scores, limiares novos, execução de ordens ou alegação de assertividade financeira.

## Casos anotados para revisão independente

Com tick de cinco pontos e sequência observada `P`, definir `U=(max(P)−P0)/tick`, `D=(P0−min(P))/tick`, `RB=(max(P)−Plast)/tick` e `RS=(Plast−min(P))/tick`. São distâncias não negativas. `RB` e `RS` não são atribuição causal ao agressor. A avaliação abaixo é um oráculo aritmético preparado antes da implementação; não é resultado de teste executado nem rótulo de recomendação do JEV.

| Caso / preços na ordem aceita | U | D | RB | RS | Leitura permitida |
| --- | ---: | ---: | ---: | ---: | --- |
| A: 100000, 100020, 100005 | 4 | 0 | 3 | 1 | Avanço observado de quatro ticks; último três abaixo do máximo. |
| B: 100000, 100005 | 1 | 0 | 0 | 1 | Mesmo saldo final de A, sem devolução observada do máximo. |
| C: 100000, 99980, 99995 | 0 | 4 | 1 | 3 | Espelho vendedor de A. |
| D: 100000, 99995 | 0 | 1 | 1 | 0 | Mesmo saldo final de C, sem recuperação observada do mínimo. |
| E: 100000, 100000 | 0 | 0 | 0 | 0 | Duas observações válidas sem distância. Não substituir por indisponível. |
| F: 100000, 99990, 100015, 100005 | 3 | 2 | 2 | 3 | Extremos dos dois lados; não inferir movimentos entre observações. |
| G: sequência vazia | null | null | null | null | Contagem zero e insuficiência explícita. |
| H: 100000 | null | null | null | null | Contagem um; não há percurso suficiente. |
| I: A com `full_tape=False` ou lacuna | 4 | 0 | 3 | 1 | Métricas do observado, cobertura parcial mantida; não confirmar fenômeno por esses números. |

Aplicar A–I às três janelas, verificando seus próprios limites temporais. Adicionar o caso de negócios com mesmo timestamp, IDs distintos e preços na ordem A: preservar todos os IDs e a ordem aceita; registrar que essa ordem não comprova a cronologia absoluta da bolsa. Verificar também que `build_context` leva os números e a premissa literal ao estado comum sem modificar a sequência original, flags ou regras financeiras. Os testes usam seams públicos e respostas locais; comparação de inferências reais continua pendente em FW-12.

## Alternativas reais e próximo caminho

| Alternativa | Informação acrescentada | Dependência / decisão nesta fatia |
| --- | --- | --- |
| Distâncias observadas da janela | Diferencia amplitude, avanço e distância do último aos extremos usando negócios já aceitos. | Recomendada agora. Não demonstra causalidade ou vantagem econômica. |
| Agressão e volume por faixa de preço, comparando janelas | Ajuda a localizar onde volume/agressão se concentraram e comparar resposta do preço. | Evolução posterior; precisa de eventos individuais, lados conhecidos, identidade e cobertura verificadas. Não somar VAP agregado a negócios para fabricar volume. |
| Reposição, retirada e consumo de liquidez por evento | Permite separar alterações observadas do livro e, com eventos suficientes, relacioná-las às execuções. | Depende de feed/licença/adaptador autorizados e continuidade. Dois snapshots mostram mudança visível; não bastam para distinguir cancelamento, execução e reposição ocultos. |
| Avaliação contextual em casos reais anotados | Mede erros de interpretação, contradição e insuficiência antes de revisar perguntas ou thresholds. | Necessária para alegar melhoria do JEV; requer captura autorizada, rótulos e comparação congelada. Não fazer treinamento automático nem chamadas pagas nos testes desta fatia. |

O próximo ciclo elegível deve primeiro obter evidência do contrato/campos reais e manter o ticket canônico de piloto aberto. Estatística melhor não supre cobertura inexistente. A aprovação independente do candidato, o piloto Windows de 30 minutos e a comparação contextual não foram executados por este pesquisador.

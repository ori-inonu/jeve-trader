# Cadência e termômetro contextual

Type: research
Status: resolved
Blocked by: none

## Question

Como obter movimento e respostas rápidas preservando validade, orçamento e significado dos indicadores?

## Answer

Separar dois ciclos: ingestão/cálculos/visualização reagem aos dados novos; JEV interpreta snapshots tipados por mudança relevante, com uma chamada em voo e coalescência do estado mais recente. Proposta inicial: intervalo mínimo de 1 segundo, configurável dentro do orçamento, sem repetir snapshot inalterado. Medir latência e descarte; 1 Hz é alvo de engenharia, não desempenho demonstrado. Recuar em 429/529 sem prolongar validade de respostas antigas.

JEV usa requisição/resposta e perguntas paralelas sobre estado compartilhado, não fornece feed de mercado. Confidence descreve concentração de Choice e Noul estima uma proposição; nenhum deles certifica lucro. Fontes primárias: [API](https://docs.typesafe.ai/api), [perguntas paralelas](https://docs.typesafe.ai/cookbooks/parallel_questions), [confidence](https://docs.typesafe.ai/confidence), [limitações do modelo](https://docs.typesafe.ai/model-jaggedness/jev-1.13).

Direção proposta por Choice explícito `compra/venda/aguardar`, vinculado ao contrato, geração da fonte, geometria e conta: `T=100*(P(compra)-P(venda))`. Nome visível: força direcional contextual experimental. Ausência/expiração vira indisponível, não zero neutro. Não somar Nouls independentes nem transformar absorção automaticamente em reversão. Seleção técnica consultou Jev advisory; não constitui validação empírica.

Alertas: episódio identificado, cruzamento de limiar, histerese, deduplicação e cooldown; fonte válida, plano/custos conferidos e risco admissível. Entrada a mercado só com bid/ask atual e margem de execução explícita; se faltar, mostrar nível observado/entrada condicional sem inventar preço. Bloqueio econômico principal permanece até modelo aprovado; ação continua manual.

## Comments

Pesquisa concluída por agente leitor. Gabriel escolheu horizonte de segundos a dois minutos e alertas experimentais identificados. Implementação atual ainda tem mínimo de 10 segundos; este ticket define caminho, não a alteração do motor. Para UI: preservar instância ECharts e foco/zoom; animar somente transições de valores reais; exibir idade, cobertura e latência. Banca manual não recebe movimento fictício.

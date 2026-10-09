# Contrato resolvido — disponibilidade, execução e utilidade

Date: 2026-10-07
Version: causal-execution-v1
State: specified; execution_not_validated
Ticket: [Utilidade após latência e execução](../issues/03-latencia-execucao.md)
Depends on: [Identidade](01-identidade.md)

## Registro causal e relógios

Cada fato registra tempo do evento quando conhecido, captura, chegada/validação no motor e disponibilidade efetiva, com domínio de relógio e incerteza. Informação só entra no corte quando já disponível. Uma correção cria outra revisão com sua própria disponibilidade. Replaying às 10:00:01 não incorpora uma correção recebida às 10:00:03, mesmo se ela se refere a um negócio de 09:59:59. É uma regra de engenharia coerente com [point-in-time joins](https://docs.feast.dev/getting-started/concepts/point-in-time-joins); não exige adotar Feast.

| Campo/evento | Uso | Limitação e regra |
|---|---|---|
| `event_at`, domínio da fonte | Ordem do evento no mercado | Null quando não fornecido; não prova disponibilidade ou continuidade |
| `captured_at`, `ingested_at`, `available_at` | Captura, chegada e disponibilidade após processamento | Guardar separadamente; validar dependências dos atributos calculados |
| `cut_at`, `submitted_at`, `received_at` | Documento conhecido e tentativa JEV | O corte não se desloca até a resposta; timeout e vencimento são eventos distintos |
| `composed_at`, `presented_at` | Cálculo e informação efetivamente exibida | Sem confirmação de apresentação, não inventar atraso visual medido |
| `human_decided_at`, `order_arrived_at` | Decisão humana e chegada à execução | Manual/observado/hipotético identificados; null se não mensurável |
| `fill_at`, `closed_at`, `label_available_at` | Parcelas e maturidade do desfecho | Rótulo exige parcela/custo/cobertura; fechamento simulado é proxy |

Latências e TTL dentro da mesma sessão usam relógio monotônico. UTC serve de referência externa; guardar deslocamento e intervalo de erro quando mensurável. Não subtrair tempos de domínios distintos sem transformação demonstrada. Para intervalos incertos, admitir um fato no replay apenas se o limite superior de disponibilidade não ultrapassa o limite inferior do corte. Comparação impossível gera `CLOCK_UNVERIFIABLE`; campos futuros dependentes ficam desconhecidos. Clock regressivo/novo motor cria nova sessão.

Quando event_at existe, ele também deve ser anterior ou igual ao corte após a transformação validada; tempo futuro/inconsistente é rejeitado. Ausência desse campo conserva a limitação e bloqueia as hipóteses que o exigem. A disponibilidade de um atributo calculado é posterior à disponibilidade de todos os seus insumos e à conclusão do cálculo. O horizonte do comparador é ancorado na formação da oportunidade; outras âncoras de apresentação/entrada são variantes distintas, versionadas antes de comparar.

Validade contextual começa no corte ancorado, não no recebimento. Prazo efetivo é o mínimo dos prazos aplicáveis, sujeito às invalidações do contrato causal. Validade não é horizonte futuro. O comparador de 2.000 ms, timeout 3 s e cadência 10 s fica registrado como tal: uma resposta aos 3 s pode estar vencida. Não ampliar validade para esconder esse custo.

## Oportunidades e execução são máquinas distintas

O gerador congelado cria `opportunity_id` por episódio/corte antes de escolher cadência. Candidatos simultâneos e consultas repetidas são filhos dessa unidade. Uma política que não consultou ou respondeu tarde continua no denominador.

Oportunidade: `created → eligible | blocked → awaiting_information → evaluated → presented | missed | expired → outcome_pending → known | unknown | censored`. Bloqueio registra motivo; etapas opcionais como apresentação ausente são explicitadas. Correções/apurações posteriores são revisões anexadas, sem modificar o que estava conhecido no corte.

Execução: `not_submitted → submitted → no_fill | partially_filled | fully_filled`; depois podem ocorrer `cancelled_remainder`, novas parcelas e `partially_closed → closed`. `unknown` é possível a partir de qualquer etapa sem prova suficiente. Cancelamento após uma parcela preserva a entrada e seu resultado; não vira ausência de execução. IDs e revisões de cada parcela impedem dupla contabilização.

`submitted` inclui pending/accepted/rejected explicitamente. `no_fill` terminal exige acompanhamento completo até rejeição/cancelamento/expiração sem parcelas; apenas “ainda sem preenchimento” permanece pending, com resultado não apurado.

| Estado demonstrado | Resultado de negociação | Patrimônio e denominador |
|---|---|---|
| Não submetida/sem entrada comprovada | Zero, se não houve despesa de negociação | Uma oportunidade; despesas de consulta registradas separadamente |
| Integral ou parcial apurada | Soma líquida de parcelas, taxas e posição remanescente apurada | Usa quantidade efetiva, não quantidade proposta |
| Cancelada com preenchimento anterior | Resultado das parcelas e liquidação restante | Não classificar como no-fill |
| Posição aberta além do horizonte | Mark-to-market/saída pelo método prévio e sua cobertura | Não presumir execução no último preço |
| Desconhecida, gap ou censurada | Null/intervalo com motivo, nunca zero presumido | Massa desconhecida e oportunidade permanecem registradas |

## OutcomeEstimate e probabilidades financeiras

Registro obrigatório: `estimate_id`, evento econômico literal, oportunidade/candidato/avaliação, janela/horizonte, quantidade solicitada e realizada, cenário de execução, origem dos preços, cobertura, classes de resultado líquido e massa desconhecida, incerteza, modelo/feature/custo/política versionados, dados de desenvolvimento e `validation_record_id`. Evento padrão de pesquisa: **resultado líquido de negociação estritamente positivo por oportunidade**, após as despesas de negociação definidas, para candidato/quantidade/regra/horizonte determinados. Despesas de pesquisa da política seguem ledger separado e entram no desempenho total.

Distribuições por quantidade devem compartilhar estados de mercado/execução coerentes. Não assumir `X(q)=q×X(1)` quando fila, liquidez, preenchimento, tarifas ou slippage dependem de q. Cada estado explicita quantidades preenchidas, parcelas, preço e custos.

Guardar `P(positivo | entrada executada)` e `P(positivo | oportunidade)` com nomes e denominadores diferentes. Se 10 oportunidades têm 6 entradas conhecidas, 3 resultados positivos, 2 não entradas conhecidas e 2 casos desconhecidos, a frequência positiva por oportunidade está entre 3/10 e 5/10; entre execuções está entre 3/8 e 5/8 se ambos os desconhecidos puderem ser entradas. O valor 3/6 descreve apenas as execuções conhecidas e não resolve os desconhecidos. Isso é um exemplo de limites, não estimativa WIN. Sem limite para as perdas desconhecidas, expectativa/log-crescimento ficam não identificáveis; não descartar a massa e renormalizar.

## Custos reconciliáveis

Os limites do exemplo anterior são limites lógicos decorrentes dos casos desconhecidos, não intervalos estatísticos de confiança. A incerteza amostral será avaliada separadamente no protocolo.

`CostRecord`: conta e moeda, componente, base por lado/contrato/volume/período, fórmula por quantidade, arredondamento, fonte documental, vigência, status `manual_unverified | verified_for_scope`, versão e parcelas já incluídas no preço. `MarginRecord` é separado: margem exigida, disponível, reserva interna e perda de estresse têm campos próprios.

Resultado líquido usa preços/quantidades efetivamente observados ou simulados, mais tarifas B3/corretagem/despesas de negociação. Spread e slippage são descontados somente quando ainda não incorporados ao preço escolhido. Consulta JEV é despesa por tentativa da política; depois da consulta já realizada é custo passado comum ao ranking, e não taxa repetida em cada alternativa. Comparar estratégias desde antes das consultas inclui todas essas despesas. Tratamento tributário é declarado no protocolo; um resultado antes de tributos não recebe rótulo de resultado após tributos.

A [página educativa B3](https://edu.b3.com.br/pt/day-trade) informa R$0,50 de entrada e saída; o comparador usa R$0,50 por lado. Nenhuma dessas informações estabelece a tarifa da conta. Preencher tabela efetiva, volume/base, arredondamento e vigência antes de confirmação; até lá são cenários experimentais. Margem R$155 permanece fixture, não contrato da corretora.

As [regras tarifárias B3](https://b3.com.br/en_us/products-and-services/fee-schedules/calculation-rules-for-listed-derivatives/) dependem de volume e arredondamentos. O registro inclui ADV, classificação day trade e consolidação aplicável; políticas com volumes diferentes podem gerar faixas próprias. Tarifa de liquidação no vencimento não é automaticamente taxa de toda saída intradiária. A reconciliação efetiva da conta está pendente, com `verified=false`.

## Comparação pareada de cadência

Fixar oportunidades, relógios disponíveis, dataset, catálogo/modelo, orçamento/limite de consultas e calendário. Braço F usa intervalo fixo congelado; braço M consulta após mudança material de candidato/premissa/geometria/janela/projeção/cobertura necessária ou vencimento, respeitando cooldown/limite congelados. Conta/custo mudado recalcula a decisão; só exige nova consulta quando altera a projeção contextual. Fonte incapaz de responder à hipótese bloqueia a consulta com motivo, sem apagar a oportunidade.

Registrar para ambos: consultas tentadas/completas, falhas, idade, descartes, cache com idade original, gastos, momento útil perdido, ausência de consulta/entrada e cobertura. Comparar utilidade líquida e risco nas mesmas oportunidades; não atribuir mudança de latência a ganho de previsão. Variar atrasos hipotéticos em sensibilidade separada dos medidos.

Separar o estudo com orçamento igual do estudo com gasto natural de cada política. Replay de consultas existentes não possui respostas contrafactuais para cortes nunca consultados: não preencher esse vazio com a resposta de outro instante. A primeira comparação pode medir somente clocks/cobertura; respostas novas exigem protocolo/orçamento.

## Capacidade de medição e aceite

| Fonte | O que pode sustentar | O que continua ausente |
|---|---|---|
| Fixtures/replay sintético | Testes de causalidade e estados; atrasos controlados | Frequência real, fila, execução humana e rentabilidade |
| Excel parcial | Campos presentes, captura local e mudanças observadas | Continuidade da fita, fila/cancelamentos e relógio de chegada à ordem sem registro próprio |
| Livro manual | Parcelas/custos informados e revisões | Sincronização externa automática ou prova independente de completude |
| ProfitDLL autorizado | Apenas capacidades demonstradas pelo SDK/contrato/captura | Licença, ABI, callbacks e integridade reais ainda não conferidos nesta rodada |

Os nove casos do ticket têm regra acima: chegada/correção tardia, resposta vencida, não entrada, parcial, gap, custo por quantidade, oportunidade perdida e latência humana não medida. O protocolo confirma parâmetros posteriormente; esta entrega não valida execução.

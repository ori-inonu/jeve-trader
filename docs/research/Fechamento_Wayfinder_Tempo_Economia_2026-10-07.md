# Pesquisa de fechamento — tempo, execução e economia

Date: 2026-10-07
Researcher: agente research_jev; consolidação documental pela sessão principal
Scope: leitura do checkout e fontes primárias; sem chamadas pagas ou alterações do aplicativo

## Estado observado

O [motor](../../app/decision_engine.py) indexa OutcomeEstimate por candidate_id, multiplica gross_points por R$0,20 e q, e usa custo linear. Há gates de validação além do booleano validated. O filtro atual encontra o melhor plano positivo, aplica teto floor(q_best × fração / (1+DD/0,30)) e reordena os que cabem. select_plan aceita qualquer ID da shortlist admissível ou espera; não é restrito a empate. O serviço ainda não integra estimativa financeira aprovada/Choice econômico. São observações do checkout desta data, sem alegação de estabilidade futura.

## Disponibilidade e execução

[Feast](https://docs.feast.dev/getting-started/concepts/point-in-time-joins) diferencia event time de disponibilidade. created_timestamp pode apenas deduplicar; filtro adicional depende da representação do instante disponível e do suporte do store. A regra deste projeto exige registrar chegada/disponibilidade de insumos, conclusão dos atributos e correções conhecidas depois do corte. Timestamp de negócio sozinho não basta.

Inferência de engenharia: registrar corte, submissão, resposta, composição, apresentação, ação humana, chegada à ordem e cada parcela com domínio/precisão/observabilidade. Monotônico serve às durações locais; cruzar relógios exige desvio demonstrado. Horizonte deve declarar âncora. Uma resposta recebida não renova validade e uma correção não retroage.

Oportunidade, consulta e execução são registros independentes. Ordem cancelada pode conter parcelas preenchidas. Falta de registro não prova no-fill; tocar preço não demonstra fila ou execução humana. Desconhecido/censurado é null ou limite, não zero. A proporção positiva com massa desconhecida admite limites lógicos, que não são intervalos estatísticos ou probabilidade calibrada. Cada frequência deve declarar se o denominador é oportunidade ou entrada.

## Reconciliação de custo

[B3 WIN](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/futuro-mini-de-ibovespa.htm) informa ponto de R$0,20 e tick de cinco pontos. [B3 Educação](https://edu.b3.com.br/pt/day-trade) apresenta R$0,50 para entrada e saída; o default examinado usa R$0,50 por lado e cinco pontos de slippage por lado, total hipotético R$3 por contrato completo. O código marca a configuração não verificada.

[Tabela de futuros](https://b3.com.br/en_us/products-and-services/fee-schedules/listed-equities-and-derivatives/equities/ibovespa-and-brazil-index-50-fees/futures-and-structured-operations/) e [regras de cálculo](https://b3.com.br/en_us/products-and-services/fee-schedules/calculation-rules-for-listed-derivatives/) usam fator do contrato, faixas de ADV, redução day trade e arredondamentos. A reconciliação exige configuração/vigência da conta e consolidação de volume aplicável. Tarifa de liquidação no vencimento não é taxa automática de qualquer saída intradiária. A página educativa não configura a conta.

Inferência: CostSchedule precisa admitir quantidade/cenário/estado tarifário, tarifas fixas ou mínimas, parcelas e custos já incorporados no preenchimento. Spread/slippage não devem ser cobrados duas vezes. Despesa JEV por tentativa pertence à política; custo já incorrido não é cobrado de novo em cada alternativa. Margem, reserva e perda de estresse são conceitos diferentes.

## Comparadores e incerteza

Para W positivo, o objetivo de pesquisa é E[log(1+X(q)/W)] nas quantidades inteiras admissíveis, incluindo zero. Cenário possível que deixa capital não positivo produz valor não finito; cenário de probabilidade zero não deve gerar cálculo indefinido. O modelo precisa produzir resultados líquidos por quantidade e cenário de preenchimento; X(q) não precisa ser qX(1).

[Sun e Boyd](https://stanford.edu/~boyd/papers/robust_kelly.html) estudam pior crescimento esperado em conjuntos de distribuições. O contrato deste projeto exige probabilidades normalizadas e relações conjuntas entre retorno, execução, latência e custo. A convexidade do problema contínuo do artigo não se transfere a contratos inteiros/custos arbitrários. Não se extrai do artigo uma fração adequada ao WIN.

O fator suave de drawdown atual não demonstra limite probabilístico de risco. [Busseti, Ryu e Boyd](https://www.web.stanford.edu/~boyd/papers/kelly.html) formulam restrições de risco sob premissas próprias. Comparar Kelly discreto, teto atual, domínio fracionado e alternativa robusta exige distinguir o objeto reduzido. Multiplicar apenas o objetivo por uma constante positiva não muda o ótimo.

## Fixture cronológico conferido

Sem JEV e sem tarifa operacional. Ambas as políticas iniciam com R$400. Quatro retornos brutos por contrato: +40, −80, +30 e −30 reais. C(q)=2q+2q²; margem=100q; estresse=80q+C(q). Restrição do fixture: margem+estresse≤W. A escolhe um contrato admissível; B escolhe a maior capacidade, que não é Kelly. Aporte R$200 após a primeira oportunidade; retirada R$100 após a segunda.

| Evento | q A | PnL A | W A | q B | PnL B | W B |
|---|---:|---:|---:|---:|---:|---:|
| Inicial | — | — | 400 | — | — | 400 |
| Oportunidade 1 | 1 | 36 | 436 | 2 | 68 | 468 |
| Aporte +200 | — | 0 | 636 | — | 0 | 668 |
| Oportunidade 2 | 1 | −84 | 552 | 3 | −264 | 404 |
| Retirada −100 | — | 0 | 452 | — | 0 | 304 |
| Oportunidade 3 | 1 | 26 | 478 | 1 | 26 | 330 |
| Oportunidade 4 | 1 | −34 | 444 | 1 | −34 | 296 |

A: 444=400+100−56. B: 296=400+100−204. R$44 acima do saldo inicial de A não são lucro: seu PnL é −56. Um contrato exige R$184 nesta restrição; R$180 admite somente zero.

Unitização proposta: v0=1, n0=W0; no fluxo F, n'=n+F/v, W'=W+F, v'=v; negociações alteram W sem alterar n. DD=1−v/max(v); pico equivalente H=n×max(v). Em fluxo, H'=H×(W+F)/W. Somar o aporte ao pico em dinheiro quando já há drawdown distorce risco. A referência de retorno ponderado pelo tempo é o [GIPS Handbook](https://www.gipsstandards.org/standards/gips-standards-for-firms/gips-standards-handbook-for-firms/); não há alegação de conformidade GIPS.

Retorno final ajustado A=−7,0706%, B=−31,1016%; máximo DD A=14,7437%, B=41,1125%. São resultados do fixture, não vantagem demonstrada em mercado. Banca não positiva/retirada integral encerra o período unitizado; recapitalização exige novo período, sem recuperação fictícia.

## Resolução e limites

Os contratos finais são [tempo e execução](../../.scratch/wayfinder-evolucao-decisao/contracts/03-tempo-execucao.md) e [dimensionamento](../../.scratch/wayfinder-evolucao-decisao/contracts/04-dimensionamento.md). Cadências usam oportunidades comuns; orçamento igual e gasto natural são comparações distintas. Replay não observa uma resposta JEV contrafactual nunca consultada.

Persistem como gates empíricos: clocks/captura real, execução/fila/latência humana, tabela da conta, distribuição por quantidade, conjunto de incerteza, dados e orçamento. Contrato definido não resolve esses gates por hipótese ou flag.

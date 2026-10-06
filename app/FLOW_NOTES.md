# Fluxo calculado e comparação de risco

## Contrato de entrada

`FlowEngine(symbol, tick_points=5)` recebe trades completos, cronológicos e com IDs estáveis:

```python
engine = FlowEngine("WINZ26")
engine.set_source_quality({
    "feed_connected": True, "sequence_ok": True,
    "full_tape": True, "data_origin": "replay",
})
engine.add_trade({
    "id": "trade-42", "symbol": "WINZ26", "ts_ms": 1801848600000,
    "price_points": "131000", "quantity": 2, "aggressor": "buy",
})
engine.set_book({
    "symbol": "WINZ26", "ts_ms": 1801848600000,
    "bids": [{"price_points": "130995", "quantity": 80}],
    "asks": [{"price_points": "131000", "quantity": 100}],
})
context = engine.snapshot(1801848600000)
```

Os métodos de ingestão retornam `accepted` e `reason`; não levantam exceção por um evento financeiro inválido. Configuração e relógio inválidos levantam `ValueError`. Dataclasses com `trade_id`, preço numérico finito e agressor `BUY/SELL/UNKNOWN` também são aceitas. Agressor desconhecido permanece desconhecido; o motor não o deduz de variação de preço.

Um snapshot de Excel ou uma tela amostrada deve declarar `full_tape=False`. O motor ainda mede os eventos visíveis, mas não converte essa amostra em confirmação de progressão, absorção ou exaustão. Alterar a flag para `True` inicia um novo período de aquecimento após o primeiro novo trade; nunca melhora retroativamente a cobertura anterior. Troca de contrato exige `reset("WINZ26")`.

`snapshot` contém `computed_features`, `observations`, `evidence_coverage` e `hypotheses`; estes campos podem entrar no estado enviado ao JEV. `bid_points`/`ask_points` ficam `None` se a cotação estiver ausente, futura ou velha. O estado é descritivo: não incorpora candidato, conta, probabilidade de lucro ou autorização de ordem.

## Cálculos e limites de interpretação

As janelas usam intervalo aberto à esquerda e fechado à direita: `(agora − 5 segundos, agora]`, `(agora − 30 segundos, agora]`, além dos 5 segundos imediatamente anteriores. Preço inicial e final são os primeiros e últimos trades dentro da janela; não se inventa preço na borda do intervalo. Volume é quantidade de contratos, delta é compra menos venda, intensidade é contratos ou trades divididos pela duração da janela. Eficiência descritiva é variação de pontos por 100 contratos com agressor conhecido; não é uma eficiência de investimento.

Progressão exige dominância de agressão e avanço de preço na mesma direção. Absorção potencial exige agressão dominante, volume mínimo e avanço pequeno ou contrário. Ela pode ter explicações concorrentes; não comprova iceberg, defesa de preço ou identidade de contraparte. Exaustão potencial exige avanço na janela anterior, desaceleração da agressão na mesma direção e ausência de continuação na atual. Uma janela anterior incompleta torna a hipótese inconclusiva.

Redução da liquidez exibida exige dois snapshots recentes com mais de um nível e a mesma grade de preços. A causa da redução permanece desconhecida: execução, cancelamento ou atualização podem produzir essa observação. Topo de book isolado, mudança da grade ou book velho não estabelece retirada de liquidez. O desequilíbrio `(quantidade bid − quantidade ask)/(quantidade bid + quantidade ask)` cobre somente os níveis visíveis e não é o indicador OFI do artigo abaixo.

As regras em `flow_rules.json` são definições experimentais e não foram calibradas no WIN. O motor mantém até 60 segundos, 10 mil trades e 256 snapshots de book por padrão, com limites máximos de configuração. Descarte por capacidade torna incompleta qualquer janela afetada. Duplicata idêntica não soma volume; ID conflitante, evento inválido, quebra de sequência e evento fora de ordem bloqueiam confirmação até reset. São rejeitados preços fora do tick, valores não finitos, timestamps/quantidades booleanos, book cruzado, níveis duplicados e quantidades inválidas.

## Simulações determinísticas

`generate_flow_scenario(mode, side="buy")` aceita `progression`, `absorption`, `exhaustion` e `choppy`. Retorna `events`, `now_ms`, `source_quality`, `symbol`, `mode` e identificação de dado sintético. Cada evento traz `type="trade"` ou `type="book"`; alimentar o método correspondente gera de fato as estatísticas, em vez de preencher números previamente escolhidos. `side="sell"` produz cenários simétricos. Nenhuma dessas simulações valida rentabilidade.

## Capital adaptativo e risco

`compare_risk_policies(config, account, candidate, now_ms)` compara, por padrão, frações de 1%, 3%, 5%, 10% e 15% sob `session_start_cap` e `current_equity`. Cada linha chama os motores existentes `evaluate_risk` e `project_stop_capacity`, preservando stop, alvo, custos e demais limites. `session_start_cap` limita a base de reinvestimento ao capital inicial da sessão; `current_equity` adapta o orçamento à equity atual, incluindo seu componente não realizado. Nenhum deles aumenta lote para recuperar perdas.

O resultado contém 10 `rows`; cada uma possui `sizing`, `allowed_contracts`, `attempts_until_policy_stop` e `trajectories`. As trajetórias incluem lotes e equity após cada perda planejada. A projeção ignora futuras oportunidades e mantém o mesmo risco por contrato; limite de cálculo aparece como `truncated_at_max_attempts`. A trajetória que ignora somente o limite de perdas consecutivas continua sendo diagnóstico hipotético, não autorização para contornar a política. Não há ranking, política ótima, estimativa de retorno futuro nem Kelly sem dados empíricos. As contas live, velhas, não conciliadas ou aritmeticamente inconsistentes continuam bloqueadas pelo motor de risco.

## Fontes conceituais

- [Nelogica — Entenda o conceito de Agressão](https://ajuda.nelogica.com.br/hc/pt-br/articles/360054997651-Entenda-o-conceito-de-Agress%C3%A3o): agressão de compra/venda consome liquidez do lado oposto.
- [Nelogica — Times & Trades](https://ajuda.nelogica.com.br/hc/pt-br/articles/360054569632-Times-Trades): negócios realizados, horário, preço, quantidade e agressão.
- [Cont, Kukanov e Stoikov — The Price Impact of Order Book Events](https://arxiv.org/abs/1011.6402): estudo de eventos de book e desequilíbrio de fluxo em ações da NYSE. Esse artigo não valida os limiares deste código nem rentabilidade em WIN.

As fontes definem dados e contexto de microestrutura; os critérios de absorção/exaustão aqui são hipóteses operacionais do projeto.

Verificação dos módulos: `python -m unittest test_flow_engine test_risk_research -v`.

## Conclusão estruturada para revisão

`recommendation_engine.build_recommendation(snapshot, candidate_report, risk_study, latest_jev_result, now_ms)` reúne contexto, geometria, avaliação JEV e risco em um resultado sem execução. Os estados são `SEM_DADOS`, `AGUARDAR`, `BLOQUEADO_RISCO` e `HIPOTESE_PARA_REVISAO`; não são uma classificação ordinal de qualidade ou rentabilidade. O retorno contém motivos, evidência faltante, contradições, opções dimensionadas e os IDs de hipóteses que podem ser examinadas por uma pessoa.

O motor recalcula `evaluate_risk` com a conta manual fornecida e mantém veto financeiro antes da consideração de apoio do modelo. Lotes previamente armazenados nunca são tomados como autorização. A geometria deve coincidir com seus dois níveis observados, buffer de um tick e oferta atual. Timestamps de tape, cotação e conta preservam seus prazos originais; uma resposta nova do JEV não renova um dado vencido. Para demonstração ou replay estático, o chamador usa explicitamente o relógio original daquele registro, com origem histórica/sintética visível.

Tape parcial mantém métricas, opções e interpretação descritiva visíveis, mas resulta em `AGUARDAR`, sem confirmar uma hipótese com cobertura integral. Uma hipótese para revisão exige cobertura completa e atual, ausência de veto financeiro, cenário de preços realmente avaliado pelo JEV e apoio contextual maior que sua contradição. Essa comparação não representa um limiar calibrado de entrada, taxa de acerto ou seleção de lucro máximo. A confiança do JEV aparece apenas como informação; não existe gate arbitrário de 0,65. Absorção e exaustão continuam sem confirmar reversão.

Conta, margem, ausência de posição e valores financeiros são pressupostos de cenário manual, não consulta à Toro. `win_probability`, `expected_return`, `ranking` e `optimal_configuration` permanecem `None`. Mesmo `HIPOTESE_PARA_REVISAO` preserva `actionable_live_signal=False` e `order_sent=False`.

Verificação da conclusão: `python -m unittest test_recommendation_engine -v`.

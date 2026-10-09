# Validade da evidência de liquidez quando a profundidade muda

Pesquisa delimitada, 2026-10-08. Resultado: defeito reproduzido na cópia congelada; recomendação para FW-07/FW-08. Este documento não implementa nem certifica a própria recomendação. A prontidão e a aceitação cabem ao coordenador e à revisão independente. Nenhuma chamada paga, ordem ou alteração no projeto principal foi feita.

## Conclusão

`FlowEngine.snapshot` pode apresentar uma redução histórica de profundidade como hipótese vigente depois que a observação mais recente contém somente topo. A seleção filtra primeiro os livros com mais de um nível e só então escolhe os dois últimos. Assim, a cobertura e a cotação descrevem o livro atual, mas a hipótese pode usar outro par, sem revelar seus timestamps. Uma cotação fresca também pode manter elegível um par de profundidade cujos dois extremos já excederam a validade de 2 s.

Os números antigos não são aritmeticamente falsos: 300 contratos exibidos passaram a 60, redução de 80%, entre 10000 e 10100. O erro é tratá-los como evidência suficiente da hipótese corrente em 10200, quando existe apenas um nível por lado e sua quantidade é 90. Quantidades de universos diferentes não são comparáveis como profundidade. Nada nesse par identifica cancelamento, execução, ordem, participante ou quantidade escondida.

## Contrato e fontes locais congeladas

Li somente os cinco arquivos da cópia isolada, os skills `codex-desktop-harness` e `research`, o contexto obrigatório do harness e as fontes oficiais abaixo. O contexto foi recuperado usando a identidade nativa efetiva, sem importar estado de outro chat; nenhuma transcrição ou estado privado foi copiado para este relatório. Metadados da tarefa ficam sob responsabilidade do coordenador.

SHA-256 dos bytes da cópia pesquisada; estes hashes não afirmam igualdade com uma árvore principal posteriormente alterada:

| Fonte relativa à cópia | SHA-256 |
|---|---|
| `app/flow_engine.py` | `5676EB1CBACC3002D9BB44E03B091B97180F26E07BA29DF3E1B00C8FB1061D72` |
| `app/test_flow_engine.py` | `6032C7DC24E52BCD7BB1D7194D0F6B9E6A85EECE987EAFE4635729BF3261FEFC` |
| `app/flow_rules.json` | `5B0C8049C6410E5DB21C4BF8C544C7F33A7FEBDB27C56A9F4A831DFB8D7C7565` |
| `app/context_cycle.py` | `F9140D89302079D03B4B349B6272D7E626991DBA5EAD4190FEF021D18854E627` |
| `.scratch/wayfinder-live-windows/spec.md` | `0183310D90DCFFFD921AC551DF12E7D2590DB55FDFB7C1E1604A7C2B22F1CED6` |

Evidência literal do contrato congelado:

- FW-07: “Fluxo local e hipóteses: agressor, cenário, fenômeno, premissa literal”.
- FW-08: “dados ausentes indisponíveis”.
- FW-04: “horários mercado/captura/recebimento separados”.
- Contrato: “dados parciais permanecem parciais. Nenhuma contratação ou chamada paga em testes.”
- FW-11: “depende de Profit/Excel e dados autorizados disponíveis”. FW-12: “sintéticos não certificam rentabilidade nem equivalem a piloto real”.

`flow_rules.json` mantém `short_window_ms=5000`, `max_age_ms=2000` e `depth_reduction_fraction_min="0.50"`; seu status é `experimental_descriptive_rules_not_calibrated_on_WIN`. A recomendação preserva esses valores e não recalibra WIN.

## Fontes primárias e alcance

1. **B3, Binary UMDF — Messaging Specification Guidelines, 2.3.1.2**, modificado em 2026-09-28. O snapshot representa estado válido para uma sequência/versão, não recupera eventos intermediários; os blocos de negócios têm semântica distinta das atualizações de livro. A especificação distingue quantidade divulgada de quantidade escondida e descreve campos explícitos para ordens/eventos. Isso sustenta o limite de inferência, não demonstra que Profit/Excel entregue esses campos ou um feed integral. Trecho literal, página impressa 56: “Any intermediary statistics (for example trades) will not be recovered.” [B3 UMDF, pp. 13, 56, 71, 84–85](https://www.b3.com.br/data/files/84/B7/1D/9E/AB611A103BBB511AAC094EA8/BinaryUMDF-MessageSpecificationGuidelines-v.2.3.1.2-enUS.pdf#page=56).

2. **B3, PUMA Trading System Timestamps, 1.1.0**, modificado em 2025-06-13. Distingue instante do evento, recebimento e envio e pontos de medição dos campos. Logo, `ts_ms` normalizado não pode ser chamado de horário de mercado sem auditoria do adaptador. [B3 timestamps, pp. 4–6](https://www.b3.com.br/data/files/F3/30/BD/D4/E1F87910C2881879AC094EA8/B3-PUMA-Timestamps-1.1.0-enUS.pdf#page=4).

3. **Nelogica, Livro de ofertas**. Diferencia aba de quantidades por preço, profundidade acumulada e Price Trader com topo; permite filtros. O relógio do cabeçalho corresponde à última negociação, não necessariamente à última alteração do livro. Isso exige auditar se a coluna capturada contém quantidade por preço ou acumulada, evitando somar acumulados como níveis independentes. Trechos literais usados para hash, separados por exatamente um LF, sem LF final:

   ```text
   Mostra o total de ofertas do ativo por faixa de preço.
   Mostra a quantidade de ofertas acumuladas por nível de preço.
   ```

   [Nelogica, Livro de ofertas, seções Preços, Profundidade, Aba Superior e Price Trader](https://ajuda.nelogica.com.br/hc/pt-br/articles/360049025732-Livro-de-ofertas).

4. **Nelogica, Livro Visual**. Permite ocultar ofertas por configuração. Inferência limitada: ausência visual pode resultar de filtragem; não prova retirada no mercado. Não foi demonstrado que a tabela Excel pesquisada siga esses filtros. Trecho literal usado para hash, sem LF final: “É possível fazer a retirada de ofertas dos níveis de preços que contenham um volume que não é significativo:” [Nelogica, Livro Visual, Aba Avançado](https://ajuda.nelogica.com.br/hc/pt-br/articles/360049032792-Livro-Visual).

5. **Nelogica, Ordens Iceberg**. Quantidade aparente pode ser inferior à real; snapshots agregados não identificam liquidez escondida. Trecho literal usado para hash, sem LF final: “uma ordem encaminhada para determinado ativo que aparenta aos outros players ser menor do que a quantidade real de contratos enviada.” [Nelogica, Ordens Iceberg](https://ajuda.nelogica.com.br/hc/pt-br/articles/360056146191-Ordens-Iceberg).

Proveniência dos hashes externos:

| Fonte | Captura e SHA-256 |
|---|---|
| B3 UMDF 2.3.1.2 | PDF, HTTP 200, 5.015.743 bytes, 2026-10-08T20:37:36.033582+00:00; `0cb7f95c9a3f6b908b51abc0309f91fd7e619475ebaf8fc95893579be19e07e0` |
| B3 timestamps 1.1.0 | PDF, HTTP 200, 502.719 bytes, 2026-10-08T20:37:35.813815+00:00; `ea863896525c1309959c55297fd8ddbe937cab537fe21083a38609479734572e` |
| Nelogica Livro de ofertas | SHA-256 somente do trecho literal UTF-8 acima: `5332e0945edc3e750dbeff59f1518b1afb734cc83bf7af2525123ca35853657f` |
| Nelogica Livro Visual | SHA-256 somente do trecho literal UTF-8 acima: `6f6a1c9709d4ba7e342d3cea7d3199b096a2cc4e526a5e866771e76f96fa4237` |
| Nelogica Ordens Iceberg | SHA-256 somente do trecho literal UTF-8 acima: `fe133d445118e20c3c7a9ce2d0607bd946e53908290a86156d17bd747057ffc1` |

Os três artigos Nelogica foram lidos pelo navegador de pesquisa em 2026-10-08; download HTTP direto retornou literalmente `HTTP Error 403: Forbidden`. Hash do HTML original é **indisponível**, não substituído pelo hash do trecho. A abertura posterior do PDF UMDF pelo navegador retornou “is not accessible via this tool”; a leitura anterior e o hash do PDF obtido com HTTP 200 permanecem evidência, sem garantia de disponibilidade futura. Não houve insistência em contornar transporte.

## Causa factual no código

Em `flow_engine.py:297–314`, `book_fresh`, preços e `depth_levels` usam `self.books[-1]`. Em `flow_engine.py:391–406`, a hipótese usa outro conjunto. Trechos literais:

```python
depth = [book for book in self.books if now_ms - self.rules["short_window_ms"] < book["ts_ms"] <= now_ms and len(book[side]) > 1]
first, last = depth[-2], depth[-1]
```

Esse filtro remove a observação intermediária ou atual de um nível antes de decidir qual par comparar. A idade dos extremos selecionados não é verificada por `max_age_ms`; só a do último livro global é. A igualdade da grade de preços já é exigida, e uma redução de três para dois níveis já retorna `DEPTH_PRICE_GRID_CHANGED`.

`set_book` aceita profundidade assimétrica e armazena apenas timestamp, bids e asks; não armazena flags de integridade por snapshot. `set_source_quality` trava `SOURCE_SEQUENCE_GAP_RESET_REQUIRED` após `sequence_ok=False`, mas desconexão/restauração de `feed_connected` não invalida o histórico de livro. Essa última é uma limitação adjacente registrada para decisão de escopo, sem propor alteração de outros fenômenos.

`context_cycle.py:76–78` copia `hypotheses` para `observed_phenomena` e copia `evidence_coverage`. A evidência incompleta pode assim alcançar o contexto do JEV; o JEV não deve preencher o que o cálculo local não observou. Não foram executados `build_context` ou APIs.

Os testes congelados verificam dois livros somente topo e uma redução seguida de grade alterada, mas não o caso deep→deep→top, topo intercalado, lados assimétricos ou extremos vencidos.

## Reprodutor público e resultado observado

Execução local: Python 3.14.7; `Windows-11-10.0.26300-SP0`. Fixtures sintéticas `WIN_SIM`, preços alinhados a 5 pontos, somente seams públicos `set_source_quality`, `set_book`, `snapshot`; nenhuma mutação de estado interno. `full_tape` continua desconhecido e não é promovido a integral. Foi usado `sys.dont_write_bytecode=True`, sem gerar arquivos de código/cache.

Executar de dentro da cópia isolada:

```python
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, "app")
from flow_engine import FlowEngine

def book(ts, qty, bids=3, asks=None, shift=0):
    asks = bids if asks is None else asks
    return {
        "symbol": "WIN_SIM", "ts_ms": ts,
        "bids": [{"price_points": str(131000 + shift - i * 5),
                  "quantity": qty} for i in range(bids)],
        "asks": [{"price_points": str(131005 + shift + i * 5),
                  "quantity": qty} for i in range(asks)],
    }

engine = FlowEngine("WIN_SIM")
engine.set_source_quality({"feed_connected": True, "sequence_ok": True})
for event in (book(10000, 100), book(10100, 20), book(10200, 90, 1)):
    assert engine.set_book(event)["accepted"]
state = engine.snapshot(10200)
print(state["quote_ts_ms"], state["evidence_coverage"]["depth_levels"])
for row in state["hypotheses"]:
    if row["kind"] == "liquidity_withdrawal":
        print(row["side"], row["status"], row["missing"], row["evidence"])
```

Saída factual essencial, ambos os lados:

```json
{"quote_ts":10200,"book_fresh":true,"depth_levels":{"bids":1,"asks":1},"integrity_ok":true,"hypotheses":[{"side":"bids","status":"potential","missing":[],"fraction":"0.8"},{"side":"asks","status":"potential","missing":[],"fraction":"0.8"}]}
```

Casos adicionais executados em engines novas, todos os livros aceitos. `D3(10000,100)` significa três níveis, cada qual com quantidade 100; `T` significa um nível. Grade igual salvo onde declarado. Sem operações de fonte, flags connected/sequence são `True`.

| Caso e sequência | Corte | Resultado congelado | Oráculo conservador proposto |
|---|---:|---|---|
| `D3(10000,100) → D3(10100,20) → T(10200,90)` | 10200 | ambos `potential`, `0.8`, sem missing | ambos inconclusivos; topo atual não demonstra profundidade |
| `D3(10000,100) → T(10100,90) → D3(10200,20)` | 10200 | ambos `potential`, `0.8`, sem missing | inconclusivo até segundo profundo consecutivo |
| Caso anterior + `D3(10300,10)` | 10300 | ambos `potential`, `0.5` | par 10200→10300, totais 60→30, redução 0.5 |
| `D3(10000,100) → D3(10100,20) → bids1/asks3(10200,10)` | 10200 | bids `potential/0.8`; asks `potential/0.5` | bids inconclusivo; asks par atual 10100→10200, 60→30 |
| `D3(10000,100) → D3(10100,20) → T(14000,90)` | 14000 | ambos `potential/0.8`; book fresh | inconclusivo; par antigo tem idades 4000/3900 ms |
| `D3(10000,100) → D3(13000,20)` | 13000 | ambos `potential/0.8`; book fresh | inconclusivo; primeiro extremo tem 3000 ms |
| `D3(10000,100) → D3(10100,20)`, grade +5 pontos no segundo | 10100 | ambos inconclusivos, `DEPTH_PRICE_GRID_CHANGED`, fração null | preservar bloqueio, sem completar preços ausentes |
| `D3(10000,100) → D2(10100,20)` | 10100 | mesmo bloqueio de grade, fração null | não tratar níveis ausentes como quantidade zero |
| `D3(10000,100) → D3(10100,20)` | 12101 | ambos inconclusivos, `DEPTH_SEQUENCE_REQUIRED`, fração `0.8`; book stale | indisponível, sem cotação fresca artificial |
| `D3(10000,100) → D3(10100,50)` | 10100 | ambos `potential/0.5` | preservar limiar inclusivo: 300→150 |
| `D3(10000,100) → D3(10100,60)` | 10100 | ambos `not_observed/0.4` | preservar: 300→180 não cruza limiar |
| `D3(10000,20) → D3(10100,30)` | 10100 | ambos `not_observed/-0.5` | preservar: 60→90 é aumento |
| Par válido, depois `feed_connected=False` | 10100 | inconclusivo, `SOURCE_INTEGRITY_NOT_VERIFIED`, fração `0.8` | manter indisponibilidade atual |
| Par válido, depois sequence false→true | 10100 | inconclusivo, `SOURCE_SEQUENCE_GAP_RESET_REQUIRED` | manter trava até reset explícito |
| Par válido, depois feed false→true sem novo livro | 10100 | ambos `potential/0.8`, sem missing | flags atuais não provam integridade histórica; decidir fronteira de recuperação separadamente |

O oráculo usa aritmética independente: `(Q_antes-Q_depois)/Q_antes`. O objetivo não é retirar um registro histórico correto, mas impedir que ele substitua evidência atual ausente. Não executar inferência de volume oculto nem estimar transações intermediárias para resolver o vazio.

## Requisitos e aceitação candidata, limitados a FW-07/FW-08

1. **Par atual por lado:** selecionar primeiro as duas observações de livro aceitas mais recentes, em ordem cronológica, e depois verificar elegibilidade daquele lado. Não saltar observação somente topo para fabricar sequência de profundidade. Ambos os extremos devem ter mais de um nível naquele lado e grade de preços idêntica. Não exigir igual número de níveis entre bids e asks.
2. **Validade dos extremos:** ambos precisam estar dentro da janela já existente e ter idade não negativa e ≤ `max_age_ms` existente. A idade do último livro ou da cotação não substitui a idade de cada extremo. No limite 2000 ms, manter elegibilidade; em 2001 ms, indisponível. Esses casos de fronteira são critérios para a execução independente futura, não resultados de teste da correção.
3. **Evidência explícita:** anexar timestamps normalizados dos dois extremos, corte/idades, nível e total por extremo, lado e escopo exibido. Identificar o instante do livro atual separadamente quando necessário. Não rotular `ts_ms` como tempo de mercado sem contrato auditado. Valores financeiros permanecem strings/inteiros determinísticos conforme schema.
4. **Falta de evidência:** hipótese inconclusiva com razão explícita quando topo, sequência, grade, idade ou integridade não permitem o par. Para impedir reaproveitamento acidental, recomendar fração null para par inelegível; um dado histórico, se mantido, precisa de seção/escopo histórico explícito. Não transformar missing em zero nem em `not_observed`.
5. **Recuperação e preservação:** dois profundos atuais consecutivos restauram a comparação por lado. Grade alterada só é comparável após novo par na mesma grade. Preservar falhas travadas, resets, ordem temporal e rejeições existentes; flags não verificadas continuam bloqueando. Não mudar tape, absorção, exaustão, thresholds ou políticas de alerta neste incremento.
6. **Aceitação independente:** os quatro primeiros casos da tabela, pares vencidos, mudança de grade/níveis e controles 0.5/0.4/-0.5 devem ser avaliados pelo seam público por executor/revisor distinto. Os metadados devem conferir com entradas literais, sem deduzir timestamps pelo valor da fração. Nenhum resultado sintético encerra FW-06, FW-11 ou FW-12.

A política de desconexão/restauração sem novo snapshot é uma limitação factual adjacente. Tornar snapshots portadores de proveniência ou exigir geração de fonte nova teria impacto além da seleção do par. Não certificar recuperação histórica pelo valor atual das flags e não incluir uma política nova silenciosamente neste conserto.

## Alternativas reais

| Alternativa | Ganho e custo | Decisão recomendada |
|---|---|---|
| Par atual consecutivo, válido por lado | Conservador, local e reversível; pode perder oportunidades de descrição durante alternância de topo/profundidade | Recomendada para hipótese vigente em FW-07/FW-08 |
| Par profundo histórico com timestamps/idade próprios e rótulo histórico | Preserva descrição passada; exige apresentar vigência distinta e impede usar quote fresco como renovação | Adiar: precisa contrato explícito de apresentação/consumo histórico |
| Interseção dos preços presentes nos dois snapshots | Possibilita métrica de sobreposição; muda universo, pode ocultar perda de cobertura e altera a semântica da fração | Não usar como substituto; eventual métrica separada requer especificação própria |

## Não objetivos e desconhecidos

Sem implantação, calibração, ordens, contratação/feed pago, JEV consultivo, inferência de cancelamento/execução, identificação de ordem/participante, iceberg detectado ou probabilidade de lucro. Nenhuma afirmação de performance visual ou rentabilidade.

Ainda desconhecidos: fórmulas e origem real das colunas Excel; quantidade independente versus acumulada; timestamp do adaptador e sua relação com mercado/captura/recebimento; seleção/filtros/rolagem; perda de snapshots; reinício de fonte; comportamento real durante rajadas. Um par de snapshots consecutivos na memória não prova continuidade do feed, identidade de ordens ou ausência de eventos entre eles. O piloto Windows Profit/Excel e a avaliação contextual independente permanecem necessários nas fronteiras FW-06/FW-11/FW-12.

Pergunta da pesquisa respondida: profundidade ausente ou vencida não sustenta hipótese vigente de redução de liquidez; a elegibilidade deve pertencer ao par explicitamente comparado e ao lado observado. Pesquisa encerrada neste limite, aguardando implementação e verificação independentes.

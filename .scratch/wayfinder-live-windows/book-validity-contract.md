# Evidência atual de liquidez — contrato do incremento

Status: ready (2026-10-08). Derivado de FW-07/FW-08, sem substituir os critérios congelados. Pesquisa e revisão independente do delta concluídas antes da implementação.

## Objetivo e origem

Corrigir a mistura entre livro atual e comparações antigas quando a profundidade disponível diminui. O pedido humano continua sendo melhorar a interpretação de fluxo WIN pelo JEV. A baseline 6839d9c reproduz uma hipótese `potential` de redução `0.8` com um livro atual de apenas um nível; [Validade da evidência de liquidez quando a profundidade muda](issues/07-validade-liquidez.md) conserva a investigação. O comportamento será descritivo; dois snapshots não identificam cancelamentos, consumo, reposição ou liquidez oculta.

## Escopo e limites

`FlowEngine.set_book` → `FlowEngine.snapshot` e `build_context` são as fronteiras públicas já adotadas pelo plano aprovado e pelo incremento anterior. Não haverá novos feeds, perguntas pagas, aprendizado de modelo, alteração de limiares, lote, ordens ou cobertura da fonte. Choice e os Nouls de apoio/contradição/insuficiência continuam independentes sobre o mesmo estado. FW-06/FW-11/FW-12 permanecem abertos. Instalação ou testes sintéticos não os encerram.

## Aceites imutáveis do incremento

- **LB-01 — Par vigente.** Para cada lado, comparar somente os dois últimos snapshots aceitos, consecutivos na sequência observada e dentro da janela curta de 5 s. Não filtrar previamente os snapshots com um nível para procurar um par profundo antigo. Os dois precisam ter mais de um nível nesse lado e a mesma lista ordenada de preços. O último precisa ser o livro atual. Ambos os extremos precisam ter idade não negativa e ≤ 2000 ms, usando o limite existente. Falta de par/profundidade resulta em `inconclusive`, `DEPTH_SEQUENCE_REQUIRED` e fração indisponível; mudança de grade conserva `DEPTH_PRICE_GRID_CHANGED`. Extremo vencido acrescenta `BOOK_COMPARISON_EXPIRED` e deixa a fração indisponível.
- **LB-02 — Independência dos lados.** A perda de profundidade em bids não invalida uma comparação válida de asks, nem o inverso. Um snapshot de topo entre dois profundos interrompe aquele par: uma primeira recuperação profunda continua inconclusiva; dois novos snapshots profundos comparáveis recuperam a avaliação. Nenhuma qualidade anterior é reaproveitada para preencher campos ausentes.
- **LB-03 — Tempo e escopo.** Cada hipótese de liquidez inclui o intervalo observado: timestamps antes/depois, duração em ms, idade do último no corte e quantidade de níveis de cada snapshot. Indisponíveis são `null`. O escopo literal é `consecutive_observed_snapshots`, que não certifica continuidade completa do feed. O cálculo válido 3×100 → 3×20 entrega fração decimal textual `0.8`; uma quantidade maior entrega fração negativa e `not_observed`. Não acrescentar ID de ordem, causa de redução ou posição de investidor.
- **LB-04 — Qualidade.** Livro vencido, fonte desconectada, sequência não verificada ou falha de integridade mantêm a hipótese inconclusiva. Cotação/tape recentes não renovam o livro nem os timestamps de comparação. O intervalo anterior pode ser preservado como evidência histórica quando o livro vence, acompanhado da idade e insuficiência; jamais vira hipótese vigente. Os bloqueios existentes permanecem.
- **LB-05 — Estado contextual.** O estado comum entregue ao JEV preserva os timestamps, a limitação de profundidade e `missing` da hipótese. Uma explicação literal distingue a redução exibida entre os últimos snapshots observados de cancelamento/execução/absorção comprovados. Mudança semântica recebe nova versão de pergunta. Mesma Choice, mesmos Nouls, sem novos envios HTTP, sem resposta simulada apresentada como real e sem leitura de respostas entre perguntas.
- **LB-06 — Verificação e revisão.** TDD em cópia isolada pelo implementador: reproduzir a falha antes da correção e manter oráculos numéricos independentes para ambos os lados, recuperação e idade. Revisões independentes em cópias hash-verificadas cobrem especificação e padrões; o integrador aplica apenas arquivos exclusivos. Executar verificações Python e frontend pertinentes, registrar plataforma e limites. Preservar configurações/diário e alterações de outro chat.

## Casos anotados locais

Os casos são sintéticos e avaliam coerência do motor, sem validar rentabilidade ou a interpretação real do JEV:

1. 10000 ms: 3 níveis ×100; 10100: 3×20; 10200: 1×90. Resultado atual de cada lado: inconclusivo, fração null, comparação 10100→10200 (100 ms), níveis 3→1.
2. Acrescentar 10300: 3×10. Resultado: inconclusivo, sem pular 10200. Acrescentar 10400: 3×5. Resultado: potencial, `0.5`, comparação 10300→10400, idade 0.
3. Último snapshot com um nível apenas em bids, asks 3×10 após asks 3×20. Bids inconclusivo; asks potencial `0.5`.
4. Par válido 10000→10100, corte 12200. Resultado inconclusivo, idade 2100 ms. Eventos de tape recentes não mudam a idade do livro.
5. Grade de preços alterada, mesma quantidade/contagem: inconclusivo com `DEPTH_PRICE_GRID_CHANGED`, sem redução inferida. Fonte com sequência não verificada: inconclusivo mesmo com par numericamente comparável.
6. Par profundo 10000→13000, corte 13000: inconclusivo, idade do primeiro 3000 ms mesmo com último fresco. Par 10000→11000 no corte 12000: válido no limite 2000 ms; no corte 12001: inconclusivo, sem renovar idade por tape novo.

## Clarificações de schema e preservação

`evidence.comparison` inclui `scope`, `before_ts_ms`, `after_ts_ms`, `elapsed_ms`, `before_age_ms`, `after_age_ms`, `before_depth_levels` e `after_depth_levels`. O escopo é `consecutive_observed_snapshots`; os campos desconhecidos ficam null. A escolha do par precede toda filtragem por lado. Preservar `descriptive_only=true`, `future_profit_probability=null`, `actionable_live_signal=false`, `strategy_validated=false` e `win_probability=null`.

A pesquisa independente reproduziu e documentou o defeito e a validade dos extremos em `book-validity-research.md` (SHA-256 `eb2f2fb103df03512a661f28bee3cc442b2f69966932f41eea2267559b3540d7`). A revisão independente do delta decidiu `READY_WITHOUT_BLOCKERS` em `.artifacts/flow-book-research-20261008/spec-review/workspace/spec-readiness-delta-review.md` (SHA-256 `b616b1c788a4a1cb360106b1396abb8f65c0e5e61ea577e99fdd550f25a812f5`), sobre os aceites deste contrato antes da alteração exclusiva de status e registro. Desconexão/restauração sem novo livro permanece uma limitação adjacente, sem introduzir nova política de geração de fonte neste incremento.

## Ownership

Pesquisa e revisores escrevem somente relatórios em suas cópias isoladas. Implementador: `app/flow_engine.py` e novo `app/test_flow_book_validity.py` em cópia isolada. Integrador principal: `app/context_cycle.py`, teste público contextual e este contrato/ticket/evidências. Ninguém edita documentos de outro chat. A prontidão da especificação não comprova implementação, captura real ou qualidade do JEV.

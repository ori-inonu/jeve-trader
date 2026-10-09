# Contrato resolvido — identidade causal

Date: 2026-10-07
Version: causal-identity-v1
State: specified; software_not_implemented
Ticket: [Identidade causal da decisão](../issues/01-identidade-causal.md)

## Decisão e alcance

Usar identidade de conteúdo para candidato e snapshot, UUID para tentativa e sessão, e registros imutáveis para entradas e respostas. IDs de apresentação continuam disponíveis. Nenhum índice de lista participa da associação. A decisão aponta para a avaliação aceita; uma decisão de espera tem `selected_candidate_key=null`, podendo expor alternativas identificadas separadamente.

É uma decisão de engenharia. A observação do serviço atual — aceitação parcial e extração por `candidate_0` — está no [complemento datado](../../../docs/research/Complemento_Wayfinder_JEV_WIN_2026-10-07.md). Não foi reproduzido um erro na janela Windows.

## Campos obrigatórios e fronteiras

| Registro | Campos e significado |
|---|---|
| `MarketSnapshot` | `schema_version`, `snapshot_key`, `engine_session_id`, `market_session_id`, `instrument_contract`, `source_id`, `source_generation`, `sequence`, `cut_at`, `clock_domain`, `coverage_version`, `coverage`, `evidence_refs`, `computed_features`, `feature_derivation_version`, `context_projection_hash`. O hash identifica a projeção exata enviada ao JEV, incluindo transformações. A sequência ordena apenas dentro da sessão do motor. |
| `EvidenceRevision` | `evidence_id`, `revision`, `payload_hash`, `source_id`, `event_at` conhecido ou null, `captured_at`, `available_at`, `clock_domain`, `quality`, `supersedes_revision` ou null. Uma correção é outra revisão. |
| `CandidateSpec` | `candidate_key`, `display_id`, `instrument_contract`, `market_session_id`, `generator_version`, `hypothesis_id`, `hypothesis_version`, `literal_premise`, `family`, `side`, `entry_ticks`, `stop_ticks`, `target_ticks`, `tick_points`, `observation_start`, `observation_end`, `horizon_ms`, `entry_rule_version`, `exit_rule_version`, referências de evidência com revisão e hash. |
| `ContextRequest` | `request_id`, sessão, `candidate_keys`, `snapshot_key`, `context_projection_hash`, `evidence_bundle_hash`, `question_set_hash`, `question_version`, `model_requested`, `submitted_at`, `deadline_at`, `validity_rule_version`, bindings imutáveis pergunta → candidato/dimensão. Um batch pode conter vários candidatos; cada Evaluation pertence a um candidato. Exclui conta e custo do documento contextual. |
| `ContextResponse` | `response_id`, `request_id`, hash e bytes originais da resposta, `model_returned`, `received_at`, resultado tipado por pergunta, referência ao erro quando houver. Não altera o pedido. |
| `Evaluation` | `evaluation_id`, `candidate_key`, `snapshot_key`, pedido e resposta ou erro, hashes/versionamento da semântica e validade, corte causal. Materializada ao completar a tentativa; classificações posteriores são eventos separados. |
| `DecisionPlan` | `decision_id`, avaliação ou motivo explícito de ausência, `selected_candidate_key`, `quantity`, `account_revision`, `cost_version`, `risk_policy_version`, `outcome_estimate_id` ou null, `composed_at`, `effective_expires_at`, `reason_codes`, `mode`. Preços e quantidades são calculados pelo motor. |

Campos obrigatórios ausentes não são preenchidos por defaults implícitos. Timestamps disponíveis usam o contrato de [tempo e execução](03-tempo-execucao.md). Estado atual é uma projeção dos registros e eventos; não se reescreve a avaliação original para fazê-la parecer atual.

## Representação canônica

Usar SHA-256 dos bytes UTF-8 canônicos com prefixo de domínio: `jev:candidate:causal-identity-v1\n`, `jev:snapshot:causal-identity-v1\n` ou `jev:questions:causal-identity-v1\n`. O prefixo pertence aos bytes, não ao JSON. O hash identifica conteúdo; não autentica uma fonte nem concede autorização.

Aplicar [JCS, RFC 8785](https://www.rfc-editor.org/rfc/rfc8785): chaves sem duplicatas, ordenação determinística, sem espaços externos e strings Unicode preservadas. Não normalizar, traduzir, aparar nem alterar a premissa depois da construção. Rejeitar Unicode inválido, NaN e infinitos. Guardar o documento original separado dos bytes canônicos.

Para evitar divergência de precisão, valores financeiros/preços não usam floats: BRL em centavos inteiros representados por string; preço em número inteiro de ticks representado por string, com `tick_points` decimal canônico em string; horários/durações em milissegundos inteiros em string. Inteiros não têm sinal `+`, zeros iniciais ou `-0`. Decimal canônico não usa notação exponencial e remove zeros fracionários finais. Números recebidos são validados em Decimal antes dessa conversão; arredondamento não é uma forma de validar preço fora do grid.

Listas que representam conjuntos de evidência são ordenadas por `(evidence_id, revision, payload_hash)`, sem duplicatas. Listas semanticamente ordenadas — regras, opções de Choice e argumentos — conservam ordem. `display_id`, posição visual e quantidade desejada pela pessoa ficam fora do hash do candidato; quantidade efetiva, conta e custos pertencem à decisão. Horizonte, janela, versão e regra de entrada/saída ficam dentro. Cada representação inclui sua versão de schema.

O próprio campo de identidade calculada (`candidate_key`, `snapshot_key` ou `question_set_hash`) fica fora de seu preimage; as identidades de dependências permanecem dentro. Instrumento e sessão de mercado fazem parte do candidato. A ordenação do conjunto usa as strings canônicas em ordem lexicográfica. Novo corte de janela rolante produz nova identidade; uma resposta anterior só é reutilizável para a mesma janela ancorada e a mesma projeção. Mudança da derivação ou da projeção contextual invalida a associação com `CONTEXT_PROJECTION_CHANGED`. Dados novos fora dessa projeção não podem ser apresentados como se tivessem sido avaliados.

Vetor mínimo de serialização: o objeto `{"side":"buy","entry_ticks":"20000"}` produz exatamente `{"entry_ticks":"20000","side":"buy"}` antes do prefixo. Consumidores React usam as identidades produzidas pelo motor, sem inventar uma segunda identidade.

Vetor completo fictício, com referências de hash artificiais para testar a codificação; horários relativos à simulação, não timestamps de mercado:

```json
{"entry_rule_version":"manual-v1","entry_ticks":"20000","evidence_refs":[{"evidence_id":"e1","payload_hash":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","revision":"1"},{"evidence_id":"e2","payload_hash":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","revision":"1"}],"exit_rule_version":"stop-target-horizon-v1","family":"continuation","generator_version":"geometry-v1","horizon_ms":"60000","hypothesis_id":"buy-continuation","hypothesis_version":"continuation-v2","instrument_contract":"WIN-fixture","literal_premise":"Recent aggressive buying is accepted at higher prices.","market_session_id":"fixture-session-1","observation_end":"30000","observation_start":"0","schema_version":"causal-identity-v1","side":"buy","stop_ticks":"19980","target_ticks":"20040","tick_points":"5"}
```

SHA-256 com o prefixo definido: `e76a9bc939f018fd8ed4dc451f2026384ef8a1f922227d8a410f7b2c9ea9c38c`. Trocar somente `stop_ticks` para `19979` produz `ce81c0317d1527358666cd404875879f923c9c1781ff5caea3488504de1b84b5`; trocar somente `horizon_ms` para `120000` produz `8bc0bd9cd3e9916cdc9821671e5aba8b2b65405feb6d922e68724fcf5eefb15b`. Reordenar as chaves conserva o primeiro digest. Esses três checks foram reproduzidos com Python `-B` em 07/10/2026, sem importar o aplicativo. O vetor usa apenas chaves ASCII e strings; não comprova uma implementação geral de JCS ou aceitação de referências de mercado.

## Compatibilidade e vigência

A aceitação exige conjunção das verificações abaixo. Uma nova leitura do cache não modifica `available_at`, corte, expiração ou versão. Validade efetiva é o menor prazo entre fonte, hipótese, pedido e plano, mais as invalidações por evento. Um prazo desconhecido necessário impede estado vigente. Resposta recebida após o prazo continua registrada.

| Mudança desde a submissão | Contexto | Decisão financeira | Motivo |
|---|---|---|---|
| Reordenar A/B, conteúdo idêntico | Mesma associação por chave | Pode manter-se se demais condições iguais | nenhum |
| ID textual reutilizado; premissa/geometria/janela/horizonte/regra mudou | Histórico incompatível | Recalcular | `CANDIDATE_CONTENT_CHANGED` |
| Evidência corrigida, removida ou hash diferente | Incompatível com o bundle atual | Reavaliar | `EVIDENCE_REVISION_CHANGED` / `EVIDENCE_REFERENCE_MISSING` |
| Fonte/geração, contrato ou sessão de mercado mudou | Incompatível | Reavaliar | `SOURCE_GENERATION_CHANGED` / `MARKET_SCOPE_CHANGED` |
| Perda de cobertura requerida | Não vigente | Espera | `REQUIRED_COVERAGE_LOST` |
| Conta ou custo mudou; semântica contextual idêntica | Reutilização contextual possível enquanto válida | **Nova decisão** com versões novas | `ACCOUNT_REVISION_CHANGED` / `COST_VERSION_CHANGED` |
| Pergunta, opções, catálogo ou modelo mudou | Incompatível | Reavaliar | `QUESTION_CONTRACT_CHANGED` / `MODEL_MISMATCH` |
| Projeção calculada ou sua versão mudou | Incompatível | Reavaliar | `CONTEXT_PROJECTION_CHANGED` |
| Prazo ultrapassado | Vencido | Espera/reavaliação | `EVALUATION_EXPIRED` |
| Nova sessão do motor, sequência reiniciada | Somente histórico da sessão anterior | Nova avaliação | `ENGINE_SESSION_CHANGED` |
| Resposta malformada/referência inexistente/relógio necessário ausente | Falha | Espera | `RESPONSE_SCHEMA_INVALID` / `EVIDENCE_REFERENCE_MISSING` / `CLOCK_UNVERIFIABLE` |

Reutilização contextual por mudança de conta/custo cria uma **nova avaliação derivada**, apontando à resposta original, sem renovação do prazo. Exige candidato, bundle, perguntas, modelo, sessão e validade idênticos. É proibida entre sessões do motor no primeiro contrato; eventual reaproveitamento entre sessões exige contrato novo. Mudança de política mantém contexto quando seu documento não muda, mas cria nova decisão. Qualquer revisão desconhecida falha de forma explícita.

Classificações: `active`, `superseded`, `expired`, `incompatible`, `failed`. `pending` descreve tentativa sem resposta, não avaliação válida. Um registro pode acumular vários motivos; preservar todos, exibindo primeiro falha estrutural, depois incompatibilidade e expiração. Revalidar para cada uso. Não há transição que ressuscite uma avaliação vencida.

## Exemplos e histórico esperado

Exemplo fictício: pedido R1 contém perguntas `p1→A:a1`, `p2→B:b1`, sendo `a1/b1` hashes completos abreviados. Após reordenar `[B,A]`, R1 recebido ainda preenche `context_by_candidate[a1]` e `[b1]`; o índice não é reinterpretado. Uma decisão de B aponta a `b1/evalB`. A espera aponta a null; um painel aberto de A diz “Alternativa A — avaliação evalA”.

Se `display_id=A` passa de stop 99.900 para 99.895, cria `a2≠a1`. R1 fica `incompatible/CANDIDATE_CONTENT_CHANGED`; o histórico guarda R1/a1 e sua geometria. Se apenas custo C1 passa a C2, a resposta contextual de a1 ainda pode ser válida: D1/C1 fica substituída, E2 deriva de E1 com prazo original e D2 aponta C2. D1 nunca é reapresentada como D2.

Pedido às 10:00:00, deadline às 10:00:02, resposta às 10:00:03: guardar resultado com `EVALUATION_EXPIRED`. Cache às 10:00:04 continua vencido. Reinício em sessão S2 com sequência 1 não aceita avaliação de S1, mesmo que todos os preços coincidam. Correção de evidência e7/r2 às 10:01 mantém e7/r1 no passado; novo snapshot/eval usa r2 somente após sua disponibilidade.

## Aceite documental e transferência

Campos e separações estão na tabela; codificação e precisão na representação; todos os oito casos do ticket aparecem na matriz e exemplos. A implementação deverá verificar troca de candidato, custos durante consulta, expiração, cache, reinício, revisões, campos ausentes e projeção histórica com relógio controlado. Nenhum desses testes de aplicativo foi executado nesta rodada.

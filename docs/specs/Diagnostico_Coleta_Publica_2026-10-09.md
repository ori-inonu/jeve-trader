# EM-03 — diagnóstico causal da coleta pública

Status: especificação candidata; implementação ainda não iniciada.
Baseline: `3e2bfec012512582859bee69e9edae76fb70aabf`. Continuação do plano EM-03 em `docs/implementation/Multimercado_2026-10-09.md`, dentro do recorte observador de `Implementacao_Multimercado_2026-10-09.md`.

## Objetivo e fronteira

Distinguir falha de sincronização, erro remoto e fechamento local, preservando a cadeia causal antes que a invalidação do livro ou o shutdown substitua o motivo. Os três ensaios públicos anteriores falharam; a causa original continua desconhecida. Repetir um ensaio genérico para procurar um resultado saudável permanece em quarentena.

Esta entrega acrescenta instrumentação e um ensaio diagnóstico finito, condicionado à verificação offline. Não modifica a política de ponte `U <= S <= u`, a continuidade subsequente, os limites de conexão/retry ou as regras financeiras. Não habilita ordens, novos mercados, retenção de payloads ou probabilidade de lucro. Uma falha observada deve continuar invalidando os dados; diagnosticar não significa validar a coleta.

## Requisitos e aceites imutáveis

| ID | Evento/condição e comportamento observável | Verificação |
|---|---|---|
| DI-01 | Diagnóstico desligado por padrão: nenhuma captura adicional, rede, arquivo ou saída de histórico. Habilitação explícita permite somente metadados de sequência/lifecycle por accessor dedicado. | Fakes/spy comprovam default e import offline; CLI sem flag mantém contrato existente. |
| DI-02 | Snapshot, decisão da ponte, delta rejeitado, falha da tentativa, erro do reader e pedido de fechamento local deixam metadados sanitizados. Registrar `S`, `U/u`, último ID aplicado, tentativa, relógio monotônico local, estado/motivo do livro antes da invalidação e indicador de fechamento local quando pertinentes. Ausência de informação fica `null`. | Fakes reproduzem snapshot atrás do buffer, gap subsequente, erro remoto genuíno e encerramento local; IDs e motivos correspondem aos eventos realmente executados. |
| DI-03 | A primeira falha causal da sessão fica preservada separadamente, inclusive após retry/stop e evicção do histórico. Fechamento local não se promove a erro remoto causal. O diagnóstico descreve evidência e não inventa causa quando os metadados forem insuficientes. | Regressões distinguem gap→close de erro remoto→close e preservam o primeiro motivo após shutdown/reconexão. |
| DI-04 | Histórico em memória limitado a 64 eventos e saída completa do accessor limitada a 16384 bytes UTF-8 de JSON canônico. Evicção/perda fica contada. Limites são de bytes serializados e contagem, sem afirmar limite de RSS. Contabilizar a memória diagnóstica no budget gerenciado existente. | Teste de saturação comprova ambos os limites, contador e preservação da primeira falha; snapshots retornados não permitem alterar o estado interno. |
| DI-05 | Schema de saída fechado: enums conhecidos, booleanos, IDs inteiros limitados, contadores e relógio monotônico. Nunca exportar preços, quantidades, corpos REST/WS, mensagens livres de exceção, URLs, headers, credenciais, caminhos privados ou dados pessoais. Sem persistência automática. | Injetar sentinelas sensíveis nos erros/payloads e verificar ausência na saída serializada; valores inválidos não escapam da allowlist. |
| DI-06 | CLI `--diagnostic-sequence` habilita accessor e conserva diagnóstico final após stop; duração/live continuam explícitos e limitados. Serviço/UI comuns permanecem sem histórico. Shutdown com helper vivo continua visível e impede sucesso/restart. | Testes CLI/observer com fakes; falha live continua exit não zero; modo offline não abre fonte. |
| DI-07 | Somente após DI-01–06 verificados, um ensaio público de até 20 segundos pode investigar a hipótese causal com estes metadados. Registrar versão, comando, plataforma, resultado e classificação ou insuficiência de evidência, sem payloads. Não repetir para obter sucesso; não declarar estabilidade/rentabilidade/AC-07. | Evidência sanitizada de execução real e revisão independente. Se dependência externa impedir o ensaio, registrar bloqueio exato e concluir apenas a instrumentação demonstrada. |

## Divisão e ownership

Integrador: esta SPEC, proposta/estado SDD, documentação canônica, evidência e PR. Implementador único em workspace isolado: `app/public_crypto_feed.py`, `app/multimarket_observer.py`, `scripts/observe_multimarket.py` e testes focados desses componentes. Não alterar arquivos de contratos, replay, economia, UI, política de sequência ou suites congeladas. Revisores independentes usam cópia isolada e baseline fixo.

TDD: executar regressões novas em RED, implementar o mínimo, GREEN focado e verificação global pertinente. Não chamar fonte pública/JEV pago em testes ou setup. Depois da integração, dois eixos independentes revisam o novo candidato. Documentos distinguem instrumentação entregue, diagnóstico real, coleta estável e evidência financeira.

## Decisão consultiva

Jev Workflows recomendou accessor opt-in, preservação no observer e flag CLI, com recibo persistido `c3d3bec7-7c46-4742-9ecf-87cac253fe44` (2026-10-09). A recomendação é consultiva; os gates determinísticos permanecem locais. Custo faturado desconhecido: `null`.

## Contrato fechado de saída — DI-02/04/05

Esclarecimento da SPEC candidata após revisão documental; DI-01–07 acima permanecem iguais. Este contrato exige nova vinculação da proposta e do parecer de escopo antes de congelar ou implementar. Jev Workflows recomendou este apêndice no recibo `0e90898a-b05e-454a-93fb-ff5a41efacd8`; a decisão continua consultiva.

Com diagnóstico desligado, o accessor retorna `null`, sem capturar eventos. Quando habilitado, a saída tem exatamente as chaves `enabled` (sempre `true`), `events` (lista), `first_failure` (evento ou `null`), `dropped_events` (contador) e `metadata_complete` (booleano). `first_failure=null` significa que nenhuma falha causal foi capturada; não prova coleta saudável. Nenhuma outra chave é admitida.

Cada evento tem exatamente estas chaves:

| Chave | Tipo e domínio |
|---|---|
| `kind` | Enum: `snapshot`, `bridge`, `delta_rejected`, `attempt_failure`, `reader_error`, `local_close_requested`. |
| `attempt` | Inteiro 1–12, ou `null` quando desconhecido. O limite segue o teto existente de tentativas. |
| `monotonic_ns` | Inteiro em nanossegundos do relógio monotônico local, 0–9223372036854775807, ou `null`. Não é relógio da venue nem latência de rede. |
| `snapshot_id`, `first_update_id`, `last_update_id`, `last_applied_id` | Inteiro 0–9223372036854775807, ou `null` se ausente, inválido ou fora da faixa. Correspondem a `S`, `U`, `u` e último ID realmente aplicado. |
| `book_state` | Enum: `cold`, `syncing`, `live`, `invalid`, `unknown`. Sem estado conhecido, usar `unknown`. |
| `reason` | Enum fechado abaixo, ou `null` quando não há motivo. Capturar o motivo pertinente antes da invalidação; não interpolar exceção livre. |
| `local_close` | Booleano que indica pedido local de fechamento; não classifica sozinho erro remoto. |
| `metadata_complete` | Booleano; `false` quando algum metadado pertinente era desconhecido ou foi descartado por validação. Ausência não pertinente mantém `null` sem inventar valor. |

Valores permitidos de `reason`: `unknown`, `awaiting_snapshot`, `snapshot_behind_buffer`, `invalid_delta`, `invalid_snapshot`, `sequence_gap`, `crossed_book`, `book_level_limit_exceeded`, `snapshot_depth_limit_exceeded`, `sync_buffer_limit_exceeded`, `depth_stale`, `disconnected`, `memory_budget_exceeded`, `sync_timeout`, `permanent_http_403`, `permanent_http_418`, `permanent_http_451`, `transport_error`, `message_invalid`, `message_too_large`, `event_queue_overflow`, `resync_budget_exhausted`, `not_started`, `stop_requested`, `stopped`, `snapshot_rate_budget_exhausted`, `snapshot_bridge_budget_exhausted`, `server_shutdown`, `websocket_transport_error`, `public_rest_transport_error`, `invalid_http_response`, `local_rest_weight_budget_exhausted`, `http_429_retry_exhausted`, `rest_path_not_allowed`, `snapshot_invalid`, `websocket_ping_unsupported`, `rest_request_already_active`, `websocket_close_timeout`, `live_websocket_dependency_missing`, `stop_timeout_rest_alive`, `stop_timeout_reader_alive`, `stop_timeout_close_alive`, `stop_timeout_worker_alive`, `http_status_error`.

Texto vazio do motivo vira `null`; valor fora da lista vira `unknown` e `metadata_complete=false`. Um motivo com formato estrito `http_status_` seguido de três dígitos ASCII 100–599 vira somente o enum `http_status_error`; o status numérico não é exportado. Outras mensagens não são copiadas. Não promover um motivo de shutdown a primeira falha causal. `bridge` registra a decisão observada por IDs/estado/motivo; uma espera de snapshot sem falha demonstrada não vira automaticamente `first_failure`.

Booleanos não são inteiros válidos. IDs, tentativa e relógio inválidos tornam-se `null` e marcam metadado pertinente como incompleto. Contadores inteiros ficam em 0–9223372036854775807; no teto, saturar e marcar `metadata_complete=false`, sem wrap ou perda silenciosa. A projeção final tem no máximo 64 registros de evento somando `events` e `first_failure` quando presente; a primeira falha permanece separada e participa do mesmo limite total de 16384 bytes.

Medir os bytes da saída completa, incluindo a primeira falha e contadores, por `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")`. Evictar os eventos mais antigos até satisfazer ambos os limites e incrementar `dropped_events`; cópias da primeira falha não são removidas por essa evicção. O accessor entrega cópias independentes e não persiste a projeção. Testes devem rejeitar chaves extras e exercer cada enum/faixa, inclusive bool como int, teto, desconhecidos e sentinelas sensíveis.

O campo HTTP numérico sugerido inicialmente foi removido após revisão Spec por exceder as categorias existentes de DI-02/05; a normalização conserva apenas um enum permitido. Jev Workflows recomendou essa correção no recibo `bcb7c9a8-a979-406d-9a3f-aaeed7cfc081`, sem conceder autorização nem alterar DI-01–07. Custo faturado desconhecido: `null`.

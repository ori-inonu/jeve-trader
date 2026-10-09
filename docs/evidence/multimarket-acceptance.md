# Aceite do incremento multimercado — 09/10/2026

Contrato: [SPEC I-01–I-12](../specs/Multimercado_Implementacao_2026-10-09.md), SHA256 `af174497bf764b1a7c67818cee6e3b925a40933d98c40c8e14f5b1b0f6bc01f4`. Baseline `da96c6ad4187030a98c4daa86a6b96e1e5b809a9`. O aceite local exige todos os testes, workload de qualidade e duas revisões independentes. Resultados finais são registrados após as correções da revisão; esta matriz não promove gates externos.

Verificação do backend em `ecc5eb259719311f8cf9bf18eef85e7d178e5438`: [321 testes offline e autoteste legado](multimarket-verification.json). Verificação do frontend em `3edf5d27a3036f97db5c331407996124a023783b`: [36 testes e build TypeScript/Vite](multimarket-frontend-verification.json). A [jornada no navegador](multimarket-ui-validation.json) confirmou conexão por teclado, atualização sem reload, retorno do legado, layout estreito e expiração local após parada do backend. O chunk legado lazy mantém um aviso de tamanho no build.

| Aceite | Evidência executável | Alcance e limite |
|---|---|---|
| I-01 | `test_decimal_wire_contract_is_finite_and_rejects_float`, `test_registry_keeps_same_symbol_separate_by_venue_and_account`, round trips de contratos | Decimal validado, venue/conta/workspace isolados; metadata incompatível bloqueia dependentes |
| I-02 | `test_duplicate_event_is_idempotent`, testes de gap/regressão/metadata/clocks, overflow runtime e projeção frontend | L1 e trades individuais continuam parciais; origem/recepção não certificam continuidade |
| I-03 | Testes de endpoint TLS fixo, normalização, discovery/reconnect/slow-stop e [smoke público](multimarket-public-smoke.json) | Fixtures offline e conexão pontual BTCUSDT; disponibilidade contínua/regional não certificada |
| I-04 | Testes Decimal/q=0, mínimo notional, moeda/tick/step, posição spot e conta/custos | Nenhum funding/liquidação presumido; custos desconhecidos não viram zero |
| I-05 | Testes de fill idempotente, snapshot atrasado/conflitante, expiração/reset monotônico | Ledger/importação manual local; não foi acessada conta privada |
| I-06 | Testes de Choice/Noul, coalescência/limite, conta/revisões/seleção, expiração, integração causal e recuperação após timeout | Executor fake nas suítes; sem chamada paga. Licença desconhecida impede envio de payload ao JEV |
| I-07 | `desktop/tests/multimarket.test.mjs`, comandos do cockpit e [validação no navegador](multimarket-ui-validation.json) | Causas/gates/contexto, teclado e layout estreito; janela nativa da nova versão ainda não certificada |
| I-08 | Testes unknown/allowed retention, idempotência e replay paginado, gates do serviço | Retenção/exportação afirmativa exigida; nenhum dataset de mercado capturado no repositório |
| I-09 | Testes de modelo não aprovado, escopo/comparadores temporais e conta stale/idade desconhecida | Promoção determinística por instrumento; probabilidade financeira nula sem aprovação. Não há prova de rentabilidade |
| I-10 | Teste sidecar outer1/2 + inner3/legacy2, preservação byte a byte, diagnóstico wire e build TypeScript/Vite | Novo pacote/dependência incluídos no empacotamento; não foi produzido nem instalado um novo release Tauri |
| I-11 | [Baseline antes do código](multimarket-baseline-performance.json), [workload multimercado](multimarket-performance.json) e exportação de métricas | Queue2000/drain500/4Hz/200trades, 1000 eventos/s por 10s, p95 por batch <=50ms; GPU/jornada/benefício permanecem null |
| I-12 | Stress abaixo e suites domain/runtime/service/frontend | Dependentes bloqueados com causa; nenhum stress sintético certifica sessão live contínua |

## Stress obrigatório

| Condição | Verificação |
|---|---|
| Gap com conexão saudável e update atrasado | Gap/regressão/late-book em domain; invalidar domínio sem afirmar tape completo |
| Tick/step alterados | Invalidação por metadata e gates financeiros por escopo exato |
| Quote expirado, wall clock ajustado | Idade monotônica domain/service/frontend; snapshot não renova a origem |
| Seleção/conta/custos mudam com chamada pendente | Identidade exata runtime/service e descarte contextual no frontend |
| Conta stale ou idade desconhecida com quote fresh | Gate de risco impede quantidade recomendada e lucro líquido |
| Fill duplicado após reconnect | Idempotência persistida por conta/ID/revisão, sem duplicar patrimônio |
| Burst/overflow | Queue limitada, nova epoch/diagnóstico e invalidação de dependentes |
| JEV indisponível/timeout | Falha tipada, resposta tardia descartada e substituição limitada a dois workers; chamadas travadas mantêm reserva de uso pendente e causam backpressure |
| Retenção/exportação negada | Payload não persistido nem exportado; apenas diagnóstico/contadores sanitizados |

## Dependências externas

B3 independente exige fornecedor/SKU, entitlement e licença de uso/retention/export. Conta automática exige escopos read-only e fixture autorizada. Aprovação financeira exige corpus licenciado e avaliação temporal por escopo. Benefício de JEV, etapas manuais e desempenho nativo exigem comparação prospectiva pareada real. Esses aceites externos permanecem abertos; somente seu bloqueio local integra esta entrega.

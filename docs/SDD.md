# SDD — Jeve Trader

## Revisão contra main e próximo ciclo — 09/10/2026

O [PR #2](https://github.com/ori-inonu/jeve-trader/pull/2) foi revisado contra `main` (`0171aed6c4a25adf26d349bfe2c3140805a35e97`). O candidato de código corrigido é `e52172de0c127a8f1d3768cc072964501eb8ff69`, árvore `3e2e3ceb4856ea71ec1b903efda4fc6fd729098e`. As revisões independentes [Standards](evidence/pr2-main-standards-final.md) e [Spec](evidence/pr2-main-spec-final.md) terminaram com zero achados restantes. A [evidência Windows offline](evidence/pr2-main-verification-public.json) registra 326 testes Python, autoteste legado, 36 testes frontend e build TypeScript/Vite aprovados. Rust offline foi reaproveitado porque seus arquivos não mudaram. O merge local com a baseline não tem conflitos; checks e base remotos são conferidos separadamente antes da entrega.

Corrigidos os dois achados reproduzidos: concorrência entre OFF e despacho JEV e retenção ilimitada de identidades. Os [aceites R-01–R-04](specs/PR2_Revisao_Main_2026-10-09.md) e o [RED/GREEN](evidence/pr2-repair-tests.md) preservam FW-01 e I-01–I-12. OFF pode aguardar uma tentativa já iniciada; timeout de transporte não comprova latência da janela.

A [SPEC de instrumentação e protocolo](specs/Instrumentacao_Protocolo_Multimercado_2026-10-09.md) está **ready_local para EN-T1–EN-T3**, conforme [revisão independente](evidence/rt12-next-spec-readiness-final.md), SHA-256 `9e6d06ed4ea275981bdcf8c0d4d26e568b3ff79d9f9be20482feb06e77565e26`. O cabeçalho draft conserva o snapshot exato revisado; este registro e o relatório fixam sua prontidão. Isso é planejamento concluído, sem implementação dessas três tarefas nesta rodada.

| Próxima entrega | Dependência e aceite |
|---|---|
| EN-T1 — origem e manifest de pacote | Hashes de código/artefatos, validação fechada e regressões offline; primeiro incremento local elegível |
| EN-T2 — correlação de telemetria | Origem EN-T1; relógio único do renderer, allowlist, buffer limitado e sanitização |
| EN-T3 — protocolo verificável | Schemas de run/tarefa/evento/pares; estados e falhas preservados; ganho null |
| EN-T4 — jornada Windows J1–J6 | Pacote identificado, observação nativa e ponte J6 comprovada; não executada |
| EN-T5 — comparação humana prospectiva | Tratamento B congelado, ambiente equivalente ou diferenças qualificadas e cinco pares completos; não executada |

O JEV recomendou [fechar schemas locais](evidence/rt12-schema-jev.json) e [aprofundar o schema público Cedro](evidence/b3-next-diligence-jev.json). A consulta anterior de prioridade foi inválida e não virou recomendação. O [dossiê B3](research/B3_Qualificacao_Publica_2026-10-09.md) delimita Cedro/CQG/UMDF; SKU WIN/WDO, entitlement, licença e direitos de retenção/envio ao JEV continuam sem confirmação. O [adendo Cedro](research/Cedro_Socket_Schema_Publico_2026-10-09.md) encerrou quatro páginas de pesquisa: parser real não ready; faltam payload versionado, identidade WDO e recuperação aplicável. Conta real depende de fonte/formato/autorização; calibração financeira depende de corpus e aprovação por escopo. Ordens permanecem desabilitadas. O piloto FW-11 de 30 minutos e seus critérios originais continuam abertos; a prontidão local do código não certifica release operacional.

O incremento multimercado de 09/10/2026 implementa o [contrato finito I-01–I-12](specs/Multimercado_Implementacao_2026-10-09.md), derivado do [mapa Wayfinder](../.scratch/wayfinder-multimercado/map.md) e do [draft de destino MM-01–MM-12](../.scratch/wayfinder-multimercado/spec.md). A baseline é `da96c6ad4187030a98c4daa86a6b96e1e5b809a9`; a branch de entrega é `codex/multimarket-spec`.

| Ticket | Entrega | Verificação |
|---|---|---|
| IMP-01 | Identidade, metadata, estado, conta, risco Decimal e promoção por escopo | `app/test_multimarket_domain.py` |
| IMP-02 | Transporte público BTCUSDT, scheduler causal e journal condicionado à licença | `app/test_multimarket_runtime.py` |
| IMP-03 | Cockpit, projeção causal, frescor e detalhes progressivos | `desktop/tests/multimarket.test.mjs` e prévia no navegador |
| IMP-04 | Sidecar, wire externo 1/2, Snapshot3, orçamento e legado isolado | `app/test_multimarket_service.py`, testes de transport e build |
| IMP-05 | Aceites, workload, revisão independente e PR | [Matriz de aceite](evidence/multimarket-acceptance.md) |

IMP-01–IMP-05 concluídos no escopo finito, com revisões independentes [Standards](evidence/multimarket-standards-review.md) e [Spec](evidence/multimarket-spec-review.md), ambas sem achados restantes. O [PR #2](https://github.com/ori-inonu/jeve-trader/pull/2) reúne a entrega.

Os testes locais usam fixtures e executores injetados, sem API paga. O smoke público prova acesso pontual HTTPS/WSS a BTCUSDT no host. A matriz conserva as limitações: fornecedor/licença B3, integração privada de conta, aprovação financeira e medição prospectiva da janela Windows. Nenhum gate local comprova essas dependências externas.

O planejamento histórico continua no backlog. Este incremento não encerra automaticamente especificações draft ou experimentos financeiros anteriores. Não há ordens, migração destrutiva ou conexão automática no boot; Profit/Excel/OCR permanecem disponíveis no modo legado.

A auditoria anterior deixou o [contrato N-01–N-05](specs/Multimercado_Proximo_Ciclo_2026-10-09.md). A retomada resolveu a pesquisa RT-12 e derivou EN-01–EN-04, com prontidão local revisada acima. O recibo de abstenção daquela rodada permanece histórico; as consultas posteriores estão registradas separadamente.

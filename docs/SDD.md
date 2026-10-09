# SDD — Jeve Trader

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

A auditoria deixa um [contrato candidato para a próxima melhoria](specs/Multimercado_Proximo_Ciclo_2026-10-09.md) e o ticket RT-12. Sua pesquisa pode avançar dentro do objetivo, mas não foi iniciado outro ciclo de implementação. A consulta JEV sobre a prioridade absteve-se e está registrada no contrato.

# Revisão final de prontidão da SPEC RT-12

**Decisão:** pronta para implementação local de EN-T1–EN-T3 (`ready_local=true`). Esta é uma revisão de prontidão documental, não autorização para dependências externas nem afirmação de execução.

A SPEC atual corresponde ao SHA-256 `9e6d06ed4ea275981bdcf8c0d4d26e568b3ff79d9f9be20482feb06e77565e26`; a pesquisa RT-12 corresponde a `607acb62c3df7c05bbf93298814c2282f690de7dfcd367fef85ad6c991b1ef73`. Conferi também os hashes das fontes imutáveis I-01–I-12, N-01–N-05, FW-01–FW-12 e R-01–R-04.

Os dois bloqueios da revisão inicial foram resolvidos. EN-02 agora define schemas fechados e allowlist, nulabilidade, limites, correlação, relógios, sanitização e descarte do buffer (linhas 32–51). EN-04 define registros fechados para run/task/event, ações e intervenções, gates, falhas, estágios e pares prospectivos (linhas 53–72). EN-01 e EN-03 completam identidade/manifest e semântica das métricas. Os aceites N-01–N-05 permanecem preservados: screenshots são explicitamente excluídos de v1 e essa parte de N-04 fica aberta; os estados build/instalação/janela/ganho não se promovem entre si; sem pares prospectivos o ganho segue null.

A prontidão cobre somente implementação e testes offline locais T1–T3. T4 continua bloqueado por observação nativa Windows e ponte demonstrada do J6; T5 exige B congelado e comparação prospectiva. B3/licença/entitlement, conta privada, calibração e promoção financeira permanecem gates externos separados. Nenhum teste de produto foi executado nesta revisão documental.

**Atenção futura para T5:** o validador de pares exige mesma tarefa, identidade, operador e política, mas não igualdade completa de ambiente. A etapa de comparação deve exigir ambiente equivalente ou qualificar diferenças para evitar atribuir à versão mudanças de host/runtime. Isso não bloqueia T1–T3, pois T5 está explicitamente separado e requer método próprio.

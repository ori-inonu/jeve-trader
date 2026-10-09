# Implementação multimercado — 2026-10-09

Baseline fixa: `da96c6ad4187030a98c4daa86a6b96e1e5b809a9`.
Branch: `codex/multimarket-data`; PR: https://github.com/ori-inonu/jeve-trader/pull/1.

Contrato original: [Coleta Multimercado](../specs/Coleta_Multimercado_2026-10-09.md).
Plano e dependências: [EM-00 a EM-12](../research/Expansao_Mercados_Plano_2026-10-09.md).
A autorização atual inicia a implementação de software e sua verificação. Os aceites empíricos permanecem exigidos; fixtures não os satisfazem.

| Frente | Responsável | Arquivos exclusivos | Dependências | Critérios |
|---|---|---|---|---|
| EM-01 | Pesquisador | ready-spec fora do checkout | documentação primária | feed, regras e limites fixados |
| EM-02/03 | Implementador feed | market_data_contract.py, public_crypto_feed.py e testes próprios | EM-01 | AC-01, AC-02, AC-04 |
| EM-04/05 | Implementador replay/contexto | market_replay.py, multimarket_context.py e testes próprios | contratos congelados EM-01 | AC-03, AC-04, AC-05 |
| EM-08/09 | Implementador economia | multimarket_economics.py e testes próprios | regras/payoffs congelados | AC-06; protocolo AC-07, sem certificar resultados empíricos |
| EM-05/10 | Integrador | serviço, observador, CLI, UI, requisitos e evidências | três frentes | integração offline e observação limitada sem ordens |
| Revisão | Revisores independentes | relatórios fora do checkout | candidato fixo | standards + spec, sem autoaprovação |

Estados dos tickets serão atualizados apenas com evidência. EM-06 (B3), acesso operacional EM-07 (derivativos), EM-11 (esportes) e EM-12 (binárias) dependem de fontes, licença/jurisdição ou dados ainda ausentes. Os cálculos locais dos quatro tipos de payoff podem avançar sem habilitar esses mercados.

A fronteira inicial é contrato → coleta / replay-contexto / economia → integração → revisão. Nenhuma frente modifica o checkout principal, que contém trabalho de outra conversa.

R$400 → R$4.000 em menos de uma semana é o objetivo de investigação. Nenhum módulo pode converter essa meta em promessa de retorno, probabilidade inventada ou aumento de lote para recuperar perda. Custos, risco, acesso ou evidência ausentes mantêm `wait` e a probabilidade financeira em `null`.

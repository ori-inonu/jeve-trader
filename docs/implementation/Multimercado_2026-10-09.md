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

## Estado demonstrado

| Ticket | Estado | Evidência / próxima condição |
|---|---|---|
| EM-00/01 | Pesquisa e SPEC ready concluídas | Fontes primárias e contrato congelado; SHA da SPEC `7e8d2034…00612` |
| EM-02 | Contratos integrados | Catálogo, envelopes e testes de Decimal/unidades/relógios; WIN preservado |
| EM-03 | Software integrado; transporte real em investigação | Três smokes de 20 s receberam 7, 772 e 147 execuções e reprovaram livro/saúde. No terceiro, o shutdown terminou `off`, com todos os helpers encerrados. Coleta saudável sustentada continua pendente |
| EM-04 | Replay/VAP integrados | Hash/índice, dedup, intervalos e soma exata; retenção real desligada |
| EM-05 | Serviço/CLI/UI integrados | Padrão desligado; fixture conferida no navegador Windows com sidecar real; janela Tauri não validada |
| EM-06 | Dependência externa | SDK/feed B3 autorizado, licença, cobertura e custos atuais |
| EM-07 | Dependência externa | Produto derivativo, acesso, margem, funding/liquidação e custos; feed spot não satisfaz |
| EM-08 | Calculadoras e gates integrados; comparação real pendente | Payoffs sintéticos por família; custo/FX/risco/produto ausente mantém `wait`, q=0 |
| EM-09 | Protocolo integrado; aceite empírico pendente | Relatório `pending`, amostra 0 e probabilidades null; AC-07 permanece aberto |
| EM-10 | Estudo prospectivo pendente | Dataset representativo, método e critérios independentes congelados |
| EM-11 | Dependência externa | API esportiva permitida no Brasil e responsabilidade das posições |
| EM-12 | Dependência externa | Admissibilidade, settlement verificável e payout líquido |
| Revisão | Em andamento em candidato fixo | Dois revisores independentes, Standards e Spec; não equivale a autoaprovação |

O código `09e7b3090106cd1cabccef4327f541fca55f0354` passou 343 testes Python e self-test offline do serviço com socket/rede bloqueados no Windows. Tipos, 15 testes Node e build passaram. Os revisores Standards e Spec avaliam o candidato documental `52464af031919cf695182737b9651aa069011df1`. O implementador corrige separadamente um defeito reproduzido offline: fechamento local durante recuperação mascara o motivo original do livro na saúde pública. Esse diagnóstico não determina o motivo da falha real do terceiro smoke. [Evidência de integração](../evidence/multimercado-integracao-2026-10-09.md) e [uso local](Multimercado_Uso_2026-10-09.md) registram alcance e pendências. Uma entrega de software não conclui o objetivo financeiro nem os aceites globais empíricos.

A fronteira inicial é contrato → coleta / replay-contexto / economia → integração → revisão. Nenhuma frente modifica o checkout principal, que contém trabalho de outra conversa.

R$400 → R$4.000 em menos de uma semana é o objetivo de investigação. Nenhum módulo pode converter essa meta em promessa de retorno, probabilidade inventada ou aumento de lote para recuperar perda. Custos, risco, acesso ou evidência ausentes mantêm `wait` e a probabilidade financeira em `null`.

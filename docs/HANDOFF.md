# Retomada — Jeve Trader

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

## Incremento multimercado — 09/10/2026

Entrega isolada na branch `codex/multimarket-spec`, com [SPEC finita](specs/Multimercado_Implementacao_2026-10-09.md), [grafo SDD](SDD.md) e [matriz de aceite](evidence/multimarket-acceptance.md). O cockpit React acessa BTCUSDT spot por API pública, mantém identidade/metadata/frescor por fonte e instrumento e expõe causas de AGUARDAR. O motor modular inclui conta reconciliada, risco Decimal, scheduler JEV causal, journal condicionado à licença e métricas exportáveis.

Nenhuma fonte, conta ou chamada JEV é ativada no boot. A inicialização exige conexão explícita; a reconexão posterior e a descoberta de metadata são automáticas. Ordens continuam desligadas. A pasta `multimarket/` separa o novo armazenamento dos dados JevWIN; Excel/OCR/laboratório continuam acessíveis pelo modo legado.

Verifique com `.venv/Scripts/python.exe scripts/verify.py`, `npm test` e `npm run build` em `desktop/`. A [evidência de desempenho](evidence/multimarket-performance.json) mede processamento sintético pós-recebimento; o [smoke público](evidence/multimarket-public-smoke.json) mede alcance pontual de HTTPS/WSS, sem persistir cotações. Consulte a matriz para os resultados finais e os limites da revisão.

Continuam pendentes: fornecedor/SKU/entitlement/licença B3 para WIN/WDO; conta privada com escopos read-only; corpus autorizado e aprovação financeira por instrumento; instalação e jornada da nova versão na janela Windows com avaliação prospectiva pareada. A observação no navegador não substitui essa medição. O estado de 07/10 abaixo é histórico e descreve o painel anterior.

## Estado atual — 07/10/2026

A implementação local 0.4.0 está neste checkout, ainda sem commit/PR. Preserve as alterações que já existiam antes desta tarefa; o patch inicial está em `.artifacts/before-implementation.patch`. Não clone por cima deste diretório. [Guia atual](DECISION_PANEL.md), [status](IMPLEMENTATION_STATUS.md), [backlog](BACKLOG.md) e [evidência](evidence/decision-panel-2026-10-07.json) descrevem o escopo demonstrado.

Entregues o painel Tauri/React em quatro áreas, serviço Python independente, coletor COM isolado, contratos JEV com premissas literais, dimensões contextuais separadas, registro experimental, banca inteira e posições reais informadas manualmente. Há comparação determinística de quantidades e contratos financeiros/seleção tipada. O laboratório offline executa replay causal, logística multiclasse, calibração temporal e comparação de 17 variantes de dimensionamento. O serviço ainda não carrega um modelo financeiro aprovado nem chama a seleção econômica JEV; mantém Aguardar e probabilidade não estimada. Isso é trabalho pendente, além da falta de dados empíricos.

Verificados no Windows: 188 testes, autoteste legado, build React/Tauri, diagnóstico Python congelado e instalação/reinstalação/desinstalação isoladas com preservação dos dados. A janela nativa e o processo supervisionado foram observados. Os formulários foram exercitados na prévia React conectada ao mesmo serviço: R$400 → R$800 → R$600 e duas saídas parciais com resultado final R$627, sem ordens. Interações nos formulários nativos, Excel/RTD real, API JEV real, SDK ProfitDLL e rentabilidade não foram verificados. O teste estatístico é sintético e não aprova um modelo para operação.

O instalador e ZIP estão em `.artifacts/desktop-windows/`. Abra a UI com `powershell -File scripts/start-desktop.ps1`; o build exige PowerShell 7, Rust/MSVC, Node/npm, NSIS e as dependências Python de build. Use `.venv/Scripts/python.exe scripts/verify.py`. O laboratório requer `app/requirements-lab.txt` e usa `scripts/run_decision_lab.py`. Preserve `%LOCALAPPDATA%/JevWIN`; o novo `decision-lab.sqlite3` fica separado do diário legado, com importação inicial de valores compatíveis, sem sincronização contínua.

Próximos trabalhos: completar hipótese específica de exaustão (JT-002); conferir contrato RTD real sem ampliar cobertura; obter amostra WIN autorizada e auditável; validar prospectivamente estimativas/custos/latência; definir artefato versionado e ligação estimador → serviço → seleção tipada JEV (JT-013/JT-015); validar formulários na janela Windows e SDK/licença ProfitDLL quando disponíveis. Não promover `--smoke` nem um relatório com `deployment_approved=false`. Sem acesso autorizado ao SDK, continue apenas o adaptador contratual.

Mission Control não respondeu à consulta inicial; respondeu à nova consulta antes da conclusão, disponível e sem tarefas neste projeto. Consulte novamente o contexto antes de iniciar novos escritores. Não faça chamadas pagas em testes/setup. A preferência do agente de desenvolvimento continua GPT-6.1 Sol, separada do modelo/chave do aplicativo.

## Histórico da transferência — 06/10/2026

As seções abaixo descrevem a transferência anterior. Use o estado atual acima para retomar.

Data de consolidação: 06/10/2026, America/Sao_Paulo.

Publicação no GitHub e no Codex confirmada em 07/10/2026 (UTC).

## Goal & Scope

Gabriel quer continuar este projeto no Codex e GitHub. O produto acompanha o mini índice WIN no Profit Pro/Windows, interpreta fluxo com JEV e pesquisa decisões e dimensionamento condicionados ao capital. O objetivo econômico exige avaliação fora da amostra após custos e limites explícitos; crescimento garantido não foi estabelecido.

## Current State

- Repositório privado publicado: [ori-inonu/jeve-trader](https://github.com/ori-inonu/jeve-trader), branch `main`. A árvore do commit de publicação corresponde integralmente aos 132 arquivos preparados. A história remota preserva o commit inicial do GitHub e arquiva o histórico local anterior em bundle.
- Ambiente **Jeve Trader publicado no Codex** e confirmado na lista de ambientes de um novo chat. Setup: `bash scripts/setup-codex.sh`; verificação: `.venv/bin/python scripts/verify.py`. O [chat de configuração](https://chatgpt.com/local/01a113f1-e024-75b3-9113-723a82fd30f9?hostId=local) registra a preparação com GPT-6.1 Sol. A interface não forneceu URL exclusiva do ambiente nem um campo de branch; o setup confirmou checkout `main`. Estado detalhado em `docs/TRANSFER_STATUS.json`.
- A tarefa de preparação registrou Python 3.12.14, 166 testes e autoteste aprovados, 71 arquivos do aplicativo intactos e Git limpo. Essa preparação não implementou o backlog e não configurou credenciais, Profit ou chamadas JEV. A implementação fica para a próxima sessão solicitada por Gabriel.
- `app/` conserva a baseline JevWIN v0.3.0. A transferência organiza código/documentos e ferramentas de desenvolvimento; não aplica as melhorias da pesquisa.
- Interface Tk, COM Excel quote/tape/combined, importação CSV, fluxo, geometria, risco, diário e cliente JEV existem. Conta manual, cobertura parcial, nenhuma ordem.
- Empacotamento NSIS existe. Instalação/UI/Profit reais no Windows permanecem sem verificação. A causa da falha anterior do EXE não foi determinada.
- Os testes históricos de software são descritos em `app/VALIDATION.md`; a evidência da organização deste repositório fica em `docs/evidence/`.
- Pesquisa em `docs/research/Pesquisa_Decisao_JEV_WIN_2026-10-06.md`; plano E01–E10 em `docs/research/Plano_Experimentos_JEV.json`. Experimentos empíricos não executados.

## Decisions & Invariants

Mantenha separados contexto JEV, desfecho financeiro e risco. Preserve `full_tape=False`, validação temporal e execução desligada. Não transforme apoio/confiança em probabilidade de ganho nem perda passada em motivação para aumentar lote. Use `AGENTS.md` e `docs/decisions/README.md`.

Nome público: Jeve Trader. Nomes internos JevWIN permanecem para preservar compatibilidade. Não reformate/refatore toda a baseline antes de resolver os problemas de decisão identificados.

O histórico local pré-publicação está arquivado em `docs/archive/Jeve_Trader_Historico_2026-10-06.bundle`. Os ZIPs anteriores são snapshots dessa preparação. O clone GitHub é a base de continuidade; o bundle é histórico separado, sem instrução de empurrar sua branch sobre `main` remoto.

## Active Blockers

Para validação externa, continuam pendentes instalação Windows, contrato real de exportação do Profit, acesso/licença de dados e conta, amostra de mercado reconciliável e chamadas JEV autorizadas com orçamento. Nenhum desses bloqueios impede a correção do payload e a instrumentação local no ambiente Codex publicado ou sobre um clone do repositório.

## Suggested Skills

Use skills disponíveis no novo ambiente, sem presumir os caminhos desta sessão: implementação para executar o backlog; diagnóstico de bugs quando houver erro concreto; pesquisa para documentação primária; revisão de código para mudanças materiais. A skill oficial TypeSafe está referenciada no relatório de pesquisa e deve ser consultada ao alterar a integração. Não instale automaticamente um plugin ou substitua o modelo selecionado por Gabriel.

## Exact Next Action

No Codex, crie um novo chat, selecione o ambiente **Jeve Trader** e use `docs/CODEX_NEXT_TASK.md` quando desejar iniciar a implementação. Para trabalhar no computador, obtenha a base atual pelo repositório privado:

```bash
git clone https://github.com/ori-inonu/jeve-trader.git
cd jeve-trader
```

Na raiz, execute a preparação adequada ao sistema e `scripts/verify.py`. Depois use o texto de `docs/CODEX_NEXT_TASK.md`. Comece pelo problema da premissa em `app/desktop_app.py` e pela semântica das perguntas, conforme os IDs do backlog. Não reinicie a fase de definição do produto.

Para contexto adicional, consulte apenas a seção necessária de `PRD.md`, `ARCHITECTURE.md`, `IMPLEMENTATION_STATUS.md` e `BACKLOG.md`. Ao terminar, registre arquivos alterados, verificações, limitações e próximo item desbloqueado.

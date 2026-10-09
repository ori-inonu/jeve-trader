# Retomada — Jeve Trader

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

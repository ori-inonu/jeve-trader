# Jeve Trader — implementação e evidências

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

Implementados os módulos de contratos/registro, saúde de mercado, ledger por conta, risco determinístico, scheduler contextual causal, fonte pública BTCUSDT, journal/replay licenciado, integração sidecar e cockpit. A [SPEC I-01–I-12](specs/Multimercado_Implementacao_2026-10-09.md) fixa o incremento; a [matriz de aceite](evidence/multimarket-acceptance.md) reúne verificações e limitações. A baseline anterior permanece acessível no modo legado e em suas regressões.

| Capacidade | Alcance demonstrado | Dependência restante |
|---|---|---|
| Cripto público | Discovery/HTTPS/WSS read-only, filtros atuais, L1 e trades individuais; fixtures/reconnect offline e smoke pontual | Disponibilidade contínua e elegibilidade regional |
| Inteligência | Choice/Noul tipadas, identidade exata, timeout/expiração monotônicos, orçamento e licença | Habilitação do produto e política afirmativa para envio de dados; sem chamada paga na verificação |
| Conta/risco | Importação manual/read-only contratual, idempotência, conciliação e q=0 | Acesso privado real, custos vigentes e modelo financeiro aprovado |
| Interface | Cockpit React, seleção, frescor, causas, exportação de métricas e acesso ao legado | Jornada e desempenho da nova janela nativa Windows |
| Evidência | Suítes offline, build, stress e workload por batch | Avaliação econômica/prospectiva real |

Probabilidade de lucro segue não estimada sem modelo aprovado no escopo atual. B3 independente permanece bloqueado até qualificação de fornecedor e licença. Confiança contextual não promove modelo financeiro. Os resultados de 07/10 abaixo são históricos e não certificam o novo incremento nativo.

## Entrega atual — 07/10/2026, painel 0.4.0

Implementado o painel Tauri 2/React/TypeScript/Vite/Tailwind 4/ECharts, com serviço Python separado da UI Tkinter. Mudanças locais anteriores foram preservadas; o diff inicial foi arquivado em `.artifacts/before-implementation.patch`. A distribuição mantém os identificadores JevWIN e o diretório de dados legado. [Guia](DECISION_PANEL.md), [ADR](decisions/0010-painel-e-capital-progressivo.md) e [evidência sanitizada](evidence/decision-panel-2026-10-07.json).

| Entrega | Código e evidência | Limite restante |
|---|---|---|
| Premissas e dimensões JEV | Premissa literal/versionada, continuidade e absorção separadas, apoio/contradição/insuficiência independentes; testes offline. | Família de exaustão e validação remota/empírica ainda pendentes. |
| Registro experimental | Estado e perguntas exatos, hashes de código/perguntas, receita, modelo solicitado, relógios, conta/custos, resposta e falhas sanitizadas. | Política de retenção, captura real e protocolo E02 completo. |
| Painel e capital | Quatro áreas, cálculos `Decimal`, banca inteira, pico, ausência de parada por lucro/pausa fixa, alternativas e capacidade. | Recomendação financeira principal continua aguardar; não há modelo aprovado integrado. |
| Registro de execução | Entrada manual e saída parcial, margem proporcional, taxas uma vez, histórico, idempotência e revisão otimista. | Sem posição/saldo automático, lucro flutuante ou envio de ordens. |
| Excel/RTD | Processo COM próprio com timeout/reconexão; cotação e tape combinado continuam parciais. | Exportação real do Profit, campos, continuidade e uso prolongado não verificados. |
| Laboratório financeiro | Replay causal de preço, rótulos censurados, logística multiclasse, calibração, teste temporal, comparação pareada com/sem JEV e 17 políticas. | Smoke sintético; sem vantagem empírica WIN, execução por fila ou modelo exportado/aprovado. |
| Escolha econômica | Motor compara quantidades e `q=0`, crescimento log líquido, Kelly fracionado/adaptação e Choice tipado. | Conectar modelo validado e Choice ao serviço; parâmetros operacionais ainda não selecionados em dados WIN. |
| ProfitDLL | Contrato read-only para callbacks/Market Data, overflow/gaps identificados; testes locais. | SDK autorizado, licença e adaptação ABI real ausentes. |
| Windows | Pacote x64, instalador e portátil; instalar/reinstalar/desinstalar, janela nativa, sidecar e encerramento dos descendentes verificados. | Interações na janela nativa, RTD real, assinatura do instalador e auditoria completa das licenças. |

**Verificação de software:** 188 testes `unittest` e autoteste aprovados em Windows 11 x64/Python 3.14.7; rede Python bloqueada durante a suíte. TypeScript e build Vite aprovados; build release Tauri aprovado. Diagnóstico do Python empacotado: PASS, schema 1, 16 alternativas sintéticas, ordens desligadas e probabilidade financeira nula. Instalação isolada confirmou preservação do SQLite após reinstalação/desinstalação e nenhuma alteração da instalação/dados primários. A janela nativa foi observada; isso não verifica seus formulários. Uma regressão adicional confirma o reinício da sequência Labouchère após sua conclusão no laboratório.

**Verificação visual:** quatro páginas React na prévia local conectada ao Python, com dados isolados. Banca R$400 → R$800 → R$600 preservou pico R$800 e drawdown 25%; capacidade passou a 3 contratos no cenário sintético. Entrada fictícia de 2 contratos a 131000, custo R$1 e margem R$310: banca R$599/margem R$289. Saídas de 1 contrato a 131100 e 131050, custo R$1 cada: banca final R$627, margem R$627, posição zero e pico R$800. Foram registros locais de teste, sem operações no Profit.

**Laboratório:** 300 linhas sintéticas em 10 sessões, separadas em treino 180/calibração 60/teste 60; modelos com/sem JEV permanecem `RESEARCH_ONLY` e `deployment_approved=false`. Comparações e risco estimados nesse cenário não são resultados do WIN. Nenhuma chamada paga/autenticada ao JEV, conta real ou ProfitDLL ocorreu.

Mission Control em `127.0.0.1:18792` estava indisponível durante a consulta inicial. A nova consulta antes da conclusão respondeu `available=true`, sem tarefas neste projeto. Nenhum writer concorrente foi iniciado. Consulte [HANDOFF.md](HANDOFF.md) e o [backlog](BACKLOG.md) antes de continuar.

## Planejamento documental — Wayfinder, 07/10/2026

Resolvidos documentalmente [mapa e seis tickets](../.scratch/wayfinder-evolucao-decisao/map.md), com seis contratos internos, [especificação transversal](../.scratch/wayfinder-evolucao-decisao/spec.md), [sequência de implementação](../.scratch/wayfinder-evolucao-decisao/implementation-plan.md) e [auditoria de aceite](../.scratch/wayfinder-evolucao-decisao/acceptance-audit.md). O [complemento datado](research/Complemento_Wayfinder_JEV_WIN_2026-10-07.md) preserva os achados e registra o fechamento. Conferidos isoladamente vetores de identidade e fixture aritmética; nenhuma linha do aplicativo ou parâmetro operacional foi alterado nesta rodada. Catálogo/status E01–E10 e estados empíricos JT permanecem preservados. Implementação dos novos contratos, confirmação econômica e sessão Windows ainda não foram executadas; dados, custos da conta, orçamento e limites pessoais constam como pendências.

## Nova descoberta — oportunidades com valor verificável, 07/10/2026

Aberto o [novo mapa Wayfinder](../.scratch/wayfinder-proximas-oportunidades/map.md), com pesquisa de composições tipadas JEV, evidência que falta para aprender com casos e experiências de compreensão da decisão. O [enquadramento](../.scratch/wayfinder-proximas-oportunidades/spec.md) preserva as escolhas anteriores e distingue hipótese de melhoria de benefício demonstrado. Investigação documental; nenhum código, parâmetro operacional, estado empírico JT/E ou aprovação financeira muda por esta rodada. A última consulta ao Mission Control recusou conexão; os pesquisadores são leitores e a escrita é centralizada pelo principal.

## Histórico de 06/10/2026 e da transferência

O texto abaixo preserva o estado da época. Afirmações sobre ausência de painel moderno/laboratório ou de instalação Windows devem ser lidas como históricas, com o alcance da entrega atual descrito acima.

Baseline documental em 06/10/2026: aplicação **JevWIN v0.3.0** preservada em `app/`; Jeve Trader é o nome de apresentação do projeto. Este documento distingue código existente, verificações de software e validação no ambiente real. A organização do repositório não implica nova versão do aplicativo, correção do executável ou execução de experimentos financeiros.

## Resultado conhecido

O desktop Python/Tkinter, a Central de decisão, estudos de capital e a ponte Excel/CSV estão implementados. [VALIDATION.md](../app/VALIDATION.md) registra **166 testes automatizados aprovados em Linux** e autoteste aprovado. COM e HTTP foram simulados; os testes de controlador substituem componentes de tela. A evidência não comprova abertura nativa no Windows, conexão real ao Profit/Excel ou acesso autenticado JEV.

A transferência também reproduziu a suíte em **venv Linux novo, com Python 3.12.14 e tzdata 2025.2**: 166 testes e autoteste aprovados, sem abrir a interface ou consultar serviços reais. A [verificação da transferência](evidence/transfer-verification.json) registra essa evidência nova, separada dos relatórios históricos. Instalação, runtime e interface nativos Windows continuam pendentes.

O histórico registra falha ao abrir um executável anterior. **A causa permanece desconhecida:** a mensagem exata/diagnóstico da máquina não foi recebida. A v0.3.0 mudou o empacotamento para instalador NSIS e runtime Windows convencional, com diagnósticos. Isso é uma alteração verificável de distribuição, não uma confirmação de que a falha específica foi resolvida. [Limites de build](../app/WINDOWS_BUILD.md).

## Matriz de estado

“Testado” abaixo descreve verificações de software: a cobertura histórica foi reproduzida na transferência pelo ambiente Linux indicado acima. Nenhuma dessas execuções valida os comportamentos reais/empíricos da última coluna.

| Capacidade | Implementado | Evidência de software | Verificação real/empírica pendente |
|---|---|---|---|
| Desktop Tkinter e Central | Sim; oito abas, conclusões, impedimentos e alternativas | Autoteste e controlador com componentes substituídos | Abertura, aparência e uso em Windows. |
| Painel HTML | Sim; exportação estática | Escape, exclusão de credenciais e equivalência da conclusão | Não é painel conectado ou prova da janela nativa. |
| CSV e parsing temporal | Sim; schema de negócios, validação e deduplicação | Casos sintéticos e formatos nos testes | Integralidade e qualidade de dados reais. |
| Excel `quote`/`tape` | Sim; leitura COM somente de valores | COM simulado, parsing e recursos | Anexação ao Excel/Profit do usuário, frescor e layout autorizado. |
| Excel `combined` | Sim; duas tabelas, falha conjunta e deduplicação | Testes de falha parcial e percurso até cenários | Exportação real de negócios e perdas entre leituras; cobertura continua parcial. |
| Fluxo e referências | Sim; medidas e até oito geometrias observadas | Eventos sintéticos, retenção, geometria e integridade | Valor preditivo no WIN e limiares por regime. |
| Risco/capital dinâmico | Sim; `Decimal`, pisos, pausa e recálculo após P&L manual | Testes monetários, sequências e capital negativo | Conta real, margem/custos atuais e adequação da política escolhida. |
| Diário SQLite | Sim; histórico, configurações e JSON | Testes de persistência e transições | Conciliação com corretora; dataset experimental completo não implementado. |
| Cliente JEV | Sim; `jev-1.13.0`, `Choice`/`Noul`, validação e limites | HTTP/respostas artificiais e descarte de avaliação antiga | Credenciais, acesso e latência reais; benefício incremental do modelo. |
| NSIS/runtime Windows | Scripts e distribuição histórica existentes | Inspeção PE, conteúdo, extração e hashes em relatórios | Instalar/desinstalar e executar nativamente em Windows. |
| Conta Toro, ordens e posição | Não | Sem integração ou ordem real | Contrato autorizado, reconciliação e gestão de execução. |
| Feed integral/ProfitDLL | Não | Não foi inventada integração | Licença, contrato, sequenciamento, correções e captura adequada. |
| Notícias/calendário e simulador de fila | Não | Propostas | Implementação e validação própria. |
| Rentabilidade/calibração/lote ótimo | Não | Contas ilustrativas não medem desempenho | Resultados fora da amostra, custos, execução, incerteza e drawdown. |

Fontes de evidência: [`app/test_inventory.json`](../app/test_inventory.json), [`app/desktop_self_test.json`](../app/desktop_self_test.json), [validação histórica](../app/VALIDATION.md) e [relatórios preservados](evidence/JevWIN_distribution_report.json). Os relatórios em `docs/evidence/` podem abranger métodos anteriores; sua existência não atesta que binários correspondentes estejam incluídos neste repositório ou tenham sido executados no Windows.

## Limites que não podem desaparecer na continuidade

- Não há envio de ordens, consulta de saldo/posição ou proteção efetiva de operações feitas diretamente no Profit. Conta e resultados são manuais.
- Excel/CSV são amostras parciais. `combined` não produz tape integral; a aba `Negocios` do template começa vazia e depende de exportação real compatível.
- Não houve chamada autenticada à API JEV nem conexão real ao ambiente do usuário na validação descrita. Acesso informado pelo usuário é contexto histórico, não teste de disponibilidade.
- Software correto, empacotamento inspecionado e contas reproduzíveis não são backtest, operações observadas ou prova de lucro.
- Frações agressivas, custos e margens de exemplo não foram selecionados/validados para operação real. Stops planejados não garantem limite absoluto de perda.
- A mudança de nome para Jeve Trader ainda não migra dados `%LOCALAPPDATA%\JevWIN`, atalhos, scripts, versão ou recursos internos.

## Pesquisa aprofundada: entregue como proposta

O [relatório de pesquisa](research/Pesquisa_Decisao_JEV_WIN_2026-10-06.md), [plano JSON](research/Plano_Experimentos_JEV.json) e [snapshot auditado](research/study-2026-10-06/manifest.json) documentam auditoria, fontes e propostas. A reprodução local do estudo examina projeção de payload e exemplos matemáticos; não consulta modelo/mercado e não mede rentabilidade. **Nenhum experimento empírico E01–E10 foi executado, e nenhuma proposta foi incorporada à v0.3.0.**

Achados relevantes para o próximo trabalho: a premissa criada no candidato não é transportada na projeção enviada ao JEV; o diário não preserva todos os prompts, versões e hashes necessários para reconstituir um experimento; apoio, contradição e insuficiência precisam ser avaliados como dimensões distintas. Corrigir esses pontos exige mudanças explícitas e verificação, não apenas atualizar este documento.

## Ordem recomendada para continuidade

1. **Reproduzir a baseline offline e implementar o ciclo local JT-001–JT-005:** registrar ambiente/resultados, corrigir a perda de premissa, separar apoio/contradição/insuficiência e acrescentar registro experimental versionado e relógios. Esse trabalho usa fixtures e transporte simulado; não depende de Windows, feed real ou chamadas autenticadas. Consulte o [backlog](BACKLOG.md) e a [primeira tarefa no Codex](CODEX_NEXT_TASK.md).
2. **Conduzir as verificações externas como trilhas independentes:** JT-006 valida instalação/abertura/diagnóstico em Windows e exige logs sanitizados caso falhe; JT-007 formaliza exportação autorizada, IDs, símbolo, relógios, agressor, correções e perda de eventos. A indisponibilidade desses ambientes não bloqueia o ciclo local. Windows é gate para anunciar distribuição validada; o contrato da fonte é gate para experimentos que exigem dados reais. Nenhuma trilha confirma por si só a correção da falha anterior ou tape integral.
3. **Preparar e executar os experimentos próprios:** com dados/acesso/orçamento apropriados, congelar o protocolo, apurar desfechos causalmente e comparar regras, quantitativo e quantitativo+JEV com divisões temporais, custos/execução e teste futuro separado; incluir abstenções e falhas. Instrumentação local não conclui E01–E10.
4. **Estudar exposição por vantagem após os fundamentos:** com distribuição de resultados e conta conciliada, comparar quantidades menores que o teto e incerteza. Execução de ordens é uma etapa adicional, ainda sem implementação.

## Proveniência e manutenção

Este é o registro canônico de status; o [PRD](PRD.md) define intenção e a [arquitetura](ARCHITECTURE.md) descreve o código. [`archive/Projeto_JEV_Profit.md`](archive/Projeto_JEV_Profit.md) e documentos herdados preservam afirmações e nomes da entrega anterior. Atualizações devem registrar data, alteração, evidência e alcance da execução. Uma capacidade só passa de “pendente” a “verificada” com evidência no ambiente correspondente; aprovação de testes locais não promove o projeto a ferramenta operacional ou lucrativa.

## Registro de 06/10/2026 — sessão Windows (máquina do usuário)

- **Primeira abertura nativa registrada:** a janela Tkinter abriu em Windows 11 com Python 3.14.7 (a máquina não tem `py -3.12`; o `.venv` foi criado manualmente equivalente ao `setup-windows.ps1`, que também falha por quoting quando invocado via Git Bash). Autoteste `--self-test` aprovado nesta máquina (`.artifacts/desktop-self-test.json`). Isto cobre a abertura da janela; aparência/uso prolongado e COM/RTD real seguem pendentes (JT-006 não está concluído).
- **Suíte reproduzida em Windows:** 167 testes `unittest` aprovados (antes: 5 falhas). Correções: dois testes de controlador fechavam o diário SQLite só no `addCleanup`, após a remoção do `TemporaryDirectory` (WinError 32; Linux mascarava); três testes da ponte Excel presumiam `comtypes` ausente — agora forçam `reader._com_modules = None` para exercitar o fallback PowerShell pretendido em qualquer ambiente; `verify.py` deixou de quebrar em console cp1252 ao imprimir logs com `\ufffd`.
- **Mudança de interface (não altera capacidade):** as oito abas viraram sete — nova home **Copiloto** centrada no JEV (estado da fonte, medidas, faixa de contexto com validade, conclusão), **Conexões+JEV** fundidas em **Configuração**, e campo **Sua leitura**: texto declarado pelo usuário entra no estado JEV como `state.user_premise` e recebe três Nouls independentes (`premise_evidence_support`, `premise_evidence_contradiction`, `premise_evaluable`), mantendo apoio/contradição/suficiência como dimensões separadas. É a direção de JT-002/JT-003 no trecho da premissa, mas **não conclui** esses tickets (premissa do motor de candidatos continua fora do payload). Nenhuma chamada autenticada ao JEV foi feita; o JEV segue sem observar ações do usuário no Profit — posição/ordens exigem ProfitDLL roteamento (JT-014).

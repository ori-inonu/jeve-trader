# RT-12 — evidência e dependências do próximo ciclo

> Publication projection: personal checkout paths and the conversation UUID are omitted. Non-personal task and reviewer role labels are retained as provenance. Acceptance, findings, source hashes and measured results are unchanged. Raw source SHA-256: 607acb62c3df7c05bbf93298814c2282f690de7dfcd367fef85ad6c991b1ef73

Pesquisa de 09/10/2026, sobre `5f15ab73f4f5adfd3221b9bd5f785c24c9afc496`, no checkout isolado `{research_checkout}`. Este relatório prepara alternativas e aceites candidatos; não aprova uma SPEC, não revisa o próprio trabalho e não certifica o PR. O coordenador conserva o ticket canônico RT-12.

O próximo incremento com melhor fundamento local é estabelecer a identidade do pacote e a baseline da jornada nativa, com observabilidade limitada. A qualificação documental B3 pode avançar em paralelo. A integração real de conta depende de uma fonte/formato autorizado e não deve ser inferida da presença do ledger. Essa é uma recomendação condicionada às dependências observadas, para avaliação consultiva do JEV e revisão independente.

## Contratos que permanecem fixos

O draft do próximo ciclo exige jornada Windows, comparador prospectivo da mesma tarefa, métricas sanitizadas e distinção entre build, instalação, comportamento nativo e ganho. A SPEC finita mantém conexão explícita, BTCUSDT spot público, cobertura parcial/L1, ordens desligadas, JEV desligado por padrão, risco Decimal e `WAIT/q=0`; resultados financeiros desconhecidos continuam `null`. A qualificação B3 e a conta privada permanecem dependências externas. [L04, L05, L02, L03]

Não há autorização nesta pesquisa para instalar ferramentas/plugins, executar instalação/release, comprar feed, entrar em conta privada, enviar ordens, chamar o JEV do produto ou publicar resultados. Não foram consultados ambientes, credenciais, diários nem dados privados. A fronteira Wayfinder inclui a evidência nativa, qualificação B3 e importação read-only; tickets históricos de grilling não recebem respostas humanas inventadas. [L01, L06–L09]

## Capacidades observadas

Inspeção somente de leitura, em 09/10/2026 às 12:02 UTC; a presença do NSIS foi conferida separadamente neste trabalho, antes da captura das fontes às 12:09 UTC. Os resultados abaixo são observações do host, não pré-requisitos integralmente certificados.

| Capacidade | Resultado literal/observado | Proveniência e limite |
|---|---|---|
| Windows | `Microsoft Windows NT 10.0.26300.0` | `[Environment]::OSVersion.VersionString`; não houve exercício da janela. |
| Python / Node | `Python 3.14.7` / `v26.9.0` | `python --version`, `node --version`; não certificam dependências de empacotamento. |
| Rust MSVC | `rustc 1.99.0 (b940084d7 2026-09-28)`; `cargo 1.99.0 (5f94df478 2026-08-27)`; `stable-x86_64-pc-windows-msvc (default)` | Comandos de versão e toolchain ativo, sem compilação. |
| C++ Build Tools | `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools` | `vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`. `cl` e `msbuild` não apareceram no PATH; isso não prova ausência do componente. |
| WebView2 | Pasta `154.0.4258.62`, com `msedgewebview2.exe` | Diretório fixo `C:/Program Files (x86)/Microsoft/EdgeWebView/Application`; versão compatível de driver ainda não observada. |
| NSIS | `C:/Program Files (x86)/NSIS/makensis.exe` presente | `Test-Path` do caminho fixo; versão e build não exercitados. |
| Dependências do checkout | `.venv/Scripts/python.exe` ausente; `desktop/node_modules` ausente | `Test-Path` dos dois alvos; Python/Node globais não substituem esses alvos do script. |
| Automação nativa | CUA nativo desabilitado nesta tarefa; `tauri-driver`, `msedgedriver`, `Appium`, `WinAppDriver` não encontrados no PATH | Limite declarado da ferramenta e `Get-Command`; não é uma busca global nem prova ausência em todo o host. |
| Binário existente | `%LOCALAPPDATA%/Programs/JevWIN/JevWIN.exe`, versão PE `0.5.4`, SHA-256 `6625a09e5a53ffd66183a503853fb1249827d45b4a6cf964136e4718eafd6f03` | Metadados e hash do arquivo; commit de origem `null`. Não foi aberto. A versão é compartilhada com o código atual e não identifica o PR. |
| Build / instalação / jornada / ganho do candidato | `null` / `null` / `null` / `null` | Nenhum desses procedimentos foi executado pelo pesquisador. |

Tauri exige C++ Build Tools e WebView2 no Windows. O inventário encontra esses componentes, mas o script local também exige `.venv`, Cargo, NSIS, preparação OCR, dependências Python/npm, frontend, sidecar e compilação Rust. O script oferece `-IsolatedInstaller` e gera um `package-manifest.json` com hashes dos arquivos; é necessário vinculá-lo também ao commit/árvore realmente construídos. [Pré-requisitos Tauri](https://v2.tauri.app/start/prerequisites/), [L20, L21]

O projeto não declara dependências WebdriverIO nem plugin WebDriver nos manifests inspecionados. A documentação Tauri atual recomenda `@wdio/tauri-service`, cujo servidor padrão é embutido no aplicativo; também descreve a alternativa direta `tauri-driver`. O modo navegador continua distinto do binário Tauri. A rota direta no Windows depende de Microsoft Edge Driver compatível; a Microsoft exige correspondência com a versão do runtime WebView2. Não instalar nenhuma dessas rotas por inferência nesta pesquisa. [WebDriver Tauri](https://v2.tauri.app/develop/tests/webdriver/), [configuração manual](https://v2.tauri.app/develop/tests/webdriver/manual-setup/), [WebView2/Microsoft Edge WebDriver](https://learn.microsoft.com/en-us/microsoft-edge/webview2/how-to/webdriver), [L16, L19]

A prévia existente exercitou BTCUSDT público, teclado, legado/retorno, frescor após parar o backend e largura 390×844 no navegador. Seu próprio registro contém `native_window_verified: false`, `paired_manual_step_gain: null` e GPU `null`. Além disso, a configuração nativa limita a janela a 600×640: 390 pixels no navegador não comprovam esse comportamento Windows. [L13, L15]

O transporte nativo usa `listen('engine')` e IPC, enquanto o navegador usa eventos Vite e POST `'/__engine'`. O fechamento do host tem supervisão do sidecar por job Windows e encerramento/espera; o efeito real precisa ser observado no processo pertencente ao ensaio. [L18, L26–L28]

## Significado das medições

Evidência literal: `measurement_scope: { gpu: 'not_measured', native_windows_ui: 'not_measured' }` em `desktop/src/multimarketModel.ts:185`. O exportador admite somente `events`, `duplicates`, `rejected`, `overflow`, `process_p95_ms`, `market_lag_ms`, `rss_bytes` e estados dos quatro gates; força GPU a `null`. Não exporta conta nem payload de mercado. [L30]

Evidência literal: `self.metrics['market_lag_ms'] = max(0, item.received_at_ms-item.market_ts_ms)` em `app/multimarket/service.py:319`. Essa diferença usa timestamps de parede e trunca valores negativos. Sem offset/incerteza dos relógios, ela é uma idade aparente entre origem e recebimento, não uma medição isolada do transporte. O p95 atual usa `time.perf_counter()` em processamento de lotes pós-recebimento; não inclui renderização nem interação humana. [L23]

| Medida candidata | Como obter sem ampliar a alegação | Resultado atual |
|---|---|---|
| Processamento pós-recebimento | Preservar o workload e o gate da SPEC finita: 1.000 eventos/s por 10 s, p95 de lote ≤50 ms; identificar fixture e máquina | Há evidência sintética anterior; nenhuma nova execução nesta pesquisa. |
| Publicação → recebimento no renderer | Correlacionar sequência/época e documentar os domínios de relógio; subtração entre relógios sem calibração é inválida | `null`; instrumentação específica ainda necessária. |
| Recebimento → commit React | Marcas no mesmo domínio `performance.now()`, associadas à identidade/sequence; sem payload | `null`; não atribuir esse tempo a GPU. |
| Oportunidade de pintura | Uma observação de RAF deve ser denominada oportunidade de pintura; não comprova apresentação de pixels pelo compositor | `null`. |
| Idade/frescor | Relógio monotônico local e identidade correta; conservar TTL de quote 5 s, trades 30 s, book 2 s e conta 60 s | Contratos locais existentes; jornada nativa ainda `null`. [L24, L25, L30] |
| Memória/GPU | RSS do processo identificado; GPU só com ferramenta/método nativo identificado, sem inferir de RSS | GPU `null`. |
| Ações/intervenções humanas | Observador/operador identificado por pseudônimo, roteiro congelado, início/fim e recuperação inesperada registrados | `null`; script WebDriver não equivale a observação humana. |

Campos de uma futura evidência: commit e hashes do pacote/sidecar, variante, pseudônimo da sessão/operador, task_id, ordem A/B, dimensões da janela, sistema/runtime, fonte/instrumento, cenário, sequência/época, definição dos relógios, ações, intervenções, duração, gates e falhas. Não registrar preços, trades, saldo, UID, conta, chave, argumentos privados, corpus, transcrição nem imagem com esses dados. Uma captura desconectada pode apoiar layout; não substitui a sequência de eventos da jornada. Resultados ausentes permanecem `null`, nunca zero.

## Comparador e protocolo prospectivo

**Controle A:** o cockpit em `5f15ab73f4f5adfd3221b9bd5f785c24c9afc496`, empacotado e identificado. **Tratamento B:** um futuro commit finito com a melhoria de fluxo, usando o mesmo BTCUSDT spot público, tarefas, estados iniciais e gates. Comparar WIN/Excel no legado com BTC spot altera fonte, mercado e tarefa; não mede redução da mesma intervenção. O legado continua sendo uma etapa de navegação a verificar, não um comparador de ganho cripto. [L04, L05, L10–L12]

O primeiro ciclo estabelece A. Instrumentar a mesma UI sem alterar seu fluxo não cria um ganho. Antes de B, congelar tarefas, método de contagem, condição de conclusão e falhas que invalidam pares. Ensaios automatizados verificam comportamento e tempos de máquina; o ganho humano exige execução prospectiva observada. Cinco pares A/B alternando AB e BA são uma proposta de piloto limitado do mesmo operador, sem generalização populacional; o coordenador/revisor deve fixar amostra e critério antes de coletar.

### Preparação executável, ainda não executada

1. Confirmar árvore limpa e commit do pacote; conferir os hashes de cada arquivo em `package-manifest.json`. Separar hash do instalador, binário Tauri e sidecar. Manter registros individuais de build, instalação e execução, inclusive falhas. O pacote instalado 0.5.4 sem origem conhecida não substitui A.
2. Escolher uma rota de observação realmente disponível: operador com janela visível ou uma ferramenta nativa autorizada. Se só houver navegador, executar o preflight e deixar a aceitação Windows pendente. WebDriver valida o WebView/aplicativo suportado; instalação e diálogos do sistema exigem protocolo próprio. [WebView2 WebDriver](https://learn.microsoft.com/en-us/microsoft-edge/webview2/how-to/webdriver)
3. Usar uma pasta vazia exclusiva do ensaio via `JEV_TRADER_DATA_DIR`, sem abrir dados JevWIN existentes. O launcher já repassa esse valor ao `--data-dir` do sidecar. Não enumerar ambiente nem copiar dados privados. [L18, L22]
4. Na etapa de execução autorizada, a receita abaixo abre apenas o pacote identificado em diretório de dados isolado. Não foi rodada nesta pesquisa; pressupõe pacote existente e acesso de observação nativa.

```powershell
$packageRoot = Join-Path $PWD '.artifacts/desktop-windows/portable'
$manifest = Get-Content -LiteralPath (Join-Path $packageRoot 'package-manifest.json') -Raw | ConvertFrom-Json
foreach ($file in $manifest.files) {
    $target = Join-Path $packageRoot $file.name
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $file.sha256) { throw "Package hash mismatch: $($file.name)" }
}
$runId = [guid]::NewGuid().ToString()
$runData = Join-Path '{private_evidence_directory}/rt12-runs' $runId
$start = [Diagnostics.ProcessStartInfo]::new()
$start.FileName = Join-Path $packageRoot 'JevWIN.exe'
$start.WorkingDirectory = $packageRoot
$start.UseShellExecute = $false
$start.Environment['JEV_TRADER_DATA_DIR'] = $runData
$ownedApp = [Diagnostics.Process]::Start($start)
# Observar o PID $ownedApp.Id e somente seus filhos; registrar hashes/estados sem payload.
```

5. Executar a sequência abaixo primeiro em A. O tempo máximo de espera de 30 s é um limite do ensaio, não SLA do produto. Falha de rede é registrada como tal, sem substituir o resultado por zero ou inventar cotação. A execução ao vivo verifica integração pública; comparação de throughput requer a mesma fixture autorizada e deve continuar rotulada sintética. Não há ponte de replay nativa já demonstrada.

| Jornada | Ação concreta | Condição observável / gate |
|---|---|---|
| J1 — início | Abrir com dados isolados e aguardar a UI até 30 s | Fonte desconectada; nenhuma conexão pública, conta ou chamada JEV automática; ordens desligadas; motivo de WAIT visível. |
| J2 — fonte | Pelo teclado, conectar explicitamente BTCUSDT; observar por 30 s | Descoberta de metadata seguida de atualização sem reload; identidade fonte/venue/segmento/instrumento; L1/parcial explícitos; WAIT/q=0 e resultados desconhecidos. |
| J3 — navegação | Abrir legado e voltar ao cockpit, pelo teclado | Foco utilizável; dados voltam a atualizar sem subscription duplicada/reload; nenhuma ativação JEV. Repetir nas dimensões padrão 1440×960 e mínima 600×640. |
| J4 — interrupção controlada | Desconectar e reconectar explicitamente; em execução de falha separada, interromper somente o sidecar do ensaio | Estado/cause visível e quote/trades vencem nos TTL contratuais; valores vencidos deixam de parecer atuais. Reconexão não reaproveita contexto anterior. Registrar o caminho real de recuperação do motor, inclusive reabertura se necessária; não presumir restart automático. |
| J5 — término | Fechar a janela do ensaio | Identificar o PID do sidecar pertencente ao ensaio e verificar sua saída em até 5 s; registrar orphan/falha. Não matar processos externos nem desligar rede do host. |
| J6 — fronteira OFF | Em uma variante de teste identificada, com executor JEV local stub, enfileirar trabalho e manter uma barreira imediatamente antes do dispatch; acionar OFF pelo teclado, observar o acknowledgement e então liberar a barreira | Medir request→ack no mesmo domínio de relógio; nenhum novo dispatch começa após o ack; resultado antigo não volta a ser aceito/exibido; contabilizar chamadas/estado sem payload. Não há chamada ao JEV do produto. |

J6 exige que o stub/barreira esteja realmente ligado ao sidecar da janela candidata, com hashes próprios e isolamento. `configure_jev` oferece injeção no serviço, mas uma ligação de teste até a janela nativa não foi demonstrada. Enquanto faltar essa ligação, delay e resultado Windows de OFF permanecem `null`; regressão de concorrência local não certifica a interação nativa. O timeout do transporte não é meta de latência de OFF. [L23, L26]

Cada tentativa usa dados isolados novos, mesma configuração de custos/conta desconhecida e JEV desligado. Uma tentativa inválida fica registrada e só é repetida com motivo documentado. A comparação inclui cold start ou warm start de forma constante. Ação é uma operação planejada do operador; intervenção é uma recuperação manual inesperada necessária para concluir. Conexão explícita e autorização JEV são controles intencionais: não removê-los para reduzir a contagem.

Ganho só é reportável após pares completos com os mesmos gates de identidade, frescor, cobertura, segurança, acessibilidade e término. Publicar contagens/durações individuais e diferenças pareadas; qualquer resumo deve declarar amostra e método. Não excluir falhas de B para melhorar a mediana, nem traduzir menor esforço em melhor decisão financeira. Até então, ganho e tempo humano permanecem `null`. [L04, L05]

## Alternativas reais e dependências

| Caminho | Trabalho elegível com evidência disponível | Dependências que limitam o resultado | Relação com o objetivo |
|---|---|---|---|
| A — baseline nativa e observabilidade | Congelar protocolo/comparador; vincular pacote ao código; especificar marcas/allowlist e executar preflight local | Dependências de build ausentes no checkout; pacote candidato; acesso/ferramenta de observação nativa; sessão prospectiva humana para afirmar ganho. Nova instalação/plugin não foi autorizada aqui | Verifica a jornada já entregue e dá fundamento para reduzir etapas sem ocultar risco. |
| B — qualificação documental B3 | Dossiê público por fornecedor/SKU: WIN/WDO, metadata, quote/trades/book, sequência/gaps, recovery, entitlement, uso analítico/JEV, retenção/redistribuição, condições e lacunas | A pesquisa atual não fecha SKU, contrato, licença ou acesso. Contato comercial, compra e feed real continuam dependências próprias | Remove incertezas para independência do Profit; não produz integração ou teste ao vivo por si só. [L07, L10] |
| C — importação read-only de conta | Especificar formato/proveniência e importação offline com fixtures autorizadas sobre o ledger já existente | Fonte/formato ainda não fixados; dados reais dependem de autorização. API privada exige credencial/escopos; não há conector real demonstrado | Pode eliminar redigitação de conta; não depende de retirar controles de conexão/JEV nem valida WIN/B3. [L09, L25, L29] |

A fonte pública spot não dá acesso à conta. `GET /api/v3/account` é USER_DATA e assinado, exige chave; dados de saldos e histórico de execuções são contratos diferentes (`/api/v3/myTrades`). Escolher Binance como exemplo documental não escolhe a conta do usuário. Uma importação por arquivo reduz a dependência de API, mas continua exigindo formato e dados autorizados. [API oficial Binance — conta](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/account), [fonte oficial fixada](https://github.com/binance/binance-spot-api-docs/blob/263ac1aa96556af0b4da824c82a1d8cd9a0edda9/rest-api.md)

Não foi reaberta a pesquisa geral B3/cripto sem decisão pendente. O dossiê B3 deve reutilizar seus resultados e registrar exatamente o que falta; listar um distribuidor não prova licença para WIN/WDO ou permissão de processar/reter dados com JEV. [L10, L12]

Para a consulta JEV de prioridade, enviar apenas estas três alternativas, disponibilidade dos gates e fatos públicos sanitizados. A recomendação deve indicar dependências e possibilidade de trabalho independente. Abstinência mantém a pesquisa/documentação elegível e adia apenas o passo dependente. O recibo anterior de prioridade foi abstinência; não é decisão operacional. [L14]

## Aceites candidatos e tarefas para revisão independente

Estes aceites são propostos para o próximo contrato; não foram congelados ou aprovados pelo autor. N-01–N-05 e I-01–I-12 não podem ser enfraquecidos por eles. [L04, L05]

| ID | Aceite observável | Tarefa/dependência e responsável sugerido |
|---|---|---|
| R12-01 | Pacote, sidecar e instalador têm hashes e origem do código; build, instalação, jornada e ganho são registros separados; arquivo instalado sem origem não é candidato | T1, release: build existente, dependências identificadas, escopo de instalação isolada distinto. |
| R12-02 | Schema de telemetria possui allowlist e definição dos relógios/escopo; nenhum saldo/payload/segredo; medidas ausentes `null`; `market_lag_ms` não é renomeado latência de rede | T2, implementação independente: SPEC revisada, marcas de recibo/commit e testes de sanitização. |
| R12-03 | J1–J3 passam na janela Windows real, com fonte/metadata/frescor/cobertura e teclado registrados; 600×640 não tem perda de controles essenciais | T3, verificação: T1, método nativo disponível; preflight navegador não conclui o aceite. |
| R12-04 | J4/J5 registram vencimento, recuperação e encerramento apenas dos processos pertencentes ao ensaio; contexto anterior não reaparece como atual | T3, verificação: ambiente isolado e protocolo de falha autorizado, critérios financeiros preservados. |
| R12-05 | A/B usam mesmo roteiro, instrumento, fonte, estado inicial e operador/método; ordem e falhas são prospectivas; contagem automatizada é distinguida de intervenção humana | T4, avaliação: T3, B finito e sessões observadas; ausência de B permite somente baseline A. |
| R12-06 | Toda alegação de ganho apresenta pares completos, gates intactos, contagens/duração e falhas; não generaliza piloto nem afirma rentabilidade; sem pares o resultado é `null` | T4 e revisor independente: R12-05, critérios congelados antes da coleta. |
| R12-07 | Qualificação B3 entrega matriz fornecedor/SKU/capacidade/licença/entitlement/retention/uso JEV, com literal, URL, versão/hash e desconhecidos explícitos; nenhum feed é promovido por documentação | T5, pesquisador distinto: reutilizar RT-01/RT-10; contrato/acesso permanecem externos. |
| R12-08 | Antes de importar conta real, formato/proveniência e escopo read-only são explícitos; fixtures verificam Decimal, revisão, duplicação/conflito e frescor; nenhum endpoint de ordens ou saldo no contexto JEV | T6, pesquisador/implementador separados: escolha de formato e autorização dos dados; API privada depende também de credencial/escopo. |
| R12-09 | J6 observa request→ack de OFF na janela real com stub local identificado; após o ack há zero novos dispatches e contexto anterior não é reativado; prazo/resultados não exercitados são `null` | T3 e revisor independente: correção de concorrência sob sua SPEC de regressão, ligação do stub à variante nativa e barreira controlada; não requer API paga. |

T1/T2/T5 podem ter especificações delimitadas sem resolver conta privada. T3 depende de acesso nativo real; T4 depende de T3 e uma melhoria B comparável. T6 não deve receber dados privados para contornar a escolha pendente. O pesquisador não implementa T1–T6 nem certifica esses aceites.

## Fontes e integridade

Todos os caminhos Lxx são relativos à base absoluta `{research_checkout}`; seus hashes SHA-256 identificam bytes observados antes de escrever este relatório. O estado histórico de uma pesquisa não substitui o código atual.

| ID | Caminho local | SHA-256 |
|---|---|---|
| L01 | `AGENTS.md` | `65ff3937f04f44714517aa769fd64cb69b4242beb659ba8430ddbc16f59f8a95` |
| L02 | `docs/HANDOFF.md` | `da34d8191e0643515127f59b12add0756a7ed949bff762451b74eb88baea4aeb` |
| L03 | `docs/SDD.md` | `311a2253ca0fed242ae613f5ab026131a10de3a6320fc7f853329573db0a40dd` |
| L04 | `docs/specs/Multimercado_Proximo_Ciclo_2026-10-09.md` | `fff2b8adb6ef815fcc70ead80f1ff46e91d4bd60ba5a7e7bb3239b078c46c632` |
| L05 | `docs/specs/Multimercado_Implementacao_2026-10-09.md` | `af174497bf764b1a7c67818cee6e3b925a40933d98c40c8e14f5b1b0f6bc01f4` |
| L06 | `.scratch/wayfinder-multimercado/map.md` | `cb7e0e62fc6f53360adc31862600ee75fc1f99a0ca0928472d5e6bdf1dbd5795` |
| L07 | `.scratch/wayfinder-multimercado/issues/10-qualificacao-b3.md` | `dbd8ebfe4727a4cbc6e09898bf3be26ef88a0a3bab9a647d588b6fb9e8f81266` |
| L08 | `.scratch/wayfinder-multimercado/issues/12-evidencia-proximo-ciclo.md` | `6b93c9fbaa8919521114c040a87ebec0b5ecd64b1e95d035523d8e95fd45c7c6` |
| L09 | `.scratch/wayfinder-multimercado/issues/08-automacao-conta.md` | `54d19faa8d064dd9f59c87fad69749f2a61507cd51e8d74e41182c62995d7eb0` |
| L10 | `docs/research/B3_Dados_Independentes_2026-10-09.md` | `ddb756cce3675113639bf366a13fd76f84a6b781dd3bf29c27441cc6c3e819fa` |
| L11 | `docs/research/Arquitetura_Multimercado_Lacunas_2026-10-09.md` | `c4860a714cde60a654d6bb0cd30e26b03454830b126a326d1818c8dbac75cc90` |
| L12 | `docs/research/Cripto_Streaming_Contratos_2026-10-09.md` | `2757599314e0401b262dde35773d6199973e2666358eaac76eec918528be8abc` |
| L13 | `docs/evidence/multimarket-ui-validation.json` | `d2481dfc7a76850b21c00cdac4cba49b65bc38f75c65b8aca00dbe19f9a109ca` |
| L14 | `docs/evidence/multimarket-next-cycle-jev.json` | `23692dc88e44c079886a7b7d6cadcd02667852f3af0fe6ff2f26a6fbd6b37d16` |
| L15 | `desktop/src-tauri/tauri.conf.json` | `a3ccca01c932c14f69525de0c16dfd3922d55fcae5d84c287e58de6c7f5e5466` |
| L16 | `desktop/src-tauri/Cargo.toml` | `856ec8f16a2490ac7abdcc59bc415a071cbb5137a9878203e7800ddd76dbc620` |
| L17 | `desktop/src-tauri/capabilities/default.json` | `332d82b949934f7b6d3a514e4ec55bd45fc6663e41e2bca8298995f7fd05e982` |
| L18 | `desktop/src-tauri/src/main.rs` | `24e2fa9ea67bf2ca70ef6c997b148c336d5b2fe1f1e22a087607617c166208bd` |
| L19 | `desktop/package.json` | `f63cd7a2276646c36a718d92e5f4d4c1132854698216a4f6c79b1422a42d3e46` |
| L20 | `desktop/build-windows.ps1` | `50b506bd110ad789801dd28bd178b1ef123f77e32cb3eaede4f64e7384359938` |
| L21 | `app/WINDOWS_BUILD.md` | `f56a585f7594cb9759770d40403c325951067a2ac2c30e94e75370c6f04b1dd3` |
| L22 | `app/desktop_service.py` | `5c87818980264220447150b3840f81e1f9ed93bbd1618cf8eb7d1cd1c8984d16` |
| L23 | `app/multimarket/service.py` | `b87386d071b9e1b1d10c4fdca23b1a8d3f3f5af513bc269f81926cce42af2d00` |
| L24 | `app/multimarket/market_state.py` | `1068797c845b2b4089cc3cc9d17305362b4f05100e14f0aa81c75d4a3fe4941a` |
| L25 | `app/multimarket/accounts.py` | `19a927a1b1254601feee77ec1cd47591494137e123a034adb818b35f4e00fb6d` |
| L26 | `desktop/src/multimarketTransport.ts` | `889a3afab4dd9d03077e9fcde2a9dda01be169ecf58182748fdf055ab5090880` |
| L27 | `desktop/src/MultimarketRoot.tsx` | `89ab772b5a455a734fda75c8f5d3d924b35989a59a0967567d740a3b002a0a0f` |
| L28 | `desktop/src/multimarketSubscriptions.ts` | `8062fb3036c383bda9bea197fb82eb9a95917c8b6fe85d561261bbac65c50c94` |
| L29 | `desktop/src/MultimarketCockpit.tsx` | `bd773a327c6a0ae29b111d17b8a0c29aa55e50a7ce45450987022f0264d5ae3e` |
| L30 | `desktop/src/multimarketModel.ts` | `c270f4cb8cfa90218661e19364643de689f7e18419b3a40c1d15df5a3a1f0ef3` |

Fontes públicas consultadas com `web` e corpos HTTP públicos capturados para hash em 09/10/2026 às 12:09–12:10 UTC. Hash de corpo HTML identifica aquela resposta, não garante imutabilidade futura. A captura direta de duas páginas Binance retornou HTTP 202 com zero bytes: hash de conteúdo documental ficou `null`; o conteúdo foi lido pelo navegador de pesquisa e corroborado no repositório oficial fixado abaixo.

| Fonte pública | SHA-256 do conteúdo observado |
|---|---|
| [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/) | `d51d336f63f051b53cdd93a944be88d6f03e7bd87d61706d046ec65bcb2f0934` |
| [Tauri WebDriver](https://v2.tauri.app/develop/tests/webdriver/) | `1455d6179737613e3d4c6bf7d692b1b33de0cd063a1756d99938fd8dd48bda73` |
| [Tauri manual setup](https://v2.tauri.app/develop/tests/webdriver/manual-setup/) | `0f5285d281beb0f4bed9f1e7522998016478d1827b6c002247075118e0f735f3` |
| [Microsoft WebView2 WebDriver](https://learn.microsoft.com/en-us/microsoft-edge/webview2/how-to/webdriver) | `aa5aadeb4323c420a9b55b9898ce76804933b41d84099f3749fdaf8114ac6723` |
| [Binance REST oficial, commit 263ac1aa96556af0b4da824c82a1d8cd9a0edda9](https://raw.githubusercontent.com/binance/binance-spot-api-docs/263ac1aa96556af0b4da824c82a1d8cd9a0edda9/rest-api.md) | `49ea6809243fc7fb426e07f2fe662097736c7bb405bd2da5eef637d715427999` |

Evidência literal externa delimitada: `GET /api/v3/account` (linha 4176) e `GET /api/v3/myTrades` (linha 4572) no REST oficial fixado. A ausência de chave/escopo não é suprida por essas referências. Não foram feitas requisições aos endpoints de conta.

O integrador comunicou durante esta pesquisa: `cargo check --locked --offline` concluído em 5f15, 322 testes backend e autoteste, 36 testes frontend e build; também comunicou achados de concorrência no OFF e deduplicação sem limite, com correção sob SPEC de regressão distinta. Esses relatos não foram executados nem certificados pelo pesquisador, não atualizam os hashes desta baseline e não comprovam janela Windows. A SPEC de regressão e a revisão da correção devem ser ligadas pelo integrador ao contrato seguinte.

Verificação da pesquisa: leitura de contratos/código, hashes, inventário delimitado do host e documentação primária. Não foram executados testes de produto, build, instalação, janela nativa, coleta de conta, feed B3 nem avaliação pareada. O próximo passo é revisão independente deste fundamento e seleção consultiva de um contrato finito elegível; nenhuma conclusão de ganho foi antecipada.

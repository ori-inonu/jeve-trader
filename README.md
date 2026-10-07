# Jeve Trader

Copiloto experimental de leitura de fluxo para o **mini índice WIN da B3**, desenvolvido para acompanhar o **Profit Pro no Windows** com avaliações contextuais do **JEV, da TypeSafe AI**.

O painel experimental **0.4.0** usa Tauri 2, React, TypeScript, Vite, Tailwind CSS 4 e ECharts, com motor Python independente. A baseline **JevWIN v0.3.0** e seus dados continuam preservados. Veja o [guia do painel moderno](docs/DECISION_PANEL.md) para abrir, configurar Excel/Profit, registrar execuções manuais e reproduzir a distribuição Windows.

## Começar pelo ponto certo

- **Continuar a implementação no Codex:** leia [docs/HANDOFF.md](docs/HANDOFF.md) e use [docs/CODEX_NEXT_TASK.md](docs/CODEX_NEXT_TASK.md).
- **Entender o que já funciona e o que falta verificar:** [estado da implementação](docs/IMPLEMENTATION_STATUS.md).
- **Preparar o computador e executar verificações:** [desenvolvimento](docs/DEVELOPMENT.md).
- **Configurar o ambiente Codex:** [guia Codex](docs/CODEX.md).
- **Ver a sequência de trabalho:** [roadmap](docs/ROADMAP.md) e [backlog](docs/BACKLOG.md).

## Obter o projeto

O repositório privado é [ori-inonu/jeve-trader](https://github.com/ori-inonu/jeve-trader), na branch `main`. Com acesso a essa conta/repositório, clone a versão publicada e abra a pasta no Codex ou no editor:

```bash
git clone https://github.com/ori-inonu/jeve-trader.git
cd jeve-trader
```

O **ambiente remoto no Codex ainda está pendente**. Consulte [docs/CODEX.md](docs/CODEX.md) para sua configuração e [docs/TRANSFER_STATUS.json](docs/TRANSFER_STATUS.json) para o estado confirmado.

Os ZIPs entregues anteriormente são snapshots da preparação anterior à publicação. O histórico Git local dessa fase fica preservado separadamente em [docs/archive/Jeve_Trader_Historico_2026-10-06.bundle](docs/archive/Jeve_Trader_Historico_2026-10-06.bundle); a publicação tem história remota própria. Para continuidade, use o clone GitHub. O bundle é arquivo de consulta/recuperação histórica, não uma branch a empurrar sobre `main`. [Guia de transferência](docs/TRANSFER_GUIDE.md).

## Estado real

O painel tem quatro áreas: Decisão, Capital, Pesquisa e Configuração. O serviço Python calcula planos com `Decimal`, incluindo aguardar e quantidades admissíveis dentro do limite computacional documentado; usa toda a banca informada, preserva seu pico e registra entradas e saídas parciais efetivamente informadas. Não há parada por lucro nem pausa automática em drawdown de 30%. Excel/COM roda em processo separado; a cobertura disponível continua parcial. As avaliações JEV preservam a premissa exata e separam apoio, contradição e insuficiência.

Em 07/10/2026 passaram **188 testes e autoteste em Windows**. O novo pacote foi instalado, aberto, reinstalado e desinstalado em ambiente isolado Windows x64, preservando dados e encerrando os processos filhos. Os formulários React foram verificados na prévia local; interações dentro da janela nativa e RTD real ainda precisam de validação. [Evidência e alcance](docs/IMPLEMENTATION_STATUS.md).

O laboratório offline implementa replay causal, regressão logística multiclasse, calibração temporal, comparação com/sem atributos JEV e 17 políticas experimentais. Seu smoke test usa dados sintéticos. **Não há envio de ordens, conciliação automática, modelo financeiro aprovado para o painel ou vantagem econômica demonstrada.** A recomendação principal permanece aguardar, e a probabilidade de lucro aparece como “não estimada”. A conexão de um modelo financeiro aprovado e do Choice econômico ao serviço faz parte da continuação documentada; nenhum relatório sintético libera essa etapa.

## Desenvolvimento no Windows

Com Python 3.12 x64, incluindo Tcl/Tk, instalado:

```powershell
powershell -File .\scripts\setup-windows.ps1
.\.venv\Scripts\python.exe .\scripts\verify.py
.\.venv\Scripts\python.exe .\app\desktop_app.py
```

Os comandos não configuram a conta da corretora nem habilitam o envio de ordens. O aplicativo tem exemplos locais para exploração sem chave. Uma chave TypeSafe só é necessária para consultas autenticadas e deve ser fornecida localmente; não a grave no repositório.

Para gerar o instalador, veja [app/WINDOWS_BUILD.md](app/WINDOWS_BUILD.md). O script de build fica em `app/build_windows.ps1` e exige NSIS e os pré-requisitos documentados.

Para o painel moderno, use `powershell -File .\scripts\start-desktop.ps1`; o build Tauri/Python fica em `desktop/build-windows.ps1` e requer PowerShell 7. Pré-requisitos e diagnóstico estão em [docs/DECISION_PANEL.md](docs/DECISION_PANEL.md).

## Desenvolvimento no Codex/Linux

```bash
bash scripts/setup-codex.sh
.venv/bin/python scripts/verify.py
```

O ambiente Linux valida componentes sem abrir a janela. Ele não substitui Windows, Excel e Profit para verificar a integração real. O workflow de CI é iniciado manualmente, sem disparo automático no primeiro envio.

## Mapa do repositório

| Caminho | Responsabilidade |
|---|---|
| `app/` | Baseline preservada, serviço Python, contratos, diário financeiro, laboratório e testes. |
| `desktop/` | Painel React, host Tauri, transporte e empacotamento Windows 0.4.0. |
| `docs/PRD.md` | Objetivo, escopo e critérios do produto. |
| `docs/ARCHITECTURE.md` | Componentes, dados e limites de responsabilidade. |
| `docs/IMPLEMENTATION_STATUS.md` | Evidência disponível e pendências. |
| `docs/research/` | Pesquisa aprofundada, plano E01–E10 e reprodução. |
| `docs/archive/` | Especificações e guias históricos desta conversa. |
| `docs/evidence/` | Relatórios históricos e evidência da organização do projeto. |
| `docs/decisions/` | Registro das decisões de arquitetura. |
| `scripts/` | Preparação e verificação do ambiente. |
| `AGENTS.md` | Instruções curtas para agentes que trabalham no projeto. |

A documentação canônica descreve o estado atual. Os documentos históricos conservam decisões e contexto da época; consulte a proveniência antes de tratar um número de margem, custo ou parâmetro como atual.

## Retomada

A fundação e o painel moderno estão implementados, com evidência de software e distribuição. A continuação exige contrato real da fonte, dados WIN autorizados, validação financeira temporal e integração do modelo aprovado ao serviço. Veja [HANDOFF.md](docs/HANDOFF.md) e os estados por item no backlog.

O status de publicação e vinculação ao Codex está em [docs/TRANSFER_STATUS.json](docs/TRANSFER_STATUS.json). A presença destes arquivos não cria, por si só, um ambiente remoto no Codex.

Licenças das dependências distribuídas anteriormente estão em `app/licenses/`. Não foi escolhida uma licença de código aberto para o código do projeto.

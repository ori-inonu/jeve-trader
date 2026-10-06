# Jeve Trader

Copiloto experimental de leitura de fluxo para o **mini índice WIN da B3**, desenvolvido para acompanhar o **Profit Pro no Windows** com avaliações contextuais do **JEV, da TypeSafe AI**.

Este repositório reúne o código e o trabalho desta conversa em uma base portátil para continuar no Codex. O aplicativo importado é o **JevWIN v0.3.0**. O nome do projeto passa a ser **Jeve Trader**; os nomes internos, caminhos de dados e instaladores permanecem preservados até uma migração explícita.

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

Há interface Tk, leitura de Excel por COM nos modos `quote`, `tape` e `combined`, importação CSV, medidas de fluxo, cenários geométricos, laboratório de capital/risco, cliente JEV, diário local e empacotamento Windows com NSIS. As fontes de negócios disponíveis mantêm cobertura parcial.

O acompanhamento é de observação e pesquisa: **não há envio de ordens, conciliação automática da conta, probabilidade financeira calibrada ou vantagem econômica demonstrada**. O instalador foi gerado e inspecionado; a instalação, a interface e a conexão real com Profit/Excel ainda precisam de validação nativa no Windows. A causa da falha do EXE relatada pelo usuário permanece desconhecida.

As pesquisas de melhoria estão documentadas e ainda não foram aplicadas à versão 0.3.0. Testes de software e exemplos sintéticos não representam operações observadas no mercado.

## Desenvolvimento no Windows

Com Python 3.12 x64, incluindo Tcl/Tk, instalado:

```powershell
powershell -File .\scripts\setup-windows.ps1
.\.venv\Scripts\python.exe .\scripts\verify.py
.\.venv\Scripts\python.exe .\app\desktop_app.py
```

Os comandos não configuram a conta da corretora nem habilitam o envio de ordens. O aplicativo tem exemplos locais para exploração sem chave. Uma chave TypeSafe só é necessária para consultas autenticadas e deve ser fornecida localmente; não a grave no repositório.

Para gerar o instalador, veja [app/WINDOWS_BUILD.md](app/WINDOWS_BUILD.md). O script de build fica em `app/build_windows.ps1` e exige NSIS e os pré-requisitos documentados.

## Desenvolvimento no Codex/Linux

```bash
bash scripts/setup-codex.sh
.venv/bin/python scripts/verify.py
```

O ambiente Linux valida componentes sem abrir a janela. Ele não substitui Windows, Excel e Profit para verificar a integração real. O workflow de CI é iniciado manualmente, sem disparo automático no primeiro envio.

## Mapa do repositório

| Caminho | Responsabilidade |
|---|---|
| `app/` | Baseline v0.3.0: aplicativo, testes, configurações, templates e distribuição. |
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

O primeiro ciclo implementa premissas explícitas, separação entre apoio/contradição/insuficiência e registro reproduzível das avaliações. Captura real, latência, apuração de resultados, comparação com uma base sem JEV e dimensionamento econômico têm etapas e critérios próprios no backlog.

O status de publicação e vinculação ao Codex está em [docs/TRANSFER_STATUS.json](docs/TRANSFER_STATUS.json). A presença destes arquivos não cria, por si só, um ambiente remoto no Codex.

Licenças das dependências distribuídas anteriormente estão em `app/licenses/`. Não foi escolhida uma licença de código aberto para o código do projeto.

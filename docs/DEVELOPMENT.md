# Desenvolvimento e verificação offline

O aplicativo em `app/` conserva sua estrutura original de módulos Python no
mesmo diretório. Execute os comandos próprios do aplicativo dentro de `app/` ou
use os scripts abaixo a partir de qualquer diretório. Os scripts localizam o
repositório pelo próprio caminho; ativar o ambiente virtual é opcional. Não use
`pip install -e .`: este repositório não transforma o aplicativo em um pacote
Python instalável.

## Requisitos do ambiente

Use Python **3.12** para desenvolvimento e distribuição Windows. O código do
núcleo exige Python **3.10 ou posterior**, mas as evidências registradas aqui
foram produzidas com Python 3.12 no Linux, sem uma matriz de testes com várias
versões ou Windows. A compilação Windows exige especificamente o Python oficial
para Windows **3.12 x64**.

As dependências mínimas estão em `app/requirements-runtime.txt`:

- `tzdata==2025.2` fornece dados portáveis de fusos horários.
- `comtypes==1.4.17` é instalado somente no Windows e permite acesso ao Excel via COM.
- Os componentes Tcl/Tk vêm com a instalação do Python, não com pip.
  `desktop_app.py` importa `tkinter` inclusive no modo de autoteste; os testes
  offline do controlador e o autoteste desktop precisam dessa importação.
  Eles **não** criam uma janela e não precisam de display, Xvfb, Excel ou Profit.

Não há requisito de pytest nem de SDK de modelo. A suíte usa `unittest`, da
biblioteca padrão do Python; os testes de HTTP e COM usam respostas sintéticas
e objetos simulados.

## Linux / Codex

Na raiz do repositório:

```bash
bash scripts/setup-codex.sh
.venv/bin/python scripts/verify.py
```

O script de preparação prefere `python3.12`, depois `python3`. Para escolher
outro interpretador:

```bash
PYTHON=/path/to/python3.12 bash scripts/setup-codex.sh
```

Ele cria `.venv` quando ausente e o reutiliza nas execuções seguintes. Instala
somente as dependências de execução, sem atualizar pip ou instalar ferramentas
de empacotamento, e verifica Python/Tk e o fuso de São Paulo. Se um `.venv`
existente usar o interpretador errado, remova ou mova esse ambiente descartável
e execute a preparação novamente. No Debian/Ubuntu, uma instalação Python sem
esses componentes pode exigir os pacotes de sistema correspondentes
`python3-venv` e `python3-tk`; o script informa o erro de pré-requisito sem
alterar pacotes do sistema por conta própria.

A instalação de dependências normalmente precisa de acesso a um índice de
pacotes. Em um ambiente restrito, forneça arquivos wheel autorizados e use as
configurações offline do pip:

```bash
PIP_NO_INDEX=1 PIP_FIND_LINKS=/path/to/wheels bash scripts/setup-codex.sh
```

A verificação não instala nada nem exige acesso à internet. Se o interpretador
disponível já tiver Tk e dados de fusos horários, pode executar o verificador
diretamente, sem preparar um ambiente virtual:

```bash
python3 scripts/verify.py
```

A preparação não ativa o ambiente no shell que a chamou. Use o caminho do
Python do ambiente explicitamente e configure o Codex para executar o script
ao preparar uma cópia nova do repositório. Essa etapa não exige chaves de API,
configuração de conta ou chamadas a modelos.

### Preparação validada neste ambiente

A preparação foi executada com sucesso em um `.venv` novo, usando apenas um
wheel autorizado de `tzdata==2025.2` já disponível localmente, com
`PIP_NO_INDEX=1`. Uma segunda execução também passou, reutilizando o ambiente
e a dependência instalada. A suíte de **166 testes** e o autoteste desktop
passaram com o Python **3.12.14** desse `.venv`, `tzdata==2025.2` e Tk **9.0**.
A dependência `comtypes` foi corretamente ignorada pelo marcador de plataforma
no Linux. Os resultados estão em `.artifacts/verification.json` e
`.artifacts/setup-codex-validation.json`; o log da segunda preparação está em
`.artifacts/setup-codex.log`. Isso não valida a preparação ou a interface no
Windows, nem outros ambientes Linux ou versões de Python.

## Desenvolvimento no Windows

Instale o Python oficial para Windows 3.12 com Tcl/Tk. Na raiz do repositório,
em PowerShell e sob a política de execução já existente na máquina:

```powershell
powershell -File .\scripts\setup-windows.ps1
.\.venv\Scripts\python.exe .\scripts\verify.py
.\.venv\Scripts\python.exe .\app\desktop_app.py
```

Para usar um interpretador em outro local:

```powershell
.\scripts\setup-windows.ps1 -Python 'C:\Path\To\Python312\python.exe'
```

O padrão usa `py -3.12`. A preparação cria ou reutiliza o `.venv` da raiz e
instala as dependências de execução para Windows, incluindo `comtypes`. Não
instala Profit, Excel ou NSIS, altera políticas de execução, desativa Defender
ou concede permissões. Se a política existente impedir a execução de scripts,
a mesma preparação pode ser feita com comandos individuais, sem alterar essa
política:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\app\requirements-runtime.txt
.\.venv\Scripts\python.exe .\scripts\verify.py
```

O comando explícito `desktop_app.py` do primeiro exemplo abre a interface.
O verificador executa `--self-test`, que não abre uma janela. A integração real
com Excel/Profit exige um teste Windows separado e autorizado, com esses
aplicativos instalados e configurados. O script Windows foi inspecionado, mas
não executado em Windows neste ambiente.

## O que a verificação faz

`scripts/verify.py` inicia as duas verificações com o interpretador que o chamou,
define o diretório de trabalho de cada subprocesso como `app/` e usa `-E -s -B`
para ignorar opções de ambiente do Python, excluir pacotes do diretório de
usuário e evitar a gravação de bytecode no aplicativo. Ignorar as opções de
ambiente também garante que as asserções do autoteste continuem habilitadas.

As verificações correspondem a estes comandos locais do aplicativo:

```bash
cd app
python -m unittest discover -s . -p 'test_*.py' -v
python desktop_app.py --self-test --report ../.artifacts/desktop-self-test.json
```

O verificador da raiz também bloqueia eventos de auditoria de conexão de socket
Python, consulta DNS e envio de datagramas nos subprocessos. Um teste futuro
que tente uma conexão Python real falhará, em vez de acessar o JEV
silenciosamente. É uma proteção para as verificações sintéticas existentes,
não uma sandbox do sistema operacional.

Cada verificação tem prazo máximo de 180 segundos. A execução falha se um
subprocesso terminar com erro, se unittest não executar testes ou se o relatório
desktop não contiver `"status": "passed"`. As duas verificações são tentadas,
permitindo consultar suas falhas independentes. Um relatório desktop antigo é
removido antes da execução.

As evidências são gravadas na raiz do repositório, independentemente do
diretório de onde o comando foi chamado:

| Arquivo | Conteúdo |
| --- | --- |
| `.artifacts/tests.log` | Resultados detalhados de unittest |
| `.artifacts/desktop.log` | Saída ou falha do autoteste desktop |
| `.artifacts/desktop-self-test.json` | Relatório do autoteste em caso de execução bem-sucedida |
| `.artifacts/verification.json` | Resultado geral, interpretador exato, plataforma, comandos, durações e quantidade de testes |

São arquivos locais gerados, excluídos do controle de versão. Uma execução
Linux bem-sucedida demonstra a lógica determinística do aplicativo e a
importação do controlador desktop. Não demonstra instalação Windows,
renderização ou usabilidade da interface, inicialização do runtime nativo
Windows, resposta real do JEV, conexão Excel/Profit ou execução de ordens.
A base herdada do aplicativo contém 166 testes; consulte o
`verification.json` atual para saber o resultado de uma nova execução.

## GitHub Actions

`.github/workflows/ci.yml` oferece uma tarefa Linux **somente manual**, em
Ubuntu 24.04 com Python 3.12. Ela prepara o ambiente mínimo, executa o mesmo
verificador e disponibiliza `.artifacts/` por sete dias, incluindo evidências
de falhas. Não há gatilhos de push, pull request ou agendamento. Importar ou
enviar o repositório não inicia automaticamente esse workflow. Uma execução
manual ainda pode consumir a cota de Actions da conta.

Para usá-lo depois que o repositório e a branch padrão estiverem disponíveis,
abra **Actions → Offline Python verification → Run workflow**. O GitHub
documenta os requisitos de execução manual e branch padrão em
[Manually running a workflow](https://docs.github.com/actions/managing-workflow-runs/manually-running-a-workflow).

O workflow usa as tags oficiais de versão principal `actions/checkout@v4`,
`actions/setup-python@v5` e `actions/upload-artifact@v4`. Essas tags são mutáveis;
não são referências imutáveis da cadeia de dependências. Antes de exigir
referências imutáveis, identifique e confira o SHA do commit em cada repositório
oficial e atualize o workflow. Nenhum SHA não verificado foi inserido. A
preparação Python está descrita na
[documentação de workflows Python do GitHub](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).

O workflow é fornecido como configuração; sua presença não comprova uma
execução remota bem-sucedida no GitHub Actions. Empacotamento e integração
Windows não fazem parte dessa tarefa de CI.

## Compilação da distribuição Windows

O aplicativo já contém um fluxo separado de empacotamento, documentado em
[`app/WINDOWS_BUILD.md`](../app/WINDOWS_BUILD.md). Ele exige Python Windows
3.12 x64 com Tcl/Tk e NSIS 3.09 ou posterior. Na raiz do repositório:

```powershell
powershell -File .\app\build_windows.ps1
```

Esse script muda para seu próprio diretório de aplicativo e usa ali
`.build-venv` e `.build-wheels`; não usa o `.venv` de desenvolvimento da raiz.
Sua saída fica em `app/dist/`. Não instale `requirements-build.txt` como
pré-requisito de desenvolvimento offline: esse arquivo descreve a cadeia antiga
de PyInstaller, enquanto a distribuição atual usa lançador/instalador NSIS com
um runtime Windows convencional. Os arquivos experimentais preservados não
são o fluxo padrão de compilação.

Compilar um instalador, inspecionar PE/hashes ou executar o autoteste Linux não
comprova a abertura do programa no Windows. Antes de distribuir um novo pacote,
valide o instalador, a abertura da interface, os atalhos de diagnóstico e
qualquer conexão Excel/RTD pretendida em uma conta Windows de teste separada.
Estes scripts de desenvolvimento não comprovam validação da interface ou do
empacotamento no Windows.

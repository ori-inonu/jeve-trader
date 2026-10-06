# Distribuição Windows do JevWIN

A distribuição atual usa um **instalador NSIS x64 real** e uma pasta convencional com o interpretador oficial do Windows. O programa é iniciado por `pythonw.exe` com as bibliotecas, arquivos Tcl/Tk e módulos da aplicação em suas pastas normais. A inicialização do CPython não usa o arquivo congelado experimental da versão 0.2.

## Arquivos entregues

- `JevWIN_Instalador.exe`: assistente de instalação para o usuário atual, em `%LOCALAPPDATA%\Programs\JevWIN`, com atalhos e desinstalador. Python está incluído.
- `JevWIN_Portatil.zip`: extraia a pasta inteira e abra o `JevWIN.exe` dentro dela. Esse executável pequeno é um lançador; preserve `runtime/`, `app/` e os demais arquivos.
- `JevWIN.cmd`: abre a aplicação com console e mantém a janela aberta se houver falha.
- `Diagnosticar_JevWIN.cmd`: verifica componentes, Tcl/Tk e o autoteste; a janela permanece aberta para copiar a mensagem.

Dados, diário e registros ficam em `%LOCALAPPDATA%\JevWIN` e são preservados pela desinstalação. Os registros de inicialização ficam em `logs/startup.log` e `logs/python-errors.log`; o diagnóstico também produz `diagnostico.json` e `self-test.json`.

O lançador captura erros de inicialização, de callbacks Tk e de threads. Registra a versão do Python, arquitetura, caminhos locais de componentes e erros sanitizados. Não faz uma cópia das variáveis de ambiente, configurações, credenciais ou conteúdo de respostas da API. URLs remotas e campos de credenciais são omitidos dos registros de exceção.

## Compilar no Windows

Pré-requisitos para quem mantém o código: Windows Python 3.12 x64 com Tcl/Tk e NSIS 3.09 ou posterior. Em PowerShell, na pasta do projeto:

```powershell
powershell -File .\build_windows.ps1
```

Se o NSIS não estiver no caminho padrão:

```powershell
.\build_windows.ps1 -MakeNSIS 'C:\Program Files (x86)\NSIS\makensis.exe'
```

O script cria um ambiente local de compilação, obtém os pacotes declarados em `requirements-runtime.txt`, mantém a estrutura normal do runtime e compila `packaging/launcher.nsi` e `packaging/installer.nsi`. O resultado fica em `dist/`.

O script não instala automaticamente o programa no usuário que está compilando. Teste a instalação, a abertura da interface e o diagnóstico em uma conta Windows de teste antes de publicar.

## Compilar em outro sistema com NSIS nativo

O compilador NSIS também gera instaladores Windows em Linux sem executar o instalador. Com uma árvore oficial completa do Windows Python 3.12, os pacotes `comtypes==1.4.17` e `tzdata==2025.2`, execute:

```text
python packaging/build_installer.py --runtime WINDOWS_PYTHON_DIRECTORY --comtypes-wheel comtypes-1.4.17-py3-none-any.whl --tzdata-wheel tzdata-2025.2-py2.py3-none-any.whl --makensis MAKENSIS_PATH --nsisdir NSIS_RESOURCE_DIRECTORY --output-dir dist
```

O parâmetro opcional `--sevenzip SEVENZIP_PATH` extrai o instalador gerado e compara cada arquivo com os hashes originais. O relatório `JevWIN_distribution_report.json` registra a identidade PE, hashes, estrutura do runtime e resultados das verificações.

## Limites de validação

A geração do instalador e as verificações de extração não constituem uma execução no Windows. **A instalação, a interface e uma conexão real com Profit/Excel ainda precisam de teste em Windows.** Este ambiente não permite iniciar Wine, pois bloqueia o socket IPC necessário. A falha observada no EXE anterior não teve sua causa exata confirmada: ainda é necessária a mensagem apresentada pelo Windows.

O EXE anterior também era portátil de um arquivo, não um instalador. `build_offline_windows.py` e `JevWIN.spec` permanecem como referência do método experimental anterior; não são o fluxo principal de distribuição atual. O executável instalador atual é produzido pelo compilador NSIS, com seu formato padrão e runtime convencional.

Os executáveis gerados são não assinados. O pacote não modifica Defender, políticas de execução ou permissões do Windows. Bibliotecas e respectivas licenças estão incluídas na pasta do programa.

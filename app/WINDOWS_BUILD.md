# Distribuição Windows do JevWIN

## Painel moderno 0.4.0

Use [o guia atual](../docs/DECISION_PANEL.md) e `pwsh -File desktop/build-windows.ps1` para o painel Tauri/React com motor Python congelado. O instalador e ZIP desta implementação ficam em `.artifacts/desktop-windows/`; os testes de instalação usam uma identidade isolada. Dados em `%LOCALAPPDATA%/JevWIN` são preservados. O build requer PowerShell 7 e WebView2 deve estar instalado para abrir o painel.

## OCR local do painel atual

O build Tauri prepara `app/ocr_runtime/` por `scripts/prepare_ocr_runtime.py`: Tesseract 5.5.3 compilado de fontes no vcpkg `2750401336fb7c95f6619657a46a7e798661341c`, triplet `x64-windows-static`, helper C# x64 do .NET Framework e modelo `eng` fixado de tessdata_fast. O primeiro build requer Git, Visual Studio Build Tools com C++/CMake, acesso aos fontes públicos e pode demorar; os seguintes reutilizam o cache local. O executável vcpkg confiável tem SHA256 fixado no script; ferramentas diferentes exigem uma atualização deliberada desse contrato. O script não instala Tesseract globalmente nem modifica a política de execução.

O caminho padrão da ferramenta é Visual Studio **18** Build Tools em `Program Files (x86)`. Para uma cópia do mesmo executável confiável em outro local, use `pwsh -File desktop/build-windows.ps1 -VcpkgTool 'C:\caminho\vcpkg.exe'` ou `python scripts/prepare_ocr_runtime.py --vcpkg-tool 'C:\caminho\vcpkg.exe'`. A verificação do hash permanece obrigatória. Overlays externos de ports/triplets são rejeitados e downloads de cache binário são desativados na preparação. Pacotes já instalados localmente podem ser reutilizados; os registros ABI acompanham o inventário, sem alegar recompilação completa a cada execução.

O preparador valida hashes e reconhece texto gerado conhecido. O build falha se o runtime ou seu diagnóstico estiver indisponível. O sidecar inclui o runtime e manifesto; os avisos de todas as dependências, inventário, ABI e fontes também ficam acessíveis em `licenses/local-ocr` na distribuição. Esses binários/modelos gerados não entram no Git.

Em execução, OCR começa OFF e usa processos locais com limite de quatro segundos por etapa, sem PowerShell. Pixels temporários são removidos após reconhecimento, falha ou timeout. A captura exige janela Profit visível, não minimizada e região interna. O snapshot é textual e parcial, sem negócios ou livro estruturados: o diagnóstico gerado não valida o Profit, continuidade, perdas ou latência de dados reais. A interface informa a disponibilidade do runtime. `jeve-engine.exe --diagnose` usa somente arquivos temporários e texto gerado, sem acesso ao Profit ou API JEV.

## Distribuição anterior — Tkinter (histórico)

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

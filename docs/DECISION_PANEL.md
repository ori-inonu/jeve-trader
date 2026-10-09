# Jeve Trader 0.4 — painel de decisão

Entrega experimental de 07/10/2026 para Windows x64. O painel usa Tauri 2, React, TypeScript, Vite, Tailwind CSS 4 e Apache ECharts, conectado ao motor Python. O aplicativo Tkinter permanece disponível para compatibilidade. [Decisão de arquitetura](decisions/0010-painel-e-capital-progressivo.md), [evidência](evidence/decision-panel-2026-10-07.json).

## Abrir o aplicativo

O build desta sessão está em `.artifacts/desktop-windows/JevWIN_0.4.0_setup.exe`; a alternativa portátil é `JevWIN_0.4.0_portable.zip` no mesmo diretório. Execute o instalador ou extraia a pasta inteira do ZIP e abra `JevWIN.exe`. O pacote inclui o Python necessário ao motor. Requer Windows 10/11 x64 e WebView2 Evergreen instalado; o instalador não baixa esse componente. O pacote ainda não possui assinatura de código.

Os identificadores de instalação JevWIN e a pasta `%LOCALAPPDATA%\JevWIN` são preservados. O novo registro fica em `decision-lab.sqlite3`, separado de `journal.sqlite3` da interface anterior. Na primeira abertura, valores/configurações compatíveis do diário anterior inicializam o novo serviço; não há sincronização contínua entre as duas interfaces. Evite editar a mesma conta simultaneamente nas duas. Faça backup dessa pasta antes de uma migração de máquina. A desinstalação preserva os dados.

O teste desta entrega instalou uma variante isolada, observou a janela nativa e o processo Python, encerrou o processo raiz, reinstalou e desinstalou, preservando os dados de teste e a instalação principal. Os formulários foram verificados na prévia do navegador com o mesmo React e serviço Python. Interações dentro da janela nativa e conexão real ao RTD ainda não foram verificadas.

## Usar o painel

1. **Capital:** informe banca atual inteira e margem disponível, conferidas na corretora. O pico registrado permanece após perdas. R$400 → R$800 → R$600 recalcula a base; não reinicia o lote em um contrato. 30% de drawdown é referência de adaptação, sem pausa automática e sem parada por lucro.
2. **Configuração:** confira o contrato vigente, arquivo Excel já aberto, planilhas e intervalos com cabeçalhos. `WINV26` e os nomes iniciais são exemplos, sem seleção automática de vencimento. Informe tarifas por lado, corretagem, slippage, margem, fonte, vigência, conta e versão. Valores iniciais, incluindo R$155 de margem e R$0,50 de tarifa por lado, são hipóteses manuais, não uma tabela operacional conferida.
3. **Decisão:** acompanhe fonte, referência de horário, cobertura, banca e capacidade calculada. Os detalhes mostram planos com entrada, stop, alvo, quantidade e resultado líquido condicional ao preço. Esses resultados não são lucro esperado. A tela principal mostra uma única conclusão.
4. **Pesquisa:** consulte as famílias de dimensionamento e a avaliação temporal. Progressões após perdas só participam de comparações offline. R$300 → R$4.000 é cenário de investigação, sem obrigação de atingir o valor.

O capital é realizado e informado manualmente; não inclui marcação automática da posição a mercado. Registre **entrada efetivamente executada** com contrato, lado, quantidade, preço, custo pago e margem reservada. Depois registre saída total ou parcial com quantidade, preço e custo pago. O sistema desconta cada custo uma vez, atualiza a banca e libera margem proporcionalmente. O registro não envia uma ordem ao Profit. Com posição aberta, novas entradas ficam aguardando conciliação/encerramento; saídas recomendadas para posições abertas exigem uma etapa posterior.

Na primeira entrega, a conclusão é **Aguardar — modelo financeiro aguarda validação temporal**. As hipóteses geométricas e capacidades já são calculadas. Apoio, contradição e insuficiência são medidas contextuais independentes do JEV; sem consulta real, permanecem “sem avaliação”. Probabilidade financeira e distribuição permanecem **não estimadas**. O serviço não carrega nem promove os modelos do laboratório; os contratos de estimativa e seleção tipada estão preparados no motor para uma integração posterior com evidência própria.

O painel considera até oito geometrias e enumera `q=0` e os lotes financeiramente admissíveis até o limite computacional atual de 100 contratos por geometria. Este limite não é uma quantidade recomendada; ampliar a enumeração/transporte deve preceder estudos com capacidades acima dele. Margem, perda planejada e custos restringem a capacidade; perda passada não determina aumento de lote. Stop planejado não garante execução nesse preço.

## Excel e JEV

O serviço usa a ponte combinada do [guia de campos](../app/PROFIT_BRIDGE.md): cotação e negócios do mesmo arquivo já aberto. Negócios requerem ID estável, contrato, timestamp, preço, quantidade e agressor. Não fabrica tape a partir de volume agregado nem presume uma fórmula de Times & Trades que sua instalação não ofereça.

A leitura COM ocorre em processo próprio. Excel ocupado, erro ou timeout invalidam a fonte; o processo de coleta pode ser encerrado/recriado sem encerrar o Excel e sem bloquear o formulário de capital. Leituras são amostragens, `full_tape=False`. Reconexão não prova continuidade. Sem exportação autorizada de negócios compatíveis, a conexão combinada permanece indisponível.

A chave TypeSafe é opcional e permanece na memória do processo. Consultas automáticas começam desligadas; habilitá-las usa o orçamento configurado. O limite inicial é 120 consultas por execução, intervalo mínimo de 10 segundos e timeout de 3 segundos. Horário de resposta não rejuvenesce evidência: resultados de fonte, conta, premissa, receita ou geometria antigas são descartados. Nem setup, diagnóstico, testes nem laboratório fazem chamadas pagas. O diário experimental registra payload/perguntas, hashes, relógios, modelo solicitado e resultado/falha, sem gravar a chave. Custo efetivo da API permanece desconhecido.

O contrato Market Data da ProfitDLL existe em `app/profitdll_contract.py`, sem ABI adivinhada, ordens ou DLL proprietária incluída. Conexão real depende de SDK autorizado, licença e contrato documentado. [Acesso oficial](https://ajuda.nelogica.com.br/hc/pt-br/articles/51583791325211-Como-obter-acesso-%C3%A0-ProfitDLL).

## Desenvolvimento e build

Use um `.venv` preparado conforme [desenvolvimento](DEVELOPMENT.md). Esta entrega foi verificada com Python 3.14.7 no Windows. O desenvolvimento da interface requer Node/npm; o desktop nativo acrescenta Rust e MSVC C++/Windows SDK. O build abaixo requer **PowerShell 7**, NSIS e as dependências em `app/requirements-desktop-build.txt`.

```powershell
.\.venv\Scripts\python.exe .\scripts\verify.py
powershell -File .\scripts\start-desktop.ps1
# Prévia com dados sintéticos separados da conta padrão:
powershell -File .\scripts\start-desktop.ps1 -BrowserPreview -DataDirectory .\.artifacts\ui-test-data
# Gera instalador e ZIP; não instala na conta principal:
pwsh -File .\desktop\build-windows.ps1
# Variante para teste automatizado de instalação isolada:
pwsh -File .\desktop\build-windows.ps1 -SkipInstallDependencies -IsolatedInstaller
pwsh -File .\scripts\verify-desktop-package.ps1
```

`npm.cmd` é usado pelos scripts para não depender de liberação de execução do `npm.ps1`. Não altere Defender, TLS ou política de execução para contornar instalação. `Diagnosticar_JevWIN.cmd` testa o motor empacotado em uma pasta temporária, sem chave. Os avisos/licenças coletados ficam no pacote; o inventário informa ausências e não constitui auditoria para distribuição comercial.

## Laboratório offline

Dependências estatísticas são opcionais e ficam fora do pacote desktop:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\app\requirements-lab.txt
.\.venv\Scripts\python.exe .\scripts\run_decision_lab.py --smoke --initial 300 --target 4000 --output-dir .\.artifacts\lab-smoke
.\.venv\Scripts\python.exe .\scripts\run_decision_lab.py --input-csv C:\dados\WIN.csv --coverage-manifest C:\dados\coverage.json --contexts C:\dados\contexts.json --costs C:\dados\costs.json --output-dir .\.artifacts\lab-real
```

Use apenas dados cuja coleta e uso foram autorizados. `--smoke` produz 300 linhas sintéticas em dez sessões para verificar execução do pipeline. O CSV segue o schema da ponte; cobertura do laboratório exige manifesto ligado ao contrato, hash dos eventos e intervalo auditado, descrito no [estudo, §13](research/Pesquisa_Decisao_JEV_WIN_2026-10-06.md#13-implementação-experimental-em-07102026). Sem prova compatível, desfechos são censurados. Um manifesto declarado manualmente não prova por si só a qualidade do feed.

Treino, calibração e teste ficam separados por sessões cronológicas. O relatório compara logística multiclasse com/sem atributos JEV disponíveis na entrada, confiabilidade, crescimento, drawdown, VaR/ES e trajetórias das políticas. O replay usa preço de negócio como aproximação de execução, sem validação de fila ou fills. Todo relatório mantém `deployment_approved=false`; não salva nem instala um modelo no aplicativo. Validação prospectiva, custos reais, latência, ganho incremental líquido do custo JEV e execução plausível continuam necessários.

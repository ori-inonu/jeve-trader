# JEV WIN v0.3.0 — Central de decisão, fluxo e capital

Preparado para Gabriel em 06/10/2026, para Windows x64 com Profit Pro, conta Toro e acesso à API TypeSafe/JEV. **O aplicativo desktop está implementado e os pacotes Windows incluem o runtime necessário.** A tela inicial é a **Central de decisão**, que reúne conclusão, evidências, impedimentos, comparação dos cenários e histórico de estados. O aplicativo oferece demonstrações locais, replay CSV, leitura combinada de cotações/negócios do Excel RTD, cálculos de fluxo e estudo de capital.

A conexão Excel precisa ser configurada e validada na instalação do usuário. **Conta Toro, saldo, posição, ordens e execução não estão conectados.** A licença ProfitDLL/DLL Feed não está disponível no ambiente confirmado, e nenhuma DLL ou assinatura de callback foi inventada para substituí-la. O caminho implementado usa a exportação RTD/DDE do próprio Profit, dentro das permissões disponíveis ao usuário.

Nenhuma análise desta entrega demonstrou lucro futuro, vantagem estatística ou lote de retorno máximo. O monitor diferencia demonstração, replay e observação Excel; cenários de pesquisa permanecem não acionáveis em conta real.

## Abrir no Windows

| Pacote/caminho | Como usar | Python separado |
|---|---|---|
| `JevWIN_Instalador.exe` | Instale para seu usuário e abra pelo atalho JEV WIN | Não exige; runtime incluído |
| `JevWIN.exe` | Lançador nativo na instalação/pasta extraída; preserve toda a pasta | Não exige |
| `JevWIN_Portatil.zip` | Extraia tudo e abra `JevWIN.cmd`, mantendo todas as pastas | Não exige; runtime incluído |
| Fontes do projeto | Execute `python desktop_app.py` | Exige Python com Tcl/Tk; `comtypes` para leitura COM |

Use Windows 10/11 x64. **Esta versão inclui um instalador real por usuário**, distinto do pacote portátil anterior. O instalador coloca o aplicativo em `%LOCALAPPDATA%\Programs\JevWIN` e cria atalhos **JevWIN**, **Diagnosticar JevWIN** e **Desinstalar JevWIN**; não instala Profit/Excel nem configura RTD ou sua conta. O instalador e os executáveis não possuem assinatura digital comercial. O pacote portátil deve ser extraído completamente; não execute o lançador de dentro do ZIP. Profit e Microsoft Excel são instalações externas do usuário, necessárias apenas para observação RTD. A demonstração e os estudos locais funcionam sem conexão ao Profit ou chave JEV. No portátil, `Diagnosticar_JevWIN.cmd` executa o diagnóstico local e conserva mensagens de erro; não conecta a corretora nem comprova RTD funcionando. `JevWIN.exe` é um lançador que depende dos arquivos da pasta, não um executável avulso. Logs e relatórios ficam em `%LOCALAPPDATA%\JevWIN`, incluindo `startup.log`, `python-errors.log` e `diagnostico.json`/`self-test.json`. A desinstalação preserva esses dados.

Os relatórios de build e `VALIDATION.md` distinguem inspeção do arquivo PE Windows, verificações do conteúdo empacotado e testes da lógica de uma execução real no Windows. A janela nativa, seu Excel/Profit e sua API não foram validados neste ambiente. **Não interprete teste extraído no Linux como abertura comprovada do aplicativo Windows.**

Comece pelo [GUIA_WINDOWS.md](GUIA_WINDOWS.md), que contém o passo a passo, limites e solução de falhas.

## As oito abas

| Aba | O que faz |
|---|---|
| **Central de decisão** | Conclusão e próxima ação, evidências/impedimentos, cenários calculados e histórico de estados |
| **Monitor** | Gráfico de preços capturados, medidas de cinco segundos, estado das hipóteses, idade e cobertura da origem |
| **Cenários técnicos** | Até oito combinações estruturais de entrada/stop/alvo com referências rastreáveis e dimensionamento financeiro |
| **Capital e risco** | Capital manual, orçamento, lote calculado, projeção de stops e comparação de políticas |
| **Conexões** | Anexação ao Excel já aberto, modos `quote`/`tape`/`combined`, replay CSV e modelos de exportação |
| **JEV** | Chave em memória, interpretação estruturada do contexto e consultas opcionais com orçamento |
| **Diário** | Registro manual de resultado líquido, histórico de estudos/análises e exportação JSON |
| **Guia** | Orientações incorporadas à interface |

### Central de decisão: motivo e impedimento visíveis

A Central é a primeira aba. Dentro dela, **Evidências e impedimentos**, **Cenários calculados** e **Histórico de estados** organizam a mesma avaliação. Os botões são **Atualizar avaliação**, **Consultar JEV**, **Demonstrar cenários** e **Exportar painel HTML**.

A conclusão distingue **SEM DADOS SUFICIENTES**, **AGUARDAR CONFIRMAÇÃO**, **BLOQUEADO PELO RISCO** e **HIPÓTESE PARA REVISÃO**. A cobertura parcial das fontes Excel/CSV permanece como impedimento: uma classificação favorável do JEV ou lote financeiramente viável não a remove. Limites monetários têm precedência sobre apoio do modelo. Apoio/contradição são medidas contextuais, sem conversão para probabilidade de lucro ou ranking de retorno esperado.

**Exportar painel HTML** grava um registro visual do instante, para abrir no navegador. Não é um painel conectado, não continua recebendo preços e não executa consultas JEV. O histórico permite examinar por que a conclusão mudou; não é um extrato de ordens.

### Fluxo observado

`flow_engine.py` normaliza negócios com ID, contrato, preço em pontos, quantidade inteira, timestamp e agressor. Calcula volume, delta capturado, intensidade, progressão e cobertura em janelas limitadas. Trabalha com agressão reportada pela fonte; não a deduz do último preço. Repetições, eventos regressivos e registros inválidos têm tratamento explícito, com buffers limitados.

Progressão é agressão acompanhada por avanço observado do preço. Absorção potencial é agressão sem avanço proporcional. Exaustão potencial é perda de intensidade após avanço e ausência de continuação. Essas condições descrevem a amostra; não provam intenção, liquidez oculta ou reversão futura. Redução de quantidade visível não prova cancelamento: execução ou atualização também podem explicar a diferença.

### Cenários técnicos

`candidate_research.py` extrai referências de preços efetivamente negociados na janela observada: extremos e níveis com toques repetidos. Cada referência preserva IDs, horários e volume capturado. Combina stops e alvos usando a geometria existente; faltas de referência, faixa estreita, dados antigos ou geometria inválida podem produzir uma comparação vazia.

Não inventa alvos futuros ou estreita stop artificialmente para caber no patrimônio. As linhas são **combinações de pesquisa sem ranking de valor esperado**, probabilidade de acerto calibrada ou recomendação de operação. A viabilidade financeira não comprova apoio do mercado. Uma demonstração técnica separada usa níveis sintéticos explicitamente identificados.

### Capital manual e registro de resultado

O motor monetário usa `Decimal`, patrimônio inicial/atual/pico, custos, slippage, margem e pisos escolhidos. Recalcula lote após resultado líquido registrado, em vez de congelar a quantidade do exemplo inicial. Projeta stops consecutivos com lote recalculado e distingue limite da política de capacidade financeira diagnóstica.

O perfil agressivo é um parâmetro de laboratório; não é uma configuração validada para sua conta. O usuário pode comparar frações/base patrimonial sem pressupor que maior exposição proporciona maior lucro esperado. Após perda registrada no diário, o estudo aplica pausa de 60 segundos. Digitar uma sequência no formulário permanece um cenário separado. O aplicativo não impede operações no Profit nem gere posição aberta.

O diário e as configurações são gravados em `%LOCALAPPDATA%\JevWIN`, com histórico limitado e exportação JSON. Não representam extrato da corretora. A chave de API não é persistida.

## Preparar Profit → Excel → aplicativo

1. Em **Conexões**, use **Salvar modelos de exportação**.
2. No Profit, configure **Arquivo → Exportar em Tempo Real (RTD/DDE)** e habilite a transferência para Excel.
3. Abra `Profit_RTD_Modelo.xlsx`. Digite o contrato exato em `Dados!A2`; o modelo usa sufixo `_F_0` sem escolher vencimento automaticamente.
4. Confira a atualização no Excel. No aplicativo, informe o mesmo contrato, arquivo aberto, planilha `Dados`, intervalo `A1:I2` e modo `quote`.
5. Use **Conectar leitura Excel**. **Parar leitura** encerra o acompanhamento e invalida a avaliação atual.

O backend preferencial é COM nativo com `comtypes==1.4.17`, incluído no pacote. Anexa apenas Excel já aberto, usa dispatch dinâmico e lê `Value2`. Não inicia Excel, abre arquivos, grava células, recalcula ou altera políticas. O helper PowerShell existe como alternativa **somente quando comtypes está ausente**, sem fallback por permissão nem `ExecutionPolicy Bypass`.

A leitura ocorre em background. COM nativo não possui timeout rígido interrompível; Excel ocupado pode atrasar a operação. Acesso bem-sucedido à planilha não comprova feed da bolsa ativo. RTD pode pausar conforme aba/janela vinculada no Profit. Data/hora ausentes deixam a idade real desconhecida.

O template fornecido contém fórmulas de cotações e uma aba **Negocios inicialmente vazia**, sem coletor automático do Times & Trades. `ULT`, `QUL` ou `VOL` não permitem reconstruir todos os negócios ou agressão. Snapshot de ofertas não comprova sequência/profundidade do livro.

### Cotações e negócios combinados

Para conservar ofertas e trades na mesma sessão, selecione `combined` em **Modo: quote / tape / combined**. Use o mesmo arquivo `Profit_RTD_Modelo.xlsx` e configure:

| Campo | Valor de referência |
|---|---|
| **Planilha principal / cotações** | `Dados` |
| **Intervalo principal com cabeçalho** | `A1:I2` |
| **Planilha de negócios (combined)** | `Negocios` |
| **Intervalo de negócios (combined)** | `A1:F501` |

A aba Negocios precisa receber exportação **real, compatível e autorizada**, com ID estável, contrato, timestamp completo, preço, quantidade e agressor reportado. A disponibilidade/layout dessa exportação deve ser conferida no Profit do usuário: o aplicativo não descobre a janela Times & Trades nem fabrica suas fórmulas. Colagem estática vira dado antigo quando deixa de atualizar. Ordene do mais antigo ao mais recente; preserve IDs como texto.

Uma única anexação COM lê os dois intervalos sequencialmente. Falha, tabela vazia ou registro inválido em qualquer fonte invalida o ciclo inteiro, sem misturar dados novos com uma metade antiga. Os timestamps continuam separados e a leitura não é atômica na bolsa. O modo combinado permite calcular referências e geometria quando ambas as fontes forem utilizáveis; **não transforma a amostra em tape integral nem retira o estado AGUARDAR da Central**. O consumidor confere frescor, evidência e limites de risco.

### CSV e tape

`negocios_modelo.csv` contém 141 eventos sintéticos `WIN_SIM`, identificados por `SYNTHETIC-*`. Para carregá-lo, informe `WIN_SIM` e use **Carregar negócios CSV**. O relógio é o do replay.

Para dados próprios, use cabeçalho:

```text
id;symbol;ts_ms;price_points;quantity;aggressor
```

Também são aceitos timestamp ISO com data/hora e offset ou colunas data/hora. Quantidades precisam ser inteiras; agressor desconhecido permanece desconhecido. Negócios sem ID não alimentam o acumulador da interface. Excel `tape` exige negócios individuais realmente exportados. **Todas essas fontes mantêm cobertura parcial (`full_tape=False`)**. Detalhes de formatos, limites e integridade estão em [PROFIT_BRIDGE.md](PROFIT_BRIDGE.md).

## Integração JEV

O cliente usa o endpoint oficial TypeSafe, versão fixada `jev-1.13.0`, perguntas `Choice`/`Noul` independentes e validação rigorosa da resposta. O JEV recebe medidas, referências e limites de cobertura; patrimônio e pressão por recuperação ficam separados. Apoio contextual e `confidence` não equivalem à probabilidade de lucro.

A chave é informada na aba JEV ou pela variável `TYPESAFE_API_KEY` e permanece em memória. Consultas automáticas começam desligadas, exigem leitura Excel ativa/evidência suficiente e têm intervalo mínimo de 10 segundos. O orçamento padrão é 120 chamadas por abertura, configurável entre 1 e 10.000. A chamada pode consumir créditos da conta TypeSafe.

Troca de fonte, atraso, resposta inválida, evidência antiga ou contexto alterado impedem tratar uma avaliação passada como atual. Nenhuma consulta fornece instrução de execução ou envia ordem. Notícias, calendário de eventos e consulta à conta não foram integrados.

## Fontes, testes e ferramentas anteriores

Para executar os fontes com Python 3.10 ou superior e Tcl/Tk:

```powershell
python -m pip install comtypes==1.4.17 tzdata
python desktop_app.py
python -m unittest discover -v
python desktop_app.py --self-test --report self-test.json
```

Os testes avaliam integridade do software, parsing, cálculo, falhas e contratos; não constituem backtest financeiro ou validação de rentabilidade. A contagem e os procedimentos finais constam em `VALIDATION.md` e nos relatórios do pacote.

`dashboard.py`, `copilot.py`, replay JSON, `stress_lab.py` e projeções antigas continuam disponíveis para pesquisa/auditoria. O aplicativo principal é `desktop_app.py`. Para reproduzir um build nativo via PyInstaller, consulte `build_windows.ps1`, `JevWIN.spec` e `requirements-build.txt`; isso é opcional para quem usa os pacotes prontos.

## Documentação e próximos limites

- [GUIA_WINDOWS.md](GUIA_WINDOWS.md): uso cotidiano e primeira configuração.
- [PROFIT_BRIDGE.md](PROFIT_BRIDGE.md): coletor implementado, formatos e limites.
- [PROFIT_INTEGRATION.md](PROFIT_INTEGRATION.md): estado da integração e requisitos futuros.
- `DECISION_DESIGN.md`, `RISK_MANAGEMENT.md`, `VALIDATION.md`: desenho, estudos monetários e evidências de validação.

Um feed integral licenciado, conta conciliada, tratamento de correções/cancelamentos e avaliação temporal com custos continuam requisitos separados para pesquisar uso operacional. Nenhum lucro isolado ou aprovação de testes promove automaticamente a conta real.

## Fontes oficiais relevantes

- [TypeSafe: skill oficial](https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md), [API](https://docs.typesafe.ai/api), [modelos](https://docs.typesafe.ai/models), [confiança](https://docs.typesafe.ai/confidence) e [limitações JEV](https://docs.typesafe.ai/model-jaggedness/jev-1.13).
- [Nelogica: RTD/DDE](https://ajuda.nelogica.com.br/hc/pt-br/articles/360044293432-Como-configurar-RTD-DDE-no-Profit), [sintaxe RTD](https://ajuda.nelogica.com.br/hc/pt-br/articles/7834206674075-Significados-e-sintaxe-do-RTD), [ProfitDLL](https://ajuda.nelogica.com.br/hc/pt-br/articles/22396517026203-Ecossistema-ProfitDLL-e-primeiros-passos), [replay](https://ajuda.nelogica.com.br/hc/pt-br/articles/360043469772-Replay-de-Mercado) e [pulo de ordens](https://ajuda.nelogica.com.br/hc/pt-br/articles/360053623191-Compreendendo-o-Pulo-de-Ordens).
- [comtypes: documentação](https://comtypes.readthedocs.io/en/stable/client.html) e [pacote oficial](https://pypi.org/project/comtypes/).
- [B3: especificação WIN](https://www.b3.com.br/en_us/products-and-services/trading/equities/mini-ibovespa-futures.htm), [margem mínima](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-participantes-e-traders/regras-e-parametros-de-negociacao/margem-minima-requerida-e-guia-educacional-para-minicontratos/) e [Toro: custos](https://www.toroinvestimentos.com.br/info/custos?hsLang=pt-br).

Custos, margem e condições efetivas devem ser conferidos pelo usuário. Os exemplos armazenados não garantem que esses parâmetros continuam aplicáveis à sua conta.

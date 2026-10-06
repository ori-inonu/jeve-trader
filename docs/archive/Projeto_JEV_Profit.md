# Projeto JEV WIN v0.3.0 — implementação e limites

Este documento reúne a visão do aplicativo, o desenho das decisões, a gestão de risco e a verificação. Para instalar e configurar, consulte Guia_JevWIN.md.


---

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


---

# Projeto do motor de decisão de tape reading

Este é um desenho de pesquisa para WIN/B3. Os sinais microestruturais abaixo são hipóteses a testar no feed disponível e não regras comprovadas de lucro. As capacidades do JEV e da ProfitDLL estão documentadas nas fontes do README; a seleção de features e políticas a seguir é proposta de engenharia.

## Implementação v0.3.0

O aplicativo `desktop_app.py` implementa leitura de Excel existente por COM, importação de negócios CSV, acumulador de eventos, medidas em janelas de 5 e 30 segundos, classificação local de hipóteses, extração de níveis observados, comparação de até oito geometrias, consultas estruturadas ao JEV e diário SQLite. A Central de decisão reúne conclusão, evidências, impedimentos, alternativas e histórico. Há instalador por usuário e pacote portátil Windows x64 com runtime incluído e diagnóstico. A integração no computador do usuário e a abertura nativa da janela ainda precisam de validação.

O modo `combined` lê a tabela de cotações e a tabela de negócios do mesmo arquivo Excel aberto, em um ciclo. Qualquer falha em uma tabela invalida o ciclo inteiro; a deduplicação só é confirmada depois de validar ambas. Essa combinação corrige a limitação anterior de escolher apenas uma fonte, mas as leituras continuam sequenciais e a captura parcial. A aba de negócios do modelo começa vazia e depende de uma exportação real compatível; não há coleta automática de Times & Trades.

O Excel é consultado em intervalos de aproximadamente dois segundos, sem sobreposição de leituras. A consulta automática ao JEV tem intervalo mínimo de dez segundos e orçamento de chamadas configurável. Esses intervalos definem um observador amostrado; não equivalem a captura integral de cada negócio ou latência garantida para scalping.

O arquivo de cotações RTD não fornece agressor ou histórico integral de trades. A aplicação mantém esse limite explícito, bloqueia análise de fluxo quando não há negócios suficientes e não converte valores amostrados em eventos autoritativos de livro. Dados sintéticos completos existem apenas para verificar os cálculos.

## 1. O evento recente e o contexto

Toda observação de mercado já ocorreu quando chega ao sistema. A escolha útil é quanto atraso tolerar e qual informação ainda ajuda a decidir. O projeto prioriza eventos recentes de negociação e ofertas, com contexto curto, sem usar cruzamentos de médias ou osciladores como condição central.

Uma agressão compradora elevada, isoladamente, não distingue continuidade de absorção. O sistema precisa comparar fluxo executado, resposta do preço e comportamento da liquidez. Retirada de oferta não prova manipulação; uma oferta grande não garante que permanecerá; uma corretora visível não identifica necessariamente um único investidor.

Há pesquisa sobre relação de eventos do livro e variações de preço de curto prazo: [Cont, Kukanov e Stoikov — The Price Impact of Order Book Events](https://arxiv.org/abs/1011.6402) e [Gould e Bonart — Queue Imbalance as a One-Tick-Ahead Price Predictor](https://arxiv.org/abs/1512.03492). São estudos em ações americanas; apoiam investigar essas variáveis, não comprovam vantagem no WIN nem desempenho do JEV. A adaptação proposta precisa de teste próprio no mercado e horizonte escolhidos.

## 2. Mapa de dados e decisões

| Bloco | Dados/medidas calculadas em código | Pergunta contextual e limitação |
|---|---|---|
| Negócios executados | Preço, quantidade, agressor quando informado, frequência, tamanho relativo, sequência de execuções | Há iniciativa persistente ou apenas evento isolado? Agressão desconhecida não pode ser inventada. |
| Volume e intensidade | Contratos por segundo, desequilíbrio comprador/vendedor, aceleração, concentração por preço | O fluxo recente está crescendo, desacelerando ou alternando? Limiar fixo deve ser testado por horário/regime. |
| Resposta do preço | Deslocamento, permanência fora de nível, retorno após rompimento, avanço por unidade de volume | O mercado aceita o preço ou o movimento falhou? Classificar observação não garante continuação futura. |
| Livro de ofertas | Spread, profundidade, desequilíbrio por faixa, reposição, consumo e cancelamentos quando acessíveis | A liquidez absorve ou cede? Snapshot raso não reconstitui a fila ou ordens ocultas. |
| Absorção | Volume executado repetido contra região sem avanço proporcional, com reposição observável | Há evidência compatível com absorção? Não declarar iceberg ou intenção do participante como fato. |
| Exaustão | Desaceleração de agressões e perda de progressão, comparadas à janela anterior | Falta iniciativa nova ou existe apenas pausa? Exige comparação temporal. |
| Rompimento/falha | Negócios além de nível, manutenção/retorno, consumo de ofertas e resposta oposta | O rompimento está sustentado pelas observações? Definir duração e invalidação antes do teste. |
| Contexto da sessão | Abertura, ajuste anterior, máximas/mínimas observadas, volume por preço e áreas de negociação | Onde a hipótese deixa de fazer sentido? Referências contextualizam; não são barreiras garantidas. |
| Eventos externos | Calendário oficial, anúncio conhecido, status de leilão e interrupções | A volatilidade esperada permite o setup? Notícia não conhecida não pode ser antecipada. |
| Instrumentos relacionados | IND, WDO e outros dados licenciados e sincronizados, se usados | Há confirmação ou divergência útil? Adicionar somente se provar ganho incremental. |
| Conta e execução | Saldo líquido, margem, risco já comprometido, posição e ordens confirmadas | A proposta cabe na exposição? Essa decisão é determinística, não delegada ao JEV. |
| Qualidade do sistema | Perdas de sequência, atraso de cada canal, relógio, latência e reconciliação | Ainda há informação suficiente para um sinal utilizável? Dado ausente não significa ausência de risco. |

"Volume financeiro" no futuro é notional negociado, calculável por preço × multiplicador × quantidade. Não equivale ao dinheiro novo depositado por um participante nem revela sua riqueza. O modelo deve receber o nome correto da métrica. Evite tratar agressão como prova de posição direcional líquida de um agente.

## 3. Features e memória

A implementação usa janela curta de 5 s, comparação com os 5 s anteriores e contexto de 30 s, com retenção de até 60 s. Os valores em `flow_rules.json` são hipóteses de engenharia sem calibração no WIN. A quantidade de ticks pode variar muito entre regimes; não assumir que igual número de mensagens corresponde a igual duração ou informação.

Calcule numericamente volume, deltas, spread, volatilidade local, posição relativa a níveis, intensidade e diferenças entre janelas. Envie ao JEV os números e relações já computadas, acompanhados de definições e indicadores de cobertura. Não peça ao modelo para calcular somas, distâncias ou vencimentos.

Mantenha quatro tipos de memória separadamente: eventos observados; estado atual reconstruído; hipóteses e sinais emitidos; resultados observados posteriormente. Não insira resultados futuros no estado usado para uma decisão histórica. A memória pertence ao aplicativo, e não a uma suposta conversa persistente no endpoint JEV.

## 4. Comparar entradas, stops, alvos e espera

O estado atual permite gerar candidatos finitos. Cada candidato carrega: lado, condição de entrada, preço ou faixa admitida, referência de invalidação, stop técnico, referência de alvo, limite de duração, evidências necessárias, evidências contrárias e metadados temporais.

O aplicativo extrai preços executados repetidos e extremos da janela anterior dos eventos retidos. A entrada usa a melhor oferta disponível, identificando quando ela é apenas uma amostra RTD. `candidate_research.py` combina até oito pares de stop e alvo a partir dos níveis observados; não inventa um nível distante para fazer o resultado caber no capital. Esses níveis não são suportes/resistências validados. A confirmação de rompimento/pullback permanece futura. A matriz finita não abrange todas as situações possíveis do mercado.

O motor deve primeiro eliminar: stop/alvo incorretos, preço fora do tick, referência sem evidência, dados insuficientes, custo inviável, margem insuficiente, risco excedido e sessão imprópria. O JEV pode avaliar apoio e contradição contextual das propostas que cabem no estudo financeiro. Nesta versão desktop, a saída é descritiva e sem ordem ou sinal de compra/venda acionável. Se faltam dados, a análise fica indisponível; não há seleção de operação por valor esperado.

Uma relação ganho/risco alta pode decorrer de um alvo distante e improvável. A probabilidade do evento “alvo antes do stop dentro de um horizonte definido” depende de dados de resultados. Só depois dessa calibração pode haver cálculo de valor esperado, comparação econômica de candidatos e dimensionamento dependente de vantagem estimada.

## 5. Fórmulas do motor monetário

Para quantidade `q`, valor por ponto `v`, distância até o stop `d_stop`, distância até o alvo `d_target`, taxas por contrato `c` e slippage total em pontos `s`:

```text
risco_por_contrato = d_stop × v + c + s × v
ganho_liquido_se_alvo = d_target × v − c − s × v
relacao_liquida = ganho_liquido_se_alvo / risco_por_contrato
lote_por_risco = floor(orcamento_restante / risco_por_contrato)
margem_por_contrato = max(margem_B3, margem_corretora)
lote_por_margem = floor(margem_utilizavel / margem_por_contrato)
lote = min(lote_por_risco, lote_por_margem, limite_do_perfil, quantidade_candidata)
```

No perfil com reserva conjunta, `margem_utilizavel = min(margem_disponivel, patrimonio) − reserva_caixa` e o denominador do lote por margem passa a `margem_por_contrato + risco_por_contrato`. A reserva de perda é uma decisão da política; não altera a exigência da B3 nem garante cobertura de gaps.

Com base dinâmica e pisos ativados, o motor também calcula:

```text
piso_diario = capital_inicio × (1 − fracao_perda_diaria)
piso_do_pico = pico_patrimonial × (1 − fracao_drawdown)
capacidade = min(patrimonio − piso_diario, patrimonio − piso_do_pico) − risco_reservado
orcamento_da_proposta = min(fracao_por_operacao × patrimonio, capacidade)
```

Capacidade não positiva bloqueia a proposta. O pico precisa vir da conta/histórico conciliado, ser finito e não inferior ao capital inicial nem ao atual. Na configuração de controle, a base proporcional continua limitada ao menor valor entre patrimônio atual e inicial. O painel só fornece contas fictícias para explorar essas fórmulas.

O slippage simétrico usado nos testes é uma aproximação. Um modelo de execução mais realista deve ter distribuições distintas para entrada, alvo, stop, liquidez e zeragem compulsória. O risco de estresse deve ser analisado separadamente do risco planejado.

Com probabilidade validada `p`, ganho líquido médio condicional `G` e perda líquida média condicional `L`, a expressão simplificada `p × G − (1−p) × L` permite estimar valor esperado. Essa fórmula pressupõe que esses termos capturem os resultados e custos relevantes. No sistema entregue, `p` não existe: a confiança do JEV não a substitui.

## 6. Alavancagem agressiva e crescimento

Alavancagem modifica o tamanho dos resultados e a vulnerabilidade da conta; não produz uma vantagem estatística por si só. Para capital pequeno, granularidade de um contrato, margem, spread e custos tornam algumas combinações inviáveis mesmo quando o sinal parece bom.

O motor amplia a quantidade calculada após lucro informado e a reduz quando o orçamento cai, no perfil de capital atual. No desktop, o capital é manual e a conta sem posição é uma hipótese do estudo, sem conciliação com a Toro. O núcleo de risco rejeita estados de conta ausentes, vencidos, não conciliados ou com exposição pendente quando esses campos são fornecidos. Isso permite estudar crescimento entre operações encerradas. Realização parcial, manutenção de posição, stop móvel e adição a posição aberta exigem estados de execução e risco agregado que ainda não existem neste protótipo.

O planejador projeta perdas consecutivas e recalcula a quantidade a cada passo; não estima probabilidade nem futuras oportunidades. Mantém trajetória que respeita a política e diagnóstico que ignora exclusivamente a trava por sequência. A comparação de políticas está em `RISK_MANAGEMENT.md`. Uma camada econômica futura precisará comparar quantidades menores que o teto admissível, considerando distribuição líquida de resultados, liquidez, impacto e incerteza. O máximo admissível é apenas um limite de exposição.

Pirâmide em posição vencedora deve recalcular a perda total caso todos os stops sejam atingidos, o lucro já garantido somente quando houver proteção válida e o risco de gap. Lucro não realizado não deve ser tratado como dinheiro livre sem considerar a posição existente. O protótipo não faz pirâmide, preço médio ou gerenciamento de posição aberta.

Sem meta fixa de lucro, ainda são necessárias regras de saída por invalidação, custo de permanência, horário e risco. Uma tese invalidada deve poder encerrar a avaliação mesmo que o objetivo financeiro do dia não tenha sido alcançado.

## 7. Avaliação do valor do JEV

Crie três versões comparáveis: regras determinísticas, modelo quantitativo apropriado aos dados e a mesma base acrescida dos julgamentos JEV. Mantenha custo, feed, período, execução e conjunto de oportunidades comparáveis. Alterar várias partes simultaneamente impede atribuir um resultado ao JEV.

Avalie separadamente precisão de classificação do contexto, calibração do evento financeiro e desempenho da estratégia completa. Inclua dias negativos, trades rejeitados e intervalos sem operação. A taxa de acerto sozinha não determina lucro; ganhos pequenos e perdas grandes podem produzir prejuízo com maioria de acertos.

Use divisões temporais, controle de vazamento entre janelas sobrepostas e testes fora da amostra. Registre cada tentativa de ajuste para reduzir seleção retrospectiva. Varie custos e slippage; teste latência e indisponibilidade. Métricas de cauda e drawdown devem acompanhar retorno.

“Melhor que qualquer especialista” não é um benchmark definido. Uma hipótese verificável é: superar uma baseline especificada em retorno líquido ajustado ao risco, em períodos não usados para ajuste, com incerteza quantificada. Sem essa definição, o projeto mede ambição em vez de capacidade.

## 8. O que falta implementar

Continuam pendentes: feed integral com sequência verificável, adaptador ProfitDLL licenciado, calendário/notícias, integração e conciliação da conta real, simulador de fila/execução, gestão de posição aberta e avaliação estatística fora da amostra. O coletor Excel, cálculo de medidas, níveis observados, diário e empacotamento Windows foram implementados, mas a coleta na instalação do usuário ainda não foi validada. A chave JEV deve ser informada localmente; nenhuma chamada autenticada foi realizada nesta entrega.

O código entregue deliberadamente sinaliza `research_only`, origem sintética/replay e ausência de probabilidade de lucro. Modificar um JSON para `live` não transforma o laboratório em um serviço de pregão.

## 9. Validade e rastreabilidade na interface

Cada fonte recebe uma geração: respostas de trabalhos anteriores são descartadas quando ela muda. No Excel, a idade do negócio original continua contando durante a inferência; receber uma resposta não renova o evento. Cenários técnicos expiram após dois segundos desde a referência de cotação e são descartados ao editar capital, custos ou demais parâmetros. O diário preserva os registros anteriores como histórico.

Uma perda informada atualiza patrimônio, pico e sequência; perdas que esgotam ou ultrapassam o capital são registradas integralmente e deixam novos cálculos bloqueados. Uma sequência digitada sem horário é uma hipótese explícita de estudo com pausa já transcorrida; uma perda registrada no diário usa seu horário real para a pausa. Nenhuma dessas regras bloqueia operações feitas diretamente no Profit.

## 10. Como a Central chega à conclusão

`build_decision_bundle` produz uma visão comum para a janela e o relatório HTML. `recommendation_engine.py` verifica a fonte e sua idade, a validade dos dados financeiros, a geometria observada e o risco recalculado de cada alternativa. O veto financeiro prevalece sobre qualquer apoio do JEV. Respostas do modelo precisam corresponder à geração, modo, símbolo e geometria; uma análise de fluxo isolada não vira confirmação de entrada.

Os estados são `SEM_DADOS`, `AGUARDAR`, `BLOQUEADO_RISCO` e `HIPOTESE_PARA_REVISAO`. Cobertura parcial mantém a confirmação pendente, mesmo quando existem medidas, geometrias e interpretação do modelo. A hipótese para revisão exige evidência compatível e continua sem ordem ou sinal operacional validado. O motor não contém probabilidade de lucro, seleção por valor esperado ou configuração ótima. Apoio maior que contradição é apenas uma comparação contextual do modelo.

Cada mudança relevante de conclusão é registrada com a origem e geração dos dados, inclusive transições rápidas. A interface preserva as últimas 50 mudanças da execução e o diário mantém os registros persistidos. O botão de exportação gera HTML estático com a mesma conclusão, gráfico amostrado, impedimentos e alternativas. O HTML não recebe dados novos e não é uma captura da janela Windows.


---

# Gerenciamento de risco para crescimento agressivo

Este documento descreve a política implementada em `config.json`, `risk.py` e `capital_planner.py`. O sistema trabalha com contas de estudo informadas manualmente; os dados de mercado podem vir de demonstração, replay ou observação parcial do Excel. Não há leitura de saldo/posição da Toro. Os lotes abaixo são resultados de exemplos contábeis reproduzíveis, sem recomendação de operação, previsão de lucro ou validação de desempenho.

## Objetivo e restrições

O objetivo de pesquisa é crescer o capital com leitura de fluxo, permitindo recalcular a exposição quando o patrimônio variar. Não há meta nem teto obrigatório de lucro diário. Ainda assim, o problema exige orçamento de perda: sem ele, “maximizar lucro” não determina uma política finita de exposição.

**Máximo lote admissível e lote economicamente ótimo são decisões diferentes.** O primeiro cabe nas restrições de margem e perda planejada. O segundo depende da distribuição dos resultados, custos, liquidez, probabilidade de execução e perdas extremas. O motor calcula o primeiro; ainda não estima o segundo.

Cada hipótese precisa de entrada, invalidação e alvo sustentados pelas observações. O JEV pode apoiar ou contrariar hipóteses, mas sua confiança de classificação não equivale à probabilidade de lucro. Todas as alternativas podem terminar em abstenção. Uma relação ganho/risco atraente, isoladamente, não demonstra vantagem.

## Matriz de políticas

| Política | Situação atual | Papel e condição de uso |
|---|---|---|
| Risco fixo em reais | Não implementado como limite independente | Permite comparar propostas com orçamento monetário constante; não acompanha automaticamente o capital. |
| Fração do patrimônio | Implementada | O perfil agressivo usa patrimônio corrente; o perfil de controle limita a base ao menor entre patrimônio inicial e atual. |
| Stop e volatilidade | Parcial | A distância do stop determina risco monetário. Níveis repetidos e extremos observados são extraídos em `candidate_research.py`; a relevância preditiva e a adaptação à volatilidade permanecem sem validação. |
| Perda diária e drawdown | Implementados | Pisos de patrimônio limitam novas propostas; o pico informado restringe devolução de ganhos. |
| Sequência de perdas | Bloqueio e pausa implementados | A quantidade cai quando o capital diminui. Redução progressiva específica por sequência ainda não existe. |
| Kelly fracionado | Não implementado | Exige distribuição de resultados estimada e calibrada fora da amostra. Scores brutos do JEV não atendem a esse requisito. |
| Pirâmide, saídas parciais, trailing e hedge | Não implementados | Exigem posição conciliada, risco agregado, custos e tratamento de execuções parciais antes de modificar exposição. |
| Martingale e aumento para recuperar | Não escolhidos | O prejuízo anterior não autoriza aumentar lote, afastar stop ou fabricar alvo de compensação. |

## Comparação implementada no painel

`risk_research.py` compara dez combinações: frações de 1%, 3%, 5%, 10% e 15% em duas bases, patrimônio atual e base limitada ao início. Cada combinação usa a mesma geometria, custos, margem e restrições de perda, para que a comparação seja coerente. A tabela mostra lote permitido e stops projetados até a trava da política. Não escolhe uma vencedora por lucro esperado, porque essa distribuição não foi estimada.

A aba Cenários técnicos permite comparar até oito geometrias de entrada/stop/alvo extraídas dos dados, cada uma com sua própria conta de risco. Ordenar por relação ganho/risco não transforma um alvo em provável. A aba Capital permite estudar um stop/alvo digitado, separado desses níveis técnicos.

## Política agressiva disponível

`agressivo_pesquisa` usa **15% do patrimônio por proposta**, piso diário correspondente a **50% do capital inicial** e tolerância de **50% de queda do pico**. São parâmetros arbitrários de laboratório, não calibrados nem escolhidos pelo usuário para operação real.

O perfil bloqueia novas propostas após quatro perdas consecutivas e aplica pausa de um minuto após perda. `max_contracts: 100` é um teto técnico configurável, não um lote desejado. O tamanho resulta do menor limite entre quantidade solicitada, teto técnico, orçamento dividido pelo risco unitário e margem disponível.

A margem considera uma reserva para a perda planejada ao lado da garantia. O orçamento de uma nova proposta é o menor entre:

- 15% do patrimônio corrente;
- patrimônio disponível acima do piso diário, descontado risco reservado;
- patrimônio disponível acima do piso de drawdown, descontado risco reservado.

Os pisos são restrições alternativas: seleciona-se a mais apertada, sem somar as reservas duas vezes. Ganhos podem ampliar o orçamento; perdas o reduzem. Posições abertas ou entradas pendentes bloqueiam novas propostas nesta implementação.

## Exemplos: R$ 400 e R$ 4.000

O [WIN vale R$ 0,20 por ponto](https://www.b3.com.br/en_us/products-and-services/trading/equities/mini-ibovespa-futures.htm). A [margem mínima publicada pela B3](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-participantes-e-traders/regras-e-parametros-de-negociacao/margem-minima-requerida-e-guia-educacional-para-minicontratos/) é R$ 155 por contrato; a corretora pode exigir mais.

Considere stop de 100 pontos e alvo de 200 pontos. A configuração acrescenta R$ 1 de tarifas hipotéticas e cinco pontos de slippage total, equivalentes a R$ 1: **R$ 2 de custos modelados**, não uma tabela real da corretora.

O risco unitário é R$ 22 e o ganho líquido condicionado ao alvo é R$ 38. Para dimensionar, cada contrato exige R$ 155 de margem mais R$ 22 de reserva: **R$ 177**.

| Cenário | Patrimônio R$ 400 | Patrimônio R$ 4.000 |
|---|---:|---:|
| Capital inicial da sessão | R$ 400 | R$ 400 |
| Pico informado | R$ 400 | R$ 4.000 |
| Orçamento de 15% | R$ 60 | R$ 600 |
| Piso diário / piso do pico | R$ 200 / R$ 200 | R$ 200 / R$ 2.000 |
| Lote admissível calculado | 2 | 22 |
| Perda planejada desse lote | R$ 44 | R$ 484 |
| Stops consecutivos até bloqueio da política | 4 | 4 |
| Contagem diagnóstica ignorando somente a trava de sequência | 7 | 6 |

Pressupostos: nenhuma perda consecutiva inicial, nenhuma posição pendente, toda a margem informada disponível e repetição da mesma geometria. A projeção recalcula o lote após cada stop e mantém o pico original. Lotes maiores explicam a menor contagem em R$ 4.000. As contagens não preveem oportunidades, duração dos trades ou quantas operações cabem no pregão. O cálculo é limitado em iterações; resultados truncados representam apenas o trecho calculado.

Após perder R$ 20, R$ 400 viram R$ 380 e o orçamento de 15% cai de R$ 60 para R$ 57. Recuperar R$ 20 é um objetivo do operador, não uma informação que aumenta a vantagem da próxima entrada.

## Resultados e pausa

O diário atualiza o capital a partir do resultado líquido digitado. Ganho aumenta o patrimônio; prejuízo diminui. Uma perda registrada inicia a pausa de 60 s do perfil de pesquisa. Um valor que esgote o patrimônio é preservado, inclusive saldo negativo; novos cálculos ficam indisponíveis. Reiniciar o aplicativo não restaura o capital anterior.

Uma sequência de perdas digitada no formulário, sem horário registrado, é assumida como cenário com a pausa já transcorrida; o sistema informa essa hipótese e mantém a contagem. Projeções de stops usam pausas hipotéticas entre tentativas. Nenhuma contagem representa número garantido de oportunidades ou capacidade real de sobreviver ao mercado.

## Execução e limites pendentes

A [Toro publica R$ 35 por contrato WIN em zeragem compulsória](https://www.toroinvestimentos.com.br/info/custos?hsLang=pt-br). Esse custo de estresse não está embutido nos R$ 2 ilustrativos. A [Nelogica documenta o pulo de ordens](https://ajuda.nelogica.com.br/hc/pt-br/articles/360053623191-Compreendendo-o-Pulo-de-Ordens); um stop planejado não garante execução pelo preço desejado. Perdas reais podem ultrapassar a reserva e o depósito.

Permanecem não implementados: calibração de lucro e valor esperado, escolha economicamente ótima de lote, gerenciamento de posição aberta, pirâmides, saídas dinâmicas, hedge e detecção automática do capital real. Saldos, pico, sequência e margem recebidos são pressupostos do cenário; sua obtenção e conciliação com Profit/Toro ainda exigem integração.


---

# Verificação da versão 0.3.0

Data: 06/10/2026. A entrega contém o aplicativo desktop JEV WIN, instalador por usuário para Windows x64, pacote portátil, código, modelos de exportação e documentação.

## Resultado e alcance

**166 testes automatizados passaram.** O autoteste do aplicativo também passou, incluindo quatro cenários sintéticos de fluxo, oito cenários técnicos, oito alternativas na Central e recálculo de capital. A conclusão do exemplo sem JEV é `AGUARDAR`. Os testes foram executados com Python no ambiente Linux de desenvolvimento. Nenhuma chamada autenticada à API JEV, conexão à Toro, conexão ao Profit do usuário ou ordem real foi realizada.

**A abertura da interface no Windows não foi validada.** O ambiente disponível não permite executar Wine e o servidor de display necessários a esse teste. Testes de lógica e inspeção do formato executável não substituem abrir a janela, verificar a instalação e testar Excel/RTD no computador do usuário. A mensagem exata da falha com o pacote anterior não foi recebida; não há diagnóstico confirmado da causa naquela máquina.

## Correções desta versão

- Instalador real com atalhos de abertura, diagnóstico e desinstalação, em lugar da dependência de abrir um executável portátil isolado.
- Inicialização pelo interpretador Windows oficial incluído no pacote. A inicialização principal deixa de depender do bootstrap CArchive personalizado usado na versão anterior.
- Pré-verificação de recursos, captura de falhas de início e callbacks, arquivos de diagnóstico e logs persistentes. Não são coletadas chaves, configurações completas, variáveis de ambiente ou payloads da API.
- Central de decisão como primeira aba, com conclusão, evidências, impedimentos, alternativas e histórico. A mesma projeção de dados produz um relatório HTML estático.
- Leitura combinada de cotações e negócios no mesmo arquivo Excel. Falha em uma tabela invalida o ciclo; a captura continua identificada como parcial.
- Verificação determinística de risco e correspondência da resposta JEV à fonte, geometria e prazo de validade antes de usar seu apoio contextual.

## Cobertura automatizada

- Cálculo monetário com Decimal: ponto, stop/alvo, custos, slippage, margem e lote inteiro.
- Limites por operação, perda diária, pico, reserva de margem/perda, sequência e pausa.
- Redimensionamento com capital variável, sem recuperação obrigatória ou aumento motivado pelo prejuízo.
- Projeção de stops e comparação de dez combinações de fração/base, sem ranking de lucro esperado.
- Eventos duplicados, horários, integridade, retenção e cobertura parcial de fluxo.
- Progressão, absorção e exaustão em exemplos sintéticos; exigência de informação de livro quando necessária.
- Extração de níveis observados, exclusão de informação futura, geometria e até oito pares por comparação.
- CSV/Excel: separador brasileiro, datas, serial Excel, ID estável e agressor desconhecido preservado.
- COM simulado: Excel existente, leitura Value2, liberação de recursos e ausência de contorno após erro de permissão.
- Fonte combinada: as duas tabelas, falha parcial, deduplicação, ordem temporal e percurso até os cenários técnicos com cotação amostrada.
- Contrato HTTP JEV, tipos, distribuição das respostas, sanitização de erros e rejeição de respostas inesperadas.
- Separação dos valores financeiros e do contexto de mercado enviado ao JEV.
- Motor de conclusão: veto financeiro, recálculo de lote, cobertura parcial, resposta antiga ou de outra fonte, geometria divergente e ausência de suporte inventado.
- HTML: valores escapados, ausência de scripts/requisições e exclusão de campos arbitrários e credenciais.
- Controlador da Central: persistência de transições imediatas, deduplicação e mudança de geração da fonte.
- Pausa real após perda registrada, hipótese explícita quando falta horário e preservação de patrimônio negativo no diário.

`test_inventory.json` contém o inventário por módulo. `desktop_self_test.json` registra o autoteste. Testes de API e COM usam respostas/objetos artificiais. Os testes do controlador usam a lógica real da atualização com componentes de tela substituídos; não executam uma janela Windows nem medem sua usabilidade.

## Empacotamento Windows

O novo instalador usa NSIS e inclui o runtime CPython 3.12.10 oficial para Windows x64, Tcl/Tk, SQLite, tzdata e comtypes. Instala em `%LOCALAPPDATA%\Programs\JevWIN`; diário e logs ficam separados em `%LOCALAPPDATA%\JevWIN` e são preservados na desinstalação. O portátil mantém o mesmo runtime e deve ser extraído inteiro antes de abrir `JevWIN.cmd`.

O processo de build registra formato PE, arquitetura, dependências privadas, recursos, extração e hashes dos arquivos distribuídos. O autoteste do código extraído pode ser executado com o Python Linux apenas para verificar lógica e recursos; isso não valida o interpretador Windows. Os relatórios de build descrevem o alcance exato das verificações. Instalador e lançadores não têm assinatura Authenticode.

O `JevWIN.exe` dentro da instalação é um lançador que depende da pasta completa. Não deve ser distribuído isoladamente. `WINDOWS_BUILD.md` descreve a reprodução do pacote; `GUIA_WINDOWS.md` explica instalação e diagnóstico. A confirmação da abertura nativa, da aparência, do comportamento do instalador e da integração real permanece pendente.

## Exemplos reproduzíveis, sem previsão de desempenho

| Caso de pesquisa | Resultado calculado |
|---|---|
| R$400; controle de 1%; stop 100 pontos; R$2 de custos hipotéticos | Nenhum contrato cabe no orçamento de R$4 |
| R$400; perfil de pesquisa de 15%; margem hipotética R$155; mesmo stop/custo | 2 contratos; perda planejada R$44; reserva de margem e perda R$354 |
| R$380 após perda de R$20; pausa transcorrida | 2 contratos nas mesmas hipóteses; orçamento por proposta cai para R$57 |
| Mesma perda registrada há menos de 60 segundos | Nova proposta de estudo bloqueada pela pausa |
| R$4.000; mesmas hipóteses | 22 contratos; perda planejada R$484; margem R$3.410 |
| Perda manual de R$401 sobre R$400 | Capital registrado em −R$1; novos cálculos bloqueados |
| Cotações RTD sem negócios individuais | Cotações observáveis; análise de fluxo indisponível |
| Cotação e tape combinados com cobertura parcial | Medidas e geometrias quando suficientes; confirmação permanece pendente |

Os valores de margem e custos são entradas dos exemplos, não cotação atual das condições da Toro/B3. As quantidades não são recomendações para a conta real. Stops projetados não garantem perda máxima.

## Revisão aplicada

A revisão desta versão encontrou dois problemas médios e verificou suas correções: pressuposto temporal de perda anterior não aparecia na Central/HTML; e uma limitação de frequência do diário podia perder transições rápidas. O pressuposto agora é exibido, cada alteração relevante é persistida e a geração da fonte fica registrada. Nove testes focados passaram no fechamento; fazem parte do total de 166. Não restaram pendências desses achados no escopo revisado.

Também permanecem cobertas as correções anteriores de expiração de cotação, alteração de capital, descarte de respostas de fonte anterior, distinção entre amostra RTD e livro, idade original do negócio e capital negativo.

## O que não foi demonstrado

Rentabilidade, lucro contínuo, recuperação de perdas, ganho de 900% em um dia, superioridade do JEV, probabilidade de alvo antes do stop, configuração ótima, tape completo, latência garantida ou sobrevivência da conta. Isso exige dados reais autorizados, conta conciliada e avaliação temporal fora da amostra com custos e execução plausíveis. A versão não contém simulador de fila, integração de notícias, gestão de posição aberta ou envio de ordens.

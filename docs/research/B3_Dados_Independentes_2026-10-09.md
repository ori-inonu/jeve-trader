# Dados B3 independentes do Profit — pesquisa em 2026-10-09

**Escopo:** ticket `01-dados-b3.md`; pesquisa pública, sem contratação, cadastro, autenticação, consultas ao JEV ou ordens. Este relatório reúne evidência para a especificação. Não seleciona fornecedor, não certifica integração e não estabelece direito de uso dos dados.

**Resultado:** existem rotas de dados independentes do Profit. A B3 oferece UMDF direto mediante infraestrutura e contrato. Cedro Socket e CQG WebAPI são alternativas comerciais com evidência pública de streaming e de licença no segmento de futuros da B3. Ainda falta comprovar WIN/WDO, vencimentos, continuidade e direitos de processamento pelo JEV no produto contratado. A Enfoque oferece uma terceira rota para diligência. A cobertura B3 publicada pela dxFeed consultada é de ações L1; ela não comprova mini futuros.

## 1. Instrumentos e autorização dos distribuidores

A B3 identifica os códigos-base **WIN** e **WDO** nas páginas dos respectivos contratos. São futuros com vencimentos, não apenas o índice à vista ou o par cambial. O símbolo operacional do fornecedor e o contrato específico devem ser resolvidos por metadados; a existência desses códigos na B3 não prova cobertura em determinado plano de API. Fontes: [WIN](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/futuro-mini-de-ibovespa.htm), [WDO](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/moedas/futuro-mini-de-taxa-de-cambio-de-reais-por-dolar-comercial.htm).

A [lista oficial de distribuidores licenciados](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/distribuidores/distribuidores-licenciados/) marca Cedro Technologies e Enfoque nas colunas de ações/opções e futuros/câmbio. CQG aparece em futuros/câmbio. dxFeed aparece em ações/opções, sem marcação na coluna de futuros/câmbio. Essa lista comprova a classificação pública da empresa, não o entitlement do Jeve Trader, o SKU, a profundidade ou cada vencimento disponível.

## 2. B3 direta: UMDF e infraestrutura institucional

A política de consumo situa o acesso direto em co-location próprio/de terceiros ou RCB. Portanto, a evidência não descreve uma API pública REST que o aplicativo Windows possa usar imediatamente pela internet. Fonte: [política de consumo vigente, §4.1](https://www.b3.com.br/data/files/66/82/D8/17/973699100A29E189AC094EA8/Politica%20de%20Consumo%20Market%20Data%20B3.pdf).

A [documentação UMDF da B3](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-desenvolvedores-e-vendors/fix-fast-umdf/) cobre negócios, livro, estado de instrumentos e estatísticas PUMA. O caminho FIX/FAST utiliza UDP multicast e canais de instrumentos. O TCP Replayer recupera incrementais do dia por FIX 4.4 e é indicado para perdas pequenas. Perdas grandes ou entrada tardia requerem snapshot. O Historical Replayer tem maior tempo de resposta e recomendação para gráficos; seu nome não comprova arquivo histórico de múltiplos anos ou replay irrestrito.

Na [especificação UMDF v2.2.2, §5.2.2 e seção de Sequence Reset](https://www.b3.com.br/data/files/EC/B1/9A/AD/2E86F910FC0436F9AC094EA8/UMDF_MarketDataSpecification_v2.2.2.pdf), `MsgSeqNum` identifica sequência de mensagens e `RptSeq` permite detectar lacunas por instrumento. A recuperação precisa respeitar sessões e resets: o TCP Replayer não disponibiliza mensagens anteriores a um Sequence Reset. Não se deve confundir o fluxo incremental com retransmissão genérica de sessão FIX.

**Inferência para o projeto:** acesso direto transfere responsabilidade de decodificação, canais, redundância, sessão, snapshot e recuperação para a infraestrutura de ingestão. Um snapshot atualizado do livro não demonstra recuperação dos negócios perdidos. Timestamps ordenados também não demonstram continuidade. A especificação futura deve conservar `full_tape=False` até haver prova explícita de cobertura do intervalo e mecanismo de recuperação.

## 3. Alternativas comerciais reais

| Rota | Fato público demonstrado | Limite que impede decisão final |
|---|---|---|
| Cedro Socket | Streaming B3 com cotações, livro completo/resumido e times & trades; modos real-time ou delay; segmento BM&F anunciado. [Produto oficial](https://cedrotech.com/market-apis/api-socket/) | A página não estabelece schema versionado, sequência por instrumento, recuperação de gap, SLA ou inclusão dos vencimentos WIN/WDO no SKU. A afirmação comercial de latência em milissegundos não é medição do projeto. |
| CQG WebAPI | API enterprise ASP, WSS/TLS e Protobuf, streaming L1/L2, histórico tick e barras. Exige conformance antes da produção. [Documentação oficial](https://help.cqg.com/apihelp/Documents/cqgwebapi.htm) | Mercados dependem de autorização/configuração. Demo é inteiramente simulada, sem comprovar B3 real. Falta confirmar habilitação WIN/WDO e a rota comercial de acesso ao aplicativo. |
| Enfoque e-Data/Feed | Anuncia dados históricos e em tempo real, webservices/socket personalizados e sinal Bovespa/BM&F via TCP/IP. [Produto oficial](https://enfoque.com.br/e-data) | A evidência pública consultada não entrega protocolo completo, event types de negócios/livro, sequência, recovery, preços ou símbolos. É alternativa de diligência, com maturidade documental pública inferior às duas anteriores nesta pesquisa. |

Na [página institucional CQG de 2025](https://www.cqg.com/2025), a empresa registra conectividade de market data e negociação B3 para futuros e ações. Isso complementa sua presença na lista B3, mas não resolve o entitlement do cliente.

O catálogo [dxFeed Equities & ETFs](https://dxfeed.com/market-data/equities-etfs/) descreve B3 Equities Level 1. Combinado à lista oficial da B3, o material encontrado **não comprova WIN/WDO**. Isso não demonstra impossibilidade comercial futura; impede tratar a marca B3, ofertas de outras bolsas ou recursos genéricos dxFeed como prova de mini futuros brasileiros.

**Varejo e customização:** a documentação CQG caracteriza WebAPI como enterprise; o catálogo Cedro dirige APIs a aplicações e fornece documentação/credenciais mediante processo comercial. Assinatura de terminal, login de corretora ou produto de varejo não foi demonstrada como autorização equivalente para ingestão própria, armazenamento e processamento por uma API customizada. Essa equivalência permanece pendente.

### Cedro: REST, WebSocket e arquivos não são intercambiáveis

A [API REST Cedro](https://cedrotech.com/market-apis/api-rest/) anuncia consultas HTTP com dados real-time ou delay. Portanto, REST não significa necessariamente cotação atrasada; atualidade depende do serviço contratado. **Inferência:** consulta de último preço por polling não demonstra que todos os negócios entre consultas foram recebidos.

A [página dedicada WebSocket](https://cedrotech.com/market-apis/api-websocket/) comprova cotações em streaming XML/JSON, B3/BM&F, real-time ou delay. Descrições cruzadas do catálogo usam rótulos de livro, enquanto o texto dedicado e a central de ajuda enfatizam cotação. Não há base suficiente para atribuir o mesmo times & trades/livro do Socket ao SKU WebSocket sem confirmação técnica.

A [central de ajuda Cedro](https://ajuda.cedrotech.com/market-data/quais-sao-as-apis-do-market-data-cedro/) distingue Tick By Tick em arquivo FTP com atualizações intradiárias e EOD em arquivo de fechamento. Esses arquivos podem servir a histórico/reconciliação se licenciados; não comprovam entrega streaming imediata ou recuperação automática de todo gap. A oferta histórica declarada também não comprova granularidade completa para cada WIN/WDO.

### CQG: observar entitlement, snapshot e collapsing

A [documentação Market Data Subscription](https://help.cqg.com/apihelp/Documents/marketdatasubscription.htm) informa que níveis/flags podem ser reduzidos por entitlement, contrato e bolsa. Metadados incluem `market_data_delay` e `end_of_day_delay`; sua ausência precisa ser lida junto ao status de acesso. O primeiro estado é snapshot; atualizações podem ser fragmentadas em várias mensagens. O servidor pode aplicar collapsing de DOM, BBA e trades sob condições documentadas. `collapsing_level` sinaliza o estado. Desabilitar collapsing explicitamente pode levar ao fechamento da conexão quando a fila chega ao limite. Histórico tick disponível não comprova que o cliente recupera, sem perdas ou duplicações, a faixa ausente após desconexão.

**Inferência para o projeto:** o contrato normalizado precisa expor atraso, nível efetivo, entitlement, collapsing, snapshot versus incremental e cobertura recuperada. WSS, conexão ativa e mensagens recentes não equivalem a tape completo.

## 4. Uso pelo JEV e mudança de política próxima

A B3 publica política vigente **até 31/10/2026** e nova política **a partir de 01/11/2026**. A integração planejada atravessa essa transição; o documento aplicável deve ser confirmado na data de contratação. Fonte: [índice oficial de políticas e contratos](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/distribuidores/politica-comercial-e-contratos/).

A [política de consumo vigente, §§3.3.2, 5.1 e 6.3](https://www.b3.com.br/data/files/66/82/D8/17/973699100A29E189AC094EA8/Politica%20de%20Consumo%20Market%20Data%20B3.pdf) distingue Display, Non-Display e desenvolvimento de produtos, este sujeito a avaliação prévia/contrato B3. Inclui produtos de análise/inteligência e certas utilizações próprias. Dados delay/EOD/histórico não têm autorização irrestrita para produto ou armazenamento. **Inferência, não conclusão jurídica:** licença de exibição de terminal não basta para presumir autorização de enviar dados brutos ao JEV, armazená-los, gerar features ou comercializar o copiloto. A finalidade exata e o processamento externo precisam de confirmação escrita.

A [política comercial 2026](https://www.b3.com.br/data/files/EA/C2/79/58/A73699100A29E189AC094EA8/Politica%20Comercial%20de%20Market%20Data_2026.pdf) separa cobranças por dataset, Display/Non-Display e modalidades de acesso. Seus valores não são cotação total de um fornecedor para Jeve Trader. Não foi obtido preço atual completo de nenhuma rota. Custos de infraestrutura, feed, direitos de uso, onboarding, histórico e suporte permanecem desconhecidos; desconhecido não significa zero.

## 5. Evidência a obter antes de escolher/contratar

Checklist de diligência proposto; não representa contratação nem aprovação:

1. **Cobertura exata:** declaração de WIN/WDO reais e lista de vencimentos; símbolos, calendário, fuso, sessão, rollover e metadados monetários. Confirmar demo versus produção e delay versus real-time.
2. **Eventos por SKU:** negócios individuais, identificadores, quantidade, correções/cancelamentos, campos de agressor quando existentes, BBA, livro agregado/por ordem e profundidade. Campos não fornecidos devem permanecer ausentes, sem inferência apresentada como observação.
3. **Continuidade:** especificação versionada e amostras autorizadas com sequências, resets, duplicações, snapshot, gap detectável, limites/retensão do replay e collapsing. Definir quais perdas podem ser recuperadas e quando a cobertura fica parcial.
4. **Histórico:** datas, granularidade, sessões, instrumentos expirados, ajustes e retenção. Diferenciar histórico de último preço/barras de negócios completos e livro reconstruível. Obter condições para reconciliar histórico com stream.
5. **Desempenho contratual:** limites de assinatura, mensagens, banda e concorrência; política de desconexão, reconnect, rate limits, SLA e manutenção. Separar latência da bolsa, do distribuidor e observada no Windows.
6. **Licenciamento:** contrato/entitlement B3 aplicável à data, Display/Non-Display/produto, retenção, derivados/features, processamento externo JEV, logs, replay, usuários e redistribuição. Não enviar dados privados ou licenciados ao JEV enquanto a permissão permanecer desconhecida.
7. **Preço e operação:** orçamento integral datado, taxa B3 repassada, acesso API independente de plataforma, exigência de intermediário/conta, onboarding/conformance, suporte e encerramento/exportação. Sem estimar custo faturado ausente.
8. **Prova independente:** demonstração autorizada em produção real de mercado, sem ordens, com trecho de sessão e incidente controlado de perda/reconexão. Revisão por pessoa/agente diferente do autor da integração. Fixtures e demo simulada não certificam comportamento do feed B3.

## 6. Insumos para uma SPEC posterior

Propostas derivadas das lacunas, a serem congeladas e revisadas independentemente pelo integrador:

- Identidade do instrumento inclui bolsa, classe, símbolo nativo e vencimento; índices/pairs spot não substituem WIN/WDO.
- Estado do feed e da UI distingue real-time, delayed, stale, disconnected, recovering, partial e unknown. Idade, origem e instante de observação ficam visíveis.
- Livro e tape possuem cobertura separada. Snapshot do livro não restaura automaticamente cobertura de trades. Nenhum detector eleva `full_tape` apenas por ordem de timestamps.
- JEV recebe somente conteúdo permitido, com procedência/qualidade declaradas; regras monetárias, validação e bloqueios seguem determinísticos locais.
- Nada nesta pesquisa amplia autorização para ordens, publicação, compra ou envio de segredos. Escolha posterior pode consultar Jev Workflows usando opções reais e evidência mínima sanitizada; recomendação não substitui direitos contratuais nem testes.

## 7. Evidência literal e proveniência

Trechos curtos de fontes primárias; cada identificador liga ao registro de hash abaixo. A ausência de informação é apresentada como não comprovada, nunca como negação absoluta de capacidade.

| Fonte | Evidência literal | Localização |
|---|---|---|
| S01 | “AÇÕES E OPÇÕES*” / “FUTUROS E CÂMBIO**” | Cabeçalho da tabela de distribuidores; conferir linhas Cedro, CQG, Enfoque e dxFeed. |
| S02 | “válida até 31/10/2026” / “válida a partir de 01/11/2026” | Títulos das políticas. |
| S03 | “A Licença para o Desenvolvimento de Produtos deverá ser avaliada previamente pela B3” | §6.3, página impressa 23. |
| S05 | “Esse método de recuperação deve ser usado apenas se poucas mensagens foram perdidas.” | Seção TCP Replayer. |
| S06 | “TCP Replayer is not available for messages prior to a Sequence Reset” | Seção Sequence Reset. |
| S07 | “Solução streaming que entrega cotações, book de ofertas (completo e resumido) e times & trades” | Descrição API Socket. |
| S08 | “Sinal Real-Time ou Delay” | Benefícios API WebSocket. |
| S09 | “Acessar dados da bolsa em tempo real ou delay” | Benefícios API REST. |
| S11 | “We require a formal conformance test before any API-powered application can connect to our production environment.” | Getting Access And Testing. |
| S12 | “Connectivity for futures and equity trading and market data” | Global Market Coverage, B3. |
| S13 | “First stage: DOM quotes are collapsed.” / “Third stage: Trade quotes are collapsed.” | Collapsing of market data. |
| S14 | “Sinal de Cotações em Tempo Real” / “via socket TCP/IP” | Corpo e-Data. |
| S15 | “B3 Equities Level 1 market data feed for equities from B3 (formerly BM&FBOVESPA)” | Brazil, B3. |
| S16 | “Código de negociação” / “WIN” | Características técnicas. |
| S17 | “Código de negociação” / “WDO” | Características técnicas. |

**Método dos hashes:** SHA-256 dos bytes do corpo HTTP recebido por `HttpClient`, após descompressão HTTP gzip/deflate quando aplicável, sem reconversão de texto. Respostas bem-sucedidas HTTP 200; URLs finais iguais às solicitadas. Coleta dos registros S01–S09 às `2026-10-09T04:48:46Z`, S10–S14 e S16–S17 às `2026-10-09T04:48:51Z`. Hash identifica a instância consultada, não autenticidade da fonte nem permanência futura de páginas dinâmicas. Nenhuma cópia do corpo de fontes ou de estado privado foi acrescentada ao repositório.

| ID / fonte primária | Bytes | SHA-256 |
|---|---:|---|
| S01 [B3 distribuidores](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/distribuidores/distribuidores-licenciados/) | 76943 | `9de3d64dab60203f471bf34b7f3becf73d8f6f8093a2359e0c52e67759981432` |
| S02 [B3 políticas](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/distribuidores/politica-comercial-e-contratos/) | 50242 | `67e283090576628dd8595ee45bca3747d0e1d83fe947c4f3f6243205cdc9d790` |
| S03 [Consumo vigente](https://www.b3.com.br/data/files/66/82/D8/17/973699100A29E189AC094EA8/Politica%20de%20Consumo%20Market%20Data%20B3.pdf) | 562463 | `1e56c699070a099945989abd1d4e891f4df6b7f05d25fda5d6552de7c0936285` |
| S04 [Comercial 2026](https://www.b3.com.br/data/files/EA/C2/79/58/A73699100A29E189AC094EA8/Politica%20Comercial%20de%20Market%20Data_2026.pdf) | 330318 | `457ec1f22561b59fc7aa97eed21d36268a08fe622e72503c40f85b5c3122b39c` |
| S05 [UMDF](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-desenvolvedores-e-vendors/fix-fast-umdf/) | 65810 | `dec4dc91e79728e7c924a292908c3c92c19761097afbe4d4a9a3509eeab26e9c` |
| S06 [UMDF v2.2.2](https://www.b3.com.br/data/files/EC/B1/9A/AD/2E86F910FC0436F9AC094EA8/UMDF_MarketDataSpecification_v2.2.2.pdf) | 2989248 | `e0ef01ecf65d9cb654b2e8f05e53a16dbb916691059b83996b69c1551ed1ecdb` |
| S07 [Cedro Socket](https://cedrotech.com/market-apis/api-socket/) | 202929 | `339135245dc42a02f864aa8eebdc8cb796e8f4deb356e6f564a4ada9c61acf4f` |
| S08 [Cedro WebSocket](https://cedrotech.com/market-apis/api-websocket/) | 202833 | `fae79deaeff9ad55603dc799e78c4b441662db3d39ce393100c1a8c674602b7d` |
| S09 [Cedro REST](https://cedrotech.com/market-apis/api-rest/) | 203619 | `f8f3a95dfc2b3737d1c10e708e79d11023c0e804923f8a01d74f63605f5864d8` |
| S10 [Cedro help](https://ajuda.cedrotech.com/market-data/quais-sao-as-apis-do-market-data-cedro/) | 107124 | `6001c806b4c3ab7d27a90c8b81caec14e0a1e2fd310ab4fc9263d4612a93d39c` |
| S11 [CQG WebAPI](https://help.cqg.com/apihelp/Documents/cqgwebapi.htm) | 14098 | `147f188d0516ba200c029cd0009ff2df48c8a7d3d0d6a6913c5b82f26774c1d6` |
| S12 [CQG 2025](https://www.cqg.com/2025) | 57357 | `a0d871b7bc125377725e6b878c4c0ab3fa9120be2697446b0835ffba23342347` |
| S13 [CQG subscription](https://help.cqg.com/apihelp/Documents/marketdatasubscription.htm) | 80733 | `1651f38cd0b09e6d779ac26a0a4bf85c9a322d31a97738e1ef8711840e58df45` |
| S14 [Enfoque e-Data](https://enfoque.com.br/e-data) | 35477 | `a06cedbd2110ae9e311559036774c47d3588dd961f34b0570f33b9f1a3d58c16` |
| S15 [dxFeed equities](https://dxfeed.com/market-data/equities-etfs/) | não disponível | Hash integral indisponível: fetch HTTP local recebeu 403. Evidência textual foi lida pelo navegador de pesquisa. |
| S16 [B3 WIN](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/futuro-mini-de-ibovespa.htm) | 43491 | `c8e33c5e6352b6a648b4742a9a14108c8db0c9ebf01cf43dd9c7775122427512` |
| S17 [B3 WDO](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/moedas/futuro-mini-de-taxa-de-cambio-de-reais-por-dolar-comercial.htm) | 43510 | `0694b754b2b43517c69d165d9eca3f4ddd29431d1b89ec8417238c424f88f15c` |

**Limitação literal S15:** `Response status code does not indicate success: 403 (Forbidden).` Não foi contornado. SHA-256 apenas do trecho literal S15 transcrito acima, UTF-8 sem quebra de linha, 80 bytes: `7adb34dac10bfee4fbcbc1aa95651c2369356e8b720d65be534fa673338cca3c`. Este é hash do trecho, **não** hash integral da fonte. A ferramenta de navegação recebeu `Failed to fetch https://enfoque.com.br/e-data: (502) Bad Gateway` em uma leitura posterior, mas HTTP local retornou 200 e o texto foi conferido diretamente; não se infere falha do serviço de dados desses erros de página pública.

### Contratos locais e identidade da tarefa

Hash SHA-256 dos arquivos consultados/pertinentes nesta rodada:

| Arquivo | SHA-256 |
|---|---|
| `C:/Users/gabri/OneDrive/Documentos/GitHub/jeve-trader/AGENTS.md` | `7805ec279f827c3e7208053ef1a669d06446093fc6fc957d6baec990fca5a799` |
| `.scratch/wayfinder-multimercado/issues/01-dados-b3.md` | `2d54a3266c9f180244236bd92cd26170f4e51ea8b09a37eb781a451ddebf34bc` |
| `C:/Users/gabri/.agents/skills/research/SKILL.md` | `985569f15739c713d6784887c3d186d4ef9ac85bec5ad9c068d25bf0739928e4` |
| `C:/Users/gabri/.codex/skills/codex-desktop-harness/SKILL.md` | `c77cd3459817b09970a7b8bcedeefd9f8383db78dba44e0b3ab42c471924e475` |

Identidade nativa observada no ambiente: `CODEX_THREAD_ID=01a11ef8-eb5d-7852-8ff6-b936c87f1e37` (pesquisador); `CODEX_SESSION_ID=01a11ef3-c241-7b81-a800-ee169307161e`. Recuperação do harness usou o próprio `CODEX_THREAD_ID`, com contexto bounded: revisão 0, fase research, status idle, próxima ação start. Metadados privados não autorizam trabalho nem foram copiados ao repositório. O integrador permanece responsável pelo ticket canônico, especificação e revisão independente.

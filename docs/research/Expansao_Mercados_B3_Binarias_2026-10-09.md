# Pesquisa delimitada — B3 e opções binárias

Consulta: **2026-10-09**. Autor: agente de pesquisa `/root/research_b3_binary`. Objetivo autorizado: investigar dados e preparar próximos passos; sem implementação, ordens, depósito, conta nova, contratação, instalação ou chamadas ao JEV do aplicativo. Entrega privada fora do repositório. Baseline informada pelo integrador: `da96c6ad4187030a98c4daa86a6b96e1e5b809a9`; alterações preexistentes preservadas.

## Conclusão para integração

A **ProfitDLL Market Data** é uma alternativa documentada à ponte Excel para negócios e livro B3: usa uma DLL Windows, permite iniciar apenas dados e exige contratação/licença própria. Há callbacks de negócios, livro por preço e ofertas individuais. Não foi identificada, nas fontes gratuitas consultadas, uma rota documentada que entregue gratuitamente a combinação WIN/WDO + todos os negócios + livro completo + histórico correspondente. Essa conclusão limita-se às fontes desta investigação e não prova inexistência universal. [Ecossistema ProfitDLL][N1], [acesso à DLL][N2], [funções de dados][N6], [brapi OpenAPI][A1].

A brapi documenta WIN/WDO sem token, mas seus endpoints de futuros consultados fornecem **último pregão e histórico diário**. É útil para referência e investigação histórica diária; a documentação não sustenta tratá-la como tape ou livro ao vivo. [brapi OpenAPI][A1].

A Deriv tem API pública oficial para ticks e histórico. Contudo, são **preços da plataforma**, com granularidade até um segundo no schema consultado; não há quantidade executada, agressor ou livro nesses schemas. A CVM publicou alerta e suspensão de ofertas públicas de intermediação da Deriv/Binary dirigidas a residentes no Brasil. A API pública, isoladamente, não estabelece elegibilidade jurídica nem vantagem econômica. [API Deriv][D1], [schema de ticks][D4], [termos de negociação][D3], [CVM Deriv/Binary][R1].

## Contrato atual do projeto

O projeto documenta Profit → exportação autorizada RTD/DDE → Excel aberto → valores lidos; não presume adaptador ProfitDLL existente. Excel/CSV têm `full_tape=False`. Capital e resultados continuam manuais; contexto ou `confidence` não são probabilidades calibradas de lucro. Estes contratos precisam sobreviver à expansão. [ARCHITECTURE.md](../ARCHITECTURE.md), [PRD.md](../PRD.md).

Evidência literal local: “As fontes Excel/CSV mantêm `full_tape=False`.” — `docs/ARCHITECTURE.md:73`. SHA-256 do arquivo: `BDF2AED8AD163C5380EDACAC63275E9D475F391D86F1C4CA79C648C8F0D8CEBE`. SHA-256 de `docs/PRD.md`: `D7AD3CE616F51B3752A90DBF3C0C66CF0852438D343E4F4A722BC09FC38F85BC`.

## Comparação dos dados documentados

L2/MBP = agregado por preço; MBO = ofertas individuais visíveis. Classificar MBO como “L3 integral” exigiria ainda verificar identificadores, cobertura e continuidade reais. Nenhuma sessão de feed foi testada nesta pesquisa.

| Rota | Preço/negócios/volume e livro | Histórico e continuidade | Latência, limites e acesso |
|---|---|---|---|
| ProfitDLL Market Data | Negócios executados: preço, quantidade, agentes, horário com milissegundos e tipo de agressão. Topo, PriceDepth agregado e OfferBook individual com agente/posição/preço/quantidade e ações de inclusão, edição ou exclusão. Volume por preço pode ser calculado a partir dos negócios recebidos, com cobertura explicitada. | `GetHistoryTrades`: limite **10 dias por pedido**, recomendação diária. Isso não estabelece retenção total. Conexão/callbacks precisam ser monitorados; dados recebidos não demonstram integralidade automaticamente. | Dados por callbacks; não foi localizado SLA numérico ponta a ponta. `TNewDailyCallback` é periódico em segundos e não substitui cada negócio. Assinatura, chave/login e SDK autorizados; preço total não estabelecido nesta pesquisa. [Funções DLL][N6], [PriceDepth][N3], [histórico][N4], [acesso][N2]. |
| B3 Binary UMDF direto | Manual v2.3.1.1 documenta SBE sobre UDP multicast e **MBO**; MBP/TOB não são perfis desse protocolo. Eventos de negócios e `ExecutionSummary` permitem agressor onde o resumo existe; ele não é gerado em todos os tipos de execução. | Snapshot recupera estado do livro, não todos os negócios perdidos. Detectar gaps e conciliar incrementais é requisito de coleta. Arquivo histórico de tape é aquisição/armazenamento separado a confirmar. | Produto de baixa latência relativa; SLA numérico não estabelecido. Acesso direto exige conexão e contrato; há também distribuidores licenciados. Não é API REST gratuita. [Manual Binary UMDF][B2], [produto][B1], [consumo][B3]. |
| B3 UP2DATA | Fechamento e referência distribuídos em arquivos; documentação de entrega não descreve tape e livro intradiários. | A maioria das informações D0 é publicada ao fim do dia. API de monitoramento de publicação de arquivos não equivale a stream de negócios. | Desktop/cloud e CSV/JSON/TXT/XML; horários dependem do conteúdo. Custo/entitlement específico e limites não estabelecidos nesta leitura. [Entrega UP2DATA][B5]. |
| brapi — futuros | Cotação do último pregão: máxima/mínima/fechamento/ajuste/volume diário; não há rota de livro ou agressor documentada nos endpoints de futuros consultados. | Diário, cerca de um ano; `open` sempre nulo nesse produto. Histórico termina no vencimento; construir contínuo exige política de rolagem explícita. | `quote/specs` até 20 contratos por pedido; Pro, com exceção documentada sem token para símbolos WIN/WDO. Frequência intradiária/SLA de atualização desconhecidos. Quotas totais, preço vigente e redistribuição não foram estabelecidos. [brapi OpenAPI][A1]. |
| Deriv — público oficial | `ticks`: `quote`, `epoch`, `symbol`, `pip_size`, `id`, `ask`/`bid` opcionais; **sem volume executado, agressor ou ordens**. `id` da resposta é identificador da assinatura/conexão, não identidade de negócio de bolsa. | `ticks_history`: preços/tempos ou candles OHLC; sem volume. `count` padrão 1000, não um máximo provado; início padrão de um dia não prova retenção. Histórico pode depender de licença. | Stream até um segundo no schema; não é SLA. Documentação atual: grupo de dados WebSocket 220 chamadas/min e 14.400/h, limites por categoria. Endpoint público não requer autenticação. Elegibilidade no Brasil pendente. [Schemas][D4], [pedido histórico][D5], [resposta histórica][D6], [limites][D2], [API][D1], [CVM][R1]. |
| IQ Option via `iqoptionapi` comunitária | README oferece candles e streams de candles; o próprio projeto declara ser não oficial. Não demonstra tape completo/L2/agressor de uma bolsa. | README alerta aproximadamente 30 segundos de atraso em `get_candles`; funções de realtime candles são diferentes. Retenção e continuidade atuais não testadas. | Usa login/senha no exemplo, sem contrato oficial de estabilidade ou SLA identificado nesta investigação. Sem login ou instalação realizados. Alerta CVM impede recomendação operacional com a evidência atual. [README comunitário][W2], [CVM IQ Option][R2]. |

## Licença, gratuidade e expansão B3

A aquisição de código aberto e a contratação de dados são contratos diferentes. O exemplo comunitário DLLNelogica reconhece a necessidade de licença Nelogica; qualquer afirmação desse repositório sobre redistribuir o binário é afirmação do mantenedor, não comprovação de autorização contratual para o Jeve Trader. O acesso oficial ao SDK vem depois da contratação e download na assinatura “DLL Feed”. [Avisos do exemplo][W1L], [acesso oficial][N2].

Na B3, acesso pode ser direto ou por distribuidor. A política distingue aplicações/instâncias e usos **Non Display**, inclusive estratégias e usos não associados à tela. É preciso confirmar enquadramento do copiloto, armazenamento, histórico e redistribuição com o fornecedor; possuir tela Profit não demonstra esses direitos. Há política comercial 2026 e transição de consumo anunciada para **01/11/2026**: registrar a versão aplicável antes da contratação. Não foi calculado custo final de conexão, licença ou infraestrutura. [Consumo B3][B3], [comercial 2026][B4], [vigência e contratos][B7].

O catálogo pode investigar outros produtos B3 — o material oficial inclui BIT, ETR, SOL, GLD e EUP além de WIN/WDO. Essa lista não demonstra liquidez, capacidade de alavancagem admissível ou que a licença já inclua os instrumentos. Especificações por contrato, horário, vencimento, valor de tick, margem e custos vigentes devem vir das fichas contratuais e corretora antes de qualquer comparação operacional. As tabelas educacionais não são configuração de risco. [Material B3 sobre produtos][B6].

Dados de cliente/KYC não foram solicitados. ProfitDLL exige assinatura/login e UMDF exige habilitação comercial/técnica; requisitos individuais de cadastro continuam desconhecidos. UP2DATA não foi tratado como produto gratuito. brapi sem token e Deriv público reduzem a necessidade de credenciais na consulta documentada, mas não demonstram permissão de redistribuição nem feed integral. [Acesso Nelogica][N2], [consumo B3][B3], [UP2DATA][B5], [brapi][A1], [API Deriv][D1].

## Binárias: natureza dos preços, payout e Brasil

“Binary” no nome **Binary UMDF** significa formato binário de mensagens de dados B3; não identifica opções binárias OTC. O modelo usual de opção binária oferece pagamento predeterminado ou nada, condicionado a um evento, e não dá direito de comprar/vender o ativo subjacente. Esse produto não deve ser fundido com a categoria das opções listadas convencionais no catálogo do Jeve Trader. [Manual UMDF][B2], [SEC: binárias][R3].

Termos Deriv R26|03, de **20/08/2026**, §§2.1.1.8, 2.2.1.1–3, 2.3.1 e 6.2: atualização de preço no máximo uma vez por segundo; quando há múltiplos ticks, último válido; preço OTC sem referência central oficial, podendo usar média bid/ask sem negócio recente; payout depende de modelo com viés a favor do provedor. Uso excessivo/redistribuição pode motivar bloqueio. Portanto não há payout fixo universal nem retorno esperado verificável sem amostras, contrato, custos e regras de liquidação. [Termos de negociação Deriv][D3].

Os termos gerais Deriv R26|03 de **17/09/2026** tornam produtos/entidade dependentes do país e prevêem KYC, identidade/endereço e possível recusa/restrição da conta. Acesso público a preço é diferente de elegibilidade de cliente. [Termos gerais, §§2.8, 2.11 e 5.1][D7].

A CVM publicou alerta Deriv/Binary em 14/06/2023, atualizado 29/01/2024, sobre ausência de autorização para intermediação/captação e suspensão da oferta pública dirigida a residentes no Brasil; a medida é preventiva. Para IQ Option, o alerta de 26/04/2021, atualizado 01/02/2024, também reforça ausência de autorização. A situação cadastral e eventual revogação posterior não foram verificadas neste trabalho. A conclusão proposta é **adiar elegibilidade operacional**, sem afirmar proibição universal de qualquer produto binário. [CVM Deriv/Binary][R1], [CVM IQ Option][R2].

A SEC/CFTC relata reclamações sobre recusa de saque, roubo de identidade e manipulação de software em plataformas de binárias pela internet. Isso descreve reclamações/riscos e não prova fraude de toda plataforma. Sem dataset próprio e conciliado, esta pesquisa não mede acerto, rentabilidade ou probabilidade de transformar R$400 em R$4.000. [SEC: binárias][R3].

## Evidência literal curta

| Origem | Trecho exato | O que sustenta |
|---|---|---|
| Nelogica acesso | “Após a contratação da ProfitDLL” | A rota requer contrato; arquivo não é licença. [Nelogica][N2]. |
| Nelogica histórico | “Intervalo máximo por requisição” / “10 dias” | Tamanho de pedido, não retenção total. [Histórico DLL][N4]. |
| Deriv schema pinned | “Latest spot price for a given symbol. Continuous responses with a frequency of up to one second.” | Atualização de preço, não tape de negócios. [Schema ticks][D4]. |
| Wrapper IQ | “this is a no official repository, it means it is maintained by community” | Autoria comunitária, não API oficial. [README][W2]. |
| Wrapper DLL: licença | “Ter o binário não substitui a licença.” | O próprio exemplo não dispensa entitlement. [Avisos][W1L]. |

## Proposta de requisitos e aceites independentes

Estes itens são candidatos para o integrador e revisor; não representam implementação nem aprovação/autocertificação.

| ID | Requisito proposto | Aceite observável a congelar |
|---|---|---|
| DAT-B3-01 | Separar cotações, negócios executados, MBP/MBO, referência diária e preços OTC. | Para cada adaptador, schema/capability registra origem e cobertura; cotação/candle não satisfaz teste de tape. Evidência: [N6][N6], [B2][B2], [A1][A1], [D4][D4]. |
| DAT-B3-02 | Preservar `full_tape=False` até validar captura e recuperação reais. | Teste independente com fonte autorizada identifica gaps, duplicatas, reconexão, correção e fronteira histórico/ao vivo; relatório não confunde snapshot com recuperação dos negócios. [Contrato local](../ARCHITECTURE.md), [UMDF][B2]. |
| DAT-B3-03 | Calcular volume por preço somente com quantidade executada e identificação suficiente; aplicar cancelamentos/correções quando fornecidos. | Reconciliação por ativo/vencimento/janela confronta negócios capturados com referência independente, com diferenças visíveis; Deriv e diário não passam por simulação de volume. [DLL][N6], [UMDF][B2], [schemas Deriv][D4]. |
| DAT-B3-04 | Licença, custo vigente e elegibilidade precedem ativação de coleta autenticada. | Evidência contratual registra uso display/non-display, histórico, armazenamento e redistribuição. Dados/segredos ficam privados. [Nelogica][N2], [B3 consumo][B3], [CVM][R1]. |
| DAT-BIN-01 | Manter binárias OTC fora da elegibilidade operacional com pendências regulatórias e sem calibração econômica. | Revisão independente confirma situação regulatória/produto/provedor; dataset e validação fora da amostra precedem qualquer comparação de retorno. Probabilidade contextual do JEV nunca vira taxa de acerto financeira. [CVM][R1], [CVM IQ][R2], [termos Deriv][D3], [PRD](../PRD.md). |

Alternativas reais: **(1)** ProfitDLL Market Data após contrato/SDK — menor ruptura no contexto atual, sujeita à captura real; **(2)** distribuidor B3 licenciado com API de negócios e livro — solicitar documentação e cotação para as mesmas capacidades, sem presumir fornecedor gratuito; **(3)** UMDF direto — protocolo documentado, maior dependência de conexão e recuperação; **(4)** continuar Excel parcial e brapi diária para pesquisa enquanto licença/capacidade são verificadas. Escolha final de rota não foi implementada nem contratada. [Nelogica][N1], [B3 consumo][B3], [UMDF][B2], [brapi][A1], [arquitetura local](../ARCHITECTURE.md).

Próximas tarefas elegíveis: congelar contrato comum de dados; preencher inventário de entitlement e preço; revisar documentação do SDK autorizado; definir captura em modo observador com comparação independente; medir latência e continuidade; só depois preparar dataset econômico e ranking. Não são objetivos desta entrega: roteamento, martingale/recuperação de perda, scraping de login, bypass de licença/antibot, inferência de livro por pixels, contratação automática, margem operacional ou promessa de rentabilidade.

Consulta consultiva Jev sobre **sequência da pesquisa**, sem fonte privada: recomendou `official_feed_then_wrappers`, confiança 0,87; recibo `1014eee2-b3fc-43d9-be7f-de5feaeb7d28`, digest `43fc4eafa58842605657943632cfcfa502f235fb4e67b2e8ac6b60b80207fee6`, modelo `jev-1.13.0`, rubric `decision-2026-09-26.2`, persistido. Custo faturado desconhecido. Limitação de proveniência: origin.chatId foi preenchido inicialmente com identidade informada do integrador `[identidade privada omitida]`; a variável nativa do agente revelou depois `[identidade privada omitida]`. Contexto próprio foi lido com essa identidade; não importou estado do integrador. Conselho não aprovou execução ou especificação.

## Observado, não testado e bloqueios

**Observado:** leitura de documentação oficial, schemas públicos e contratos locais; HTTP 200 das representações catalogadas abaixo; callbacks/streams descritos nas fontes. **Não testado:** conectividade a feeds, autenticação, entitlement, tick/tape reais, compatibilidade com SDK instalado, latência medida, gaps de pregão, quantidade de histórico recuperável, KYC efetivo, custos totais, rentabilidade ou continuidade do funcionamento após restart.

Fetch direto das cinco páginas Nelogica N1/N2/N3/N4/N6 retornou **HTTP 403**. O navegador de pesquisa pôde lê-las, e a API pública oficial Zendesk forneceu os artigos com HTTP 200; os hashes abaixo são do JSON oficial efetivamente obtido, não da tela de bloqueio. Não houve login, alteração de TLS ou bypass. Tentativas auxiliares a `https://brapi.dev/llms.txt` e URLs `.md` sugeridas retornaram literalmente **“Internal Error”** no navegador de pesquisa; a OpenAPI foi lida normalmente. Esse erro não foi tratado como ausência do produto.

## Catálogo de fontes e hashes

Todos os acessos abaixo ocorreram em **2026-10-09**. SHA-256 refere-se aos bytes do corpo HTTP obtidos por `fetch` em memória, após descompressão HTTP; não foi salvo feed nem payload privado. HTML/JSON dinâmicos podem mudar entre acessos. Para Nelogica, o alvo de hash é a API oficial `https://ajuda.nelogica.com.br/api/v2/help_center/pt-br/articles/<ID>.json`; as citações apontam para a página humana correspondente. Para schemas Deriv, versão fixada no commit `54e353807146d31f58291693243cbbf671de7bce` (commit consultado de 2026-09-07). Raw público equivalente ao blob citado. Código não foi executado ou instalado.

| ID / fonte | Representação/versionamento | SHA-256 |
|---|---|---|
| [N1 — Ecossistema ProfitDLL][N1] | JSON artigo 22396517026203, atualizado 2026-05-20 | `d2a56a2af5422881dc296b96eb2d0e771b6cf29725efd079f0fef2f4134a487c` |
| [N2 — Acesso ProfitDLL][N2] | JSON artigo 51583791325211, atualizado 2026-09-15 | `6267779484867a8d33b2d073128e4801aaf7f655935d71a3b10dd46489cacd3a` |
| [N3 — PriceDepth][N3] | JSON artigo 50587290263835, atualizado 2026-05-19 | `cee8a0e059e26ee136ba8d05b8a4d126eef9ca3135c685d09f0b75f379ea9039` |
| [N4 — Histórico][N4] | JSON artigo 11973319153563, atualizado 2026-05-19 | `ba4b34bc3a79b2c9408d3e8c2ee7ec064ab72d6243c975277022fcb16eeda29a` |
| [N6 — Funções Real Time][N6] | JSON artigo 11168755650459, atualizado 2026-05-21 | `2b0c1e1c45410e153d3506c866edc7d70131bbdcab03d84d9da5e82bdba29cda` |
| [B1 — Binary UMDF][B1] | HTML 200 | `4522df0d27d63b7056b38ef523f8ee82a71fe1ed753ca4248b899733a699ba44` |
| [B2 — Manual Binary UMDF][B2] | PDF v2.3.1.1, changelog 19/08/2026 | `2568afa165eae6c19dc83faa8de49c780e81f640d43c719197e9912d4472c2aa` |
| [B3 — Consumo Market Data][B3] | PDF, vigente antes de 01/11/2026 | `1e56c699070a099945989abd1d4e891f4df6b7f05d25fda5d6552de7c0936285` |
| [B4 — Comercial Market Data][B4] | PDF 2026 | `457ec1f22561b59fc7aa97eed21d36268a08fe622e72503c40f85b5c3122b39c` |
| [B5 — Entrega UP2DATA][B5] | HTML 200 | `65678847b9bdc56c62c61a19fbbf5bbd1d0cb9aee30933b6c49e3d277baef78a` |
| [B6 — Produtos B3][B6] | HTML 200 | `800ddb27ade21cef11aafe291cab94e06d85cb9e6423b4dd4143e708bc85214c` |
| [B7 — Vigências e contratos][B7] | HTML 200 | `21528d8f09d85aeb02351603dd42a83fc858f9e42ca9c997fbed61a234fa7b41` |
| [A1 — brapi OpenAPI][A1] | HTML 200 com spec da página | `0711e73b3e7c481c555435b8d1d6f257d287520ff09463428a84aa6b2842817d` |
| [D1 — Deriv API overview][D1] | HTML 200 | `1cdc7e0a8eed399de4d9d888b3014f1614a5588be3c7ac4e0953ce7fbef00947` |
| [D2 — Limites Deriv][D2] | HTML 200 | `c93efcbc2a397a460ee1ede5da0aff1414998118624c42d327078f2e4140a96e` |
| [D3 — Termos de negociação][D3] | HTML R26\|03, 20/08/2026 | `ae878a506e9280c12e182e0f53a71a7249236d71bdebdb6faa7851226943cf0d` |
| [D4 — Schema ticks][D4] | Raw pinned, SHA citado acima | `e45cb48b2d3bdcc02f89456b2a3d7e9745c0c6ca1588233b15b7c6732b41ea5b` |
| [D5 — Schema pedido histórico][D5] | Raw pinned | `3768ec3b34f05d61e4860481b481ab40503da5f7ca6af69903242ae5662ee4be` |
| [D6 — Schema resposta histórico][D6] | Raw pinned | `fc19cb71a06417c4dcd4f30b084fb9a3e2fc2bd7312e6e6d3855e20244a7d23a` |
| [D7 — Termos gerais Deriv][D7] | HTML R26\|03, 17/09/2026 | `401ce95fd0307e1f90b33510b21719d9e553485d75271b9e9cd0ed15dd8c2fd0` |
| [R1 — CVM Deriv/Binary][R1] | HTML 200 | `f4d6f28ba6e7104c55c1304e9eca9a727bcf1b845b92ed1148e27ea7eb1423c5` |
| [R2 — CVM IQ Option][R2] | HTML 200 | `cd99cae7afbe3f81f07cabd1a3dd4780ca9287e53cd96970cd0e48ff3a628c39` |
| [R3 — SEC/CFTC binárias][R3] | HTML 200 | `6008564cd17f12de008c8ac2a99fbd4cbc503b2e147c471511ede9e7676f5890` |
| [W1L — Avisos do DLLNelogica][W1L] | Raw branch main; declaração do mantenedor | `24dee37cdbc27560560e4cebd834b3cd60b13827abdca71948806460bc1017b1` |
| [W2 — README IQ comunitário][W2] | Raw branch master; declaração do mantenedor | `f29689fd522ad38823262a6d4d714753ca97ce4b70e94223395ad84cc51e5b4d` |

Referências internas úteis no manual B2: MBO (p.14), snapshot/recovery (pp.50–58), `ExecutionSummary` (p.83), `TradeBust` (p.94). A numeração é a impressa no PDF; o índice do visualizador pode diferir em uma página.

[N1]: https://ajuda.nelogica.com.br/hc/pt-br/articles/22396517026203-Ecossistema-ProfitDLL-e-primeiros-passos
[N2]: https://ajuda.nelogica.com.br/hc/pt-br/articles/51583791325211-Como-obter-acesso-%C3%A0-ProfitDLL
[N3]: https://ajuda.nelogica.com.br/hc/pt-br/articles/50587290263835-Como-utilizar-o-Livro-de-Profundidade-Price-Depth-via-DLL-Real-Time
[N4]: https://ajuda.nelogica.com.br/hc/pt-br/articles/11973319153563-Como-requisitar-trades-hist%C3%B3ricos-com-a-ProfitDLL
[N6]: https://ajuda.nelogica.com.br/hc/pt-br/articles/11168755650459-Fun%C3%A7%C3%B5es-Real-Time-DLL
[B1]: https://www.b3.com.br/en_us/solutions/platforms/puma-trading-system/for-developers-and-vendors/binary-umdf/
[B2]: https://www.b3.com.br/data/files/F6/82/B3/0F/F2A30A105BF9020AAC094EA8/BinaryUMDF-MessageSpecificationGuidelines-v.2.3.1.1-enUS.pdf
[B3]: https://www.b3.com.br/data/files/66/82/D8/17/973699100A29E189AC094EA8/Politica%20de%20Consumo%20Market%20Data%20B3.pdf
[B4]: https://www.b3.com.br/data/files/EA/C2/79/58/A73699100A29E189AC094EA8/Politica%20Comercial%20de%20Market%20Data_2026.pdf
[B5]: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/up2data/central-de-ajuda/entrega-de-informacoes.htm
[B6]: https://borainvestir.b3.com.br/tipos-de-investimentos/renda-variavel/day-trade/conheca-as-caracteristicas-dos-principais-produtos-de-day-trade/
[B7]: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/distribuidores/politica-comercial-e-contratos/
[A1]: https://brapi.dev/docs/openapi
[D1]: https://developers.deriv.com/docs/intro/api-overview/
[D2]: https://developers.deriv.com/docs/limits/
[D3]: https://deriv.com/terms-and-conditions/trading-terms
[D4]: https://github.com/deriv-com/deriv-api-schemas/blob/54e353807146d31f58291693243cbbf671de7bce/schemas/ticks_response.schema.json
[D5]: https://github.com/deriv-com/deriv-api-schemas/blob/54e353807146d31f58291693243cbbf671de7bce/schemas/ticks_history_request.schema.json
[D6]: https://github.com/deriv-com/deriv-api-schemas/blob/54e353807146d31f58291693243cbbf671de7bce/schemas/ticks_history_response.schema.json
[D7]: https://deriv.com/terms-and-conditions/general-terms-of-use
[R1]: https://www.gov.br/cvm/pt-br/assuntos/noticias/2023/cvm-alerta-para-atuacao-irregular-de-deriv-com-e-binary.com
[R2]: https://www.gov.br/cvm/pt-br/assuntos/noticias/2021/cvm-reforca-alerta-de-atuacao-irregular-da-iq-option-ltd
[R3]: https://www.investor.gov/protect-your-investments/fraud/types-fraud/binary-options-fraud
[W1L]: https://github.com/YouTrade/DLLNelogica/blob/main/THIRD-PARTY-NOTICES.md
[W2]: https://github.com/iqoptionapi/iqoptionapi/blob/master/README.md

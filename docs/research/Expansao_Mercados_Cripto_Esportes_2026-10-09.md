# Jeve Trader — coleta de dados cripto e esportes

Pesquisa delimitada em 2026-10-09. Autor: pesquisador auxiliar; conversa própria `01a11ee3-1734-7602-a28a-5b63b56b816a`, sessão `01a11ee0-293d-7a82-8719-5c41909aebcb`. Repositório somente leitura, baseline `da96c6ad4187030a98c4daa86a6b96e1e5b809a9`. Este arquivo é investigação e requisitos propostos; não implementa nem certifica uma especificação. Nenhuma conta, chave, ordem, depósito, assinatura de dados ou dependência foi criada.

## Resultado e relação com a meta financeira

O objetivo do usuário permanece filtrar mercados que tenham mecanismo de alavancagem e dados suficientes para estudar R$400 → R$4.000 em menos de uma semana. Isso exige multiplicar o capital por 10, ganho líquido de 900%. Disponibilidade de dados, exposição mecânica e probabilidade de alcançar essa meta são três variáveis diferentes. A pesquisa não estima P(meta), retorno esperado ou rentabilidade de qualquer candidato.

**Cripto spot público é uma infraestrutura viável para validar coleta e microestrutura**, com REST observado e contratos WebSocket documentados. Spot comprado sem empréstimo não fornece alavancagem embutida; entra como referência e laboratório, não como vencedor da seleção financeira. Dados desse mercado não substituem o tape de WIN/WDO ou o livro da B3.

**Perpétuos/futuros cripto merecem uma linha própria no filtro de mercados alavancados**, porque possuem preço de marcação, índice, funding e dados de livro/negócios específicos. A documentação técnica consultada não demonstra autorização ou disponibilidade do produto para esta conta residente no Brasil. Não se recomenda operação offshore ou lote. O gate de entidade, jurisdição, produto e permissões segue pendente.

**Betfair Exchange possui microestrutura útil, mas a API pessoal direta está expressamente indisponível para clientes brasileiros.** Isso impede tratar uma chave pessoal como próximo passo elegível. Odds e estatísticas de fornecedores REST podem apoiar pesquisa esportiva; seus schemas não equivalem ao livro e tape de uma exchange. [Betfair: Brasil — acesso direto](https://support.developer.betfair.com/hc/en-us/articles/17814508363804-Brazil-Direct-API-Access-Not-Available).

## Fontes spot e bibliotecas

| Candidato | Contrato de dados consultado | Implicação e estado |
|---|---|---|
| Binance Spot nativo | REST público; WS `trade` individual, `aggTrade` agregado por ordem tomadora; L2 agregado por preço | Quatro pequenos GETs, dois desta fonte, responderam; WS ainda não exercitado. Primeira alternativa para especificar um laboratório de coleta. |
| Kraken Spot v2 nativo | WS de trades com lado tomador; L2 e checksum; REST público | Dois GETs responderam. Alternativa para comparar explicitamente outro contrato e recuperação. |
| CCXT/CCXT Pro | Biblioteca MIT, REST e WS conforme exchange/capacidade | Código aberto não abre os dados, não remove regras geográficas nem concede redistribuição. Pro integra a biblioteca gratuita atual; WS não deve ser descrito como necessariamente pago. |

### Binance Spot

Contrato documentado: `@trade` expõe ID, preço/quantidade como strings, timestamps e `m` indicando comprador maker. A transformação local `m=true → agressor vendedor` é derivação dessa semântica. `@aggTrade` não deve ser contado como negócios individuais. L2 usa `U/u`, quantidades absolutas e zero para excluir nível; cadência documentada de 1000 ou 100 ms. A recuperação exige stream com buffer e snapshot REST, descarte de atualizações antigas e reinício quando houver lacuna; snapshot tem máximo de 5000 níveis por lado, portanto níveis externos não são conhecidos até atualização. Não é L3 nem evidência de todas as intenções de ordens. A conexão termina em 24 h; ping a cada 20 s, pong em até 1 min; limite de 5 mensagens de controle/s, 1024 streams/conexão e 300 tentativas/5 min/IP. Timestamp padrão em ms, opção de microssegundos. Esses tempos são contratos, não latência medida nem SLA. [Documentação oficial fixada por commit](https://raw.githubusercontent.com/binance/binance-spot-api-docs/e556feb906511189fc423e3b58c0452366e802d3/web-socket-streams.md).

Evidência literal curta: “If the event `U` > the update ID of your local order book + 1”. Esta condição exige invalidação, não preenchimento fictício de continuidade. Fonte S01.

Histórico público oficial oferece trades, aggTrades e candles, arquivos diários no dia seguinte e mensais na primeira segunda-feira. Desde 2025-01-01 os timestamps spot do arquivo são em microssegundos; tratar arquivos anteriores como iguais causaria erro de escala. Cada ZIP acompanha `.CHECKSUM` SHA-256 e arquivos podem ser revisados. Não foi identificado arquivo L2 nos conjuntos enumerados pelo README consultado; isso não prova inexistência de outro produto. A publicação pública do arquivo e a licença do código não estabelecem, sozinhas, licença de redistribuição comercial do feed. [Binance Public Data](https://raw.githubusercontent.com/binance/binance-public-data/bd110bb04caad6ad964a0098809f18343b1e104b/README.md).

### Kraken Spot v2

O `book` público é L2, profundidades 10/25/100/500/1000, snapshot habilitado por padrão e CRC32 dos dez melhores níveis de cada lado. O schema L2 examinado não oferece o par `U/u` da Binance; timestamps não substituem continuidade. [Book v2](https://docs.kraken.com/exchange/api-reference/spot-websocket-v2/book).

O `trade` pode agrupar vários negócios numa mensagem sem afirmar mesma ordem tomadora; `side` é o lado do taker, `trade_id` é único por livro, e snapshot opcional contém os últimos 50 negócios. Preço e quantidade são números JSON: o parser deve preservar decimal antes de calcular volumes e checksum. [Trade v2](https://docs.kraken.com/exchange/api-reference/spot-websocket-v2/trade). Evidência literal: “The side of the taker order”.

Aplicar todos os updates, excluir quantidade zero, truncar à profundidade contratada e só então verificar CRC32 é requisito do guia. Checksum top-10 não prova integridade de níveis externos. Nova inscrição com snapshot após divergência é proposta de recuperação; não foi exercitada nesta pesquisa. [Guia de checksum](https://docs.kraken.com/exchange/guides/websockets/book-checksum-v2).

Há histórico oficial de time-and-sales em CSV/ZIP, atualização trimestral, sete campos incluindo ID de negócio e manifesto. A página atualizada em 2026-09-16 oferece o conjunto completo até 2026-Q2 e incrementais Q1/Q2; não se afirma cobertura Q3 completa. Não baixamos nem validamos os ZIPs, nem encontramos histórico L2 nesta página. [Histórico oficial](https://support.kraken.com/articles/360047543791-downloadable-historical-market-data-time-and-sales-). A FAQ descreve paginação por `since`/cursor; candles de REST limitados a 720 pontos não são um arquivo infinito. [FAQ de API](https://support.kraken.com/articles/advanced-api-faq).

O guia vigente recomenda REST público com frequência de até uma chamada por segundo; Trades/OHLC têm limites por IP/par, outros por IP. Os dois GETs exploratórios abaixo não mediram quotas sustentadas. [Limites](https://support.kraken.com/articles/206548367-what-are-the-api-rate-limits-).

Kraken tem canal L3, mas exige token autenticado e exclui liquidez oculta/ordens ainda não visíveis. Não foi criado token nem inferida elegibilidade. [Level 3](https://docs.kraken.com/exchange/api-reference/spot-websocket-v2/level3).

### CCXT

A versão declarada no `package.json` fixado é **4.5.85**, commit de 2026-10-06. [Manifesto oficial](https://raw.githubusercontent.com/ccxt/ccxt/ab01bbb1780afa451e8bc017a54fa3f5317ea5b6/package.json). O manual afirma literalmente: “CCXT Pro is a free part of CCXT that adds support for WebSocket streaming:”. Suporte real precisa ser consultado em `exchange.has`; `watchTrades` e `watchOrderBook` não garantem a mesma cobertura em toda exchange. O cache padrão de trades/candles/ordens é limitado a 1000 elementos; `since`/`limit` se aplicam à janela em memória. Normalização pode esconder campos específicos e exige validação de precisão, deduplicação e ressincronização por venue. [Manual Pro](https://docs.ccxt.com/docs/pro-manual), [repositório e licença do software](https://github.com/ccxt/ccxt). Nenhuma biblioteca foi instalada.

## Perpétuos/futuros cripto: candidato condicionado

O catálogo USDⓈ-M atual da Binance documenta `/fapi/v1/premiumIndex` com `markPrice`, `indexPrice`, `lastFundingRate` e `nextFundingTime`; `/fundingRate` para histórico, compartilhando 500 consultas/5 min/IP com fundingInfo; `/depth` para L2; `/trades` para negócios recentes. Peso de depth depende de profundidade (2 para 5–50, 5 para 100, 10 para 500, 20 para 1000), e trades tem peso 5. **Depth exclui RPI**; `aggTrades` agrega fills de mesmo preço/lado em 100 ms e só consulta as últimas 48 h, excluindo negócios ADL/seguro. Não se deve alegar tape completo ou transportar o contrato de resync de spot sem especificar o derivativo. [Catálogo REST oficial](https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data). Evidência literal: “Retail Price Improvement(RPI) orders are not visible and excluded in the response message.”

O endpoint histórico individual `historicalTrades` aparece com cabeçalho API key na documentação; acesso público a alguns endpoints não torna todos anônimos. Essa distinção faz parte do gate, não foi testada. A [página oficial de Mark Price Stream](https://developers.binance.info/en/docs/products/derivatives-trading-usds-futures/websocket-market-streams/Mark-Price-Stream) foi localizada, mas o conteúdo renderizado desta leitura não permite congelar seus detalhes de cadência; permanecem pendentes a documentação WS exata e sua verificação.

Kraken Futures documenta stream público `book`, inscrição por `product_ids`, snapshot e atualizações com `seq`, `timestamp`, lado, preço e quantidade; os schemas spot e futures são diferentes. Não houve conexão a futures nem validação de regras de gap. [Book Futures](https://docs.kraken.com/exchange/api-reference/futures-websocket/book).

Proposta de dados extras antes de comparar alavancagem: contrato/instrumento e tipo de margem; multiplier/tick/lot/min-notional; limites de exposição e tiers; margem inicial e manutenção; saldo disponível; regra de preço de liquidação e possível ADL; preço spot, trade, mark e index separados; funding realizado e agenda; taxas, spread, slippage, liquidação e regras de collateral. Não supor funding fixo a cada oito horas, nem preço mark igual à última negociação. Esses são campos necessários ao modelo determinístico, não preenchidos nesta investigação. Acesso geográfico, entidade contratual, legalidade do produto no Brasil e licença de dados ficam **não comprovados**.

## Esportes: acesso e qualidade

### Betfair Exchange

O artigo de suporte atualizado em **2026-08-05** registra literalmente: “we are no longer providing Personal Direct API access to Brazilian customers.” Relaciona mudanças de 2025, controles geográficos/autenticação e software de fornecedores aprovados. Essa lista não concede ao Jeve permissão de exportação, redistribuição ou integração própria. [Restrição direta no Brasil](https://support.developer.betfair.com/hc/en-us/articles/17814508363804-Brazil-Direct-API-Access-Not-Available).

Betfair Brasil apresenta produto Exchange e operador local; isso não revoga o gate específico da API pessoal. Não substituir Exchange por Sportsbook na análise. [Informações regulatórias Betfair Brasil](https://www.betfair.bet.br/aboutUs/Regulatory.Information/), [lista oficial de operadores](https://www.gov.br/fazenda/pt-br/composicao/orgaos/secretaria-de-premios-e-apostas/lista-de-empresas/empresas-autorizadas).

O suporte atualizado em **2026-09-12** informa ativação Live de **£499, uma vez, não reembolsável**, destinada a apostas com conta elegível/aprovada/fundada, e proíbe Live usado somente para leitura. Delayed é a chave de desenvolvimento conforme elegibilidade. Pagar £499 não resolve a restrição brasileira nem permite usar Live apenas como feed de observador. [Custos e acesso](https://support.developer.betfair.com/hc/en-us/articles/115003864531-Are-there-any-costs-associated-with-API-access). Evidência literal: “Read-only access to the Live API is not permitted.”

O delayed de stream reúne alterações dos três minutos anteriores e envia uma mensagem a cada três minutos. O delayed de snapshot tem atraso variável de 1–180 s, conforme outro artigo; não confundir as duas modalidades. Delayed pode acessar produção e não constitui sandbox de dinheiro virtual. [Stream e delayed](https://support.developer.betfair.com/hc/en-us/articles/115003887871-How-do-I-get-access-to-the-Stream-API), [quando usar cada chave](https://support.developer.betfair.com/hc/en-us/articles/360009638032-When-should-I-use-the-Delayed-or-Live-Application-Key).

Exchange Stream é socket TLS com JSON delimitado por CRLF, não WebSocket. Market stream e order stream são separados. O schema público documenta atb/atl (preço/tamanho disponível), trd (volume negociado por preço), seleção/handicap, `pt`, `initialClk`/`clk`, imagens, deltas de retomada, heartbeat e conflation. Uma ladder de volume negociado não fornece ID/identidade de cada fill público nem equivalência com agressão de futuros. Valores numéricos exigem parser decimal. Retomada e filtros precisam ser preservados; cursor inválido deve levar a nova imagem e perda de continuidade visível. [Documentação oficial](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687396/Exchange%2BStream%2BAPI), [schema oficial fixado](https://raw.githubusercontent.com/betfair/stream-api-sample-code/c7b6106d5348bc0d7a32933ce675b54473d9f523/ESASwaggerSchema.json).

Há pacotes históricos Basic/Advanced/Pro. A página de setembro de 2026 aponta especificações, mas preços e conteúdo da tabela/PDF não foram confirmados visualmente nesta pesquisa; não congelar custos, resolução nem profundidade por tier. [Pacotes históricos](https://support.developer.betfair.com/hc/en-us/articles/360002423271-Where-can-I-view-the-data-specification-for-each-historical-data-package). O programa de vendors menciona requisitos específicos para Brasil; ausência de autorização escrita/contrato de uma interface de exportação é lacuna. [Requisitos de vendors](https://developer.betfair.com/vendor-program/product-requirements/).

### The Odds API

Plano gratuito atual: **500 créditos/mês**, sem histórico; primeiro plano pago: **US$30/mês, 20.000 créditos**, com histórico. Acesso requer API key, não criada. [Planos](https://the-odds-api.com/). REST disponibiliza eventos, bookmakers, mercados, odds e atualização; mercados de lay de exchange existem onde cobertos, mas o schema revisado não oferece tamanhos de ofertas, profundidade ou negócios individuais. Custo ordinário: mercados × regiões; histórico: 10 × mercados × regiões. Histórico desde junho de 2020: snapshots de dez minutos, passando a cinco em setembro de 2022, e cobertura inicia quando bookmaker/mercado foi incluído. É histórico de snapshots, não continuidade do livro. [Documentação v4](https://the-odds-api.com/liveapi/guides/v4/).

Intervalos publicados: mercados principais 60 s antes/40 s durante evento; exchanges 20 s antes/10 s durante. Isso descreve atualização do fornecedor, não latência ponta a ponta garantida. [Intervalos](https://the-odds-api.com/sports-odds-data/update-intervals.html). Cálculo local: para uma região/mercado, 500 consultas custeadas permitem 500 minutos por mês em polling de 1 min, ou aproximadamente 83 min em polling de 10 s; respostas sem eventos têm exceções de custo documentadas. Gratuito não sustenta vigilância contínua nesses intervalos.

Termos permitem armazenamento, análise e aplicações comerciais, mas proíbem redistribuir/vender raw data como feed concorrente/API/arquivo. Contrato precisa ser lido antes de construir exportação ou produto público. Dados de odds não autorizam operar uma casa/exchange. [Termos](https://the-odds-api.com/terms-and-conditions.html).

### API-Football

Plano gratuito de **100 requisições/dia**, temporadas limitadas; fixtures, estatísticas, odds e predictions são endpoints listados. Plano Pro anunciado: US$19/mês, 7500/dia. [Preços](https://www.api-football.com/pricing). Guia oficial de março de 2026 descreve fixtures com polling de 15–60 s, estatísticas em torno de 1 min e live odds atualizadas em 5–60 s; live odds não são arquivadas, e cobertura de estatísticas varia por competição. Esses valores não prometem frescor universal nem book/tape. Cem requisições não cobrem sequer uma consulta por minuto durante o dia todo. Predictions do fornecedor são estimativas com metodologia/calibração ainda não examinadas. [Guia oficial](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide). Preços/guia foram legíveis via navegação web; a tentativa de captura HTTP direta retornou 403, separada no manifesto.

## Risco, probabilidade e seleção de mercado

| Mercado | Mecanismo a modelar | Dados disponíveis nesta pesquisa | Classificação proposta |
|---|---|---|---|
| Cripto spot sem empréstimo | Compra integral do ativo, sem exposição emprestada embutida | L2/trades e arquivos | Referência de infraestrutura; não candidato final alavancado por facilidade da API |
| Cripto perp/futures | Exposição por margem, funding e liquidação | Contratos REST e book Futures documentados; sem teste live | Candidato técnico condicional; nenhum teto/lote ou acesso brasileiro confirmado |
| Exchange esportiva | Payoff assimétrico back/lay e responsabilidade, liquidez e regra de liquidação do evento | Contrato de book/volume documentado; acesso pessoal brasileiro bloqueado | Pesquisa de produto/vendor permitido antes de coleta própria |
| Odds/estatísticas REST | Informação para hipóteses/calibração, sem mecanismo de financiamento próprio | Fornecedores documentados, sem chave/teste | Contexto esportivo; não substitui venue executável ou prova edge |

Lay: para stake `s` e odd decimal `o`, responsabilidade `L = s × (o−1)`, ganho bruto quando seleção perde `s`, perda quando vence `L`. A relação entre stake e responsabilidade precisa aparecer na UI/modelo; stake não é perda máxima. [Definição oficial de lay](https://support.betfair.com/app/answers/detail/417-exchange-what-does-the-term-lay-mean-and-what-is-a-lay-bet/). Comissão incide conforme o resultado líquido do mercado e regras da conta; não assumir taxa universal de 5%. [Betfair Charges](https://support.betfair.com/app/answers/detail/betfair-charges). Atrasos in-play, suspensão, erro de disponibilidade e ausência de contraparte impedem presumir saída instantânea; cash out não foi modelado como garantido. [Regras gerais](https://support.betfair.com/app/answers/detail/exchange-general-rules), [outage e suspensão](https://support.betfair.com/app/answers/detail/6541-betfair-exchange-outage/).

Derivação local: `1/o` é probabilidade implícita bruta da odd; não é probabilidade estatística calibrada. Normalização de overround é hipótese de distribuição, não demonstração de chances verdadeiras. Para avaliar a meta semanal é necessário histórico causal, custos, liquidez, regras do produto, modelo de resultados validado fora da amostra e risco de ruína. Cada candidato deve conservar **P(meta)=não estimada** até essa evidência. A alavancagem amplifica movimentos adversos; a capacidade mecânica de exposição não estabelece ganho provável. Não há escolha de lotes ou aumento para recuperar prejuízo.

## Teste real delimitado

Foram feitos **quatro GETs públicos anônimos**, timeout de 10 s, sem instalar cliente; respostas ficaram transitórias em memória/saída de ferramenta. Este arquivo guarda somente metadados/schema/hash, sem preços ou payload de mercado. Todos responderam HTTP 200 entre 04:26:08.726 e 04:26:11.680 UTC em 2026-10-09. A localização do IP de saída não foi verificada. Não comprova elegibilidade Brasil, WebSocket, continuidade, latência de evento, licença, SLA ou quotas sustentadas.

| Endpoint | UTC de início → recebimento | RTT local | Contagem/schema observado | Bytes / SHA-256 do corpo |
|---|---|---:|---|---|
| `https://data-api.binance.vision/api/v3/depth?symbol=BTCUSDT&limit=5` | 04:26:08.726 → 04:26:10.005 | 1276 ms | 5 bids/5 asks; lastUpdateId inteiro, preços/quantidades strings | 368 / `ba2cba639a06d896a0f1957bf4cfd6b6e28303e0717414b24f2dc15828aa7546` |
| `https://data-api.binance.vision/api/v3/trades?symbol=BTCUSDT&limit=3` | 04:26:10.005 → 04:26:10.296 | 291 ms | 3 negócios; id/time inteiros; price/qty/quoteQty strings; maker/bestMatch booleanos | 442 / `28c9606c6c351d116dc835300904846edcef182362bbd248f177d5bb000a706d` |
| `https://api.kraken.com/0/public/Depth?pair=XBTUSD&count=5` | 04:26:10.297 → 04:26:10.596 | 300 ms | error=[]; 5 bids/5 asks; [preço string, quantidade string, timestamp inteiro] | 404 / `caf706b826e338fda756f5d0696bde2416b7c2dc60c413b4086771a614585823` |
| `https://api.kraken.com/0/public/Trades?pair=XBTUSD&count=3` | 04:26:10.596 → 04:26:11.680 | 1084 ms | error=[]; 3 negócios; [preço/volume strings, segundos fracionários, lado, tipo, misc, ID]; cursor last string | 270 / `2bd1fb78f8276650313482712527a37f22d45ce9b2f4a335cdb39e22062f8cd3` |

Comparar esses quatro RTTs não demonstra que uma venue é mais rápida. São observações isoladas de GET, incluindo conexão/rede, sem sincronização dos relógios de exchange nem distribuição p50/p95.

## Contratos do projeto e requisitos para a próxima especificação

Foram lidos contratos em `docs/ARCHITECTURE.md` na baseline fixa. A baseline é observador/laboratório; captura manual/COM de Profit e estimativa financeira online ainda possuem limitações explícitas. A seleção de fontes deve respeitar Decimal e schemas locais, distinção entre observado/calculado/inferido, capital manual, ausência de ordens e `full_tape=False` parcial. Confidence/Noul contextual não é probabilidade de lucro. O contrato de snapshot/avaliação deve ser estendido por produto, sem tratar semânticas distintas como WIN.

Requisitos propostos ao integrador, sujeitos à especificação e revisão independente:

- **CS-R01 — procedência e produto:** cada dado deve indicar fonte, venue, produto, instrumento/contrato, moeda/unidade/multiplier, origem/recebimento, timestamp/unidade, cadência contratada, frescor e cobertura. Spot, perp, futures, back/lay e estatísticas não podem ser confundidos.
- **CS-R02 — precisão e tape:** preços, quantidades, dinheiro, funding e comissão conservam decimal exato; trade individual, agregado, volume de candle e volume de ladder têm tipos distintos. Derivação de agressor registra fonte/semântica e não inventa participante.
- **CS-R03 — continuidade:** snapshots/deltas/sequence/cursor/checksum têm adaptador específico. Lacuna, divergência, reconexão e truncamento invalidam as features dependentes; não extrapolar `full_tape=True` de timestamps ordenados ou CRC top-10.
- **CS-R04 — histórico:** capturas e arquivos mantêm checksum, versão, unidade temporal, janela, IDs/cursors e intervalos faltantes. Replay causal não consulta eventos futuros nem soma negócio duplicado. Ausência de livro histórico é visível.
- **CS-R05 — esportes:** identidade de evento, seleção, handicap, mercado, fornecedor/bookmaker, status/suspensão, odd, responsabilidade, volume e regra de liquidação devem ser separados. `implied_probability` não recebe o nome de probabilidade calibrada. Estatística/prediction de terceiro exige método/evidência antes de entrar em estimativa econômica.
- **CS-R06 — risco determinístico:** custos, margens, funding, liquidação, responsabilidade e quantidades permanecem locais; JEV só explica/contextualiza. Compare não participar (`q=0`) às exposições admissíveis após gates. Meta 10× não autoriza aumentar exposição nem afirmar chance de lucro.
- **CS-R07 — autorização e licença:** a leitura pública de um endpoint não habilita ordens ou confirma acesso local. Cada fonte declara necessidade de chave, custo, quota, restrição geográfica e licença de armazenamento/redistribuição; desconhecido permanece desconhecido.

Não objetivos: implementar ou ativar coletores nesta rodada; criar contas/chaves; contratar dados; operar/apostar; scraping autenticado ou bypass geográfico; publicação de dados; promessa de alcançar 10×; um livro universal completo; tratar OSS como licença de feed; certificar operação de derivativos offshore.

## Aceitação independente proposta e sequência elegível

Critérios de pesquisa já preservados: fontes primárias, hashes, limites honestos, separação documentação/teste, sem ordem ou conta. Critérios futuros abaixo **não foram executados nem aprovados pelo próprio autor**; não enfraquecem os invariantes do projeto.

1. Revisor independente confirma os trechos/hash/versão e o mapeamento do schema de um instrumento spot; dados pessoais e payload sem licença ficam fora do repositório. Faz sentido congelar o contrato antes de escrever adapter.
2. Para collector futuro, exercitar duplicação, reorder, gap, quantidade zero, precisão fracionária, checksum inválido e snapshot truncado. Cada caso deve gerar estado inválido/frescura/cobertura observáveis e nenhuma decisão financeira com continuidade inventada.
3. Live futuro exige amostra de recebimento prolongada com uma reconexão real, relógios/uncerteza documentados, contagens, perdas, p50/p95 de frescor e recuperação; 30 minutos é proposta mínima de ensaio, não certificação de desempenho. Cadência documental não pode passar como medição.
4. Replay futuro testa fronteira de unidade ms→µs do arquivo Binance, paginação/IDs e faltas. Volume at price soma quantidades de negócios individuais únicos e reconcilia com fonte, sem incluir delta de oferta como negócio.
5. Mercado alavancado só entra na avaliação econômica depois de contrato do produto e custos/margem/liquidação vigentes, gate brasileiro específico e método causal independente. P(meta) permanece não estimada enquanto não houver validação fora da amostra; JEV confidence não satisfaz esse aceite.
6. Esportes só entram como book/tape quando fornecedor permitir acesso/exportação e o schema efetivamente contiver esses dados; odds REST ficam no tipo correspondente. Revisão de quota e termos é pré-condição ao uso contínuo.

Próximas tarefas pequenas: (A) especificar adaptador nativo Binance Spot de um instrumento para laboratório/referência, preservando interfaces do projeto; (B) especificar paralelo de dados perp/Futures com mark/index/funding e gates, sem assumir operação; (C) especificar catálogo esportivo de identidade/odds/estatística e probabilidade implícita, usando só documentação enquanto não houver acesso autorizado; (D) pesquisar opção Betfair vendor/contrato que permita coleta brasileira e exportação, sem contato externo não autorizado; (E) comparar Kraken e eventual CCXT depois de verificar o contrato nativo. Não criar backlog de código `ready` a partir da simples presença deste relatório.

## Consultas JEV e limites da recomendação

A skill Classify Decision foi aplicada com contexto mínimo sanitizado, sem transcript e sem estado privado. A primeira consulta de método absteve-se (confiança 0,29); foi usada a sequência reversível de leitura de contratos e documentação, já autorizada. Recibo `40598121-1db2-4002-ad4e-27c7bcdb3e45`, digest `da611699ac048c3543455d83b8726ec6e2ace115fc1e0588bca48dd38d40f0dc`.

Lote `mode=evaluate` posterior, recibo persistido `fdcb2e74-015f-47fc-9266-ffdbbae5ca1a`, digest `7d1effded20f7d381b9dfdc0e88495d157d6f335bcd71dd7a186f6c57d852dba`, modelo `jev-1.13.0`, rubric `batch-2026-09-26.2`: escolha entre Binance nativo/Kraken nativo/CCXT primeiro recomendou **Binance Spot nativo** (probabilidade da escolha 0,82, confiança 0,76); escolha esportiva entre catálogo de odds/estatísticas, investigação de vendor ou adiar esporte recomendou **catálogo de odds/estatísticas** (0,87, confiança 0,83). Critérios eram adequação técnica e acesso, não lucro; números não são probabilidades de sucesso financeiro. Recibo não autoriza implementação, operação nem gasto de dados.

Essa consulta ocorreu antes do steering que enfatizou alavancagem; sua recomendação continua útil para infraestrutura, mas não seleciona o candidato financeiro final. O steering humano prevalece. Não se reutiliza o recibo como recomendação de que spot atende a meta. Usage registrado: 960 tokens de entrada/131 de saída; custo faturado desconhecido/null, não zero. A configuração local conservadora e o nome do modelo não demonstram calibração no projeto.

Lacunas centrais: nenhuma sessão WS ou derivações VAP foi testada; não há histórico L2 verificado; direitos de redistribuição das exchanges ainda não estabelecidos; localização de egress/eligibilidade Brasil não testada; termos de API-Football pendentes; preços e schemas finais de histórico Betfair não congelados; interface real de vendor para Jeve não encontrada; produto/permissão brasileira e custos de derivativos não provados; nenhuma probabilidade econômica calibrada nem P(meta).

## Manifesto de fontes e hashes

Hashes SHA-256 abaixo são dos **bytes do corpo da resposta HTTP**, sem armazenar corpos de mercado/documentos no repo. Capturas S01–S18 entre 2026-10-09T04:25:40.762Z e 04:25:41.960Z; S19–S21 em torno de 04:27:27.841Z; S23–S24 04:31:30.602Z/04:31:31.051Z. HTML dinâmico pode mudar ao refazer GET; hashes de commits GitHub fixos são reproduzíveis. Um hash de 403 identifica a página de erro, **não a evidência documental** legível via navegador.

| ID | URL/captura | HTTP / bytes | SHA-256 |
|---|---|---|---|
| S01 | [Binance WS, commit e556feb](https://raw.githubusercontent.com/binance/binance-spot-api-docs/e556feb906511189fc423e3b58c0452366e802d3/web-socket-streams.md) | 200 / 22958 | `32bf73a0bed3b75e3ca981fdbaf48c53544bbdfb5944ef8ed1c4d7af9aceba0a` |
| S02 | [Binance archive, commit bd110bb](https://raw.githubusercontent.com/binance/binance-public-data/bd110bb04caad6ad964a0098809f18343b1e104b/README.md) | 200 / 5282 | `2e133d9945a9263a02781369078e72805eff074680f305cd5460016471c6caad` |
| S03 | [CCXT package, commit ab01bbb](https://raw.githubusercontent.com/ccxt/ccxt/ab01bbb1780afa451e8bc017a54fa3f5317ea5b6/package.json) | 200 / 26876 | `cc12a281b6577d467ca87c4ef01d35cb62b6c0803f7830e564b534829975fa05` |
| S04 | [Betfair schema, commit c7b6106](https://raw.githubusercontent.com/betfair/stream-api-sample-code/c7b6106d5348bc0d7a32933ce675b54473d9f523/ESASwaggerSchema.json) | 200 / 37399 | `01fd4b33ca8e4dcd269bc6b605528b128d39edd3875098d925090b03a9230adb` |
| S05 | [Kraken book v2](https://docs.kraken.com/exchange/api-reference/spot-websocket-v2/book) | 200 / 793891 | `9f4e60e9f9147c2afed4e4c6095f0027703c75a3891f92f8c5e4da24c00993d6` |
| S06 | [Kraken trade v2](https://docs.kraken.com/exchange/api-reference/spot-websocket-v2/trade) | 200 / 661519 | `dfafae4c27efa65bdf4873ea24634767a7e6a8722a28310a8599f7341515e14c` |
| S07 | [Kraken checksum](https://docs.kraken.com/exchange/guides/websockets/book-checksum-v2) | 200 / 495752 | `2ac8552559ab65c8969d035b1cef3abef65d60f8a479eae14ee45d6233a41c31` |
| S08 | [Kraken history](https://support.kraken.com/articles/360047543791-downloadable-historical-market-data-time-and-sales-) | 200 / 994050 | `7b03acfab26a2cbb8400b8626cad007ac11325c633b41d7291f45becd8f4d6d7` |
| S09 | [Kraken limits](https://support.kraken.com/articles/206548367-what-are-the-api-rate-limits-) | 200 / 995105 | `0949046505f68c160bcada26a12b8c3f88ceb2de5388024ecb7516b8e16e5ea8` |
| S10 | [Betfair Brasil Direct](https://support.developer.betfair.com/hc/en-us/articles/17814508363804-Brazil-Direct-API-Access-Not-Available) | 200 / 24857 | `2eda4fef3ffa3fa867af045982570dc3fbe86d7a6ff5f03e6536749fad04d63b` |
| S11 | [Betfair API fee](https://support.developer.betfair.com/hc/en-us/articles/115003864531-Are-there-any-costs-associated-with-API-access) | 200 / 21760 | `5d13f8ed6893e9ec8ca960d2ea4b4760af8fe0a893696d19a526bd9d6e4b3f7f` |
| S12 | [Betfair stream access](https://support.developer.betfair.com/hc/en-us/articles/115003887871-How-do-I-get-access-to-the-Stream-API) | 200 / 22232 | `dc9857690ed6a6ebc254012f24f7074c9b161b871549a614c661c433a09d622b` |
| S13 | [Betfair historical packages](https://support.developer.betfair.com/hc/en-us/articles/360002423271-Where-can-I-view-the-data-specification-for-each-historical-data-package) | 200 / 21977 | `6d328442cecede27f5cb00714a63c654f3ac3cb0f35f163c7249c78843dd1448` |
| S14 | [The Odds API plans](https://the-odds-api.com/) | 200 / 34534 | `e20f5b3cf5e41e1eda28e130b1beaf651fad7d26f309624f53cdae2ad052a54c` |
| S15 | [The Odds API v4](https://the-odds-api.com/liveapi/guides/v4/) | 200 / 325540 | `79126de8feb81cbf4934e167747446e6949df34acc57ea44c55b57b766bb9ae8` |
| S16 | [The Odds API intervals](https://the-odds-api.com/sports-odds-data/update-intervals.html) | 200 / 14865 | `bb9290054870151923b911b9b1043d2f5eaee960007d4533d3c62925d41975e1` |
| S17 | [The Odds API terms](https://the-odds-api.com/terms-and-conditions.html) | 200 / 19458 | `42e14c204def47d6b7f0aa6f0f4f0a93365f190bc56f3ee0b9d5d342a85f0161` |
| S18 | [Betfair vendors](https://developer.betfair.com/vendor-program/product-requirements/) | 403 / 3285 — erro | `ec19917fb5009897e3b2476223065aa21ca4bf240ce82ca5f1442dc027e0e3a7` |
| S19 | [CCXT Pro manual](https://docs.ccxt.com/docs/pro-manual) | 200 / 1949049 | `e20783cd4657683e84b3817d1c099d58c065dd6c9c9eac73447a6e32d3bd0d40` |
| S20 | [API-Football plans](https://www.api-football.com/pricing) | 403 / 5453 — erro | `bbf45dc2b237d7237ef2ca9f8081b73ceaf4e8154b080d45b8b884a070413779` |
| S21 | [API-Football guide](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide) | 403 / 5742 — erro | `d6e1369c69f4568309e1b89e173c669a44c4081d2cf40b463538ced1a9f02878` |
| S23 | [Binance Futures REST](https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data) | 200 / 1557062 | `a225c052c1b192902ad5e2d983541e469026b7dbad8ba0b0e96775a0b1169eab` |
| S24 | [Kraken Futures book, final URL](https://docs.kraken.com/exchange/api-reference/futures-websocket/book) | 200 / 539962 | `efd5b1ea001beaba9fc042b84c29eabfb9f0e3335b3b4f64749bceb9da7ce7f0` |

Fontes complementares citadas sem captura/hash HTTP próprio (limitação explícita): FAQ Kraken, L3, Betfair stream docs/renderização, regulatório Brasil, chaves delayed/live, charges/lay/regras/outage, manifesto README CCXT, Mark Price WS. O conteúdo dessas páginas foi lido via ferramenta web, exceto Mark Price WS com renderização insuficiente.

Hashes dos bytes de blobs Git na baseline, calculados localmente por `git show` sem normalizar linhas: `AGENTS.md`, 3323 bytes, `65ff3937f04f44714517aa769fd64cb69b4242beb659ba8430ddbc16f59f8a95`; `docs/ARCHITECTURE.md`, 13004 bytes, `bdf2aed8ad163c5380edacac63275e9d475f391d86f1c4ca79c648c8f0d8cebe`; `app/decision_engine.py`, 13068 bytes, `809a3010b398a9fb685fe32fb8c4ec6cf1d78af564a144e0fa62e389cbfde450`. Instruções AGENTS fornecidas nesta conversa prevalecem sobre o blob histórico.

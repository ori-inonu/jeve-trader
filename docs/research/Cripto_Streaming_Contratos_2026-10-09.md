# Cripto: contratos públicos de streaming para Jeve Trader

Pesquisa documental em 2026-10-09. Ticket: `02-dados-cripto`. Estado: evidência para decisão e especificação; implementação, streaming ao vivo e revisão independente não realizados. Não foram criadas contas, usadas chaves, consultadas APIs autenticadas ou enviadas ordens. As requisições HTTP realizadas buscaram documentação.

## Resultado para a decisão

Binance Spot e Coinbase Advanced Trade documentam acesso público a negócios e livro. A Binance fornece domínios exclusivos de market data sem autenticação. A Coinbase separa o WebSocket público do canal privado de ordens. Isso permite investigar um observador cripto independente do Profit Pro; não demonstra permissão de negociação, condições de conta, redistribuição dos dados ou elegibilidade de um produto no Brasil. Esses pontos permanecem **não verificados**. [B5] [C1] [C2]

A integração deve conservar contratos por provedor e instrumento, mesmo com uma representação comum para a interface e o JEV. Há duas lacunas documentais que precisam permanecer abertas na especificação: escopo da sequência Coinbase e limite de ligação snapshot/evento Binance. Nenhuma recomendação deste relatório autoriza derivativos ou execução financeira.

## Contratos que não podem ser normalizados sem preservar origem

| Aspecto | Binance Spot | Coinbase Advanced Trade público |
|---|---|---|
| Negócios | `@trade`: individual, ID `t`. `@aggTrade`: agregação por taker, ID `a`, limites `f/l`. `m` identifica comprador maker. [B1] | `market_trades` envia lotes de 250 ms com negócios individuais e `trade_id`. `side` é o lado maker. Agrupar mensagens não equivale a agregar negócios. [C4] |
| Melhor oferta, L1 | `@bookTicker`: bid/ask e quantidades. [B1] | `ticker` inclui bid/ask e tamanhos, mas é acionado por negócios; não promete atualização a cada mudança do livro. Para derivar BBO contínuo, avaliar `level2`. [C5] |
| Livro, L2 | `@depth5/10/20`: parcial; `@depth`: atualizações com `U/u`. Snapshot REST limitado a 5.000 níveis por lado. [B1] [B2] | Assinatura `level2`, envelope recebido `l2_data`; eventos snapshot/update com preço, lado e `new_quantity` absoluto. Zero remove o nível. Livro agregado por preço, sem identidade de cada ordem. [C3] |
| Identidade | Descobrir `baseAsset`, `quoteAsset`, status e filtros em `exchangeInfo`. [B2] | Descobrir IDs base/quote, tipo, venue, status e aliases. Produtos `-USDC`, exceto `USDT-USDC` e `EURC-USDC`, retornam dados do par `-USD` correspondente. Não contar aliases como liquidez independente. [C8] [C2] |
| Precisão e limites | `PRICE_FILTER.tickSize`, `LOT_SIZE.stepSize`, limites de quantidade e `MIN_NOTIONAL`/`NOTIONAL`; precisão da moeda não substitui filtros. [B3] | `price_increment`, `base_increment`, `quote_increment`, mínimos/máximos base/quote. A descrição de `quote_min_size` não basta para equipará-lo automaticamente ao filtro Binance `MIN_NOTIONAL`. [C8] |

**Implicação proposta:** preservar `venue`, `instrument_type`, produto canônico e ID original, base/quote, significado de quantidade, ID de negócio e agregação, lado original e sua semântica. Inversão maker → agressor deve ser calculada deterministicamente pelo adaptador, jamais inferida pelo JEV. Livros de venues distintos continuam separados. Isso é uma proposta de modelagem, não um contrato já implementado.

## Continuidade, reconexão e limites

**Binance.** Abrir e bufferizar `@depth`, obter snapshot, descartar eventos antigos e aplicar quantidades absolutas; `U > local_id + 1` obriga descartar o livro e reconstruir. Níveis fora do snapshot inicial ficam desconhecidos até mudarem. Conexões duram 24 h; ping a cada 20 s, pong com o mesmo payload, prazo de 1 min; `serverShutdown` pede nova conexão. Limites: 5 mensagens recebidas/s, incluindo ping/pong/controle; 1.024 streams/conexão; 300 tentativas/5 min/IP. Esses limites não são a taxa de negócios entregues. [B1]

REST Binance tem pesos por rota e limites por IP: ler `rateLimits` e cabeçalhos `X-MBX-USED-WEIGHT-*`, respeitar `Retry-After` em 429/418. Repetição de excesso pode gerar banimento. Snapshot de 1.001–5.000 níveis custa peso 250. `trades` recupera até 1.000 recentes; `aggTrades` aceita `fromId` inclusivo e até 1.000 agregados. Esses endpoints não provam recuperação ilimitada do tape individual. [B2]

**Coinbase.** Assinar em até 5 s. O feed público permite mensagens sem JWT; o endpoint de dados de usuário exige autenticação. [C1] A maioria dos canais pode fechar após 60–90 s sem atividade; `heartbeats` mantém a conexão. [C2] Heartbeats chegam aproximadamente a cada segundo e têm contador, que ajuda detectar perdas; isso não certifica a completude de negócios ou profundidade. [C6] O limite atual publicado é **8 conexões/s/IP e 8 mensagens não autenticadas/s/IP**; não reutilizar números de documentação antiga. [C7]

`level2` documenta entrega de todas as atualizações, snapshot e atualização absoluta. Essa promessa não dispensa detecção de desconexão, validação de sequência e novo snapshot antes de mostrar livro sincronizado. [C3] O guia recomenda distribuir produtos/canais em conexões para reduzir perdas em carga elevada. [C9] Backoff com jitter, limite de buffer e estados visíveis `conectando → sincronizando → atual → vencido/ressincronizando` são propostas locais a especificar, não garantias de disponibilidade do provedor.

As APIs REST públicas Coinbase usam cache de 1 s; o guia sugere WebSocket para atualização ou `Cache-Control: no-cache` para contornar cache. Não foi estabelecido um limite numérico universal de REST Advanced Trade nesta pesquisa: o futuro adaptador deve verificar o contrato vigente da rota e tratar 429. [C10]

### Duas divergências que exigem prova antes de certificar continuidade

1. **Coinbase: sequência por produto ou conexão.** O overview diz “Sequence numbers are increasing integer values for each product”. [C1] Os schemas atuais de `level2` e `market_trades` dizem “Per-connection message sequence number; use it to detect dropped or out-of-order messages.” [C3] [C4] Em assinatura de vários produtos/canais, validar apenas por produto pode criar lacunas falsas; validar apenas por conexão também pode perder mensagens se o primeiro contrato prevalecer. Registrar ambas as fontes e resolver em captura pública controlada/documentação esclarecida. Um produto/canal por conexão reduz ambiguidade, mas não certifica a semântica ou a recuperação.
2. **Binance: evento inicial.** O tutorial literalmente diz “The first buffered event should now have `lastUpdateId` within its `[U;u]` range.” [B1] Sua regra posterior identifica lacuna apenas quando `U > local_id + 1`. A fronteira `U = snapshot_id + 1` merece um teste de contrato explícito. Não corrigir silenciosamente o texto, descartar uma sequência potencialmente válida ou declarar sincronização apenas pela ordem dos timestamps.

## Taxas, spot e perpetuals

A FAQ Binance separa comissão standard, tax e special, maker/taker, buyer/seller e descontos; seus números são exemplos fictícios. Taxas efetivas dependem de configuração, conta e símbolo. [B4] A Coinbase oferece resumo **autenticado** com maker/taker, tiers, promoções e dimensões de qualificação, incluindo volume e ativos na plataforma; exemplos de schema não são tabela de preço operacional. Não consultado. [C11]

**Requisito proposto:** taxas desconhecidas devem permanecer desconhecidas; não converter ausência em zero nem apresentar lucro líquido sem custos suficientes. Preservar moeda de cobrança, validade, origem e modelo maker/taker. USD, USDT, USDC e BRL não são intercambiáveis automaticamente.

| Dimensão a especificar | Spot | Perpetual, apenas comparação de requisitos |
|---|---|---|
| Quantidade e exposição | Ativo base/quote, incremento e valor nocional por venue. [B3] [C8] | Unidade de contrato, tamanho, moeda de liquidação/colateral, instrumento linear/inverso e fórmula de PnL precisam de contrato próprio; não herdar multiplicador, lote ou margem do WIN. |
| Preço | Negócios, bid/ask e livro identificados pela venue. | Last, índice e mark têm funções distintas; precisam de fontes/idade independentes. O canal Coinbase de perpetual expõe índice, `interest` e timestamp. [C13] |
| Custos/risco | Comissão e slippage com modelo explícito. | Acrescentar funding, períodos, pagamentos efetivos, margem, liquidação e regras de conta. A taxa corrente de um canal não comprova pagamento realizado nem PnL líquido. |
| API | Binance Spot e Advanced Trade spot documentados acima. | Na Coinbase, INTX via Advanced Trade terminou em **01/10/2026**; Global Derivatives usa outro gateway/protocolo JSON-RPC 2.0. Spot permanece em `api.coinbase.com`. Não planejar integração nova de trading em `/intx/*`. [C12] |

Os canais públicos Global Derivatives têm host `wss://streams.drb.coinbase.com/ws/api/v2` e método `public/subscribe`; métodos de consulta e canais privados usam outros contratos/hosts. [C2] O intervalo `raw` do canal de perpetual é reservado a usuários autorizados; modalidades públicas agregadas não equivalem a acesso integral. [C13] **Brasil e elegibilidade de negociação spot/perpetual não verificados.** O quadro não define derivativos como etapa aprovada.

## Requisitos candidatos, exclusões e aceite independente

São propostas para o integrador congelar na SPEC após decisões; não são aceites executados ou aprovados pelo pesquisador. Preservam os contratos locais: `AGENTS.md:32` exige que `full_tape=False` permaneça parcial e dados ausentes/vencidos/inconsistentes sejam visíveis; `AGENTS.md:33` mantém a baseline observador/laboratório. `docs/PRD.md:9` e `docs/ARCHITECTURE.md:85` mantêm finanças com `Decimal`. `docs/PRD.md:49` exclui chamadas autenticadas/ordens apenas para verificar documentação.

| ID | Requisito candidato | Evidência de aceite a cargo de verificador independente |
|---|---|---|
| CR-R1 | Aquisição pública separada de conta e execução; cobertura e origem visíveis. | Inspecionar rotas/credenciais; exercício público limitado posteriormente autorizado mostra estados reais; nenhuma ordem ou conta é requisito de teste. |
| CR-R2 | Especificação por venue/produto; nenhum agregado vira negócio individual ou maker vira agressor sem regra local. | Fixtures distintas preservam trade ID, aggregate ID e limites, moeda/unidade, aliases, lado original; comparar com payload oficial e evidência capturada. |
| CR-R3 | Livro só fica atual após sincronização verificada; perda/disconexão invalida cálculos dependentes. | Casos snapshot antes/depois, duplicata, fora de ordem, lacuna, zero-remove, reentrada e buffer excedido. Incluir fronteira Binance `U=L+1` e captura Coinbase de escopo de sequência. Divergência documental impede afirmar contrato resolvido. |
| CR-R4 | Aritmética decimal e metadados versionados; mínimos/ticks/steps específicos, sem arredondamento silencioso. | Fronteiras acima/abaixo de incremento e mínimo; filtro ausente/modificado bloqueia cálculo que o exige; base/quote diferentes produzem unidades corretas. Teste local não substitui validação de venue. |
| CR-R5 | Gestão de limites e frescor por canal; reconexão não mascara buraco histórico. | Contadores de controle/ping, janela IP, backoff/Retry-After, ausência de evento, relógio do provedor versus recebimento, ressincronização. Heartbeat ativo com livro vencido deve continuar mostrar livro vencido. |
| CR-R6 | JEV recebe resumo com provenance, cobertura, lacunas e idade; não calcula regras financeiras nem valida o próprio feed. | Inspecionar envelope mínimo e decisões locais; recomendação não remove gates. Sem evidência econômica suficiente, probabilidade/lucro permanecem não estimados. |
| CR-R7 | Custos desconhecidos e derivativos não aprovados ficam explícitos. | Taxa `null` nunca gera lucro líquido como se fosse zero; funding aparece só em instrumento/perfil de derivativos deliberadamente especificado; operação no Brasil não é presumida. |

**Exclusões desta pesquisa:** implementação do adaptador/frontend; chave ou conta; publicação/redistribuição; contratação de dados; seleção de exchange por preferência comercial; execução de ordens; autorização de perpetuals; certificação regulatória, de desempenho, latência, qualidade ao vivo ou rentabilidade; declaração de tape/book completo.

**Medições futuras sugeridas:** tempo até snapshot válido; lacunas por canal/produto; idade do último evento; reconexões e ciclos de recuperação; atraso recepção/evento com incerteza de relógio; taxa de descarte/duplicação; carga e perda sob assinatura multiproduto. Sem captura, todas estão **não medidas**.

## Alternativas reais para consulta ao JEV

| Alternativa | Benefício | Custo/condição que a decisão deve avaliar |
|---|---|---|
| A — Primeiro adaptador Binance Spot público | Negócios individuais, agregados opcionais e BBO específico; contrato de reconstrução detalhado. [B1] | Gerenciar snapshot/IDs, rotação de conexão e fronteira documental. Não comprova disponibilidade regional. |
| B — Primeiro adaptador Coinbase Advanced Trade spot | Snapshot/update no mesmo canal L2 e negócios individuais em lotes. [C3] [C4] | Resolver escopo de sequência; preservar alias USD/USDC e cadência de ticker. |
| C — Dois adaptadores spot com contrato comum de qualidade | Comparar fontes mantendo livros independentes; exercita a modelagem multimercado. | Mais esforço de aquisição/replay/operação. Só agregar estatísticas compatíveis; não somar livros como mercado único. |
| D — Primeiro incremento apenas negócios e L1, L2 em incremento posterior | Menor superfície inicial de reconstrução; permite avaliar UX e qualidade do contexto. | Excluir explicitamente inferências que exigem profundidade/filas; L1 não certifica continuidade do tape. |

Critérios de escolha: necessidade real de microestrutura, evidência de qualidade, esforço de recuperação, limite de intervenção manual e metadados necessários à inteligência. Não há vencedor certificado por esta pesquisa. A consulta ao JEV pode receber esta matriz e as lacunas, sem payloads privados, transcrições ou credenciais.

## Manifesto de fontes e evidência literal

Hashes SHA-256 dos bytes HTTP/arquivos lidos em 2026-10-09, sem normalização. Binance está fixada no commit oficial `263ac1aa96556af0b4da824c82a1d8cd9a0edda9`; páginas Coinbase `.md` são mutáveis e o hash identifica exatamente a revisão observada. A recuperação do último lote de fontes terminou em `2026-10-09T04:49:22.359773+00:00`; consultas complementares posteriores ocorreram no mesmo dia. Hash não prova disponibilidade de serviço.

| ID / fonte primária | SHA-256 |
|---|---|
| [B1 — Binance WebSocket Streams][B1] | `32bf73a0bed3b75e3ca981fdbaf48c53544bbdfb5944ef8ed1c4d7af9aceba0a` |
| [B2 — Binance REST API][B2] | `49ea6809243fc7fb426e07f2fe662097736c7bb405bd2da5eef637d715427999` |
| [B3 — Binance Filters][B3] | `4b5a8f0f5d15bcf68fd7ac2059ba6c88da641c06fd7885e642330c5ac8124dd3` |
| [B4 — Binance Commission FAQ][B4] | `580cfa59c9f55adae0d27bf38d2bc7f268ad759fdf054486e356464c30bbd54c` |
| [B5 — Binance Market Data Only][B5] | `57d608507426215c43f11907c07ed693f02725840d9ee4d6630f134de402b6da` |
| [C1 — Coinbase WebSocket Overview][C1] | `c8f7e384762ea598007c08b5e8dc4241c37437ed3c104535f5e0be2124d5b38a` |
| [C2 — Coinbase WebSocket Endpoints][C2] | `747b7f665569c70eac2998da5d1b213977937ef24bfeda9be89d048dbd7404bc` |
| [C3 — Coinbase Level2 AsyncAPI][C3] | `922d778d79c1e4a2338678abb2358c15bb8499aa0368b8ac4bbcf8d95a843213` |
| [C4 — Coinbase Market Trades AsyncAPI][C4] | `c041c23184dfe2c3309985a65a0a9515c570c58600b7f9eee75e9ce01f221771` |
| [C5 — Coinbase Ticker AsyncAPI][C5] | `380ecdddc723b186f4e3f0253c328bcc8a9dc571279b512c360e2c52feb7ea64` |
| [C6 — Coinbase Heartbeats AsyncAPI][C6] | `fd31083d9d6fcd37f87e646ab02817fd2b25d6fe05ecf29059ae0c412deee808` |
| [C7 — Coinbase WebSocket Rate Limits][C7] | `55f4f354c4ddb53a342e176963bfab7b6dd94678b1ecdbbae25a2d8d95149a13` |
| [C8 — Coinbase Get Public Product][C8] | `47571c31b9792b21cb941cce58e49f66250b5078288501d11018c69f955af7cb` |
| [C9 — Coinbase WebSocket Guide][C9] | `a28fe70b935e1f4dfcb8b2ca4e7eb3c6af3592b3ac4c5f6af0c92a025ca08ca6` |
| [C10 — Coinbase REST Overview][C10] | `dd1b270a7c02f55a7a30d52088d0f3ee69ff5e2d02a2a81ffc3733937b763770` |
| [C11 — Coinbase Transaction Summary][C11] | `2c819c6cecfa52e983e7ca968e0682129f1261de17526bd7e0d80db3322f1cd7` |
| [C12 — Coinbase Global Derivatives Migration][C12] | `d946128eeb222b89ec1113da99a33bc11e02e1fe4b6bd80eb106a4ede19a26ac` |
| [C13 — Coinbase Perpetual Stream][C13] | `5ebd55f6c9c2c21771d1003021ec7360aa36299a0c245ea4f06fdcd87e59bb2b` |
| Projeto: `AGENTS.md` | `7805ec279f827c3e7208053ef1a669d06446093fc6fc957d6baec990fca5a799` |
| Projeto: `docs/PRD.md` | `d7ad3ce616f51b3752a90dbf3c0c66cf0852438d343e4f4a722bc09fc38f85bc` |
| Projeto: `docs/ARCHITECTURE.md` | `bdf2aed8ad163c5380edacac63275e9d475f391d86f1c4ca79c648c8f0d8cebe` |
| Projeto: `docs/HANDOFF.md` | `5a7c1ed0ea7057b43f4b651115a487ab0183eced12b4b85da3d1a2cbff2bda1c` |

Trechos literais adicionais para auditoria: B3, `LOT_SIZE`, “quantity % stepSize == 0”; C4, `side`, “The maker's side of the trade.”; C7, “8 per second per IP”; C12, “INTX perpetuals trading through the Advanced Trade API ended”. As duas divergências acima conservam seus próprios trechos e localizadores.

Limitações de acesso documental: `https://help.coinbase.com/en/advanced-trade/trading-and-funding/advanced-trade-fees` retornou `HTTP Error 403: Forbidden`; a pesquisa de taxas usa C11 e não números do help. Dois URLs de documentação Binance Futures retornaram corpo HTTP vazio nesta consulta; nenhum conteúdo vazio foi tratado como evidência. O comparativo de perpetuals usa C2/C12/C13 e requisitos propostos, sem certificar a API de Binance Futures.

[B1]: https://raw.githubusercontent.com/binance/binance-spot-api-docs/263ac1aa96556af0b4da824c82a1d8cd9a0edda9/web-socket-streams.md
[B2]: https://raw.githubusercontent.com/binance/binance-spot-api-docs/263ac1aa96556af0b4da824c82a1d8cd9a0edda9/rest-api.md
[B3]: https://raw.githubusercontent.com/binance/binance-spot-api-docs/263ac1aa96556af0b4da824c82a1d8cd9a0edda9/filters.md
[B4]: https://raw.githubusercontent.com/binance/binance-spot-api-docs/263ac1aa96556af0b4da824c82a1d8cd9a0edda9/faqs/commission_faq.md
[B5]: https://raw.githubusercontent.com/binance/binance-spot-api-docs/263ac1aa96556af0b4da824c82a1d8cd9a0edda9/faqs/market_data_only.md
[C1]: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-overview.md
[C2]: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-endpoints.md
[C3]: https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/websocket/level2.md
[C4]: https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/websocket/market-trades.md
[C5]: https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/websocket/ticker.md
[C6]: https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/websocket/heartbeats.md
[C7]: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-rate-limits.md
[C8]: https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/public/get-public-product.md
[C9]: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/guides/websocket.md
[C10]: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/rest-api.md
[C11]: https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/fees/get-transaction-summary.md
[C12]: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/guides/derivatives/overview.md
[C13]: https://docs.cdp.coinbase.com/api-reference/coinbase-deribit-app-api/websocket/market-data/perpetualinstrument_nameinterval.md

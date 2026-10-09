# Expansão do Jeve Trader — dados e potencial de alavancagem

Investigação de 2026-10-09. Objetivo confirmado por Gabriel: **filtrar mercados com potencial de alavancagem financeira e dados adequados à tomada de decisão**, estudando R$400 → R$4.000 em menos de uma semana. Estado: pesquisa/plano; integração, execução e desempenho financeiro não demonstrados.

## Decisão da pesquisa

Priorizar **futuros B3 e derivativos cripto** para o estudo econômico. Usar **cripto spot público** como primeira base de coleta, livro e replay, pois reduz dependências e permite testar a infraestrutura sem conta. Spot é referência técnica, não cumprimento da meta de alavancagem. **Trading esportivo e binárias ficam pendentes** pelas limitações de acesso e dados encontradas, com condições explícitas para reconsideração.

Não há evidência suficiente para escolher qual mercado tem a maior probabilidade de alcançar 10×: nenhum retorno, taxa de acerto ou risco de ruína do sistema foi medido. A shortlist combina mecanismos de exposição e viabilidade dos dados; não declara rentabilidade superior. Jev Workflows recomendou essa prioridade no recibo `62035197-461c-4c76-8051-864eb7bd2632`; o conselho não autoriza operações. [Direção confirmada](Expansao_Mercados_Direcao_2026-10-09.md), [decisões e recibos](../evidence/expansao-mercados-decisoes-2026-10-09.json).

## O que pode substituir Profit/Excel

| Rota | O que entrega / pode calcular | Acesso e bloqueio | Papel proposto |
|---|---|---|---|
| ProfitDLL Market Data | Negócios com preço, quantidade e agressão; livro por preço e ofertas individuais; VAP calculável dos negócios capturados | DLL Windows, SDK e licença próprios; autenticação e preço total pendentes | Alternativa mais próxima da arquitetura B3 atual; pode dispensar leitura Excel, mantendo dependência comercial de dados |
| B3 UMDF / distribuidor licenciado | Feed de negócios e livro; Binary UMDF documenta MBO e recuperação de estado | Contrato/conexão; uso non-display, histórico e redistribuição precisam ser enquadrados | Investigar API de distribuidor antes de UMDF direto; nenhum feed gratuito integral foi identificado nas fontes consultadas |
| brapi / UP2DATA | Referência e histórico diário/fechamento | brapi documenta exceções WIN/WDO sem token; granularidade diária não resolve o intraday; UP2DATA não é stream | Complemento de catálogo/histórico, sem satisfazer tape/book |
| Binance/Kraken spot públicos | Trades e L2, IDs/seq ou checksum conforme provedor; VAP em janela e agressor conforme contrato | REST/WS públicos; limites e termos; a sondagem REST não valida WS/continuidade/Brasil | Primeiro piloto técnico sem chave; catálogo decimal e replay antes do JEV |
| Binance/Kraken derivativos | Negócios/agregados, L2, preços mark/index e funding conforme venue | Produto, regras de margem e disponibilidade brasileira separados da API pública | Candidato de alavancagem para pesquisa; dados spot não substituem dados do contrato |
| Betfair Exchange | API documenta preços back/lay, quantidades e volumes por seleção; históricos específicos | FAQ oficial confirma API pessoal direta indisponível a clientes brasileiros | Pendente para adapter direto; aplicação comercial aprovada não concede API pessoal ao Jeve |
| Odds API / API-Football | Odds por polling, resultados e estatísticas | Chave, quotas, planos e história/cobertura variáveis | Complemento estatístico; odds/resultados não substituem livro/tape de exchange |
| Deriv / wrappers de IQ Option | Deriv pública oficial oferece ticks/histórico de preços da plataforma; wrapper IQ é comunitário | Sem negócios/volume/book nesses ticks; limites/termos e alertas CVM | Pesquisa comparativa; não integrar como fonte de fluxo de lotes ou rota operacional |

As fontes, rotas, cadências, limites e custos conhecidos de cada linha constam das [notas B3/binárias](Expansao_Mercados_B3_Binarias_2026-10-09.md) e [notas cripto/esportes](Expansao_Mercados_Cripto_Esportes_2026-10-09.md). Campos comerciais não estabelecidos permanecem desconhecidos, sem presumir custo zero. O código aberto do cliente não concede direito ao feed.

Para clientes open source, CCXT/CCXT Pro são opções atuais: o manual oficial descreve Pro como parte gratuita com WebSocket. Isso ajuda a conectar venues, mas cobertura, precisão e recuperação continuam específicas de cada exchange. Para o primeiro perfil, o pesquisador e a consulta delegada favoreceram Binance Spot nativo, mantendo Kraken como alternativa; o par e contrato final ainda serão congelados em EM-01. [Manual oficial CCXT Pro](https://docs.ccxt.com/docs/pro-manual), [limites e recibo nas notas](Expansao_Mercados_Cripto_Esportes_2026-10-09.md).

A Nelogica descreve contratação de ProfitDLL e callbacks de dados; essa rota pode reduzir a dependência da planilha, mas precisa do SDK oficial e licença compatível. O wrapper comunitário não resolve entitlement. [Acesso ProfitDLL](https://ajuda.nelogica.com.br/hc/pt-br/articles/51583791325211-Como-obter-acesso-%C3%A0-ProfitDLL), [funções Real Time](https://ajuda.nelogica.com.br/hc/pt-br/articles/11168755650459-Fun%C3%A7%C3%B5es-Real-Time-DLL).

O protocolo direto da B3 tem recuperação e regras próprias; snapshot de livro não reconstrói todos os negócios perdidos. O manual **Binary UMDF** trata de mensagens binárias de dados B3, não de opções binárias OTC. O enquadramento do consumo pode mudar em 01/11/2026; confirmar política aplicável antes de contratar. [Manual B3 v2.3.1.1](https://www.b3.com.br/data/files/F6/82/B3/0F/F2A30A105BF9020AAC094EA8/BinaryUMDF-MessageSpecificationGuidelines-v.2.3.1.1-enUS.pdf), [política e contratos](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/distribuidores/politica-comercial-e-contratos/).

## Dados necessários para as decisões

Para **entrada de lotes e volume por preço**, precisamos de negócios executados com preço, quantidade, tempo e identidade suficiente para deduplicação/recuperação. Para **livro**, precisamos de snapshot e deltas conciliáveis, com limites de profundidade e cobertura. Mudança de oferta não é execução; cancelamento não é automaticamente compra ou venda. Agressor é fornecido ou inferido por um contrato declarado, e fica desconhecido quando não houver base.

“Todos os dados” precisa de recorte: venue, contrato, canal, profundidade e janela. Um L2 público não mostra ordens ocultas ou fluxo de outras bolsas; o tape de uma corretora/plataforma não é automaticamente mercado consolidado. No cripto, dados spot e perp são mercados distintos. Binance Futures documenta filtros como exclusão de RPI em depth e agregação de fills no stream agregado; a cobertura não pode ser ampliada por normalização. [Dados de mercado Futures](https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data).

Para **probabilidades**, preço/odds não bastam: precisamos de resultados e labels definidos, amostra cronológica, contexto de execução, custos e calibração fora da amostra. Para **alavancagem**, precisamos ainda de payoff/margem/minimos/funding/comissões, liquidez executável, moeda/câmbio e responsabilidade. São conjuntos diferentes; a camada JEV recebe evidência de cada um e as lacunas.

A FAQ Betfair atualizada em 05/08/2026 é explícita sobre a indisponibilidade da API pessoal Brasil. Ter site licenciado ou usar software aprovado não prova direito a API própria, extração ou redistribuição. [FAQ oficial Betfair](https://support.developer.betfair.com/hc/en-us/articles/17814508363804-Brazil-Direct-API-Access-Not-Available).

Ticks Deriv são cotações da plataforma, sem quantidade executada ou book nos schemas consultados. A CVM mantém alertas de ofertas de Deriv/Binary e IQ Option; a situação cadastral/revogação atual precisa de verificação antes de elegibilidade operacional. Isso não é conclusão de proibição universal de qualquer produto binário. [Schema oficial ticks](https://github.com/deriv-com/deriv-api-schemas/blob/54e353807146d31f58291693243cbbf671de7bce/schemas/ticks_response.schema.json), [alerta CVM Deriv/Binary](https://www.gov.br/cvm/pt-br/assuntos/noticias/2023/cvm-alerta-para-atuacao-irregular-de-deriv-com-e-binary.com), [alerta CVM IQ Option](https://www.gov.br/cvm/pt-br/assuntos/noticias/2021/cvm-reforca-alerta-de-atuacao-irregular-da-iq-option-ltd).

No cripto, dados públicos e autorização de operar um produto são gates separados. As regras brasileiras de prestadores mudaram em 2026 e houve alteração em setembro com efeitos em outubro e janeiro/2027. Esta pesquisa não certifica entidade ou derivativo acessível à conta do usuário. [BCB Resolução 520](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=520&tipo=resolu%C3%A7%C3%A3o+bcb), [nota BCB sobre alterações](https://www.bcb.gov.br/detalhenoticia/21267/nota).

## Uso de sites e navegador

Páginas públicas são úteis para documentação, especificações, eventos e referência histórica, conforme termos. Para fluxos granulares, priorizar APIs oficiais: extração da tela é afetada por atualização, amostragem, atraso e identidade incompleta das mensagens. Scraping não torna gratuita uma licença e não contorna autenticação/geografia. Se uma página pública permitida for a única fonte, classificá-la como snapshot parcial, registrar horário de coleta, versão/parser e limitações; não inventar tape, volume ou estatística a partir de pixels.

## Raciocínio financeiro e filtro

R$400 → R$4.000 exige 10× de capital, **900% líquidos**. O crescimento constante equivalente é 58,49% por sessão em cinco sessões, ou 38,95% por dia em sete dias; o prazo solicitado é menor que sete. Multiplicador de exposição torna ganhos e perdas mais sensíveis, não cria vantagem. Não existe neste estudo uma estratégia validada para a meta. [Contas reproduzíveis e protocolo econômico](Expansao_Mercados_Economia_2026-10-09.md).

O filtro proposto segue esta ordem: acesso e cobertura suficientes → produto/payoff/custos admissíveis → estimativa econômica com execução e incerteza → comparação entre candidatos e aguardar. A comparação futura prioriza distribuição do resultado líquido e chance de alcançar o alvo **com risco explícito**, em vez de ranquear somente pela maior alavancagem anunciada. Sem dados suficientes, preservar `P(meta)=desconhecido`.

O relatório econômico detalha futures, spot/perp, payout binário, stake/back e responsabilidade lay, além de custos, calibração e simulação de banca. Capital de R$400 admissível, custos vigentes e orçamento de perda não foram confirmados; contas exemplares do app não os estabelecem.

## Consequência para a arquitetura e tarefas

O código atual tem suposições WIN: quantidade inteira, ponto de R$0,20, conta em BRL e tarifas manuais exemplares. A expansão precisa de catálogo/payoff por família e envelopes decimais, procedência, clocks, IDs/seq, saúde e replay. Excel continua parcial. Cripto fracionário, stake/lay e payoff binário exigem unidades próprias. Fonte local: `app/profit_bridge.py`, `app/profitdll_contract.py`, `app/decision_engine.py` na baseline `da96c6a`, inspecionada em Windows.

O [plano EM-00–12](Expansao_Mercados_Plano_2026-10-09.md) separa fonte, contratos, adapter, replay, contexto JEV, B3, derivativos cripto e avaliação econômica. A [SPEC CM-01–12](../specs/Coleta_Multimercado_2026-10-09.md) define comportamentos e aceites futuros. O próximo incremento pequeno é fixar um contrato de feed público; B3 e derivativos avançam como frentes documentais de alavancagem. Nenhuma tarefa proposta equivale a integração pronta.

Os comentários para escolhas do JEV registrarão alternativa, evidência, frescor/cobertura, custo, risco, lacuna, motivo e próxima verificação capaz de mudar a decisão. Finanças, schemas, permissões e gates ficam determinísticos. Contexto/Choice/confidence não se convertem em probabilidade de lucro.

## Alcance desta entrega

Documentação primária consultada em 2026-10-09; sondagens públicas pequenas sem conta registradas nas notas. Não foram validados WS contínuo, feed B3, conta brasileira, APIs autenticadas, book histórico integral, estratégia, lucro, latência ponta a ponta ou restart. Aplicativo e checkout concorrente preservados: os artefatos vivem em worktree anexado à conversa. Verificação/hashes e parecer independente acompanham a entrega; autorização para pesquisa não foi convertida em operações.

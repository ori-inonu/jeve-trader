# Qualificação pública B3 — WIN/WDO, 2026-10-09

> Publication projection: personal checkout paths and the conversation UUID are omitted. Non-personal task and reviewer role labels are retained as provenance. Acceptance, findings, source hashes and measured results are unchanged. Raw source SHA-256: 372c44b66d683fb7bd6aceb0208f81b3a1b35cfdbe0f36da70666f16a6e68255

## Resultado e limite da conclusão

**CQG WebAPI e UMDF direto possuem documentação pública suficiente para especificar testes offline de contratos de ingestão. Cedro Socket possui oferta pública pertinente e um portal técnico acessível, mas o schema Socket ainda precisa ser examinado. Nenhuma das três rotas possui, neste dossiê, prova suficiente para escolher SKU/licença ou habilitar um feed WIN/WDO.**

O ticket canônico `10-qualificacao-b3.md` permanece aberto. Seu aceite exige cobertura, continuidade, entitlement, uso analítico/non-display, retenção, latência, custo e ambiente de teste do produto efetivamente contratado. Este documento acrescenta pesquisa à fronteira Wayfinder; não resolve o contrato, certifica fornecedor, aprova implementação ou registra resposta humana.

Objetivo observado: reduzir a dependência do Profit na coleta B3 e preparar o copiloto multimercado com evidência verificável. Pesquisa restrita a três rotas já identificadas: Cedro Socket, CQG WebAPI e UMDF direto. Enfoque não foi aprofundada neste incremento; sua evidência anterior permanece preservada. Não houve busca geral, contato comercial, cadastro, compra, credencial, acesso autenticado, chamada JEV, captura de mercado, instalação, ordem, commit ou publicação.

Baseline local: `5f15ab73f4f5adfd3221b9bd5f785c24c9afc496`, checkout isolado `{research_checkout}`. A SPEC vigente mantém B3 bloqueada até qualificação documental e entitlement; retenção/export desconhecidos permitem somente diagnóstico sanitizado. Fonte local: [SPEC de implementação](../specs/Multimercado_Implementacao_2026-10-09.md), requisitos I-02/I-07 e contratos da seção 5.

## Método e significado dos estados

Foram examinadas **seis URLs primárias públicas** neste incremento, sem seguir novos links após esse limite. Documentos anteriores foram reutilizados com seus registros e hashes, explicitamente separados das capturas novas. Não foram baixados protocolos compactados, templates, PCAPs ou amostras de mercado.

- **C — confirmado documentalmente:** a fonte pública identifica o comportamento genérico; não comprova que a conta/SKU terá esse recurso.
- **A — ausente nas páginas examinadas:** não encontramos a informação no corpus delimitado. Não significa que o fornecedor não a possua.
- **NP — não publicado no corpus:** uma condição comercial ou específica do cliente não aparece nas fontes examinadas; necessita documento aplicável.
- **`null`:** preço, medição, entitlement, licença ou resultado não estabelecido. Não significa zero, gratuito ou autorizado.

A lista B3 anterior distingue fornecedores habilitados por segmento, mas não identifica o pacote de um cliente. Cedro e CQG constam na diligência de futuros/câmbio. WIN e WDO são famílias de contratos futuros; o símbolo operacional deve identificar o vencimento e o dialeto da fonte. Essas fontes não bastam para afirmar acesso de uma conta. [Distribuidores licenciados B3](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/distribuidores/distribuidores-licenciados/), [produto WIN](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/futuro-mini-de-ibovespa.htm), [produto WDO](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/moedas/futuro-mini-de-taxa-de-cambio-de-reais-por-dolar-comercial.htm). Registro anterior: S01/S16/S17, em [pesquisa B3 existente](B3_Dados_Independentes_2026-10-09.md).

## Matriz técnica por rota e produto

Os nomes abaixo são produtos/protocolos públicos. **Identificador comercial do SKU contratado = `null` em todas as rotas.** As referências em cada célula sustentam somente a capacidade descrita.

| Aspecto | Cedro — API Socket | CQG — WebAPI | B3 — UMDF direto, FIX/FAST |
|---|---|---|---|
| WIN/WDO por vencimento | C: anúncio B3/BM&F. A: catálogo de vencimentos e cobertura do SKU. [Socket](https://cedrotech.com/market-apis/api-socket/) | C: conectividade B3 anunciada anteriormente. A: entitlement e símbolos WIN/WDO da conta. [CQG/B3](https://www.cqg.com/2025) | C: instrumentos PUMA/segmento BM&F; seleção de canais/instrumentos requer definição efetiva. [UMDF](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-desenvolvedores-e-vendors/fix-fast-umdf/) |
| Metadata e identidade | A: schema de contrato/vencimento nas páginas lidas. Portal técnico existe; conteúdo Socket ainda não examinado. [Portal](https://docs.cedrotech.com/) | C: resolução de símbolo, metadata e alterações de listas; dialeto CQG pode diferir do símbolo B3. [Metadata](https://help.cqg.com/apihelp/Documents/metadata.htm) | C: definição de instrumentos e documento Security Definition Report ligado no hub. Template específico não lido neste ciclo. [UMDF](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-desenvolvedores-e-vendors/fix-fast-umdf/) |
| Quotes/trades/L1/L2 | C: cotação, negócios e livro completo/resumido anunciados. A: campos/profundidade por SKU. [Socket](https://cedrotech.com/market-apis/api-socket/) | C: L1/L2 e histórico de ticks/barras genéricos; nível efetivo pode ser reduzido. [WebAPI](https://help.cqg.com/apihelp/Documents/cqgwebapi.htm), [Subscription](https://help.cqg.com/apihelp/Documents/marketdatasubscription.htm) | C: negócios e livro; hub distingue MBO, MBP e TOB nos exemplos de derivativos. [UMDF](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-desenvolvedores-e-vendors/fix-fast-umdf/) |
| IDs e sequência | A: identidade de trade, sequência, escopo/reset. [Socket](https://cedrotech.com/market-apis/api-socket/), [Portal](https://docs.cedrotech.com/) | C: `contract_id` muda entre sessões; `request_id` correlaciona respostas. A: sequência contígua de negócios WIN/WDO. [Subscription](https://help.cqg.com/apihelp/Documents/marketdatasubscription.htm) | C: `MsgSeqNum` e `RptSeq` têm escopos distintos na versão 2.2.2. [Specification 2.2.2](https://www.b3.com.br/data/files/EC/B1/9A/AD/2E86F910FC0436F9AC094EA8/UMDF_MarketDataSpecification_v2.2.2.pdf), registro anterior S06 |
| Gaps/recovery | A: protocolo versionado de detecção/replay, limites e snapshot. [Portal](https://docs.cedrotech.com/) | C: snapshot, updates fragmentados e collapsing; A: recuperação sem perda garantida de todos os trades. [Subscription](https://help.cqg.com/apihelp/Documents/marketdatasubscription.htm) | C: TCP Replayer intradiário para perdas pequenas; snapshot para perdas grandes/entrada tardia. Replay não cruza Sequence Reset. [UMDF](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-desenvolvedores-e-vendors/fix-fast-umdf/), [Specification 2.2.2](https://www.b3.com.br/data/files/EC/B1/9A/AD/2E86F910FC0436F9AC094EA8/UMDF_MarketDataSpecification_v2.2.2.pdf) |
| Entitlement e delay | C: real-time/delay anunciados; NP: pacote e permissões individuais. [Socket](https://cedrotech.com/market-apis/api-socket/) | C: delay e status de acesso dependem do contrato/usuário; ausência de delay não prova acesso concedido. [Subscription](https://help.cqg.com/apihelp/Documents/marketdatasubscription.htm) | C: conexão por co-location/RCB. NP: contrato/canais/entitlement do projeto. [UMDF](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-desenvolvedores-e-vendors/fix-fast-umdf/) |
| Ambiente de teste | C: oferta de teste gratuito por 7 dias, sem escopo WIN/WDO comprovado. Nenhum teste solicitado. [Socket](https://cedrotech.com/market-apis/api-socket/) | C: ambiente totalmente simulado e conformidade obrigatória antes de produção. Não valida B3 real. [WebAPI](https://help.cqg.com/apihelp/Documents/cqgwebapi.htm) | C: exemplos públicos ligados no hub. NP: acesso/entitlement de ambiente de certificação deste projeto. [UMDF](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-desenvolvedores-e-vendors/fix-fast-umdf/) |
| Custo público aplicável | `null`: tabela completa do SKU não examinada/disponível no corpus. [Socket](https://cedrotech.com/market-apis/api-socket/) | `null`: preço completo do cliente/API/B3 não encontrado no corpus. [WebAPI](https://help.cqg.com/apihelp/Documents/cqgwebapi.htm) | `null`: total B3 + infraestrutura/conectividade + operação não estabelecido. Tarifas gerais não são proposta do projeto. [Política comercial 2026](https://www.b3.com.br/data/files/EA/C2/79/58/A73699100A29E189AC094EA8/Politica%20Comercial%20de%20Market%20Data_2026.pdf), registro anterior S04 |

Não usamos ordens ou funcionalidades de trading da WebAPI como requisito. A API financeira genérica não muda o escopo observador do projeto. A existência de transporte streaming também não comprova tape completo.

## Permissões e lacunas comerciais

A política B3 registrada na investigação anterior exige avaliação prévia para desenvolvimento de produtos; distingue uso display, non-display e desenvolvimento. O índice daquele registro identifica políticas até **31/10/2026** e a partir de **01/11/2026**. Antes de um contrato/piloto que atravesse essa data, deve-se identificar qual versão e modalidade se aplicam. Não inferimos licença a partir de assinatura de terminal, demo, anúncio comercial ou acesso técnico. [Política de consumo](https://www.b3.com.br/data/files/66/82/D8/17/973699100A29E189AC094EA8/Politica%20de%20Consumo%20Market%20Data%20B3.pdf), [índice de políticas/contratos](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/distribuidores/politica-comercial-e-contratos/). Fontes reutilizadas S02/S03; não houve nova análise jurídica.

| Documento necessário do SKU | Cedro Socket | CQG WebAPI | UMDF direto |
|---|---|---|---|
| Uso analítico/non-display pelo motor local | NP no corpus; autorização aplicável = `null` | NP no corpus; autorização aplicável = `null` | Modalidades gerais documentadas; enquadramento do projeto = `null` |
| Envio de dados ou features ao JEV/terceiro | NP; destino/conteúdo/permissão = `null` | NP; destino/conteúdo/permissão = `null` | NP para este projeto; avaliação/contrato aplicável = `null` |
| Retenção bruta, logs, replay, features derivadas | NP; prazo e restrições = `null` | NP; prazo e restrições = `null` | NP para a licença do projeto; prazo e restrições = `null` |
| Redistribuição/exportação e número de usuários | NP; permissão = `null` | NP; permissão = `null` | NP para a licença do projeto; permissão = `null` |
| SLA, limites e preço completo com data | NP; latência medida = `null` | NP para WIN/WDO/cliente; latência medida = `null` | NP para implantação do projeto; latência medida = `null` |

O corpus é [Cedro Socket/Portal](https://cedrotech.com/market-apis/api-socket/), [portal Cedro](https://docs.cedrotech.com/), [CQG WebAPI](https://help.cqg.com/apihelp/Documents/cqgwebapi.htm), [UMDF](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-desenvolvedores-e-vendors/fix-fast-umdf/) e as [políticas B3](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/distribuidores/politica-comercial-e-contratos/) reutilizadas. A matriz descreve a falta de documento aplicável nesses materiais; não afirma proibição universal ou autorização implícita.

Consequência local proposta, derivada da SPEC vigente: conservar `retention="unknown"`, `export="unknown"` e `full_tape=False` até prova específica; não gravar nem enviar dados licenciados para demonstrar integração. Features também precisam de enquadramento explícito. Uso de fixtures sintéticas próprias permite testar o software sem pressupor licença de dados reais.

## Caminhos comparáveis e dependências

| Próximo caminho | O que a evidência permite agora | Dependência que impede conexão real | Valor técnico e limite |
|---|---|---|---|
| CQG: especificar contrato offline | Exercitar identidade de sessão, status efetivo, fragmentação e degradação. Documentação genérica pública permite cenários; versão de protocolo do futuro SKU ainda precisa ser fixada. | SKU B3 WIN/WDO, símbolos/metadados efetivos, direitos, credenciais e conformidade. | Menor incerteza de estados publicados; não comprova continuidade completa ou entitlement. |
| Cedro Socket: fechar schema antes de adapter | Registrar checklist de mensagens/campos e próxima leitura delimitada do portal técnico, sem login ou solicitação de trial. | Schema/versionamento Socket, metadados WIN/WDO, IDs/recovery, licença e pacote. | Oferta alinhada a cotação/livro/tape; implementar parser antes do schema seria especulação. |
| UMDF direto: referência de continuidade | Usar escopos de sequência/reset/recovery publicados para especificar fixtures próprias e revisar invariantes genéricas. | Infraestrutura co-location/RCB, contrato, canais, operação/certificação e custo total. | Melhor referência pública de mecanismos de recuperação; dependências operacionais maiores para o Windows atual. |

Esta comparação é uma inferência técnica a partir da matriz, não decisão comercial nem recomendação de investimento. As opções permanecem elegíveis para consulta técnica posterior pelo coordenador. Não houve consulta JEV nesta pesquisa. Cedro exige mais leitura de schema; CQG exige protocolo/entitlement de cliente; UMDF exige infraestrutura antes de provar acesso.

As escolhas não substituem a prioridade do aceite nativo do cockpit ou os gates determinísticos do PR. Os testes abaixo podem ser especificados em paralelo, sem compra de feed. Não existe justificativa documental para inserir um placeholder B3 rotulado live na interface.

## Testes offline possíveis e aceites propostos

**Não executados neste incremento.** São propostas para uma SPEC futura com revisão independente, mantendo I-02 e os contratos existentes. Fixtures devem ser construídas localmente; não copiar PCAPs reais para o repositório sem autorização de retenção/redistribuição.

| ID proposto | Entrada/condição | Resultado observável e evidência | Dependência |
|---|---|---|---|
| B3-QP-01 — ficha do produto | Cada rota selecionada fornece SKU/versão, WIN/WDO por vencimento e pacote efetivo | Matriz sem equivaler família a contrato; campos faltantes continuam `null`; reviewer confere documentos fixados por hash | Documento fornecedor/B3 aplicável; pendente |
| B3-QP-02 — identidade e valores | Fixtures próprias de WIN e WDO com vencimentos distintos, metadata incompleta, preços/quantidades decimais | IDs/metadata não colidem; ausência de campo obrigatório impede `constraints_verified`; nenhum float monetário aceito | Contratos locais já existentes; seleção dos valores reais depende de B3/SKU |
| B3-QP-03 — sessão CQG | Fixture de reconexão com novo `contract_id`, símbolo resolvido novamente e resposta da sessão antiga | Evento antigo não altera workspace atual; epoch/identidade diferenciam sessões | Schema de protocolo futuro fixado; regra documentada de sessão |
| B3-QP-04 — acesso e cobertura | Fixture de nível solicitado diferente do efetivo, delay, acesso negado, collapsing e update dividido | Saúde/capacidade efetivas visíveis; JEV não recebe contexto apresentado como tape completo; `full_tape=False` | Mapeamento de campos CQG fixado; sem dados reais |
| B3-QP-05 — sequência e recovery | Fixture UMDF com gap pequeno, reset, gap grande e snapshot de livro | Domínio afetado invalida; reset abre fronteira; snapshot de livro não reconstitui negócios perdidos; replay fora da janela não restaura cobertura por suposição | Escopos/regras de 2.2.2 como referência, versão implantada futura pendente |
| B3-QP-06 — políticas locais | Retenção/export `unknown` ou `denied`; opção de gravar/avaliar contexto | Só contadores/diagnóstico sanitizado; nenhum payload real gravado/exportado ou enviado ao JEV sob permissão desconhecida | Direitos aplicáveis pendentes; testar por stub/fixture próprios |
| B3-QP-07 — escolha contratual | Documentos e proposta aplicáveis atendem todo o ticket 10 | Revisor independente relaciona cláusulas a uso, custo, teste e cobertura; conflito/falta preserva bloqueio | Autoridade humana para contato/contratação; respostas do fornecedor/B3 |
| B3-QP-08 — piloto observado | Após B3-QP-07 e autorização própria, ingestão somente leitura no candidato Windows com falha/reconexão controladas | Instrumento real, entitlement efetivo, sequência/recovery, frescor e limitações observados; medições sanitizadas por execução | Credenciais/ambiente/licença e candidato nativo; todos pendentes |

As propostas B3-QP-03/04 são ancoradas em [CQG Subscription](https://help.cqg.com/apihelp/Documents/marketdatasubscription.htm); B3-QP-05 usa [UMDF 2.2.2](https://www.b3.com.br/data/files/EC/B1/9A/AD/2E86F910FC0436F9AC094EA8/UMDF_MarketDataSpecification_v2.2.2.pdf). Critérios de invalidação, identidade e política são invariantes locais, não certificações dos fornecedores.

Medição futura sanitizada: hash do candidato/protocolo, versão da fixture, route/SKU, família/vencimento público, run ID, resultado e motivo por gate, número de duplicatas/gaps/retries, tempo monotônico de recovery, idade do evento e intervenções manuais. Não incluir credenciais, conta, ordens, diários privados, tape bruto ou transcrições. Latência/recovery real, preço faturado e ganho de automação atuais = **`null`**. Fixtures aprovam comportamento local; ambiente simulado aprova somente seu escopo; build, entitlement, execução nativa e ganho pareado continuam estados distintos.

## Dependências externas exatas preservadas

1. **Fornecedor:** entregar proposta/SKU com WIN/WDO e vencimentos, campos efetivos, nível/livro, trades/correções, IDs, escopo de sequência, reset, recovery/limites, protocolo versionado e ambiente de teste. Obter uma amostra autorizada somente quando isso tiver autorização própria.
2. **Fornecedor/B3:** esclarecer contrato aplicável para cálculo local, produto, non-display, envio de raw/features ao JEV externo, retenção/replay, logs, exportação e usuários. Identificar a política em vigor na data do piloto, inclusive a fronteira 01/11/2026.
3. **Fornecedor/implantação:** fornecer custo datado completo, tarifas repassadas B3, suporte, conectividade, limites/SLA e requisitos de conformidade; confirmar independência de instalação/login do Profit no pacote escolhido.
4. **Humano autorizado:** decisões que envolvam contato, credenciais, contratação, compra ou ações externas. Este relatório não envia solicitações nem converte conselho técnico em autorização.

Próxima ação independente elegível: coordenador selecionar uma investigação/contrato offline e criar SPEC com os IDs pertinentes. Para Cedro, a próxima leitura deve focar o conteúdo Socket do portal público; para CQG, fixar o protocolo produção e seus comentários sem conectar; para UMDF, fixar templates/definição de canais apenas se a opção direta continuar pertinente. Nenhuma dessas leituras ocorreu além das seis URLs deste incremento.

## Evidência literal curta

Cada excerto aparece uma vez e está abaixo de 25 palavras por fonte. Os campos técnicos da matriz são identificadores funcionais, não cópia de trechos do manual.

| Fonte | Evidência literal | Alcance |
|---|---|---|
| N01 — [Cedro Socket](https://cedrotech.com/market-apis/api-socket/) | “O Market Data Cedro pode ser testado gratuitamente por um período de 7 dias.” | Oferta de teste; não entitlement deste projeto |
| N04 — [Portal Cedro](https://docs.cedrotech.com/) | “Este é o portal para desenvolvedores das APIs Cedro.” | Portal público; conteúdo Socket não examinado |
| N02 — [CQG WebAPI](https://help.cqg.com/apihelp/Documents/cqgwebapi.htm) | “We require a formal conformance test before any API-powered application can connect to our production environment.” | Conformidade antes de produção |
| N05 — [CQG Subscription](https://help.cqg.com/apihelp/Documents/marketdatasubscription.htm) | “contract_id value does not persist between sessions” | Identidade de sessão |
| N06 — [CQG Metadata](https://help.cqg.com/apihelp/Documents/metadata.htm) | “The fields contract_symbol, title, and description are returned in the CQG dialect.” | Dialeto da metadata |
| N03 — [B3 UMDF](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-desenvolvedores-e-vendors/fix-fast-umdf/) | “Esse método de recuperação deve ser usado apenas se poucas mensagens foram perdidas.” | Limite do TCP Replayer |
| S06 anterior — [UMDF 2.2.2](https://www.b3.com.br/data/files/EC/B1/9A/AD/2E86F910FC0436F9AC094EA8/UMDF_MarketDataSpecification_v2.2.2.pdf) | “TCP Replayer is not available for messages prior to a Sequence Reset” | Fronteira de recovery; registro anterior |
| S03 anterior — [Política de consumo](https://www.b3.com.br/data/files/66/82/D8/17/973699100A29E189AC094EA8/Politica%20de%20Consumo%20Market%20Data%20B3.pdf) | “A Licença para o Desenvolvimento de Produtos deverá ser avaliada previamente pela B3” | §6.3, p. impressa 23; registro anterior |

## Proveniência, versões e hashes

Capturas novas: `urllib.request`, resposta HTTP 200, `Accept-Encoding: identity`, SHA256 dos bytes do corpo recebido, sem conversão textual. Timestamp abaixo é o início da requisição; URL final igual à URL solicitada em todos os casos. Corpos públicos não foram persistidos no repositório. O hash de HTML dinâmico identifica somente aquela captura. A diferença do hash N03 em relação ao registro S05 anterior não prova mudança semântica.

| ID | URL literal | Início UTC em 2026-10-09 | Bytes | SHA256 |
|---|---|---|---:|---|
| N01 | https://cedrotech.com/market-apis/api-socket/ | 12:39:31.134017Z | 202929 | `339135245dc42a02f864aa8eebdc8cb796e8f4deb356e6f564a4ada9c61acf4f` |
| N02 | https://help.cqg.com/apihelp/Documents/cqgwebapi.htm | 12:39:31.137237Z | 14098 | `147f188d0516ba200c029cd0009ff2df48c8a7d3d0d6a6913c5b82f26774c1d6` |
| N03 | https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-desenvolvedores-e-vendors/fix-fast-umdf/ | 12:39:31.138707Z | 65810 | `5133d50c6ee55a4826b83e87f7d29dbb1b3d2a08019ab73a675e4204260ea010` |
| N04 | https://docs.cedrotech.com/ | 12:39:31.140138Z | 260775 | `f250b99b7e923a71d2bc01421aab1b43d55677b07798aa9db4d5228b4edfebdf` |
| N05 | https://help.cqg.com/apihelp/Documents/marketdatasubscription.htm | 12:39:31.141401Z | 80733 | `1651f38cd0b09e6d779ac26a0a4bf85c9a322d31a97738e1ef8711840e58df45` |
| N06 | https://help.cqg.com/apihelp/Documents/metadata.htm | 12:39:31.145908Z | 41806 | `0e4bf3ae5f3efade473a05f39cd1555b146c733025170071d5d58572fcbf60ac` |

Versões observadas: N03 liga Messaging Specification/Message Reference **2.2.2**, Security Definition Report **1.0.1** e Release Notes **18/07/2025**. Isso identifica a referência publicada no hub, não a versão futura negociada. N01/N02/N04/N05/N06 não exibem versão comercial aplicável do SKU nos trechos examinados. [Hub UMDF](https://www.b3.com.br/pt_br/solucoes/plataformas/puma-trading-system/para-desenvolvedores-e-vendors/fix-fast-umdf/).

Fontes anteriores reutilizadas; **não recapturadas neste incremento**. Hashes são os da pesquisa B3 existente, com coleta registrada em 2026-10-09 às 04:48:46Z (S01–S06) e 04:48:51Z (S12/S16/S17). Não são provas de permanência futura das condições.

| ID anterior e documento | SHA256 registrado |
|---|---|
| S01 — distribuidores licenciados | `9de3d64dab60203f471bf34b7f3becf73d8f6f8093a2359e0c52e67759981432` |
| S02 — índice políticas/contratos | `67e283090576628dd8595ee45bca3747d0e1d83fe947c4f3f6243205cdc9d790` |
| S03 — política de consumo | `1e56c699070a099945989abd1d4e891f4df6b7f05d25fda5d6552de7c0936285` |
| S04 — política comercial 2026 | `457ec1f22561b59fc7aa97eed21d36268a08fe622e72503c40f85b5c3122b39c` |
| S06 — Messaging Specification 2.2.2 | `e0ef01ecf65d9cb654b2e8f05e53a16dbb916691059b83996b69c1551ed1ecdb` |
| S12 — CQG/B3, página 2025 | `a0d871b7bc125377725e6b878c4c0ab3fa9120be2697446b0835ffba23342347` |
| S16 — WIN | `c8e33c5e6352b6a648b4742a9a14108c8db0c9ebf01cf43dd9c7775122427512` |
| S17 — WDO | `0694b754b2b43517c69d165d9eca3f4ddd29431d1b89ec8417238c424f88f15c` |

Fontes locais lidas, base comum `{research_checkout}/`, HEAD `5f15ab73f4f5adfd3221b9bd5f785c24c9afc496`:

| Caminho relativo à base absoluta acima | SHA256 |
|---|---|
| `AGENTS.md` | `65ff3937f04f44714517aa769fd64cb69b4242beb659ba8430ddbc16f59f8a95` |
| `docs/research/B3_Dados_Independentes_2026-10-09.md` | `ddb756cce3675113639bf366a13fd76f84a6b781dd3bf29c27441cc6c3e819fa` |
| `.scratch/wayfinder-multimercado/issues/10-qualificacao-b3.md` | `dbd8ebfe4727a4cbc6e09898bf3be26ef88a0a3bab9a647d588b6fb9e8f81266` |
| `docs/specs/Multimercado_Implementacao_2026-10-09.md` | `af174497bf764b1a7c67818cee6e3b925a40933d98c40c8e14f5b1b0f6bc01f4` |
| `app/multimarket/contracts.py` | `0341d03ebed624a83f4475d40daf1cf6776a44ff9d6430a5c6598dad0740c899` |
| `app/multimarket/market_state.py` | `1068797c845b2b4089cc3cc9d17305362b4f05100e14f0aa81c75d4a3fe4941a` |

Entrega exclusivamente documental. Ticket contratual não resolvido, feed não habilitado, testes propostos não executados e relatório ainda sujeito à revisão independente do coordenador.

# SPEC draft — copiloto multimercado

Status: draft
Revision: 1
Date: 2026-10-09
Origin: pedido de arquitetura/dados B3/cripto/frontend; [mapa](map.md); [recibo JEV](jev-receipt.json)
Inspected baseline: [HEAD e hashes](baseline.json)
Implementation: não iniciada nesta frente

Esta SPEC converte o objetivo em comportamentos candidatos e cenários de aceite. Recomendações consultivas não encerraram tickets grilling; schemas, parâmetros prospectivos e contrato do primeiro piloto precisam ser definidos antes de qualquer incremento ready. O contrato ready de descoberta refere-se somente à entrega documental.

## Requisitos e cenários

| ID | Origem / comportamento esperado | Aceite futuro | Pendência |
|---|---|---|---|
| MM-01 | Pedido B3 independente + cripto: fonte e instrumento têm identidade/capacidades versionadas, sem pressupostos WIN globais | WIN por vencimento, BTC spot e mesmo símbolo em duas venues não misturam trades/livro/conta; metadata incompatível é rejeitada | [Instrumento](issues/05-identidade-instrumento.md) |
| MM-02 | Invariantes: ingestão conserva origem, clocks, sequência/ID e qualidade por domínio | Duplicata é idempotente; regressão/gap/desconexão invalida livro e dependentes; quote atual não certifica tape completo; recovery segue contrato da fonte; agregado/maker/aliases não viram negócios individuais/agressor/liquidez independente sem regra comprovada | [B3](issues/01-dados-b3.md), [cripto](issues/02-dados-cripto.md), [contratos](issues/11-prontidao-contratos.md) |
| MM-03 | Pedido menos manual: conexão/metadados/reconnect automatizados com estado verificável | Instrumento elegível é descoberto da API; sem metadata válida não se calcula lote; reconnect reconstrói snapshot antes de tornar livro disponível | [Automação](issues/08-automacao-conta.md) |
| MM-04 | Invariantes monetários: risco/custos usam Decimal e regras por família, incluindo q=0 | Tick/step/minimum/currency são respeitados; WIN usa multiplicador próprio; spot admite quantidade fracionária válida; moedas não se somam sem FX verificado; funding/liq não são presumidos para spot | [Instrumento](issues/05-identidade-instrumento.md) |
| MM-05 | Pedido menos manual: conta read-only/importada é conciliada e modo manual explícito | Fill repetido ou fora de ordem não duplica patrimônio; snapshot conflitante mantém conta não conciliada; trading scopes não são solicitados para somente leitura | [Automação](issues/08-automacao-conta.md) |
| MM-06 | Pedido inteligência JEV: perguntas tipadas e scheduler causal, limitado e auditável | Mudança relevante agenda; sem mudança não consulta; backlog é limitado; timeout/abstenção visíveis; consultas pagas não ocorrem em CI/setup; versão exata registrada | [Inteligência](issues/06-inteligencia-jev.md) |
| MM-07 | Invariantes temporais: resposta pertence ao mesmo instrumento/epoch/conta/custos/features | Trocar instrumento durante chamada, receber nova revisão da conta ou reconstruir livro descarta resposta antiga; cache não renova idade da evidência | [Processamento](issues/04-fronteira-processamento.md), [contratos](issues/11-prontidao-contratos.md) |
| MM-08 | Pedido frontend: workspace concentra decisão, saúde e detalhes progressivos | Operador conecta mercado, reconhece falta/gap e localiza motivo de aguardar; troca de workspace preserva isolamento; movimento reduzido/fallback e keyboard funcionam no Windows | [Frontend](issues/07-jornada-frontend.md) |
| MM-09 | Pedido inteligência: registro/replay autorizado torna casos e avaliações reproduzíveis | Replay conserva causalidade, censura/gaps, perguntas/versões e contexto; retenção/exportação respeitam licença; não copiar dataset de mercado para repo | [Inteligência](issues/06-inteligencia-jev.md), [qualificação B3](issues/10-qualificacao-b3.md) |
| MM-10 | Invariantes financeiros: contexto JEV e estimativa calibrada têm gates distintos | Sem modelo aprovado no escopo o painel mostra probabilidade não estimada; taxa/custo ausente não vira zero nem lucro líquido estimado; resultados de WIN não promovem BTC/derivativos; regras/contexto/quantitativo+JEV são comparados temporalmente | [Inteligência](issues/06-inteligencia-jev.md) |
| MM-11 | Continuidade: migração preserva JevWIN, ledger e modos legados | Instalar/migrar/abrir cópia autorizada de dados existentes preserva conteúdo; protocolo versionado rejeita incompatibilidade com diagnóstico; fixtures antigas continuam com cobertura parcial | [Processamento](issues/04-fronteira-processamento.md), [contratos](issues/11-prontidao-contratos.md) |
| MM-12 | Evidência prospectiva: desempenho e redução manual têm baseline e budget anteriores ao código | Medir workload/eventos/s, p95 após recebimento, atraso do mercado, latência JEV, memória/GPU e etapas por jornada; comparar mesmo workload em janela nativa; não transferir teste sintético para live | [Contratos](issues/11-prontidao-contratos.md) |

## Cenários obrigatórios de stress

Conexão aparentemente saudável com buraco de sequência; livro com update atrasado; mudança de tick/step; ticker expirado; troca rápida WIN ↔ cripto com JEV pendente; conta stale com quote fresh; dois fills duplicados após reconnect; relógio local ajustado; burst maior que capacidade da UI; JEV indisponível; provedor restringindo retenção. Cada um deve produzir estado rastreável e impedir dependentes incorretos.

O primeiro piloto também deve resolver a sequência Coinbase por produto/conexão, testar a fronteira Binance `U=L+1` se usar essa fonte e distinguir collapsing/entitlement B3. Não selecionar exchange ou certificar acesso regional apenas pela documentação pública.

## Excluído desta SPEC

Envio de ordens, contratação e publicação, margem/custos inventados, recuperação compulsória de perdas, promoções financeiras por confiança JEV e aprendizagem autônoma na conta real. Derivativos cripto exigem contrato/especificação próprios caso incluídos; não reutilizar silenciosamente modelo de spot ou WIN.

## Critério de promoção

Encerrar decisões técnicas nos tickets e revisar schemas + orçamento prospectivo em [Contratos finais](issues/11-prontidao-contratos.md). Derivar SPEC ready finita para contrato/piloto público sem esperar licença B3; adapter B3 permanece bloqueado até [Qualificação de feed](issues/10-qualificacao-b3.md). Tarefas de implementação e TDD só derivam desse incremento ready, vinculadas aos IDs acima. Este documento não altera PRD/status do código existente.

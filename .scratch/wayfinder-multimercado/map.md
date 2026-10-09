# Jeve Trader — arquitetura multimercado e inteligência verificável

> Publication projection: personal checkout paths and the conversation UUID are omitted. Non-personal task and reviewer role labels are retained as provenance. Acceptance, findings, source hashes and measured results are unchanged. Raw source SHA-256: 28b19d43efed203706b4ac339ccc5b3ac3c39792b043b2bc15a66cf9a61773e9

Label: wayfinder:map
Status: open
Created: 2026-10-09
Tracker: local-markdown
Conversation: [local conversation id omitted]

## Destination

Definir contratos e sequência de evolução para dados B3 independentes do Profit, mercado cripto e cockpit multimercado com menos etapas manuais e inteligência JEV verificável. A saída é uma proposta de arquitetura, uma especificação rastreável e uma fronteira de decisões; implementação e contratação têm gates próprios.

## Notes

Habilidades explicitamente solicitadas: grill-me, grilling, wayfinder, grill-with-docs; domain-modeling fornece vocabulário e contratos. Research investiga fontes primárias em workspaces isolados. Escolhas técnicas, visuais e de fluxo são consultadas ao Jev Workflows em evaluate, com contexto mínimo e recibos; sua recomendação não é resposta humana, autorização externa ou ganho medido.

A sessão inicial de charting resolveu somente pesquisa; recomendações sobre tickets grilling permanecem propostas. Na retomada, Gabriel pediu implementação do contrato finito e depois revisão do PR contra main e continuidade do plano. A pesquisa de evidência seguinte é resolvida documentalmente; a prontidão da nova SPEC recebe revisão independente. Não importar autorização de outros chats. Não contratar feed, cadastrar contas, acessar credenciais, executar ordens ou publicar distribuição. Preservar Tauri/React/Python e alterações preexistentes como baseline até decisão revisada de migração. Ordens automáticas permanecem fora deste mapa.

## Decisions so far

- [Dados B3 sem Profit](issues/01-dados-b3.md): rotas independentes existem; WIN/WDO por SKU, continuidade e processamento externo exigem qualificação/licença. Pesquisa resolvida, integração pendente.
- [Dados cripto](issues/02-dados-cripto.md): contratos públicos documentados; granularidade, lado e sequência não são equivalentes. Divergências e regionalidade precisam de prova no piloto.
- [Arquitetura atual](issues/03-arquitetura-atual.md): snapshot confirma gates Excel, regras WIN/quantidades inteiras e estado global. Migração precisa contratos de instrumento, fonte e conta; código preservado.
- [Evidência para a próxima entrega](issues/12-evidencia-proximo-ciclo-resolution.md): pesquisa concluída com origem de pacote, protocolo Windows e comparador prospectivo; SPEC local ready para instrumentação offline, gates nativos abertos.

- [Schema público Cedro](issues/13-schema-publico-cedro.md): pesquisa concluída; lacunas públicas impedem parser real, qualificação contratual permanece aberta.

O [lote JEV persistido e sanitizado](../../docs/evidence/multimarket-planning-jev.json) recomenda core modular local, identidade tipada por venue/instrumento, scheduler por evidência, cockpit focado na decisão, reconciliação read-only e piloto spot em paralelo à qualificação B3. Essas direções estão na [proposta](architecture-proposal.md), [vocabulário candidato](domain-proposal.md) e [SPEC draft](spec.md); os tickets abaixo conservam alternativas, perguntas de stress e lacunas. Nenhuma recomendação foi tratada como resposta humana ou prontidão de código.

## Tickets e fronteira

O [lote complementar sanitizado](../../docs/evidence/multimarket-planning-jev.json), baseado nos relatórios finais, propõe reaproveitar o isolamento local existente, snapshot visual do workspace selecionado e prioridade por relevância/severidade com aging. Houve abstenção sobre o recorte do piloto cripto: [Sequência dos pilotos](issues/09-sequencia-pilotos.md) conserva a dependência daquela rodada; o incremento posterior escolhe seu piloto pelo contrato finito e novo recibo.

| Ticket | Tipo | Dependências |
|---|---|---|
| [Dados B3 independentes](issues/01-dados-b3.md) | research | nenhuma |
| [Dados cripto públicos](issues/02-dados-cripto.md) | research | nenhuma |
| [Acoplamentos da arquitetura atual](issues/03-arquitetura-atual.md) | research | nenhuma |
| [Fronteira de processamento e migração](issues/04-fronteira-processamento.md) | grilling | Arquitetura atual |
| [Identidade e capacidades do instrumento](issues/05-identidade-instrumento.md) | grilling | B3, cripto, arquitetura atual |
| [Inteligência JEV e validade econômica](issues/06-inteligencia-jev.md) | grilling | Arquitetura atual |
| [Jornada e informação do frontend](issues/07-jornada-frontend.md) | grilling | Arquitetura atual |
| [Automação e reconciliação de conta](issues/08-automacao-conta.md) | grilling | B3, cripto, arquitetura atual |
| [Sequência dos pilotos](issues/09-sequencia-pilotos.md) | grilling | B3, cripto, arquitetura atual |
| [Qualificação de feed B3](issues/10-qualificacao-b3.md) | task | Dados B3 |
| [Contratos finais e prontidão](issues/11-prontidao-contratos.md) | grilling | Seis decisões de arquitetura anteriores |
| [Evidência para próxima entrega](issues/12-evidencia-proximo-ciclo-resolution.md) | research, concluída | contrato finito implementado |
| [Schema público Cedro](issues/13-schema-publico-cedro.md) | research, concluída | dossiê B3 e consulta JEV |

Próxima fronteira de decisão: os seis tickets técnicos, visuais e de fluxo, começando por [Fronteira de processamento e migração](issues/04-fronteira-processamento.md). A qualificação B3 pode avançar em leitura documental; contratação ou acesso privado continuam dependências externas. Esta rodada encerra a descoberta documental, mantendo o mapa aberto.

## Not yet specified

Atualização após o pedido explícito de implementação: o [contrato finito I-01–I-12](../../docs/specs/Multimercado_Implementacao_2026-10-09.md) delimita o incremento executável, com [evidência](../../docs/evidence/multimarket-acceptance.md). Ele não resolve retroativamente tickets HITL nem gates externos. A [resolução da pesquisa de evidência](issues/12-evidencia-proximo-ciclo-resolution.md) conserva o [contrato histórico N-01–N-05](../../docs/specs/Multimercado_Proximo_Ciclo_2026-10-09.md) e deriva a [SPEC de instrumentação e protocolo](../../docs/specs/Instrumentacao_Protocolo_Multimercado_2026-10-09.md), ready_local para EN-T1–EN-T3 conforme revisão independente. A consulta inicial JEV foi inválida; consultas distintas e válidas recomendaram schemas fechados e diligência pública Cedro. Recibos e limites estão ligados à resolução e ao ticket de schema.

Calibração financeira e promoção por instrumento/venue; derivados cripto, funding, colateral e liquidação se sua inclusão for decidida; parâmetros numéricos de latência após piloto; conectores privados B3 quando documentação e acesso estiverem disponíveis; desenho visual detalhado após contrato de capacidades; agregação econômica de carteira com moedas e horários distintos.

## Out of scope

Ordens e gestão automática de execução, contratação/licenciamento de dados, publicação, migração destrutiva e promessa de desempenho financeiro. A redução de preenchimento manual não dispensa reconciliação verificável de conta e posição.

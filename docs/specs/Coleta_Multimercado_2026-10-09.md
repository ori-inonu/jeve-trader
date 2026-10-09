# Coleta multimercado — especificação das próximas etapas

Data: 2026-10-09. Estado: **proposta documental; aplicativo não implementado**. Origem: investigação solicitada por Gabriel. Critérios da entrega atual: [AM-01–AM-06](../research/Expansao_Mercados_Aceites_2026-10-09.md). Este documento especifica incrementos futuros; não concede autorização para contas, despesas, publicação ou operações.

## Resultado esperado

Receber dados com procedência, unidade e cobertura explícitas, reduzir entradas manuais quando houver fonte autorizada e alimentar o contexto JEV. Comparar oportunidades somente após separar disponibilidade dos dados, admissibilidade do produto, custos e qualidade estatística. Aguardando é uma alternativa válida. Não classificar mercados por multiplicador máximo anunciado.

Primeiro recorte proposto: observador público de cripto spot, um provedor e um par, sem carteira e sem operações. Spot permite estudar coleta, livro e replay; não demonstra viabilidade de alavancagem nem substitui o WIN. A escolha do provedor será ligada ao recibo de decisão e ao relatório de fontes. B3 permanece frente específica de acesso licenciado; esportes e binárias mantêm gates próprios.

## Requisitos verificáveis

| ID | Evento ou condição | Comportamento esperado |
|---|---|---|
| CM-01 | Fonte cadastrada | Registrar entidade, mercado/venue, endpoint e versão, instrumentos, moeda, granularidade, autenticação, termos, licença, jurisdição, cadência publicada e estado de verificação; desconhecido é null, não zero. |
| CM-02 | Mensagem recebida | Envelope com schema_version, provider, venue, instrument_id, event_kind, exchange_time nullable, receive_time_utc, relógio monotônico local, payload/hash, IDs/seq com namespace e unidades. Valores financeiros e quantidades são strings decimais; sem conversão por float. |
| CM-03 | Instrumento novo | Catálogo tipado: spot, futuro, mercado de exchange esportiva ou contrato binário. Tick/step, moeda base/cotação/liquidação, multiplicador, vencimento e payoff não são inferidos do nome. Campo inaplicável é null com motivo. |
| CM-04 | Livro incremental | Estado cold → syncing → live; aplicar regras oficiais de snapshot/deltas/checksum e removals. Gap, desconexão ou checksum inválido torna livro inválido imediatamente e inicia ressincronização. Ordenação de timestamp não prova continuidade. |
| CM-05 | Trade válido | Deduplicar pelo ID na partição documentada. VAP é soma de quantidade negociada por nível em janela, com unidade, filtros e cobertura. Mudança de tamanho no book não vira negócio. Agressor só quando fornecido/derivável por contrato explícito; inferência fica rotulada. |
| CM-06 | Dado faltante/vencido | Expor saúde por canal, profundidade e janela: coverage (bounded_complete/partial/unknown), connected, stale, gaps, resyncs, last_update, reason. bounded_complete exige IDs/seq e backfill suficientes para aquela janela; full_tape nunca resulta apenas de conexão. |
| CM-07 | Reconexão/replay | Registrar apenas dados cuja retenção seja permitida, versão do adapter/catálogo, tempos e checksums. Replay reproduz trades/agregados determinísticos; aponta lacunas em vez de preenchê-las silenciosamente. Termos limitam retenção/distribuição. |
| CM-08 | Fonte ativa por tempo prolongado | Respeitar limites e heartbeat, backoff limitado com jitter, fila limitada e observabilidade de perdas. Orçamento de memória/disco e política de retenção precisam ser definidos e verificados antes do piloto prolongado. Sem chamadas JEV por tick. |
| CM-09 | Contexto enviado ao JEV | Snapshot delimitado e sanitizado de features, janela, frescor, cobertura, origem, divergências e opções admissíveis. Comentário do JEV separado de observado/calculado. Confidence contextual não preenche profit_probability. |
| CM-10 | Alternativas econômicas comparadas | Usar payoff/custos específicos do mercado, precisão decimal, moeda comum com câmbio datado, preço executável/liquidez/latência e capital/responsabilidade. Sem custos/risco/autorizações suficientes, resultado é não avaliável ou aguardar; não maximizar lote para recuperar perdas. |
| CM-11 | Probabilidade/modelo candidato | Protocolo cronológico fora da amostra, calibração, custos e simulação de banca com incerteza. Sem amostra suficiente, não fornecer taxa de acerto/rentabilidade/probabilidade da meta. Histórico público acessível não certifica adequação estatística. |
| CM-12 | Mudança de integração | Compatibilidade WIN/Excel preservada, full_tape=False continua parcial; novo adapter não herda multiplicador .20, lotes inteiros ou tarifas WIN. Nenhuma rota habilita ordens. |

## Contratos e responsabilidade dos módulos

Separar `InstrumentSpec`, `SourceDescriptor`, `TradeEvent`, `BookSnapshot/BookDelta`, `SourceHealth` e eventos específicos de resultado/settlement. `SourceBatch` existente serve de referência de envelope, mas não é contrato financeiro universal. Adaptar na borda para não quebrar o observador WIN. Catálogo e capacidades devem ser versionados; quantidade fracionária de cripto e stake/responsabilidade esportiva não cabem silenciosamente em `MarketEvent.quantity: int`.

| Família | Unidade/valor | Informação adicional necessária |
|---|---|---|
| B3 futuro | contratos inteiros × multiplicador monetário por ponto | tick, vencimento/rolagem, sessão, margem vigente da corretora, custos, limites e ajustes; instrumento/código autorizado |
| Cripto spot | quantidade base decimal × preço moeda cotada | step, tick, mínimo, taxas e conversão BRL; sem funding ou liquidação por alavancagem spot simples |
| Derivativo cripto | contratos lineares/inversos e margem | mark/index, funding, manutenção, liquidação, collateral e payoff específico; gate separado da API spot |
| Exchange esportiva | stake back ou stake lay + responsabilidade | market/selection IDs, odds decimais, estado in-play/suspended/closed, delay, regras de redução/settlement, comissão líquida por mercado |
| Binária | stake e payoff definido pelo contrato | cotação/payout na entrada, strike, barreiras, expiração, fonte de liquidação, empate/anulação; ticks não são volume negociado |

Escolhas e comentários para o JEV usam um registro versionado: `decision_id`, `objective`, `as_of`, `candidates`, `evidence_refs`, `data_access`, `legal_product_gate`, `coverage`, `costs`, `risk_metrics`, `missing`, `deterministic_admissibility`, `jev_comment`, `choice`, `receipt_id`. Cada comentário indica o que poderia mudar a conclusão. `costs=null` não significa gratuito. A política de risco da pessoa continua dependência humana; JEV não inventa limites de perda aceitáveis.

## Aceites dos incrementos futuros

| ID | Demonstração requerida | Requisitos |
|---|---|---|
| AC-01 | Catálogo rejeita preço/quantidade inválidos e conserva decimais/unidades; fixtures WIN continuam equivalentes | CM-01–03, CM-12 |
| AC-02 | Testes de gap, delta fora de ordem, duplicata, remoção, checksum e resync seguem contrato do provedor; nenhum estado inválido produz book válido | CM-04, CM-06 |
| AC-03 | Replay conhecido produz VAP exato; alteração de book não cria volume; agressor desconhecido permanece desconhecido | CM-05, CM-07 |
| AC-04 | Timeout/desconexão/backfill incompleto/fila saturada tornam limitações visíveis e não fabricam continuidade; métricas de perdas e retenção verificadas | CM-06, CM-08 |
| AC-05 | Snapshot contextual tem referências e missing; JEV desligado funciona; testes locais/CI não fazem chamadas pagas | CM-09 |
| AC-06 | Payoffs testados por família e alternativas inadmissíveis filtradas; aguardar disponível; custo/câmbio ausentes bloqueiam comparação econômica | CM-10, CM-12 |
| AC-07 | Avaliação prospectiva e fora da amostra registra calibração, intervalo, perdas, custos e probabilidade da meta apenas quando estimável; relatório distingue backtest e resultado real | CM-11 |

## Prontidão e dependências

O plano de dados CM-01–09 permite especificar um observador sem conta. Antes de declarar o primeiro incremento `ready`, fixar provedor/par, contrato de reconciliação, retenção permitida, limites locais e baseline atualizado da implementação. A presente entrega não chama o conjunto inteiro de `ready`.

CM-10–11 são desenho de avaliação, ainda `draft`: orçamento de perda aceitável, custos vigentes, entidade/produto legalmente acessível, dados representativos e tamanho de amostra permanecem necessários. Contratar feed B3, habilitar API comercial e executar operações exigem escopo próprio. Nenhum impedimento destas etapas bloqueia documentação e protótipo de coleta pública autorizado em etapa futura.

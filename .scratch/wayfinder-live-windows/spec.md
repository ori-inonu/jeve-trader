# Mesa de fluxo — especificação aprovada

Status: ready (2026-10-07). Origem: plano integral aprovado por Gabriel nesta conversa.
Fronteira: `issues/04-piloto-real.md`. Prontidão da especificação não encerra o piloto.

## Requisitos e aceites

| ID | Comportamento | Aceite observável |
|---|---|---|
| FW-01 | JEV inicia OFF; `jev.set_enabled({enabled})` controla todos os envios | OFF antes/durante uma chamada, retorno tardio, reinício e erro não produzem novo HTTP, contexto, alerta ou recuo vigente; uso confirmado continua contabilizado |
| FW-02 | Uma chamada em voo, mínimo 1 s, estado mais recente, validade máxima 2 s | testes com cliente local, orçamento SQLite US$1/dia e US$5 total sem renovação |
| FW-03 | Perfil Excel: cotação, negócios, livro e VAP opcionais, auditoria dos campos/fórmulas reais | COM em tabelas selecionadas, sem inventar IDs; negócios coincidentes com IDs distintos preservados; correção detectada; livro/VAP separados do tape |
| FW-04 | Corretoras opcionais; fonte principal única; horários mercado/captura/recebimento separados | estado de fluxo por corretora descreve janela observada e campos ausentes; nenhuma posição de investidor inferida |
| FW-05 | RTD throttle opt-in 250 ms com restauração; polling COM 250 ms | teste de salvamento/restauração e indicador do valor observado; interrupção forçada registra restauração não confirmada |
| FW-06 | Captura auxiliar local Profit selecionado, inicialmente OFF, OCR parcial | imagens permanecem locais; livro/snapshot identificado, perdas e legibilidade explícitas, nenhum volume duplicado com Excel |
| FW-07 | Fluxo local e hipóteses: agressor, cenário, fenômeno, premissa literal | janelas 5 s/5 s anteriores/30 s; absorção vendedora favorece cenário comprador; exaustão compradora não confirma venda; Choice e Nouls independentes |
| FW-08 | Mesa integrada reativa com termômetro bipolar, tape, delta, livro, corretores e hipóteses dos dois lados | dados ausentes indisponíveis, transições curtas, movimento reduzido; inspeção em 640×800 |
| FW-09 | Alertas por episódio com limiar 80/rearme 60/15 s e cotação fresca | cotação vencida bloqueia som/alerta; episódio permanece entre cortes da mesma direção, rearmado somente após limiar/configuração/fonte |
| FW-10 | Entrega Windows preserva instalação/configuração/diário | testes, revisão independente, build e diagnóstico da versão; upgrade sobre 0.4.1 quando instalado |
| FW-11 | Captura real demonstrada e latências separadas | piloto Windows ≥30 min com rajadas/rolagem/filtros/abas/janelas e p95 visual ≤250 ms após recebimento; depende de Profit/Excel e dados autorizados disponíveis |
| FW-12 | Avaliação contextual anotada | casos independentes com contradição/insuficiência/interpretação; sintéticos não certificam rentabilidade nem equivalem a piloto real |

## Contratos de implementação

Seams autorizados: `DecisionService.command/snapshot`, `SourceBatch`, `CombinedExcelBridge`,
`ObservationSession`, `FlowEngine.snapshot`, `build_context` e `liveSnapshot`.
Sem ordens nesta etapa. Capital é manual, regras monetárias permanecem determinísticas,
dados parciais permanecem parciais. Nenhuma contratação ou chamada paga em testes.
RTD/OCR não constituem prova de tape integral. Não foi confirmado feed público gratuito
com todos os dados WIN; MT5/ProfitDLL são rotas condicionadas a acesso, sem ABI inventada.

## Tarefas desta implementação

1. Controle e validade JEV — FW-01/02/09.
2. Contratos/auditoria Excel e cálculo observado — FW-03/04/05/07.
3. Captura auxiliar local — FW-06.
4. Mesa integrada — FW-08/09.
5. Verificação, revisão e pacote — FW-10/12.
6. Piloto real e fronteira externa — FW-11 (aberto até evidência).

Evidência: `implementation-evidence.md`; registrar plataforma, testes, hashes e limites.

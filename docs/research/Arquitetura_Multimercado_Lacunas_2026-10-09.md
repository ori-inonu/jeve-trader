# Arquitetura atual e lacunas para múltiplos mercados — 2026-10-09

Status: pesquisa de código concluída; propostas abaixo não são uma especificação aprovada, implementação ou certificação. Ticket: `.scratch/wayfinder-multimercado/issues/03-arquitetura-atual.md`.

## Resultado

O projeto dispõe de fronteiras úteis: adaptador de aquisição, acumulador de eventos, geração contextual, risco determinístico, diário e renderização. A versão examinada, entretanto, representa uma única sessão WIN alimentada por Excel, uma conta manual em BRL e um ciclo contextual em voo. Substituir somente a coleta não entrega um sistema B3 + cripto: há regras WIN no cálculo, persistência, identidade de candidatos e apresentação, além de gates que reconhecem exclusivamente Excel como fonte ao vivo.

A evolução pode reutilizar Tauri/React e Python, as validações de integridade, a separação entre observação e inferência, o descarte de respostas vencidas e o diário de reconciliação. Precisa ampliar os contratos antes de conectar novos mercados, mantendo a execução de ordens fora deste escopo. Fonte de mercado e estado de conta são integrações diferentes; um feed direto não elimina a reconciliação manual nem fornece uma distribuição financeira validada.

## Escopo e método

- Foram examinadas somente as cópias de fontes e contratos fornecidas pelo integrador, incluindo suas alterações preexistentes. Os hashes representam esses bytes, não um commit limpo ou uma release.
- As referências `arquivo:linha` abaixo são relativas à raiz do projeto. A evidência literal foi lida com numeração de linhas; SHA-256 foi recalculado antes da produção deste relatório.
- Houve inspeção estática e cálculo de hashes. Não foram executados aplicativo, testes, compilação, janela Windows, feed de bolsa, consulta autenticada ao JEV ou ordem. Nenhum resultado operacional, latência de mercado ou rentabilidade foi verificado.
- O ticket chegou à cópia após a primeira inspeção; foi lido antes de concluir. Nenhum código, ticket, diário privado ou estado do harness foi alterado. O único arquivo escrito foi este relatório.
- Dependências importadas como `jev_client.py`, gerador completo de geometria, `app_store.py`, host Rust/Tauri, `risk_config.json` e `flow_rules.json` não integram esta cópia. Não se atribui comportamento adicional a elas. Pesquisa externa de fornecedores/licenças cabe ao ticket separado; este relatório não escolhe fornecedor ou informa preço vigente.

## Evidência executável e consequências

### Instrumento, quantidade e dinheiro

`FlowEngine` já recebe `tick_points` como parâmetro (`app/flow_engine.py:62–63`), aceita um símbolo genérico (`:89–91`) e impede mistura de símbolos e rollover implícito (`:53–59`). Entretanto, `ObservationSession` constrói o motor sem informar esse parâmetro tanto na abertura quanto no reset (`app/app_core.py:94–96,109–122`), herdando tick 5. Seu estado contém uma única sessão, gráfico, cotação, livro e geração. Não há identificador explícito de venue, classe de ativo, vencimento, base/quote, unidade de quantidade ou revisão da especificação do instrumento nesses contratos.

Evidência literal:

```python
# app/decision_engine.py:8–9
CENT = Decimal('.01')
POINT_VALUE = Decimal('.20')
# app/flow_engine.py:155–158
price = _decimal(event["price_points"], positive=True)
if price % self.tick:
    raise ValueError("Price off tick")
quantity = _integer(event["quantity"], 1, 10**9)
# app/context_cycle.py:52,61
value = Decimal(row[name+'_points']) / Decimal(5)
literal_premise=premise, side=row['side'], **prices, tick_points='5',
```

O financeiro aceita somente texto, inteiro ou `Decimal`, rejeita float e valores não finitos (`app/decision_engine.py:12–18`); esse contrato é reutilizável. A quantização monetária é fixa em centavos, os campos têm sufixo `_brl`, custos e margens são por contrato, slippage está em pontos e os ganhos usam `POINT_VALUE` (`:21–22,26–42,105–130,152–155,176`). A geometria é validada em múltiplos de 5 (`:147`), o conjunto de quantidades é inteiro (`:149–150`) e `DecisionPlan.quantity` é inteiro (`:83–99`). Esses fatos descrevem a versão examinada, não uma comprovação de parâmetros operacionais atuais da B3.

O acoplamento também está na entrada: `MarketEvent.price_points` e `QuoteSnapshot` são floats e as quantidades são inteiras (`app/profit_bridge.py:35–60`); `_price` converte `Decimal` em float (`:182–186`), `_quantity` rejeita frações (`:189–193`). Livro e VAP validam `% 5` (`:765,785`). O motor converte o preço recebido de volta a `Decimal`, mas não recupera precisão perdida na fronteira. A identidade contextual exige números canônicos em texto e rejeita floats (`app/context_identity.py:1–5,12–32,35–50`); convém preservá-la e generalizar suas unidades/versionamento.

No diário, a abertura exige símbolo começando com WIN, quantidade inteira e preço `% 5`; só consolida a mesma posição/lado/símbolo (`app/decision_store.py:63–101`). O fechamento calcula P&L com `POINT_VALUE` e trata a primeira posição (`:103–134`). Portanto, não basta aceitar `BTCUSDT` no formulário: a aritmética e a identidade da posição continuariam incorretas. Uma futura operação spot ou derivativo requer fórmula documentada por produto, unidade de liquidação, precisões e tratamento de custos próprios. Nenhuma fórmula financeira nova é escolhida neste relatório.

Contrato a especificar: `InstrumentSpec` versionado, identificador canônico separado do símbolo do provedor, venue, classe de produto, vencimento quando aplicável, tick, quantity step/min/max, multiplicador, unidade de preço/quantidade, base/quote e moeda de liquidação. Números econômicos devem permanecer texto decimal desde o adaptador. Produtos sem contrato completo ficam disponíveis apenas na leitura que sua evidência permite, sem reutilizar o cálculo WIN por omissão. Conversão para moeda de apresentação exige taxa com fonte, corte e idade; não deve alterar silenciosamente a moeda contábil.

### Fonte, relógios, sequência e livro

`SourceBatch` é uma fronteira existente para eventos, cotações, saúde, avisos, livros, agregados, capabilities e evidência (`app/profit_bridge.py:80–95`). É reutilizável como conceito, mas os tipos atuais não carregam provider/venue/stream ID nem sequência de exchange ou contrato do instrumento. `SeenTradeIds` distingue símbolo, data UTC e ID, com limite e contador de eviction (`:98–124`); o namespace ainda não distingue provedores/venues. Timestamp sem fuso é interpretado como São Paulo (`:196–202,240–245`), apropriado à origem histórica examinada, não à normalização universal de APIs.

O núcleo retém falhas de integridade até reset; mesmo instante requer IDs distintos e rollover é explícito (`app/flow_engine.py:53–59`). Completar os flags agora não torna o histórico anterior completo (`:106–122`). Trades exigem ID, grade, quantidade válida e agressor buy/sell/unknown (`:147–185`). O contrato `set_book` recebe snapshot completo, ordenado e sem duplicação/travamento/cruzamento; alteração com o mesmo horário gera falha (`:189–223`). Ele não reconstrói um livro incremental a partir de um snapshot REST e deltas de WebSocket. Essa responsabilidade precisa ficar em um adaptador/reconstrutor que conheça a sequência e as regras do fornecedor; não deve entrar no motor como um snapshot aparentemente íntegro antes da sincronização.

A coleta COM mantém cotações, tape, livro e VAP no mesmo ciclo, mas registra falta de atomicidade, `full_tape=False` e continuidade não demonstrada (`app/profit_bridge.py:698–736`). `sequence_ok=True` na leitura combinada não representa sequência de exchange; a verificação anterior é ordenação temporal (`:341–350,706–721`). `market_ts_ms` e `captured_at_ms` já são separados no livro (`:774–775`) e o motor usa idades independentes para trade e livro (`app/flow_engine.py:274–319,390–443`). Isso deve ser conservado.

Evidência literal de um acoplamento decisivo:

```python
# app/app_core.py:143–149
self.mode = "replay" if replay else "excel_observation"
quality = batch.health.to_dict()
quality["data_origin"] = "replay" if replay else "live"
if not replay:
    # Successful Excel reads do not prove a Nelogica market connection.
    quality["feed_connected"] = None
```

Essa regra é prudente para Excel, mas usá-la sem alteração para um adaptador direto descartaria a informação de conexão verificada e o rotularia Excel. As mensagens sobre RTD (`app/app_core.py:173–177`) e limitations do serviço (`app/desktop_service.py:298`) também são específicas dessa fonte. Capability deve comunicar disponibilidade, validade e alcance por canal; uma flag global `connected` não prova que tape e livro estão sincronizados.

`ProfitDLLContract` demonstra somente a fronteira de SDK autorizado: assinaturas trade/quote/disconnect, fila limitada, gap quando a sequência é documentada por símbolo e overflow visível (`app/profitdll_contract.py:8–61`). Exige WIN (`:14–16`), não traz callback de livro e retorna `full_tape=False` (`:54–61`). Não é um driver operacional demonstrado, nem uma alternativa independente da Nelogica já instalada.

Contrato a especificar: origem e stream identificados; exchange event time, provider time quando existir, receive time e persist time separados; relógio monotônico local para durations/timeouts; event ID e âmbito da sequência documentados; lifecycle disconnected/connecting/synchronizing/live/degraded/stale; política de overflow/gap e nova geração; capacidades por canal com unknown explícito. Deltas exigem reconstrução determinística, descarte de período inconsistente e ressincronização documentada. Repetição do horário de captura não renova o horário do evento. A continuidade alegada precisa de evidência do contrato do feed e da execução; ordenação e conexão TCP não bastam.

### Conta, reconciliação e persistência

Conta e feed estão separados no serviço, uma base útil. `AccountState` exige `reconciliation_origin='manual'` e guarda patrimônio, pico e margem somente em BRL (`app/decision_engine.py:26–42`). `DecisionStore.update_account` usa revisão esperada, preserva posições e registra divergência em vez de apagá-las (`app/decision_store.py:39–52`). A declaração de execução real além da capacidade é preservada com divergência (`:90–100`); idempotência existe e retries conflitantes falham (`:55–61`). Esses princípios são reutilizáveis em uma futura integração de conta somente leitura.

Evidência literal da estrutura atual:

```sql
-- app/decision_store.py:18
CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, body TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY, ts_ms INTEGER NOT NULL,
    kind TEXT NOT NULL, body TEXT NOT NULL, event_key TEXT UNIQUE);
```

Há uma chave global `account` (`:19–37`), configurações globais `live_source`/custos/contexto no serviço (`app/desktop_service.py:188–198,300–302`) e `event_key` único em todo o ledger. O histórico usa ordem global por ID (`app/decision_store.py:171–175`). Isso funciona para o laboratório atual; não isola duas contas, o mesmo ID em duas venues ou instrumentos simultâneos. O timestamp do ledger é inserção local (`:163–169`), não necessariamente o horário da execução declarada.

Contrato a especificar: account ID estável e origem; saldos/posições por ativo/moeda; last reconciliation time, freshness e divergências; executions/fills separados de leitura de saldo; chaves idempotentes com namespace de origem, conta e execução; partições de mercado por provider/venue/instrument/stream/session, eventos e experiências contextual/econômica separados. Migração deve preservar os dados WIN e identificadores de instalação; não reinterpretar registros antigos sem a versão do contrato. Sincronização externa autenticada e readonly precisa de autorização e documentação específicas. Falta de acesso mantém conta manual explícita, em vez de inventar saldo.

### JEV, cadência e evidência contextual

O código já automatiza avaliações relevantes após habilitação: `ContextCadence.start` exige ausência de pending, projeção alterada, intervalo e retry elegíveis; failures geram backoff (`app/live_context.py:10–32`). `relevant_projection` exclui mudança apenas de relógio, preservando fatos/qualidade/geração/configuração (`:88–101`). `request_jev` mantém uma chamada em voo, reserva orçamento antes de dispatch, persiste submissão, usa worker e timeout de 3 segundos (`app/desktop_service.py:489–548`); o tick automático está em `:701–710`. Não é necessário criar outro fluxo manual para cada atualização.

Os gates de retorno incluem geometria literal, enabled/control/credential/parameter revisions, custos, expiry, source generation e account revision (`app/desktop_service.py:270–284`). Há recusa de resultado ao desligar e preservação de consumo conhecido/pendente (`:656–710`). `context_cycle.py` associa candidato e snapshot a hashes/versionamento, janela e evidência (`:39–67,83–129`) e separa support, contradiction e insufficient; ausência de apoio não vira contradição (`:102–114`). A decisão contextual Choice é experimental e não dimensiona lote (`:115–121`). `context_requests.py:18–26` repete esses limites. Reutilizar esses contratos é mais valioso do que aumentar número de chamadas sem qualidade de dados.

Os acoplamentos estão na elegibilidade exclusivamente `excel_observation` (`app/desktop_service.py:278,497–501,701`), um `ContextCadence`, um pending e um latest result por serviço (`:143–158`), uma conta/custo global e tick 5 no candidato (`app/context_cycle.py:51–63`). Múltiplos instrumentos precisam de fairness e prioridade documentadas, não apenas N threads que multiplicam chamadas. As regras de idade também distinguem ao vivo de histórico pelo modo Excel (`app/app_core.py:257–279`); qualquer modo novo precisa entrar no mesmo contrato de validade.

O risco online não ganha validação por ter feed real. `snapshot` chama `compare_plans` sem outcome estimates e seleciona espera (`app/desktop_service.py:207–212`). `compare_plans` inclui `q=0`; a probabilidade financeira só é calculada com evidência temporal/deployment aprovada e sem sintético (`app/decision_engine.py:138–140,165–183`). Os gates locais e `orders_enabled=False` (`app/desktop_service.py:268`) permanecem invariantes. A semântica de confidence/Noul deve continuar contextual.

Há dois planos de controle que não devem ser confundidos. A delegação de escolhas de arquitetura usa o plugin Jev Workflows, conforme AGENTS fornecido. O aplicativo examinado ainda contém `PilotBudget` com default diário US$1 e total US$5, reserva persistida, estimativa por token e `billed_usd=None` (`app/live_context.py:59–62,80–83,104–157`); a UI expõe esses máximos (`desktop/src/LiveConfiguration.tsx:82–83`). Esse é um fato do código do produto. Não prova teto ativo no plugin consultivo e sua remoção não pode ser inferida como autorização para renovar/substituir ledger ou consumo do aplicativo. A cotação por token comentada no código não foi validada neste ticket.

Contrato a especificar: context job por instrumento/stream/generation/spec/config/corte; invalidation local em mudanças; projeção estável com orçamento e scheduler compartilhados; fila limitada com coalescing da última projeção, prioridades/fairness e backpressure; máximo de chamadas e consumo desconhecido visíveis. Escolher multi-instrumento no mesmo request ou requests independentes deve considerar validade e independência das respostas; decisão consultiva não altera regra de risco nem concede autoridade para ordem.

### Transporte, interface e trabalho manual

O transporte já oferece commands com UUID, promises e timeout de 10 segundos, evento `engine` e alternativa local HTTP para desenvolvimento (`desktop/src/transport.ts:18–41`). O lado Python aceita JSON versionado e retorna snapshot completo; publica em mudança com mínimo de 100 ms e heartbeat de 1 s (`app/desktop_service.py:796–838`). A sequência é de publicação do snapshot, não sequência de exchange. O consumidor possui uma única callback (`desktop/src/transport.ts:20,28–32`); o `App` mantém um snapshot e rejeita sequência menor/igual globalmente (`desktop/src/App.tsx:39–59`). Não existe subscription por instrumento nesses trechos. O host nativo não foi inspecionado; não se afirma comportamento de restart ou segurança de processo além do contrato visto.

O renderer já invalida contexto/livro/tape quando o motor silencia, preserva snapshot histórico e usa validade distinta por canal (`desktop/src/liveView.ts:3–27`). Essa proteção é condicionada ao modo Excel (`:6–14`). `tradeProjection` valida linhas, exclui IDs ambíguos, limita 200 pontos, distingue histórico/current/stale/unavailable e preserva seleção observada (`desktop/src/tradeProjection.ts:21–89,96–109`). Sua quantidade é `Number.isSafeInteger` (`:25`), freshness atual exige `excel_running` (`:57–67`) e identidade é `JSON.stringify([generation,symbol,id])` (`:92–93`), sem provider/venue/engine session. É necessário ampliar identidade e epoch de conexão antes de compartilhar um transporte entre mercados; uma geração local igual em outra sessão não deve reutilizar uma seleção ou resposta.

As telas demonstram vínculos concretos: `App` mostra moeda BRL por `Number` e `Intl`, conta manual/uma primeira posição, formulário Profit/WIN e custos B3 (`desktop/src/App.tsx:10,27–36`); `CockpitShell` mostra WIN/B3 Mini Índice e mede fonte com Excel (`desktop/src/CockpitShell.tsx:14–16,27–30`); `LivePanel` mostra EXCEL RTD, pontos/contratos, top 5 níveis e explicitamente limita interpretação de corretoras/VAP/OCR (`desktop/src/LivePanel.tsx:46–62,82–118`); `TradeExplorer` usa eixos pontos WIN/contratos e current pela fonte Excel (`desktop/src/TradeExplorer.tsx:40–58,68–95,167–180,203`).

Há componentes a preservar: tabela/2D acessível, seleção com detalhes de evento, qualidade/limites visíveis, fallback WebGL→2D (`desktop/src/TradeExplorer.tsx:13–29,117–141`), navegação com aria/skip e reduced motion (`desktop/src/CockpitShell.tsx:8–37`). A utilidade de uma visualização 3D não foi medida neste ticket; redesign não exige substituí-la nem promovê-la a principal sem avaliação de tarefa.

As etapas manuais atualmente são perfil Excel com arquivo/planilhas/ranges/contrato/filtros, abertura do arquivo, conta/custos/execuções declaradas, seleção de janela/região OCR e habilitação do JEV (`desktop/src/LiveConfiguration.tsx:18–86`; `App.tsx:27–36`). O aplicativo já salva perfil e reconecta, descobre nomes de arquivos e armazena credencial pelo serviço (`app/desktop_service.py:188–198,325–343,376–399,433–474,592–655`). O código não precisa que o usuário refaça toda configuração a cada snapshot. Uma integração direta pode remover os passos Excel/OCR e oferecer catálogo de instrumentos/metadata e diagnóstico de conexão; automação de conta é uma entrega separada. Habilitação de gasto não é restaurada em disk (`app/desktop_service.py:139–140`) e essa decisão não deve ser apagada como mera fricção visual.

Contrato a especificar: selecionar venue/instrumento e fixar pane; snapshot ou subscription com stream/session/revision; preço/quantidade/moedas e precisão da metadata; capability state visible com motivo e horário por canal; freshness local para qualquer live source, com histórico separado; conta/reconciliação e JEV por contexto selecionado, sem misturar último resultado de outro mercado. Tabela e renderização podem converter números para coordenadas após validar limites/erro de visualização, mas o valor literal original e os cálculos econômicos devem permanecer preservados.

## Intenção documental e estado do código

`docs/ARCHITECTURE.md` mistura a camada Desktop documentada como 0.4.0 e referências históricas da baseline. O propósito de observador, conta manual, falta de ordens e falta de probabilidade financeira validada coincide com o código (`:5–31,65–87,104`). Outras declarações precisam ser atualizadas quando houver SPEC:

| Declaração documental | Evidência da cópia atual | Limite da conclusão |
|---|---|---|
| Chave somente em memória e nunca persistida (`:93`) | Serviço lê/escreve vault e UI descreve Gerenciador de Credenciais (`app/desktop_service.py:120–158,446–459`; `LiveConfiguration.tsx:49–54`) | Foi inspecionada a chamada, não o vault/Windows em execução. |
| Polling histórico ~2 s (`:81`), cadência mínima 10 s e padrão 120 por abertura (`:93`) | Collector e evidência apontam 250 ms; settings contextual default 1000 ms, bounds 1000–60000; UI permite calls até 10000 (`desktop_service.py:93`; `profit_bridge.py:735`; `live_context.py:59,70`; `LiveConfiguration.tsx:53`) | Não foi medido atraso efetivo de exchange/Excel/JEV. |
| Alterações da pesquisa anterior não incorporadas à baseline (`:114`) | A cópia atual inclui premissas literais, hashes e registro experimental (`context_cycle.py:39–129`; `desktop_service.py:519–528,656–710`) | Há evolução no checkout; não se afirma release instalada ou deployment. |
| Runtime/JobObject/instalação e armazenamento sob JevWIN (`:5,110`) | Implementação do host/build não fornecida | Preservar como contrato/intenção, sem certificar lifecycle ou migração. |

O integrador deve citar hashes e escopo, não tratar a documentação histórica como prova de capacidades executáveis atuais. `AGENTS.md:30–37` e `CONTEXT.md` continuam exigindo separação entre observado/calculado/inferido, capital manual e ordens fora de escopo.

## Requisitos propostos para a especificação independente

Os itens abaixo são entradas de pesquisa para o integrador congelar com fontes e submeter a revisão independente. Não constituem aceite passado nem permitem enfraquecer os invariantes do projeto.

| ID | Requisito observável | Fonte que motiva o requisito | Ensaio de aceitação a preparar independentemente |
|---|---|---|---|
| R-ARC-01 | Instrumento/venue/produto/revisão e unidades acompanham todo evento, candidato, plano, ledger e pane. WIN legado mantém identidade/valores. | `app_core.py:94–122`; `context_cycle.py:51–63`; `decision_store.py:73` | Dois símbolos iguais em venues diferentes e dois contratos/vencimentos nunca colidem; metadata incompleta impede cálculo econômico; roundtrip legado preserva bytes econômicos. |
| R-ARC-02 | Preços/qty/custos financeiros têm representação decimal e grade/step/fórmula por produto; nenhuma fallback implícita em tick5/0,20/BRL. | `profit_bridge.py:35–60,182–193`; `decision_engine.py:8–22,125–155` | Inputs decimais de alta precisão mantêm literal/valor; step inválido falha; vetor financeiro independente por produto/moeda; float/nonfinite não chega ao cálculo. |
| R-ARC-03 | Gap/overflow/desconexão/ressync ficam visíveis e invalidam a geração afetada; timestamps e sequência são domínios distintos. | `flow_engine.py:53–59,106–122`; `profitdll_contract.py:34–61`; `profit_bridge.py:706–736` | Replay de evento ausente, ID conflitante, book delta fora de ordem, reset e silêncio nunca exibe continuidade comprovada nem indicação vigente; outro instrumento saudável segue válido. |
| R-ARC-04 | Snapshot e deltas formam livro apenas após sincronização determinística; idade do livro independe de tape. | `flow_engine.py:189–223,390–443`; `profit_bridge.py:774–775` | Caso de snapshot+deltas com deletion, duplicação e gap tem resultado de níveis/seq conhecido por fonte primária; gap exige resync; novo trade não revalida livro antigo. |
| R-ARC-05 | Conta readonly reconciliada tem origem, corte e revisão; divergência preserva execuções; conta manual continua explícita quando necessária. | `decision_engine.py:26–42`; `decision_store.py:39–61,90–100` | Mesma execution em duas contas não colide; retry idempotente não duplica fee/P&L; saldo inconsistente não apaga fill; dados vencidos não se tornam reais por inferência JEV. |
| R-ARC-06 | Scheduler local limita trabalho, reserva consumo e aplica fairness; retorno JEV só vale para contexto original ainda vigente. | `live_context.py:10–32,88–157`; `desktop_service.py:270–284,489–548` | Instrumento ativo não elimina o menos ativo; fila limitada coalesce; respostas após troca de fonte/spec/conta/OFF/expiry são históricas; uso desconhecido não zera. |
| R-ARC-07 | Qualquer fonte live é invalidada no frontend em silêncio; identidade de stream/session/sequence não se confunde com exchange. | `App.tsx:39–59`; `liveView.ts:3–27`; `tradeProjection.ts:57–108` | Duas panes recebendo respostas fora de ordem/restart mantêm seleção e dado corretos; ocultar/retornar janela não renova dado; fonte degradada mostra canal/motivo. |
| R-ARC-08 | Redução de passos é mensurada por tarefa e mantém evidência/controle de gasto/ordens. | `LiveConfiguration.tsx:18–86`; `desktop_service.py:139–140,268` | Comparação de tarefas onboarding→dado válido e reconexão mede passos/intervenções/tempo com mesmo critério de qualidade; quote-only ou demo não conta como leitura de fluxo válida. |
| R-ARC-09 | Mercado, conta, contexto, custo e experiências têm namespaces/migração reversível; sem segredos ou estado privado no repo. | `decision_store.py:13–37,163–175`; `AGENTS.md:37` | Fixture DB legado migra com saldo/posição/eventos preservados; novo provider/conta não contamina histórico; export selecionado respeita origem/redistribuição; backup/rollback demonstrável. |

Não objetivos: envio ou habilitação de ordens; acesso/pagamento de feed ou conta sem autorização; estratégia ou probabilidade de lucro nova; remoção de gates para demo; upgrade global do harness/plugin; renomear dados/instalação JevWIN sem migração; publicação/deployment remoto; persistência de chave/transcrição/diário privado em repositório. A aquisição direta da B3 também depende de acesso/licença documentados no ticket de fornecedores; este código não os concede.

## Alternativas reais para o lote consultivo do JEV

Estas alternativas são mutuamente distinguíveis e têm apoio nas fronteiras encontradas. Não há uma escolha técnica aprovada neste relatório. O integrador pode enviar ao plugin contexto mínimo sanitizado, alternativas e critérios, preservando recibo e gates locais.

| Opção | Forma | Pontos favoráveis | Custos/risco | Evidência e condição para escolha |
|---|---|---|---|---|
| A | Manter Desktop Tauri/React + um serviço Python como monólito modular; acrescentar registry, adapters e sessões por stream, scheduler/ledger locais. | Reusa pipeline, deploy/lifecycle existentes, SQLite, modo offline e proteção de contexto; menor número de fronteiras novas. | Acoplamento atual precisa ser retirado; carga de feeds/CPU e fairness podem competir com UI/contexto; fronteiras internas devem ser realmente profundas. | `desktop_service.py:120–158,796–838`; `app_core.py:93–205`. Escolher se volume e isolamento medidos cabem no processo e os contratos por stream passam. |
| B | Separar supervisor local de dados/reconstrução/replay do serviço de decisão/contexto/UI, com protocolo versionado e armazenamento local. | Reconexão/backpressure e livro ficam independentes da latência JEV; replay central reproduz exatamente a entrada; falhas de um adapter não comprometem todo o serviço. | Novo IPC/lifecycle, cópias/filas, versionamento e observabilidade; maior superfície Windows e integridade do log. | O subprocesso COM existente já isola aquisição (`desktop_service.py:52–118`), enquanto jobs JEV usam worker (`:531–548`). Escolher se feeds reais revelarem necessidade de isolamento e o host puder provar shutdown/restart. |
| C | Centralizar ingestão e armazenamento em serviço remoto; Desktop/web consome subscriptions autenticadas. | Pode servir sessões/dispositivos múltiplos e reduzir dependência de Windows para aquisição. | Hosting, custos, auth/segredos, licenciamento/redistribuição, privacidade, latência e operação remota novos; deployment não está autorizado por esta pesquisa. | A UI já consome transporte, mas não existe backend remoto demonstrado (`transport.ts:18–41`). Somente especificar se o requisito multiusuário/dispositivo e permissões forem confirmados; não executar como fallback. |

Uma decisão independente é o recorte inicial cripto: leitura spot, leitura de derivativos ou ambos. A leitura spot ainda requer qty decimal/base-quote; derivativos acrescentam liquidação/margem/funding e fórmula de P&L por produto. Essas capacidades não existem no risco WIN examinado. A pesquisa de APIs deve confirmar os contratos concretos antes de oferecer alternativas com qualidade de evidência comparável. Evitar uma opção fictícia “adaptador genérico pronto”: não há essa implementação no checkout.

Outra decisão é a atualização UI: snapshot por instrumento/pane com assinatura filtrada versus envelope agregado com estado por instrumento. O transporte atual torna ambas implementáveis conceitualmente; a opção deve considerar payload real, latência ponta a ponta, troca de instrumento e seleção histórica. Não há benchmark que autorize declarar uma mais rápida. Uma opção mínima focada em um instrumento selecionado pode coexistir com ingestão de múltiplos streams, desde que a troca invalide contexto/seleção corretamente e o produto não prometa panes simultâneas ainda não suportadas.

Sequência de entregas a considerar, sem implementação: congelar contrato de instrumento/stream/capability → ensaios de adapters readonly e replay → isolamento de ledger/conta → scheduler por contexto → redesign com subscriptions/estados → avaliação Windows com dado real autorizado. Reduzir configurações Excel/OCR vem do adapter e do catálogo confiável; “mais inteligência” exige boa evidência, identidade e feedback experimental, além de interface.

## Perguntas ainda dependentes de outras fontes

1. Quais direitos de dados B3, sequência, depth e redistribuição são realmente acessíveis ao usuário sem Profit? Este ticket não resolveu licença/provedor.
2. Qual primeiro produto/venue cripto e que grandezas financeiras/contábeis devem ser representadas? Há intenção de expansão; falta contrato concreto.
3. A conta readonly será integrada com qual broker/exchange e autorização? A dependência manual permanece demonstrada até isso ser resolvido.
4. Qual carga real de streams e qualidade/latência esperada? Sem avaliação pareada, A/B/C e snapshot/subscription são alternativas, não ganho demonstrado.
5. Host, cliente JEV, geometria, fixtures e regras não copiados precisam entrar na revisão de implementação. Não bloqueiam estes achados locais; impedem conclusão mais ampla.

## Manifesto de fontes da cópia examinada

SHA-256 dos arquivos fornecidos, recalculados em 2026-10-09. Arquivos auxiliares fornecidos mas não analisados integralmente (`capture_pilot.py`, `package.json`) são listados para identificar a cópia; nenhuma conclusão depende de comportamento não inspecionado neles.

Nota de proveniência do integrador (após revisão independente): o hash do ticket `03-arquitetura-atual.md` abaixo é histórico, da cópia pesquisada antes da resolução canônica. O registro original foi preservado; não representa o hash da versão atual do ticket.

```text
.scratch/wayfinder-multimercado/issues/03-arquitetura-atual.md e4a6d4fb0e8b19b02d7da11fea8d0a1f84468e3bb058fc6b6669136ba2c783a7
AGENTS.md 7805ec279f827c3e7208053ef1a669d06446093fc6fc957d6baec990fca5a799
CONTEXT.md 5aa480820c1774d3b6d2b4642256ebef0c6cc0c28a7968e1cb50feee70593dcc
docs/ARCHITECTURE.md bdf2aed8ad163c5380edacac63275e9d475f391d86f1c4ca79c648c8f0d8cebe
app/app_core.py d124d3f7627eff9213b3da600c1f147539d76d45b39bd703821de26f9dd6db52
app/profit_bridge.py e717dcfb4f0a9f7f8d67b801c7e2575e6a1c81bdef50ce629ccdd5ccae55ee3b
app/profitdll_contract.py 8eb1a97cdac3b1103dcf6b490a9e3073ae1a54df59444c014bb68d918f139c3a
app/desktop_service.py 7ebcd5ddd961e158f7a1d5646c9343d3c9eac38e333e26d832f2b256af4f39c6
app/decision_engine.py 809a3010b398a9fb685fe32fb8c4ec6cf1d78af564a144e0fa62e389cbfde450
app/flow_engine.py cf1c7244e73e06e049a728e684be10124757a005c4f489ade4d5e5f210eaef16
app/decision_store.py 1d0650ac12073185b83066f2f25656f93be4e5f79f56c85a2626362580913335
app/context_requests.py ec1749a33381e47433bb74aa0c6e6bb47cfd9e29ff4b63ae91ed2dbf1458e275
app/live_context.py 023faffaa5db7dc02aba6fccf3ed36bf02d28d10363d71734e99e86173f8ab12
app/context_cycle.py 0d9205ccaa282a4a4cfe9a517de0c973bc445588a6789f77905563c6d997a9ea
app/context_identity.py c7c587d19636fa6b8d3300129d55fae1a9a7b83300e7c5b11a914825c4ab92d1
app/capture_pilot.py 1d248a73371b16d46d7ef2f36592b76730e01829a9f2d3776e81f5c5368ee813
desktop/package.json 4e8cc593708ce9946a7d91a7a0f4a3c61c0b7326e9bbc4141a44e52262a9e0b6
desktop/src/App.tsx 50e86225c16a13a67a84de107f998e30706a3e4b0263be5d3105a5822219b4bd
desktop/src/LivePanel.tsx 20d6a8c2c5a5f69b1381eb648a3aaf8929cea6c70842a144a5796ee6f8d37771
desktop/src/CockpitShell.tsx e2c49d7b61a8277f91b91dc50e6e0ee86a67a8b376dc6936d84e078cbf148626
desktop/src/TradeExplorer.tsx fc58b9910b972de4e84f342958be594228377766a5d3ade47ceefdb2943e205b
desktop/src/transport.ts cf78cf2c9e9d885b1a56d55967b01aae4f5a1bcded7e0caa214620ff9bc2ed3b
desktop/src/liveView.ts 9df8a405ec0ff697229ef7668fa1ad7c9868a3b99e54396905f2867c6746ed5b
desktop/src/tradeProjection.ts 7040fe6ec6716426255a16457ad031cfb1899265bf365698f1965ea62156b230
desktop/src/LiveConfiguration.tsx 5c0f2521be3abdbcd4dd039a2913aa7052efb5841d88691ddc073dc4a371969a
```

# Implementação multimercado — contrato finito
Status: ready para implementação local; gates externos continuam abertos.
Revision: 1. Date: 2026-10-09.
Baseline: da96c6ad4187030a98c4daa86a6b96e1e5b809a9.
Origem: ../../.scratch/wayfinder-multimercado/spec.md (MM-01–MM-12); pedido explícito implement-spec.
Esta SPEC não substitui nem enfraquece o draft de destino. Define o incremento executável que ele exige antes de um piloto público; licenciamento B3, calibração, acesso privado e benefício nativo conservam seus aceites próprios.

## Resultado e limites
Cockpit React/Tauri local com motor Python modular por instrumento e fonte. Piloto público Binance BTCUSDT spot: exchangeInfo, trade individual e bookTicker L1. Sem ordens. WIN por vencimento tem contrato de identidade; feed independente B3 permanece bloqueado até qualificação documental e entitlement. Excel/OCR/laboratório JevWIN continuam acessíveis no modo legado. Não usar resultados WIN para BTC ou cripto derivativos.
Os dados do legado não serão migrados: novo armazenamento fica em multimarket/ dentro da pasta do usuário. Nenhum feed ou conta é conectado automaticamente na inicialização; depois de conexão explícita, metadata/reconnect são automáticos. JEV do produto inicia desabilitado e respeita autorização e budget do produto existentes; consultas de arquitetura são separadas.

## Aceites imutáveis do incremento
| ID | Comportamento observável e verificação pública |
|---|---|
| I-01 / MM-01 | Registro valida metadata Decimal e separa venue/segment/symbol/expiry/source/workspace. Mesma sigla em venues diferentes não compartilha estado. Metadata ausente/incompatível impede cálculo de quantidade. |
| I-02 / MM-02,03 | Envelopes preservam origem/clocks/epoch/metadata/ID/sequência por domínio. Duplicata não altera estado; regressão/gap/overflow/desconexão invalida dependentes, recovery requer nova evidência. quote fresh não prova tape completo. Binance L1 não é livro L2; IDs de trade/bookTicker não certificam continuidade. |
| I-03 / MM-03 | Fonte pública descobre filtros atuais via API, conecta streams, reencontra metadata em reconnect e exibe connecting/live/retrying/error com motivo. Rejeita símbolos fora do piloto; sem metadata verificada não torna workspace elegível. Transporte é read-only, endpoints fixos e TLS validado. CI usa fixtures offline. |
| I-04 / MM-04 | Risco usa Decimal, tick/step/minimum/multiplicador/currency; sempre inclui q=0. WIN step1/tick5/multiplicador0.2, spot fracionário. Valores de fixtures não são defaults operacionais. Não soma moedas, presume funding/liquidação, nem transforma taxa desconhecida em zero. |
| I-05 / MM-05 | Ledger por conta aceita snapshot/fill read-only/importado/manual explícito, com IDs e revisões. Duplicata/out-of-order não duplica patrimônio; conflitos e stale mantêm conta não conciliada. Não solicita trading scopes. Integração privada real continua externa. |
| I-06 / MM-06,07 | Scheduler por evidência relevante, fila limitada/coalescida, sem mudança sem chamada. Perguntas Choice/Noul tipadas e versão exata; timeout/abstenção visíveis. Identidade inclui instrumento/fonte/epoch/metadata/features/questions/custos/conta/seleção e clock monotônico. Mudança invalida resposta/cache; cache não renova idade. JEV indisponível não libera finanças. Setup/CI não consultam API paga. |
| I-07 / MM-08 | Cockpit oferece conexão cripto, B3/legado, seleção de workspace, decisão AGUARDAR com motivos, saúde por domínio, origem/frescor, conta/custos e detalhes progressivos; teclado, layout estreito e reduced-motion. Troca rápida não mostra resposta de outro workspace. Nenhuma confiança contextual é rotulada lucro. |
| I-08 / MM-09 | Journal/replay preserva causalidade, clocks/epoch/IDs/revisões/perguntas/versões e censura. Persistência/exportação exige política afirmativa por fonte; unknown/denied não armazena payload de mercado. Não incluir dataset capturado no repositório. Replay é identificado, não live. |
| I-09 / MM-10 | Sem modelo aprovado no instrumento/venue/horizonte/metadata atual: probabilidade de lucro não estimada. Custos/conta ausentes impedem lucro líquido/quantidade recomendada. Gate de promoção exige comparação temporal sem leakage (regras/contexto/quantitativo+JEV), origem e escopo exatos; aprovação não ocorre por confidence. |
| I-10 / MM-11 | Wire externo1/2 compatível; multimarket usa wire2 event multimarket.snapshot e resultado interno schema3; incompatibilidade exibe diagnóstico. Ledger/settings legado preservados byte a byte em cópia de teste; fixtures antigas continuam parciais. Build/packaging inclui novo pacote e dependência. |
| I-11 / MM-12 | Antes de código: baseline offline260 testes e workload sintético registrado; queue2000/drain500/snapshot4Hz/200trades, 1000eventos/s por10s, p95 por batch pós-recebimento<=50ms no host. Instrumentar atraso/latência/memória e permitir exportar métrica sem payload privado. Janela nativa/GPU/etapas manuais/benefício JEV permanecem não medidos até comparação prospectiva real; nenhuma conclusão sintética certifica live. |
| I-12 / stress | Testar gap com conexão saudável, update atrasado, tick/step alterado, quote expirado, seleção com chamada pendente, conta stale/quote fresh, fill duplicado após reconnect, clock wall ajustado, burst/overflow, JEV indisponível e retenção negada. Cada caso deve expor motivo e bloquear dependente. |

## Contratos e seams públicos
Clock injetável: wall_ms()->int e monotonic_ns()->int. SystemClock usa time.time e time.monotonic_ns. Decimal de domínio serializa como string; schema não aceita float para dinheiro.

app/multimarket/contracts.py:
- InstrumentSpec frozen: instrument_id,venue,segment,symbol,family,metadata_version,price_tick,quantity_step,quantity_min,minimum_notional,contract_multiplier,base_asset,quote_currency,settlement_currency,expiry_at_ms,calendar_id,status,constraints_verified.
- SourceCapabilities frozen: source_id,version,quote,trades,book,account,trade_semantics,side_semantics,sequence_scope,book_mode,full_tape,retention,export. Binance: quote/trades true, book/account false, individual/aggressor (m buyer_is_maker => sell), sequence_scope unknown, book_mode unavailable, full_tape false, retention/export unknown.
- EventEnvelope frozen, JSON schema3: workspace_id,instrument_id,source_id,epoch,metadata_version,event_id,kind,market_ts_ms,received_at_ms,received_monotonic_ns,sequence_first,sequence_last,payload. Quote payload bid/ask/bid_quantity/ask_quantity, trade price/quantity/aggressor, Decimal strings. Book only para fonte com contrato explícito.
- EvaluationIdentity frozen: workspace_id,instrument_id,source_id,epoch,metadata_version,feature_version,question_version,cost_revision,account_id,account_revision,selection_revision,event_range,received_monotonic_ns. account_id é str|None; comparar revisões sem a identidade da conta é inválido.
- from_wire/to_wire para cada contrato; decimal_text rejeita nonfinite/bool/float.
- Registry(*,clock=None,max_workspaces=8): register_instrument(spec),register_source(caps),open_workspace(*,source_id,instrument_id,account_id=None,workspace_id=None),select(id),get_workspace(id),get_instrument(id),get_source(id),snapshot(); revision e selection_revision.

MarketState(spec,caps,*,clock=None,workspace_id='',epoch=1): ingest(EventEnvelope)->IngestResult(applied,duplicate,resync_required,reasons,epoch); invalidate(reason,domains=('quote','trades','book')); snapshot().
AccountLedger(path,*,clock=None): ingest_fill(dict),reconcile(dict),view(account_id),close(). Wire account includes account_id,revision,mode,status,asof_ms,received_monotonic_ns,balances por currency,positions por instrument_id.
RiskPolicy(*,currency,max_quantity:Decimal,max_cash_risk:Decimal,max_candidates=256,version='mm-risk-v1').
evaluate_quantities(spec,account,costs,*,policy,entry_price:Decimal,stop_price:Decimal,target_price=None,side='buy',quantities=None,model_gate=None)->list[dict]. First WAIT quantity='0'. Unknown estimate fields null.

ContextScheduler(config,*,clock=None): offer(identity,questions,feature_key,priority=0)->dict,take()->dict|None,complete(call_id,response,current_identity)->dict,set_enabled(bool),snapshot(); config max_pending8,min_interval_ms2000,timeout_ms10000,validity_ms2000,model='jev-1.13.0',question_version='mm-context-v1'; timeout/expiry monotônico. build_questions() Choice wait/observe_buy/observe_sell + Noul support/contradiction/insufficient/context only. No account values in provider state.
Journal(path): append(kind,namespace,idempotency_key,payload,*,policy)->dict,replay(namespace)->Iterator[dict],status(),close(); policy retention/export enum allowed/denied/unknown. Sem licenciamento afirmativo, só contadores/diagnóstico sanitizado.
PublicSpotAdapter(transport,*,clock=None): discover(symbol='BTCUSDT')->InstrumentSpec,capabilities(),normalize(message,workspace_id,epoch,metadata_version)->list[EventEnvelope],start(*,workspace_id,epoch,metadata_version),drain(limit=500),stop(). Transporte injetável; transporte real separado fixed HTTPS/WSS. Descoberta pode executar worker; nenhum bloqueio de rede no owner thread.

MultimarketService(data_dir,*,clock=None,adapters=None): command(method,params)->dict,tick()->bool,snapshot()->dict,close(). Métodos multimarket.snapshot,discover,connect,disconnect,select,account.reconcile,account.fill,costs.update,jev.set_enabled,recording.set,replay,metrics. Request outer schema2, sem permitir ordens. Service root integra credencial/budget existentes por callback somente quando habilitado.
Snapshot3 mínimo:
{schema_version:3,sequence,generated_at_ms,selected_workspace_id,workspaces:[{workspace_id,instrument_id,source_id,symbol,venue,segment,status}],selected:null|{workspace_id,instrument_id,source_id,instrument:InstrumentSpec,source:SourceCapabilities,market:{epoch,quote:null|{bid,ask,bid_quantity,ask_quantity,market_ts_ms,received_at_ms,age_ms},recent_trades:[],health:{quote:{status,reason,age_ms},trades:{...},book:{...}},features:{version,trade_count,buy_quantity,sell_quantity,delta_quantity,spread,event_range},warnings:[],full_tape:false},account,decision:{action:'wait',reason,profit_probability:null,quantity:'0',net_profit:null},context:null|{status,model,questions_version,origin_monotonic_ns,age_ms,answers,financial_probability:null},costs},scheduler:{enabled,status,pending,queued,model,question_version,error},recording:{status,reason},metrics:{events,duplicates,rejected,overflow,process_p95_ms,market_lag_ms,rss_bytes,gpu_bytes},gates:{b3,private_account,financial_model,native_evidence},orders_enabled:false}.
O frontend pode aceitar campos extras; ausência de campo obrigatório/versão inválida gera diagnóstico e remove contexto. Snapshot em repouso continua atualizando frescor por monotonic; snapshots não renovam idade.
Transport independente do Snapshot legado. MultimarketCockpit props {snapshot:MultimarketSnapshot,run:(method,params)=>Promise<MultimarketSnapshot>}. Root owns transport/subscriptions, page root/main and service integration.

## Grafo de tarefas e ownership
| Ticket | Dependência | Arquivos exclusivos | Dono |
|---|---|---|---|
| IMP-01 Contratos/state/conta/risco/promoção | ready SPEC | app/multimarket/{__init__,contracts,market_state,accounts,risk}.py; app/test_multimarket_domain.py | implementer domain |
| IMP-02 Fonte pública/scheduler/journal | contrato congelado, executável após IMP01 | app/multimarket/{adapters,network,scheduler,journal}.py; app/test_multimarket_runtime.py | implementer runtime |
| IMP-03 Cockpit/projeção | contrato JSON congelado | desktop/src/{MultimarketCockpit.tsx,multimarket.css,multimarketModel.ts}; desktop/tests/multimarket.test.mjs | implementer UI |
| IMP-04 Integração/migração/empacotamento | IMP01–03 | service.py, desktop_service.py, multimarketTransport.ts, MultimarketRoot.tsx, main.tsx, package metadata, packaging scripts, integration tests | root integrator |
| IMP-05 Verificação/PR/revisão | IMP04 | docs/evidence e entrega | integrator + revisores independentes |
TDD em slices pelos seams públicos; cada writer em branch/worktree exclusivo. Merger integra commits; dois revisores standards/spec contra baseline fixo. Não encerrar tickets B3/benefício por gates implementados.

## Evidência e gates externos
Baseline offline: ../evidence/multimarket-baseline-verification.json.
Baseline sintética antes de código: ../evidence/multimarket-baseline-performance.json.
Escolhas JEV: ../evidence/multimarket-jev-decisions.json. Binance recomendado; seams/workload abstidos, resolução de engenharia reversível fundamentada nos aceites.
B3: faltam proveedor/SKU WIN/WDO, entitlement, schemas/captura e licença de uso/retention/export externo. Não conectar placeholder como feed live.
Conta: credenciais read-only, scopes e fixture autorizada; não ler conta privada nesta tarefa.
Modelo: corpus autorizado, avaliação temporal e aprovação por escopo. Somente gate local nesta tarefa.
Windows/benefício: medição pareada prospectiva de janela nativa e jornada humana; browser/offline não substituem.
Cripto: smoke HTTPS/WSS público neste host prova alcance pontual, não elegibilidade regional ou disponibilidade contínua.

# EM-01 — contrato de implementação local multimercado

Data: 2026-10-09. Autor: pesquisador `/root/multimarket_ready_spec`, conversa própria `[identidade privada omitida]`. Estado: **candidato pronto para congelamento pelo integrador e revisão independente; não implementado ou certificado pelo autor**. Autorização observada: iniciar a implementação das especificações com até três subagentes. Esta autorização não inclui conta, chave, ordem, aposta, depósito, compra, publicação ou validação financeira.

## Resultado e limite da entrega

Implementar um observador Binance Spot BTCUSDT com decimais exatos, negócios individuais, livro agregado por preço, saúde visível, replay sintético, contexto sanitizado e calculadoras de payoff com gates determinísticos. O objetivo financeiro do projeto continua R$400 → R$4.000 em menos de sete dias. Spot é infraestrutura e referência; não representa alavancagem embutida ou vencedor econômico.

O recorte de software CM-01–09/12 pode ser exercitado sem conta. CM-10 terá somente fórmulas e bloqueio de comparação quando faltar evidência; CM-11 terá protocolo/relatório de pendências. **CM-10 operacional, CM-11 empírico e AC-07 permanecem pendentes.** Aceites globais não são enfraquecidos nem classificados como satisfeitos por fixtures. B3, derivativos cripto, esportes e binárias conservam os gates da especificação original. Não substituir o contrato WIN/Excel nem converter cripto em `MarketEvent.quantity: int` ou aplicar multiplicador WIN `0.20`.

## Perfil de fonte congelável

`source_id=binance_spot_public_btcusdt_v1`; `provider=binance`; `venue=binance_spot`; `instrument_id=binance_spot:BTCUSDT`; `kind=spot`; `base_asset=BTC`; `quote_asset=USDT`; `settlement_currency=USDT`; autenticação `none`; produto operacional/jurisdição `null` com motivo não verificado. Sem API key, cookies, carteira, endpoints privados ou fallback para outro host após bloqueio.

Documentação primária revisada hoje no commit `263ac1aa96556af0b4da824c82a1d8cd9a0edda9`. Versão do adapter local `binance-spot-json-v1`. REST v3: base `https://data-api.binance.vision`, GET `/api/v3/exchangeInfo?symbol=BTCUSDT`, GET `/api/v3/depth?symbol=BTCUSDT&limit=1000`; `/api/v3/trades?symbol=BTCUSDT&limit=1000` é capacidade diagnóstica, não backfill integral. Nada consulta `/historicalTrades` ou `aggTrades` para fingir trades individuais completos. WS: `wss://data-stream.binance.vision/stream?streams=btcusdt@trade/btcusdt@depth@100ms`, wrapper `{stream,data}`; timestamps em milissegundos, sem `timeUnit` alternativo. [URLs públicos oficiais](https://raw.githubusercontent.com/binance/binance-spot-api-docs/263ac1aa96556af0b4da824c82a1d8cd9a0edda9/faqs/market_data_only.md).

Metadados atuais de tick/step vêm de `exchangeInfo`, não de valores fixos em produção. Falta de `PRICE_FILTER.tickSize` ou `LOT_SIZE.stepSize`, ativo divergente ou filtro inválido impede catálogo ativo. Quantidades de negócios são positivas; mínimos de criação de ordem não são usados para rejeitar execuções parciais observadas. O catálogo conserva os filtros datados para futura análise; não certifica admissibilidade de ordens. [Filtros oficiais](https://raw.githubusercontent.com/binance/binance-spot-api-docs/263ac1aa96556af0b4da824c82a1d8cd9a0edda9/filters.md).

Trade `t` identifica a execução na partição `(venue,instrument_id,trade_id)`. `p/q` são strings; `T` é horário do trade e `E` horário do evento. `m=true` deriva agressor vendedor, `m=false` comprador; a origem é `derived:buyer_is_maker`, nunca participante observado. Ausência ou tipo incorreto de `m` produz `unknown` ou erro contratual visível, conforme campo presente. Não somar book como trade. IDs não demonstram integralidade do universo; há stream `blockTrade` separado. `full_tape=False`, cobertura live de trades `partial`, até existir contrato e backfill suficientes. [Trade e depth](https://raw.githubusercontent.com/binance/binance-spot-api-docs/263ac1aa96556af0b4da824c82a1d8cd9a0edda9/web-socket-streams.md).

## Reconciliação do livro e saúde

1. `cold → syncing`: conectar WS e bufferizar deltas antes de solicitar snapshot. Marcar livro inválido até existir ponte de sequência. Snapshot tem `S=lastUpdateId`; deltas têm `[U,u]`, quantidades absolutas e zero significa remoção.
2. Regra inicial conservadora da documentação fixada: se `S < U` do primeiro delta bufferizado, solicitar snapshot novo dentro do budget. Descartar deltas com `u <= S`. Primeiro delta restante precisa satisfazer `U <= S <= u`; se ainda não existe, permanecer syncing até existir ponte ou timeout. Essa condição replica literalmente o guia fixado; não usar `S+1` silenciosamente como correção de texto. A variante usual `U <= S+1 <= u` é uma alternativa de contrato que exige decisão documentada pelo integrador antes de congelamento, preservando a prova de ausência de gap.
3. Depois da ponte: para cada delta com `u > last`, exigir `U <= last+1`; `U > last+1` é gap, invalida imediatamente, descarta estado e inicia resync. `u <= last` é stale/duplicata e não muda quantidades. Sobreposição com avanço é admissível; não exigir igualdade estrita de `U` porque uma mensagem pode conter intervalo sobreposto. `U > u`, preço inválido ou tamanho negativo invalida.
4. Aplicar os novos tamanhos por preço com Decimal; quantidade zero remove inclusive nível inexistente. Atualizar `last=u` somente após validação e aplicação atômica. Não aplicar delta parcialmente. Ordenar bids descendentes/asks ascendentes para saída; livro cruzado invalida e ressincroniza.
5. Snapshot limitado a 1000 níveis por lado não revela níveis mais profundos não alterados. `valid/live` indica continuidade do estado conhecido, não livro universal. `coverage=partial`, `depth_limit=1000`, `checksum_status=not_provided`; não inventar CRC no Binance. Teste genérico de checksum requer rejeitar hash de journal corrompido; teste de CRC de venue é inaplicável e deve aparecer como tal.
6. Desconexão, erro de contrato, fila saturada, limite de níveis/memória ou timeout invalida o livro e torna os motivos visíveis. Trade mantém janela parcial. Nunca inferir continuidade de ordem de timestamps. Reconectar cria `session_epoch` novo; um snapshot não preenche trades perdidos.

Os limites oficiais de WS são de controle/heartbeat enviados ao servidor; não limitar o volume de dados recebido a cinco ticks por segundo. Transport deve responder ping com payload igual, observar encerramento/`serverShutdown` e não iniciar conexão infinita. A cadência publicada de depth não é garantia de latência medida.

## Limites locais verificáveis

Todos são escolhas conservadoras de software, não quotas prometidas pelo provedor. O transport respeita limites oficiais mais restritivos quando presentes.

| Recurso | Padrão e reação obrigatória |
|---|---|
| Ensaio CLI | Offline sintético por padrão. `--live` explícito; duração padrão 60 s, máximo 1800 s. Nunca iniciar live durante setup, import ou CI. |
| Mensagem/JSON | Máximo 1 MiB antes de parse; JSON inválido/oversize incrementa contador e invalida canal. |
| Fila recebida | Máximo 4096 eventos e 8 MiB de bytes UTF-8, vale o primeiro limite; excesso incrementa `dropped_events/dropped_bytes`, não bloqueia owner/UI indefinidamente, invalida o epoch e força resync. |
| Sync de depth | Buffer máximo 2048 deltas/4 MiB, timeout 10 s; orçamento de 3 snapshots por tentativa e 6 por minuto, respeitando rate limit real. Falha continua inválida e volta por backoff. |
| Estado do livro | Até 5000 preços conhecidos por lado. Ao exceder, invalidar e resync; não truncar em segredo para parecer completo. Saída contextual limitada a top 20 por lado. |
| Dedup e VAP | LRU de até 20000 IDs; janela padrão 60 s, máximo 300 s; 20000 trades e 5000 níveis VAP. Evicção incrementa contador e degrada cobertura. Zero perdas não prova tape completo. |
| Memória gerenciada | Budget de 32 MiB de bytes serializados dos buffers/estado; limites de contagem também valem. Registrar uso gerenciado e pico; não anunciar limite de RSS total Python sem medir. Superação aborta epoch com `memory_budget_exceeded`. |
| REST | Timeout 10 s; rate limiter local ponderado máximo 500 weight/min; weights do perfil: exchangeInfo 20, depth1000 50, trades 25. Guardar headers `X-MBX-USED-WEIGHT-*`; `429` respeita Retry-After, `418/403/451` para sessão com motivo, sem geo/auth bypass. Não extrapolar quota IP de outros processos. |
| Reconexão | Backoff 1,2,4,8,16,30 s, jitter até 20% injetável; máximo 12 tentativas por ensaio. stop cancelável; máximo uma conexão ativa. Sem retry rápido de erro permanente. |
| Stale | Depth stale após 2000 ms sem delta; trade stale após 10000 ms sem trade, identificado como ausência de atualização, não automaticamente desconexão. Clock monotônico governa durations; exchange lag UTC é observado com incerteza. |
| Disco default | Zero payload real persistido. Fixtures sintéticas permitidas. Log de diagnóstico default somente status/counters, sem preços, tamanhos, payload ou dados pessoais. |
| Retenção opt-in | Exige `enabled=True`, `permission_ref` não vazia e declaração humana/documental da permissão para esta fonte e uso. Só fora do repo, diretório exclusivo validado. Máximo 64 MiB total, chunks até 8 MiB e idade até 24 h. Ao atingir budget, parar gravação e sinalizar; não remover paths externos. Não habilitar opt-in só porque endpoint respondeu 200. |

REST e WS jamais são chamados pelo próprio módulo ao importar. Falta da dependência de transport live produz erro acionável, preservando replay/offline. [REST e limites](https://raw.githubusercontent.com/binance/binance-spot-api-docs/263ac1aa96556af0b4da824c82a1d8cd9a0edda9/rest-api.md). Página de [termos](https://www.binance.com/en/terms) não entregou texto contratual suficiente nesta captura; permissão de retenção/redistribuição continua `unknown`, não `allowed`.

## API Python dos contratos — escritor contratos/feed

Dataclasses frozen, `tuple` para coleções, `dict[str,Any]` somente em payload/metadata extensível. Cada tipo exportável oferece `to_dict()` JSON-safe, `allow_nan=False`; valores financeiros ficam strings. `DataContractError(ValueError)` é a exceção sanitizada comum. Enums podem ser literais string validados. Sem importar tipos WIN como universais.

```python
# app/market_data_contract.py
SCHEMA_VERSION = "multimarket.v1"
def decimal_value(value: str, *, allow_zero: bool = False) -> Decimal: ...

@dataclass(frozen=True)
class InstrumentSpec:
    instrument_id: str; kind: str; symbol: str
    base_asset: str | None; quote_asset: str | None
    settlement_currency: str; tick_size: str | None; quantity_step: str | None
    multiplier: str | None = None
    expiry: str | None = None
    payoff_type: str = "spot"
    catalog_version: str = "1"
    as_of_ms: int | None = None
    metadata: dict = field(default_factory=dict)

@dataclass(frozen=True)
class SourceDescriptor:
    source_id: str; provider: str; venue: str; market: str
    endpoint_version: str; endpoints: tuple[str, ...]
    auth_required: bool; terms_url: str; retention_permission: str
    redistribution_permission: str; jurisdiction: str | None
    cadence_ms: int | None
    as_of_ms: int; evidence_refs: tuple[str, ...]

@dataclass(frozen=True)
class MarketEnvelope:
    schema_version: str; provider: str; venue: str; instrument_id: str
    event_kind: str; exchange_time_ms: int | None
    receive_time_ms: int; receive_monotonic_ns: int
    origin: str; session_epoch: str; payload_sha256: str
    sequence_namespace: str | None = None
    first_sequence: int | None = None; last_sequence: int | None = None

@dataclass(frozen=True)
class TradeEvent:
    instrument_id: str; trade_id: str; price: str; quantity: str
    trade_time_ms: int; aggressor: str; aggressor_origin: str
    envelope: MarketEnvelope

@dataclass(frozen=True)
class BookSnapshot:
    instrument_id: str; last_update_id: int
    bids: tuple[tuple[str,str], ...]; asks: tuple[tuple[str,str], ...]
    envelope: MarketEnvelope

@dataclass(frozen=True)
class BookDelta:
    instrument_id: str; first_update_id: int; last_update_id: int
    bids: tuple[tuple[str,str], ...]; asks: tuple[tuple[str,str], ...]
    envelope: MarketEnvelope

@dataclass(frozen=True)
class BookView:
    instrument_id: str; state: str; valid: bool; last_update_id: int | None
    bids: tuple[tuple[str,str], ...]; asks: tuple[tuple[str,str], ...]
    depth_limit: int; coverage: str; checksum_status: str
    reason: str = ""

@dataclass(frozen=True)
class SourceHealth:
    channel: str; connected: bool; state: str; valid: bool; stale: bool
    coverage: str; last_exchange_time_ms: int | None
    last_receive_time_ms: int | None; last_receive_monotonic_ns: int | None
    sequence_ok: bool; gaps: int; resyncs: int
    dropped_events: int; dropped_bytes: int
    reason: str; metrics: dict = field(default_factory=dict)

@dataclass(frozen=True)
class FeedBatch:
    source: SourceDescriptor; instrument: InstrumentSpec
    trades: tuple[TradeEvent, ...]; book: BookView | None
    health: tuple[SourceHealth, ...]
    warnings: tuple[str, ...] = ()
```

Preço >0, trade quantity >0, delta size >=0; rejeitar bool, float, vazio, NaN, infinidade, valores negativos, IDs ausentes ou inválidos. Aceitar precisão/tamanho lexical com limites de string 128 caracteres; cálculo por Decimal, sem arredondar para tick ou float. SHA-256 do payload do evento é do JSON canônico recebido, UTF-8, sort_keys e separators `(',',':')`; não inclui clocks locais. A origem live/synthetic/replay é obrigatória. `exchange_time_ms=None` para snapshot sem timestamp da venue, em vez de inventar hora da exchange. Instrumentos futuros/back/lay/binária são tipos de catálogo/payoff; não implicam adapters implementados. Metadata explicita campos inaplicáveis e motivos.

```python
# app/public_crypto_feed.py
@dataclass(frozen=True)
class HttpResponse:
    status: int; data: object; headers: dict[str,str]

class BinanceSpotAdapter:
    def __init__(self, *, session_epoch: str = "offline") -> None: ...
    def instrument_from_exchange_info(self, payload: dict, *, as_of_ms: int) -> InstrumentSpec: ...
    def parse_trade(self, payload: dict, *, receive_time_ms: int,
                    receive_monotonic_ns: int, origin: str = "synthetic") -> TradeEvent: ...
    def parse_snapshot(self, payload: dict, *, receive_time_ms: int,
                       receive_monotonic_ns: int, origin: str = "synthetic") -> BookSnapshot: ...
    def parse_delta(self, payload: dict, *, receive_time_ms: int,
                    receive_monotonic_ns: int, origin: str = "synthetic") -> BookDelta: ...

class LocalOrderBook:
    def __init__(self, instrument_id: str, *, max_levels: int = 5000) -> None: ...
    def buffer_delta(self, delta: BookDelta) -> bool: ...
    def install_snapshot(self, snapshot: BookSnapshot) -> bool: ...
    def apply_delta(self, delta: BookDelta) -> bool: ...
    def invalidate(self, reason: str) -> None: ...
    def view(self, *, limit: int = 20) -> BookView: ...

class PublicCryptoFeed:
    def __init__(self, *, rest_get=None, ws_factory=None, clock_utc_ms=None,
                 clock_mono_ns=None, jitter=None, limits=None) -> None: ...
    def start(self) -> None: ...
    def poll(self, *, max_events: int = 1000) -> FeedBatch: ...
    def stop(self) -> None: ...
    def status(self) -> dict: ...
```

`start()` é não bloqueante para o owner/UI; `poll()` retira no máximo max_events sem rede síncrona; `stop()` encerra worker owned e conexão em até 2 s. As seams injetadas são `rest_get(path:str, params:dict, timeout_s:float)->HttpResponse`; `ws_factory(url:str)->transport` com `recv(timeout_s)->dict|str|None`, `close()` e suporte verificável ao ping/pong; clocks retornam ints, jitter retorna fração [0,0.2]. `None` usa transport live opcional e nenhum acesso ocorre até start explícito. Contratos e replay não dependem de biblioteca WS. Exceções sanitizadas saem em health/status, sem chave/endpoint privado. Se o integrador alterar assinatura, documentar no contrato canônico antes da escrita dependente, sem mudar aceites.

## API replay/contexto — escritor exclusivo

```python
# app/market_replay.py
@dataclass(frozen=True)
class RetentionPolicy:
    enabled: bool = False
    permission_ref: str | None = None
    max_bytes: int = 64*1024*1024
    max_age_seconds: int = 86400
    max_chunk_bytes: int = 8*1024*1024

class JournalWriter:
    def __init__(self, path=None, *, policy: RetentionPolicy = RetentionPolicy()) -> None: ...
    def append(self, record: dict) -> bool: ...
    def close(self) -> None: ...
    def status(self) -> dict: ...

class ReplaySession:
    def __init__(self, records, *, verify_hashes: bool = True) -> None: ...
    def events(self): ...  # iterator[dict], ordem armazenada; não reordenar lacunas
    def status(self) -> dict: ...

class VolumeAtPrice:
    def __init__(self, instrument: InstrumentSpec, *, max_trades: int = 20000,
                 max_levels: int = 5000) -> None: ...
    def accept(self, trade: TradeEvent) -> bool: ...
    def snapshot(self, *, start_ms: int, end_ms: int) -> dict: ...

# app/multimarket_context.py
def build_multimarket_context(batch: FeedBatch, *, features: dict | None = None,
                              economics: dict | None = None, as_of_ms: int) -> dict: ...
```

Journal JSONL tem header `{schema_version,adapter_version,source,instrument,origin,permission_ref,created_at_ms}`; registros `{record_index,record_kind,payload,payload_sha256}` e registros de gap explícitos. SHA do payload canônico é verificado antes de replay; corrupção, versão desconhecida, índice faltante/fora de ordem ou mensagem excedida gera erro/health inválido, sem fill silencioso. Default disabled não cria arquivo mesmo com path; real live exige permission_ref além de opt-in e path fora do repo. Fixture `origin=synthetic` não inclui body real capturado. Retenção opt-in não cria capacidade de exportação pública.

VAP dedup por partição/ID; mesmo ID com `price,quantity,trade_time,aggressor` equivalentes é duplicata e não soma; conteúdo financeiro conflitante gera erro e invalidação. Hash diferente só por recepção ou zeros finais de decimal não é conflito de execução. Snapshot usa intervalo semiaberto `[start_ms,end_ms)`, soma quantidade base exata por preço e também notional cotado `sum(price*quantity)`, inclui `unit`, trade_count, coverage, duplicates/conflicts/evictions e missing. Book não tem método que gere volume. Aggressor unknown continua unknown. Replay sintético completo para aquela lista pode declarar `bounded_complete` com intervalo e IDs de fixture explícitos; nunca converte o resultado em full tape live.

Contexto limitado a 64 KiB JSON e no máximo top20 book/VAP; se exceder, reduzir features com `truncated=True/missing`, nunca ocultar a redução. Campos mínimos: `{schema_version,as_of_ms,objective,source,instrument,health,features,economics,missing,evidence_refs,allowed_actions,jev_comment,profit_probability,target_probability}`. `allowed_actions` default `["wait","observe"]`; `jev_comment=None`, probabilidades None sem avaliação estatística. Evidence refs são hashes/IDs públicos ou sintéticos; nada de payload bruto, segredos, conta, histórico privado ou transcript. Módulo puro: nenhum import ou chamada de cliente JEV. Integração poderá reutilizar uma chamada contextual explicitamente autorizada e delimitada; jamais uma por tick.

## API economia/relatório — escritor exclusivo

```python
# app/multimarket_economics.py
def payoff(kind: str, *, quantity: str, entry_price: str | None = None,
           exit_price: str | None = None, side: str = "buy",
           multiplier: str | None = None, odds: str | None = None,
           net_payout: str | None = None, outcome: str | None = None) -> dict: ...
def assess_candidates(candidates: list[dict], *, capital: str,
                      currency: str, as_of_ms: int) -> dict: ...
def evaluation_report(*, dataset: dict | None = None, method: dict | None = None,
                      results: dict | None = None) -> dict: ...
```

`payoff` é calculadora de cenários brutos, nunca probabilidade ou sizing. Spot/linear_future: sinal buy/sell × q × (exit-entry), multiplicador obrigatório para futuro; não usar default .20. Payoff inverso é `unsupported`, sem aproximar por linear. Back: seleção vence +s(o−1), perde −s. Lay: seleção perde +s, vence −s(o−1), responsabilidade s(o−1). Binary: win +s*b líquido contratado, lose −s, void zero; 180% total não é net_payout=1.8. Retornar `{kind,currency:null,gross_pnl,maximum_loss,liability,missing,assumptions}`; máximo de perda futuro/short sem stop/estrutura definida é None, não margem. Resultado void não assume comissão zero de operação real.

Cada candidate mapping tem `{candidate_id,instrument,quantity,payoff,costs,fx,executable_quote,liquidity,risk_mandate,product_gate,authorization_gate,coverage,as_of_ms}`. Costs precisa declarar valores em moeda, método/base, data e origem; zero só é zero explícito. FX exige par, taxa positiva, timestamp e origem; conversão necessária ausente bloqueia. Quote stale, risco insuficiente, payoff não suportado, liquidez/cobertura inadequada e produto/acesso desconhecidos bloqueiam. Resultado `{status,candidates,admissible,missing,wait,selected,profit_probability,target_probability,ruin_probability}`: q=0/wait sempre disponível; sem insumos suficientes `status=not_evaluable`, selected wait, probabilidades None. Não inventar custos WIN, câmbio 1, risco humano, margem ou P(alvo), nem recomendar lotes para recuperar perdas. Cenários sintéticos completamente especificados podem exercitar comparações determinísticas, sempre origin synthetic e separados de seleção real.

`evaluation_report` default tem `{status:"pending",sample_size:0,chronology:null,costs:null,calibration:null,intervals:null,drawdown:null,target_probability:null,ruin_probability:null,missing:[...],result_type:"protocol_only"}`. Protocolo documenta split temporal causal, purga/embargo quando houver overlap, seleção múltipla, calibração Brier/logloss, custos/execução, banca e intervalos por dependência temporal. Se `results` não traz evidência suficiente/metodologia, o módulo não calcula ou aceita automaticamente probabilidade a partir de confidence do JEV. Um relatório de fixture permanece `synthetic`, nunca lucro real ou aceite empírico AC-07. Não implementar modelo probabilístico sem dataset/critério independente.

## Seams integradas — responsabilidade exclusiva do integrador

`scripts/observe_multimarket.py`: CLI offline padrão, flags `--live --duration-seconds N`, fixtures sintéticas/replay, output diagnóstico sanitizado, retorno não zero para erro, encerramento cooperativo, sem ordens. Gravação real exige opt-in e declaração separada de retenção; o integrador pode omitir flag de gravação real nesta entrega e deixar somente seam de policy testada.

`app/desktop_service.py` e UI: seção/snapshot multimercado adicional desligado por padrão, origem e missing visíveis. Não enviar lote/quantidade cripto para WIN nem substituir capital manual. Fechamento encerra exclusivamente worker próprio, sem matar Excel/Profit. O integrador publica contrato de comandos/status usado no front e testa estado desativado, captura simulada, stale/invalid e stop. Nenhum comando expõe rota de ordens.

## Aceites imutáveis do recorte de software

O revisor deve executar testes reais do software no checkout/cópia isolada, com hash da SPEC e baseline fixos. Estes aceites detalham o recorte; não substituem AC-01–07 globais.

| ID | Evidência exigida |
|---|---|
| IM-01 | Round-trip JSON mantém decimais fracionários, units, clocks e hashes; rejeita float/bool/NaN/negative/ID inválido. Catálogo lê filtros synthetic, e baseline WIN/Excel continua equivalente sem alteração do payoff .20 existente. |
| IM-02 | Livro synthetic valida cold/sync/live, primeira ponte da política fixada, overlaps, stale/dup, zero removal, gap, reorder, snapshot antigo, crossed book, buffer overflow e resync. Nenhuma transição inválida entrega book valid. CRC venue ausente rotulado; journal checksum inválido falha. |
| IM-03 | Replay fixture conhecido soma VAP exatamente (quantidade base e notional); dedup/conflito/evicção e intervalo semiaberto exercitados. Alterações de book não criam volume, unknown não vira buy/sell, falhas de hash/índice aparecem. |
| IM-04 | Transport fake exercita disconnect, ping/pong, serverShutdown, REST429/RetryAfter, permanente403/418, timeout, limite de tentativa, fila/byte/memória/disco e stop. Contadores e health mostram perdas e não fabricam continuidade; nenhuma persistência real default. |
| IM-05 | Contexto puro, bounded, missing/evidence_refs presentes, JEV desligado funciona. Spy/fake prova zero rede na suíte/import/offline, zero JEV pago e zero endpoints privados/ordens. UI state preserva orientação observacional. |
| IM-06 | Payoffs win/lose/void por família com Decimal, lay stake100 odd5 liability400, binary b0.8 payoff80 para stake100, futuro multiplier explicit; inverso unsupported. Fees/FX/risk/product unknown bloqueiam ranking com wait, P(meta)/ruína None. |
| IM-07 | evaluation_report mantém pendência e separa synthetic/backtest/prospective/real; não promove confidence contextual ou fixture a probabilidade econômica. AC-07 fica pending sem evidência temporal/calibração/custos/amostra. |
| IM-08 | CLI default offline, live apenas explícito e bounded; serviço desligado preserva testes WIN/Excel e os inputs manuais. Teste Windows UI/worker registra escopo de plataforma; teste Python sozinho não certifica UI. |
| IM-09 | Verificação independente mapeia TODOS CM/AC, registra hashes/baseline/saída real, falhas e pendências. Não afirmar integração live, qualidade estatística, direitos, acesso Brasil ou lucro a partir de teste synthetic. |

Live opcional: uma observação curta explícita pode registrar só contagem/health/status e confirmar transporte, relógios e close. Uma sessão WS não prova piloto sustentado. Ensaio prospectivo de até 1800 s e reconexão real permanecem evidência adicional necessária antes de alegar duração/recovery/performance real; p50/p95 só medidos, não inventados. Nenhum preço/payload real deve entrar no repo. API bloqueada não autoriza mudar IP/host/jurisdição.

## Matriz preservada da especificação global

| Requisito original | Alcance deste recorte | Aceite global relacionado / status honesto |
|---|---|---|
| CM-01 fonte/endpoints/termos/jurisdição/cadência | Perfil e SourceDescriptor; unknown explícito | AC-01; retenção real/jurisdição unknown |
| CM-02 envelope/decimais/clocks/hash/namespace | Contratos e adapter | AC-01 implementável local |
| CM-03 catálogo/payoff por família | Schema tipado e fixtures; só spot tem feed | AC-01; produto derivativo/esporte/binária não validado |
| CM-04 cold/sync/live/gap/checksum | Livro Binance; sem checksum venue disponível | AC-02 implementável por contrato; CRC venue N/A declarado |
| CM-05 dedup/VAP/agressor/cobertura | Trades únicos, janela e derived/unknown | AC-03 local, cobertura live parcial |
| CM-06 saúde por canal/janela, faltas | Health e métricas; full_tape False | AC-02/04 locais; nenhum backfill completo |
| CM-07 retenção conforme direito/replay/hash | Disabled real; fixture e opt-in gate | AC-03/04 locais; direitos reais pendentes |
| CM-08 quota/heartbeat/backoff/queue/budgets | Limits/fakes/CLI finite | AC-04 local; piloto prolongado/performance real pendente |
| CM-09 contexto sanitizado/JEV separado | Módulo puro, JEV opcional pelo integrador | AC-05 local; sem paid CI |
| CM-10 payoff/custo/FX/liquidez/capital/q0 | Calculadoras/gates/relatório, não operação | AC-06 local sintético; comparação real pending |
| CM-11 cronologia/OOS/calibração/banca/incerteza | Protocolo/report pending, nenhuma estimação | **AC-07 pending**, não satisfeito por software |
| CM-12 compatibilidade WIN/.20/ints/ordens | Módulos separados, regressões baseline | AC-01/06, sem rota de ordens |

## Grafo de tarefas e ownership

EM-01 perfil/spec (este documento) → EM-02 contratos → EM-03 feed → EM-04 replay → EM-05 integração. Para concorrência, depois de congelar as assinaturas de EM-02, replay/contexto e economia/relatório podem ser escritos isoladamente contra fixtures dessas assinaturas; integração depende das três entregas reais.

1. Escritor A: somente `app/market_data_contract.py`, `app/public_crypto_feed.py`, testes próprios de contrato/feed. EM-02/03, IM-01/02/04. Não edita serviço/UI/dependências compartilhadas.
2. Escritor B: somente `app/market_replay.py`, `app/multimarket_context.py`, fixtures synthetic e testes próprios. EM-04, contexto CM-09, IM-03/04/05. Não edita contratos; reporta divergência de seam.
3. Escritor C: somente `app/multimarket_economics.py`, testes próprios e protocolo/relatório. Recorte EM-08/09 software, IM-06/07. Não declara EM-08 operacional/EM-09 empírico completos.

Integrador sozinho edita serviço, CLI, UI, dependências/build e docs compartilhados; integra em branch única sem incluir mudanças preexistentes de terceiros. Revisor independente vem após implementação/testes com três slots auxiliares respeitados. EM-06/07 seguem pesquisa/licença/produto; EM-10 depende de dados/método real; EM-11/12 pendentes conforme acesso/admissibilidade. Contatos, compra ou operação não são tarefas elegíveis desta entrega.

## Dependências externas que continuam abertas

Direitos de armazenamento/redistribuição reais; disponibilidade WS/IP do Brasil; SDK/licença/custos B3; contrato e permissões de derivativos cripto; alternativa de API sports Brasil; admissibilidade binária e settlement; custo/FX/margem/risco humanos atuais; dataset representativo e método congelado para AC-07. A falta desses itens não bloqueia módulos puros, fixtures ou observer público explicitamente iniciado, mas bloqueia as respectivas alegações/ações econômicas.

Baseline de pesquisa `da96c6ad4187030a98c4daa86a6b96e1e5b809a9`; integrador deve registrar seu checkout atual antes do freeze. Hashes, trechos literais das fontes e consultas estão em `findings.md`. A aprovação/revisão independente e evidência de implementação são responsabilidade separada do autor desta SPEC.

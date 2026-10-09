export type UnknownRecord = Record<string, unknown>;

export interface MultimarketWorkspace {
  workspace_id: string;
  instrument_id: string;
  source_id: string;
  symbol: string;
  venue: string;
  segment: string;
  status: string;
  expiry_at_ms?: number | null;
}

export interface MultimarketSnapshot extends UnknownRecord {
  schema_version: 3;
  sequence: number;
  generated_at_ms: number;
  selected_workspace_id: string | null;
  workspaces: MultimarketWorkspace[];
  selected: UnknownRecord | null;
  scheduler: UnknownRecord;
  recording: UnknownRecord;
  metrics: UnknownRecord;
  gates: UnknownRecord;
  orders_enabled: false;
}

export type MultimarketRun = (method: string, params: UnknownRecord) => Promise<MultimarketSnapshot>;

export interface ProjectedSelected extends UnknownRecord {
  identity: MultimarketWorkspace & { epoch: number; metadata_version: string };
  market: UnknownRecord & { quote: (UnknownRecord & { age_ms: number }) | null };
  context: (UnknownRecord & { age_ms: number }) | null;
  contextStatus: string;
  decision: UnknownRecord & { action: 'wait'; reason: string; profit_probability: null; quantity: '0'; net_profit: null };
}

export interface MultimarketProjection {
  diagnostic: string | null;
  workspaces: MultimarketWorkspace[];
  selected: ProjectedSelected | null;
  context: ProjectedSelected['context'];
  ordersEnabled: false;
  scheduler: UnknownRecord | null;
  recording: UnknownRecord | null;
  metrics: UnknownRecord | null;
  gates: UnknownRecord | null;
}

type AgeAnchor = { identity: string; baseAgeMs: number; atMs: number };
const CONTEXT_VALIDITY_MS = 2_000;
const DECIMAL = /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/;

const isRecord = (value: unknown): value is UnknownRecord =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

const isString = (value: unknown): value is string => typeof value === 'string' && value.trim().length > 0;
const isFiniteNumber = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value);
const isAge = (value: unknown): value is number => isFiniteNumber(value) && value >= 0;
const isDecimal = (value: unknown): value is string => typeof value === 'string' && DECIMAL.test(value);
const safeText = (value: unknown, fallback = 'Motivo não informado'): string =>
  typeof value === 'string' && value.trim() ? value.slice(0, 240) : fallback;

function validWorkspace(value: unknown): value is MultimarketWorkspace {
  return isRecord(value) && ['workspace_id', 'instrument_id', 'source_id', 'symbol', 'venue', 'segment', 'status'].every(key => isString(value[key]));
}

export function workspaceIdentity(workspace: Pick<MultimarketWorkspace, 'workspace_id' | 'instrument_id' | 'source_id' | 'symbol' | 'venue' | 'segment'> & { expiry_at_ms?: number | null }): string {
  return JSON.stringify([
    workspace.workspace_id,
    workspace.venue,
    workspace.segment,
    workspace.instrument_id,
    workspace.symbol,
    workspace.expiry_at_ms ?? null,
    workspace.source_id,
  ]);
}

function snapshotFailure(input: unknown): string | null {
  if (!isRecord(input)) return 'Snapshot inválido: resposta não é um objeto.';
  if (input.schema_version !== 3) return `Snapshot incompatível: schema ${String(input.schema_version ?? 'ausente')}; esperado schema 3.`;
  if (!isFiniteNumber(input.sequence) || !isFiniteNumber(input.generated_at_ms)) return 'Snapshot inválido: sequência ou relógio de geração ausente.';
  if (input.selected_workspace_id !== null && !isString(input.selected_workspace_id)) return 'Snapshot inválido: identidade do workspace selecionado ausente.';
  if (!Array.isArray(input.workspaces) || !input.workspaces.every(validWorkspace)) return 'Snapshot inválido: registro de workspaces incompleto.';
  if (!isRecord(input.scheduler) || !isRecord(input.recording) || !isRecord(input.metrics) || !isRecord(input.gates)) return 'Snapshot inválido: scheduler, gravação, métricas ou gates ausentes.';
  if (input.orders_enabled !== false) return 'Snapshot incompatível: a interface exige ordens desabilitadas.';
  if (input.selected === null) {
    if (input.selected_workspace_id !== null) return 'Snapshot inválido: workspace selecionado sem estado de instrumento.';
    return null;
  }
  if (!isRecord(input.selected)) return 'Snapshot inválido: estado selecionado ausente.';
  const selected = input.selected;
  const instrument = selected.instrument;
  const source = selected.source;
  const market = selected.market;
  if (!isString(selected.workspace_id) || !isString(selected.instrument_id) || !isString(selected.source_id) || !isRecord(instrument) || !isRecord(source) || !isRecord(market)) return 'Snapshot inválido: identidade, instrumento, fonte ou mercado ausente.';
  if (selected.workspace_id !== input.selected_workspace_id) return 'Snapshot inválido: workspace selecionado não corresponde ao estado de mercado.';
  if (instrument.instrument_id !== selected.instrument_id || !isString(instrument.venue) || !isString(instrument.segment) || !isString(instrument.symbol) || !isString(instrument.metadata_version)) return 'Snapshot inválido: identidade ou metadata do instrumento incompatível.';
  if (!isString(source.source_id) || source.source_id !== selected.source_id) return 'Snapshot inválido: identidade da fonte incompatível.';
  if (!isFiniteNumber(market.epoch) || !isRecord(market.health) || !isRecord(market.features) || !Array.isArray(market.recent_trades) || !Array.isArray(market.warnings)) return 'Snapshot inválido: saúde, features, negócios recentes ou avisos ausentes.';
  const domainHealth = market.health;
  if (!['quote', 'trades', 'book'].every(domain => isRecord(domainHealth[domain]))) return 'Snapshot inválido: saúde por domínio incompleta.';
  if (market.quote !== null && !isRecord(market.quote)) return 'Snapshot inválido: cotação não está no formato esperado.';
  if (!isRecord(selected.decision) || !isString(selected.decision.reason)) return 'Snapshot inválido: decisão de espera sem justificativa.';
  if (selected.context !== null && !isRecord(selected.context)) return 'Snapshot inválido: contexto não está no formato esperado.';
  const workspace = input.workspaces.find((item: MultimarketWorkspace) => item.workspace_id === selected.workspace_id);
  if (!workspace || workspace.instrument_id !== selected.instrument_id || workspace.source_id !== selected.source_id) return 'Snapshot inválido: workspace não corresponde à venue e à fonte selecionadas.';
  return null;
}

function quoteIdentity(selected: UnknownRecord, quote: UnknownRecord): string {
  const instrument = selected.instrument as UnknownRecord;
  const market = selected.market as UnknownRecord;
  return JSON.stringify([
    selected.workspace_id,
    selected.instrument_id,
    selected.source_id,
    market.epoch,
    instrument.metadata_version,
    quote.event_id ?? quote.sequence ?? null,
    quote.bid,
    quote.ask,
    quote.bid_quantity,
    quote.ask_quantity,
    quote.market_ts_ms,
    quote.received_at_ms,
  ]);
}

function tradeIdentity(selectionKey: string, trade: UnknownRecord): string {
  return JSON.stringify([
    selectionKey,
    trade.event_id ?? trade.id ?? null,
    trade.sequence ?? null,
    trade.market_ts_ms ?? null,
    trade.received_at_ms ?? null,
    trade.price ?? null,
    trade.quantity ?? null,
    trade.aggressor ?? null,
  ]);
}

function healthIdentity(domain: 'quote' | 'trades' | 'book', selectionKey: string, selected: UnknownRecord, health: UnknownRecord, market: UnknownRecord): string {
  const domainState = isRecord(market.health) && isRecord(market.health[domain]) ? market.health[domain] : {};
  const evidence = domain === 'quote'
    ? isRecord(market.quote) ? quoteIdentity(selected, market.quote) : null
    : domain === 'trades'
      ? (() => {
          const trades = Array.isArray(market.recent_trades) ? market.recent_trades.filter(isRecord) : [];
          const latest = trades.at(-1);
          return JSON.stringify([market.features && isRecord(market.features) ? market.features.event_range ?? null : null, latest ? tradeIdentity(selectionKey, latest) : null]);
        })()
      : (() => {
          const book = isRecord(market.book) ? market.book : isRecord(market.book_state) ? market.book_state : null;
          return book ? JSON.stringify([book.event_id ?? null, book.sequence ?? null, book.market_ts_ms ?? null, book.received_at_ms ?? null]) : null;
        })();
  return JSON.stringify([
    selectionKey,
    evidence,
    domainState.event_id ?? health.event_id ?? null,
    domainState.sequence ?? health.sequence ?? null,
    domainState.received_at_ms ?? health.received_at_ms ?? null,
    domainState.status ?? null,
    domainState.reason ?? null,
  ]);
}

function accountIdentity(selectionKey: string, account: UnknownRecord): string {
  return JSON.stringify([selectionKey, account.account_id ?? null, account.revision ?? null, account.asof_ms ?? null]);
}

function contextStamp(context: UnknownRecord): string {
  return JSON.stringify([
    context.origin_monotonic_ns ?? null,
    context.questions_version ?? null,
    context.model ?? null,
    context.answers ?? null,
  ]);
}

function contextMismatch(context: UnknownRecord, selected: UnknownRecord): string | null {
  const identity = isRecord(context.identity) ? context.identity : context;
  const instrument = selected.instrument as UnknownRecord;
  const market = selected.market as UnknownRecord;
  const expected: Record<string, unknown> = {
    workspace_id: selected.workspace_id,
    instrument_id: selected.instrument_id,
    source_id: selected.source_id,
    epoch: market.epoch,
    metadata_version: instrument.metadata_version,
  };
  for (const [field, expectedValue] of Object.entries(expected)) {
    if (identity[field] !== undefined && identity[field] !== expectedValue) return `Contexto descartado: identidade divergente (${field}).`;
  }
  return null;
}

function ageFromAnchor(current: AgeAnchor | null, identity: string, rawAge: unknown, nowMs: number): { anchor: AgeAnchor | null; age: number | null } {
  if (!isAge(rawAge)) return { anchor: null, age: null };
  if (!current || current.identity !== identity) {
    return { anchor: { identity, baseAgeMs: rawAge, atMs: nowMs }, age: rawAge };
  }
  const progressed = current.baseAgeMs + Math.max(0, nowMs - current.atMs);
  const age = Math.max(progressed, rawAge);
  return { anchor: { identity, baseAgeMs: age, atMs: nowMs }, age };
}

export class MultimarketProjector {
  private quoteAnchor: AgeAnchor | null = null;
  private contextAnchor: AgeAnchor | null = null;
  private readonly healthAnchors = new Map<string, AgeAnchor>();
  private readonly tradeAnchors = new Map<string, AgeAnchor>();
  private accountAnchor: AgeAnchor | null = null;
  private selectedIdentity: string | null = null;
  private lastContextStamp: string | null = null;

  private clearAges(): void {
    this.quoteAnchor = null;
    this.contextAnchor = null;
    this.healthAnchors.clear();
    this.tradeAnchors.clear();
    this.accountAnchor = null;
  }

  project(input: unknown, nowMonotonicMs: number): MultimarketProjection {
    const failure = snapshotFailure(input);
    if (failure) {
      this.clearAges();
      this.selectedIdentity = null;
      this.lastContextStamp = null;
      return { diagnostic: failure, workspaces: [], selected: null, context: null, ordersEnabled: false, scheduler: null, recording: null, metrics: null, gates: null };
    }
    if (!isRecord(input)) throw new Error('unreachable snapshot validation state');
    const workspaces = input.workspaces as MultimarketWorkspace[];
    if (input.selected === null) {
      this.clearAges();
      this.selectedIdentity = null;
      this.lastContextStamp = null;
      return { diagnostic: null, workspaces, selected: null, context: null, ordersEnabled: false, scheduler: input.scheduler as UnknownRecord, recording: input.recording as UnknownRecord, metrics: input.metrics as UnknownRecord, gates: input.gates as UnknownRecord };
    }

    const raw = input.selected as UnknownRecord;
    const instrument = raw.instrument as UnknownRecord;
    const market = raw.market as UnknownRecord;
    const workspace = workspaces.find(item => item.workspace_id === raw.workspace_id)!;
    const identity = {
      ...workspace,
      expiry_at_ms: typeof instrument.expiry_at_ms === 'number' ? instrument.expiry_at_ms : null,
      epoch: market.epoch as number,
      metadata_version: instrument.metadata_version as string,
    };
    const selectionKey = JSON.stringify([
      workspaceIdentity(identity),
      identity.epoch,
      identity.metadata_version,
    ]);
    const selectionChanged = this.selectedIdentity !== null && this.selectedIdentity !== selectionKey;
    const previousContextStamp = this.lastContextStamp;
    if (selectionChanged) {
      this.clearAges();
      this.lastContextStamp = null;
    }
    this.selectedIdentity = selectionKey;

    let projectedQuote: (UnknownRecord & { age_ms: number }) | null = null;
    let quoteWarning: string | null = null;
    if (isRecord(market.quote)) {
      const quote = market.quote;
      if (![quote.bid, quote.ask, quote.bid_quantity, quote.ask_quantity].every(isDecimal) || !isFiniteNumber(quote.market_ts_ms) || !isFiniteNumber(quote.received_at_ms) || !isAge(quote.age_ms)) {
        quoteWarning = 'Cotação removida: campos ou clocks incompatíveis.';
        this.quoteAnchor = null;
      } else {
        const age = ageFromAnchor(this.quoteAnchor, quoteIdentity(raw, quote), quote.age_ms, nowMonotonicMs);
        this.quoteAnchor = age.anchor;
        projectedQuote = { ...quote, age_ms: age.age ?? quote.age_ms };
      }
    } else {
      this.quoteAnchor = null;
    }

    const projectedHealth: UnknownRecord = {};
    const domainHealth = market.health as UnknownRecord;
    for (const domain of ['quote', 'trades', 'book'] as const) {
      const rawHealth = domainHealth[domain] as UnknownRecord;
      const age = ageFromAnchor(this.healthAnchors.get(domain) ?? null, healthIdentity(domain, selectionKey, raw, rawHealth, market), rawHealth.age_ms, nowMonotonicMs);
      if (age.anchor) this.healthAnchors.set(domain, age.anchor);
      else this.healthAnchors.delete(domain);
      projectedHealth[domain] = { ...rawHealth, age_ms: age.age };
    }

    const currentTradeIdentities = new Set<string>();
    const recentTrades = market.recent_trades as unknown[];
    const projectedTrades = recentTrades.map((item: unknown) => {
      if (!isRecord(item) || !isAge(item.age_ms)) return item;
      const identity = tradeIdentity(selectionKey, item);
      currentTradeIdentities.add(identity);
      const age = ageFromAnchor(this.tradeAnchors.get(identity) ?? null, identity, item.age_ms, nowMonotonicMs);
      if (age.anchor) this.tradeAnchors.set(identity, age.anchor);
      return { ...item, age_ms: age.age ?? item.age_ms };
    });
    for (const identity of this.tradeAnchors.keys()) {
      if (!currentTradeIdentities.has(identity)) this.tradeAnchors.delete(identity);
    }

    const rawAccount = isRecord(raw.account) ? raw.account : null;
    let projectedAccount: UnknownRecord | null = rawAccount;
    if (rawAccount && isAge(rawAccount.age_ms)) {
      const age = ageFromAnchor(this.accountAnchor, accountIdentity(selectionKey, rawAccount), rawAccount.age_ms, nowMonotonicMs);
      this.accountAnchor = age.anchor;
      projectedAccount = { ...rawAccount, age_ms: age.age ?? rawAccount.age_ms };
    } else {
      this.accountAnchor = null;
      if (rawAccount) projectedAccount = { ...rawAccount, age_ms: null };
    }

    const rawContext = isRecord(raw.context) ? raw.context : null;
    let projectedContext: (UnknownRecord & { age_ms: number }) | null = null;
    let contextStatus = rawContext ? safeText(rawContext.status, 'Contexto recebido') : 'JEV desabilitado ou sem resposta';
    if (rawContext) {
      const mismatch = contextMismatch(rawContext, raw);
      const contextIdentity = selectionKey + ':' + contextStamp(rawContext);
      const contextIdentityRecord = isRecord(rawContext.identity) ? rawContext.identity : null;
      const hasIdentity = contextIdentityRecord !== null && ['workspace_id', 'instrument_id', 'source_id', 'epoch', 'metadata_version'].every(field => contextIdentityRecord[field] !== undefined);
      const reusedAcrossSelection = selectionChanged && !hasIdentity && contextStamp(rawContext) === previousContextStamp;
      if (mismatch || reusedAcrossSelection) {
        this.contextAnchor = null;
        contextStatus = mismatch ?? 'Contexto descartado após troca de workspace: aguarda identidade nova.';
      } else if (isAge(rawContext.age_ms) && isAge(rawContext.origin_monotonic_ns) && Array.isArray(rawContext.answers)) {
        const age = ageFromAnchor(this.contextAnchor, contextIdentity, rawContext.age_ms, nowMonotonicMs);
        this.contextAnchor = age.anchor;
        if (age.age !== null && age.age <= CONTEXT_VALIDITY_MS && rawContext.financial_probability === null) {
          projectedContext = { ...rawContext, age_ms: age.age, answers: rawContext.answers.slice(0, 12) };
          contextStatus = safeText(rawContext.status, 'Contexto recebido');
          this.lastContextStamp = contextStamp(rawContext);
        } else {
          this.contextAnchor = null;
          contextStatus = rawContext.financial_probability !== null ? 'Contexto descartado: probabilidade financeira não autorizada.' : 'Contexto expirado.';
        }
      } else {
        this.contextAnchor = null;
        contextStatus = 'Contexto descartado: clock ou respostas incompatíveis.';
      }
    } else {
      this.contextAnchor = null;
      this.lastContextStamp = null;
    }

    const decision = raw.decision as UnknownRecord;
    const warnings = Array.isArray(market.warnings) ? market.warnings.map(value => safeText(value, 'Aviso de mercado')) : [];
    if (quoteWarning) warnings.unshift(quoteWarning);
    const projectedMarket = { ...market, quote: projectedQuote, recent_trades: projectedTrades, health: projectedHealth, warnings };
    const reason = decision.action === 'wait' ? safeText(decision.reason) : 'A interface mantém AGUARDAR; ordens não fazem parte deste piloto.';
    const projectedDecision = { ...decision, action: 'wait' as const, reason, profit_probability: null, quantity: '0' as const, net_profit: null };
    const selected: ProjectedSelected = {
      ...raw,
      identity,
      market: projectedMarket,
      account: projectedAccount,
      context: projectedContext,
      contextStatus,
      decision: projectedDecision,
    };
    return {
      diagnostic: null,
      workspaces,
      selected,
      context: projectedContext,
      ordersEnabled: false,
      scheduler: input.scheduler as UnknownRecord,
      recording: input.recording as UnknownRecord,
      metrics: input.metrics as UnknownRecord,
      gates: input.gates as UnknownRecord,
    };
  }
}

export function createMultimarketProjector(): MultimarketProjector {
  return new MultimarketProjector();
}

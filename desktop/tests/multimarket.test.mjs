import test from 'node:test';
import assert from 'node:assert/strict';
import { contextAnswerRows, createMultimarketProjector, gatePresentation, metricsExportPayload, multimarketCommandMethod, schedulerErrorMessage, warningMessages, workspaceIdentity } from '../src/multimarketModel.ts';

const evaluationIdentity = () => ({
  workspace_id: 'spot-btc',
  instrument_id: 'binance:spot:BTCUSDT',
  source_id: 'binance_public_spot',
  epoch: 1,
  metadata_version: 'exchange-info-7',
  feature_version: 'features-v1',
  question_version: 'mm-context-v1',
  cost_revision: null,
  account_id: null,
  account_revision: null,
  selection_revision: 1,
  event_range: null,
  received_monotonic_ns: 5000,
});

const snapshot = (overrides = {}) => {
  const selected = {
    workspace_id: 'spot-btc',
    instrument_id: 'binance:spot:BTCUSDT',
    source_id: 'binance_public_spot',
    instrument: { instrument_id: 'binance:spot:BTCUSDT', venue: 'BINANCE', segment: 'SPOT', symbol: 'BTCUSDT', metadata_version: 'exchange-info-7', price_tick: '0.01', quantity_step: '0.00001', quantity_min: '0.00001', minimum_notional: null, contract_multiplier: '1', quote_currency: 'USDT', status: 'trading', constraints_verified: true },
    source: { source_id: 'binance_public_spot', version: '1', quote: true, trades: true, book: false, account: false, trade_semantics: 'individual', side_semantics: 'aggressor', sequence_scope: 'unknown', book_mode: 'unavailable', full_tape: false, retention: 'unknown', export: 'unknown' },
    market: {
      epoch: 1,
      quote: { bid: '60000.00', ask: '60000.10', bid_quantity: '0.2', ask_quantity: '0.3', market_ts_ms: 10000, received_at_ms: 10010, age_ms: 0 },
      recent_trades: [],
      health: { quote: { status: 'live', reason: null, age_ms: 0 }, trades: { status: 'live', reason: null, age_ms: 0 }, book: { status: 'unavailable', reason: 'Binance pilot has no L2 book', age_ms: null } },
      features: { version: 'features-v1', trade_count: 0, buy_quantity: '0', sell_quantity: '0', delta_quantity: '0', spread: '0.10', event_range: null },
      warnings: [],
      full_tape: false,
    },
    account: null,
    decision: { action: 'wait', reason: 'No approved financial model', profit_probability: null, quantity: '0', net_profit: null },
    evaluation_identity: evaluationIdentity(),
    context: { status: 'complete', model: 'jev-1.13.0', questions_version: 'mm-context-v1', origin_monotonic_ns: 5000, age_ms: 100, answers: {
      direction: { type: 'choice', choice: 'observe_buy', probabilities: { wait: 0.05, observe_buy: 0.9, observe_sell: 0.05 }, confidence: 0.85 },
      context_support: { type: 'noul', noul: 0.72 },
      context_contradiction: { type: 'noul', noul: 0.18 },
      evidence_sufficiency: { type: 'noul', noul: 0.8 },
    }, financial_probability: null, identity: evaluationIdentity() },
    costs: null,
  };
  return {
    schema_version: 3,
    sequence: 10,
    generated_at_ms: 10010,
    selected_workspace_id: 'spot-btc',
    workspaces: [{ workspace_id: 'spot-btc', instrument_id: 'binance:spot:BTCUSDT', source_id: 'binance_public_spot', symbol: 'BTCUSDT', venue: 'BINANCE', segment: 'SPOT', status: 'live' }],
    selected,
    scheduler: { enabled: false, status: 'disabled', pending: 0, queued: 0, model: 'jev-1.13.0', question_version: 'mm-context-v1', error: null },
    recording: { status: 'disabled', reason: 'Retention policy unknown' },
    metrics: { events: 0, duplicates: 0, rejected: 0, overflow: 0, process_p95_ms: null, market_lag_ms: null, rss_bytes: null, gpu_bytes: null },
    gates: { b3: 'blocked', private_account: 'blocked', financial_model: 'blocked', native_evidence: 'not_measured' },
    orders_enabled: false,
    ...overrides,
  };
};

test('valid Snapshot3 keeps domain identity and ages source data from a monotonic client receipt', () => {
  const projector = createMultimarketProjector();
  const first = projector.project(snapshot(), 1000);
  const later = projector.project(snapshot({ selected: { ...snapshot().selected, market: { ...snapshot().selected.market, quote: { ...snapshot().selected.market.quote, age_ms: 0 } } } }), 2500);

  assert.equal(first.diagnostic, null);
  assert.equal(first.selected.identity.workspace_id, 'spot-btc');
  assert.equal(first.selected.market.quote.age_ms, 0);
  assert.equal(later.selected.market.quote.age_ms, 1500);
  assert.equal(later.selected.context.age_ms, 1600);
  assert.equal(later.selected.market.quote.market_ts_ms, 10000);
  assert.equal(first.selected.decision.profit_probability, null);
  assert.equal(first.ordersEnabled, false);
});

test('public bookTicker quote stays usable when exchange market time is unknown', () => {
  const projector = createMultimarketProjector();
  const input = snapshot();
  input.selected.market.quote.market_ts_ms = null;
  const first = projector.project(input, 1000);
  const laterInput = snapshot();
  laterInput.selected.market.quote.market_ts_ms = null;
  const later = projector.project(laterInput, 2400);

  assert.equal(first.selected.market.quote.market_ts_ms, null);
  assert.equal(first.selected.market.quote.age_ms, 0);
  assert.equal(later.selected.market.quote.market_ts_ms, null);
  assert.equal(later.selected.market.quote.age_ms, 1400);
});

test('market domains, individual trades, and manual account age without snapshot renewal', () => {
  const projector = createMultimarketProjector();
  const firstSnapshot = snapshot();
  const trade = { event_id: 'trade-1', price: '60000.05', quantity: '0.2', aggressor: 'buy', market_ts_ms: 10000, received_at_ms: 10010, age_ms: 100 };
  firstSnapshot.selected.market.recent_trades = [trade];
  firstSnapshot.selected.market.health.trades.age_ms = 100;
  firstSnapshot.selected.account = { account_id: 'manual-ledger', revision: 2, asof_ms: 9000, age_ms: 100, balances: { USDT: '5.00' }, positions: {} };
  projector.project(firstSnapshot, 1000);

  const laterSnapshot = snapshot();
  laterSnapshot.selected.market.recent_trades = [{ ...trade, age_ms: 0 }];
  laterSnapshot.selected.market.health.trades.age_ms = 0;
  laterSnapshot.selected.account = { ...firstSnapshot.selected.account, age_ms: 0 };
  const later = projector.project(laterSnapshot, 2500);

  assert.equal(later.selected.market.quote.age_ms, 1500);
  assert.equal(later.selected.market.health.quote.age_ms, 1500);
  assert.equal(later.selected.market.health.trades.age_ms, 1600);
  assert.equal(later.selected.market.recent_trades[0].age_ms, 1600);
  assert.equal(later.selected.account.age_ms, 1600);
});

test('a malformed or incompatible snapshot exposes a diagnostic and removes contextual data', () => {
  const projector = createMultimarketProjector();
  const invalid = projector.project(snapshot({ schema_version: 2 }), 1000);

  assert.match(invalid.diagnostic, /schema/i);
  assert.equal(invalid.selected, null);
  assert.equal(invalid.context, null);
});

test('context from another workspace is discarded after a fast workspace switch', () => {
  const projector = createMultimarketProjector();
  projector.project(snapshot(), 1000);

  const otherWorkspace = snapshot({
    selected_workspace_id: 'other-venue-btc',
    workspaces: [{ workspace_id: 'other-venue-btc', instrument_id: 'other:spot:BTCUSDT', source_id: 'other_public_spot', symbol: 'BTCUSDT', venue: 'OTHER', segment: 'SPOT', status: 'live' }],
    selected: {
      ...snapshot().selected,
      workspace_id: 'other-venue-btc',
      instrument_id: 'other:spot:BTCUSDT',
      source_id: 'other_public_spot',
      instrument: { ...snapshot().selected.instrument, instrument_id: 'other:spot:BTCUSDT', venue: 'OTHER', metadata_version: 'other-1' },
      source: { ...snapshot().selected.source, source_id: 'other_public_spot' },
      evaluation_identity: { ...evaluationIdentity(), workspace_id: 'other-venue-btc', instrument_id: 'other:spot:BTCUSDT', source_id: 'other_public_spot', metadata_version: 'other-1' },
      context: { ...snapshot().selected.context, identity: evaluationIdentity() },
    },
  });
  const projected = projector.project(otherWorkspace, 1100);

  assert.match(projected.selected.identity.workspace_id, /other-venue-btc/);
  assert.equal(projected.selected.context, null);
  assert.match(projected.selected.contextStatus, /identity|workspace/i);
});

test('context requires a complete exact evaluation identity for every dependency', () => {
  const fields = Object.keys(evaluationIdentity());
  for (const field of fields) {
    const selected = snapshot().selected;
    const currentValue = selected.context.identity[field];
    const changedValue = field === 'event_range' ? { from: 1, to: 2 }
      : field === 'account_id' || field === 'cost_revision' || field === 'account_revision' ? 'revision-2'
        : ['epoch', 'selection_revision', 'received_monotonic_ns'].includes(field) ? currentValue + 1
          : `${currentValue}-changed`;
    selected.context.identity = { ...selected.context.identity, [field]: changedValue };
    const projected = createMultimarketProjector().project({ ...snapshot(), selected }, 1000);
    assert.equal(projected.selected.context, null, `context must be removed when ${field} changes`);
    assert.match(projected.selected.contextStatus, /identidade|divergente|incompleta/i, `context status should explain ${field}`);
  }
  for (const field of fields) {
    const selected = snapshot().selected;
    delete selected.context.identity[field];
    const projected = createMultimarketProjector().project({ ...snapshot(), selected }, 1000);
    assert.equal(projected.selected.context, null, `context must be removed when ${field} is missing`);
  }
  for (const field of fields) {
    const selected = snapshot().selected;
    delete selected.evaluation_identity[field];
    const projected = createMultimarketProjector().project({ ...snapshot(), selected }, 1000);
    assert.equal(projected.selected.context, null, `context must be removed when expected ${field} is missing`);
  }

  const selectedWithoutEvaluationIdentity = snapshot().selected;
  delete selectedWithoutEvaluationIdentity.evaluation_identity;
  const missingExpected = createMultimarketProjector().project({ ...snapshot(), selected: selectedWithoutEvaluationIdentity }, 1000);
  assert.equal(missingExpected.selected.context, null);

  const selectedWithoutContextIdentity = snapshot().selected;
  delete selectedWithoutContextIdentity.context.identity;
  const missingActual = createMultimarketProjector().project({ ...snapshot(), selected: selectedWithoutContextIdentity }, 1000);
  assert.equal(missingActual.selected.context, null);
});

test('contextual answers use readable labels and explicitly contextual percentages', () => {
  const projected = createMultimarketProjector().project(snapshot(), 1000);
  const rows = contextAnswerRows(projected.selected.context.answers);

  assert.deepEqual(rows, [
    'Leitura contextual: observar compra · confiança contextual 85% (não é probabilidade de lucro).',
    'Apoio contextual: 72% (escala contextual, não probabilidade de lucro).',
    'Contradição contextual: 18% (escala contextual, não probabilidade de lucro).',
    'Evidência suficiente para avaliar: 80% (escala contextual, não probabilidade de lucro).',
  ]);
  assert.deepEqual(contextAnswerRows([{ kind: 'Choice', value: 'raw payload' }]), []);

  const unknownChoice = snapshot();
  unknownChoice.selected.context.answers.direction.choice = 'arbitrary-provider-text';
  const rejected = createMultimarketProjector().project(unknownChoice, 1000);
  assert.equal(rejected.selected.context, null, 'unknown choice labels must not leave an empty valid context panel');
});

test('scheduler errors keep license, timeout, and unavailable blockers visible as plain text', () => {
  assert.equal(schedulerErrorMessage('license_required'), 'A licença/configuração do JEV bloqueia novas respostas.');
  assert.equal(schedulerErrorMessage('timeout'), 'O JEV excedeu o tempo limite; não há resposta contextual válida.');
  assert.equal(schedulerErrorMessage('unavailable'), 'JEV indisponível; decisões financeiras continuam bloqueadas.');
  assert.equal(schedulerErrorMessage({ reason: 'provider unavailable' }), 'JEV indisponível; decisões financeiras continuam bloqueadas.');
  assert.equal(schedulerErrorMessage({ code: null, reason: 'timeout' }), 'O JEV excedeu o tempo limite; não há resposta contextual válida.');
  assert.equal(schedulerErrorMessage({ code: '', message: 'license required' }), 'A licença/configuração do JEV bloqueia novas respostas.');
  assert.equal(schedulerErrorMessage(null), null);
});

test('gate objects preserve backend status and reason for cockpit presentation', () => {
  assert.deepEqual(gatePresentation({ status: 'blocked', reason: 'entitlement_required' }), {
    status: 'blocked', reason: 'entitlement_required',
  });
  assert.deepEqual(gatePresentation({ status: 'not_measured', reason: null }), {
    status: 'not_measured', reason: null,
  });
  assert.deepEqual(gatePresentation('allowed'), { status: 'allowed', reason: null });
});

test('projected market warnings preserve reason strings from backend warning objects', () => {
  assert.deepEqual(warningMessages([
    { domain: 'quote', reason: 'quote_stale' },
    { domain: 'trades', reason: 'trade_sequence_gap' },
    'source_partial',
    { domain: 'book', reason: '' },
  ]), ['quote_stale', 'trade_sequence_gap', 'source_partial', 'Aviso de mercado']);
});

test('cockpit commands use the transport multimarket namespace', () => {
  for (const action of ['jev.set_enabled', 'account.reconcile', 'costs.update', 'recording.set', 'replay', 'metrics']) {
    assert.equal(multimarketCommandMethod(action), `multimarket.${action}`);
  }
  assert.equal(multimarketCommandMethod('multimarket.discover'), 'multimarket.discover');
});

test('invalid backend snapshots retain precise warning reasons after projection', () => {
  const input = snapshot();
  input.selected.market.warnings = [{ domain: 'quote', reason: 'quote_stale' }];
  const projected = createMultimarketProjector().project(input, 1000);
  assert.deepEqual(projected.selected.market.warnings, ['quote_stale']);
});

test('metrics export includes only approved counters and coarse gate states', () => {
  const payload = metricsExportPayload({
    events: 14, duplicates: 2, rejected: 1, overflow: 0, process_p95_ms: 4.5,
    market_lag_ms: 0.8, rss_bytes: 1024, gpu_bytes: 4096,
    symbol: 'BTCUSDT', quote: { bid: '50000' }, recent_trades: [{ price: '50001' }],
    account_id: 'private-account-id', secret: 'do-not-export',
  }, {
    b3: { status: 'blocked', reason: 'entitlement path C:/private' },
    private_account: { status: 'not_connected', account_id: 'private-account-id' },
    financial_model: 'unknown',
    native_evidence: { status: 'not_measured', window_title: 'private window' },
    private_payload: 'do-not-export',
  });

  assert.deepEqual(payload, {
    schema_version: 1,
    metrics: { events: 14, duplicates: 2, rejected: 1, overflow: 0, process_p95_ms: 4.5, market_lag_ms: 0.8, rss_bytes: 1024, gpu_bytes: null },
    gates: { b3: 'blocked', private_account: 'unknown', financial_model: 'unknown', native_evidence: 'not_measured' },
    measurement_scope: { gpu: 'not_measured', native_windows_ui: 'not_measured' },
  });
  assert.doesNotMatch(JSON.stringify(payload), /BTCUSDT|50000|private-account-id|entitlement path|private window|do-not-export/i);
});

test('stale contextual responses are removed with an explicit expiry cause', () => {
  const projector = createMultimarketProjector();
  projector.project(snapshot(), 1000);
  const stale = projector.project(snapshot(), 3100);

  assert.equal(stale.selected.context, null);
  assert.equal(stale.selected.contextStatus, 'Contexto expirado.');
});

test('same symbol at different venues has a distinct workspace identity', () => {
  const first = workspaceIdentity({ workspace_id: 'a', instrument_id: 'binance:spot:BTCUSDT', source_id: 'binance_public_spot', symbol: 'BTCUSDT', venue: 'BINANCE', segment: 'SPOT' });
  const second = workspaceIdentity({ workspace_id: 'b', instrument_id: 'other:spot:BTCUSDT', source_id: 'other_public_spot', symbol: 'BTCUSDT', venue: 'OTHER', segment: 'SPOT' });

  assert.notEqual(first, second);
});

test('quote expiry clears the actionable quote and marks domain health stale after the 5 second TTL', () => {
  const projector = createMultimarketProjector();
  const makeFreshQuote = () => {
    const input = snapshot();
    input.selected.market.quote.event_id = 'quote-1';
    return input;
  };

  projector.project(makeFreshQuote(), 1_000);
  const boundary = projector.project(makeFreshQuote(), 6_000);
  const expired = projector.project(makeFreshQuote(), 6_001);

  assert.equal(boundary.selected.market.quote.age_ms, 5_000);
  assert.equal(boundary.selected.market.health.quote.status, 'live');
  assert.equal(expired.selected.market.quote, null);
  assert.equal(expired.selected.market.health.quote.status, 'stale');
  assert.equal(expired.selected.market.health.quote.reason, 'quote_stale');
  assert.equal(expired.selected.market.health.quote.age_ms, 5_001);
  assert.equal(expired.selected.market.features.spread, null);
  assert.ok(expired.selected.market.warnings.includes('quote_stale'));
  assert.equal(expired.selected.decision.reason, 'quote_stale');
});

test('trade expiry removes stale rows and aggregates while quote freshness remains independent', () => {
  const projector = createMultimarketProjector();
  const makeSnapshot = (quoteId) => {
    const input = snapshot();
    input.selected.market.quote.event_id = quoteId;
    input.selected.market.quote.received_at_ms += Number(quoteId.slice(-1));
    input.selected.market.recent_trades = [{ event_id: 'trade-1', price: '60000.05', quantity: '0.2', aggressor: 'buy', market_ts_ms: 10000, received_at_ms: 10010, age_ms: 0 }];
    input.selected.market.health.trades.age_ms = 0;
    input.selected.market.features = { ...input.selected.market.features, trade_count: 1, buy_quantity: '0.2', delta_quantity: '0.2', event_range: ['trade-1', 'trade-1'] };
    return input;
  };

  projector.project(makeSnapshot('quote-1'), 1_000);
  const boundary = projector.project(makeSnapshot('quote-2'), 31_000);
  const expired = projector.project(makeSnapshot('quote-2'), 31_001);

  assert.equal(boundary.selected.market.quote.age_ms, 0);
  assert.equal(boundary.selected.market.health.trades.age_ms, 30_000);
  assert.equal(boundary.selected.market.health.trades.status, 'live');
  assert.equal(expired.selected.market.quote.age_ms, 1);
  assert.equal(expired.selected.market.health.trades.status, 'stale');
  assert.equal(expired.selected.market.health.trades.reason, 'trades_stale');
  assert.equal(expired.selected.market.health.trades.age_ms, 30_001);
  assert.deepEqual(expired.selected.market.recent_trades, []);
  assert.equal(expired.selected.market.features.trade_count, 0);
  assert.equal(expired.selected.market.features.buy_quantity, '0');
  assert.equal(expired.selected.market.features.sell_quantity, '0');
  assert.equal(expired.selected.market.features.delta_quantity, '0');
  assert.equal(expired.selected.market.features.event_range, null);
  assert.ok(expired.selected.market.warnings.includes('trades_stale'));
});

test('book expiry removes a stale book and reports age without renewing its source clock', () => {
  const projector = createMultimarketProjector();
  const makeSnapshot = () => {
    const input = snapshot();
    input.selected.source = { ...input.selected.source, book: true, book_mode: 'l2' };
    input.selected.market.book = { event_id: 'book-1', received_at_ms: 10010, age_ms: 0, bids: [], asks: [] };
    input.selected.market.health.book = { status: 'live', reason: null, age_ms: 0 };
    return input;
  };

  projector.project(makeSnapshot(), 1_000);
  const boundary = projector.project(makeSnapshot(), 3_000);
  const expired = projector.project(makeSnapshot(), 3_001);

  assert.equal(boundary.selected.market.book.age_ms, 2_000);
  assert.equal(boundary.selected.market.health.book.status, 'live');
  assert.equal(expired.selected.market.book, null);
  assert.equal(expired.selected.market.health.book.status, 'stale');
  assert.equal(expired.selected.market.health.book.reason, 'book_stale');
  assert.equal(expired.selected.market.health.book.age_ms, 2_001);
  assert.ok(expired.selected.market.warnings.includes('book_stale'));
});

test('manual account freshness expires independently and unknown age never remains reconciled', () => {
  const projector = createMultimarketProjector();
  const first = snapshot();
  first.selected.account = { account_id: 'manual-ledger', revision: 2, asof_ms: 9000, age_ms: 0, status: 'reconciled', reason: null, balances: { USDT: '5.00' }, positions: {} };
  projector.project(first, 1_000);

  const later = snapshot();
  later.selected.market.quote.event_id = 'quote-fresh-after-account-age';
  later.selected.market.quote.received_at_ms = 71_010;
  later.selected.account = { ...first.selected.account, age_ms: 0 };
  const boundary = projector.project(later, 61_000);
  const expired = projector.project(later, 61_001);

  assert.equal(boundary.selected.account.status, 'reconciled');
  assert.equal(boundary.selected.account.age_ms, 60_000);
  assert.equal(expired.selected.market.quote.age_ms, 1);
  assert.equal(expired.selected.account.status, 'stale');
  assert.equal(expired.selected.account.reason, 'account_snapshot_expired');
  assert.equal(expired.selected.account.age_ms, 60_001);
  assert.deepEqual(expired.selected.account.balances, {});
  assert.deepEqual(expired.selected.account.positions, {});

  const unknown = snapshot();
  unknown.selected.account = { ...first.selected.account, age_ms: null };
  const unknownProjection = createMultimarketProjector().project(unknown, 1_000);
  assert.equal(unknownProjection.selected.account.status, 'stale');
  assert.equal(unknownProjection.selected.account.reason, 'account_freshness_unknown');
  assert.equal(unknownProjection.selected.account.age_ms, null);
  assert.deepEqual(unknownProjection.selected.account.balances, {});
  assert.deepEqual(unknownProjection.selected.account.positions, {});
});

test('an unchanged backend snapshot expires quote, trades, book, and account on the local monotonic clock', () => {
  const projector = createMultimarketProjector();
  const unchanged = snapshot();
  unchanged.selected.market.quote.event_id = 'last-quote';
  unchanged.selected.market.recent_trades = [{ event_id: 'last-trade', price: '60000.05', quantity: '0.2', aggressor: 'buy', market_ts_ms: 10000, received_at_ms: 10010, age_ms: 0 }];
  unchanged.selected.market.health.trades.age_ms = 0;
  unchanged.selected.market.features = { ...unchanged.selected.market.features, trade_count: 1, buy_quantity: '0.2', delta_quantity: '0.2', event_range: ['last-trade', 'last-trade'] };
  unchanged.selected.source = { ...unchanged.selected.source, book: true, book_mode: 'l2' };
  unchanged.selected.market.book = { event_id: 'last-book', received_at_ms: 10010, age_ms: 0, bids: [], asks: [] };
  unchanged.selected.market.health.book = { status: 'live', reason: null, age_ms: 0 };
  unchanged.selected.account = { account_id: 'manual-ledger', revision: 2, asof_ms: 9000, age_ms: 0, status: 'reconciled', reason: null, balances: { USDT: '5.00' }, positions: { WIN: '1' } };

  projector.project(unchanged, 1_000);
  const afterBackendStops = projector.project(unchanged, 62_001);

  assert.equal(afterBackendStops.selected.market.health.quote.status, 'stale');
  assert.equal(afterBackendStops.selected.market.health.quote.age_ms, 61_001);
  assert.equal(afterBackendStops.selected.market.quote, null);
  assert.equal(afterBackendStops.selected.market.health.trades.status, 'stale');
  assert.deepEqual(afterBackendStops.selected.market.recent_trades, []);
  assert.equal(afterBackendStops.selected.market.features.trade_count, 0);
  assert.equal(afterBackendStops.selected.market.health.book.status, 'stale');
  assert.equal(afterBackendStops.selected.market.book, null);
  assert.equal(afterBackendStops.selected.account.status, 'stale');
  assert.deepEqual(afterBackendStops.selected.account.balances, {});
  assert.deepEqual(afterBackendStops.selected.account.positions, {});
});

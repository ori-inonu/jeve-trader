import test from 'node:test';
import assert from 'node:assert/strict';
import { createMultimarketProjector, workspaceIdentity } from '../src/multimarketModel.ts';

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
    context: { status: 'complete', model: 'jev-1.13.0', questions_version: 'mm-context-v1', origin_monotonic_ns: 5000, age_ms: 100, answers: [{ kind: 'Choice', value: 'observe_buy' }], financial_probability: null, identity: { workspace_id: 'spot-btc', instrument_id: 'binance:spot:BTCUSDT', source_id: 'binance_public_spot', epoch: 1, metadata_version: 'exchange-info-7' } },
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
  assert.equal(first.selected.decision.profit_probability, null);
  assert.equal(first.ordersEnabled, false);
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
      context: { ...snapshot().selected.context, identity: { ...snapshot().selected.context.identity, workspace_id: 'spot-btc', instrument_id: 'binance:spot:BTCUSDT', source_id: 'binance_public_spot' } },
    },
  });
  const projected = projector.project(otherWorkspace, 1100);

  assert.match(projected.selected.identity.workspace_id, /other-venue-btc/);
  assert.equal(projected.selected.context, null);
  assert.match(projected.selected.contextStatus, /identity|workspace/i);
});

test('same symbol at different venues has a distinct workspace identity', () => {
  const first = workspaceIdentity({ workspace_id: 'a', instrument_id: 'binance:spot:BTCUSDT', source_id: 'binance_public_spot', symbol: 'BTCUSDT', venue: 'BINANCE', segment: 'SPOT' });
  const second = workspaceIdentity({ workspace_id: 'b', instrument_id: 'other:spot:BTCUSDT', source_id: 'other_public_spot', symbol: 'BTCUSDT', venue: 'OTHER', segment: 'SPOT' });

  assert.notEqual(first, second);
});

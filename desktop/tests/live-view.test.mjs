import test from 'node:test';
import assert from 'node:assert/strict';
import {liveSnapshot} from '../src/liveView.ts';
import {receivedSnapshot,paintLatency} from '../src/visualLatency.ts';

const snapshot = () => ({
  generated_at_ms:10000,
  market:{application_mode:'excel_observation',flow_ts_ms:10000,last_quote:{ts_ms:10000}},
  context_settings:{validity_ms:2000},
  source:{capabilities:{quote_fresh:true,tape:true,aggression:true,price_depth:true,full_tape:false}},
  directional:{temperature:93,expires_at_ms:10500,geometry:{entry_points:'131000'}},
  context:{support:.9},hypothesis_context:[{family:'absorption'}],context_by_candidate:{a:{}},
  jev:{current:true},alert:{active:true,episode:{id:1}},
});

test('visual measurement excludes background receipt and background paint', () => {
  Object.defineProperty(globalThis,'document',{value:{visibilityState:'hidden'},configurable:true});
  receivedSnapshot(1);
  document.visibilityState='visible';
  assert.equal(paintLatency(1).count,0);
  receivedSnapshot(2);
  document.visibilityState='hidden';
  assert.equal(paintLatency(2).count,0);
  document.visibilityState='visible';
  receivedSnapshot(3);
  assert.equal(paintLatency(3).count,1);
  assert.equal(paintLatency(3).count,1); // a sequence is counted only once
  delete globalThis.document;
});

test('reply expiry removes live context and alerts while source may remain fresh', () => {
  const raw=snapshot(), view=liveSnapshot(raw,10501);
  assert.equal(view.directional.temperature,null);
  assert.equal(view.directional.geometry,null);
  assert.equal(view.alert.active,false);
  assert.deepEqual(view.hypothesis_context,[]);
  assert.equal(view.source.capabilities.quote_fresh,true);
  assert.equal(raw.directional.temperature,93); // frozen historical input is preserved
});

test('engine silence and source timestamps expire independently of the last snapshot', () => {
  const raw=snapshot();raw.directional.expires_at_ms=14000;
  const view=liveSnapshot(raw,12001);
  assert.equal(view.directional.temperature,null);
  assert.equal(view.alert.active,false);
  for(const key of ['quote_fresh','tape','aggression','price_depth']) assert.equal(view.source.capabilities[key],false);
  raw.generated_at_ms=12500;
  assert.equal(liveSnapshot(raw,12500).source.capabilities.tape,false);
  assert.equal(liveSnapshot(raw,12500).source.capabilities.quote_fresh,false);
});

test('fresh live values and explicitly identified historical modes remain intact', () => {
  const raw=snapshot();assert.equal(liveSnapshot(raw,10499).directional.temperature,93);
  raw.market.application_mode='synthetic';assert.equal(liveSnapshot(raw,20000),raw);
});

test('fresh context cannot alert with stale quote or JEV OFF; configured TTL is honored', () => {
  const raw=snapshot();raw.market.last_quote.ts_ms=9000;raw.context_settings.validity_ms=500;
  assert.equal(liveSnapshot(raw,10001).source.capabilities.quote_fresh,false);
  assert.equal(liveSnapshot(raw,10001).alert.active,false);
  raw.market.last_quote.ts_ms=10000;raw.jev.enabled=false;
  assert.equal(liveSnapshot(raw,10001).directional.temperature,null);
});

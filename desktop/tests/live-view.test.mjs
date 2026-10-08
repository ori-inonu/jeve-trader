import test from 'node:test';
import assert from 'node:assert/strict';
import {liveSnapshot} from '../src/liveView.ts';
import {observeReducedMotion} from '../src/motionPreference.ts';
import {receivedSnapshot,paintLatency,visualPilotReport,discardBackgroundReceipts,discardSnapshot} from '../src/visualLatency.ts';

test('renderer reload establishes a capture baseline instead of remeasuring the retained snapshot', async () => {
  Object.defineProperty(globalThis,'document',{value:{visibilityState:'visible'},configurable:true});
  const first=await import('../src/visualLatency.ts?first-renderer');
  const receive=first.createVisualCaptureReceiver();
  receive(401,null,false,null);first.paintLatency(401);
  receive(402,'pilot-reload',true,'pilot-reload:1:10000');first.paintLatency(402);
  assert.equal(first.visualPilotReport('pilot-reload').buckets.reduce((n,[,count])=>n+count,0),1);
  const reloaded=await import('../src/visualLatency.ts?reloaded-renderer');
  const resumed=reloaded.createVisualCaptureReceiver();
  resumed(403,'pilot-reload',true,'pilot-reload:1:10000');reloaded.paintLatency(403);
  resumed(404,'pilot-reload',true,'pilot-reload:1:10000');reloaded.paintLatency(404);
  assert.equal(reloaded.visualPilotReport('pilot-reload').buckets.length,0);
  resumed(405,'pilot-reload',true,'pilot-reload:1:10250');reloaded.paintLatency(405);
  resumed(406,'pilot-reload',true,'pilot-reload:1:10250');reloaded.paintLatency(406);
  assert.equal(reloaded.visualPilotReport('pilot-reload').buckets.reduce((n,[,count])=>n+count,0),1);
  assert.equal(reloaded.visualPilotReport('pilot-reload').excluded,0);
  delete globalThis.document;
});

const snapshot = () => ({
  generated_at_ms:10000,
  market:{application_mode:'excel_observation',flow_ts_ms:10000,last_quote:{ts_ms:10000}},
  context_settings:{validity_ms:2000},
  source:{capabilities:{quote_fresh:true,tape:true,aggression:true,price_depth:true,full_tape:false}},
  directional:{temperature:93,wait:.37,selected:'buy',candidate_key:'candidate',evaluated_at_ms:10000,
    latency_ms:150,expires_at_ms:10500,geometry:{entry_points:'131000'}},
  context:{support:.9},hypothesis_context:[{family:'absorption'}],context_by_candidate:{a:{}},
  jev:{current:true},alert:{active:true,episode:{id:1}},
});

test('reduced motion follows live system changes and unsubscribes on unmount',()=>{
  const original=globalThis.matchMedia, values=[];
  let listener=null;
  const preference={matches:false,
    addEventListener:(event,fn)=>{assert.equal(event,'change');listener=fn;},
    removeEventListener:(event,fn)=>{assert.equal(event,'change');assert.equal(fn,listener);listener=null;}};
  globalThis.matchMedia=query=>{assert.equal(query,'(prefers-reduced-motion: reduce)');return preference;};
  try {
    const stop=observeReducedMotion(value=>values.push(value));
    assert.deepEqual(values,[false]);
    preference.matches=true;listener();
    preference.matches=false;listener();
    assert.deepEqual(values,[false,true,false]);
    stop();assert.equal(listener,null);
  } finally {
    if(original)globalThis.matchMedia=original;else delete globalThis.matchMedia;
  }
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

test('pilot exposes canceled paints, pending frames and intermediate background periods', () => {
  Object.defineProperty(globalThis,'document',{value:{visibilityState:'visible'},configurable:true});
  receivedSnapshot(201,'pilot-C',true);discardSnapshot(201);paintLatency(201);
  receivedSnapshot(202,'pilot-C',true);
  assert.equal(visualPilotReport('pilot-C').excluded,2); // includes the pending frame
  document.visibilityState='hidden';discardBackgroundReceipts();
  document.visibilityState='visible';paintLatency(202);
  assert.equal(visualPilotReport('pilot-C').excluded,2);
  assert.equal(visualPilotReport('pilot-C').buckets.length,0);
  delete globalThis.document;
});

test('periodic checkpoints leave pending frames for a later completed sample', () => {
  Object.defineProperty(globalThis,'document',{value:{visibilityState:'visible'},configurable:true});
  receivedSnapshot(301,'pilot-checkpoint',true);
  assert.equal(visualPilotReport('pilot-checkpoint',false).excluded,0);
  assert.equal(visualPilotReport('pilot-checkpoint').excluded,1);
  paintLatency(301);
  assert.equal(visualPilotReport('pilot-checkpoint',false).excluded,0);
  assert.equal(visualPilotReport('pilot-checkpoint',false).buckets.reduce((n,[,count])=>n+count,0),1);
  delete globalThis.document;
});

test('pilot visual exclusions count actual captures instead of repeated polling snapshots', () => {
  Object.defineProperty(globalThis,'document',{value:{visibilityState:'visible'},configurable:true});
  receivedSnapshot(101,'pilot-A',true);paintLatency(101);paintLatency(101);
  receivedSnapshot(102,'pilot-A',false);paintLatency(102);
  receivedSnapshot(105,'pilot-A',false);paintLatency(105);
  document.visibilityState='hidden';receivedSnapshot(103,'pilot-A',true);
  receivedSnapshot(106,'pilot-A',false);
  document.visibilityState='visible';paintLatency(103);
  const report=visualPilotReport('pilot-A');
  assert.equal(report.buckets.reduce((n,[,count])=>n+count,0),1);
  assert.equal(report.excluded,1);
  receivedSnapshot(104,'pilot-B',true);paintLatency(104);
  assert.equal(visualPilotReport('pilot-A').buckets.length,0);
  assert.equal(visualPilotReport('pilot-B').buckets.reduce((n,[,count])=>n+count,0),1);
  delete globalThis.document;
});

test('reply expiry removes live context and alerts while source may remain fresh', () => {
  const raw=snapshot(), view=liveSnapshot(raw,10501);
  assert.equal(view.directional.temperature,null);
  assert.equal(view.directional.geometry,null);
  for(const key of ['wait','candidate_key','evaluated_at_ms','expires_at_ms','latency_ms']) assert.equal(view.directional[key],null);
  assert.equal(view.directional.selected,'unavailable');
  assert.equal(view.alert.active,false);
  assert.deepEqual(view.hypothesis_context,[]);
  assert.equal(view.source.capabilities.quote_fresh,true);
  assert.equal(raw.directional.temperature,93); // frozen historical input is preserved
  assert.equal(raw.directional.wait,.37);
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

const flowSnapshot=()=>{
  const raw=snapshot();
  raw.market.hypotheses=[{kind:'progression'},{kind:'liquidity_withdrawal'}];
  raw.market.order_flow={recent_trades:[{id:'a'}],delta_path:[{delta_contracts:4}],brokers:[{broker:'A'}],
    book:{market_ts_ms:10000,captured_at_ms:10000,bids:[],asks:[]},book_history:[{market_ts_ms:10000}],volume_at_price:[]};
  return raw;
};
test('book freshness uses its market timestamp even with a fresh quote and tape',()=>{
  const raw=flowSnapshot();raw.market.order_flow.book.market_ts_ms=7000;
  const view=liveSnapshot(raw,10001);
  assert.equal(view.source.capabilities.tape,true);
  assert.equal(view.source.capabilities.price_depth,false);
  assert.equal(view.market.order_flow.book,null);
  assert.deepEqual(view.market.order_flow.book_history,[]);
  assert.deepEqual(view.market.hypotheses,[{kind:'progression'}]);
  assert.equal(raw.market.order_flow.book.market_ts_ms,7000);
  raw.market.order_flow.book.market_ts_ms=null;
  assert.equal(liveSnapshot(raw,10001).source.capabilities.price_depth,false);
});
test('expired tape removes retained trades, delta, brokers and tape hypotheses without removing a fresh book',()=>{
  const raw=flowSnapshot();raw.market.flow_ts_ms=7000;
  const view=liveSnapshot(raw,10001);
  for(const key of ['recent_trades','delta_path','brokers']) assert.deepEqual(view.market.order_flow[key],[]);
  assert.equal(view.market.order_flow.book.market_ts_ms,10000);
  assert.deepEqual(view.market.hypotheses,[{kind:'liquidity_withdrawal'}]);
  raw.source.capabilities.tape=false;raw.market.flow_ts_ms=10000;
  assert.deepEqual(liveSnapshot(raw,10001).market.order_flow.recent_trades,[]);
});
test('JEV OFF clears context in every mode and preserves fresh local observations',()=>{
  for(const mode of ['excel_observation','synthetic','replay']){
    const raw=flowSnapshot();raw.market.application_mode=mode;raw.jev.enabled=false;
    const view=liveSnapshot(raw,10001);
    assert.equal(view.directional.temperature,null);assert.equal(view.alert.active,false);
    assert.equal(view.directional.wait,null);assert.equal(view.directional.selected,'unavailable');
    assert.equal(view.directional.candidate_key,null);
    assert.equal(view.context,null);assert.deepEqual(view.hypothesis_context,[]);
    assert.equal(view.market.order_flow.recent_trades.length,1);
    assert.equal(view.market.order_flow.book.market_ts_ms,10000);
  }
});

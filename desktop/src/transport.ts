import {invoke} from '@tauri-apps/api/core';
import {listen} from '@tauri-apps/api/event';
export type Wire = {schema_version:number; id?:string; event?:string; error?:string; result?:Snapshot};
export type Plan = {id:string; action:string; quantity:number; entry_points:string|null; stop_points:string|null; target_points:string|null; expires_at_ms:number|null; costs_brl:string; loss_brl:string; target_net_brl:string; margin_brl:string; expected_log_growth:number|null; profit_probability:number|null; probability_interval?:number[]|null; distribution?:{net_brl:string;probability:number}[]; reason:string; premise?:string; order_sent:boolean};
export type UpdateState = {current_version:string;status:'idle'|'checking'|'available'|'current'|'no_release'|'no_installer'|'auth_required'|'unavailable';latest_version:string|null;release_url:string|null;notes:string;checked_at_ms:number|null};
export type Snapshot = LiveSnapshot & {updates:UpdateState;schema_version:number;sequence:number;generated_at_ms:number;market:{application_mode:string;symbol:string;ts_ms:number;flow_ts_ms?:number;quote_ts_ms?:number;order_flow?:OrderFlow;hypotheses?:FlowHypothesis[];last_quote?:{ts_ms:number}|null;source_generation:number;warnings:string[];evidence_coverage:{source_quality?:{full_tape?:boolean};[key:string]:unknown};computed_features:Record<string,unknown>};account:{equity_brl:string;peak_brl:string;available_margin_brl:string;revision:number;asof_ms:number;drawdown:number;positions:{id:string;side:string;quantity:number;entry_points:string;reserved_margin_brl:string;symbol:string}[]};costs:Record<string,string|boolean>;decision:Plan;alternatives:Plan[];context:{support:number|null;contradiction:number|null;insufficient:number|null}|null;jev:{enabled:boolean;control_revision:number;pending_call:string|null;status:string;configured:boolean;calls:number;limit:number;pending:boolean;current:boolean;model:string};source:{audit:{status:string;tables:unknown[];note?:string};rtd:{enabled:boolean;status:string;previous_ms?:number|null;current_ms?:number|null;restored?:boolean};ocr?:OcrState;error:string|null;excel_running:boolean;config:Record<string,string>;reconnect_enabled:boolean;retry_in_ms:number|null;capabilities:Record<string,boolean|string[]>;discovery:{status:string;error?:string;workbooks:{workbook:string;sheets:string[]}[];cells_read:boolean}};equity_history:{ts_ms:number;equity_brl:string}[];history:{id:number;ts_ms:number;kind:string;payload:unknown}[];research:{status:string;profitdll:string;risk_catalog:string[]};orders_enabled:boolean};
export type LiveSettings = {revision:number;automatic:boolean;cadence_ms:number;validity_ms:number;horizon_seconds:number;alert_threshold:number;alert_rearm:number;alert_cooldown_ms:number;alerts_enabled:boolean;sound_enabled:boolean;daily_limit_usd:string;total_limit_usd:string};
export type Dimensions = {support:number|null;contradiction:number|null;insufficient:number|null};
export type LiveSnapshot = {
  pilot:CapturePilotState;
  directional:{temperature:number|null;wait:number|null;selected:string;candidate_key:string|null;geometry:Record<string,unknown>|null;expires_at_ms:number|null;evaluated_at_ms:number|null;latency_ms:number|null};
  context_settings:LiveSettings; context_by_candidate:Record<string,Dimensions>; hypothesis_context:{candidate_key:string;family:string;side:string;aggressor_side:string;scenario_side:string|null;literal_premise:string;dimensions:Dimensions}[];
  budget:{estimated_usd:string;reserved_usd:string;today_usd:string;committed_usd:string;daily_limit_usd:string;total_limit_usd:string;unknown_attempts:number;billed_usd:null};
  jev_error:string|null; jev_retry_in_ms:number; alert:{active:boolean;episode:{id:number;side:string;at_ms:number;temperature:number}|null}; chart_points:[number,number][];
};
export type CapturePilotState={status:'idle'|'recording'|'finished'|'interrupted';id:string|null;symbol?:string;started_at_ms?:number;duration_ms?:number;capture_samples?:number;interruptions?:number;contract_changes?:number;coverage?:Record<string,number>;scenarios?:{scenario:string;evidence_kind:string;elapsed_ms:number}[];timings?:Record<string,{count:number;p95_ms:number|null;excluded?:number}>;pending?:string[];acceptance?:string;report_path?:string|null;save_error?:string|null};
const native = '__TAURI_INTERNALS__' in window;
const pending = new Map<string,{resolve:(value:Snapshot)=>void;reject:(error:Error)=>void;timer:ReturnType<typeof setTimeout>}>();
let onSnapshot: (value:Snapshot)=>void = ()=>{};
function receive(message:Wire) {
  if(![1,2].includes(message.schema_version))return;
  if(message.id && pending.has(message.id)) {
    const request=pending.get(message.id)!;pending.delete(message.id);clearTimeout(request.timer);
    if(message.error)request.reject(new Error(message.error));else if(message.result){request.resolve(message.result);onSnapshot(message.result);}
  } else if(message.result)onSnapshot(message.result);
}
export async function connect(callback:(value:Snapshot)=>void) {
  onSnapshot=callback;
  if(native) return listen<Wire>('engine',event=>receive(event.payload));
  import.meta.hot?.on('engine',receive);
  return ()=>import.meta.hot?.off('engine',receive);
}
export async function command(method:string,params:Record<string,unknown>={}) {
  const message={schema_version:2,id:crypto.randomUUID(),method,params};
  if(!native){const response=await fetch('/__engine',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(message)});if(!response.ok)throw new Error('Serviço local indisponível');const wire:Wire=await response.json();if(wire.error)throw new Error(wire.error);if(!wire.result)throw new Error('Resposta inválida');onSnapshot(wire.result);return wire.result;}
  return new Promise<Snapshot>((resolve,reject)=>{
    const timer=setTimeout(()=>{pending.delete(message.id);reject(new Error('Motor Python não respondeu'));},10000);
    pending.set(message.id,{resolve,reject,timer});
    invoke('engine_send',{message:JSON.stringify(message)}).catch(error=>{clearTimeout(timer);pending.delete(message.id);reject(new Error(String(error)));});
  });
}

export type FlowHypothesis = {id:string;kind:string;side:string;aggressor_side:string|null;scenario_side:string|null;scenario_effect:string;status:string;description:string;evidence:Record<string,unknown>;missing:string[]};
export type BookLevel = {price_points:number|string;quantity:number};
export type BookSnapshot = {symbol:string;bids:BookLevel[];asks:BookLevel[];market_ts_ms:number|null;captured_at_ms:number;kind:string};
export type OrderFlow = {window_ms:number;recent_trades:{id:string;ts_ms:number;price_points:string;quantity:number;aggressor:string;buyer_broker:string|null;seller_broker:string|null}[];delta_path:{ts_ms:number;delta_contracts:number}[];brokers:{broker:string;buy_contracts:number;sell_contracts:number;net_contracts:number}[];broker_scope:string;broker_identified_trades:number;investor_positions_known:false;book:BookSnapshot|null;book_history:BookSnapshot[];volume_at_price:{price_points:number;quantity:number}[];source_capabilities:Record<string,boolean>;capture_evidence:{captured_at_ms?:number;received_at_ms?:number;window_mode?:string;filters?:string;polling_effective_ms?:number;rtd_change_interval_ms?:number}};
export type OcrState = {enabled:boolean;status:string;error?:string|null;runtime?:{available:boolean;engine:string;version:string|null;error:string|null};windows:{handle:number;title:string}[];config:Record<string,unknown>;observation?:{text:string;captured_at_ms:number;legibility:string;coverage:string;rows:string[];dropped_rows:number;engine?:string;engine_version?:string}};

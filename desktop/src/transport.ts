import {invoke} from '@tauri-apps/api/core';
import {listen} from '@tauri-apps/api/event';
export type Wire = {schema_version:number; id?:string; event?:string; error?:string; result?:Snapshot};
export type Plan = {id:string; action:string; quantity:number; entry_points:string|null; stop_points:string|null; target_points:string|null; expires_at_ms:number|null; costs_brl:string; loss_brl:string; target_net_brl:string; margin_brl:string; expected_log_growth:number|null; profit_probability:number|null; probability_interval?:number[]|null; distribution?:{net_brl:string;probability:number}[]; reason:string; premise?:string; order_sent:boolean};
export type UpdateState = {current_version:string;status:'idle'|'checking'|'available'|'current'|'no_release'|'no_installer'|'auth_required'|'unavailable';latest_version:string|null;release_url:string|null;notes:string;checked_at_ms:number|null};
export type Snapshot = {updates:UpdateState;schema_version:number;sequence:number;generated_at_ms:number;market:{application_mode:string;symbol:string;ts_ms:number;flow_ts_ms?:number;source_generation:number;warnings:string[];evidence_coverage:{source_quality?:{full_tape?:boolean};[key:string]:unknown};computed_features:Record<string,unknown>};account:{equity_brl:string;peak_brl:string;available_margin_brl:string;revision:number;asof_ms:number;drawdown:number;positions:{id:string;side:string;quantity:number;entry_points:string;reserved_margin_brl:string;symbol:string}[]};costs:Record<string,string|boolean>;decision:Plan;alternatives:Plan[];context:{support:number|null;contradiction:number|null;insufficient:number|null}|null;jev:{configured:boolean;calls:number;limit:number;pending:boolean;current:boolean;model:string};source:{error:string|null;excel_running:boolean;config:Record<string,string>};equity_history:{ts_ms:number;equity_brl:string}[];history:{id:number;ts_ms:number;kind:string;payload:unknown}[];research:{status:string;profitdll:string;risk_catalog:string[]};orders_enabled:boolean};
const native = '__TAURI_INTERNALS__' in window;
const pending = new Map<string,{resolve:(value:Snapshot)=>void;reject:(error:Error)=>void;timer:ReturnType<typeof setTimeout>}>();
let onSnapshot: (value:Snapshot)=>void = ()=>{};
function receive(message:Wire) {
  if(message.schema_version!==1)return;
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
  const message={schema_version:1,id:crypto.randomUUID(),method,params};
  if(!native){const response=await fetch('/__engine',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(message)});if(!response.ok)throw new Error('Serviço local indisponível');const wire:Wire=await response.json();if(wire.error)throw new Error(wire.error);if(!wire.result)throw new Error('Resposta inválida');onSnapshot(wire.result);return wire.result;}
  return new Promise<Snapshot>((resolve,reject)=>{
    const timer=setTimeout(()=>{pending.delete(message.id);reject(new Error('Motor Python não respondeu'));},10000);
    pending.set(message.id,{resolve,reject,timer});
    invoke('engine_send',{message:JSON.stringify(message)}).catch(error=>{clearTimeout(timer);pending.delete(message.id);reject(new Error(String(error)));});
  });
}

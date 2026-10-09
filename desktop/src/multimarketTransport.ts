import {invoke} from '@tauri-apps/api/core';
import {listen} from '@tauri-apps/api/event';
import type {MultimarketSnapshot, UnknownRecord} from './multimarketModel';

type Wire = {schema_version?:number; id?:string; event?:string; error?:string; result?:unknown};
const pending = new Map<string,{resolve:(value:MultimarketSnapshot)=>void;reject:(error:Error)=>void;timer:ReturnType<typeof setTimeout>}>();
const subscribers = new Set<(value:MultimarketSnapshot)=>void>();
const native = () => '__TAURI_INTERNALS__' in window;
function result(wire:Wire):MultimarketSnapshot {
  if(wire.error)throw new Error(wire.error);
  if(![1,2].includes(wire.schema_version??0) || !wire.result || typeof wire.result!=='object' || (wire.result as UnknownRecord).schema_version!==3)
    throw new Error('Resposta multimercado incompatível; esperado snapshot 3.');
  // Detailed field/identity validation is centralized in multimarketModel.
  return wire.result as MultimarketSnapshot;
}
function receive(wire:Wire) {
  if(wire.id && pending.has(wire.id)) {
    const request=pending.get(wire.id)!;pending.delete(wire.id);clearTimeout(request.timer);
    try {const value=result(wire);request.resolve(value);subscribers.forEach(callback=>callback(value));}
    catch(error){request.reject(error instanceof Error?error:new Error('Resposta inválida'));}
  } else if(wire.event==='multimarket.snapshot') {
    // Pass incompatible inner versions to the fail-closed projector as diagnostics.
    subscribers.forEach(callback=>callback(wire.result as MultimarketSnapshot));
  }
}
export async function connectMultimarket(callback:(value:MultimarketSnapshot)=>void) {
  subscribers.add(callback);
  let detach:()=>void;
  if(native())detach=await listen<Wire>('engine',event=>receive(event.payload));
  else {import.meta.hot?.on('engine',receive);detach=()=>import.meta.hot?.off('engine',receive);}
  return ()=>{subscribers.delete(callback);detach();};
}
export async function multimarketCommand(method:string,params:UnknownRecord={}):Promise<MultimarketSnapshot> {
  if(!method.startsWith('multimarket.'))throw new Error('Comando fora do domínio multimercado.');
  const message={schema_version:2,id:crypto.randomUUID(),method,params};
  if(!native()) {
    const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),10_000);
    try {
      const response=await fetch('/__engine',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(message),signal:controller.signal});
      if(!response.ok)throw new Error('Serviço local indisponível');
      const value=result(await response.json());subscribers.forEach(callback=>callback(value));return value;
    }finally{clearTimeout(timer);}
  }
  return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{pending.delete(message.id);reject(new Error('Motor Python não respondeu'));},10_000);
    pending.set(message.id,{resolve,reject,timer});
    invoke('engine_send',{message:JSON.stringify(message)}).catch(error=>{clearTimeout(timer);pending.delete(message.id);reject(new Error(String(error)));});
  });
}

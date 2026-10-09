import {invoke} from '@tauri-apps/api/core';
import {listen} from '@tauri-apps/api/event';
import type {MultimarketSnapshot, UnknownRecord} from './multimarketModel';
import {createSharedEventSubscription} from './multimarketSubscriptions';
import {parseMultimarketWire, projectMultimarketEvent, type MultimarketWire} from './multimarketWire';

type Wire = MultimarketWire;
const pending = new Map<string,{resolve:(value:MultimarketSnapshot)=>void;reject:(error:Error)=>void;timer:ReturnType<typeof setTimeout>}>();
const native = () => '__TAURI_INTERNALS__' in window;
function result(wire:Wire):MultimarketSnapshot {
  return parseMultimarketWire(wire);
}

const subscriptions = createSharedEventSubscription<MultimarketSnapshot>(async publish => {
  const receive = (wire:Wire) => {
    if(wire.id && pending.has(wire.id)) {
      const request=pending.get(wire.id)!;pending.delete(wire.id);clearTimeout(request.timer);
      try {const value=result(wire);request.resolve(value);publish(value);}
      catch(error){request.reject(error instanceof Error?error:new Error('Resposta inválida'));}
    } else if(wire.event==='multimarket.snapshot') {
      // Pass incompatible inner versions to the fail-closed projector as diagnostics.
      publish(projectMultimarketEvent(wire));
    }
  };
  if(native())return listen<Wire>('engine',event=>receive(event.payload));
  import.meta.hot?.on('engine',receive);
  return ()=>import.meta.hot?.off('engine',receive);
});

export function connectMultimarket(callback:(value:MultimarketSnapshot)=>void) {
  return subscriptions.subscribe(callback);
}
export async function multimarketCommand(method:string,params:UnknownRecord={}):Promise<MultimarketSnapshot> {
  if(!method.startsWith('multimarket.'))throw new Error('Comando fora do domínio multimercado.');
  const message={schema_version:2,id:crypto.randomUUID(),method,params};
  if(!native()) {
    const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),10_000);
    try {
      const response=await fetch('/__engine',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(message),signal:controller.signal});
      if(!response.ok)throw new Error('Serviço local indisponível');
      const value=result(await response.json());subscriptions.publish(value);return value;
    }finally{clearTimeout(timer);}
  }
  return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{pending.delete(message.id);reject(new Error('Motor Python não respondeu'));},10_000);
    pending.set(message.id,{resolve,reject,timer});
    invoke('engine_send',{message:JSON.stringify(message)}).catch(error=>{clearTimeout(timer);pending.delete(message.id);reject(new Error(String(error)));});
  });
}

import {useCallback, useEffect, useState} from 'react';
import {App} from './App';
import {MultimarketCockpit} from './MultimarketCockpit';
import type {MultimarketSnapshot, UnknownRecord} from './multimarketModel';
import {connectMultimarket, multimarketCommand} from './multimarketTransport';

export function MultimarketRoot() {
  const [legacy,setLegacy]=useState(window.location.hash==='#legacy');
  const [snapshot,setSnapshot]=useState<MultimarketSnapshot|null>(null);
  const [error,setError]=useState<string|null>(null);
  const [retry,setRetry]=useState(0);
  useEffect(()=>{const update=()=>setLegacy(window.location.hash==='#legacy');window.addEventListener('hashchange',update);return()=>window.removeEventListener('hashchange',update);},[]);
  useEffect(()=>{
    if(legacy)return;
    let cancelled=false;let detach:(()=>void)|undefined;
    setError(null);
    const publish=(value:MultimarketSnapshot)=>{if(!cancelled){setSnapshot(value);setError(null);}};
    void (async()=>{
      try {
        const cleanup=await connectMultimarket(publish);
        if(cancelled){cleanup();return;}detach=cleanup;
        const value=await multimarketCommand('multimarket.snapshot',{});publish(value);
      }catch(reason){if(!cancelled){setSnapshot(null);setError(reason instanceof Error?reason.message:'Motor indisponível');}}
    })();
    return()=>{cancelled=true;detach?.();};
  },[legacy,retry]);
  const run=useCallback(async(method:string,params:UnknownRecord)=>{
    const value=await multimarketCommand(method,params);setSnapshot(value);return value;
  },[]);
  if(legacy)return <><nav aria-label="Alternar mesa" style={{padding:'8px 16px',background:'#0e1724'}}><a href="#multimarket">Voltar ao cockpit multimercado</a></nav><App/></>;
  if(!snapshot)return <main className="mm-shell" style={{padding:32}}><h1>Jeve Trader · Multimercado</h1><p role={error?'alert':'status'}>{error??'Conectando ao motor local…'}</p>{error&&<button type="button" onClick={()=>setRetry(value=>value+1)}>Reconectar motor</button>} <a href="#legacy">Abrir laboratório legado</a><p>Ordens desabilitadas. Conecte uma fonte pública para observar o mercado.</p></main>;
  return <MultimarketCockpit snapshot={snapshot} run={run}/>;
}

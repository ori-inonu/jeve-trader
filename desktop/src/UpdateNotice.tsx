import {useState} from 'react';
import {Download,RefreshCw} from 'lucide-react';
import type {UpdateState} from './transport';

const messages:Record<UpdateState['status'],string>={
  idle:'Consulta ainda não realizada', checking:'Consultando versões publicadas…',
  available:'Atualização disponível', current:'Versão instalada atual',
  no_release:'Ainda não há versão publicada', no_installer:'Release sem instalador Windows compatível',
  auth_required:'Acesso ao repositório necessário', unavailable:'Não foi possível consultar atualizações'
};

export function UpdateNotice({state,run}:{state:UpdateState;run:(method:string)=>Promise<void>}){
  const [open,setOpen]=useState(false);
  return <div className="update-control">
    <button className={`update-toggle ${state.status==='available'?'available':''}`}
      title={messages[state.status]} aria-label={messages[state.status]} aria-expanded={open}
      onClick={()=>setOpen(!open)}><Download size={16}/>{state.status==='available'&&<span>Atualização disponível</span>}</button>
    {open&&<section className="update-popover" aria-label="Atualizações do aplicativo">
      <h3>{messages[state.status]}</h3><p>Instalada: {state.current_version}{state.latest_version&&` · Publicada: ${state.latest_version}`}</p>
      {state.checked_at_ms&&<small>Consulta: {new Date(state.checked_at_ms).toLocaleString('pt-BR')}</small>}
      {state.status==='auth_required'&&<p>Este projeto é privado. Conecte sua conta autorizada pelo Git Credential Manager no Windows e tente novamente.</p>}
      {state.notes&&<pre>{state.notes}</pre>}
      <div className="update-actions"><button className="button secondary" disabled={state.status==='checking'} onClick={()=>void run('updates.check')}><RefreshCw size={14}/>Verificar</button>
        {state.status==='available'&&<button className="button" onClick={()=>void run('updates.open')}><Download size={14}/>Abrir atualização no GitHub</button>}</div>
      <small>A página oferece o instalador. Feche o app antes de instalar a nova versão.</small>
    </section>}
  </div>;
}

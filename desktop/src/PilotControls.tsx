import {useState} from 'react';
import {type Snapshot} from './transport';
import {visualPilotReport} from './visualLatency';

type Run=(method:string,params?:Record<string,unknown>)=>Promise<void>;
const scenarios=[['burst','Rajada'],['scroll','Rolagem'],['filter','Filtro'],['hidden_tab','Aba oculta'],['window_close','Janela fechada'],['reconnect','Reconexão']] as const;
const pendingLabels:Record<string,string>={duration_below_30min:'menos de 30 minutos',capture_samples_missing:'sem amostras de captura',visual_samples_missing:'sem amostras visuais',visual_p95_above_250ms:'p95 visual acima de 250 ms',visual_percentile_unbounded:'p95 visual acima do limite de medição',operator_scenarios_missing:'cenários ainda não marcados',contract_changed:'contrato alterado',clock_inconsistency:'relógios inconsistentes',process_interrupted:'aplicativo interrompido',report_save_failed:'falha ao salvar'};
const timing=(value:number|null|undefined)=>value==null?'—':`${value.toLocaleString('pt-BR')} ms`;

export function PilotControls({data,run}:{data:Snapshot;run:Run}) {
  const pilot=data.pilot, recording=pilot.status==='recording';
  const [busy,setBusy]=useState(false);
  const act=async(method:string,params:Record<string,unknown>={})=>{setBusy(true);try{await run(method,params);}finally{setBusy(false);}};
  const elapsed=Math.floor((pilot.duration_ms??0)/1000);
  return <details className="pilot-controls">
    <summary>Piloto de captura real {recording?`· ${Math.floor(elapsed/60)}:${String(elapsed%60).padStart(2,'0')}`:pilot.status==='idle'?'· não iniciado':'· revisão pendente'}</summary>
    <p>Registre pelo menos 30 minutos com Profit e Excel abertos. O piloto mantém o controle atual do JEV e não solicita análises.</p>
    {recording?<>
      <div className="pilot-status"><b>{pilot.symbol} · {pilot.capture_samples} capturas</b><span>{pilot.interruptions} interrupções</span><span>{pilot.contract_changes} mudanças de contrato</span></div>
      <p>Marque cada situação somente após observá-la. Essas marcas são declarações suas.</p>
      <div className="pilot-actions">{scenarios.map(([id,label])=>{const marked=pilot.scenarios?.some(s=>s.scenario===id);return <button key={id} disabled={busy||marked} onClick={()=>void act('pilot.mark',{pilot_id:pilot.id,scenario:id})}>{marked?'✓ ':''}{label}</button>;})}
        <button className="button secondary" disabled={busy} onClick={()=>void act('pilot.stop',{pilot_id:pilot.id,visual:visualPilotReport(pilot.id!)})}>Encerrar e salvar relatório</button>
      </div>
    </>:<button className="button secondary" disabled={busy||data.market.application_mode!=='excel_observation'||!data.source.excel_running} onClick={()=>void act('pilot.start')}>Iniciar piloto real</button>}
    {pilot.timings&&<div className="pilot-timings">{[['quote_age_on_receive_ms','Idade da cotação'],['capture_to_receive_ms','Captura → motor'],['visual_after_receive_ms','Recebimento → 2 frames'],['jev_response_ms','Resposta JEV']].map(([key,label])=><span key={key}>{label}<b>{timing(pilot.timings?.[key]?.p95_ms)} · {pilot.timings?.[key]?.count??0} amostras</b></span>)}</div>}
    {!!pilot.pending?.length&&<p className="amber">Pendente: {pilot.pending.filter(p=>pendingLabels[p]).map(p=>pendingLabels[p]).join(' · ')}. Continuidade da fonte e revisão humana ainda necessárias.</p>}
    {pilot.report_path&&<p className="pilot-path">Relatório local: <code>{pilot.report_path}</code></p>}
    {pilot.save_error&&<p role="alert" className="red">{pilot.save_error} <button disabled={busy} onClick={()=>void act('pilot.save',{pilot_id:pilot.id})}>Tentar salvar novamente</button></p>}
    <small>Latência visual considera capturas em primeiro plano; cancelamentos e períodos ocultos são excluídos. Idade da cotação não mede a latência da bolsa. O relatório não certifica tape completo, decisões do JEV ou rentabilidade.</small>
  </details>;
}

import {useState} from 'react';
import {observableBook,probabilityLabel,type MultimarketState} from './multimarketView';

const labels:Record<string,string>={off:'Desligado',starting:'Conectando',observing:'Observando',
  degraded:'Dados incompletos',invalid:'Dados inválidos',unavailable:'Indisponível',
  synthetic:'Fixture sintética',finished:'Sessão encerrada',cold:'Aguardando',syncing:'Sincronizando',
  live:'Atualizado',stale:'Vencido'};

type Run=(method:string,params?:Record<string,unknown>)=>Promise<void>;
export function MultimarketPanel({state,run,now}:{state?:MultimarketState;run:Run;now:number}) {
  const [duration,setDuration]=useState(60);
  const [pending,setPending]=useState(false);
  const action=async(method:string,params={})=>{setPending(true);try{await run(method,params);}finally{setPending(false);}};
  if(!state)return <section className="panel"><h1>Mercados</h1><p>Atualize o motor para usar o observador multimercado.</p></section>;
  const book=observableBook(state,now);
  const vap=state.features.volume_at_price as {levels?:unknown[]}|undefined;
  const rawLevels=Array.isArray(vap?.levels)?vap.levels:[];
  const levels=rawLevels.slice(0,20) as {price:string;quantity?:string;qty?:string;notional?:string;trade_count?:number}[];
  const base=state.instrument?.base_asset||'base';
  const quote=state.instrument?.quote_asset||'cotada';
  return <>
    <div className="page-title"><div><span className="eyebrow">DADOS / EXPANSÃO</span><h1>Mercados e evidências</h1>
      <p>Coleta pública, cobertura e condições para comparar oportunidades.</p></div>
      <span className="tag amber">{labels[state.status]||state.status}</span></div>
    <div className="metrics">
      <div className="metric"><span>OBJETIVO DE PESQUISA</span><strong>R$400 → R$4.000</strong><small>10× em menos de uma semana</small></div>
      <div className="metric"><span>PROBABILIDADE DO OBJETIVO</span><strong>{probabilityLabel(state.target_probability)}</strong><small>Avaliação temporal pendente</small></div>
      <div className="metric"><span>EXECUÇÕES RECEBIDAS</span><strong>{state.received_trades}</strong><small>{state.origin==='synthetic'?'Dados sintéticos':'Fluxo público parcial'} · sem tape integral</small></div>
      <div className="metric"><span>ORIGEM</span><strong>{state.origin==='live'?'API pública':state.origin==='synthetic'?'Sintética':'Aguardando'}</strong><small>{state.enabled?`${state.remaining_seconds}s restantes`:'Coleta desligada'} · gravação desligada</small></div>
    </div>
    <section className="panel"><div className="panel-heading"><h3>BTCUSDT spot · coleta observacional</h3><span className="tag">SEM ORDENS</span></div>
      <p className="muted">Este feed permite testar o livro e o volume. Custos, acesso aos produtos alavancados e avaliação econômica ainda precisam de evidência.</p>
      <div className="multimarket-controls"><label className="field"><span>Duração pública (segundos)</span><input aria-label="Duração da coleta" type="number" min="1" max="1800" value={duration} onChange={e=>setDuration(Number(e.target.value))}/></label>
        <button className="button" disabled={pending||state.enabled||!Number.isInteger(duration)||duration<1||duration>1800} onClick={()=>void action('multimarket.start',{duration_seconds:duration})}>Iniciar coleta pública</button>
        <button className="button secondary" disabled={pending||!state.enabled} onClick={()=>void action('multimarket.stop')}>Encerrar</button>
        <button className="button secondary" disabled={pending||state.enabled} onClick={()=>void action('multimarket.synthetic')}>Carregar fixture sintética</button></div>
      {state.error&&<p role="alert" className="notice error">{state.error}</p>}
      <div className="table-wrap"><table><thead><tr><th>Canal</th><th>Saúde</th><th>Cobertura</th><th>Lacunas / ressincronizações</th><th>Eventos perdidos</th></tr></thead><tbody>
        {state.health.map(h=><tr key={h.channel}><td>{h.channel==='depth'?'Livro':'Execuções'}</td><td>{h.stale?'Vencido':!h.valid?'Inválido':labels[h.state]||h.state}</td><td>{h.coverage==='partial'?'Parcial':h.coverage}</td><td>{h.gaps} / {h.resyncs}</td><td>{h.dropped_events}</td></tr>)}
        {!state.health.length&&<tr><td colSpan={5}>Nenhuma fonte iniciada.</td></tr>}</tbody></table></div>
      {state.origin==='synthetic'&&<p className="notice">Fixture local para verificar cálculos e interface. Sem resultados de mercado real.</p>}
    </section>
    <div className="analytics"><section className="panel"><h3>Livro de ofertas · quantidade em {base}</h3>
      <p className="muted">{book?'Até 20 níveis conhecidos por lado.':'Livro indisponível, vencido ou sem sincronização válida.'}</p>
      {book&&<div className="table-wrap"><table><thead><tr><th>Compra</th><th>Quantidade</th><th>Venda</th><th>Quantidade</th></tr></thead><tbody>
        {Array.from({length:Math.max(book.bids.length,book.asks.length)},(_,i)=><tr key={i}><td>{book.bids[i]?.[0]||'—'}</td><td>{book.bids[i]?.[1]||'—'}</td><td>{book.asks[i]?.[0]||'—'}</td><td>{book.asks[i]?.[1]||'—'}</td></tr>)}</tbody></table></div>}
      <small>As ofertas representam quantidade disponível. O volume abaixo usa somente execuções recebidas.</small></section>
      <section className="panel"><h3>Volume por preço · últimos 60 segundos</h3><p className="muted">Quantidade em {base}; valor negociado em {quote}. Cobertura parcial.</p>
        <div className="table-wrap"><table><thead><tr><th>Preço</th><th>Quantidade</th><th>Valor negociado</th></tr></thead><tbody>
          {levels.map((v,i)=><tr key={i}><td>{v.price}</td><td>{v.quantity??v.qty??'—'}</td><td>{v.notional??'—'}</td></tr>)}
          {!levels.length&&<tr><td colSpan={3}>Sem execuções nesta janela.</td></tr>}</tbody></table></div></section></div>
    <section className="panel"><h3>Condições para a tomada de decisão</h3><p className="muted">O contexto mantém observar e aguardar disponíveis. Sem probabilidade financeira validada, a comparação entre mercados permanece pendente.</p>
      <div className="table-wrap"><table><thead><tr><th>Mercado</th><th>Próxima evidência necessária</th></tr></thead><tbody>
        <tr><td>B3 · WIN/WDO</td><td>Feed autorizado, licença e custos vigentes</td></tr><tr><td>Derivativos cripto</td><td>Produto, acesso, margem, liquidação e custos</td></tr>
        <tr><td>Trading esportivo</td><td>API permitida no Brasil e responsabilidade das posições</td></tr><tr><td>Opções binárias</td><td>Admissibilidade, settlement verificável e payout líquido</td></tr></tbody></table></div>
      <p className="muted">Dados empíricos: {state.evaluation.sample_size} · avaliação pendente. Retenção e jurisdição da fonte: {state.source?.retention_permission||'desconhecida'} / {state.source?.jurisdiction||'desconhecida'}.</p>
      <details><summary>Faltas e rastreabilidade</summary><pre>{JSON.stringify({missing:state.missing,health:state.health,evaluation:state.evaluation},null,2)}</pre></details>
    </section>
  </>;
}

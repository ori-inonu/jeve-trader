import {useEffect, useLayoutEffect, useRef, useState} from 'react';
import {Power, Volume2} from 'lucide-react';
import {type Snapshot, type FlowHypothesis} from './transport';
import {Chart} from './Chart';
import {liveSnapshot} from './liveView';
import {paintLatency,discardSnapshot} from './visualLatency';
import {PilotControls} from './PilotControls';

let audio:AudioContext|null = null;
export async function enableAudio() { audio ??= new AudioContext(); await audio.resume(); }
function tone(side:string) {
  if (!audio || audio.state!=='running') return;
  const oscillator=audio.createOscillator(), gain=audio.createGain();
  oscillator.frequency.value=side==='buy'?880:440;
  gain.gain.setValueAtTime(.06,audio.currentTime);gain.gain.exponentialRampToValueAtTime(.001,audio.currentTime+.3);
  oscillator.connect(gain);gain.connect(audio.destination);oscillator.start();oscillator.stop(audio.currentTime+.3);
}
const num=(v:unknown)=>v==null?null:Number.isFinite(Number(v))?Number(v):null;
const fmt=(v:number|null,s='')=>v==null?'—':`${v.toLocaleString('pt-BR',{maximumFractionDigits:1})}${s}`;
const sideName=(side:string|null)=>side==='buy'?'compra':side==='sell'?'venda':'sem direção';
type Run=(method:string,params?:Record<string,unknown>)=>Promise<void>;
function Phenomenon({h,data}:{h:FlowHypothesis;data:Snapshot}) {
  const family=h.kind==='progression'?'continuation':h.kind;
  const context=data.hypothesis_context.find(c=>c.family===family&&c.aggressor_side===h.aggressor_side);
  const dimension=context?.dimensions;
  return <div className="phenomenon" title={`${h.description}\nPremissa: ${context?.literal_premise||h.description}\nEvidências: ${JSON.stringify(h.evidence)}\nAusências: ${h.missing.join(', ')}`}>
    <div><b>{h.kind==='progression'?'Progressão':h.kind==='absorption'?'Absorção':'Exaustão'} · {sideName(h.aggressor_side)}</b><span className={['observed','potential'].includes(h.status)?'green':'amber'}>{h.status==='observed'?'observada':h.status==='potential'?'hipótese local':h.status==='not_observed'?'não observada':'insuficiente'}</span></div>
    <div className="noul-lines">{(['support','contradiction','insufficient'] as const).map((key,i)=><label key={key}><span>{['Apoio','Contradição','Insuficiência'][i]}</span><meter min={0} max={1} value={dimension?.[key]??0} className={!dimension?'unavailable':key}/><small>{fmt(dimension?.[key]==null?null:dimension[key]*100,'%')}</small></label>)}</div>
    <small>{h.scenario_side?`Cenário: ${sideName(h.scenario_side)}`:h.kind==='exhaustion'?'Enfraquece agressor; reversão não confirmada':'Sem cenário confirmado'} · {h.missing.length?`${h.missing.length} limitações`: 'avaliação local'}</small>
    <details><summary>Premissa e evidências</summary><p>{context?.literal_premise||h.description}</p><pre>{JSON.stringify(h.evidence,null,2)}</pre><small>{h.missing.join(' · ')}</small></details>
  </div>;
}

export function LivePanel({data:raw,now,run}:{data:Snapshot;now:number;run:Run}) {
  const data=liveSnapshot(raw,now), d=data.directional, f=data.market.computed_features;
  const flow=data.market.order_flow, caps=data.source.capabilities;
  const [reduced,setReduced]=useState(()=>localStorage.getItem('jeve-reduced-motion')==='true'||matchMedia('(prefers-reduced-motion: reduce)').matches);
  const [audioReady,setAudioReady]=useState(false),[audioError,setAudioError]=useState(false);
  const [latency,setLatency]=useState<{p95:number|null;count:number}>({p95:null,count:0});
  const played=useRef<number|null>(null), episode=data.alert.episode;
  useEffect(()=>{if(episode&&data.alert.active&&played.current!==episode.id){played.current=episode.id;if(data.context_settings.sound_enabled)tone(episode.side);}},[episode,data.alert.active,data.context_settings.sound_enabled]);
  useLayoutEffect(()=>{let second=0;const first=requestAnimationFrame(()=>{second=requestAnimationFrame(()=>setLatency(paintLatency(raw.sequence)));});return()=>{cancelAnimationFrame(first);cancelAnimationFrame(second);discardSnapshot(raw.sequence);};},[raw.sequence]);
  const historical=['synthetic','replay'].includes(data.market.application_mode);
  const tape=!!caps.tape, delta=tape?num(f.delta_contracts):null, intensity=tape?num(f.contracts_per_second):null;
  const book=flow?.book, books=book?[...book.asks.slice(0,5)].reverse().map(x=>({...x,side:'sell'})).concat(book.bids.slice(0,5).map(x=>({...x,side:'buy'}))):[];
  const maxBook=Math.max(1,...books.map(x=>x.quantity)), brokerMax=Math.max(1,...(flow?.brokers||[]).map(x=>Math.abs(x.net_contracts)));
  const temperature=d.temperature;
  const marks=d.geometry?['entry','stop','target'].map((key,i)=>({name:['Entrada','Stop','Alvo'][i],yAxis:num(d.geometry?.[key+'_points']),lineStyle:{color:['#8ea1ff','#ff6b87','#53ddbb'][i]},label:{formatter:['Entrada','Stop','Alvo'][i]}})).filter(m=>m.yAxis!=null):[];
  const quoteAge=data.market.last_quote?.ts_ms==null?null:Math.max(0,now-data.market.last_quote.ts_ms);
  return <section className={`flow-desk ${reduced?'reduced-motion':''}`} aria-label="Mesa de fluxo WIN">
    <div className="desk-strip">
      <strong>{data.market.symbol}</strong><span>{historical?data.market.application_mode==='synthetic'?'SINTÉTICO':'REPLAY':data.source.excel_running?'EXCEL RTD':'DESCONECTADO'}</span>
      <span className={caps.quote_fresh?'green':'amber'}>Cotação {fmt(quoteAge,' ms')}</span><span>{caps.full_tape?'Tape integral da fixture':'Cobertura parcial'}</span>
      <span title="Comprometido inclui reservas; faturamento real desconhecido">US$ {data.budget.committed_usd} / {data.budget.total_limit_usd}</span>
      <button className={`jev-power ${data.jev.enabled?'on':''}`} onClick={()=>void run('jev.set_enabled',{enabled:!data.jev.enabled})}><Power size={14}/>JEV {data.jev.enabled?'ON':'OFF'}</button>
    </div>
    {historical&&<div className="desk-note amber">{data.market.application_mode==='synthetic'?'Demonstração sintética ativada manualmente':'Replay histórico'} · não são dados atuais da B3.</div>}
    <div className={`desk-alert ${data.alert.active?'triggered':''}`} role="status">
      <b>{data.alert.active?`Alerta contextual: ${sideName(episode?.side||null)}`:!data.jev.enabled?'JEV desligado · coleta e cálculos locais continuam':'Aguardando contexto válido'}</b>
      <span>{data.jev.status==='draining'?'Chamada enviada em conclusão; pode consumir API':data.jev.pending?'Analisando estado mais recente': 'Experimental · operação manual'}</span>
    </div>
    <div className="desk-main">
      <div className="price-stream"><div className="desk-caption">PREÇO + NÍVEIS OBSERVADOS <span>{fmt(tape?num(f.price_progression_ticks):null,' ticks / 5s')}</span></div>
        <Chart reducedMotion={reduced} label="Preço observado, entrada, stop e alvo contextuais" option={{grid:{left:52,right:12,top:20,bottom:26},tooltip:{trigger:'axis'},xAxis:{type:'time',axisLabel:{color:'#8492a8',fontSize:9}},yAxis:{type:'value',scale:true,axisLabel:{color:'#8492a8',fontSize:9},splitLine:{lineStyle:{color:'#202b3a'}}},series:[{id:'price',type:'line',showSymbol:false,data:data.chart_points,lineStyle:{color:'#97acff',width:2},markLine:{symbol:'none',data:marks}}]}}/>
        {!data.chart_points.length&&<span className="stream-empty">Conecte uma fonte de preços</span>}
        <div className="desk-levels">{['entry','stop','target'].map((key,i)=><span key={key}>{['Entrada','Stop','Alvo'][i]}<b>{fmt(num(d.geometry?.[key+'_points']))}</b></span>)}<span>Lote<b>{data.decision.quantity} · manual</b></span></div>
      </div>
      <div className={`decision-temperature ${temperature==null?'unavailable':temperature>=0?'buy':'sell'}`}>
        <div className="desk-caption">JEV · DIREÇÃO</div><strong>{temperature==null?'—':`${temperature>0?'+':''}${fmt(temperature)}`}</strong>
        <div className="bipolar"><span>+100 compra</span><div className="bipolar-track"><div className="zero-line"/><i style={{bottom:`${50+(temperature??0)/2}%`,opacity:temperature==null?0:1}}/><div className="thermal-fill" style={{bottom:temperature!=null&&temperature<0?`${50+temperature/2}%`:'50%',height:`${Math.abs(temperature??0)/2}%`}}/></div><span>−100 venda</span></div>
        <small>{temperature==null?'indisponível':Math.abs(temperature)<60?'equilíbrio contextual':temperature>0?'favorável à compra':'favorável à venda'}</small><small>Aguardar {fmt(d.wait==null?null:d.wait*100,'%')}</small>
      </div>
      <div className="book-ladder"><div className="desk-caption">LIVRO <span>{book?'snapshot':'indisponível'}</span></div>
        {books.length?books.map(row=><div className={`book-row ${row.side}`} key={row.side+row.price_points}><i style={{width:`${row.quantity/maxBook*100}%`}}/><span>{fmt(Number(row.price_points))}</span><b>{row.quantity}</b></div>):<div className="stream-empty">Selecione a tabela do livro no Excel</div>}
        <small>{book?`Captura ${fmt(Math.max(0,now-book.captured_at_ms),' ms')} · origem ${book.market_ts_ms==null?'sem horário':fmt(Math.max(0,now-book.market_ts_ms),' ms')}`:'Sem profundidade observada'}</small>
        <div className="depth-history" title="Mudanças de quantidades visíveis; causa desconhecida">{flow?.book_history.slice(-24).map((b,i)=>{const buy=b.bids.reduce((s,x)=>s+x.quantity,0),sell=b.asks.reduce((s,x)=>s+x.quantity,0);return <i key={i} style={{height:`${Math.max(2,Math.abs(buy-sell)/Math.max(1,buy+sell)*100)}%`,background:buy>=sell?'#53ddbb':'#ff6b87'}}/>;})}</div>
        <small>Histórico de desequilíbrio visível · não identifica cancelamentos</small>
      </div>
    </div>
    <div className="flow-pulse">
      <div><span>Delta · 5s</span><b className={(delta??0)>=0?'green':'red'}>{fmt(delta)}</b><div className="pulse-track"><i style={{width:`${Math.min(100,Math.abs(delta??0)/Math.max(1,Number(f.total_contracts)||0)*100)}%`,background:(delta??0)>=0?'#53ddbb':'#ff6b87'}}/></div></div>
      <div><span>Contratos / segundo</span><b>{fmt(intensity)}</b><div className="pulse-track"><i style={{width:`${Math.min(100,(intensity??0)/100*100)}%`}}/></div><small>Escala visual: 100/s</small></div>
      <div className="delta-spark"><span>Delta acumulado · janela 5s</span><Chart reducedMotion={reduced} label="Delta acumulado observado" option={{grid:{left:8,right:8,top:6,bottom:6},xAxis:{type:'time',show:false},yAxis:{type:'value',show:false},series:[{type:'line',showSymbol:false,data:(flow?.delta_path||[]).map(x=>[x.ts_ms,x.delta_contracts]),lineStyle:{color:(delta??0)>=0?'#53ddbb':'#ff6b87',width:2}}]}}/></div>
    </div>
    <div className="desk-bottom">
      <div className="tape-stream"><div className="desk-caption">NEGÓCIOS <span>{tape?'amostra · 5s':'indisponível'}</span></div><div className="tape-columns"><span>Hora / preço</span><span>Contratos / agressor</span></div>
        {(flow?.recent_trades||[]).slice(-8).reverse().map(t=><div className={`tape-row ${t.aggressor}`} key={t.id} title={`ID ${t.id} · compradora ${t.buyer_broker||'ausente'} · vendedora ${t.seller_broker||'ausente'}`}><i style={{width:`${Math.min(100,t.quantity/50*100)}%`}}/><span>{new Date(t.ts_ms).toLocaleTimeString('pt-BR')}<b>{fmt(Number(t.price_points))}</b></span><strong>{t.quantity} <small>{sideName(t.aggressor)}</small></strong></div>)}
        {!flow?.recent_trades.length&&<small>Negócios com identidade verificável ausentes.</small>}
      </div>
      <div className="broker-stream"><div className="desk-caption">CORRETORAS <span>saldo da janela</span></div>
        {(flow?.brokers||[]).slice(0,6).map(b=><div className="broker-row" key={b.broker}><span>{b.broker}</span><div><i className={b.net_contracts>=0?'buy':'sell'} style={{width:`${Math.abs(b.net_contracts)/brokerMax*100}%`}}/></div><b className={b.net_contracts>=0?'green':'red'}>{b.net_contracts>0?'+':''}{b.net_contracts}</b></div>)}
        {!flow?.brokers.length&&<small>Campos de corretora ausentes. Posição dos investidores desconhecida.</small>}
        {!!flow?.brokers.length&&<small>Contrapartes observadas · {flow.broker_identified_trades} negócios com ambas identificadas. Não representa posição real.</small>}
        {!!flow?.volume_at_price.length&&<details><summary>Volume At Price · agregado separado</summary>{flow.volume_at_price.slice(0,12).map(v=><div className="vap-row" key={v.price_points}>{fmt(v.price_points)}<b>{v.quantity}</b></div>)}<small>Janela da exportação, não somada ao tape.</small></details>}
      </div>
    </div>
    <div className="desk-caption">FENÔMENOS · OBSERVADO LOCALMENTE + CONTEXTO INDEPENDENTE</div>
    <div className="phenomena-grid">{['absorption','exhaustion','progression'].map(kind=><div key={kind}>{['sell','buy'].map(side=>{const h=data.market.hypotheses?.find(h=>h.kind===kind&&h.side===side);return h?<Phenomenon key={side} h={h} data={data}/>:<div className="phenomenon" key={side}><b>{kind==='absorption'?'Absorção':kind==='exhaustion'?'Exaustão':'Progressão'} · {sideName(side)}</b><small>Dados indisponíveis</small></div>;})}</div>)}</div>
    <div className="desk-controls"><label><input type="checkbox" checked={reduced} onChange={e=>{setReduced(e.target.checked);localStorage.setItem('jeve-reduced-motion',String(e.target.checked));}}/>Movimento reduzido</label><span title="Após recebimento no frontend até dois frames; fonte e JEV medidos separadamente">Render p95 {fmt(latency.p95,' ms')} · {latency.count} amostras</span><span>JEV {fmt(d.latency_ms,' ms')}</span>{data.context_settings.sound_enabled&&<button onClick={()=>void enableAudio().then(()=>{setAudioReady(true);setAudioError(false);}).catch(()=>setAudioError(true))}><Volume2 size={14}/>{audioError?'Tentar áudio':audioReady?'Áudio ativo':'Habilitar áudio'}</button>}</div>
    <PilotControls data={raw} run={run}/>
    {data.jev_error&&<p role="status" className="desk-note amber">{data.jev_error}</p>}
    <details className="desk-explanation"><summary>Qualidade da fonte, janelas e significado do índice</summary><p>100 × (P_compra − P_venda). Pesos contextuais e Nouls independentes não são chance de lucro. Entrada, stop e alvo são hipóteses; não enviam ordens.</p><p>5s atual, 5s anterior e 30s. Resposta do preço: {fmt(tape?num(f.signed_points_per_100_aggressed_contracts):null,' pontos / 100 agredidos')}. Intensidade vs. janela anterior: {fmt(tape?num(f.intensity_ratio_to_previous_5s):null,'×')}.</p><p>COM efetivo: {fmt(flow?.capture_evidence.polling_effective_ms??null,' ms')}; mudanças amostradas: {fmt(flow?.capture_evidence.rtd_change_interval_ms??null,' ms')}. Atraso da fonte desconhecido. Modalidade: {flow?.capture_evidence.window_mode||'não informada'}; filtros: {flow?.capture_evidence.filters||'não informados'}.</p><p>{data.market.warnings.join(' · ')}</p></details>
    {data.source.ocr?.enabled&&<details className="desk-explanation"><summary>OCR auxiliar · {data.source.ocr.status} · parcial</summary><pre>{data.source.ocr.observation?.text||data.source.ocr.error||'Capturando região selecionada…'}</pre><p>Legibilidade não calibrada; perdas de negócios desconhecidas. Nenhum volume é somado ao Excel.</p></details>}
  </section>;
}

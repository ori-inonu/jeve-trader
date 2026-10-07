import {useEffect, useRef, useState} from 'react';
import {Pause, Play, Volume2} from 'lucide-react';
import {type Snapshot} from './transport';
import {Chart} from './Chart';

let audio:AudioContext|null = null;
export async function enableAudio() {
  audio ??= new AudioContext();
  await audio.resume();
}
function tone(side:string) {
  if (!audio || audio.state !== 'running') return;
  const oscillator = audio.createOscillator(), gain = audio.createGain();
  oscillator.type = 'sine'; oscillator.frequency.value = side==='buy'?880:440;
  gain.gain.setValueAtTime(.06, audio.currentTime);
  gain.gain.exponentialRampToValueAtTime(.001, audio.currentTime+.3);
  oscillator.connect(gain); gain.connect(audio.destination);
  oscillator.start(); oscillator.stop(audio.currentTime+.3);
}
const number = (value:unknown) => value==null ? null : Number.isFinite(Number(value)) ? Number(value) : null;
const display = (value:number|null, suffix='') => value==null ? 'indisponível' : `${value.toLocaleString('pt-BR',{maximumFractionDigits:2})}${suffix}`;
const clock = (value:number|null) => value ? new Date(value).toLocaleTimeString('pt-BR') : '—';

function Gauge({label, value, extent=100, detail, suffix=''}:{label:string;value:number|null;extent?:number;detail:string;suffix?:string}) {
  const width = value==null ? 0 : Math.min(100, Math.abs(value)/Math.max(1,extent)*100);
  return <div className="live-gauge"><span>{label}</span><strong>{display(value,suffix)}</strong><div className="bar"><i className={value!=null&&value<0?'red':'green'} style={{width:`${width}%`}}/></div><small>{detail}</small></div>;
}

export function LivePanel({data}:{data:Snapshot}) {
  const [frozen,setFrozen] = useState<Snapshot|null>(null);
  const [audioReady,setAudioReady] = useState(false);
  const [audioError,setAudioError] = useState(false);
  const played = useRef<number|null>(null);
  const episode = data.alert.episode;
  useEffect(() => {
    if (episode && data.alert.active && played.current!==episode.id) {
      played.current=episode.id;
      if(data.context_settings.sound_enabled) tone(episode.side);
    }
  }, [episode, data.alert.active, data.context_settings.sound_enabled]);
  const inspected = frozen ?? data, d = inspected.directional;
  const f = inspected.market.computed_features, caps = inspected.source.capabilities;
  const tape = !!caps.tape;
  const delta = tape ? number(f.delta_contracts) : null;
  const total = number(f.total_contracts) ?? 0;
  const side = d.selected==='buy_continuation'?'buy':d.selected==='sell_continuation'?'sell':null;
  const absorption = inspected.hypothesis_context.find(h=>h.family==='absorption' && h.side===side)?.dimensions;
  const exhaustion = inspected.hypothesis_context.find(h=>h.family==='exhaustion' && h.side===side)?.dimensions;
  const temperature = d.temperature;
  const liveLabel = data.alert.active ? `Alerta contextual experimental: ${episode?.side==='buy'?'compra':'venda'}` : 'Sem alerta contextual válido';
  const points = inspected.chart_points;
  return <>
    <div className={`live-alert ${data.alert.active?'triggered':''}`} role="status">
      <strong>{liveLabel}</strong><span>Operação manual · contexto sem calibração financeira</span>
      {data.context_settings.sound_enabled && <button className="button secondary" onClick={()=>void enableAudio().then(()=>{setAudioReady(true);setAudioError(false);}).catch(()=>setAudioError(true))}><Volume2 size={16}/>{audioError?'Áudio indisponível · tentar novamente':audioReady?'Áudio habilitado':'Habilitar áudio nesta janela'}</button>}
    </div>
    <section className="panel live-panel">
      {['synthetic','replay'].includes(inspected.market.application_mode) && <p className="notice">{inspected.market.application_mode==='synthetic'?'Demonstração sintética':'Replay histórico'} · estes dados não são captura atual do mercado.</p>}
      <div className="panel-heading"><div><span className="eyebrow">FORÇA DIRECIONAL CONTEXTUAL — EXPERIMENTAL</span><h2>{temperature==null?'Aguardando evidência':`${temperature>0?'+':''}${temperature.toFixed(1)}`}</h2></div><button className="button secondary" onClick={()=>setFrozen(frozen?null:data)}>{frozen?<Play size={16}/>:<Pause size={16}/>} {frozen?'Retomar inspeção':'Congelar inspeção'}</button></div>
      {frozen && <p className="notice">Inspeção histórica congelada às {clock(frozen.generated_at_ms)}. A faixa de alertas acima continua ao vivo.</p>}
      <div className="thermometer" aria-label={`Força direcional ${display(temperature)}; experimental`}>
        <div className="thermometer-track"><i style={{left:`${50+(temperature??0)/2}%`,opacity:temperature==null?0:1}}/></div>
        <div className="thermometer-labels"><span>−100 · venda</span><span>0 · equilíbrio</span><span>+100 · compra</span></div>
      </div>
      <div className="live-summary"><span>Aguardar contextual <b>{display(d.wait==null?null:d.wait*100,'%')}</b></span><span>Validade até <b>{clock(d.expires_at_ms)}</b></span><span>Horizonte <b>{inspected.context_settings.horizon_seconds}s</b></span><span>Economia <b>aguardar · lote 0</b></span></div>
      <div className="live-summary"><span>Idade do fluxo na inspeção <b>{display(inspected.market.flow_ts_ms==null?null:Math.max(0,inspected.generated_at_ms-inspected.market.flow_ts_ms),' ms')}</b></span><span>Latência da avaliação aceita <b>{display(d.latency_ms,' ms')}</b></span><span>Última avaliação aceita <b>{clock(d.evaluated_at_ms)}</b></span><span>Recuo da API <b>{data.jev_retry_in_ms ? display(data.jev_retry_in_ms,' ms') : 'sem pausa'}</b></span></div>
      {data.jev_error && <p role="status" className="notice error">{data.jev_error}</p>}
      <p className="muted">100 × (peso contextual de compra − peso contextual de venda). Esses pesos e Noul não são probabilidade de lucro.</p>
      <div className="capabilities">{[['Cotação atual','quote_fresh'],['Negócios','tape'],['Agressor','aggression'],['PriceDepth','price_depth'],['Tape integral','full_tape']].map(([label,key])=><span key={key} className={caps[key]===true?'tag green':'tag amber'}>{label}: {caps[key]===true?'disponível':'ausente / parcial'}</span>)}</div>
      <div className="live-gauges">
        <Gauge label="Delta observado · 5s" value={delta} extent={total} detail="Compra agressora − venda agressora; amostra parcial"/>
        <Gauge label="Intensidade · 5s" value={tape?number(f.contracts_per_second):null} extent={100} suffix=" contratos/s" detail="Escala visual de 100 contratos/s; sem limiar operacional"/>
        <Gauge label="Progressão · 5s" value={tape?number(f.price_change_points):null} extent={100} suffix=" pts" detail="Deslocamento da amostra; escala visual de 100 pontos"/>
        <Gauge label="Absorção · apoio contextual" value={absorption?.support==null?null:absorption.support*100} suffix="%" detail="Hipótese independente; não implica reversão"/>
        <Gauge label="Exaustão · apoio contextual" value={exhaustion?.support==null?null:exhaustion.support*100} suffix="%" detail="Depende da hipótese e da cobertura; não implica reversão"/>
        <Gauge label="Desequilíbrio do livro" value={caps.price_depth?number(f.book_imbalance):null} extent={1} detail="Somente níveis observados; Excel RTD não confirma profundidade"/>
      </div>
      <div className="trade-values">{[['Entrada','entry_points'],['Stop estrutural','stop_points'],['Alvo estrutural','target_points']].map(([label,key])=><div key={key}><span>{label}</span><strong>{d.geometry ? String(d.geometry[key]??'—') : '—'}</strong></div>)}</div>
      <small>Geometria experimental baseada nos níveis observados. Sem comando de compra a mercado. Stop e alvo não garantem execução.</small>
      <Chart label="Preço observado com horários de origem" option={{grid:{left:65,right:16,top:24,bottom:48},tooltip:{trigger:'axis'},xAxis:{type:'time',axisLabel:{color:'#8d96ad'}},yAxis:{type:'value',scale:true,axisLabel:{color:'#8d96ad'},splitLine:{lineStyle:{color:'#252c3d'}}},dataZoom:[{type:'inside'},{type:'slider',height:18,bottom:0}],series:[{id:'observed-price',type:'line',showSymbol:false,data:points,lineStyle:{color:'#91a2ff',width:2}}]}}/>
      {!points.length && <p className="muted">Sem preços observados. Conecte sua fonte na configuração.</p>}
    </section>
  </>;
}

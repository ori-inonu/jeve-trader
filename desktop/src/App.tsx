import {useEffect,useRef,useState, type FormEvent} from 'react';
import {Activity,FlaskConical,Radio,Settings2,Wallet,Zap} from 'lucide-react';
import {connect,command,type Snapshot} from './transport';
import {UpdateNotice} from './UpdateNotice';
import {Chart} from './Chart';
import {LivePanel} from './LivePanel';
import {LiveConfiguration} from './LiveConfiguration';
import {MultimarketPanel} from './MultimarketPanel';
import {liveSnapshot} from './liveView';
import {createVisualCaptureReceiver,discardBackgroundReceipts,visualPilotReport,visualSessionId} from './visualLatency';
const currency=(value:string|number)=>Number(value).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
const time=(ms:number)=>ms ? new Date(ms).toLocaleTimeString('pt-BR') : '—';
type Run=(method:string,params?:Record<string,unknown>)=>Promise<void>;
function ledgerDescription(payload:unknown) {
  const p=payload as Record<string,unknown>;
  if('equity_brl' in p)return `Banca ${currency(String(p.equity_brl))} · margem disponível ${currency(String(p.available_margin_brl))}`;
  return `${p.symbol?`${p.symbol} · `:''}${p.side?`${p.side==='buy'?'Compra':'Venda'} · `:''}${p.quantity} contrato(s) a ${p.price} pontos · custos ${currency(String(p.fees))}${p.margin?` · margem ${currency(String(p.margin))}`:''}`;
}

function Card({label,value,detail,tone=''}:{label:string;value:string;detail:string;tone?:string}) {return <div className="metric"><span>{label}</span><strong className={tone}>{value}</strong><small>{detail}</small></div>;}
function Field({label,name,value,type='text'}:{label:string;name:string;value?:string;type?:string}) {return <label className="field"><span>{label}</span><input name={name} type={type} defaultValue={value} required autoComplete="off"/></label>;}
function values(event:FormEvent<HTMLFormElement>){event.preventDefault();return Object.fromEntries(new FormData(event.currentTarget)) as Record<string,string>;}

function Decision({data,run,now}:{data:Snapshot;run:Run;now:number}) {
  return <><div className="page-title desk-title"><div><span className="eyebrow">JEV / WIN</span><h1>Mesa de fluxo</h1></div><button className="button secondary" disabled={!data.jev.enabled||!data.jev.configured||data.jev.pending} onClick={()=>void run('jev.evaluate')}><Zap size={14}/>{data.jev.pending?'Analisando…':'Avaliar agora'}</button></div><LivePanel data={data} run={run} now={now}/></>;
}

function Capital({data,run}:{data:Snapshot;run:Run}) {
  const position=data.account.positions[0];
  return <><div className="page-title"><div><span className="eyebrow">PATRIMÔNIO / CONCILIAÇÃO</span><h1>Capital e exposição</h1><p>Cada nova avaliação usa a banca inteira informada.</p></div><span className="tag">CONTA MANUAL</span></div><div className="metrics"><Card label="BANCA CONCILIADA" value={currency(data.account.equity_brl)} detail="Custos de execução descontados uma vez"/><Card label="PICO REGISTRADO" value={currency(data.account.peak_brl)} detail="Preservado após perdas"/><Card label="MARGEM DISPONÍVEL" value={currency(data.account.available_margin_brl)} detail="Confirme o valor na corretora"/><Card label="EXPOSIÇÃO REGISTRADA" value={`${position?.quantity??0} contratos`} detail="Execuções reais informadas por você"/></div><div className="analytics"><section className="panel"><h3>Conciliar a banca</h3><p className="muted">Saldo realizado, sem lucro flutuante. A alteração fica registrada no histórico.</p><form key={data.account.revision} onSubmit={e=>{const v=values(e);void run('account.update',{...v,revision:data.account.revision});}}><Field label="Banca atual (R$)" name="equity_brl" value={data.account.equity_brl}/><Field label="Margem disponível (R$)" name="available_margin_brl" value={data.account.available_margin_brl}/><button className="button" disabled={!!position}>Registrar conciliação</button></form><small>Enquanto houver posição aberta, registre as saídas antes de alterar o saldo.</small></section><section className="panel"><h3>{position?'Registrar saída executada':'Registrar entrada executada'}</h3><p className="muted">Informe somente negócios já executados no Profit Pro.</p><form onSubmit={e=>{const v=values(e);const key=crypto.randomUUID();void run(position?'position.close':'position.open',position?{key,quantity:Number(v.quantity),price:v.price,fees:v.fees}:{key,side:v.side,quantity:Number(v.quantity),price:v.price,fees:v.fees,margin:v.margin,symbol:v.symbol});}}>{position?<div className="position"><strong>{position.symbol} · {position.side==='buy'?'Compra':'Venda'} · {position.quantity} contratos</strong><p>Entrada {position.entry_points} · margem {currency(position.reserved_margin_brl)}</p></div>:<><Field label="Contrato" name="symbol" value={data.market.symbol==='WIN_SIM'?'WINV26':data.market.symbol}/><label className="field"><span>Lado executado</span><select name="side"><option value="buy">Compra</option><option value="sell">Venda</option></select></label><Field label="Margem total reservada (R$)" name="margin" value="155"/></>}<Field label="Quantidade executada" name="quantity" value="1" type="number"/><Field label="Preço executado (pontos)" name="price"/><Field label="Custos totais desta execução (R$)" name="fees" value="0"/><button className="button">Registrar execução manual</button></form></section></div><section className="panel"><h3>Histórico local</h3><div className="table-wrap"><table><thead><tr><th>Horário</th><th>Evento</th><th>Valores registrados</th></tr></thead><tbody>{data.history.filter(x=>x.kind.startsWith('actual_manual')||x.kind==='account_reconciliation').map(event=><tr key={event.id}><td>{time(event.ts_ms)}</td><td>{{actual_manual_entry:'Entrada executada',actual_manual_exit:'Saída executada',account_reconciliation:'Conciliação manual'}[event.kind as 'actual_manual_entry']||event.kind}</td><td>{ledgerDescription(event.payload)}</td></tr>)}</tbody></table></div></section></>;
}

const policyLabels:Record<string,string>={fixed_lot:'Lote fixo',fixed_cash:'Valor fixo',initial_fraction:'Fração da banca inicial',current_fraction:'Fração da banca atual',kelly:'Kelly',fractional_kelly:'Kelly fracionado',drawdown_kelly:'Kelly e drawdown',volatility:'Volatilidade / ATR',optimal_f:'Optimal f',fixed_ratio:'Fixed Ratio',paroli:'Soros / Paroli',partial_reinvest:'Reinvestimento parcial',pyramiding:'Piramidagem',martingale:'Martingale',dalembert:'D’Alembert',fibonacci:'Fibonacci',labouchere:'Labouchère'};
function Research({data}:{data:Snapshot}) {return <><div className="page-title"><div><span className="eyebrow">LABORATÓRIO / VALIDAÇÃO TEMPORAL</span><h1>Pesquisa de decisão</h1><p>Crescimento líquido, drawdown e capacidade de continuar operando.</p></div><span className="tag amber">EXPERIMENTOS</span></div><div className="analytics"><section className="panel"><h3>Modelo financeiro</h3><div className="steps">{['Replay causal e rótulos maduros','Treino → calibração → teste por sessão','Logística multiclasse: alvo, stop, tempo','Comparação com e sem atributos JEV','Crescimento, calibração, drawdown e ruína'].map((text,i)=><div key={text}><span>{String(i+1).padStart(2,'0')}</span><p>{text}</p></div>)}</div><div className="notice">Não há modelo financeiro promovido. Execute o laboratório offline com seus dados autorizados; resultados sintéticos verificam o código, sem comprovar rentabilidade.</div></section><section className="panel"><h3>Cenários de alavancagem</h3><p className="muted">R$300 → R$4.000 é um cenário para investigar.</p><div className="scenario"><strong>13,33×</strong><span>multiplicação da banca no cenário</span></div><p>Compare trajetórias líquidas, custos, probabilidade de atingir o valor e perda da capacidade de operar. O cenário não força entradas nem cria uma parada por lucro.</p><div className="notice">Progressões após perdas ficam restritas ao laboratório. O lote operacional depende da oportunidade atual.</div></section></div><section className="panel"><div className="panel-heading"><h3>Catálogo de dimensionamento</h3><span className="tag">REGRAS EXPLÍCITAS</span></div><div className="policy-grid">{data.research.risk_catalog.map(name=><div key={name}><FlaskConical size={18}/><strong>{policyLabels[name]||name}</strong><small>{['martingale','dalembert','fibonacci','labouchere'].includes(name)?'Comparação de laboratório':'Avaliação temporal necessária'}</small></div>)}</div><p className="muted">Stops: estrutural, volatilidade, temporal e trailing; saídas parciais. Métricas: VaR, CVaR, drawdown, ruína e capital abaixo da margem + reserva.</p></section></>;}

function Configuration({data,run}:{data:Snapshot;run:Run}) {
  return <><div className="page-title"><div><span className="eyebrow">FONTES / MODELO / CUSTOS</span><h1>Configuração</h1><p>Origens, horários e parâmetros financeiros identificados.</p></div></div><LiveConfiguration data={data} run={run}/><section className="panel"><h3>Custos e margem por conta</h3><p className="muted">Valores iniciais são hipóteses manuais. Confirme tabela vigente, conta e exigência da corretora. Spread já está no preço de entrada; slippage incide nos dois lados.</p><form className="cost-form" onSubmit={e=>{const v=values(e);void run('costs.update',{...data.costs,...v,verified:v.verified==='true'});}}>{[['Tarifa B3 entrada / contrato','b3_entry_brl'],['Tarifa B3 saída / contrato','b3_exit_brl'],['Corretagem entrada / contrato','brokerage_entry_brl'],['Corretagem saída / contrato','brokerage_exit_brl'],['Slippage por lado (pontos)','slippage_points'],['Margem / contrato (R$)','margin_per_contract_brl'],['Fonte dos parâmetros','source'],['Vigência inicial','effective_from'],['Identificador da conta','account_id'],['Versão dos custos','version']].map(([label,name])=><Field key={name} label={label} name={name} value={String(data.costs[name])}/>)}<label className="field"><span>Conferido por você</span><select name="verified" defaultValue={String(data.costs.verified)}><option value="false">Hipótese manual não conferida</option><option value="true">Conferido na fonte / conta informada</option></select></label><button className="button">Salvar parâmetros</button></form></section><section className="panel"><h3>Replay local</h3><form onSubmit={e=>void run('source.replay',values(e))}><Field label="Caminho absoluto do CSV autorizado" name="path"/><Field label="Contrato do arquivo" name="symbol" value="WINV26"/><button className="button secondary">Carregar replay</button></form></section></>;
}

export function App(){
  const [data,setData]=useState<Snapshot|null>(null),[page,setPage]=useState('decision'),[error,setError]=useState(''),[tick,setTick]=useState(Date.now());
  const sequence=useRef(-1);
  useEffect(()=>{let disposed=false;let cleanup:(()=>void)|undefined;
    const receiveCapture=createVisualCaptureReceiver();
    const receive=(value:Snapshot)=>{
      if(value.schema_version!==2||value.sequence<=sequence.current)return;
      sequence.current=value.sequence;
      if(!disposed){
        const pilot=value.pilot, stamp=value.market.order_flow?.capture_evidence.received_at_ms;
        const key=`${pilot.id}:${value.market.source_generation}:${stamp}`;
        const active=pilot.status==='recording';
        const eligible=active&&value.market.application_mode==='excel_observation'&&value.source.excel_running
          &&value.market.symbol===pilot.symbol&&stamp!=null&&stamp>=(pilot.started_at_ms??Infinity);
        receiveCapture(value.sequence,active?pilot.id:null,eligible,stamp==null?null:key);
        setData(value);
      }
    };
    const visibility=()=>{if(document.visibilityState!=='visible')discardBackgroundReceipts();};
    document.addEventListener('visibilitychange',visibility);
    connect(receive).then(stop=>{if(disposed)stop();else cleanup=stop;return command('snapshot').then(()=>command('updates.check'));}).catch(e=>setError(String(e)));
    return()=>{disposed=true;cleanup?.();document.removeEventListener('visibilitychange',visibility);};
  },[]);
  const run:Run=async(method,params={})=>{setError('');try{await command(method,params);}catch(e){setError(e instanceof Error?e.message:String(e));}};
  const pilotId=data?.pilot.status==='recording'?data.pilot.id:null;
  useEffect(()=>{
    if(!pilotId)return;
    let inFlight=false,disposed=false;
    const checkpoint=async()=>{
      if(inFlight||disposed)return;
      inFlight=true;
      try{await command('pilot.checkpoint',{pilot_id:pilotId,visual:visualPilotReport(pilotId,false),visual_session:visualSessionId()});}
      catch(e){if(!disposed)setError(`Checkpoint do piloto: ${e instanceof Error?e.message:String(e)}`);}
      finally{inFlight=false;}
    };
    const visibility=()=>{if(document.visibilityState!=='visible'){discardBackgroundReceipts();void checkpoint();}};
    const interval=setInterval(()=>void checkpoint(),5000);
    document.addEventListener('visibilitychange',visibility);
    return()=>{disposed=true;clearInterval(interval);document.removeEventListener('visibilitychange',visibility);};
  },[pilotId]);
  useEffect(()=>{const timer=setInterval(()=>setTick(Date.now()),100);return()=>clearInterval(timer);},[]);
  const stale=!!data&&data.market.application_mode==='excel_observation'&&!liveSnapshot(data,tick).source.capabilities.quote_fresh;
  const navigation=[['decision','Decisão',Activity],['capital','Capital',Wallet],['multimarket','Mercados',Radio],['research','Pesquisa',FlaskConical],['configuration','Configuração',Settings2]] as const;
  return <div className="shell"><aside><div className="brand"><div>J<span>V</span></div><strong>jeve<span>trader</span></strong></div><span className="nav-label">WORKSPACE</span><nav>{navigation.map(([id,label,Icon])=><button key={id} className={page===id?'active':''} onClick={()=>setPage(id)}><Icon size={19}/>{label}{page===id&&<i/>}</button>)}</nav><div className="sidebar-bottom"><div className="engine-symbol"><Zap size={19}/></div><strong>JEV contextual</strong><span>Python + TypeSafe</span><small>Execução manual / WIN</small></div></aside><main><header><span><span className={`status-dot ${data?.source.capabilities.quote_fresh&&!stale?'green':''}`}/> {data?.source.excel_running?(stale||!data.source.capabilities.quote_fresh?'Captura sem cotação atual':data.source.capabilities.tape?'Excel · fluxo parcial':'Excel · somente cotação'):data?.market.application_mode==='synthetic'?'Demonstração sintética':'Fonte desconectada'}</span><div>{data&&<UpdateNotice state={data.updates} run={run}/>}<span className="header-label">B3 · MINI ÍNDICE</span><span className="tag">WIN</span><div className="avatar">G</div></div></header><div className="content">{error&&<div role="alert" className="notice error">{error}<button onClick={()=>setError('')}>Fechar</button></div>}{data?.source.error&&<div role="status" className="notice error">{data.source.error}</div>}{data?.market.warnings.length ? <details className="notice source-warnings"><summary>Avisos da fonte ({data.market.warnings.length})</summary><ul>{data.market.warnings.slice(0,8).map((warning,index)=><li key={index}>{warning}</li>)}</ul>{data.market.warnings.length>8&&<span>Mais {data.market.warnings.length-8} avisos registrados na captura.</span>}</details>:null}{stale&&<div role="status" className="notice">Dados vencidos. Nenhuma indicação antiga permanece válida.</div>}{!data?<section className="panel loading"><Activity/><h2>Conectando ao motor Python…</h2><p>Os dados e as estimativas aparecerão após a resposta do serviço.</p></section>:page==='decision'?<Decision data={data} run={run} now={tick}/>:page==='capital'?<Capital data={data} run={run}/>:page==='multimarket'?<MultimarketPanel state={data.multimarket} run={run} now={tick}/>:page==='research'?<Research data={data}/>:<Configuration data={data} run={run}/>}<footer><span>Jeve Trader · laboratório de decisão v{data?.updates.current_version||'…'}</span><button onClick={()=>void run('source.demo')}>Carregar demonstração sintética</button><span>{data?`Atualizado ${time(data.generated_at_ms)}`:'Motor iniciando'}</span></footer></div></main></div>;
}

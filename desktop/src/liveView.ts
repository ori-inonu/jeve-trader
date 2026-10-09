import type {Snapshot} from './transport';

// The renderer must invalidate current indications even if the engine is silent.
// Leave the original immutable snapshot available for explicit historical inspection.
export function liveSnapshot(data:Snapshot, now:number):Snapshot {
  const live=data.market.application_mode==='excel_observation';
  if(!live && data.jev.enabled!==false) return data;
  const fresh=(stamp:number|null|undefined)=>stamp!=null && now>=stamp && now-stamp<=data.context_settings.validity_ms;
  const heartbeat=fresh(data.generated_at_ms);
  const caps=data.source.capabilities;
  const tape=!!caps.tape && (!live || heartbeat && fresh(data.market.flow_ts_ms));
  const book=!!caps.price_depth && (!live || heartbeat && fresh(data.market.order_flow?.book?.market_ts_ms));
  const context=data.jev.enabled!==false && heartbeat && tape && data.directional.expires_at_ms!=null && now<=data.directional.expires_at_ms;
  const quote=!!caps.quote_fresh && (!live || heartbeat && fresh(data.market.last_quote?.ts_ms));
  const flow=data.market.order_flow;
  return {...data,
    market:{...data.market,hypotheses:data.market.hypotheses?.filter(h=>h.kind==='liquidity_withdrawal'?book:tape),
      order_flow:flow?{...flow,recent_trades:tape?flow.recent_trades:[],delta_path:tape?flow.delta_path:[],
        brokers:tape?flow.brokers:[],book:book?flow.book:null,book_history:book?flow.book_history:[]}:flow},
    source:{...data.source,capabilities:{...caps,quote_fresh:quote,
      tape,aggression:!!caps.aggression && tape,price_depth:book}},
    directional:context?data.directional:{...data.directional,temperature:null,wait:null,selected:'unavailable',
      candidate_key:null,geometry:null,expires_at_ms:null,evaluated_at_ms:null,latency_ms:null},
    context:context?data.context:null,context_by_candidate:context?data.context_by_candidate:{},
    hypothesis_context:context?data.hypothesis_context:[],jev:{...data.jev,current:context && data.jev.current},
    alert:{...data.alert,active:context && quote && data.alert.active},
  };
}

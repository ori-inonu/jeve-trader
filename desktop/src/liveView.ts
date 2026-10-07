import type {Snapshot} from './transport';

// The renderer must invalidate current indications even if the engine is silent.
// Leave the original immutable snapshot available for explicit historical inspection.
export function liveSnapshot(data:Snapshot, now:number):Snapshot {
  if(data.market.application_mode !== 'excel_observation') return data;
  const fresh=(stamp:number|null|undefined)=>stamp!=null && now>=stamp && now-stamp<=data.context_settings.validity_ms;
  const heartbeat=fresh(data.generated_at_ms);
  const tape=heartbeat && fresh(data.market.flow_ts_ms);
  const context=data.jev.enabled!==false && heartbeat && tape && data.directional.expires_at_ms!=null && now<=data.directional.expires_at_ms;
  const caps=data.source.capabilities;
  const quote=!!caps.quote_fresh && heartbeat && fresh(data.market.last_quote?.ts_ms);
  return {...data,
    source:{...data.source,capabilities:{...caps,quote_fresh:quote,
      tape:!!caps.tape && tape,aggression:!!caps.aggression && tape,price_depth:!!caps.price_depth && heartbeat && fresh(data.market.quote_ts_ms ?? data.market.flow_ts_ms)}},
    directional:context?data.directional:{...data.directional,temperature:null,geometry:null},
    context:context?data.context:null,context_by_candidate:context?data.context_by_candidate:{},
    hypothesis_context:context?data.hypothesis_context:[],jev:{...data.jev,current:context && data.jev.current},
    alert:{...data.alert,active:context && quote && data.alert.active},
  };
}

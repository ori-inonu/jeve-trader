export type ChannelHealth = {
  channel:string; connected:boolean; state:string; valid:boolean; stale:boolean;
  coverage:string; last_receive_time_ms:number|null; gaps:number; resyncs:number;
  dropped_events:number; dropped_bytes:number; reason:string;
};
export type MultimarketState = {
  enabled:boolean; status:string; origin:string|null; error:string|null;
  transport?:{state?:string;reason?:string;worker_alive?:boolean;reader_alive?:boolean;rest_request_alive?:boolean};
  instrument:{symbol:string;instrument_id:string;base_asset:string|null;quote_asset:string|null}|null;
  source:{provider:string;venue:string;jurisdiction:string|null;retention_permission:string}|null;
  health:ChannelHealth[];
  book:{valid:boolean;state:string;bids:[string,string][];asks:[string,string][];reason:string;checksum_status:string;coverage:string}|null;
  features:Record<string,unknown>; missing:string[]; received_trades:number; remaining_seconds:number;
  retention_enabled:boolean; orders_enabled:boolean; target_probability:null;
  evaluation:{status:string;sample_size:number;result_type:string;missing:string[]};
};

export function observableBook(state:MultimarketState, now:number) {
  const depth = state.health.find(h=>h.channel==='depth');
  const fresh = state.origin==='synthetic' || (depth?.last_receive_time_ms!=null &&
    now-depth.last_receive_time_ms>=0 && now-depth.last_receive_time_ms<=2000);
  return state.book?.valid && depth?.valid && !depth.stale && fresh ? state.book : null;
}

export function probabilityLabel(value:number|null|undefined) {
  return value==null ? 'Não estimada' : `${(100*value).toFixed(1)}%`;
}

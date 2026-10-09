import type {MultimarketSnapshot, UnknownRecord} from './multimarketModel';

export type MultimarketWire = {schema_version?:number; id?:string; event?:string; error?:string; result?:unknown};

export function parseMultimarketWire(wire:MultimarketWire):MultimarketSnapshot {
  if(wire.error)throw new Error(wire.error);
  if(![1,2].includes(wire.schema_version??0) || !wire.result || typeof wire.result!=='object' || (wire.result as UnknownRecord).schema_version!==3)
    throw new Error('Resposta multimercado incompatível; esperado snapshot 3.');
  return wire.result as MultimarketSnapshot;
}

export function projectMultimarketEvent(wire:MultimarketWire):MultimarketSnapshot {
  try {return parseMultimarketWire(wire);}
  catch {return {schema_version:0} as unknown as MultimarketSnapshot;}
}

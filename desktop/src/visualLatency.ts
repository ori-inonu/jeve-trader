type Receipt={at:number;pilotId:string|null;eligible:boolean};
export type VisualPilotReport={buckets:[number,number][];excluded:number;overflow:number};
const receipts=new Map<number,Receipt>();
const samples:number[]=[];
let pilotId:string|null=null, excluded=0, overflow=0;
const buckets=new Map<number,number>();
const bucket=(ms:number)=>Math.min(60000,Math.ceil(ms/(ms<=1000?1:ms<=2000?10:100))*(ms<=1000?1:ms<=2000?10:100));

export function createVisualCaptureReceiver() {
  let seeded=false,lastCapture:string|null=null;
  return (sequence:number,id:string|null,eligible:boolean,captureKey:string|null)=>{
    // The first snapshot may predate this renderer. Establish its baseline;
    // only subsequent capture changes can supply a pilot latency sample.
    const fresh=seeded&&eligible&&captureKey!==null&&captureKey!==lastCapture;
    seeded=true;lastCapture=captureKey;
    receivedSnapshot(sequence,id,fresh);
  };
}

export function receivedSnapshot(sequence:number,id:string|null=null,live=false) {
  if(id!==pilotId){pilotId=id;buckets.clear();excluded=0;overflow=0;}
  const visible=document.visibilityState==='visible';
  if(id&&live&&!visible)excluded++;
  if(!visible)return;
  receipts.set(sequence,{at:performance.now(),pilotId:id,eligible:!!id&&live});
  if(receipts.size>300){
    const key=receipts.keys().next().value!;
    const lost=receipts.get(key)!;
    if(lost.eligible&&lost.pilotId===pilotId)excluded++;
    receipts.delete(key);
  }
}

export function discardBackgroundReceipts() {
  for(const receipt of receipts.values())if(receipt.eligible&&receipt.pilotId===pilotId)excluded++;
  receipts.clear();
}

export function discardSnapshot(sequence:number) {
  const receipt=receipts.get(sequence);
  if(receipt?.eligible&&receipt.pilotId===pilotId)excluded++;
  receipts.delete(sequence);
}

export function paintLatency(sequence:number) {
  const received=receipts.get(sequence);
  receipts.delete(sequence);
  if(received){
    if(document.visibilityState==='visible'){
      const ms=Math.max(0,performance.now()-received.at);
      samples.push(ms);if(samples.length>300)samples.shift();
      if(received.eligible&&received.pilotId===pilotId){
        const upper=bucket(ms);buckets.set(upper,(buckets.get(upper)||0)+1);
        if(ms>60000)overflow++;
      }
    }else if(received.eligible&&received.pilotId===pilotId)excluded++;
  }
  const sorted=[...samples].sort((a,b)=>a-b);
  return {p95:sorted.length?sorted[Math.ceil(sorted.length*.95)-1]:null,count:sorted.length};
}

export function visualPilotReport(id:string,final=true):VisualPilotReport {
  const pending=final?[...receipts.values()].filter(r=>r.eligible&&r.pilotId===id).length:0;
  return id===pilotId?{buckets:[...buckets].sort((a,b)=>a[0]-b[0]),excluded:excluded+pending,overflow}:{buckets:[],excluded:0,overflow:0};
}

let rendererSession:string|undefined;
export function visualSessionId(){return rendererSession??=crypto.randomUUID();}

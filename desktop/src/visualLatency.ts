const receipts=new Map<number,number>();
const samples:number[]=[];
export function receivedSnapshot(sequence:number) {
  if(document.visibilityState!=='visible')return;
  receipts.set(sequence,performance.now());
  if(receipts.size>300)receipts.delete(receipts.keys().next().value!);
}
export function paintLatency(sequence:number) {
  const received=receipts.get(sequence);
  receipts.delete(sequence);
  if(received!=null&&document.visibilityState==='visible'){samples.push(performance.now()-received);if(samples.length>300)samples.shift();}
  const sorted=[...samples].sort((a,b)=>a-b);
  return {p95:sorted.length?sorted[Math.ceil(sorted.length*.95)-1]:null,count:sorted.length};
}

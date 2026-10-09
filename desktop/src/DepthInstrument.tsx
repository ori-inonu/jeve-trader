import {useId} from 'react';

// Fixed projection: depth is decorative; only the bipolar level encodes a value.
export function DepthInstrument({temperature}:{temperature:number|null}) {
  const id=useId().replaceAll(':','');
  const level=temperature==null?null:Math.max(-100,Math.min(100,temperature));
  const y=84-(level??0)*.65, color=(level??0)>=0?'#53ddbb':'#ff6b87';
  return <div className="depth-instrument" role={level==null?'img':'meter'} aria-label="Índice contextual JEV"
    aria-valuemin={level==null?undefined:-100} aria-valuemax={level==null?undefined:100}
    aria-valuenow={level??undefined} aria-valuetext={level==null?'Indisponível':`${level}; peso contextual, não chance de lucro`}>
    <svg viewBox="0 0 88 174" aria-hidden="true">
      <defs>
        <linearGradient id={`${id}-metal`}><stop stopColor="#132033"/><stop offset=".35" stopColor="#40526d"/><stop offset=".65" stopColor="#18263b"/><stop offset="1" stopColor="#080f19"/></linearGradient>
        <linearGradient id={`${id}-glass`}><stop stopColor="#7eacc426"/><stop offset=".25" stopColor="#c9eaff26"/><stop offset=".55" stopColor="#142334"/><stop offset="1" stopColor="#050a12"/></linearGradient>
        <linearGradient id={`${id}-fluid`}><stop stopColor={color} stopOpacity=".28"/><stop offset=".5" stopColor={color}/><stop offset="1" stopColor={color} stopOpacity=".55"/></linearGradient>
      </defs>
      <path d="M25 14 L37 6 L69 6 L69 156 L57 164 L25 164 Z" fill={`url(#${id}-metal)`} stroke="#41546d"/>
      <path d="M57 14 L69 6 L69 156 L57 164 Z" fill="#090f1c" stroke="#35445b"/>
      <rect x="30" y="14" width="22" height="140" rx="11" fill={`url(#${id}-glass)`} stroke="#6c819659"/>
      {level!=null&&<rect className="instrument-fluid" x="34" width="14" rx="3" fill={`url(#${id}-fluid)`} style={{y:Math.min(84,y),height:Math.abs(y-84)}}/>}
      <path d="M34 26 L34 142" stroke="#d8f4ff30" strokeWidth="2"/>
      {[-100,-80,-60,-40,-20,0,20,40,60,80,100].map(t=><path key={t} d={`M${t===0?18:21} ${84-t*.65} H29`} stroke={t===0?'#c4d5ec':Math.abs(t)===80?'#d2ad6b':'#536881'} strokeWidth={t===0?2:1}/>)}
      <text x="12" y="87" fill="#a1b4cf" fontSize="8">0</text>
      {level!=null&&<g className="instrument-marker" style={{transform:`translateY(${y}px)`}}><path d="M28 0 H54 L61 -4 V4 L54 0" fill={color} stroke={color}/><circle cx="41" cy="0" r="3" fill="#effaff"/></g>}
      {level==null&&<text x="41" y="88" textAnchor="middle" fill="#7890ae" fontSize="16">—</text>}
      <ellipse cx="41" cy="157" rx="19" ry="5" fill="#0008"/>
    </svg>
  </div>;
}

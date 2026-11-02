"use client";
import {useEffect,useState,useRef} from 'react';
import NexDialog from './nex-dialog';
type Notice={kind:'success'|'error'|'warning'|'confirm';message:string;resolve?:(value:boolean)=>void};
export function notify(message:string,kind:Notice['kind']='success'){if(typeof window!=='undefined')window.dispatchEvent(new CustomEvent('nex-feedback',{detail:{message,kind}}))}
export function confirmAction(message:string):Promise<boolean>{return new Promise(resolve=>window.dispatchEvent(new CustomEvent('nex-feedback',{detail:{kind:'confirm',message,resolve}})))}
export default function NexFeedback(){
 const [queue,setQueue]=useState<Notice[]>([]);const pending=useRef(new Set<Notice>());
 useEffect(()=>{const receive=(e:Event)=>{const n=(e as CustomEvent<Notice>).detail;pending.current.add(n);setQueue(q=>[...q,n])};window.addEventListener('nex-feedback',receive);return()=>{window.removeEventListener('nex-feedback',receive);pending.current.forEach(n=>n.resolve?.(false));pending.current.clear()}},[]);
 const n=queue[0];if(!n)return null;const done=(yes=false)=>{n.resolve?.(yes);pending.current.delete(n);setQueue(q=>q.slice(1))};
 const titles={success:'Success',error:'Could not complete',warning:'Please review',confirm:'Confirmation'};
 return <NexDialog key={queue.length+':'+n.message} title={titles[n.kind]} onClose={()=>done()}><div className={'nx-feedback '+n.kind}><div className="nx-feedback-icon" aria-hidden="true">{n.kind==='success'?'✓':n.kind==='error'?'×':n.kind==='warning'?'!':'?'}</div><p role={n.kind==='error'?'alert':'status'} className="my-6 whitespace-pre-wrap text-center">{n.message}</p><div className="flex justify-center gap-3">{n.kind==='confirm'&&<button className="nx-button nx-secondary" onClick={()=>done()}>Cancel</button>}<button className="nx-button" autoFocus onClick={()=>done(true)}>{n.kind==='confirm'?'Confirm':'Okay'}</button></div></div></NexDialog>
}

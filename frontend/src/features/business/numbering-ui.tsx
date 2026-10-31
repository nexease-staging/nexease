"use client";
import SearchSelect from "@/components/search-select";

import {useState,useEffect,useRef} from 'react';import {useQuery,useQueryClient} from '@tanstack/react-query';import {apiRequest} from '@/lib/api/client';import type {Prompt} from '@/lib/api/number-choice';
type Series={kind:string;mode:'automatic'|'manual';prefix:string;next:number;padding:number};
export function NumberDialog(){
 const [prompt,setPrompt]=useState<Prompt|null>(null);
 const [mode,setMode]=useState<'automatic'|'manual'>('automatic');
 const [number,setNumber]=useState('');
 const [preview,setPreview]=useState('Assigned when saved');
 const dialog=useRef<HTMLDialogElement>(null);
 const pending=useRef<Prompt|null>(null);
 const edited=useRef(false);
 useEffect(()=>{
  const listener=(event:Event)=>{
   const p=(event as CustomEvent<Prompt>).detail;
   // A second creation must not orphan the first request's promise.
   pending.current?.resolve(null);pending.current=p;edited.current=false;
   setPrompt(p);setNumber(p.existing);setMode(p.existing?'manual':'automatic');setPreview('Assigned when saved');
   apiRequest<{series:Series[]}>('/business/numbers/').then(r=>{
    if(pending.current!==p)return;
    const s=r.data.series.find(x=>x.kind===p.kind);
    if(s){if(!edited.current)setMode(p.existing?'manual':s.mode);setPreview(s.prefix+String(s.next).padStart(s.padding,'0'));}
   }).catch(()=>{});
  };
  window.addEventListener('nexease-number',listener);document.documentElement.dataset.numberDialog='ready';
  return()=>{window.removeEventListener('nexease-number',listener);delete document.documentElement.dataset.numberDialog;pending.current?.resolve(null);pending.current=null;};
 },[]);
 useEffect(()=>{
  if(prompt && dialog.current && !dialog.current.open)dialog.current.showModal();
 },[prompt]);
 function done(save:boolean){
  const p=pending.current;if(!p)return;
  pending.current=null;dialog.current?.close();setPrompt(null);
  p.resolve(save?{kind:p.kind,mode,number}:null);
 }
 if(!prompt)return null;
 return <dialog ref={dialog} aria-label="Document numbering" onCancel={e=>{e.preventDefault();done(false)}} onClose={()=>{if(pending.current)done(false)}} className="m-auto w-[min(32rem,calc(100vw-2rem))] rounded-2xl border border-slate-200 bg-white p-6 text-slate-900 shadow-2xl backdrop:bg-black/40">
  <h2 className="text-xl font-semibold">{prompt.kind.replace(/([a-z])([A-Z])/g,'$1 $2')} number</h2>
  <label className="block my-4"><input type="radio" name="number-mode" checked={mode==='automatic'} onChange={()=>{edited.current=true;setMode('automatic')}}/> Automatic · {preview}</label>
  <label className="block my-4"><input type="radio" name="number-mode" checked={mode==='manual'} onChange={()=>{edited.current=true;setMode('manual')}}/> Enter manually</label>
  {mode==='manual'&&<input aria-label="Manual document number" className="nx-input" maxLength={50} value={number} onChange={e=>setNumber(e.target.value)}/>}
  <p className="text-xs my-4">The preview is provisional. Set defaults in Settings → Numbering.</p>
  <div className="flex gap-3"><button type="button" className="nx-button" disabled={mode==='manual'&&!number.trim()} onClick={()=>done(true)}>Save with this numbering</button><button type="button" className="nx-button nx-secondary" onClick={()=>done(false)}>Cancel</button></div>
 </dialog>;
}
export function NumberSettings(){const qc=useQueryClient();const q=useQuery({queryKey:['number-series'],queryFn:async()=>(await apiRequest<{series:Series[]}>('/business/numbers/')).data});const [draft,setDraft]=useState<Series|null>(null);const [error,setError]=useState('');const [busy,setBusy]=useState(false);async function save(){setBusy(true);try{await apiRequest('/business/numbers/',{method:'POST',body:draft});setDraft(null);await qc.invalidateQueries({queryKey:['number-series']})}catch(e){setError(e instanceof Error?e.message:'Save failed')}finally{setBusy(false)}}return <section className="nx-panel"><h1 className="text-2xl font-semibold">Numbering preferences</h1><p className="my-3">Choose a default mode, prefix and next number for each record type. Existing numbers stay unchanged. Used or reserved numbers cannot be reused; next numbers can only increase.</p>{(error||q.error)&&<p role="alert">{error||q.error?.message}</p>}<div className="overflow-auto"><table className="w-full"><thead><tr><th>Record</th><th>Default</th><th>Next</th><th>Action</th></tr></thead><tbody>{q.data?.series.map(s=><tr key={s.kind}><td className="p-3">{s.kind}</td><td>{s.mode}</td><td>{s.prefix}{String(s.next).padStart(s.padding,'0')}</td><td><button className="nx-button nx-secondary" onClick={()=>{setDraft(s);setError('')}}>Configure</button></td></tr>)}</tbody></table></div>{draft&&<div className="nx-panel mt-5"><h2>{draft.kind}</h2><label>Default mode<SearchSelect className="nx-input" value={draft.mode} onChange={e=>setDraft({...draft,mode:e.target.value as Series['mode']})}><option value="automatic">Automatic</option><option value="manual">Manual</option></SearchSelect></label><label>Prefix<input className="nx-input" value={draft.prefix} onChange={e=>setDraft({...draft,prefix:e.target.value})}/></label><label>Next number<input className="nx-input" type="number" min="1" value={draft.next} onChange={e=>setDraft({...draft,next:Number(e.target.value)})}/></label><label>Minimum digits<input className="nx-input" type="number" min="1" max="12" value={draft.padding} onChange={e=>setDraft({...draft,padding:Number(e.target.value)})}/></label><button disabled={busy} className="nx-button mt-3" onClick={save}>Save preferences</button></div>}</section>}

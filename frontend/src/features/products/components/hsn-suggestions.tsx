"use client";
import {useEffect,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {apiRequest} from '@/lib/api/client';
interface Match {code:string;description:string;item_type:string}
interface Results {results:Match[];total:number;expanded_query?:string;retrieved?:string}
export default function HSNSuggestions({name,itemType,onSelect}:{name:string;itemType:string;onSelect:(code:string)=>void}) {
 const [typed,setTyped]=useState<{name:string;kind:string;value:string}|null>(null);
 const query=(typed?.name===name&&typed.kind===itemType?typed.value:name).trim().slice(0,100);
 const [debounced,setDebounced]=useState('');
 const [notice,setNotice]=useState('');
 useEffect(()=>{setNotice('');const timer=setTimeout(()=>setDebounced(query),400);return()=>clearTimeout(timer)},[query,itemType]);
 const ready=query.length>=3&&query===debounced;
 const result=useQuery({queryKey:['hsn-suggestions',itemType,debounced],enabled:ready,
  queryFn:async()=>(await apiRequest<Results>('/business/hsn-suggestions/?'+new URLSearchParams({q:debounced,item_type:itemType}))).data,
  staleTime:300000,retry:1});
 return <section className="col-span-2 rounded-xl border border-slate-200 p-3 dark:border-slate-700" aria-label="HSN and SAC suggestions">
  <label className="text-sm font-semibold">Find HSN / SAC<input className="nx-input mt-1" maxLength={100} value={query} onChange={e=>setTyped({name,kind:itemType,value:e.target.value})} placeholder="Type a product description or code"/></label>
  <p className="mt-1 text-xs text-slate-500 dark:text-slate-300">Suggestions follow the product name. Choose the matching description to fill the code; this does not change GST rates or save the product.</p>
  {query.length<3&&<p className="mt-2 text-sm">Enter at least 3 characters.</p>}
  {ready&&result.isFetching&&<p role="status" className="mt-2 text-sm">Finding matching codes…</p>}
  {ready&&result.error&&<p role="alert" className="mt-2 text-sm">Code search is unavailable. You can enter a reviewed code manually.</p>}
  {ready&&result.data&&<>
   <p className="mt-2 text-xs">{result.data.total} matches{result.data.expanded_query?` · searched “${result.data.expanded_query}”`:''}. {result.data.total>12?'Showing 12; add more detail to narrow the list.':''}</p>
   <ul className="mt-2 max-h-52 overflow-auto divide-y divide-slate-200 dark:divide-slate-700">{result.data.results.map(m=><li key={m.code}><button type="button" className="w-full rounded p-2 text-left text-sm hover:bg-emerald-50 dark:hover:bg-slate-800" onClick={()=>{onSelect(m.code);setNotice(`Selected ${m.code}. Review the description and GST rate before saving.`)}}><strong className="mr-2">{m.code}</strong>{m.description}</button></li>)}</ul>
   {!result.data.total&&<p className="mt-2 text-sm">No matches. Try a generic description, such as “water” instead of a brand name, or enter your reviewed code manually.</p>}
   <p className="mt-2 text-xs text-slate-500 dark:text-slate-300">GSTN directory snapshot: {result.data.retrieved}. Verify classification and required code length before use.</p>
  </>}
  {notice&&<p role="status" className="mt-2 text-sm text-emerald-700 dark:text-emerald-300">{notice}</p>}
  <a className="mt-2 inline-block text-xs underline" href="https://services.gst.gov.in/services/searchhsnsac" target="_blank" rel="noopener noreferrer">Verify on the GST portal</a>
 </section>
}

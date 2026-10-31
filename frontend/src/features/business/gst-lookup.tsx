"use client";
import {useEffect,useRef,useState} from 'react';
import {apiRequest} from '@/lib/api/client';
export default function GstLookup({onSelect}:{onSelect:(data:Record<string,string>)=>void}){
 const [gst,setGst]=useState(''),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[retry,setRetry]=useState(0);const callback=useRef(onSelect);callback.current=onSelect;
 useEffect(()=>{if(gst.length!==15)return;let live=true;const timer=setTimeout(async()=>{setBusy(true);setMessage('');try{const r=await apiRequest<Record<string,string>>('/business/gst-lookup/?gstin='+encodeURIComponent(gst));if(live){callback.current(r.data);setMessage(r.data.source+'. Contact details are filled only when supplied; verify all details.')}}catch(e){if(live)setMessage((e as Error).message)}finally{if(live)setBusy(false)}},350);return()=>{live=false;clearTimeout(timer);setBusy(false)}},[gst,retry]);
 return <div className="rounded-xl border border-emerald-100 bg-emerald-50/40 p-4"><label className="text-sm font-medium">Find business by GSTIN</label><div className="mt-2 flex gap-2"><input aria-label="GSTIN to look up" maxLength={15} className="nx-input" value={gst} placeholder="Enter GSTIN to fetch details" onChange={e=>setGst(e.target.value.toUpperCase())}/><button type="button" className="nx-button" disabled={busy||gst.length!==15} onClick={()=>setRetry(r=>r+1)}>{busy?'Looking up…':'Fetch again'}</button></div>{message&&<p role="status" className="mt-2 text-sm">{message}</p>}</div>
}

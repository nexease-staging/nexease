"use client";
import {useEffect,useRef,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {getConfig} from './workspace';
import {apiRequest} from '@/lib/api/client';
import type {Master} from '@/components/master-lookup';
export type Scanned=Master&{stock?:{warehouse:string;quantity:string;reserved:string;available:string}[]};
type Detector={detect:(v:HTMLVideoElement)=>Promise<{rawValue:string}[]>};
export default function BarcodeScan({onSelect}:{onSelect:(r:Scanned)=>void}){
 const config=useQuery({queryKey:['business-config'],queryFn:getConfig});const [code,setCode]=useState(''),[msg,setMsg]=useState(''),[busy,setBusy]=useState(false),[camera,setCamera]=useState(false);const video=useRef<HTMLVideoElement>(null),stream=useRef<MediaStream|null>(null),timer=useRef<ReturnType<typeof setTimeout>|null>(null),generation=useRef(0);
 function stop(){generation.current++;stream.current?.getTracks().forEach(t=>t.stop());stream.current=null;if(timer.current)clearTimeout(timer.current);setCamera(false)}
 useEffect(()=>()=>{generation.current++;stream.current?.getTracks().forEach(t=>t.stop());if(timer.current)clearTimeout(timer.current)},[]);
 async function lookup(value:string){if(!value.trim())return;setBusy(true);setMsg('');try{const r=await apiRequest<Scanned>('/business/barcode/lookup/?code='+encodeURIComponent(value.trim()));onSelect(r.data);setCode('');setMsg('Scanned: '+r.data.name)}catch(e){setMsg((e as Error).message)}finally{setBusy(false)}}
 async function start(){stop();const current=generation.current;const DetectorClass=(window as unknown as {BarcodeDetector?:new()=>Detector}).BarcodeDetector;if(!DetectorClass){setMsg('Camera scanning is unavailable in this browser. Use a USB/Bluetooth scanner or type the barcode.');return}try{const media=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}});if(current!==generation.current){media.getTracks().forEach(t=>t.stop());return}stream.current=media;setCamera(true);if(video.current){video.current.srcObject=media;await video.current.play()}const detector=new DetectorClass();const scan=async()=>{if(current!==generation.current)return;try{if(video.current&&video.current.readyState>=2){const found=await detector.detect(video.current);if(found.length){stop();await lookup(found[0].rawValue);return}}}catch{stop();setMsg('Camera could not read the barcode. Use the scanner input.');return}timer.current=setTimeout(scan,300)};void scan()}catch{stop();setMsg('Camera access failed. Allow camera permission or use a hardware scanner.')}}
 if(config.data?.modules?.barcode===false)return null;
 return <div className="rounded-xl border p-3"><div className="flex flex-wrap gap-2"><input className="nx-input flex-1" aria-label="Scan barcode" placeholder="Scan barcode / SKU, then Enter" value={code} onChange={e=>setCode(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'){e.preventDefault();if(!busy)void lookup(code)}}}/><button type="button" className="nx-button nx-secondary" disabled={busy} onClick={()=>void lookup(code)}>Scan</button><button type="button" className="nx-button nx-secondary" onClick={()=>camera?stop():void start()}>{camera?'Stop camera':'Use camera'}</button></div><video ref={video} muted playsInline className={camera?'mt-3 max-h-64 w-full rounded-xl':'hidden'}/>{msg&&<p role="status" className="mt-2 text-sm">{msg}</p>}</div>
}

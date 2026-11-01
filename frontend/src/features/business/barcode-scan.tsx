"use client";
import {ScanBarcode,Camera,ImagePlus,Square} from 'lucide-react';
import type {ReactNode,RefObject} from 'react';
import {Capacitor} from '@capacitor/core';
import {useEffect,useRef,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {getConfig} from './workspace';
import {apiRequest} from '@/lib/api/client';
import type {Master} from '@/components/master-lookup';
export type Scanned=Master&{stock?:{warehouse:string;quantity:string;reserved:string;available:string}[]};
type Phase='idle'|'opening'|'scanning';

async function makeReader(){
 const [{BrowserMultiFormatReader},{DecodeHintType,BarcodeFormat}]=await Promise.all([import('@zxing/browser'),import('@zxing/library')]);
 const hints=new Map<import('@zxing/library').DecodeHintType,unknown>();
 hints.set(DecodeHintType.TRY_HARDER,true);
 hints.set(DecodeHintType.POSSIBLE_FORMATS,[BarcodeFormat.CODE_128,BarcodeFormat.CODE_39,BarcodeFormat.CODE_93,BarcodeFormat.EAN_13,BarcodeFormat.EAN_8,BarcodeFormat.UPC_A,BarcodeFormat.UPC_E,BarcodeFormat.ITF,BarcodeFormat.CODABAR]);
 return new BrowserMultiFormatReader(hints,{delayBetweenScanAttempts:150,tryPlayVideoTimeout:10000});
}
function cameraError(error:unknown){
 const name=(error as {name?:string})?.name;
 if(name==='NotAllowedError'||name==='SecurityError')return 'Camera access failed. Enable Camera in Android Settings → Apps → NexEase → Permissions, then retry.';
 if(name==='NotFoundError')return 'No camera found. Connect a camera, use Scan photo, or use a paired barcode scanner.';
 if(name==='NotReadableError')return 'Camera is busy. Close other camera apps and try again, or use Scan photo.';
 return 'Camera access failed. Allow camera permission and try again. You can also use Scan photo or enter the barcode.';
}
type ScanProps=({onSelect:(r:Scanned)=>void;onCapture?:never}|{onCapture:(code:string)=>void;onSelect?:never})&{renderInput?:(scan:(code:string)=>void,ref:RefObject<HTMLInputElement|null>,ready:boolean)=>ReactNode};
export default function BarcodeScan({onSelect,onCapture,renderInput}:ScanProps){
 const [hardwareReady,setHardwareReady]=useState(false);
 const config=useQuery({queryKey:['business-config'],queryFn:getConfig});
 const [code,setCode]=useState(''),[message,setMessage]=useState(''),[busy,setBusy]=useState(false),[phase,setPhase]=useState<Phase>('idle');
 const [devices,setDevices]=useState<MediaDeviceInfo[]>([]),[selected,setSelected]=useState('');
 const input=useRef<HTMLInputElement>(null),photo=useRef<HTMLInputElement>(null),video=useRef<HTMLVideoElement>(null);
 const stream=useRef<MediaStream|null>(null),controls=useRef<{stop:()=>void}|null>(null),generation=useRef(0),mounted=useRef(true),lookingUp=useRef(false);
 const hintTimer=useRef<ReturnType<typeof setTimeout>|null>(null);
 function release(){
  generation.current++;
  if(hintTimer.current)clearTimeout(hintTimer.current);
  hintTimer.current=null;
  controls.current?.stop();controls.current=null;
  stream.current?.getTracks().forEach(t=>t.stop());stream.current=null;
  if(video.current)video.current.srcObject=null;
 }
 function stop(){release();setPhase('idle')}
 useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;release()}},[]);
 async function lookup(value:string){
  const text=value.trim();if(!text||lookingUp.current)return;setHardwareReady(false);
  if(onCapture){onCapture(text);setCode(text);setMessage('Barcode captured: '+text);return;}
  lookingUp.current=true;setBusy(true);setCode(text);setMessage(`Barcode read: ${text}. Finding product…`);
  try{
   const r=await apiRequest<Scanned>('/business/barcode/lookup/?code='+encodeURIComponent(text));
   if(!mounted.current)return;
   onSelect?.(r.data);setMessage('Scanned: '+r.data.name);setCode('');
  }catch(error){if(mounted.current)setMessage(`Barcode read: ${text}. ${(error as Error).message||'Product lookup failed. Please retry.'}`)}
  finally{lookingUp.current=false;if(mounted.current)setBusy(false)}
 }
 async function start(deviceId=selected){
  stop();const attempt=generation.current;
  if(Capacitor.isNativePlatform()){
   setBusy(true);setMessage('Opening native camera scanner…');
   try{
    const {CapacitorBarcodeScanner,CapacitorBarcodeScannerTypeHint,CapacitorBarcodeScannerCameraDirection,CapacitorBarcodeScannerAndroidScanningLibrary}=await import('@capacitor/barcode-scanner');
    const result=await CapacitorBarcodeScanner.scanBarcode({hint:CapacitorBarcodeScannerTypeHint.ALL,cameraDirection:CapacitorBarcodeScannerCameraDirection.BACK,scanInstructions:'Place the complete barcode in view',scanButton:false,android:{scanningLibrary:CapacitorBarcodeScannerAndroidScanningLibrary.MLKIT}});
    if(attempt===generation.current&&mounted.current){if(result.ScanResult?.trim())await lookup(result.ScanResult);else setMessage('Scan cancelled. You can retry or use Scan photo.');}
   }catch(error){if(attempt===generation.current&&mounted.current)setMessage('Native camera scan could not complete. Allow Camera in Android Settings → Apps → NexEase → Permissions. Retry or use Scan photo.');}
   finally{if(mounted.current)setBusy(false)}
   return;
  }
  setPhase('opening');setMessage('Opening camera… Allow camera access if your phone asks.');
  hintTimer.current=setTimeout(()=>{if(attempt===generation.current)setMessage('Still waiting for the camera. Check permissions, or stop and try Scan photo.');},12000);
  try{
   if(!navigator.mediaDevices?.getUserMedia)throw new Error('Camera API unavailable');
   const media=await navigator.mediaDevices.getUserMedia({audio:false,video:deviceId?{deviceId:{exact:deviceId}}:{facingMode:{ideal:'environment'},width:{ideal:1920},height:{ideal:1080}}});
   if(attempt!==generation.current){media.getTracks().forEach(t=>t.stop());return}
   stream.current=media;
   // Device enumeration is optional: some WebViews permit video but reject enumeration.
   void navigator.mediaDevices.enumerateDevices?.().then(list=>{if(attempt===generation.current)setDevices(list.filter(d=>d.kind==='videoinput'))}).catch(()=>{});
   setSelected(media.getVideoTracks()[0]?.getSettings().deviceId??deviceId);
   const reader=await makeReader();
   if(attempt!==generation.current)return;
   if(!video.current)throw new Error('Camera preview unavailable');
   // Always use the bundled decoder. WebViews can expose BarcodeDetector without
   // providing working Code 128 support (the format used by NexEase labels).
   const scanner=await reader.decodeFromStream(media,video.current,(result,error,active)=>{
    if(attempt!==generation.current){active.stop();return}
    if(result){const value=result.getText();active.stop();stop();void lookup(value);return;}
    if(error&&!['NotFoundException','ChecksumException','FormatException'].includes((error as {getKind?:()=>string}).getKind?.()??error.name)){
     active.stop();stop();setMessage('The camera opened, but scanning failed. Try Scan photo or enter the barcode.');
    }
   });
   if(attempt!==generation.current){scanner.stop();return}
   controls.current=scanner;setPhase('scanning');
   setMessage('Scanning… Hold the complete barcode inside the camera view, with clear space on both sides.');
   if(hintTimer.current)clearTimeout(hintTimer.current);
   hintTimer.current=setTimeout(()=>{if(attempt===generation.current)setMessage('No barcode read yet. Improve the light, move the phone farther away, or try Scan photo. Scanning is still active.');},12000);
  }catch(error){if(attempt===generation.current){stop();setMessage(cameraError(error))}}
 }
 async function scanPhoto(file:File){
  stop();const attempt=generation.current;setBusy(true);setMessage('Reading barcode from photo…');
  const url=URL.createObjectURL(file);
  try{
   const reader=await makeReader();const result=await reader.decodeFromImageUrl(url);
   if(attempt===generation.current&&mounted.current)await lookup(result.getText());
  }catch{if(attempt===generation.current&&mounted.current)setMessage('No readable barcode found in this photo. Keep the full label sharp, avoid glare, and try again.');}
  finally{URL.revokeObjectURL(url);if(mounted.current)setBusy(false)}
 }
 if(config.data?.modules?.barcode===false)return renderInput?.(()=>{},input,false)??null;
 return <div className="rounded-xl border p-3">
  <div className="flex flex-wrap items-center gap-2"><div className="min-w-0 basis-full sm:basis-0 sm:flex-1">{renderInput?renderInput(value=>{stop();void lookup(value)},input,hardwareReady):<input ref={input} className="nx-input min-w-0 flex-1" aria-label="Scan barcode" placeholder="Scan barcode / SKU, then Enter" value={code} onChange={e=>setCode(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'){e.preventDefault();if(!busy){stop();void lookup(code)}}}}/>}</div>
  <button type="button" className="nx-button nx-secondary !min-h-11 !min-w-11 !px-3" disabled={busy} aria-label="Scan barcode" title="Use connected barcode scanner" onClick={()=>{stop();setHardwareReady(true);input.current?.focus();if(!renderInput&&code.trim())void lookup(code);else setMessage('Scanner ready. Scan with your paired USB/Bluetooth keyboard scanner, then Enter.')}}><ScanBarcode size={20} aria-hidden="true"/></button>
  <button type="button" className="nx-button nx-secondary !min-h-11 !min-w-11 !px-3" disabled={busy} aria-label={phase==='idle'?'Use camera':'Stop camera'} title={phase==='idle'?'Use camera':'Stop camera'} onClick={()=>{setHardwareReady(false);if(phase==='idle')void start();else {stop();setMessage('Camera stopped.')}}}>{phase==='idle'?<Camera size={20} aria-hidden="true"/>:<Square size={20} aria-hidden="true"/>}</button>
  <button type="button" className="nx-button nx-secondary !min-h-11 !min-w-11 !px-3" disabled={busy} aria-label="Scan photo" title="Scan photo" onClick={()=>{stop();setHardwareReady(false);photo.current?.click()}}><ImagePlus size={20} aria-hidden="true"/></button>
  <input ref={photo} type="file" accept="image/*" capture="environment" aria-label="Barcode photo" className="hidden" onChange={e=>{const file=e.target.files?.[0];e.target.value='';if(file)void scanPhoto(file)}}/>
  </div>
  {devices.length>1&&<label className="mt-3 block text-sm">Connected camera<select className="nx-input" disabled={busy} value={selected} onChange={e=>{setSelected(e.target.value);if(phase!=='idle')void start(e.target.value)}}>{devices.map((device,index)=><option key={device.deviceId} value={device.deviceId}>{device.label||`Camera ${index+1}`}</option>)}</select></label>}
  <video ref={video} autoPlay muted playsInline aria-label="Barcode camera preview" className={phase!=='idle'?'mt-3 aspect-video w-full rounded-xl bg-black object-contain':'hidden'}/>
  {message&&<p role="status" aria-live="polite" className="mt-2 text-sm">{message}</p>}
 </div>;
}

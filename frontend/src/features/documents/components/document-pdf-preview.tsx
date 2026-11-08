"use client";

import {useEffect, useState} from "react";
import {Eye, X} from "lucide-react";
import {getDocumentPDF} from "@/features/documents/api";
import {downloadBlob} from "@/lib/browser/download";
import type {DocumentType} from "@/features/documents/types";

export default function DocumentPDFPreview({documentType, documentId, documentNumber, disabled=false}: {
  documentType: DocumentType; documentId: string; documentNumber: string; disabled?: boolean;
}) {
  const [open,setOpen]=useState(false);
  const [file,setFile]=useState<{blob:Blob;filename:string}|null>(null);
  const [url,setUrl]=useState("");
  const [error,setError]=useState("");
  useEffect(()=>{
    if(!open)return;
    let active=true;
    setFile(null);setError("");
    getDocumentPDF(documentType,documentId).then(result=>{
      if(active)setFile({blob:result.blob,filename:result.filename||`${documentNumber}.pdf`});
    }).catch(e=>{if(active)setError(e instanceof Error?e.message:"Unable to load PDF.");});
    return ()=>{active=false;};
  },[open,documentType,documentId,documentNumber]);
  useEffect(()=>{
    if(!file){setUrl("");return;}
    const next=URL.createObjectURL(file.blob);setUrl(next);
    return ()=>URL.revokeObjectURL(next);
  },[file]);
  useEffect(()=>{
    if(!open)return;
    const close=(e:KeyboardEvent)=>{if(e.key==="Escape")setOpen(false);};
    document.addEventListener("keydown",close);
    return ()=>document.removeEventListener("keydown",close);
  },[open]);
  return <>
    <button type="button" disabled={disabled} className="nx-button nx-secondary" onClick={()=>setOpen(true)}><Eye size={16}/> Preview PDF</button>
    {open&&<dialog open aria-modal="true" aria-label={`Invoice PDF preview ${documentNumber}`} className="fixed inset-0 z-[100] m-0 h-dvh w-screen max-w-none bg-slate-900/80 p-3 md:p-6">
      <div className="flex h-full flex-col rounded-xl bg-white p-3">
        <div className="mb-3 flex items-center justify-between gap-3"><strong>{documentNumber} — PDF preview</strong><div className="flex gap-2">
          {file&&<button className="nx-button" onClick={()=>void downloadBlob(file.blob,file.filename).catch(e=>setError(e.message))}>Download / share PDF</button>}
          <button aria-label="Close PDF preview" autoFocus className="nx-button nx-secondary" onClick={()=>setOpen(false)}><X size={18}/></button>
        </div></div>
        {error?<p role="alert">{error}</p>:url?<><iframe title={`${documentNumber} PDF`} src={url} className="min-h-0 w-full flex-1 border-0"/><p className="pt-2 text-xs text-slate-500">If your device cannot display PDFs here, use Download / share PDF to open the same document.</p></>:<p role="status">Preparing invoice preview…</p>}
      </div>
    </dialog>}
  </>;
}

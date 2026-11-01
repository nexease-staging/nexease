"use client";
import {useEffect,useId,useRef,type ReactNode} from 'react';
export default function NexDialog({title,onClose,children,busy=false}:{title:string;onClose:()=>void;children:ReactNode;busy?:boolean}){
 const ref=useRef<HTMLDialogElement>(null);const id=useId();
 useEffect(()=>{const d=ref.current;d?.showModal();return()=>{d?.close()}},[]);
 return <dialog ref={ref} aria-labelledby={id} onCancel={e=>{e.preventDefault();if(!busy)onClose()}} className="nx-modal"><header className="flex items-center justify-between gap-4 border-b p-5"><div><p className="text-xs uppercase tracking-widest text-emerald-700">NexEase</p><h2 id={id} className="text-xl font-semibold mt-1">{title}</h2></div><button type="button" title="Close" aria-label="Close" disabled={busy} className="nx-button nx-secondary" onClick={onClose}>×</button></header><div className="p-5 sm:p-7">{children}</div></dialog>
}

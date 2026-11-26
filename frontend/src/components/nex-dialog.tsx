"use client";
import {useEffect,useId,useRef,type ReactNode} from 'react';
import {X} from 'lucide-react';
/** Native modal dialog styled like the NexEase form sheet (header, close icon, scrolling body). */
export default function NexDialog({title,onClose,children,busy=false}:{title:string;onClose:()=>void;children:ReactNode;busy?:boolean}){
 const ref=useRef<HTMLDialogElement>(null);const id=useId();
 useEffect(()=>{const d=ref.current;d?.showModal();return()=>{d?.close()}},[]);
 return <dialog ref={ref} aria-labelledby={id} onCancel={e=>{e.preventDefault();if(!busy)onClose()}} className="nx-modal nx-modal-sheet">
  <header className="nxf-header"><div className="min-w-0"><h2 id={id}>{title}</h2></div><button type="button" title="Close" aria-label="Close" disabled={busy} className="nxf-close" onClick={onClose}><X size={20} aria-hidden="true"/></button></header>
  <div className="nxf-body nx-modal-body">{children}</div>
 </dialog>
}

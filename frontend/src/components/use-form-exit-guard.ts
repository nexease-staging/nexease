"use client";
import {useEffect, useRef} from 'react';
import {confirmAction} from './nex-feedback';

export function useFormExitGuard(dirty:boolean,busy:boolean,onClose:()=>void) {
  const confirming=useRef(false);
  useEffect(()=>{
    if(!dirty&&!busy)return;
    const warn=(event:BeforeUnloadEvent)=>{event.preventDefault();event.returnValue='';};
    window.addEventListener('beforeunload',warn);
    return()=>window.removeEventListener('beforeunload',warn);
  },[dirty,busy]);
  return async()=>{
    if(busy||confirming.current)return;
    confirming.current=true;
    try {
      if(!dirty||await confirmAction('Discard unsaved changes? Your edits will be lost.'))onClose();
    } finally { confirming.current=false; }
  };
}

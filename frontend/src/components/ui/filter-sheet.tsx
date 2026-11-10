'use client';
import {useEffect,useRef,useId,type ReactNode} from 'react';
import {X} from 'lucide-react';
import IconButton from './icon-button';
export default function FilterSheet({open,onClose,children}:{open:boolean;onClose:()=>void;children:ReactNode}) {
 const ref=useRef<HTMLDialogElement>(null);const title=useId();
 useEffect(()=>{const d=ref.current;if(!d)return;if(open&&!d.open)d.showModal();if(!open&&d.open)d.close();},[open]);
 return <dialog ref={ref} className="nx-filter-sheet" aria-labelledby={title} onCancel={onClose} onClose={onClose}>
  <header className="flex items-center justify-between gap-3"><h2 id={title}>Filters</h2><IconButton icon={X} label="Close filters" onClick={onClose}/></header>
  <div className="space-y-4 py-4">{children}</div><button type="button" className="nx-button" onClick={onClose}>Done</button>
 </dialog>;
}

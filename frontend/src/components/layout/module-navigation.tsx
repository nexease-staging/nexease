"use client";

import {useEffect, useRef, useState} from "react";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {useQuery} from "@tanstack/react-query";
import {ChevronDown} from "lucide-react";
import {navigationSections} from "@/config/navigation";
import {useAuth} from "@/features/auth/auth-context";
import {hasPermission} from "@/lib/authorization/permissions";
import {getConfig} from "@/features/business/workspace";

/** Uses the existing route and permission catalogue; never substitutes UI access for server checks. */
export default function ModuleNavigation() {
  const pathname=usePathname();
  const {authentication}=useAuth();
  const permissions=authentication?.role.permissions??[];
  const config=useQuery({queryKey:["business-config"],queryFn:getConfig,enabled:!!authentication});
  const [open,setOpen]=useState<string|null>(null);
  const ref=useRef<HTMLElement>(null);
  useEffect(()=>setOpen(null),[pathname]);
  useEffect(()=>{
    const close=(e:PointerEvent)=>{if(!ref.current?.contains(e.target as Node))setOpen(null)};
    const key=(e:KeyboardEvent)=>{if(e.key==="Escape"){setOpen(null);ref.current?.querySelector<HTMLButtonElement>('[aria-expanded="true"]')?.focus()}};
    document.addEventListener("pointerdown",close);document.addEventListener("keydown",key);
    return()=>{document.removeEventListener("pointerdown",close);document.removeEventListener("keydown",key)};
  },[]);
  const order=["Overview","Inventory","Sales","Purchasing","Workforce","Taxation","Finance","Expenses","Administration"];
  const sections=order.flatMap(label=>{
    const section=navigationSections.find(s=>s.label===label);if(!section)return [];
    if(config.data){
      const moduleKey:Record<string,string>={Workforce:"workforce",Taxation:"taxation",Finance:"finance",Expenses:"expenses"};
      if(moduleKey[label]&&config.data.modules?.[moduleKey[label]]===false)return [];
      if(!["Overview","Expenses","Administration","Taxation","Finance","Workforce"].includes(label)&&!config.data.profile.modules.includes(label))return [];
    }
    const extra=label==="Inventory"?navigationSections.find(s=>s.label==="Barcode")?.items??[]:[];
    const items=[...section.items,...extra].filter(item=>
      hasPermission(permissions,item.permission)&&
      (!["/e-invoices","/e-way-bills"].includes(item.href)||config.data?.modules?.einvoice===true)&&
      (item.href!=="/barcode"||config.data?.modules?.barcode!==false));
    return items.length?[{label:label==="Overview"?"Dashboard":label==="Purchasing"?"Purchase":label,items}]:[];
  });
  return <nav ref={ref} aria-label="Business modules" className="nx-module-nav">
    <div className="nx-module-nav-inner">{sections.map(section=>{
      const active=section.items.some(i=>pathname===i.href||pathname.startsWith(i.href+"/"));
      const Icon=section.items[0].icon;
      const direct=section.label==="Dashboard";
      return <div className="nx-module-group" key={section.label}>
        {direct?<Link href="/dashboard" aria-current={active?"page":undefined} className="nx-module-tab"><Icon size={22}/><span>Dashboard</span></Link>:
        <button type="button" className="nx-module-tab" data-active={active} aria-expanded={open===section.label} aria-controls={"module-"+section.label}
          onClick={()=>setOpen(open===section.label?null:section.label)}><Icon size={22}/><span>{section.label}<ChevronDown size={12}/></span></button>}
        {!direct&&open===section.label&&<div id={"module-"+section.label} className="nx-module-menu" aria-label={section.label}>
          {section.items.map(({href,label,icon:ItemIcon})=><Link key={href} href={href} aria-current={pathname===href?"page":undefined} onClick={()=>setOpen(null)}><ItemIcon size={17}/>{label}</Link>)}
        </div>}
      </div>;
    })}</div>
  </nav>;
}

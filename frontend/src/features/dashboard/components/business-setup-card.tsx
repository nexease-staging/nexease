"use client";
import Link from "next/link";
import {useQuery} from "@tanstack/react-query";
import {ImagePlus,Mail,Landmark,RefreshCw} from "lucide-react";
import {useAuth} from "@/features/auth/auth-context";
import {getConfig} from "@/features/business/workspace";
import {hasPermission} from "@/lib/authorization/permissions";
export default function BusinessSetupCard(){
 const {authentication}=useAuth();
 const query=useQuery({queryKey:["business-config"],queryFn:getConfig,enabled:!!authentication});
 const setup=query.data?.setup;
 if(query.isPending)return <p className="nx-muted py-3 text-xs" role="status">Checking business setup…</p>;
 if(query.isError)return <div className="flex items-center gap-3 py-3 text-xs text-slate-500"><span>Could not check business setup.</span><button type="button" className="nx-button nx-secondary" onClick={()=>void query.refetch()}><RefreshCw size={13}/>Retry</button></div>;
 // Avoid presenting already-completed work as missing when using an older backend.
 if(!setup)return null;
 const permissions=authentication?.role.permissions??[];
 const tasks=[
  {key:"logo",title:"Add your business logo",hint:"Personalise the invoices you share with customers.",label:"Invoice settings",href:"/settings/invoices",icon:ImagePlus,permission:"organizations.update"},
  {key:"email",title:"Connect your email",hint:"Use your mailbox when sending business documents.",label:"Email settings",href:"/settings#my-email",icon:Mail},
  {key:"bank",title:"Review your bank details",hint:"Keep your payment details ready for your invoices.",label:"Bank details",href:"/settings/invoices",icon:Landmark,permission:"organizations.update"}
 ].filter(task=>!setup[task.key as keyof typeof setup]&&hasPermission(permissions,task.permission));
 if(!tasks.length)return null;
 return <section className="nx-panel nx-setup-panel" aria-label="Business setup shortcuts"><h2>Complete your business profile</h2>{tasks.map(({key,title,hint,label,href,icon:Icon})=><div key={key}><Icon size={18}/><span><strong>{title}</strong><small>{hint}</small></span><Link href={href} className="nx-button nx-secondary nx-btn-sm">{label}</Link></div>)}</section>;
}

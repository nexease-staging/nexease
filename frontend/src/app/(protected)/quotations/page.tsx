"use client";
import {useState} from "react";
import {useQuery} from "@tanstack/react-query";
import {apiRequest} from "@/lib/api/client";
import InvoiceDialog from "@/features/invoices/components/invoice-dialog";
import {formatMoney} from "@/lib/format";
import {useAuth} from "@/features/auth/auth-context";
import {hasPermission} from "@/lib/authorization/permissions";
type Quote={number:string;customer:string;date:string;valid_until:string;notes:string;total:string;items:{name:string;quantity:string;unit_price:string;total:string}[]};
export default function Quotations(){
  const [open,setOpen]=useState(false),[page,setPage]=useState(1);
  const {authentication}=useAuth();
  const query=useQuery({queryKey:["quotations",page],queryFn:async()=>(await apiRequest<{rows:Quote[];more:boolean}>(`/business/quotations/?page=${page}`)).data});
  return <section className="space-y-3"><header className="flex items-center justify-between"><h1>Estimates / Quotations</h1>
    {hasPermission(authentication?.role.permissions??[],"invoices.create") && <button className="nx-button" onClick={()=>setOpen(true)}>New quotation</button>}</header>
    {query.isPending && <p>Loading quotations…</p>}{query.error && <p role="alert">{query.error.message}</p>}
    {query.data?.rows.length===0 && <p>No quotations yet.</p>}
    {query.data?.rows.map(q=><details className="nx-card p-3" key={q.number}><summary>{q.customer} · {q.number} · {formatMoney(q.total)}</summary>
      <p>{q.date}{q.valid_until && " · Valid until "+q.valid_until}</p>{q.items.map((line,i)=><p key={i}>{line.name} · {line.quantity} × {formatMoney(line.unit_price)} · {formatMoney(line.total)}</p>)}<p>{q.notes}</p></details>)}
    {page>1 && <button onClick={()=>setPage(page-1)}>Previous</button>} {query.data?.more && <button onClick={()=>setPage(page+1)}>Next</button>}
    <InvoiceDialog quotation initialMode="direct" open={open} onClose={()=>setOpen(false)}/></section>;
}

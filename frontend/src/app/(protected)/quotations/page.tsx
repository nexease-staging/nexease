"use client";
import {ChevronDown, Download, FilePlus2, ClipboardList, Plus} from "lucide-react";
import Link from "next/link";
import {useState} from "react";
import {useQuery} from "@tanstack/react-query";
import {apiRequest,apiBinaryRequest} from "@/lib/api/client";
import {downloadBlob} from "@/lib/browser/download";
import InvoiceDialog from "@/features/invoices/components/invoice-dialog";
import type {Quotation} from "@/features/invoices/quotation";
import SalesOrderDialog from "@/features/sales-orders/components/sales-order-dialog";
import {formatMoney} from "@/lib/format";
import {useAuth} from "@/features/auth/auth-context";
import {hasPermission} from "@/lib/authorization/permissions";

export default function Quotations(){
  const [open,setOpen]=useState(false),[page,setPage]=useState(1);
  const [order,setOrder]=useState<Quotation>(),[invoice,setInvoice]=useState<Quotation>();
  const [sharing,setSharing]=useState(""),[error,setError]=useState("");
  const {authentication}=useAuth();
  const can=(key:string)=>hasPermission(authentication?.role.permissions??[],key);
  const query=useQuery({queryKey:["quotations",page],queryFn:async()=>(await apiRequest<{rows:Quotation[];more:boolean}>(`/business/quotations/?page=${page}`)).data});
  async function share(number:string){
    setSharing(number);setError("");
    try{
      const {blob}=await apiBinaryRequest(`/business/quotations/${encodeURIComponent(number)}/pdf/`);
      await downloadBlob(blob,number+".pdf");
    }catch(e){setError(e instanceof Error?e.message:"Unable to prepare quotation PDF.")}
    finally{setSharing("")}
  }
  return <section className="space-y-3"><header className="flex items-center justify-between"><h1 className="text-2xl font-bold">Estimates / Quotations</h1>
    {can("invoices.create") && <button className="nx-button" onClick={()=>setOpen(true)}><Plus size={16}/> New quotation</button>}</header>
    {query.isPending && <p>Loading quotations…</p>}{query.error && <p role="alert">{query.error.message}</p>}
    {error && <p role="alert">{error}</p>}{query.data?.rows.length===0 && <p>No quotations yet.</p>}
    {query.data?.rows.map(q=><details className="nx-card overflow-hidden" key={q.number}><summary className="flex cursor-pointer list-none items-center justify-between gap-3 p-4"><span className="min-w-0"><strong className="block break-words">{q.customer}</strong><span className="text-sm">{q.number} · {q.date}</span></span><span className="flex items-center gap-2 font-semibold">{formatMoney(q.total)} <ChevronDown size={18}/></span></summary>
      <div className="border-t p-4">{q.valid_until && <p>Valid until {q.valid_until}</p>}
      <div className="divide-y">{q.items.map((line,i)=><div key={i} className="flex justify-between gap-4 py-2"><div><strong>{line.name}</strong><p className="text-sm">{line.quantity} × {formatMoney(line.unit_price)} · GST {line.tax_rate}%{Number(line.discount)>0 && " · Discount "+formatMoney(line.discount)}</p></div><span>{formatMoney(line.total)}</span></div>)}</div>{q.notes&&<p className="my-2 whitespace-pre-wrap">{q.notes}</p>}
      <div className="mt-3 flex flex-wrap gap-2">
        <button className="nx-button nx-secondary" disabled={!!sharing} onClick={()=>share(q.number)}><Download size={16}/>{sharing===q.number?"Preparing PDF…":"Share / download PDF"}</button>
        {q.conversion?.id?<Link href={`/${q.conversion.kind==="order"?"sales-orders":"invoices"}?view=${q.conversion.id}`}>View {q.conversion.number}</Link>:
        q.conversion?<p>Conversion in progress or awaiting review.</p>:<>
          {can("sales_orders.create")&&<button className="nx-button nx-secondary" onClick={()=>setOrder(q)}><ClipboardList size={16}/>Create sales order</button>}
          {can("invoices.create")&&<button className="nx-button" onClick={()=>setInvoice(q)}><FilePlus2 size={16}/>Create invoice</button>}</>}
        {q.linked_invoice&&<Link href={`/invoices?view=${q.linked_invoice.id}`}>View invoice {q.linked_invoice.number}</Link>}
      </div></div></details>)}
    {page>1 && <button onClick={()=>setPage(page-1)}>Previous</button>} {query.data?.more && <button onClick={()=>setPage(page+1)}>Next</button>}
    <InvoiceDialog quotation initialMode="direct" open={open} onClose={()=>setOpen(false)}/>
    {invoice&&<InvoiceDialog sourceQuote={invoice} initialMode="direct" open onClose={()=>{setInvoice(undefined);void query.refetch()}}/>}
    {order&&<SalesOrderDialog sourceQuote={order} salesOrderId={null} open canCreateCustomer={can("customers.create")} canCreateProduct={can("products.create")} onClose={()=>{setOrder(undefined);void query.refetch()}}/>}
  </section>;
}

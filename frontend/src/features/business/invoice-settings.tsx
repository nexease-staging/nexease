"use client";
import {getConfig} from "./workspace";
import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {apiRequest} from '@/lib/api/client';
type Settings=Record<string,string>;
type Template={id:string;name:string;color:string;layout:string};
export { default } from "./invoice-formats";
export const invoiceDetailFields=[['po_number','PO number'],['po_date','PO date'],['service_from','Service from'],['service_to','Service to'],['site_name','Site / project'],['shipping_address','Shipping / service address'],['place_of_supply','Place of supply (2-digit state code)'],['payment_terms','Payment terms'],['bank_details','Bank details'],['terms','Terms & conditions'],['signatory','Authorised signatory']];
export function TaxSelection({value,onChange}:{value:string;onChange:(v:string)=>void}){return <label className="text-sm">GST treatment<select className="nx-input" required value={value} onChange={e=>onChange(e.target.value)}><option value="">Choose GST / non-GST classification</option><option value="taxable">With GST — taxable</option><option value="exempt">Without GST — exempt supply</option><option value="nil_rated">Without GST — nil rated</option><option value="non_gst">Non-GST supply</option><option value="unregistered">Supplier is not GST registered</option></select></label>}
export function InvoiceDetails({id,issued=false}:{id:string;issued?:boolean}){
 const config=useQuery({queryKey:["business-config"],queryFn:getConfig});
 const q=useQuery({queryKey:['invoice-details',id],queryFn:async()=>(await apiRequest<{details:Settings;templates:Template[]}>(`/business/invoices/${id}/details/`)).data});const [draft,setDraft]=useState<Settings|null>(null);const [msg,setMsg]=useState('');const [busy,setBusy]=useState(false);const d=draft??q.data?.details??{};
 if((issued?config.data?.can_edit_issued_invoices:config.data?.can_edit_invoices)!==true)return null;
 return <details className="nx-panel my-5"><summary className="cursor-pointer font-semibold">Invoice details & GST classification</summary><p className="mt-2 text-xs text-slate-500">The print format is set once for all documents in Settings → Invoice formats.</p>{q.error&&<p role="alert">{q.error.message}</p>}<div className="grid md:grid-cols-2 gap-4 mt-4">{!issued&&<TaxSelection value={d.supply_type??''} onChange={v=>setDraft({...d,supply_type:v})}/>}{invoiceDetailFields.filter(([k])=>!issued||k!=="place_of_supply").map(([k,label])=><label key={k}>{label}<input className="nx-input" type={['po_date','service_from','service_to'].includes(k)?'date':'text'} value={d[k]??''} onChange={e=>setDraft({...d,[k]:e.target.value})}/></label>)}</div><button disabled={busy} className="nx-button mt-4" onClick={async()=>{setBusy(true);try{const allowed=['supply_type',...invoiceDetailFields.map(([k])=>k)];await apiRequest(`/business/invoices/${id}/details/`,{method:'POST',body:Object.fromEntries(Object.entries(d).filter(([k])=>allowed.includes(k)))});setMsg('Saved. Download the invoice PDF to see the updated document.')}catch(e){setMsg((e as Error).message)}finally{setBusy(false)}}}>Save details</button>{msg&&<p role="status">{msg}</p>}</details>
}

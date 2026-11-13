"use client";
import PasswordInput from "@/components/password-input";

import {useState, type FormEvent} from 'react';
import Link from 'next/link';
import {useQuery, useQueryClient} from '@tanstack/react-query';
import {apiBinaryRequest, apiRequest} from '@/lib/api/client';
import {downloadBlob} from '@/lib/browser/download';

type Row={id:string;number:string;date:string;status?:string;invoice_status?:string;customer?:string;customer_name?:string;invoice_number?:string;irn?:string;ack_no?:string;ack_date?:string};
type Listing={records:Row[];configured?:boolean;gstin?:string;environment?:string;can_configure?:boolean;can_issue?:boolean;can_cancel?:boolean;can_create?:boolean};
type Choice={id:string;name:string;code:string;item_type?:string;billing_address?:string};
const input='nx-input w-full';
const paths={einvoice:'/business/e-invoices/',challan:'/business/delivery-challans/'};
const emptyLine=()=>({product_id:'',qty:'1',value:'0',rate:'0'});
const reasons={job_work:'Job work',non_supply:'Movement other than supply',liquid_gas:'Liquid gas — quantity not known at dispatch',notified:'Other notified movement'};

function Picker({kind,value,onSelect,label}:{kind:'customers'|'products';value:string;onSelect:(x:Choice)=>void;label:string}) {
  const [q,setQ]=useState('');
  const list=useQuery({queryKey:['challan-picker',kind,q],queryFn:async()=>(await apiRequest<{records:Choice[]}>(`/business/lookup/?kind=${kind}&q=${encodeURIComponent(q)}`)).data.records,staleTime:30_000});
  const [selected,setSelected]=useState<Choice>();
  const options=(list.data??[]).filter(x=>kind!=='products'||x.item_type!=='service');
  if(selected&&selected.id===value&&!options.some(x=>x.id===value))options.push(selected);
  return <div className="space-y-1"><input className={input} value={q} onChange={e=>setQ(e.target.value)} placeholder={`Search ${kind}`} aria-label={`Search ${label}`}/>
    <label>{label}<select required className={input} value={value} onChange={e=>{const row=options.find(x=>x.id===e.target.value);if(row){setSelected(row);onSelect(row);}}}><option value="">Select…</option>{options.map(x=><option key={x.id} value={x.id}>{x.name} · {x.code}</option>)}</select></label>
    {list.isError&&<p role="alert">Could not load {kind}.</p>}</div>;
}

export default function SalesDocuments({mode}:{mode:keyof typeof paths}) {
  const irp=mode==='einvoice',path=paths[mode], qc=useQueryClient();
  const [invoiceLink]=useState(()=>typeof window==='undefined'?'':new URLSearchParams(window.location.search).get('invoice')||'');
  const [search,setSearch]=useState(irp?invoiceLink:''),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
  const [form,setForm]=useState(false),[cancel,setCancel]=useState<Row>(),[reason,setReason]=useState('2'),[remarks,setRemarks]=useState('');
  const [challanReason,setChallanReason]=useState('job_work');
  const [customer,setCustomer]=useState(''),[lines,setLines]=useState([emptyLine()]);
  const list=useQuery({queryKey:['sales-documents',mode,search],queryFn:async()=>(await apiRequest<Listing>(path+'?search='+encodeURIComponent(search))).data,retry:false});
  const data=list.data;
  async function send(body:Record<string,unknown>, url=path){
    setBusy(true);setMessage('');
    try{await apiRequest(url,{method:'POST',body:{...body,confirm:true}});setMessage('Saved.');setForm(false);setCancel(undefined);setRemarks('');return true;}
    catch(e){setMessage(e instanceof Error?e.message:'Request failed.');return false;}
    finally{await qc.invalidateQueries({queryKey:['sales-documents',mode]});setBusy(false);}
  }
  function submit(e:FormEvent<HTMLFormElement>){
    e.preventDefault();const fields=Object.fromEntries(new FormData(e.currentTarget).entries());
    if(irp){void send({...fields,action:'configure'});return;}
    if(confirm('Issue this delivery challan? It records movement details without posting stock or accounting entries.')){
      void send({...fields,customer_id:customer,items:lines}).then(ok=>{if(ok){setCustomer('');setLines([emptyLine()]);}});
    }
  }
  async function pdf(row:Row){
    try{const file=await apiBinaryRequest(path+row.id+'/');await downloadBlob(file.blob,file.filename||row.number+'.pdf');}
    catch(e){setMessage(e instanceof Error?e.message:'Could not download PDF.');}
  }
  function irpAction(row:Row,action:string){
    if(confirm(action==='generate'?`Submit ${row.number} to the ${data?.environment==='live'?'LIVE':'TEST'} IRP?`:`Check the IRP status for ${row.number}?`))void send({id:row.id,action});
  }
  return <div className="mx-auto max-w-6xl space-y-5">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-sm text-slate-600">Sales</p><h1 className="text-3xl font-semibold">{irp?'GST e-invoices':'Delivery challans'}</h1></div><Link href="/invoices" className="nx-button nx-secondary">Sales invoices</Link>{irp&&<Link href="/e-way-bills" className="nx-button nx-secondary">E-way bills</Link>}</div>
    <p className="text-slate-600">{irp?'Register issued domestic B2B tax invoices with the IRP. Registered live invoices include the signed QR code on the sales invoice PDF.':'Issue movement documents for goods and download three labelled copies. Stock, invoicing and e-way bills are handled separately.'}</p>
    {data&&irp&&<p className="nx-panel">{data.environment==='live'?'LIVE IRP':'TEST IRP · not a legal invoice'} · {data.gstin||'Set your GSTIN in Taxation'} · {data.configured?'Credentials saved':'IRP credentials not connected'} {data.can_configure&&<button className="nx-button ml-2" onClick={()=>setForm(!form)}>{form?'Close':'Connect IRP'}</button>}</p>}
    {data?.can_create&&!irp&&<button className="nx-button" onClick={()=>setForm(!form)}>{form?'Close':'New delivery challan'}</button>}
    {form&&<form onSubmit={submit} className="nx-panel space-y-4">
      {irp?<><h2 className="text-xl font-semibold">Connect this workspace’s GSTIN</h2><p>Use dedicated IRP API credentials for Quicko GSP. The password is encrypted on the server.</p><div className="grid gap-3 sm:grid-cols-2">
        <label>IRP API username<input required className={input} name="username" maxLength={100}/></label><label>IRP API password<PasswordInput required className={input} name="password" type="password" autoComplete="new-password" maxLength={200}/></label>
        <label>Registered seller address<input required className={input} name="address" maxLength={100}/></label><label>Seller city<input required className={input} name="city" maxLength={50}/></label><label>Seller PIN code<input required className={input} name="pincode" pattern="[1-9][0-9]{5}" inputMode="numeric"/></label></div></>:
        <><h2 className="text-xl font-semibold">Issue a delivery challan</h2><div className="grid gap-3 sm:grid-cols-2">
        <Picker kind="customers" value={customer} onSelect={x=>setCustomer(x.id)} label="Consignee"/>
        <label>Dispatch date<input required className={input} type="date" name="date" defaultValue={new Date().toLocaleDateString('en-CA',{timeZone:'Asia/Kolkata'})}/></label>
        <label>Reason<select required className={input} name="reason" value={challanReason} onChange={e=>setChallanReason(e.target.value)}>{Object.entries(reasons).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label>
        <label>Place of supply (state code)<input required className={input} name="pos" pattern="[0-9]{2}" inputMode="numeric"/></label>
        <label>Linked sales invoice number (optional)<input className={input} name="invoice_number" defaultValue={invoiceLink} maxLength={50}/></label>
        <label>Delivery address (optional override)<input className={input} name="address" maxLength={500}/></label>
        <label>Vehicle / transport reference<input className={input} name="transport" maxLength={100}/></label>
        <label>Notes<input className={input} name="notes" maxLength={500}/></label></div>
        {lines.map((line,i)=><div key={i} className="grid items-end gap-2 rounded border p-3 sm:grid-cols-5">
          <Picker kind="products" value={line.product_id} onSelect={x=>setLines(v=>v.map((l,j)=>i===j?{...l,product_id:x.id}:l))} label={`Product ${i+1}`}/>
          {(['qty','value','rate'] as const).map((key,j)=><label key={key}>{['Quantity','Taxable value ₹','GST %'][j]}<input required className={input} type="number" step=".01" min={key==='qty'&&challanReason!=='liquid_gas'?'.01':'0'} value={line[key]} onChange={e=>setLines(v=>v.map((l,n)=>i===n?{...l,[key]:e.target.value}:l))}/></label>)}
          <button type="button" className="nx-button nx-secondary" disabled={lines.length===1} onClick={()=>setLines(v=>v.filter((_,j)=>i!==j))}>Remove</button></div>)}
        <button type="button" className="nx-button nx-secondary" disabled={lines.length>=50} onClick={()=>setLines(v=>[...v,emptyLine()])}>Add goods line</button></>}
      <button className="nx-button ml-2" disabled={busy}>{irp?'Save IRP credentials':'Issue challan'}</button>
    </form>}
    {cancel&&<form className="nx-panel flex flex-wrap items-end gap-3" onSubmit={e=>{e.preventDefault();if(confirm(`Cancel the IRN for ${cancel.number}?`))void send({id:cancel.id,action:'cancel',reason,remarks});}}>
      <label>IRP cancellation reason<select className={input} value={reason} onChange={e=>setReason(e.target.value)}>{['Duplicate','Data entry mistake','Order cancelled','Other'].map((v,i)=><option key={v} value={i+1}>{v}</option>)}</select></label>
      <label>Remarks<input required className={input} minLength={3} maxLength={100} value={remarks} onChange={e=>setRemarks(e.target.value)}/></label><button className="nx-button" disabled={busy}>Confirm IRP cancellation</button><button type="button" className="nx-button nx-secondary" onClick={()=>setCancel(undefined)}>Back</button>
    </form>}
    {message&&<p role="status" className="nx-panel">{message}</p>}
    <label>Search documents<input className={input} value={search} onChange={e=>setSearch(e.target.value)} placeholder="Document number"/></label>
    {list.isLoading&&<p role="status">Loading…</p>}
    {list.isError&&<p role="alert">{list.error.message}</p>}
    {data&&<div className="overflow-x-auto nx-panel"><table className="nx-mobile-records nx-financial-records w-full text-left text-sm"><thead><tr>{['Number / date','Customer','Status','Actions'].map(x=><th key={x} className="p-2">{x}</th>)}</tr></thead><tbody>
      {data.records.map(row=><tr className="border-t" key={row.id}><td data-label="Number / date" className="p-2">{row.number}<br/>{row.date}{row.invoice_number&&<><br/>Invoice: {row.invoice_number}</>}</td><td data-label="Customer" className="p-2">{row.customer||row.customer_name}</td><td data-label="Status" className="p-2">{row.status?.replaceAll('_',' ')||'Not submitted'}{row.irn&&<div className="max-w-56 break-all">IRN: {row.irn}<br/>Ack: {row.ack_no} {row.ack_date}</div>}</td>
      <td data-label="Actions" className="p-2"><div className="flex flex-wrap gap-2">
        {irp?<>{!row.status&&data.can_issue&&data.configured&&row.invoice_status!=='CANCELLED'&&<button className="nx-button" disabled={busy} onClick={()=>irpAction(row,'generate')}>Generate IRN</button>}
        {row.status==='pending'&&data.can_issue&&<button className="nx-button" disabled={busy} onClick={()=>irpAction(row,'recover')}>Recover IRN</button>}
        {row.status==='registered'&&data.can_cancel&&<button className="nx-button nx-secondary" disabled={busy} onClick={()=>setCancel(row)}>Cancel IRN</button>}
        {row.status==='cancel_pending'&&data.can_cancel&&<button className="nx-button" disabled={busy} onClick={()=>irpAction(row,'check-cancellation')}>Check cancellation</button>}
        <button className="nx-button nx-secondary" onClick={()=>void apiBinaryRequest(`/business/e-invoices/${row.id}/pdf/`).then(f=>downloadBlob(f.blob,f.filename||row.number+'.pdf')).catch(e=>setMessage(e.message))}>Invoice PDF</button></>:
        <><button className="nx-button" onClick={()=>void pdf(row)}>Download PDF</button>{row.status==='issued'&&data.can_cancel&&<button className="nx-button nx-secondary" disabled={busy} onClick={()=>{if(confirm(`Cancel ${row.number}?`))void send({},path+row.id+'/');}}>Cancel</button>}</>}
      </div></td></tr>)}
    </tbody></table>{!data.records.length&&<p className="p-3">No matching documents.</p>}</div>}
  </div>;
}

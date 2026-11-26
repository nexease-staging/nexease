"use client";
import PasswordInput from "@/components/password-input";

import {useState, type FormEvent} from 'react';
import {Ban, Download, FileText, Plus, RefreshCw, Send, ShieldCheck, Truck, X} from 'lucide-react';
import {CompactList, CompactRow, ListScreen, ListState, StatusBadge, useDebounced, type ListAction} from '@/components/list/list-kit';
import {Badge} from '@/components/ui/badge';
import {confirmAction, notify} from '@/components/nex-feedback';
import {challanStatus} from '@/features/sales/status';
import {formatDate} from '@/lib/format';
import {useQuery, useQueryClient} from '@tanstack/react-query';
import {useRouter} from 'next/navigation';
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
  const irp=mode==='einvoice',path=paths[mode], qc=useQueryClient(), router=useRouter();
  const [invoiceLink]=useState(()=>typeof window==='undefined'?'':new URLSearchParams(window.location.search).get('invoice')||'');
  const [search,setSearch]=useState(irp?invoiceLink:''),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
  const [form,setForm]=useState(false),[cancel,setCancel]=useState<Row>(),[reason,setReason]=useState('2'),[remarks,setRemarks]=useState('');
  const [challanReason,setChallanReason]=useState('job_work');
  const [customer,setCustomer]=useState(''),[lines,setLines]=useState([emptyLine()]);
  const query=useDebounced(search.trim());
  const list=useQuery({queryKey:['sales-documents',mode,query],queryFn:async()=>(await apiRequest<Listing>(path+'?search='+encodeURIComponent(query))).data,retry:false});
  const data=list.data;
  async function send(body:Record<string,unknown>, url=path, done='Saved.'){
    setBusy(true);setMessage('');
    try{await apiRequest(url,{method:'POST',body:{...body,confirm:true}});notify(done);setForm(false);setCancel(undefined);setRemarks('');return true;}
    catch(e){setMessage(e instanceof Error?e.message:'Request failed.');return false;}
    finally{await qc.invalidateQueries({queryKey:['sales-documents',mode]});setBusy(false);}
  }
  function submit(e:FormEvent<HTMLFormElement>){
    e.preventDefault();const fields=Object.fromEntries(new FormData(e.currentTarget).entries());
    if(irp){void send({...fields,action:'configure'},path,'IRP credentials saved.');return;}
    void confirmAction('Issue this delivery challan? It records movement details without posting stock or accounting entries.').then(yes=>{
      if(yes)void send({...fields,customer_id:customer,items:lines},path,'Delivery challan issued.').then(ok=>{if(ok){setCustomer('');setLines([emptyLine()]);}});
    });
  }
  const [downloading,setDownloading]=useState('');
  async function pdf(row:Row,url=path+row.id+'/'){
    setDownloading(row.id);
    try{const file=await apiBinaryRequest(url);await downloadBlob(file.blob,file.filename||row.number+'.pdf');}
    catch(e){notify(e instanceof Error?e.message:'Could not download PDF.','error');}
    finally{setDownloading('');}
  }
  async function irpAction(row:Row,action:string){
    const question=action==='generate'?`Submit ${row.number} to the ${data?.environment==='live'?'LIVE':'TEST'} IRP?`:action==='recover'?`Recover the IRN for ${row.number}?`:`Check the IRP status for ${row.number}?`;
    if(await confirmAction(question))void send({id:row.id,action},path,action==='generate'?'Submitted to the IRP.':'IRP status updated.');
  }
  async function cancelChallan(row:Row){
    if(await confirmAction(`Cancel delivery challan ${row.number}?`))void send({},path+row.id+'/','Delivery challan cancelled.');
  }
  function rowActions(row:Row):ListAction[]{
    const a:ListAction[]=[];
    if(!data)return a;
    if(irp){
      if(!row.status&&data.can_issue&&data.configured&&row.invoice_status!=='CANCELLED')a.push({icon:Send,label:`Generate IRN for ${row.number}`,disabled:busy,onClick:()=>void irpAction(row,'generate')});
      if(row.status==='pending'&&data.can_issue)a.push({icon:RefreshCw,label:`Recover IRN for ${row.number}`,disabled:busy,onClick:()=>void irpAction(row,'recover')});
      if(row.status==='cancel_pending'&&data.can_cancel)a.push({icon:RefreshCw,label:`Check cancellation for ${row.number}`,disabled:busy,onClick:()=>void irpAction(row,'check-cancellation')});
      a.push({icon:Download,label:`Download invoice PDF ${row.number}`,busy:downloading===row.id,onClick:()=>void pdf(row,`/business/e-invoices/${row.id}/pdf/`)});
      if(row.status==='registered'&&data.can_cancel)a.push({icon:Ban,label:`Cancel IRN for ${row.number}`,disabled:busy,onClick:()=>setCancel(row)});
    }else{
      a.push({icon:Download,label:`Download PDF ${row.number}`,busy:downloading===row.id,onClick:()=>void pdf(row)});
      if(row.status==='issued'&&data.can_cancel)a.push({icon:Ban,label:`Cancel ${row.number}`,disabled:busy,onClick:()=>void cancelChallan(row)});
    }
    return a;
  }
  const irnStatus:Record<string,{label:string;tone:'success'|'warning'|'danger'|'neutral'}>={registered:{label:'IRN registered',tone:'success'},pending:{label:'Pending',tone:'warning'},cancel_pending:{label:'Cancelling',tone:'warning'},cancelled:{label:'IRN cancelled',tone:'danger'}};
  const title=irp?'GST e-invoices':'Delivery challans';
  const canOpenForm=irp?!!data?.can_configure:!!data?.can_create;
  const formLabel=irp?(data?.configured?'Update IRP login':'Connect IRP'):'New challan';
  return <ListScreen
    title={title}
    subtitle={irp?'Register B2B tax invoices with the IRP; the signed QR prints on the invoice PDF.':'Movement documents for goods, in three labelled copies. Stock and invoicing are handled separately.'}
    primary={canOpenForm?{label:form?'Close form':formLabel,icon:form?X:irp?ShieldCheck:Plus,onClick:()=>setForm(!form)}:null}
    actions={[{icon:FileText,label:'Sales invoices',onClick:()=>router.push('/invoices')},...(irp?[{icon:Truck,label:'E-way bills',onClick:()=>router.push('/e-way-bills')}]:[])]}
    onRefresh={()=>void list.refetch()} refreshing={list.isFetching}
    search={{value:search,onChange:setSearch,placeholder:irp?'Search invoice number':'Search challan number'}}
    above={<>
    {data&&irp&&<p className="nx-panel flex flex-wrap items-center gap-2 text-sm"><Badge tone={data.environment==='live'?'success':'warning'}>{data.environment==='live'?'LIVE IRP':'TEST IRP · not a legal invoice'}</Badge><span>{data.gstin||'Set your GSTIN in Taxation'}</span><span className="nx-muted">· {data.configured?'Credentials saved':'IRP credentials not connected'}</span></p>}
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
        <label>Vehicle registration (if applicable)<input className={input} name="vehicle_number" maxLength={24}/></label><label>Transport reference<input className={input} name="transport" maxLength={100}/></label>
        <label>Notes<input className={input} name="notes" maxLength={500}/></label></div>
        {lines.map((line,i)=><div key={i} className="grid items-end gap-2 rounded border p-3 sm:grid-cols-5">
          <Picker kind="products" value={line.product_id} onSelect={x=>setLines(v=>v.map((l,j)=>i===j?{...l,product_id:x.id}:l))} label={`Product ${i+1}`}/>
          {(['qty','value','rate'] as const).map((key,j)=><label key={key}>{['Quantity','Taxable value ₹','GST %'][j]}<input required className={input} type="number" step=".01" min={key==='qty'&&challanReason!=='liquid_gas'?'.01':'0'} value={line[key]} onChange={e=>setLines(v=>v.map((l,n)=>i===n?{...l,[key]:e.target.value}:l))}/></label>)}
          <button type="button" className="nx-button nx-secondary" disabled={lines.length===1} onClick={()=>setLines(v=>v.filter((_,j)=>i!==j))}>Remove</button></div>)}
        <button type="button" className="nx-button nx-secondary" disabled={lines.length>=50} onClick={()=>setLines(v=>[...v,emptyLine()])}>Add goods line</button></>}
      <button className="nx-button ml-2" disabled={busy}>{irp?'Save IRP credentials':'Issue challan'}</button>
    </form>}
    {cancel&&<form className="nx-panel flex flex-wrap items-end gap-3" onSubmit={e=>{e.preventDefault();void confirmAction(`Cancel the IRN for ${cancel.number}? This cannot be undone.`).then(yes=>{if(yes)void send({id:cancel.id,action:'cancel',reason,remarks},path,'IRN cancellation submitted.');});}}>
      <label>IRP cancellation reason<select className={input} value={reason} onChange={e=>setReason(e.target.value)}>{['Duplicate','Data entry mistake','Order cancelled','Other'].map((v,i)=><option key={v} value={i+1}>{v}</option>)}</select></label>
      <label>Remarks<input required className={input} minLength={3} maxLength={100} value={remarks} onChange={e=>setRemarks(e.target.value)}/></label><button className="nx-button" disabled={busy}>Confirm IRP cancellation</button><button type="button" className="nx-button nx-secondary" onClick={()=>setCancel(undefined)}>Back</button>
    </form>}
    {message&&<p role="alert" className="nx-panel" style={{color:'var(--nx-danger-fg)'}}>{message}</p>}
    </>}>
    <ListState loading={list.isLoading} error={list.error} onRetry={()=>void list.refetch()} isEmpty={!data?.records.length}
      emptyIcon={irp?ShieldCheck:Truck} emptyTitle={query?'No matching documents':irp?'No invoices to register yet':'No delivery challans yet'}
      emptyDescription={query?'Try a different number.':irp?'Issued domestic B2B invoices appear here for IRN generation.':'Issue a challan when goods move without a sale, such as job work.'}>
      <CompactList label={title} columns={[{label:irp?'Customer / invoice':'Consignee / challan'},{label:irp?'IRN':'Linked invoice'},{label:'Status'}]}>
        {(data?.records??[]).map(row=><CompactRow key={row.id}
          title={row.customer||row.customer_name||'—'}
          subtitle={`${row.number} · ${formatDate(row.date)}`}
          meta={[irp?(row.irn?<span key="irn" title={row.irn}>{row.irn.slice(0,16)}… · Ack {row.ack_no}</span>:'—'):(row.invoice_number||'—')]}
          badge={irp?<Badge tone={irnStatus[row.status??'']?.tone??'neutral'}>{irnStatus[row.status??'']?.label??'Not submitted'}</Badge>:<StatusBadge status={row.status??'issued'} map={challanStatus}/>}
          actions={rowActions(row)}/>)}
      </CompactList>
    </ListState>
  </ListScreen>;
}

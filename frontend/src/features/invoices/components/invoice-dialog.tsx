"use client";
import {useEffect,useState,useRef} from "react";
import {useQueryClient} from "@tanstack/react-query";
import {Plus,Save,Trash2,X,UserRound,FileText} from "lucide-react";
import {createInvoice} from "@/features/invoices/api";
import {useSalesOrderList} from "@/features/sales-orders/hooks";
import {apiRequest} from "@/lib/api/client";
import {formatMoney} from "@/lib/format";
import MasterEntry from "@/components/master-entry";
import {TaxSelection,invoiceDetailFields} from "@/features/business/invoice-settings";
import GstLookup from "@/features/business/gst-lookup";
import BarcodeScan from "@/features/business/barcode-scan";
type Line={item_type:string;hsn_code:string;sku:string;name:string;unit:string;quantity:string;unit_price:string;tax_rate:string;discount:string};
const empty=():Line=>({item_type:"goods",hsn_code:"",sku:"",name:"",unit:"PCS",quantity:"1",unit_price:"0",tax_rate:"0",discount:"0"});
const today=()=>{const d=new Date();return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10)};
export default function InvoiceDialog({open,onClose,onCreated,initialMode="order"}:{open:boolean;onClose:()=>void;onCreated?:(id:string)=>void;initialMode?:"direct"|"order"}){
 const [mode,setMode]=useState(initialMode),[supply,setSupply]=useState(""),[customer,setCustomer]=useState<Record<string,string>>({}),[details,setDetails]=useState<Record<string,string>>({}),[lines,setLines]=useState<Line[]>([empty()]),[message,setMessage]=useState(""),[busy,setBusy]=useState(false);
 const qc=useQueryClient();const ref=useRef<HTMLDialogElement>(null);
 const orders=useSalesOrderList({page:1,page_size:100,status:"FULFILLED",sort:"-created_at"});
 useEffect(()=>{if(open){setMode(initialMode);setCustomer({});setLines([empty()]);setSupply("");setDetails({});setMessage("");ref.current?.showModal()}else ref.current?.close()},[open,initialMode]);
 async function submit(e:React.FormEvent<HTMLFormElement>){
  e.preventDefault();setBusy(true);setMessage("");const f=new FormData(e.currentTarget);
  try{
   const common={invoice_date:String(f.get("date")),due_date:String(f.get("due")||""),notes:String(f.get("notes")||""),billing_details:{...details,supply_type:supply}};
   let id="";
   if(mode==="order"){id=(await createInvoice({...common,sales_order_id:String(f.get("order"))})).id}
   else{const r=await apiRequest<{id:string}>("/business/direct-invoices/",{method:"POST",body:{...common,invoice_number:String(f.get("number")||""),customer,items:lines}});id=r.data.id}
   await qc.invalidateQueries();onClose();onCreated?.(id);
  }catch(error){setMessage((error as Error).message)}finally{setBusy(false)}
 }
 const totals=lines.reduce((sum,line)=>{
  const subtotal=Math.round(Number(line.quantity)*Number(line.unit_price)*100+1e-8),discount=Math.round(Number(line.discount)*100);
  return {subtotal:sum.subtotal+subtotal,discount:sum.discount+discount,tax:sum.tax+Math.round((subtotal-discount)*Number(line.tax_rate)/100+1e-8)}
 },{subtotal:0,discount:0,tax:0});
 const amount=(cents:number)=>formatMoney(String(cents/100));
 const update=(i:number,patch:Partial<Line>)=>setLines(prev=>prev.map((line,j)=>j===i?{...line,...patch}:line));
 return <dialog ref={ref} aria-labelledby="invoice-create-heading" onCancel={e=>{e.preventDefault();if(!busy)onClose()}} className="nx-invoice-editor">
  <form key={String(open)} onSubmit={submit}>
   <header className="nx-editor-header"><div><p>NexEase · Sales</p><h2 id="invoice-create-heading">{mode==="direct"?"Create sale invoice":"Invoice from sales order"}</h2></div>
    <button type="button" disabled={busy} onClick={onClose} aria-label="Close invoice" className="nx-icon-btn"><X size={20}/></button>
   </header>
   <div className="nx-editor-body">
    <div className="flex flex-wrap gap-2" role="group" aria-label="Invoice source">{(["direct","order"] as const).map(value=><button type="button" key={value} aria-pressed={mode===value} className={"nx-button "+(mode===value?"":"nx-secondary")} onClick={()=>setMode(value)}>{value==="direct"?"Quick invoice":"From sales order"}</button>)}</div>
    <div className="nx-editor-columns">
     <section className="nx-panel space-y-4"><h3 className="nx-editor-section-title"><UserRound size={18}/>Customer information</h3>
      {mode==="order"?<label>Fulfilled sales order *<select name="order" required className="nx-input"><option value="">Choose an order</option>{orders.data?.sales_orders.map(o=><option value={o.id} key={o.id}>{o.so_number} · {o.customer.name}</option>)}</select>{orders.error&&<p role="alert">{orders.error.message}</p>}</label>:<>
       <label className="block text-sm">Customer *</label>
       <MasterEntry kind="customers" label="Customer name *" required value={customer.name||""} onChange={name=>setCustomer(customer.id?{name}:{...customer,name,id:"",code:""})} onSelect={r=>setCustomer({id:r.id,code:r.code,name:r.name,address:r.billing_address||"",state:r.state||"",gstin:r.gstin||"",phone:r.phone||"",email:r.email||""})}/>
       <p className="text-xs text-slate-500">Select a saved customer, or enter a new name to create one when saving.</p>
       <details><summary className="nx-editor-disclosure">Find business by GSTIN</summary><div className="mt-3"><GstLookup onSelect={r=>setCustomer({...customer,id:"",code:"",...r})}/></div></details>
       <details open><summary className="nx-editor-disclosure">Customer address & contact details</summary><div className="mt-3 grid gap-3 sm:grid-cols-2">{[["address","Billing address"],["gstin","GSTIN"],["state","State"],["phone","Phone"],["email","Email"],["code","Customer code (automatic if blank)"]].map(([key,label])=><label className="text-sm" key={key}>{label}<input className="nx-input" type={key==="email"?"email":"text"} value={customer[key]||""} onChange={e=>setCustomer({...customer,[key]:e.target.value})}/></label>)}</div></details>
      </>}
     </section>
     <section className="nx-panel space-y-4"><h3 className="nx-editor-section-title"><FileText size={18}/>Invoice details</h3>
      <div className="grid gap-4 sm:grid-cols-2"><label>Invoice date *<input name="date" type="date" required defaultValue={today()} className="nx-input"/></label><label>Due date<input name="due" type="date" className="nx-input"/></label></div>
      {mode==="direct"&&<label className="block text-sm">Invoice number (automatic if blank)<input name="number" placeholder="Automatic" className="nx-input"/></label>}
      <TaxSelection value={supply} onChange={setSupply}/>
      <label className="block text-sm">Place of supply {supply==="taxable"?"*":""}<input className="nx-input" placeholder="2-digit state code, e.g. 27" required={supply==="taxable"} value={details.place_of_supply||""} onChange={e=>setDetails({...details,place_of_supply:e.target.value})}/></label>
      <p className="text-xs leading-6 text-slate-500">Save a draft first, then review and issue it. Direct invoices do not dispatch stock.</p>
     </section>
    </div>
    {mode==="direct"&&<section className="nx-panel">
     <div className="flex items-center justify-between gap-3"><h3 className="nx-editor-section-title">Product items</h3><span className="text-xs text-slate-500">{lines.length} / 100 items</span></div>
     <p className="my-3 text-xs text-slate-500">Search an item, scan its barcode, or enter a new product or service.</p>
     <div className="nx-invoice-lines"><table><thead><tr><th>Product / service</th><th>Quantity</th><th>Rate ₹</th><th>Discount ₹</th><th>GST %</th><th>Total ₹</th><th><span className="sr-only">Actions</span></th></tr></thead><tbody>
      {lines.map((line,i)=><tr key={i}>
       <td data-label={"Item "+(i+1)} className="nx-invoice-item-cell">
        <BarcodeScan onSelect={r=>update(i,{sku:r.code,name:r.name,item_type:r.item_type||"goods",hsn_code:r.hsn_code||"",unit:r.unit||"PCS",unit_price:r.selling_price||"0"})} renderInput={(scan,inputRef,ready)=><MasterEntry kind="products" label={"name line "+(i+1)} placeholder="Search or add item" required value={line.name} inputRef={inputRef} scanMode={ready} onScan={scan}
         onChange={name=>setLines(prev=>prev.map((l,j)=>i===j?(l.sku?{...empty(),quantity:l.quantity,name}:{...l,name}):l))}
         onSelect={r=>update(i,{sku:r.code,name:r.name,item_type:r.item_type||"goods",hsn_code:r.hsn_code||"",unit:r.unit||"PCS",unit_price:r.selling_price||"0"})}/>}/>
        <details className="mt-2"><summary className="text-xs cursor-pointer">Type, HSN/SAC, SKU & unit</summary><div className="mt-2 grid grid-cols-2 gap-2">
         <label className="text-xs">Type<select aria-label={"item_type line "+(i+1)} className="nx-input" value={line.item_type} onChange={e=>update(i,{item_type:e.target.value})}><option value="goods">Goods</option><option value="service">Service</option></select></label>
         {(["hsn_code","sku","unit"] as const).map(key=><label key={key} className="text-xs">{{hsn_code:"HSN/SAC",sku:"SKU (auto)",unit:"Unit"}[key]}<input aria-label={key+" line "+(i+1)} className="nx-input" value={line[key]} onChange={e=>update(i,{[key]:e.target.value})}/></label>)}
        </div></details>
       </td>
       {(["quantity","unit_price","discount","tax_rate"] as const).map(key=><td key={key} data-label={{quantity:"Quantity",unit_price:"Rate ₹",discount:"Discount ₹",tax_rate:"GST %"}[key]}><input aria-label={key+" line "+(i+1)} className="nx-input" value={line[key]} required={key==="quantity"||key==="unit_price"} type="number" min={key==="quantity"?"0.01":"0"} max={key==="tax_rate"?100:undefined} step="0.01" onChange={e=>update(i,{[key]:e.target.value})}/></td>)}
       <td data-label="Line total" className="text-right font-semibold">{amount(Math.round((Math.round(Number(line.quantity)*Number(line.unit_price)*100+1e-8)-Math.round(Number(line.discount)*100))*(1+Number(line.tax_rate)/100)+1e-8))}</td>
       <td><button type="button" className="nx-icon-btn" aria-label={"Remove line "+(i+1)} disabled={lines.length===1} onClick={()=>setLines(prev=>prev.filter((_,j)=>j!==i))}><Trash2 size={17}/></button></td>
      </tr>)}
     </tbody></table></div>
     <button type="button" className="nx-button nx-secondary mt-4" disabled={lines.length>=100} onClick={()=>setLines(prev=>[...prev,empty()])}><Plus size={17}/>Add item</button>
    </section>}
    <div className="nx-editor-columns">
     <section className="nx-panel"><h3 className="nx-editor-section-title">Terms & additional details</h3>
      <label className="mt-4 block text-sm">Notes<textarea name="notes" className="nx-input" placeholder="Add a note for this invoice"/></label>
      <details className="mt-4"><summary className="nx-editor-disclosure">PO, service period, delivery & additional details</summary><div className="mt-4 grid gap-4 sm:grid-cols-2">{invoiceDetailFields.filter(([key])=>key!=="place_of_supply").map(([key,label])=><label className="text-sm" key={key}>{label}<input className="nx-input" type={["po_date","service_from","service_to"].includes(key)?"date":"text"} value={details[key]||""} onChange={e=>setDetails({...details,[key]:e.target.value})}/></label>)}</div></details>
     </section>
     {mode==="direct"&&<section className="nx-panel nx-invoice-totals"><h3 className="nx-editor-section-title">Invoice summary</h3><dl><div><dt>Subtotal</dt><dd>{amount(totals.subtotal)}</dd></div><div><dt>Discount</dt><dd>− {amount(totals.discount)}</dd></div><div><dt>Taxable / supply value</dt><dd>{amount(totals.subtotal-totals.discount)}</dd></div><div><dt>Total GST</dt><dd>{amount(totals.tax)}</dd></div><div className="nx-invoice-grand-total"><dt>Estimated total</dt><dd><output aria-label="Estimated total">{amount(totals.subtotal-totals.discount+totals.tax)}</output></dd></div></dl><p className="mt-3 text-xs text-slate-500">The saved invoice is validated and calculated by NexEase.</p></section>}
    </div>
    {message&&<p role="alert" className="rounded-lg bg-red-50 p-4 text-red-700">{message}</p>}
   </div>
   <footer className="nx-editor-footer"><button type="button" disabled={busy} className="nx-button nx-secondary" onClick={onClose}>Cancel</button><p>Draft first. Review before issuing.</p><button className="nx-button" disabled={busy}><Save size={17}/>{busy?"Saving…":"Save draft invoice"}</button></footer>
  </form>
 </dialog>;
}

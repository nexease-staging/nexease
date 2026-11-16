"use client";
import Link from "next/link";
import {useState} from "react";
import {useQuery} from "@tanstack/react-query";
import {apiRequest} from "@/lib/api/client";

const groups:Record<string,Record<string,string>>={
  Transaction:{"Sale report":"sales/document","Purchase report":"purchases/document","Day book":"/journal-entries","General ledger":"/general-ledger","Profit & loss and balance sheet":"/financial-dashboard","Cashflow":"/cash-flow","Trial balance":"/trial-balance"},
  Party:{"Customer outstanding":"/accounts-receivable","Supplier outstanding":"/accounts-payable","Sales by party":"sales/party","Purchases by party":"purchases/party","Party report by sold items":"sales/party-item","Party report by purchased items":"purchases/party-item"},
  GST:{"GSTR-1, GSTR-3B and GSTR-9 workpapers":"/taxation","Sales summary by HSN":"sales/hsn","SAC report":"sales/sac","Sales GST rate report":"sales/rate","Purchase GST rate report":"purchases/rate"},
  "Items and stock":{"Low stock summary":"inventory/low","Stock summary by item category":"inventory/category","Stock summary":"/inventory","Stock movements":"/stock-movements","Item sales":"sales/item","Item purchases":"purchases/item","Sales by item category":"sales/category","Purchases by item category":"purchases/category"},
  "Business status":{"Bank statements":"/banking","Invoice discount report":"sales/discount","Item-wise discount":"sales/item-discount"},
  Expenses:{"Expense transactions":"expenses/document","Expense categories":"expenses/category","Expense descriptions":"expenses/item"},
  Orders:{"Sales order transactions":"sales-orders/document","Purchase order transactions":"purchase-orders/document","Sales order items":"sales-orders/item","Purchase order items":"purchase-orders/item"},
  Loans:{"Employee advances":"/workforce/advances"},
};
function localDate(){const d=new Date();return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10)}
export default function Reports(){
  const [search,setSearch]=useState(""),[selection,setSelection]=useState(""),[title,setTitle]=useState("");
  const [from,setFrom]=useState(localDate().slice(0,8)+"01"),[to,setTo]=useState(localDate());
  const [source,group]=selection.split("/");
  const query=useQuery({queryKey:["sales-report",selection,from,to],enabled:!!selection&&!!from&&!!to,queryFn:async()=>(await apiRequest<{columns:string[];rows:string[][]}>(`/business/sales-reports/?source=${source}&group=${group}&from=${from}&to=${to}`)).data});
  if(selection)return <section className="nx-card p-4 space-y-3"><button onClick={()=>setSelection("")}>← Reports</button><h1>{title}</h1>{source==="inventory"?<p>Current stock across warehouses</p>:<div className="flex flex-wrap gap-3"><label>From<input className="nx-input" type="date" value={from} onChange={e=>setFrom(e.target.value)}/></label><label>To<input className="nx-input" type="date" value={to} onChange={e=>setTo(e.target.value)}/></label></div>}
    {query.isFetching && <p>Loading…</p>}{query.error && <p role="alert">{query.error.message}</p>}{query.data && (query.data.rows.length?<div className="overflow-x-auto"><table><thead><tr>{query.data.columns.map(c=><th className="p-2" key={c}>{c}</th>)}</tr></thead><tbody>{query.data.rows.map((r,i)=><tr key={i}>{r.map((c,j)=><td className="p-2" key={j}>{c}</td>)}</tr>)}</tbody></table></div>:<p>No records in this period.</p>)}</section>;
  return <section className="space-y-3"><h1>Reports</h1><input aria-label="Search reports" className="nx-input" placeholder="Search reports" value={search} onChange={e=>setSearch(e.target.value)}/>{Object.entries(groups).map(([name,items])=>{
    const entries=Object.entries(items).filter(([label])=>(name+" "+label).toLowerCase().includes(search.toLowerCase()));
    return entries.length>0 && <section key={name} className="nx-card p-4"><h2>{name}</h2>{entries.map(([label,path])=>path.startsWith("/")?<Link className="block py-2" key={label} href={path}>{label}</Link>:<button key={label} className="block py-2" onClick={()=>{setSelection(path);setTitle(label)}}>{label}</button>)}</section>
  })}</section>;
}

"use client";
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ArrowUpRight, ChevronRight, Search, Home, LayoutGrid, FileText, Package, Eye, EyeOff, RefreshCw } from 'lucide-react';
import { type NavigationSection, navigationSections, workforceSections } from '@/config/navigation';
import { useAuth } from '@/features/auth/auth-context';
import { hasPermission } from '@/lib/authorization/permissions';
import { getConfig } from '@/features/business/workspace';
import { getMainDashboard } from '@/features/dashboard/api';
import {ThemeToggle} from '@/components/theme-provider';
import MobileConnection from './mobile-connection';

const names: Record<string,string> = {'Accounts Receivable':'Money customers owe','Accounts Payable':'Money you owe','Products':'Items & services','Customers':'Customers','Vendor Bills':'Supplier bills','Dashboard':'Business overview','Chart of Accounts':'Account categories','General Ledger':'Account transactions','Trial Balance':'Account balances'};
export function useEasyFeatures() {
 const {authentication}=useAuth();
 const config=useQuery({queryKey:['business-config'],queryFn:getConfig});
 const sections=[...navigationSections,...workforceSections];
 const seen=new Set<string>();
 return sections.filter(s=>s.label!=='Workforce'||config.data?.modules?.workforce!==false)
 .filter(s=>!['Finance','Taxation','Barcode','Expenses'].includes(s.label)||config.data?.modules?.[s.label.toLowerCase()]!==false)
 .filter(s=>s.label==='Expenses'||!config.data||['Overview','Administration','Barcode'].includes(s.label)||config.data.profile.modules.includes(s.label)||workforceSections.includes(s)&&config.data?.modules?.workforce!==false)
 .map(s=>({...s,items:s.items.filter(i=>{
  if(i.href.startsWith('/workforce')&&!hasPermission(authentication?.role.permissions??[],'labour.read')&&!hasPermission(authentication?.role.permissions??[],'payroll.read'))return false;
  if(seen.has(i.href)||!hasPermission(authentication?.role.permissions??[],i.permission)) return false;
  if(i.href==='/workforce/accounts'&&config.data?.modules?.finance===false)return false;
  seen.add(i.href); return true;
 })})).filter(s=>s.items.length).reduce<NavigationSection[]>((groups, section) => {
  const existing = groups.find(group => group.label === section.label);
  if (existing) existing.items.push(...section.items);
  else groups.push({...section, items: [...section.items]});
  return groups;
 }, []);
}
export function EasyNav(){
 const path=usePathname(); const features=useEasyFeatures().flatMap(s=>s.items);
 const tabs=[{href:'/home',label:'Home',icon:Home},{href:'/invoices',label:'Sales',icon:FileText},{href:'/products',label:'Items',icon:Package},{href:'/tools',label:'More',icon:LayoutGrid}];
 return <nav className="easy-nav" aria-label="Main navigation">{tabs.filter(t=>['/home','/tools'].includes(t.href)||features.some(f=>f.href===t.href)).map(t=><Link key={t.href} href={t.href} aria-current={path.replace(/\/$/,'')===t.href?'page':undefined}><t.icon size={22}/><span>{t.label}</span></Link>)}</nav>;
}
export function EasyTools(){
 const [search,setSearch]=useState(''); const [advanced,setAdvanced]=useState(false); const sections=useEasyFeatures();
 useEffect(()=>{setAdvanced(localStorage.getItem('nx.advanced')==='true');},[]);
 const change=(value:boolean)=>{setAdvanced(value);localStorage.setItem('nx.advanced',String(value));};
 const advancedSections=['Finance','Taxation','Administration'];
 return <div className="easy-page"><p className="easy-kicker">YOUR WORKSPACE</p><h1>What would you like to do?</h1><p className="easy-muted">Every tool, with a little less searching.</p><label className="easy-search"><Search size={20}/><input aria-label="Find a feature" placeholder="Try invoices, attendance, bank…" value={search} onChange={e=>setSearch(e.target.value)}/></label><div className="easy-preference"><div><strong>Advanced tools</strong><p>Accounting, taxes and administration</p></div><button type="button" role="switch" aria-checked={advanced} aria-label="Show advanced tools" className="easy-switch" onClick={()=>change(!advanced)}><span/></button></div>
 {sections.filter(s=>advanced||search||!advancedSections.includes(s.label)).map(s=>({...s,items:s.items.filter(i=>(i.label+' '+(names[i.label]||'')+' '+s.label).toLowerCase().includes(search.toLowerCase()))})).filter(s=>s.items.length).map(s=><section key={s.label} className="easy-section"><h2>{s.label==='Overview'?'Start here':s.label}</h2><div className="easy-tool-list">{s.items.map(i=><Link key={i.href} href={i.href}><span className="easy-tool-icon"><i.icon size={20}/></span><span>{names[i.label]||i.label}</span><ChevronRight size={17}/></Link>)}</div></section>)}
 {search&&!sections.some(s=>s.items.some(i=>(i.label+' '+(names[i.label]||'')+' '+s.label).toLowerCase().includes(search.toLowerCase())))&&<p role="status">No matching tools. Try a different word.</p>}
 <div className="mt-6"><ThemeToggle/></div><MobileConnection/></div>;
}
export function EasyHome(){
 const [period,setPeriod]=useState('month'); const [hide,setHide]=useState(false);const sections=useEasyFeatures(); const allowed=new Set(sections.flatMap(s=>s.items.map(i=>i.href)));
 const now=new Date(); const end=[now.getFullYear(),String(now.getMonth()+1).padStart(2,'0'),String(now.getDate()).padStart(2,'0')].join('-');
 const start=period==='today'?end:period==='month'?end.slice(0,8)+'01':`${now.getMonth()<3?now.getFullYear()-1:now.getFullYear()}-04-01`;
 const q=useQuery({queryKey:['easy-dashboard',start,end],queryFn:()=>getMainDashboard({start_date:start,end_date:end})});
 const money=(v?:string)=>hide?'••••':v===undefined?'—':new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(Number(v));
 const actions=[{href:'/invoices',title:'Bill a customer',hint:'Create and share invoices',icon:'↗',color:'mint'},{href:'/customer-payments',title:'Record money in',hint:'Keep payments up to date',icon:'↓',color:'blue'},{href:'/expenses',title:'Add an expense',hint:'Track your daily spending',icon:'↗',color:'peach'},{href:'/workforce',title:'Manage my team',hint:'Attendance, pay and sites',icon:'◎',color:'violet'}].filter(a=>allowed.has(a.href));
 return <div className="easy-page"><div className="easy-heading"><div><p className="easy-kicker">LET’S MAKE BUSINESS EASIER</p><h1>Your day, at a glance.</h1></div><button className="easy-icon-button" aria-label={hide?'Show amounts':'Hide amounts'} onClick={()=>setHide(!hide)}>{hide?<EyeOff size={20}/>:<Eye size={20}/>}</button></div><fieldset className="easy-segments"><legend className="sr-only">Summary period</legend>{[['today','Today'],['month','This month'],['year','Financial year']].map(([v,l])=><label key={v}><input type="radio" name="period" value={v} checked={period===v} onChange={()=>setPeriod(v)}/><span>{l}</span></label>)}</fieldset>
 {q.isError?<div role="alert" className="easy-error">We couldn’t load your summary. Your records have not changed.<button onClick={()=>void q.refetch()}><RefreshCw size={16}/>Try again</button></div>:<><div className="easy-sales"><p>Sales for this period</p><strong aria-live="polite">{q.isPending?'Loading…':money(q.data?.kpis.total_sales)}</strong><span>INR · {start} to {end}</span>{allowed.has('/invoices')&&<Link href="/invoices">View invoices <ArrowUpRight size={18}/></Link>}</div><div className="easy-balances"><div><span>Customers owe you</span><strong>{money(q.data?.kpis.receivables)}</strong><small>Outstanding receivables</small></div><div><span>You owe suppliers</span><strong>{money(q.data?.kpis.payables)}</strong><small>Outstanding payables</small></div></div></>}
 <section className="easy-section"><h2>Let’s get something done</h2><div className="easy-actions">{actions.map(a=><Link href={a.href} key={a.href}><span className={'easy-action-icon '+a.color}>{a.icon}</span><strong>{a.title}</strong><span>{a.hint}</span></Link>)}</div></section>
 <section className="easy-section"><div className="easy-heading"><h2>Needs your attention</h2><span className="easy-badge">Live</span></div>{q.isSuccess?<div className="easy-tool-list">{[{href:'/invoices',count:q.data.alerts.overdue_invoices,label:'overdue customer invoices'},{href:'/vendor-bills',count:q.data.alerts.overdue_bills,label:'overdue supplier bills'},{href:'/inventory',count:q.data.alerts.out_of_stock_items,label:'items out of stock'}].filter(a=>allowed.has(a.href)).map(a=><Link href={a.href} key={a.href}><span className="easy-count">{a.count}</span><span>{a.label}</span><ChevronRight size={18}/></Link>)}</div>:<p className="easy-muted">Your alerts will appear when the summary loads.</p>}</section><Link className="easy-all" href="/tools">Explore all your tools <LayoutGrid size={18}/></Link></div>;
}

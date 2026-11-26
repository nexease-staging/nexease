/* eslint-disable react-hooks/set-state-in-effect -- Hydrate the persisted browser preference after SSR. */
"use client";
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, ChevronRight, Search, Home, LayoutGrid, Package, Plus, Users } from 'lucide-react';
import { runQuick } from '@/features/mobile/quick-actions';
import { type NavigationSection, navigationSections, workforceSections } from '@/config/navigation';
import { useAuth } from '@/features/auth/auth-context';
import { hasPermission } from '@/lib/authorization/permissions';
import { getConfig } from '@/features/business/workspace';
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
  if(['/e-invoices','/e-way-bills'].includes(i.href)&&config.data?.modules?.einvoice!==true)return false;
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
const TAB_ROUTES:Record<string,string[]>={
 '/home':['/home','/dashboard'],
 '/parties':['/parties','/customers','/suppliers','/accounts-receivable','/accounts-payable','/customer-payments'],
 '/products':['/products','/inventory','/stock-movements','/stock-transfers','/warehouses','/barcode'],
 '/reports':['/reports','/profit-and-loss','/balance-sheet','/trial-balance','/cash-flow','/general-ledger'],
 '/tools':['/tools','/settings'],
};
/** Bottom-nav tab is active on its own screen and on the screens that belong to it. */
export function tabMatches(href:string,path:string){const p=path.replace(/\/$/,'')||'/';return (TAB_ROUTES[href]??[href]).some(r=>p===r||p.startsWith(r+'/'));}
/** Phone navigation: five tabs and an "Add sale" button on the home and parties screens. */
export function EasyNav(){
 const path=usePathname(); const features=useEasyFeatures().flatMap(s=>s.items); const {authentication}=useAuth();
 const permissions=authentication?.role.permissions??[];
 const allowed=(href:string)=>href==='/home'||href==='/tools'||(href==='/parties'?hasPermission(permissions,'customers.read')||hasPermission(permissions,'suppliers.read'):features.some(f=>f.href===href));
 const tabs=[{href:'/home',label:'Home',icon:Home},{href:'/parties',label:'Parties',icon:Users},{href:'/products',label:'Items',icon:Package},{href:'/reports',label:'Reports',icon:BarChart3},{href:'/tools',label:'Menu',icon:LayoutGrid}];
 const p=path.replace(/\/$/,'')||'/';
 const showSale=['/home','/parties'].includes(p)&&hasPermission(permissions,'invoices.create');
 return <>{showSale&&<button type="button" className="nxm-add-sale" onClick={()=>runQuick('sale')}><Plus size={20}/>Add sale</button>}<nav className="easy-nav" aria-label="Main navigation">{tabs.filter(t=>allowed(t.href)).map(t=><Link key={t.href} href={t.href} aria-current={tabMatches(t.href,path)?'page':undefined}><t.icon size={22}/><span>{t.label}</span></Link>)}</nav></>;
}
export function EasyTools(){
 const [search,setSearch]=useState(''); const [advanced,setAdvanced]=useState(false); const sections=useEasyFeatures();
 useEffect(()=>{setAdvanced(localStorage.getItem('nx.advanced')==='true');},[]);
 const change=(value:boolean)=>{setAdvanced(value);localStorage.setItem('nx.advanced',String(value));};
 const advancedSections=['Finance','Taxation','Administration'];
 return <div className="easy-page"><p className="easy-kicker">MENU</p><h1>What would you like to do?</h1><p className="easy-muted">Every tool, with a little less searching.</p><label className="easy-search"><Search size={20}/><input aria-label="Find a feature" placeholder="Try invoices, attendance, bank…" value={search} onChange={e=>setSearch(e.target.value)}/></label><div className="easy-preference"><div><strong>Advanced tools</strong><p>Accounting, taxes and administration</p></div><button type="button" role="switch" aria-checked={advanced} aria-label="Show advanced tools" className="easy-switch" onClick={()=>change(!advanced)}><span/></button></div>
 {sections.filter(s=>advanced||search||!advancedSections.includes(s.label)).map(s=>({...s,items:s.items.filter(i=>(i.label+' '+(names[i.label]||'')+' '+s.label).toLowerCase().includes(search.toLowerCase()))})).filter(s=>s.items.length).map(s=><section key={s.label} className="easy-section"><h2>{s.label==='Overview'?'Start here':s.label}</h2><div className="easy-tool-list">{s.items.map(i=><Link key={i.href} href={i.href}><span className="easy-tool-icon"><i.icon size={20}/></span><span>{names[i.label]||i.label}</span><ChevronRight size={17}/></Link>)}</div></section>)}
 {search&&!sections.some(s=>s.items.some(i=>(i.label+' '+(names[i.label]||'')+' '+s.label).toLowerCase().includes(search.toLowerCase())))&&<p role="status">No matching tools. Try a different word.</p>}
 <div className="mt-6"><ThemeToggle/></div><MobileConnection/></div>;
}

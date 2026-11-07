"use client";
import {useMemo,useState} from "react";
import Link from "next/link";
import {RefreshCw,ArrowUpRight} from "lucide-react";
import {useAuth} from "@/features/auth/auth-context";
import BusinessSetupCard from "./business-setup-card";
import {useMainDashboard} from "@/features/dashboard/hooks";
import DashboardOverview from "./dashboard-overview";
import DashboardKPIGrid from "./dashboard-kpi-grid";
import DashboardTrendCharts from "./dashboard-trend-charts";
import DashboardStatusCharts from "./dashboard-status-charts";
import DashboardTopEntities from "./dashboard-top-entities";
import DashboardAlertsActivity from "./dashboard-alerts-activity";
import DashboardLoadingSkeleton from "./dashboard-loading-skeleton";
const localDate=(date:Date)=>new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,10);
export default function DashboardShell(){
 const {authentication}=useAuth();
 const [startDate,setStartDate]=useState(()=>localDate(new Date(new Date().getFullYear(),0,1)));
 const [endDate,setEndDate]=useState(()=>localDate(new Date()));
 const [tab,setTab]=useState<"analytics"|"quick">("analytics");
 const parameters=useMemo(()=>({start_date:startDate,end_date:endDate}),[startDate,endDate]);
 const {data:dashboard,isLoading,isFetching,isError,error,refetch}=useMainDashboard(parameters);
 return <div className="nx-dashboard">
  <header className="nx-dashboard-title"><div><p>{authentication?.organization?.name??"NexEase"}</p><h1>Dashboard</h1></div><Link href="/subscription" className="text-xs text-emerald-700">Subscription & usage <ArrowUpRight size={13} className="inline"/></Link></header>
  <BusinessSetupCard/>
  <div className="nx-dashboard-tabs" role="group" aria-label="Dashboard view"><button type="button" aria-pressed={tab==="analytics"} onClick={()=>setTab("analytics")}>Analytics</button><button type="button" aria-pressed={tab==="quick"} onClick={()=>setTab("quick")}>Quick links</button></div>
  {tab==="quick"?<DashboardOverview data={dashboard} isLoading={isLoading}/>:<>
   <div className="nx-dashboard-toolbar"><div><span className="text-xs text-slate-500">Reporting period</span>{dashboard&&<p className="text-xs mt-1">{dashboard.period.start_date} → {dashboard.period.end_date} <span className="sr-only">Current view</span></p>}</div>
    <div className="flex flex-wrap items-end gap-2">
     <label>Start date<input type="date" required value={startDate} max={endDate} onChange={e=>{if(e.target.value)setStartDate(e.target.value)}} className="nx-input"/></label>
     <label>End date<input type="date" required value={endDate} min={startDate} onChange={e=>{if(e.target.value)setEndDate(e.target.value)}} className="nx-input"/></label>
     <button type="button" title="Refresh" aria-label="Refresh" disabled={isFetching} onClick={()=>void refetch()} className="nx-button"><RefreshCw size={16} className={isFetching?"animate-spin":""}/><span className="hidden sm:inline">Refresh</span></button>
    </div>
   </div>
   {isLoading&&<DashboardLoadingSkeleton/>}
   {isError&&<section role="alert" className="nx-panel border-red-200"><h2>Dashboard could not be loaded</h2><p className="mt-2 text-sm text-red-700">{error instanceof Error?error.message:"An unexpected error occurred."}</p></section>}
   {dashboard&&<div className="nx-dashboard-analytics space-y-5">
    <DashboardKPIGrid kpis={dashboard.kpis}/>
    <DashboardTrendCharts salesTrend={dashboard.sales_trend} purchaseTrend={dashboard.purchase_trend} cashFlow={dashboard.cash_flow}/>
    <DashboardStatusCharts receivableAging={dashboard.receivable_aging} invoiceStatus={dashboard.invoice_status} billStatus={dashboard.bill_status} inventoryStatus={dashboard.inventory_status}/>
    <DashboardTopEntities customers={dashboard.top_customers} suppliers={dashboard.top_suppliers}/>
    <DashboardAlertsActivity alerts={dashboard.alerts} recentActivity={dashboard.recent_activity}/>
   </div>}
  </>}
 </div>;
}

"use client";

import Link from "next/link";
import { useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Building2, CalendarCheck, ClipboardList, FileSpreadsheet, IndianRupee, Timer, Users, Wallet } from "lucide-react";
import StatCard from "@/components/ui/stat-card";
import { apiRequest } from "@/lib/api/client";
import { PopulateInputs } from "./operations-panels";
import BusinessWorkspace, { exportWorkbook, getConfig } from "./workspace";
import PayrollPanel from "./payroll-panel";
import { WorkforceBalances, DailyAttendance, LabourBilling } from "./automation-panel";
import { BulkAssignments, BooksTools } from "./pro-panels";
import LabourReport from "./labour-report";
import ApprovalsInbox from "./workforce-approvals";

const pages: Record<string, { title: string; kinds: string[]; description: string }> = {
  employees: { title: "Employees", kinds: ["employees"], description: "Your people, employment details and pay rates." },
  sites: { title: "Client sites", kinds: ["sites"], description: "The sites and customers your team serves." },
  assignments: { title: "Assignments", kinds: ["assignments"], description: "Who works where, on which shift, at what billing rate." },
  timesheets: { title: "Timesheets", kinds: ["timesheets"], description: "Review work and approve billable time." },
  leave: { title: "Leave & approvals", kinds: ["leave_requests"], description: "Approve or reject leave in one tap." },
  advances: { title: "Employee advances", kinds: ["advances"], description: "Advances paid, recovered and still outstanding." },
  inputs: { title: "Monthly pay inputs", kinds: ["attendance"], description: "Paid days, overtime, allowances, statutory wages and deductions." },
};

function Header({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <header className="nxl-header">
      <div className="min-w-0">
        <h1>{title}</h1>
        {children ? <p className="nx-muted">{children}</p> : null}
      </div>
    </header>
  );
}

export default function WorkforceHub({ section = "dashboard" }: { section?: string }) {
  const config = useQuery({ queryKey: ["business-config"], queryFn: getConfig });
  const overview = useQuery({ queryKey: ["workforce-overview"], queryFn: async () => (await apiRequest<Record<string, number>>("/business/workforce/overview/")).data, enabled: section === "dashboard" });
  const [error, setError] = useState("");

  if (pages[section]) {
    const page = pages[section];
    return (
      <div className="space-y-4">
        {section === "inputs" ? <PopulateInputs /> : null}
        {section === "assignments" ? <BulkAssignments /> : null}
        <BusinessWorkspace key={section} {...page} />
      </div>
    );
  }
  if (section === "attendance") return <div className="nxl-screen"><Header title="Daily attendance">Mark who worked today, site by site.</Header><DailyAttendance /></div>;
  if (section === "payruns" || section === "payslips") {
    return (
      <div className="nxl-screen">
        <Header title={section === "payslips" ? "Payslips & distribution" : "Pay runs"}>
          {section === "payslips" ? "Choose an approved month. Download individual PDFs, share a payslip, or download all slips as a ZIP." : "Calculate, review, approve and record salary payments."}
        </Header>
        <PayrollPanel />
      </div>
    );
  }
  if (section === "billing") return <div className="nxl-screen"><Header title="Client service billing">Turn approved timesheets into client invoices.</Header><div className="space-y-4"><LabourBilling /><LabourReport /></div></div>;
  if (section === "accounts") return <div className="nxl-screen"><Header title="Workforce accounts">Salary and advance balances, and books sync.</Header><div className="space-y-4"><WorkforceBalances /><BooksTools /></div></div>;
  if (section === "settings") {
    return (
      <div className="space-y-4">
        <BusinessWorkspace kinds={["policy", "workforce_preferences"]} title="Workforce settings" description="Effective-dated PF/ESI rates and caps, and attendance and recovery defaults." />
        <section className="nxl-panel p-4">
          <h2 className="text-base font-semibold">Where other settings live</h2>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {[["/workforce/employees", "Pay basis, overtime, PF/ESI membership and bank details"], ["/workforce/inputs", "Allowances, bonus, arrears, TDS, PT, LWF and recovery"], ["/workforce/assignments", "Shifts, assignment dates and billing rates"], ["/workforce/leave", "Leave approvals and paid/unpaid leave"], ["/settings/numbering", "Employee, site and invoice numbering"], ["/settings/roles", "Role permissions and approval access"], ["/workforce/accounts", "Accounting controls and reconciliation"], ["/settings/invoices", "Payslip company identity and invoice formats"]].map(([href, label]) => (
              <Link className="nxw-link" href={href} key={href}>{label}<ArrowRight size={15} aria-hidden="true" /></Link>
            ))}
          </div>
        </section>
      </div>
    );
  }
  if (section === "reports") {
    return (
      <div className="nxl-screen">
        <Header title="Workforce reports">Complete registers, including records beyond the on-screen 1,000-row limit. Exports follow your role permissions.</Header>
        {error ? <p role="alert" className="nxl-error">{error}</p> : null}
        <div className="grid gap-3 md:grid-cols-2">
          {Object.entries(config.data?.schemas ?? {}).filter(([, s]) => ["payroll", "labour"].includes(s.permission)).map(([k, s]) => (
            <section className="nxl-panel flex items-center justify-between gap-3 p-4" key={k}>
              <h2 className="flex items-center gap-2 text-sm font-semibold"><FileSpreadsheet size={16} aria-hidden="true" />{s.label}</h2>
              <div className="flex gap-1.5">
                {["xlsx", "csv", "pdf"].map((format) => (
                  <button className="nx-button nx-secondary nx-btn-sm" key={format} aria-label={`${s.label} ${format.toUpperCase()}`} onClick={() => exportWorkbook(`/business/workforce/reports/${k}/?format=${format}`, `${k}.${format}`).catch((e: Error) => setError(e.message))}>{format.toUpperCase()}</button>
                ))}
              </div>
            </section>
          ))}
        </div>
        <div className="mt-4"><LabourReport /></div>
        <Link className="nx-button mt-4 inline-flex" href="/workforce/payruns">Payroll and payment exports<ArrowRight size={16} aria-hidden="true" /></Link>
      </div>
    );
  }
  if (section !== "dashboard") return <p>Workforce page not found.</p>;

  const o = overview.data ?? {};
  const has = (k: string) => o[k] !== undefined;
  const cards = [
    has("employees") && { key: "employees", label: "Active employees", icon: Users, tone: "info" as const, href: "/workforce/employees", value: o.employees, hint: "On the payroll" },
    has("assignments") && { key: "assignments", label: "Deployed today", icon: Building2, tone: "success" as const, href: "/workforce/assignments", value: o.assignments, hint: `across ${o.sites ?? 0} active site${o.sites === 1 ? "" : "s"}` },
    has("pending_leave") && { key: "pending_leave", label: "Leave to approve", icon: CalendarCheck, tone: o.pending_leave ? "warning" as const : "success" as const, href: "/workforce/leave", value: o.pending_leave, hint: "Requested" },
    has("pending_timesheets") && { key: "pending_timesheets", label: "Timesheets to approve", icon: Timer, tone: o.pending_timesheets ? "warning" as const : "success" as const, href: "/workforce/timesheets", value: o.pending_timesheets, hint: "In draft" },
    has("draft_payruns") && { key: "draft_payruns", label: "Draft pay runs", icon: IndianRupee, tone: o.draft_payruns ? "violet" as const : "neutral" as const, href: "/workforce/payruns", value: o.draft_payruns, hint: "Waiting for approval" },
  ].filter(Boolean) as Array<{ key: string; label: string; icon: typeof Users; tone: "info" | "success" | "warning" | "violet" | "neutral"; href: string; value: number; hint: string }>;

  return (
    <div className="nxl-screen">
      <header className="nxl-header">
        <div className="min-w-0">
          <h1>Workforce</h1>
          <p className="nx-muted">People, sites, attendance, payroll and client billing.</p>
        </div>
        <div className="nxl-toolbar">
          <Link className="nx-button nx-secondary" href="/workforce/payruns"><Wallet size={16} aria-hidden="true" />Run payroll</Link>
          <Link className="nx-button" href="/workforce/attendance"><ClipboardList size={16} aria-hidden="true" />Mark attendance</Link>
        </div>
      </header>
      <div className="nxw-quick" role="toolbar" aria-label="Workforce quick actions">
        <Link className="nx-button" href="/workforce/attendance"><ClipboardList size={16} aria-hidden="true" />Mark attendance</Link>
        <Link className="nx-button nx-secondary" href="/workforce/payruns"><Wallet size={16} aria-hidden="true" />Run payroll</Link>
      </div>
      {overview.error ? <p role="alert" className="nxl-error">{overview.error.message}</p> : null}
      <div className="nx-kpi-strip nxw-kpis" data-cols={String(Math.min(cards.length || 4, 5))}>
        {overview.isLoading
          ? Array.from({ length: 4 }, (_, i) => <StatCard key={i} label="Loading" icon={Users} value="" loading />)
          : cards.map((c) => <StatCard key={c.key} label={c.label} icon={c.icon} tone={c.tone} href={c.href} value={String(c.value ?? 0)} hint={c.hint} />)}
      </div>
      <div className="nxw-grid">
        <ApprovalsInbox />
        <section className="nxl-panel p-4" aria-label="Monthly workflow">
          <h2 className="nxw-panel-title">Your monthly workflow</h2>
          <ol className="nxw-steps">
            {[["assignments", "Assign your team", "Workers to sites and shifts"], ["attendance", "Record daily work", "Attendance and timesheets"], ["payruns", "Approve payroll", "Calculate, approve, pay"], ["billing", "Bill your clients", "Invoices from approved time"]].map(([path, label, hint], i) => (
              <li key={path}>
                <Link href={`/workforce/${path}`}>
                  <span className="nxw-step-num">{i + 1}</span>
                  <span><strong>{label}</strong><span>{hint}</span></span>
                  <ArrowRight size={16} aria-hidden="true" />
                </Link>
              </li>
            ))}
          </ol>
        </section>
      </div>
      <div className="mt-4"><WorkforceBalances /></div>
    </div>
  );
}

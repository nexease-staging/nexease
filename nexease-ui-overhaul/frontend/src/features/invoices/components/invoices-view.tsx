"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, ChevronLeft, ChevronRight, CircleDollarSign, Eye, FilePlus2, FileText, RefreshCw, Search, TrendingUp, Zap } from "lucide-react";
import { InvoiceZip } from "@/features/business/operations-panels";
import { useAuth } from "@/features/auth/auth-context";
import { useCustomerList } from "@/features/customers/hooks";
import { useMainDashboard } from "@/features/dashboard/hooks";
import InvoiceDetailDialog from "@/features/invoices/components/invoice-detail-dialog";
import InvoiceDialog from "@/features/invoices/components/invoice-dialog";
import InvoicePaymentDialog from "@/features/invoices/components/invoice-payment-dialog";
import { useInvoiceList } from "@/features/invoices/hooks";
import type { InvoiceStatus, InvoiceSummary } from "@/features/invoices/types";
import { hasPermission } from "@/lib/authorization/permissions";
import { formatCompactMoney, formatDate, formatMoney, isInvoiceOverdue } from "@/lib/format";
import { InvoiceStatusBadge } from "@/components/ui/badge";
import EmptyState from "@/components/ui/empty-state";
import PageHeader from "@/components/ui/page-header";
import StatCard from "@/components/ui/stat-card";

const tabs: Array<{ value: InvoiceStatus | ""; label: string }> = [
  { value: "", label: "All" },
  { value: "DRAFT", label: "Draft" },
  { value: "ISSUED", label: "Issued" },
  { value: "PARTIALLY_PAID", label: "Partially paid" },
  { value: "PAID", label: "Paid" },
  { value: "CANCELLED", label: "Cancelled" },
];

type CreateMode = null | "standard" | "direct";

export default function InvoicesView() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "invoices.read");
  const canCreate = hasPermission(permissions, "invoices.create");
  const canPay = hasPermission(permissions, "invoices.record_payment");

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<InvoiceStatus | "">("");
  const [customerId, setCustomerId] = useState("");
  const [createMode, setCreateMode] = useState<CreateMode>(null);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [paying, setPaying] = useState<InvoiceSummary | null>(null);

  // Deep links from Quick Create / dashboard: /invoices?new=1 | ?new=direct | ?status=ISSUED
  useEffect(() => {
    const n = params.get("new");
    const s = params.get("status") as InvoiceStatus | null;
    if (!n && !s) return;
    if (n) setCreateMode(n === "direct" ? "direct" : "standard");
    if (s && tabs.some((t) => t.value === s)) { setStatus(s); setPage(1); }
    router.replace(pathname, { scroll: false });
  }, [params, pathname, router]);

  // Debounce typing so each keystroke does not hit the API.
  useEffect(() => {
    const t = setTimeout(() => { setSearch(searchInput.trim()); setPage(1); }, 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  const listParams = useMemo(() => ({
    page, page_size: 25, sort: "-created_at",
    search: search || undefined, status: status || undefined, customer_id: customerId || undefined,
  }), [page, search, status, customerId]);

  const query = useInvoiceList(listParams);
  const customers = useCustomerList({ page: 1, page_size: 100, is_active: true, sort: "name" }).data?.customers ?? [];
  const dash = useMainDashboard({}, canRead);
  const invoices = query.data?.invoices ?? [];
  const pagination = query.data?.pagination;
  const payable = (i: InvoiceSummary) => canPay && (i.status === "ISSUED" || i.status === "PARTIALLY_PAID") && Number(i.balance_due) > 0;

  if (!canRead) {
    return <div className="nx-card"><EmptyState icon={FileText} title="No access to invoices" description="Ask an administrator to grant the Invoices permission to your role." /></div>;
  }

  const createButtons = canCreate ? (
    <>
      <button type="button" className="nx-button nx-secondary nx-btn-sm" onClick={() => setCreateMode("direct")}><Zap size={16} aria-hidden="true" />Quick invoice</button>
      <button type="button" className="nx-button nx-btn-sm" onClick={() => setCreateMode("standard")}><FilePlus2 size={16} aria-hidden="true" />New invoice</button>
    </>
  ) : null;

  return (
    <div className="mx-auto max-w-[1400px] space-y-5">
      <PageHeader eyebrow="Sales" title="Invoices" description="Bill customers, track what is owed and record payments."
        actions={<div className="hidden items-center gap-2 md:flex">{createButtons}</div>} />

      <div className="grid gap-3 sm:grid-cols-3">
        <StatCard label="Receivables" icon={CircleDollarSign} tone="info" loading={dash.isPending}
          value={formatCompactMoney(dash.data?.kpis.receivables)} title={formatMoney(dash.data?.kpis.receivables)} hint="Owed to you" />
        <StatCard label="Overdue invoices" icon={AlertTriangle} tone={dash.data?.alerts.overdue_invoices ? "warning" : "success"} loading={dash.isPending}
          value={String(dash.data?.alerts.overdue_invoices ?? 0)} hint="Needs follow-up" />
        <StatCard label="Total sales" icon={TrendingUp} tone="success" loading={dash.isPending}
          value={formatCompactMoney(dash.data?.kpis.total_sales)} title={formatMoney(dash.data?.kpis.total_sales)} hint="This reporting period" />
      </div>

      <section className="nx-card overflow-hidden">
        <div className="space-y-3 border-b p-3 sm:p-4" style={{ borderColor: "var(--nx-border)" }}>
          <div className="flex flex-col gap-2 sm:flex-row">
            <div className="nx-search flex-1">
              <Search size={17} aria-hidden="true" />
              <input type="search" className="nx-input" aria-label="Search invoices" placeholder="Search by invoice number or customer…"
                value={searchInput} onChange={(e) => setSearchInput(e.target.value)} />
            </div>
            <select className="nx-input !mt-0 sm:w-56" aria-label="Filter by customer" value={customerId}
              onChange={(e) => { setCustomerId(e.target.value); setPage(1); }}>
              <option value="">All customers</option>
              {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <button type="button" className="nx-icon-btn hidden sm:grid" aria-label="Refresh" onClick={() => void query.refetch()}>
              <RefreshCw size={17} className={query.isFetching ? "animate-spin" : ""} aria-hidden="true" />
            </button>
          </div>
          <div className="nx-chip-row" role="group" aria-label="Filter by status">
            {tabs.map((t) => (
              <button key={t.value || "all"} type="button" className="nx-chip" aria-pressed={status === t.value}
                onClick={() => { setStatus(t.value); setPage(1); }}>{t.label}</button>
            ))}
          </div>
        </div>

        {query.isError ? (
          <div role="alert" className="p-6 text-sm" style={{ color: "var(--nx-danger-fg)" }}>
            {query.error instanceof Error ? query.error.message : "Could not load invoices."}
            <button type="button" className="nx-button nx-secondary nx-btn-sm ml-3" onClick={() => void query.refetch()}>Retry</button>
          </div>
        ) : query.isPending ? (
          <div className="space-y-3 p-4" aria-busy="true">{Array.from({ length: 6 }, (_, i) => <div key={i} className="nx-skeleton h-14" />)}</div>
        ) : invoices.length === 0 ? (
          <EmptyState icon={FileText} title={search || status || customerId ? "No invoices match these filters" : "No invoices yet"}
            description={search || status || customerId ? "Try a different search or clear the filters." : "Create your first invoice to start tracking sales."}
            action={canCreate && !(search || status || customerId) ? <button type="button" className="nx-button" onClick={() => setCreateMode("standard")}><FilePlus2 size={16} />New invoice</button> : null} />
        ) : (
          <>
            {/* Desktop / tablet: dense table */}
            <div className="nx-table-wrap hidden md:block">
              <table className="nx-table">
                <thead><tr>
                  <th>Invoice</th><th>Customer</th><th>Date</th><th>Due</th><th>Status</th>
                  <th className="nx-num">Total</th><th className="nx-num">Balance</th><th><span className="sr-only">Actions</span></th>
                </tr></thead>
                <tbody>
                  {invoices.map((i) => {
                    const overdue = isInvoiceOverdue(i);
                    return (
                      <tr key={i.id} className="cursor-pointer" onClick={() => setDetailId(i.id)}>
                        <td className="font-semibold">{i.invoice_number}</td>
                        <td className="max-w-[240px] truncate">{i.customer.name}</td>
                        <td className="whitespace-nowrap">{formatDate(i.invoice_date)}</td>
                        <td className="whitespace-nowrap" style={overdue ? { color: "var(--nx-danger-fg)", fontWeight: 600 } : undefined}>{formatDate(i.due_date)}</td>
                        <td><InvoiceStatusBadge status={i.status} overdue={overdue} /></td>
                        <td className="nx-num">{formatMoney(i.total_amount)}</td>
                        <td className="nx-num font-semibold">{formatMoney(i.balance_due)}</td>
                        <td onClick={(e) => e.stopPropagation()}>
                          <div className="flex justify-end gap-1.5">
                            {payable(i) ? <button type="button" className="nx-button nx-btn-sm" onClick={() => setPaying(i)}><CircleDollarSign size={15} aria-hidden="true" />Pay</button> : null}
                            <button type="button" className="nx-icon-btn !h-9 !w-9" aria-label={`View invoice ${i.invoice_number}`} onClick={() => setDetailId(i.id)}><Eye size={16} aria-hidden="true" /></button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Phones: card list */}
            <ul className="grid gap-3 p-3 md:hidden">
              {invoices.map((i) => {
                const overdue = isInvoiceOverdue(i);
                return (
                  <li key={i.id} className="nx-card p-4">
                    <button type="button" className="block w-full text-left" onClick={() => setDetailId(i.id)} aria-label={`Open invoice ${i.invoice_number}`}>
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0"><p className="font-bold">{i.invoice_number}</p><p className="nx-muted truncate text-sm">{i.customer.name}</p></div>
                        <InvoiceStatusBadge status={i.status} overdue={overdue} />
                      </div>
                      <div className="mt-3 flex items-end justify-between gap-2">
                        <div className="nx-muted text-xs">
                          <p>Issued {formatDate(i.invoice_date)}</p>
                          <p style={overdue ? { color: "var(--nx-danger-fg)", fontWeight: 600 } : undefined}>Due {formatDate(i.due_date)}</p>
                        </div>
                        <div className="text-right">
                          <p className="nx-muted text-xs">Total {formatMoney(i.total_amount)}</p>
                          <p className="text-lg font-bold tabular-nums">{formatMoney(i.balance_due)}</p>
                          <p className="nx-muted text-[11px]">balance due</p>
                        </div>
                      </div>
                    </button>
                    {payable(i) ? <button type="button" className="nx-button mt-3 w-full" onClick={() => setPaying(i)}><CircleDollarSign size={17} aria-hidden="true" />Record payment</button> : null}
                  </li>
                );
              })}
            </ul>

            {pagination ? (
              <footer className="flex items-center justify-between gap-3 border-t p-3 text-sm" style={{ borderColor: "var(--nx-border)" }}>
                <span className="nx-muted">Page {pagination.page} of {pagination.total_pages || 1} · {pagination.total_items} invoices</span>
                <span className="flex gap-2">
                  <button type="button" className="nx-icon-btn" aria-label="Previous page" disabled={!pagination.has_previous} onClick={() => setPage((p) => Math.max(1, p - 1))}><ChevronLeft size={18} /></button>
                  <button type="button" className="nx-icon-btn" aria-label="Next page" disabled={!pagination.has_next} onClick={() => setPage((p) => p + 1)}><ChevronRight size={18} /></button>
                </span>
              </footer>
            ) : null}
          </>
        )}
      </section>

      <InvoiceZip invoices={invoices} />

      {canCreate ? <div className="nx-sticky-bar md:hidden">{createButtons}</div> : null}

      <InvoiceDialog open={createMode !== null} initialMode={createMode === "direct" ? "direct" : undefined}
        onClose={() => setCreateMode(null)} onCreated={(id) => setDetailId(id)} />
      <InvoiceDetailDialog open={detailId !== null} invoiceId={detailId} onClose={() => setDetailId(null)}
        onRecordPayment={(inv) => { setDetailId(null); setPaying(inv); }} />
      <InvoicePaymentDialog open={paying !== null} invoice={paying} onClose={() => setPaying(null)} />
    </div>
  );
}

/* eslint-disable react-hooks/set-state-in-effect -- Consume route query commands once, then remove them from the URL. */
"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, CircleDollarSign, FileArchive, FileSpreadsheet, FileText, Plus, TrendingUp, Zap } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, StatusBadge, useDebounced } from "@/components/list/list-kit";
import { Badge } from "@/components/ui/badge";
import FilterSheet from "@/components/ui/filter-sheet";
import StatCard from "@/components/ui/stat-card";
import EmptyState from "@/components/ui/empty-state";
import { notify } from "@/components/nex-feedback";
import { InvoiceZip } from "@/features/business/operations-panels";
import { useAuth } from "@/features/auth/auth-context";
import { useCustomerList } from "@/features/customers/hooks";
import { useDocumentRowActions } from "@/features/documents/components/document-row-actions";
import { useInvoiceOverview } from "@/features/invoices/overview-hook";
import InvoiceDetailDialog from "@/features/invoices/components/invoice-detail-dialog";
import InvoiceDialog from "@/features/invoices/components/invoice-dialog";
import InvoicePaymentDialog from "@/features/invoices/components/invoice-payment-dialog";
import { useInvoiceList } from "@/features/invoices/hooks";
import type { InvoiceStatus, InvoiceSummary } from "@/features/invoices/types";
import { invoiceStatus, statusChips } from "@/features/sales/status";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatCompactMoney, formatDate, formatMoney, isInvoiceOverdue } from "@/lib/format";

const tabs = statusChips(invoiceStatus);

export default function InvoicesView() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "invoices.read");
  const canCreate = hasPermission(permissions, "invoices.create");
  const canPay = hasPermission(permissions, "invoices.record_payment");

  const [filtersOpen, setFiltersOpen] = useState(false);
  const [zipOpen, setZipOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [status, setStatus] = useState<InvoiceStatus | "">("");
  const [customerId, setCustomerId] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(() => (typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("view")));
  const [paying, setPaying] = useState<InvoiceSummary | null>(null);
  const docs = useDocumentRowActions();

  // Deep links from Quick Create / dashboard: /invoices?new=1 | ?new=direct | ?status=ISSUED
  useEffect(() => {
    const n = params.get("new");
    const s = params.get("status") as InvoiceStatus | null;
    if (!n && !s) return;
    if (n) setCreateOpen(true);
    if (s && tabs.some((t) => t.value === s)) {
      setStatus(s);
      setPage(1);
    }
    router.replace(pathname, { scroll: false });
  }, [params, pathname, router]);

  const listParams = useMemo(
    () => ({ page, page_size: 25, sort: "-created_at", search: search || undefined, status: status || undefined, customer_id: customerId || undefined }),
    [page, search, status, customerId],
  );
  const query = useInvoiceList(listParams);
  const customers = useCustomerList({ page: 1, page_size: 100, is_active: true, sort: "name" }).data?.customers ?? [];
  const dash = useInvoiceOverview(canRead && hasPermission(permissions, "accounting_reports.read"));
  const invoices = query.data?.invoices ?? [];
  const filtered = Boolean(search || status || customerId);
  const payable = (i: InvoiceSummary) => canPay && (i.status === "ISSUED" || i.status === "PARTIALLY_PAID") && Number(i.balance_due) > 0;

  if (!canRead) {
    return <div className="nx-card"><EmptyState icon={FileText} title="No access to invoices" description="Ask an administrator to grant the Invoices permission to your role." /></div>;
  }

  function exportCsv() {
    void downloadCsv(`NexEase-invoices-page-${page}`, invoices, [
      { header: "Invoice", value: (i) => i.invoice_number },
      { header: "Customer", value: (i) => i.customer.name },
      { header: "GSTIN", value: (i) => i.customer.gstin },
      { header: "Date", value: (i) => i.invoice_date?.slice(0, 10) },
      { header: "Due", value: (i) => i.due_date?.slice(0, 10) },
      { header: "Status", value: (i) => invoiceStatus[i.status]?.label ?? i.status },
      { header: "Taxable", value: (i) => i.subtotal },
      { header: "Tax", value: (i) => i.tax_amount },
      { header: "Total", value: (i) => i.total_amount },
      { header: "Paid", value: (i) => i.amount_paid },
      { header: "Balance", value: (i) => i.balance_due },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  return (
    <>
      <ListScreen
        title="Sales invoices"
        primary={canCreate ? { label: "New invoice", icon: Plus, onClick: () => setCreateOpen(true) } : null}
        actions={[
          { icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !invoices.length },
          { icon: FileArchive, label: "Download PDFs as ZIP", onClick: () => setZipOpen((v) => !v), disabled: !invoices.length },
        ]}
        onRefresh={() => void query.refetch()}
        refreshing={query.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search invoice no. or customer" }}
        onOpenFilters={() => setFiltersOpen(true)}
        filtersActive={Boolean(customerId)}
        chips={{ options: tabs, value: status, label: "Filter by status", onChange: (v) => { setStatus(v); setPage(1); } }}
        above={
          <>
            <div className="nx-kpi-strip">
              <StatCard label="To collect" icon={CircleDollarSign} tone="info" loading={dash.isLoading} value={formatCompactMoney(dash.data?.kpis?.receivables)} title={formatMoney(dash.data?.kpis?.receivables)} hint="Owed by customers" />
              <StatCard label="Overdue" icon={AlertTriangle} tone={dash.data?.alerts?.overdue_invoices ? "warning" : "success"} loading={dash.isLoading} value={String(dash.data?.alerts?.overdue_invoices ?? 0)} hint="Invoices past due" />
              <StatCard label="Sales" icon={TrendingUp} tone="success" loading={dash.isLoading} value={formatCompactMoney(dash.data?.kpis?.total_sales)} title={formatMoney(dash.data?.kpis?.total_sales)} hint="This reporting period" />
            </div>
            {zipOpen ? <InvoiceZip invoices={invoices} /> : null}
          </>
        }
        footer={<Pager pagination={query.data?.pagination} noun="invoices" onPage={setPage} />}
      >
        <ListState
          loading={query.isPending}
          error={query.error}
          onRetry={() => void query.refetch()}
          isEmpty={!invoices.length}
          emptyIcon={FileText}
          emptyTitle={filtered ? "No invoices match these filters" : "No invoices yet"}
          emptyDescription={filtered ? "Try a different search or clear the filters." : "Bill your first customer in under a minute."}
          emptyAction={canCreate && !filtered ? <button type="button" className="nx-button" onClick={() => setCreateOpen(true)}><Zap size={16} />New invoice</button> : null}
        >
          <CompactList label="Invoices" columns={[{ label: "Customer / invoice" }, { label: "Due" }, { label: "Total", align: "end" }, { label: "Balance" }]}>
            {invoices.map((i) => {
              const overdue = isInvoiceOverdue(i);
              const due = Number(i.balance_due) > 0 && i.status !== "DRAFT" && i.status !== "CANCELLED";
              return (
                <CompactRow
                  key={i.id}
                  openLabel={`View invoice ${i.invoice_number}`}
                  onOpen={() => setDetailId(i.id)}
                  title={i.customer.name}
                  subtitle={`${i.invoice_number} · ${formatDate(i.invoice_date)}`}
                  meta={[
                    <span key="due" style={overdue ? { color: "var(--nx-danger-fg)", fontWeight: 600 } : undefined}>{formatDate(i.due_date)}</span>,
                    <span key="total" className="block text-right tabular-nums">{formatMoney(i.total_amount)}</span>,
                  ]}
                  amount={formatMoney(due ? i.balance_due : i.total_amount)}
                  amountTone={overdue ? "danger" : i.status === "PAID" ? "success" : undefined}
                  amountHint={due && Number(i.amount_paid) > 0 ? `of ${formatMoney(i.total_amount)}` : undefined}
                  badge={overdue ? <Badge tone="warning" icon={AlertTriangle}>Overdue</Badge> : <StatusBadge status={i.status} map={invoiceStatus} />}
                  actions={[
                    ...(payable(i) ? [{ icon: CircleDollarSign, label: `Record payment for ${i.invoice_number}`, onClick: () => setPaying(i) }] : []),
                    ...docs.actionsFor(
                      { documentType: "INVOICE", documentId: i.id, documentNumber: i.invoice_number, recipient: i.customer.email },
                      { whatsapp: `Invoice ${i.invoice_number} for ${formatMoney(i.total_amount)}${due ? `, balance due ${formatMoney(i.balance_due)}` : ""}. Thank you for your business.` },
                    ),
                  ]}
                />
              );
            })}
          </CompactList>
        </ListState>
      </ListScreen>

      <FilterSheet open={filtersOpen} onClose={() => setFiltersOpen(false)}>
        <label className="block">Customer
          <select className="nx-input" value={customerId} onChange={(e) => { setCustomerId(e.target.value); setPage(1); }}>
            <option value="">All customers</option>
            {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </label>
        <button type="button" className="nx-button nx-secondary" onClick={() => { setCustomerId(""); setSearchInput(""); setStatus(""); setPage(1); }}>Clear filters</button>
      </FilterSheet>

      {docs.dialog}
      <InvoiceDialog open={createOpen} initialMode="direct" onClose={() => setCreateOpen(false)} onCreated={(id) => setDetailId(id)} />
      <InvoiceDetailDialog open={detailId !== null} invoiceId={detailId} onClose={() => setDetailId(null)} onRecordPayment={(inv) => { setDetailId(null); setPaying(inv); }} />
      <InvoicePaymentDialog open={paying !== null} invoice={paying} onClose={() => setPaying(null)} />
    </>
  );
}

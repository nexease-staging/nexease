"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Banknote, FileSpreadsheet, Plus, ReceiptText, Zap } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, StatusBadge, useDebounced } from "@/components/list/list-kit";
import { Badge } from "@/components/ui/badge";
import EmptyState from "@/components/ui/empty-state";
import FilterSheet from "@/components/ui/filter-sheet";
import SearchSelect from "@/components/search-select";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import QuickPurchase from "@/features/business/quick-purchase";
import { useDocumentRowActions } from "@/features/documents/components/document-row-actions";
import { isBillOverdue, vendorBillStatus } from "@/features/purchase/status";
import { statusChips } from "@/features/sales/status";
import { useSupplierList } from "@/features/suppliers/hooks";
import VendorBillDetailDialog from "@/features/vendor-bills/components/vendor-bill-detail-dialog";
import VendorBillDialog from "@/features/vendor-bills/components/vendor-bill-dialog";
import VendorBillPaymentDialog from "@/features/vendor-bills/components/vendor-bill-payment-dialog";
import { useVendorBill, useVendorBillList } from "@/features/vendor-bills/hooks";
import type { VendorBillStatus, VendorBillSummary } from "@/features/vendor-bills/types";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatDate, formatMoney } from "@/lib/format";

const tabs = statusChips(vendorBillStatus);
const sorts = [
  ["-created_at", "Newest first"],
  ["created_at", "Oldest first"],
  ["-bill_date", "Bill date (latest)"],
  ["due_date", "Due date (soonest)"],
  ["-balance_due", "Highest balance"],
  ["-total_amount", "Highest amount"],
  ["bill_number", "Bill number"],
] as const;

/** Loads the full bill, then opens the existing payment dialog. */
function PayBill({ billId, onClose }: { billId: string; onClose: () => void }) {
  const bill = useVendorBill(billId, true);
  const failed = bill.error;
  useEffect(() => {
    if (!failed) return;
    notify(failed instanceof Error ? failed.message : "Could not load the bill.", "error");
    onClose();
  }, [failed, onClose]);
  if (failed) return null;
  return <VendorBillPaymentDialog open={Boolean(bill.data)} vendorBill={bill.data ?? null} onClose={onClose} onRecorded={onClose} />;
}

export default function VendorBillsPage() {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "bills.read");
  const canCreate = hasPermission(permissions, "bills.create");
  const canPay = hasPermission(permissions, "bills.record_payment");

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [supplierId, setSupplierId] = useState("");
  const [status, setStatus] = useState<VendorBillStatus | "">("");
  const [sort, setSort] = useState<string>("-created_at");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [quickOpen, setQuickOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(() => (typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("view")));
  const [payingId, setPayingId] = useState<string | null>(null);
  const docs = useDocumentRowActions();

  const query = useVendorBillList({ page, page_size: 25, search: search || undefined, supplier_id: supplierId || undefined, status: status || undefined, sort });
  const bills = query.data?.vendor_bills ?? [];
  const suppliers = useSupplierList({ page: 1, page_size: 100, is_active: true, sort: "name" }).data?.suppliers ?? [];

  if (!authentication) return null;
  if (!canRead) {
    return <div className="nx-card"><EmptyState icon={ReceiptText} title="Purchase bills unavailable" description="You do not have permission to view supplier bills." /></div>;
  }
  const filtered = Boolean(search || status || supplierId);
  const payable = (b: VendorBillSummary) => canPay && (b.status === "POSTED" || b.status === "PARTIALLY_PAID") && Number(b.balance_due) > 0;

  function exportCsv() {
    void downloadCsv(`NexEase-purchase-bills-page-${page}`, bills, [
      { header: "Bill", value: (b) => b.bill_number },
      { header: "Supplier invoice no.", value: (b) => b.supplier_invoice_number },
      { header: "Supplier", value: (b) => b.supplier.name },
      { header: "Supplier GSTIN", value: (b) => b.supplier.gstin },
      { header: "PO", value: (b) => b.purchase_order?.po_number },
      { header: "Bill date", value: (b) => b.bill_date?.slice(0, 10) },
      { header: "Due", value: (b) => b.due_date?.slice(0, 10) },
      { header: "Status", value: (b) => vendorBillStatus[b.status]?.label ?? b.status },
      { header: "Taxable", value: (b) => b.subtotal },
      { header: "Tax", value: (b) => b.tax_amount },
      { header: "Total", value: (b) => b.total_amount },
      { header: "Paid", value: (b) => b.amount_paid },
      { header: "Balance", value: (b) => b.balance_due },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  return (
    <>
      <ListScreen
        title="Purchase bills"
        primary={canCreate ? { label: "New bill", icon: Plus, onClick: () => setCreateOpen(true) } : null}
        actions={[
          ...(canCreate ? [{ icon: Zap, label: "Quick purchase entry", onClick: () => setQuickOpen(true) }] : []),
          { icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !bills.length },
        ]}
        onRefresh={() => void query.refetch()}
        refreshing={query.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search bill no., supplier invoice or supplier" }}
        onOpenFilters={() => setFiltersOpen(true)}
        filtersActive={Boolean(supplierId) || sort !== "-created_at"}
        chips={{ options: tabs, value: status, label: "Filter by status", onChange: (v) => { setStatus(v); setPage(1); } }}
        footer={<Pager pagination={query.data?.pagination} noun="bills" onPage={setPage} />}
      >
        <ListState
          loading={query.isPending}
          error={query.error}
          onRetry={() => void query.refetch()}
          isEmpty={!bills.length}
          emptyIcon={ReceiptText}
          emptyTitle={filtered ? "No bills match these filters" : "No purchase bills yet"}
          emptyDescription={filtered ? "Try a different search or clear the filters." : "Record a supplier's invoice to track what you owe."}
          emptyAction={canCreate && !filtered ? <button type="button" className="nx-button" onClick={() => setCreateOpen(true)}><Plus size={16} />New bill</button> : null}
        >
          <CompactList label="Purchase bills" columns={[{ label: "Supplier / bill" }, { label: "Due" }, { label: "Total", align: "end" }, { label: "Balance" }]}>
            {bills.map((b) => {
              const overdue = isBillOverdue(b);
              const open = Number(b.balance_due) > 0 && b.status !== "DRAFT" && b.status !== "CANCELLED";
              return (
                <CompactRow
                  key={b.id}
                  openLabel={`View bill ${b.bill_number}`}
                  onOpen={() => setDetailId(b.id)}
                  title={b.supplier.name}
                  subtitle={`${b.bill_number}${b.supplier_invoice_number ? ` · Inv ${b.supplier_invoice_number}` : ""} · ${formatDate(b.bill_date)}`}
                  meta={[
                    <span key="due" style={overdue ? { color: "var(--nx-danger-fg)", fontWeight: 600 } : undefined}>{formatDate(b.due_date)}</span>,
                    <span key="total" className="block text-right tabular-nums">{formatMoney(b.total_amount)}</span>,
                  ]}
                  amount={formatMoney(open ? b.balance_due : b.total_amount)}
                  amountTone={overdue ? "danger" : b.status === "PAID" ? "success" : undefined}
                  amountHint={open && Number(b.amount_paid) > 0 ? `of ${formatMoney(b.total_amount)}` : undefined}
                  badge={overdue ? <Badge tone="warning" icon={AlertTriangle}>Overdue</Badge> : <StatusBadge status={b.status} map={vendorBillStatus} />}
                  actions={[
                    ...(payable(b) ? [{ icon: Banknote, label: `Pay bill ${b.bill_number}`, onClick: () => setPayingId(b.id) }] : []),
                    ...docs.actionsFor({ documentType: "VENDOR_BILL", documentId: b.id, documentNumber: b.bill_number, recipient: b.supplier.email }),
                  ]}
                />
              );
            })}
          </CompactList>
        </ListState>
      </ListScreen>

      <FilterSheet open={filtersOpen} onClose={() => setFiltersOpen(false)}>
        <label className="block">Supplier
          <SearchSelect className="nx-input" value={supplierId} onChange={(e) => { setSupplierId(e.target.value); setPage(1); }}>
            <option value="">All suppliers</option>
            {suppliers.map((s) => <option key={s.id} value={s.id}>{s.code} — {s.name}</option>)}
          </SearchSelect>
        </label>
        <label className="block">Sort by
          <select className="nx-input" value={sort} onChange={(e) => { setSort(e.target.value); setPage(1); }}>
            {sorts.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <button type="button" className="nx-button nx-secondary" onClick={() => { setSupplierId(""); setSort("-created_at"); setSearchInput(""); setStatus(""); setPage(1); }}>Clear filters</button>
      </FilterSheet>

      {docs.dialog}
      {canCreate ? <QuickPurchase kind="bill" open={quickOpen} onClose={() => setQuickOpen(false)} /> : null}
      {payingId ? <PayBill billId={payingId} onClose={() => { setPayingId(null); void query.refetch(); }} /> : null}
      <VendorBillDialog open={createOpen} onClose={() => setCreateOpen(false)} onCreated={(id) => { setCreateOpen(false); setDetailId(id); }} />
      <VendorBillDetailDialog open={detailId !== null} billId={detailId ?? ""} onClose={() => setDetailId(null)} />
    </>
  );
}

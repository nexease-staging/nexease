"use client";

import { useState } from "react";
import { ClipboardList, FileSpreadsheet, Plus, Zap } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, StatusBadge, useDebounced } from "@/components/list/list-kit";
import EmptyState from "@/components/ui/empty-state";
import FilterSheet from "@/components/ui/filter-sheet";
import SearchSelect from "@/components/search-select";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import QuickPurchase from "@/features/business/quick-purchase";
import { useDocumentRowActions } from "@/features/documents/components/document-row-actions";
import { purchaseOrderStatus } from "@/features/purchase/status";
import PurchaseOrderDetailDialog from "@/features/purchase-orders/components/purchase-order-detail-dialog";
import PurchaseOrderDialog from "@/features/purchase-orders/components/purchase-order-dialog";
import { usePurchaseOrderList } from "@/features/purchase-orders/hooks";
import type { PurchaseOrderStatus } from "@/features/purchase-orders/types";
import { statusChips } from "@/features/sales/status";
import { useSupplierList } from "@/features/suppliers/hooks";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatDate, formatMoney } from "@/lib/format";

const tabs = statusChips(purchaseOrderStatus);
const sorts = [
  ["-created_at", "Newest first"],
  ["created_at", "Oldest first"],
  ["-order_date", "Order date (latest)"],
  ["expected_delivery_date", "Delivery date (soonest)"],
  ["-total_amount", "Highest amount"],
  ["po_number", "PO number"],
] as const;

export default function PurchaseOrdersPage() {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "purchase_orders.read");
  const canCreate = hasPermission(permissions, "purchase_orders.create");

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [supplierId, setSupplierId] = useState("");
  const [status, setStatus] = useState<PurchaseOrderStatus | "">("");
  const [sort, setSort] = useState<string>("-created_at");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [quickOpen, setQuickOpen] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [detailId, setDetailId] = useState<string | null>(() => (typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("view")));
  const docs = useDocumentRowActions();

  const query = usePurchaseOrderList({ page, page_size: 25, supplier_id: supplierId || undefined, status: status || undefined, search: search || undefined, sort });
  const orders = query.data?.purchase_orders ?? [];
  const suppliers = useSupplierList({ page: 1, page_size: 100, is_active: true, sort: "name" }).data?.suppliers ?? [];

  if (!authentication) return null;
  if (!canRead) {
    return <div className="nx-card"><EmptyState icon={ClipboardList} title="Purchase orders unavailable" description="You do not have permission to view purchase orders." /></div>;
  }
  const filtered = Boolean(search || status || supplierId);
  const openCreate = () => { setEditingId(null); setFormOpen(true); };

  function exportCsv() {
    void downloadCsv(`NexEase-purchase-orders-page-${page}`, orders, [
      { header: "PO", value: (o) => o.po_number },
      { header: "Supplier", value: (o) => o.supplier.name },
      { header: "Supplier GSTIN", value: (o) => o.supplier.gstin },
      { header: "Order date", value: (o) => o.order_date?.slice(0, 10) },
      { header: "Expected delivery", value: (o) => o.expected_delivery_date?.slice(0, 10) },
      { header: "Status", value: (o) => purchaseOrderStatus[o.status]?.label ?? o.status },
      { header: "Items", value: (o) => o.item_count },
      { header: "Taxable", value: (o) => o.subtotal },
      { header: "Tax", value: (o) => o.tax_amount },
      { header: "Total", value: (o) => o.total_amount },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  return (
    <>
      <ListScreen
        title="Purchase orders"
        primary={canCreate ? { label: "New PO", icon: Plus, onClick: openCreate } : null}
        actions={[
          ...(canCreate ? [{ icon: Zap, label: "Quick purchase entry", onClick: () => setQuickOpen(true) }] : []),
          { icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !orders.length },
        ]}
        onRefresh={() => void query.refetch()}
        refreshing={query.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search PO no. or supplier" }}
        onOpenFilters={() => setFiltersOpen(true)}
        filtersActive={Boolean(supplierId) || sort !== "-created_at"}
        chips={{ options: tabs, value: status, label: "Filter by status", onChange: (v) => { setStatus(v); setPage(1); } }}
        footer={<Pager pagination={query.data?.pagination} noun="purchase orders" onPage={setPage} />}
      >
        <ListState
          loading={query.isPending}
          error={query.error}
          onRetry={() => void query.refetch()}
          isEmpty={!orders.length}
          emptyIcon={ClipboardList}
          emptyTitle={filtered ? "No purchase orders match these filters" : "No purchase orders yet"}
          emptyDescription={filtered ? "Try a different search or clear the filters." : "Order stock from a supplier, then receive it against the PO."}
          emptyAction={canCreate && !filtered ? <button type="button" className="nx-button" onClick={openCreate}><Plus size={16} />New PO</button> : null}
        >
          <CompactList label="Purchase orders" columns={[{ label: "Supplier / PO" }, { label: "Expected" }, { label: "Items" }, { label: "Total" }]}>
            {orders.map((o) => (
              <CompactRow
                key={o.id}
                openLabel={`View purchase order ${o.po_number}`}
                onOpen={() => setDetailId(o.id)}
                title={o.supplier.name}
                subtitle={`${o.po_number} · ${formatDate(o.order_date)}`}
                meta={[formatDate(o.expected_delivery_date), `${o.item_count} item${o.item_count === 1 ? "" : "s"}`]}
                amount={formatMoney(o.total_amount)}
                badge={<StatusBadge status={o.status} map={purchaseOrderStatus} />}
                actions={docs.actionsFor(
                  { documentType: "PURCHASE_ORDER", documentId: o.id, documentNumber: o.po_number, recipient: o.supplier.email },
                  { whatsapp: `Purchase order ${o.po_number} for ${formatMoney(o.total_amount)}${o.expected_delivery_date ? `, needed by ${formatDate(o.expected_delivery_date)}` : ""}.` },
                )}
              />
            ))}
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
      {canCreate ? <QuickPurchase kind="purchase_order" open={quickOpen} onClose={() => setQuickOpen(false)} /> : null}
      <PurchaseOrderDialog
        open={formOpen}
        purchaseOrderId={editingId}
        onClose={() => { setFormOpen(false); setEditingId(null); }}
        onSaved={(id) => { setFormOpen(false); setEditingId(null); setDetailId(id); }}
      />
      <PurchaseOrderDetailDialog
        open={detailId !== null}
        purchaseOrderId={detailId ?? ""}
        onClose={() => setDetailId(null)}
        onEdit={(po) => { setDetailId(null); setEditingId(po.id); setFormOpen(true); }}
      />
    </>
  );
}

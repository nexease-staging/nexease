"use client";

import { useMemo, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { FileSpreadsheet, Plus, ShoppingCart } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, StatusBadge, useDebounced } from "@/components/list/list-kit";
import EmptyState from "@/components/ui/empty-state";
import FilterSheet from "@/components/ui/filter-sheet";
import SearchSelect from "@/components/search-select";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import { useCustomerList } from "@/features/customers/hooks";
import { useDocumentRowActions } from "@/features/documents/components/document-row-actions";
import { salesOrderStatus, statusChips } from "@/features/sales/status";
import SalesOrderDetailDialog from "@/features/sales-orders/components/sales-order-detail-dialog";
import SalesOrderDialog from "@/features/sales-orders/components/sales-order-dialog";
import SalesOrderFulfillmentDialog from "@/features/sales-orders/components/sales-order-fulfillment-dialog";
import { useSalesOrderList } from "@/features/sales-orders/hooks";
import type { SalesOrderStatus } from "@/features/sales-orders/types";
import { useWarehouseList } from "@/features/warehouses/hooks";
import { apiRequest } from "@/lib/api/client";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatDate, formatMoney } from "@/lib/format";

const tabs = statusChips(salesOrderStatus);

function SalesOrdersPageContent() {
  const searchParams = useSearchParams();
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "sales_orders.read");
  const canCreate = hasPermission(permissions, "sales_orders.create");
  const canSeeProduction = hasPermission(permissions, "manufacturing.read");

  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [customerId, setCustomerId] = useState("");
  const [warehouseId, setWarehouseId] = useState("");
  const [status, setStatus] = useState<SalesOrderStatus | "">("");
  const [page, setPage] = useState(1);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [detailId, setDetailId] = useState<string | null>(() => (searchParams.get("view")));
  const [fulfillmentId, setFulfillmentId] = useState<string | null>(null);
  const docs = useDocumentRowActions();

  const listParameters = useMemo(
    () => ({ page, page_size: 25, search: search || undefined, customer_id: customerId || undefined, warehouse_id: warehouseId || undefined, status: status || undefined, sort: "-created_at" }),
    [customerId, page, search, status, warehouseId],
  );
  const query = useSalesOrderList(listParameters);
  const orders = query.data?.sales_orders ?? [];
  const salesIds = orders.map((x) => x.id).join(",");
  const production = useQuery({
    queryKey: ["manufacturing-sales-status", salesIds],
    enabled: !!salesIds && canSeeProduction,
    queryFn: async () => (await apiRequest<{ statuses: Record<string, string[]> }>("/business/manufacturing/?sales_ids=" + salesIds)).data.statuses,
  });
  const customers = useCustomerList({ page: 1, page_size: 100, is_active: true, sort: "name" }).data?.customers ?? [];
  const warehouses = useWarehouseList({ page: 1, page_size: 100, is_active: true, sort: "name" }).data?.warehouses ?? [];

  if (!authentication) return null;
  if (!canRead) {
    return <div className="nx-card"><EmptyState icon={ShoppingCart} title="Sales orders unavailable" description="You do not have permission to view sales orders." /></div>;
  }

  const filtered = Boolean(search || status || customerId || warehouseId);
  const openCreate = () => { setEditingId(null); setFormOpen(true); };

  function exportCsv() {
    void downloadCsv(`NexEase-sales-orders-page-${page}`, orders, [
      { header: "Order", value: (o) => o.so_number },
      { header: "Customer", value: (o) => o.customer.name },
      { header: "Warehouse", value: (o) => o.warehouse.name },
      { header: "Order date", value: (o) => o.order_date?.slice(0, 10) },
      { header: "Expected delivery", value: (o) => o.expected_delivery_date?.slice(0, 10) },
      { header: "Status", value: (o) => salesOrderStatus[o.status]?.label ?? o.status },
      { header: "Items", value: (o) => o.item_count },
      { header: "Total", value: (o) => o.total_amount },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  return (
    <>
      <ListScreen
        title="Sales orders"
        primary={canCreate ? { label: "New order", icon: Plus, onClick: openCreate } : null}
        actions={[{ icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !orders.length }]}
        onRefresh={() => void query.refetch()}
        refreshing={query.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search order no. or customer" }}
        onOpenFilters={() => setFiltersOpen(true)}
        filtersActive={Boolean(customerId || warehouseId)}
        chips={{ options: tabs, value: status, label: "Filter by status", onChange: (v) => { setStatus(v); setPage(1); } }}
        footer={<Pager pagination={query.data?.pagination} noun="orders" onPage={setPage} />}
      >
        <ListState
          loading={query.isPending}
          error={query.error}
          onRetry={() => void query.refetch()}
          isEmpty={!orders.length}
          emptyIcon={ShoppingCart}
          emptyTitle={filtered ? "No orders match these filters" : "No sales orders yet"}
          emptyDescription={filtered ? "Try a different search or clear the filters." : "Record a customer order, then deliver and invoice it."}
          emptyAction={canCreate && !filtered ? <button type="button" className="nx-button" onClick={openCreate}><Plus size={16} />New order</button> : null}
        >
          <CompactList label="Sales orders" columns={[{ label: "Customer / order" }, { label: "Warehouse" }, { label: "Delivery" }, { label: canSeeProduction ? "Production" : "Items" }, { label: "Total" }]}>
            {orders.map((o) => (
              <CompactRow
                key={o.id}
                openLabel={`View sales order ${o.so_number}`}
                onOpen={() => setDetailId(o.id)}
                title={o.customer.name}
                subtitle={`${o.so_number} · ${formatDate(o.order_date)}`}
                meta={[
                  o.warehouse.name,
                  formatDate(o.expected_delivery_date),
                  canSeeProduction
                    ? <Link key="mfg" className="relative z-[1] underline-offset-2 hover:underline" href={"/manufacturing?sales_order=" + o.id}>{production.data?.[o.id]?.join(" / ") || "Plan"}</Link>
                    : `${o.item_count} items`,
                ]}
                amount={formatMoney(o.total_amount)}
                badge={<StatusBadge status={o.status} map={salesOrderStatus} />}
                actions={docs.actionsFor(
                  { documentType: "SALES_ORDER", documentId: o.id, documentNumber: o.so_number, recipient: o.customer.email },
                  { whatsapp: `Order ${o.so_number} confirmed for ${formatMoney(o.total_amount)}.` },
                )}
              />
            ))}
          </CompactList>
        </ListState>
      </ListScreen>

      <FilterSheet open={filtersOpen} onClose={() => setFiltersOpen(false)}>
        <label className="block">Customer
          <SearchSelect className="nx-input" value={customerId} onChange={(e) => { setCustomerId(e.target.value); setPage(1); }}>
            <option value="">All customers</option>
            {customers.map((c) => <option key={c.id} value={c.id}>{c.code} — {c.name}</option>)}
          </SearchSelect>
        </label>
        <label className="block">Warehouse
          <SearchSelect className="nx-input" value={warehouseId} onChange={(e) => { setWarehouseId(e.target.value); setPage(1); }}>
            <option value="">All warehouses</option>
            {warehouses.map((w) => <option key={w.id} value={w.id}>{w.code} — {w.name}</option>)}
          </SearchSelect>
        </label>
        <button type="button" className="nx-button nx-secondary" onClick={() => { setCustomerId(""); setWarehouseId(""); setSearchInput(""); setStatus(""); setPage(1); }}>Clear filters</button>
      </FilterSheet>

      {docs.dialog}
      <SalesOrderDialog
        open={formOpen}
        salesOrderId={editingId}
        canCreateCustomer={hasPermission(permissions, "customers.create")}
        canCreateProduct={hasPermission(permissions, "products.create")}
        onClose={() => { setFormOpen(false); setEditingId(null); }}
      />
      <SalesOrderDetailDialog
        open={Boolean(detailId)}
        salesOrderId={detailId}
        onClose={() => setDetailId(null)}
        onEdit={(id) => { setDetailId(null); setEditingId(id); setFormOpen(true); }}
        onFulfill={(id) => { setDetailId(null); setFulfillmentId(id); }}
      />
      <SalesOrderFulfillmentDialog open={Boolean(fulfillmentId)} salesOrderId={fulfillmentId} onClose={() => setFulfillmentId(null)} />
    </>
  );
}

// useSearchParams needs a Suspense boundary for the static export used by the mobile build.
export default function SalesOrdersPage() {
  return (
    <Suspense fallback={null}>
      <SalesOrdersPageContent />
    </Suspense>
  );
}

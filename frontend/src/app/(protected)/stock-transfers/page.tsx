"use client";

import { useState } from "react";
import { ArrowRightLeft, Ban, CheckCircle2, CircleDashed, FileSpreadsheet, Plus } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, StatusBadge, useDebounced, type StatusStyle } from "@/components/list/list-kit";
import EmptyState from "@/components/ui/empty-state";
import FilterSheet from "@/components/ui/filter-sheet";
import SearchSelect from "@/components/search-select";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import StockTransferDialog from "@/features/inventory/components/stock-transfer-dialog";
import { useStockTransferList } from "@/features/inventory/hooks";
import type { StockTransferStatus } from "@/features/inventory/types";
import { statusChips } from "@/features/sales/status";
import { useWarehouseList } from "@/features/warehouses/hooks";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatDate } from "@/lib/format";

const transferStatus: Record<StockTransferStatus, StatusStyle> = {
  DRAFT: { label: "Draft", tone: "neutral", icon: CircleDashed },
  COMPLETED: { label: "Completed", tone: "success", icon: CheckCircle2 },
  CANCELLED: { label: "Cancelled", tone: "danger", icon: Ban },
};
const tabs = statusChips(transferStatus);

export default function StockTransfersPage() {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "inventory.read");
  const canTransfer = hasPermission(permissions, "inventory.transfer");

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [status, setStatus] = useState<StockTransferStatus | "">("");
  const [fromId, setFromId] = useState("");
  const [toId, setToId] = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);

  const query = useStockTransferList({ page, page_size: 25, search: search || undefined, status: status || undefined, source_warehouse_id: fromId || undefined, destination_warehouse_id: toId || undefined, sort: "-created_at" });
  const warehouses = useWarehouseList({ page: 1, page_size: 100, is_active: true, sort: "name" }).data?.warehouses ?? [];
  const transfers = query.data?.transfers ?? [];

  if (!authentication) return null;
  if (!canRead) return <div className="nx-card"><EmptyState icon={ArrowRightLeft} title="Stock transfers unavailable" description="Your role does not include the inventory.read permission." /></div>;
  const filtered = Boolean(search || status || fromId || toId);

  function exportCsv() {
    void downloadCsv(`NexEase-stock-transfers-page-${page}`, transfers, [
      { header: "Transfer", value: (t) => t.transfer_number },
      { header: "SKU", value: (t) => t.product.sku },
      { header: "Item", value: (t) => t.product.name },
      { header: "From", value: (t) => t.source_warehouse.name },
      { header: "To", value: (t) => t.destination_warehouse.name },
      { header: "Quantity", value: (t) => t.quantity },
      { header: "Status", value: (t) => transferStatus[t.status]?.label ?? t.status },
      { header: "Created", value: (t) => t.created_at?.slice(0, 10) },
      { header: "Completed", value: (t) => t.completed_at?.slice(0, 10) },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  const warehouseOptions = warehouses.map((w) => <option key={w.id} value={w.id}>{w.code} — {w.name}</option>);
  return (
    <>
      <ListScreen
        title="Stock transfers"
        primary={canTransfer ? { label: "New transfer", icon: Plus, onClick: () => setCreateOpen(true) } : null}
        actions={[{ icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !transfers.length }]}
        onRefresh={() => void query.refetch()}
        refreshing={query.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search transfer no., item or SKU" }}
        onOpenFilters={() => setFiltersOpen(true)}
        filtersActive={Boolean(fromId || toId)}
        chips={{ options: tabs, value: status, label: "Filter by status", onChange: (v) => { setStatus(v); setPage(1); } }}
        footer={<Pager pagination={query.data?.pagination} noun="transfers" onPage={setPage} />}
      >
        <ListState loading={query.isPending} error={query.error} onRetry={() => void query.refetch()} isEmpty={!transfers.length} emptyIcon={ArrowRightLeft}
          emptyTitle={filtered ? "No transfers match" : "No stock transfers yet"} emptyDescription={filtered ? "Try different filters." : "Move stock between warehouses or site stores."}
          emptyAction={canTransfer && !filtered ? <button type="button" className="nx-button" onClick={() => setCreateOpen(true)}><Plus size={16} />New transfer</button> : null}>
          <CompactList label="Stock transfers" columns={[{ label: "Item / transfer" }, { label: "From → to" }, { label: "Date" }, { label: "Quantity" }]}>
            {transfers.map((t) => (
              <CompactRow
                key={t.id}
                title={t.product.name}
                subtitle={`${t.transfer_number} · ${t.source_warehouse.name} → ${t.destination_warehouse.name}`}
                meta={[`${t.source_warehouse.code} → ${t.destination_warehouse.code}`, formatDate(t.completed_at ?? t.created_at)]}
                amount={`${Number(t.quantity).toLocaleString("en-IN", { maximumFractionDigits: 2 })} ${t.product.unit}`}
                badge={<StatusBadge status={t.status} map={transferStatus} />}
              />
            ))}
          </CompactList>
        </ListState>
      </ListScreen>

      <FilterSheet open={filtersOpen} onClose={() => setFiltersOpen(false)}>
        <label className="block">From warehouse
          <SearchSelect className="nx-input" value={fromId} onChange={(e) => { setFromId(e.target.value); setPage(1); }}><option value="">Any</option>{warehouseOptions}</SearchSelect>
        </label>
        <label className="block">To warehouse
          <SearchSelect className="nx-input" value={toId} onChange={(e) => { setToId(e.target.value); setPage(1); }}><option value="">Any</option>{warehouseOptions}</SearchSelect>
        </label>
        <button type="button" className="nx-button nx-secondary" onClick={() => { setFromId(""); setToId(""); setSearchInput(""); setStatus(""); setPage(1); }}>Clear filters</button>
      </FilterSheet>

      <StockTransferDialog open={createOpen} onClose={() => setCreateOpen(false)} />
    </>
  );
}

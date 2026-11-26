"use client";

import { useState } from "react";
import { ArrowDownUp, FileSpreadsheet, X } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, useDebounced } from "@/components/list/list-kit";
import { Badge, type Tone } from "@/components/ui/badge";
import EmptyState from "@/components/ui/empty-state";
import FilterSheet from "@/components/ui/filter-sheet";
import SearchSelect from "@/components/search-select";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import { useStockMovementList } from "@/features/inventory/hooks";
import { movementTypes } from "@/features/inventory/movement-types";
import type { StockMovementType } from "@/features/inventory/types";
import { useWarehouseList } from "@/features/warehouses/hooks";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatDate } from "@/lib/format";

const signed = (value: string, direction: number) => {
  const n = Math.abs(Number(value));
  const text = n.toLocaleString("en-IN", { maximumFractionDigits: 2 });
  return direction > 0 ? `+${text}` : direction < 0 ? `−${text}` : text;
};

export default function StockMovementsPage() {
  const { authentication } = useAuth();
  const canRead = hasPermission(authentication?.role.permissions ?? [], "inventory.read");
  const [productId, setProductId] = useState(() => (typeof window === "undefined" ? "" : new URLSearchParams(window.location.search).get("product_id") ?? ""));
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [warehouseId, setWarehouseId] = useState("");
  const [movementType, setMovementType] = useState<StockMovementType | "">("");
  const [page, setPage] = useState(1);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const query = useStockMovementList({ page, page_size: 25, product_id: productId || undefined, search: search || undefined, warehouse_id: warehouseId || undefined, movement_type: movementType || undefined, sort: "-created_at" });
  const warehouses = useWarehouseList({ page: 1, page_size: 100, is_active: true, sort: "name" }).data?.warehouses ?? [];
  const movements = query.data?.movements ?? [];

  if (!authentication) return null;
  if (!canRead) return <div className="nx-card"><EmptyState icon={ArrowDownUp} title="Stock movements unavailable" description="Your role does not include the inventory.read permission." /></div>;

  const productName = productId ? movements[0]?.product.name : "";
  const filtered = Boolean(search || warehouseId || movementType || productId);

  function exportCsv() {
    void downloadCsv(`NexEase-stock-movements-page-${page}`, movements, [
      { header: "Date", value: (m) => m.created_at?.slice(0, 16).replace("T", " ") },
      { header: "SKU", value: (m) => m.product.sku },
      { header: "Item", value: (m) => m.product.name },
      { header: "Warehouse", value: (m) => m.warehouse.name },
      { header: "Type", value: (m) => movementTypes[m.movement_type]?.label ?? m.movement_type },
      { header: "Quantity", value: (m) => signed(m.quantity, movementTypes[m.movement_type]?.direction ?? 0) },
      { header: "Before", value: (m) => m.quantity_before },
      { header: "After", value: (m) => m.quantity_after },
      { header: "Reference", value: (m) => [m.reference.type, m.reference.id].filter(Boolean).join(" ") },
      { header: "By", value: (m) => m.created_by?.email ?? "" },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  return (
    <>
      <ListScreen
        title="Stock movements"
        subtitle="Every change to stock, newest first."
        actions={[{ icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !movements.length }]}
        onRefresh={() => void query.refetch()}
        refreshing={query.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search item, SKU, reference or note" }}
        onOpenFilters={() => setFiltersOpen(true)}
        filtersActive={Boolean(warehouseId || movementType)}
        above={productId ? (
          <div className="flex items-center gap-2 text-sm">
            <Badge tone="info">History{productName ? `: ${productName}` : " for one item"}</Badge>
            <button type="button" className="nxl-icon" data-size="sm" aria-label="Show all items" title="Show all items" onClick={() => { setProductId(""); setPage(1); window.history.replaceState(null, "", "/stock-movements"); }}><X size={15} /></button>
          </div>
        ) : null}
        footer={<Pager pagination={query.data?.pagination} noun="movements" onPage={setPage} />}
      >
        <ListState loading={query.isPending} error={query.error} onRetry={() => void query.refetch()} isEmpty={!movements.length} emptyIcon={ArrowDownUp}
          emptyTitle={filtered ? "No movements match" : "No stock movements yet"} emptyDescription={filtered ? "Try different filters." : "Movements appear when stock is added, sold, adjusted or transferred."}>
          <CompactList label="Stock movements" columns={[{ label: "Item / when" }, { label: "Type" }, { label: "Before → after" }, { label: "Quantity" }]}>
            {movements.map((m) => {
              const t = movementTypes[m.movement_type] ?? { label: m.movement_type, tone: "neutral" as Tone, direction: 0 as const };
              return (
                <CompactRow
                  key={m.id}
                  title={m.product.name}
                  subtitle={`${m.warehouse.name} · ${formatDate(m.created_at)}${m.reference.type ? ` · ${m.reference.type.replaceAll("_", " ").toLowerCase()}` : ""}`}
                  meta={[<Badge key="t" tone={t.tone}>{t.label}</Badge>, `${Number(m.quantity_before).toLocaleString("en-IN")} → ${Number(m.quantity_after).toLocaleString("en-IN")}`]}
                  amount={`${signed(m.quantity, t.direction)} ${m.product.unit}`}
                  amountTone={t.direction > 0 ? "success" : t.direction < 0 ? "danger" : undefined}
                  amountHint={<span className="md:hidden">{t.label}</span>}
                />
              );
            })}
          </CompactList>
        </ListState>
      </ListScreen>

      <FilterSheet open={filtersOpen} onClose={() => setFiltersOpen(false)}>
        <label className="block">Warehouse
          <SearchSelect className="nx-input" value={warehouseId} onChange={(e) => { setWarehouseId(e.target.value); setPage(1); }}>
            <option value="">All warehouses</option>
            {warehouses.map((w) => <option key={w.id} value={w.id}>{w.code} — {w.name}</option>)}
          </SearchSelect>
        </label>
        <label className="block">Type
          <select className="nx-input" value={movementType} onChange={(e) => { setMovementType(e.target.value as StockMovementType | ""); setPage(1); }}>
            <option value="">All types</option>
            {(Object.keys(movementTypes) as StockMovementType[]).map((k) => <option key={k} value={k}>{movementTypes[k].label}</option>)}
          </select>
        </label>
        <button type="button" className="nx-button nx-secondary" onClick={() => { setWarehouseId(""); setMovementType(""); setSearchInput(""); setPage(1); }}>Clear filters</button>
      </FilterSheet>
    </>
  );
}

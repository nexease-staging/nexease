"use client";

import { useMemo, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, Archive, Boxes, CheckCircle2, Circle, FileSpreadsheet, History, IndianRupee, PackageX, Plus, ShoppingCart, SlidersHorizontal } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, useDebounced, type ListAction } from "@/components/list/list-kit";
import { Badge } from "@/components/ui/badge";
import EmptyState from "@/components/ui/empty-state";
import FilterSheet from "@/components/ui/filter-sheet";
import StatCard from "@/components/ui/stat-card";
import SearchSelect from "@/components/search-select";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import OpeningInventoryDialog from "@/features/inventory/components/opening-inventory-dialog";
import ReorderSheet from "@/features/inventory/components/reorder-sheet";
import StockAdjustmentDialog from "@/features/inventory/components/stock-adjustment-dialog";
import { useInventoryList } from "@/features/inventory/hooks";
import { useInventoryInsights, type LowStockItem } from "@/features/inventory/insights";
import type { InventorySummary } from "@/features/inventory/types";
import { useWarehouseList } from "@/features/warehouses/hooks";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatCompactMoney, formatDate, formatMoney } from "@/lib/format";

type View = "all" | "low" | "dead" | "warehouse";
const views: Array<{ value: View; label: string }> = [
  { value: "all", label: "All stock" },
  { value: "low", label: "Low stock" },
  { value: "dead", label: "Dead stock" },
  { value: "warehouse", label: "By warehouse" },
];
const qty = (v: string | number, unit = "") => `${Number(v).toLocaleString("en-IN", { maximumFractionDigits: 2 })}${unit ? ` ${unit}` : ""}`;

function InventoryPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "inventory.read");
  const canCreate = hasPermission(permissions, "inventory.create");
  const canAdjust = hasPermission(permissions, "inventory.adjust");
  const canOrder = hasPermission(permissions, "purchase_orders.create");

  const [view, setView] = useState<View>("all");
  const [warehouseId, setWarehouseId] = useState(() => (searchParams.get("warehouse_id") ?? ""));
  const [deadDays, setDeadDays] = useState(90);
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [openingOpen, setOpeningOpen] = useState(false);
  const [adjusting, setAdjusting] = useState<InventorySummary | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [reorderItems, setReorderItems] = useState<LowStockItem[] | null>(null);

  const stock = useInventoryList({ page, page_size: 25, warehouse_id: warehouseId || undefined, search: search || undefined, sort: "-updated_at" });
  const insights = useInventoryInsights(warehouseId, deadDays, canRead);
  const warehouses = useWarehouseList({ page: 1, page_size: 100, is_active: true, sort: "name" }).data?.warehouses ?? [];
  const lowIds = useMemo(() => new Set((insights.data?.low_stock ?? []).map((i) => i.product_id)), [insights.data]);

  if (!authentication) return null;
  if (!canRead) {
    return <div className="nx-card"><EmptyState icon={Boxes} title="Stock unavailable" description="Your role does not include the inventory.read permission." /></div>;
  }

  const rows = stock.data?.inventory ?? [];
  const low = insights.data?.low_stock ?? [];
  const dead = insights.data?.dead_stock ?? [];
  const byWarehouse = insights.data?.by_warehouse ?? [];
  const s = insights.data?.summary;
  const toggle = (id: string) => setSelected((prev) => { const next = new Set(prev); if (next.has(id)) next.delete(id); else next.add(id); return next; });
  const selectedItems = low.filter((i) => selected.has(i.product_id));
  const history = (productId: string) => router.push(`/stock-movements?product_id=${productId}`);

  function exportCsv() {
    const done = (p: Promise<void>) => p.catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
    if (view === "low") return done(downloadCsv("NexEase-low-stock", low, [
      { header: "SKU", value: (i) => i.sku }, { header: "Item", value: (i) => i.name }, { header: "Unit", value: (i) => i.unit },
      { header: "Available", value: (i) => i.available }, { header: "Reorder level", value: (i) => i.reorder_level }, { header: "Suggested order", value: (i) => i.suggested_quantity },
      { header: "Last supplier", value: (i) => i.supplier?.name }, { header: "Last rate", value: (i) => i.supplier?.last_rate },
    ]));
    if (view === "dead") return done(downloadCsv(`NexEase-dead-stock-${deadDays}d`, dead, [
      { header: "SKU", value: (i) => i.sku }, { header: "Item", value: (i) => i.name }, { header: "On hand", value: (i) => i.on_hand }, { header: "Unit", value: (i) => i.unit },
      { header: "Cost price", value: (i) => i.cost_price }, { header: "Value", value: (i) => i.value }, { header: "Last movement", value: (i) => i.last_movement?.slice(0, 10) ?? "Never" },
    ]));
    if (view === "warehouse") return done(downloadCsv("NexEase-stock-value-by-warehouse", byWarehouse, [
      { header: "Warehouse", value: (w) => w.name }, { header: "Code", value: (w) => w.code }, { header: "Units", value: (w) => w.units }, { header: "Value", value: (w) => w.value },
    ]));
    return done(downloadCsv(`NexEase-stock-page-${page}`, rows, [
      { header: "SKU", value: (r) => r.product.sku }, { header: "Item", value: (r) => r.product.name }, { header: "Warehouse", value: (r) => r.warehouse.name },
      { header: "On hand", value: (r) => r.quantity }, { header: "Reserved", value: (r) => r.reserved_quantity }, { header: "Available", value: (r) => r.available_quantity }, { header: "Unit", value: (r) => r.product.unit },
    ]));
  }

  const cards = (
    <div className="nx-kpi-strip" data-cols="4">
      <button type="button" className="text-left" onClick={() => setView("warehouse")} aria-label="Show stock value by warehouse">
        <StatCard label="Stock value" icon={IndianRupee} tone="info" loading={insights.isLoading} value={formatCompactMoney(s?.stock_value)} title={formatMoney(s?.stock_value)} hint={s?.unvalued_products ? `${s.unvalued_products} item${s.unvalued_products === 1 ? " has" : "s have"} no cost price` : "At cost price"} />
      </button>
      <button type="button" className="text-left" onClick={() => setView("low")} aria-label="Show low stock">
        <StatCard label="Low stock" icon={AlertTriangle} tone={s?.low_stock ? "warning" : "success"} loading={insights.isLoading} value={String(s?.low_stock ?? 0)} hint="At or below reorder level" />
      </button>
      <div><StatCard label="Out of stock" icon={PackageX} tone={s?.out_of_stock ? "danger" : "success"} loading={insights.isLoading} value={String(s?.out_of_stock ?? 0)} hint={`of ${s?.products ?? 0} goods`} /></div>
      <button type="button" className="text-left" onClick={() => setView("dead")} aria-label="Show dead stock">
        <StatCard label="Dead stock" icon={Archive} tone={s?.dead_stock ? "violet" : "success"} loading={insights.isLoading} value={formatCompactMoney(s?.dead_stock_value)} title={formatMoney(s?.dead_stock_value)} hint={`${s?.dead_stock ?? 0} item${s?.dead_stock === 1 ? "" : "s"} idle ${deadDays}+ days`} />
      </button>
    </div>
  );

  const selectionBar = view === "low" && low.length && canOrder ? (
    <div className="nxl-panel flex flex-wrap items-center justify-between gap-2 p-3 text-sm">
      <span>{selected.size ? `${selected.size} selected` : "Tap items to select them for reordering."}</span>
      <span className="flex gap-2">
        <button type="button" className="nx-button nx-secondary nx-btn-sm" onClick={() => setSelected(selected.size === low.length ? new Set() : new Set(low.map((i) => i.product_id)))}>{selected.size === low.length ? "Clear" : "Select all"}</button>
        <button type="button" className="nx-button nx-btn-sm" disabled={!selected.size} onClick={() => setReorderItems(selectedItems)}><ShoppingCart size={15} />Create draft PO</button>
      </span>
    </div>
  ) : null;

  const insightError = insights.error;
  let body;
  if (view === "low") {
    body = (
      <ListState loading={insights.isPending} error={insightError} onRetry={() => void insights.refetch()} isEmpty={!low.length} emptyIcon={CheckCircle2}
        emptyTitle="Nothing is running low" emptyDescription="Set reorder levels on products to get low-stock alerts and reorder suggestions here.">
        <CompactList label="Low stock" columns={[{ label: "Item" }, { label: "Reorder level" }, { label: "Last supplier" }, { label: "Available" }]}>
          {low.map((i) => {
            const isSelected = selected.has(i.product_id);
            const Mark = isSelected ? CheckCircle2 : Circle;
            return (
              <CompactRow
                key={i.product_id}
                openLabel={`${isSelected ? "Unselect" : "Select"} ${i.name}`}
                onOpen={canOrder ? () => toggle(i.product_id) : undefined}
                title={<span className="inline-flex items-center gap-2">{canOrder ? <Mark size={16} aria-hidden="true" style={{ color: isSelected ? "var(--nx-primary)" : "var(--nx-text-muted)" }} /> : null}{i.name}</span>}
                subtitle={`${i.sku} · order ${qty(i.suggested_quantity, i.unit)}${i.supplier ? ` from ${i.supplier.name}` : ""}`}
                meta={[qty(i.reorder_level, i.unit), i.supplier ? `${i.supplier.name} · ₹${i.supplier.last_rate}` : "—"]}
                amount={qty(i.available, i.unit)}
                amountTone={Number(i.available) <= 0 ? "danger" : undefined}
                badge={Number(i.available) <= 0 ? <Badge tone="danger">Out</Badge> : <Badge tone="warning">Low</Badge>}
                actions={[
                  ...(canOrder ? [{ icon: ShoppingCart, label: `Reorder ${i.name}`, onClick: () => setReorderItems([i]) }] : []),
                  { icon: History, label: `Stock history ${i.name}`, onClick: () => history(i.product_id) },
                ]}
              />
            );
          })}
        </CompactList>
      </ListState>
    );
  } else if (view === "dead") {
    body = (
      <ListState loading={insights.isPending} error={insightError} onRetry={() => void insights.refetch()} isEmpty={!dead.length} emptyIcon={CheckCircle2}
        emptyTitle="No dead stock" emptyDescription={`Every item with stock has moved in the last ${deadDays} days.`}>
        <CompactList label="Dead stock" columns={[{ label: "Item" }, { label: "On hand" }, { label: "Last moved" }, { label: "Value" }]}>
          {dead.map((i) => (
            <CompactRow
              key={i.product_id}
              openLabel={`Stock history ${i.name}`}
              onOpen={() => history(i.product_id)}
              title={i.name}
              subtitle={`${i.sku} · ${qty(i.on_hand, i.unit)} · ${i.last_movement ? `last moved ${formatDate(i.last_movement)}` : "never moved"}`}
              meta={[qty(i.on_hand, i.unit), i.last_movement ? formatDate(i.last_movement) : "Never"]}
              amount={formatMoney(i.value)}
              amountHint={Number(i.cost_price) ? `@ ₹${i.cost_price}` : "No cost price"}
            />
          ))}
        </CompactList>
      </ListState>
    );
  } else if (view === "warehouse") {
    body = (
      <ListState loading={insights.isPending} error={insightError} onRetry={() => void insights.refetch()} isEmpty={!byWarehouse.length} emptyIcon={Boxes} emptyTitle="No stock yet" emptyDescription="Add opening stock to see value by warehouse.">
        <CompactList label="Stock value by warehouse" columns={[{ label: "Warehouse" }, { label: "Units" }, { label: "Value" }]}>
          {byWarehouse.map((w) => (
            <CompactRow key={w.id} openLabel={`Show stock in ${w.name}`} onOpen={() => { setWarehouseId(w.id); setView("all"); setPage(1); }} title={w.name} subtitle={w.code} meta={[qty(w.units)]} amount={formatMoney(w.value)} />
          ))}
        </CompactList>
      </ListState>
    );
  } else {
    body = (
      <ListState loading={stock.isPending} error={stock.error} onRetry={() => void stock.refetch()} isEmpty={!rows.length} emptyIcon={Boxes}
        emptyTitle={search || warehouseId ? "No stock matches" : "No stock recorded yet"} emptyDescription={search || warehouseId ? "Try a different item or warehouse." : "Add opening stock for your items to start tracking."}
        emptyAction={canCreate && !search && !warehouseId ? <button type="button" className="nx-button" onClick={() => setOpeningOpen(true)}><Plus size={16} />Opening stock</button> : null}>
        <CompactList label="Stock" columns={[{ label: "Item / warehouse" }, { label: "On hand" }, { label: "Reserved" }, { label: "Available" }]}>
          {rows.map((r) => {
            const available = Number(r.available_quantity);
            const actions: ListAction[] = [
              ...(canAdjust ? [{ icon: SlidersHorizontal, label: `Adjust ${r.product.name} in ${r.warehouse.name}`, onClick: () => setAdjusting(r) }] : []),
              { icon: History, label: `Stock history ${r.product.name}`, onClick: () => history(r.product.id) },
            ];
            return (
              <CompactRow
                key={r.id}
                title={r.product.name}
                subtitle={`${r.product.sku} · ${r.warehouse.name}`}
                meta={[qty(r.quantity, r.product.unit), qty(r.reserved_quantity)]}
                amount={qty(r.available_quantity, r.product.unit)}
                amountTone={available <= 0 ? "danger" : undefined}
                badge={available <= 0 ? <Badge tone="danger">Out</Badge> : lowIds.has(r.product.id) ? <Badge tone="warning">Low</Badge> : undefined}
                actions={actions}
              />
            );
          })}
        </CompactList>
      </ListState>
    );
  }

  return (
    <>
      <ListScreen
        title="Stock"
        primary={canCreate ? { label: "Opening stock", icon: Plus, onClick: () => setOpeningOpen(true) } : null}
        actions={[{ icon: FileSpreadsheet, label: "Export this view to CSV", onClick: () => void exportCsv() }]}
        onRefresh={() => { void stock.refetch(); void insights.refetch(); }}
        refreshing={stock.isFetching || insights.isFetching}
        search={view === "all" ? { value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search item, SKU, barcode or warehouse" } : undefined}
        onOpenFilters={() => setFiltersOpen(true)}
        filtersActive={Boolean(warehouseId) || deadDays !== 90}
        chips={{ options: views, value: view, label: "Stock view", onChange: (v) => { setView(v); setSelected(new Set()); } }}
        above={<>{cards}{selectionBar}</>}
        footer={view === "all" ? <Pager pagination={stock.data?.pagination} noun="stock rows" onPage={setPage} /> : null}
      >
        {body}
      </ListScreen>

      <FilterSheet open={filtersOpen} onClose={() => setFiltersOpen(false)}>
        <label className="block">Warehouse
          <SearchSelect className="nx-input" value={warehouseId} onChange={(e) => { setWarehouseId(e.target.value); setPage(1); }}>
            <option value="">All warehouses</option>
            {warehouses.map((w) => <option key={w.id} value={w.id}>{w.code} — {w.name}</option>)}
          </SearchSelect>
        </label>
        <label className="block">Dead stock means no movement for
          <select className="nx-input" value={deadDays} onChange={(e) => setDeadDays(Number(e.target.value))}>
            {[30, 60, 90, 180, 365].map((d) => <option key={d} value={d}>{d} days</option>)}
          </select>
        </label>
        <button type="button" className="nx-button nx-secondary" onClick={() => { setWarehouseId(""); setDeadDays(90); setSearchInput(""); setPage(1); }}>Clear filters</button>
      </FilterSheet>

      <OpeningInventoryDialog open={openingOpen} onClose={() => setOpeningOpen(false)} />
      <StockAdjustmentDialog open={Boolean(adjusting)} inventory={adjusting} onClose={() => setAdjusting(null)} />
      {reorderItems ? <ReorderSheet items={reorderItems} onClose={() => setReorderItems(null)} onCreated={() => setSelected(new Set())} /> : null}
    </>
  );
}

// useSearchParams needs a Suspense boundary for the static export used by the mobile build.
export default function InventoryPage() {
  return (
    <Suspense fallback={null}>
      <InventoryPageContent />
    </Suspense>
  );
}

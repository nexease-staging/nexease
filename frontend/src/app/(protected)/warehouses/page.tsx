"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Boxes, FileSpreadsheet, Pencil, Plus, Power, PowerOff, Warehouse } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, useDebounced, type ListAction } from "@/components/list/list-kit";
import { Badge } from "@/components/ui/badge";
import EmptyState from "@/components/ui/empty-state";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import { useInventoryInsights } from "@/features/inventory/insights";
import WarehouseFormDialog from "@/features/warehouses/components/warehouse-form-dialog";
import WarehouseLifecycleDialog from "@/features/warehouses/components/warehouse-lifecycle-dialog";
import { useWarehouse, useWarehouseList } from "@/features/warehouses/hooks";
import type { WarehouseSummary } from "@/features/warehouses/types";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatMoney } from "@/lib/format";

type ActiveFilter = "" | "active" | "inactive";
const chips: Array<{ value: ActiveFilter; label: string }> = [
  { value: "", label: "All" },
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
];

export default function WarehousesPage() {
  const router = useRouter();
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "warehouses.read");
  const canCreate = hasPermission(permissions, "warehouses.create");
  const canUpdate = hasPermission(permissions, "warehouses.update");
  const canSeeStock = hasPermission(permissions, "inventory.read");

  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [active, setActive] = useState<ActiveFilter>("");
  const [page, setPage] = useState(1);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [lifecycle, setLifecycle] = useState<WarehouseSummary | null>(null);

  const query = useWarehouseList({ page, page_size: 25, search: search || undefined, is_active: active === "" ? undefined : active === "active", sort: "name" });
  const editing = useWarehouse(editingId ?? "", formOpen && Boolean(editingId));
  const insights = useInventoryInsights("", 90, canRead && canSeeStock);
  const values = useMemo(() => new Map((insights.data?.by_warehouse ?? []).map((w) => [w.id, w])), [insights.data]);
  const warehouses = query.data?.warehouses ?? [];

  if (!authentication) return null;
  if (!canRead) return <div className="nx-card"><EmptyState icon={Warehouse} title="Warehouses unavailable" description="Your role does not include the warehouses.read permission." /></div>;

  const openCreate = () => { setEditingId(null); setFormOpen(true); };
  const closeForm = () => { setFormOpen(false); setEditingId(null); };

  function rowActions(w: WarehouseSummary): ListAction[] {
    const actions: ListAction[] = [];
    if (canSeeStock) actions.push({ icon: Boxes, label: `Stock in ${w.name}`, onClick: () => router.push(`/inventory?warehouse_id=${w.id}`) });
    if (canUpdate && w.is_active) actions.push({ icon: Pencil, label: `Edit ${w.name}`, onClick: () => { setEditingId(w.id); setFormOpen(true); } });
    if (canUpdate) actions.push({ icon: w.is_active ? PowerOff : Power, label: `${w.is_active ? "Deactivate" : "Activate"} ${w.name}`, onClick: () => setLifecycle(w) });
    return actions;
  }

  function exportCsv() {
    void downloadCsv(`NexEase-warehouses-page-${page}`, warehouses, [
      { header: "Code", value: (w) => w.code },
      { header: "Name", value: (w) => w.name },
      { header: "City", value: (w) => w.city },
      { header: "State", value: (w) => w.state },
      { header: "Status", value: (w) => (w.is_active ? "Active" : "Inactive") },
      { header: "Stock units", value: (w) => values.get(w.id)?.units ?? "0" },
      { header: "Stock value", value: (w) => values.get(w.id)?.value ?? "0" },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  const filtered = Boolean(search || active);
  return (
    <>
      <ListScreen
        title="Warehouses"
        subtitle="Godowns, shops and site stores where you keep stock."
        primary={canCreate ? { label: "New warehouse", icon: Plus, onClick: openCreate } : null}
        actions={[{ icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !warehouses.length }]}
        onRefresh={() => { void query.refetch(); void insights.refetch(); }}
        refreshing={query.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search name, code or city" }}
        chips={{ options: chips, value: active, label: "Filter by status", onChange: (v) => { setActive(v); setPage(1); } }}
        footer={<Pager pagination={query.data?.pagination} noun="warehouses" onPage={setPage} />}
      >
        <ListState loading={query.isPending} error={query.error} onRetry={() => void query.refetch()} isEmpty={!warehouses.length} emptyIcon={Warehouse}
          emptyTitle={filtered ? "No warehouses match" : "No warehouses yet"} emptyDescription={filtered ? "Try a different search." : "Add where you store stock: a godown, shop or site store."}
          emptyAction={canCreate && !filtered ? <button type="button" className="nx-button" onClick={openCreate}><Plus size={16} />New warehouse</button> : null}>
          <CompactList label="Warehouses" columns={[{ label: "Warehouse" }, { label: "Location" }, { label: "Units" }, { label: "Stock value" }]}>
            {warehouses.map((w) => {
              const stock = values.get(w.id);
              return (
                <CompactRow
                  key={w.id}
                  openLabel={canUpdate && w.is_active ? `Open ${w.name}` : undefined}
                  onOpen={canUpdate && w.is_active ? () => { setEditingId(w.id); setFormOpen(true); } : undefined}
                  title={w.name}
                  subtitle={[w.code, w.city, w.state].filter(Boolean).join(" · ")}
                  meta={[[w.city, w.state].filter(Boolean).join(", ") || "—", stock ? Number(stock.units).toLocaleString("en-IN") : "0"]}
                  amount={canSeeStock ? formatMoney(stock?.value ?? "0") : undefined}
                  badge={w.is_active ? undefined : <Badge tone="neutral">Inactive</Badge>}
                  actions={rowActions(w)}
                />
              );
            })}
          </CompactList>
        </ListState>
      </ListScreen>

      <WarehouseFormDialog open={formOpen && (!editingId || Boolean(editing.data))} warehouse={editingId ? editing.data ?? null : null} onClose={closeForm} />
      <WarehouseLifecycleDialog open={Boolean(lifecycle)} warehouse={lifecycle} onClose={() => setLifecycle(null)} />
    </>
  );
}

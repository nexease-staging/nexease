"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import PhoneItems from "@/features/phone/items";
import { usePhone } from "@/features/phone/api";
import { useQuery } from "@tanstack/react-query";
import { BellRing, FileSpreadsheet, History, Package, Pencil, Plus, Power, PowerOff } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, useDebounced, type ListAction } from "@/components/list/list-kit";
import { Badge } from "@/components/ui/badge";
import EmptyState from "@/components/ui/empty-state";
import { confirmAction, notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import { useInventoryInsights } from "@/features/inventory/insights";
import ProductDialog from "@/features/products/components/product-dialog";
import ReorderLevel from "@/features/products/components/reorder-level";
import UnitSettings from "@/features/products/components/unit-settings";
import { useActivateProduct, useDeactivateProduct, useProductList } from "@/features/products/hooks";
import type { ProductSummary } from "@/features/products/types";
import { apiRequest } from "@/lib/api/client";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatMoney } from "@/lib/format";
import CategoriesPage from "../settings/categories/page";

type Section = "Products" | "Services" | "Categories" | "Units";
type ActiveFilter = "" | "active" | "inactive";
const sections: Section[] = ["Products", "Services", "Categories", "Units"];
const chips: Array<{ value: ActiveFilter; label: string }> = [
  { value: "", label: "All" },
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
];

export default function ProductsRoute() {
  return usePhone() ? <PhoneItems /> : <ProductsPage />;
}

function ProductsPage() {
  const router = useRouter();
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "products.read");
  const canCreate = hasPermission(permissions, "products.create");
  const canUpdate = hasPermission(permissions, "products.update");
  const canSeeStock = hasPermission(permissions, "inventory.read");

  const [section, setSection] = useState<Section>("Products");
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [active, setActive] = useState<ActiveFilter>("");
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [reorderId, setReorderId] = useState<string | null>(null);
  const activate = useActivateProduct();
  const deactivate = useDeactivateProduct();
  const goods = section !== "Services";

  const query = useProductList({ page, item_type: goods ? "goods" : "service", page_size: 25, search: search || undefined, is_active: active === "" ? undefined : active === "active", sort: "name" });
  const products = query.data?.products ?? [];
  const ids = products.map((p) => p.id).join(",");
  const stock = useQuery({
    queryKey: ["product-stock-balances", ids],
    enabled: canRead && canSeeStock && goods && !!ids,
    refetchInterval: 30_000,
    queryFn: async () => (await apiRequest<{ quantities: Record<string, string> }>(`/business/stock-balances/?product_ids=${encodeURIComponent(ids)}`)).data,
  });
  const insights = useInventoryInsights("", 90, canRead && canSeeStock && goods);
  const lowIds = useMemo(() => new Set((insights.data?.low_stock ?? []).map((i) => i.product_id)), [insights.data]);

  if (!authentication) return null;
  if (!canRead) return <div className="nx-card"><EmptyState icon={Package} title="Items unavailable" description="Your role does not include the products.read permission." /></div>;

  const tabs = (
    <div className="nxf-segment self-start" role="group" aria-label="Item classification">
      {sections.map((tab) => (
        <button key={tab} type="button" aria-pressed={tab === section} onClick={() => { setSection(tab); setPage(1); setSearchInput(""); }}>{tab}</button>
      ))}
    </div>
  );

  if (section === "Categories" || section === "Units") {
    return (
      <div className="nxl-screen">
        {tabs}
        {section === "Categories" ? <CategoriesPage /> : <UnitSettings canCreate={canCreate} expanded />}
      </div>
    );
  }

  const openCreate = () => { setEditingId(null); setDialogOpen(true); };
  const noun = goods ? "product" : "service";

  async function toggleActive(p: ProductSummary) {
    const on = !p.is_active;
    const ok = await confirmAction(on ? `Activate ${p.name}?\n\nIt becomes available for billing and stock again.` : `Deactivate ${p.name}?\n\nIt stays in past records but can't be billed.`);
    if (!ok) return;
    try {
      await (on ? activate : deactivate).mutateAsync(p.id);
      notify(`${p.name} ${on ? "activated" : "deactivated"}.`);
    } catch (e) {
      notify(e instanceof Error ? e.message : `Unable to ${on ? "activate" : "deactivate"} ${noun}.`, "error");
    }
  }

  function rowActions(p: ProductSummary): ListAction[] {
    const a: ListAction[] = [];
    if (goods && canUpdate && p.is_active) a.push({ icon: BellRing, label: `Reorder level for ${p.name}`, onClick: () => setReorderId(p.id) });
    if (goods && canSeeStock) a.push({ icon: History, label: `Stock history ${p.name}`, onClick: () => router.push(`/stock-movements?product_id=${p.id}`) });
    if (canUpdate && p.is_active) a.push({ icon: Pencil, label: `Edit ${p.name}`, onClick: () => { setEditingId(p.id); setDialogOpen(true); } });
    if (canUpdate) a.push({ icon: p.is_active ? PowerOff : Power, label: `${p.is_active ? "Deactivate" : "Activate"} ${p.name}`, disabled: activate.isPending || deactivate.isPending, onClick: () => void toggleActive(p) });
    return a;
  }

  function exportCsv() {
    void downloadCsv(`NexEase-${goods ? "products" : "services"}-page-${page}`, products, [
      { header: "SKU", value: (p) => p.sku },
      { header: "Name", value: (p) => p.name },
      { header: "Category", value: (p) => p.category?.name },
      { header: "HSN/SAC", value: (p) => p.hsn_code },
      { header: "Unit", value: (p) => p.unit },
      { header: "Cost price", value: (p) => p.cost_price },
      { header: "Selling price", value: (p) => p.selling_price },
      ...(goods ? [{ header: "In stock", value: (p: ProductSummary) => stock.data?.quantities[p.id] ?? "" }] : []),
      { header: "Barcode", value: (p) => p.barcode },
      { header: "Status", value: (p) => (p.is_active ? "Active" : "Inactive") },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  const filtered = Boolean(search || active);
  return (
    <>
      <ListScreen
        title={goods ? "Products" : "Services"}
        primary={canCreate ? { label: `New ${noun}`, icon: Plus, onClick: openCreate } : null}
        actions={[{ icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !products.length }]}
        onRefresh={() => void query.refetch()}
        refreshing={query.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: goods ? "Search name, SKU, brand or barcode" : "Search services", label: "Search products" }}
        chips={{ options: chips, value: active, label: "Filter by status", onChange: (v) => { setActive(v); setPage(1); } }}
        above={tabs}
        footer={<Pager pagination={query.data?.pagination} noun={goods ? "products" : "services"} onPage={setPage} />}
      >
        <ListState loading={query.isPending} error={query.error} onRetry={() => void query.refetch()} isEmpty={!products.length} emptyIcon={Package}
          emptyTitle={filtered ? `No ${noun}s match` : `No ${noun}s yet`} emptyDescription={filtered ? "Try a different search or filter." : goods ? "Add the items you buy and sell." : "Add the services you bill for."}
          emptyAction={canCreate && !filtered ? <button type="button" className="nx-button" onClick={openCreate}><Plus size={16} />New {noun}</button> : null}>
          <CompactList label={goods ? "Products" : "Services"} columns={[{ label: goods ? "Product" : "Service" }, { label: "Category" }, { label: goods ? "In stock" : "HSN/SAC" }, { label: "Selling price" }]}>
            {products.map((p) => {
              const inStock = stock.data?.quantities[p.id];
              const out = goods && inStock !== undefined && Number(inStock) <= 0;
              return (
                <CompactRow
                  key={p.id}
                  openLabel={canUpdate && p.is_active ? `Open ${p.name}` : undefined}
                  onOpen={canUpdate && p.is_active ? () => { setEditingId(p.id); setDialogOpen(true); } : undefined}
                  title={p.name}
                  subtitle={[p.sku, goods && inStock !== undefined ? `${Number(inStock).toLocaleString("en-IN", { maximumFractionDigits: 2 })} ${p.unit} in stock` : p.unit, p.hsn_code ? `HSN ${p.hsn_code}` : ""].filter(Boolean).join(" · ")}
                  meta={[p.category?.name ?? "—", goods ? (inStock !== undefined ? `${Number(inStock).toLocaleString("en-IN")} ${p.unit}` : "—") : (p.hsn_code || "—")]}
                  amount={formatMoney(p.selling_price)}
                  amountHint={Number(p.cost_price) ? `cost ${formatMoney(p.cost_price)}` : undefined}
                  badge={!p.is_active ? <Badge tone="neutral">Inactive</Badge> : out ? <Badge tone="danger">Out of stock</Badge> : lowIds.has(p.id) ? <Badge tone="warning">Low stock</Badge> : undefined}
                  actions={rowActions(p)}
                />
              );
            })}
          </CompactList>
        </ListState>
      </ListScreen>

      <ProductDialog defaultType={goods ? "goods" : "service"} open={dialogOpen} productId={editingId} onClose={() => { setDialogOpen(false); setEditingId(null); }} />
      {reorderId ? <ReorderLevel productId={reorderId} onClose={() => { setReorderId(null); void insights.refetch(); }} /> : null}
    </>
  );
}

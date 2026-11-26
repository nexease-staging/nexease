"use client";

import { useMemo, useState } from "react";
import { Pencil, Plus, Power, PowerOff, Tags } from "lucide-react";
import { confirmAction } from "@/components/nex-feedback";
import { CompactList, CompactRow, ListScreen, ListState, type ListAction } from "@/components/list/list-kit";
import { Badge } from "@/components/ui/badge";
import EmptyState from "@/components/ui/empty-state";
import { useAuth } from "@/features/auth/auth-context";
import CategoryDialog from "@/features/categories/components/category-dialog";
import { useActivateCategory, useCategories, useDeactivateCategory } from "@/features/categories/hooks";
import type { CategorySummary } from "@/features/categories/types";
import UnitSettings from "@/features/products/components/unit-settings";
import { hasPermission } from "@/lib/authorization/permissions";

type Filter = "active" | "inactive" | "all";
const filters: Array<{ value: Filter; label: string }> = [{ value: "active", label: "Active" }, { value: "inactive", label: "Inactive" }, { value: "all", label: "All" }];

export default function CategoriesPage() {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "products.read");
  const canCreate = hasPermission(permissions, "products.create");
  const canUpdate = hasPermission(permissions, "products.update");
  const [filter, setFilter] = useState<Filter>("active");
  const [search, setSearch] = useState("");
  const [dialog, setDialog] = useState<{ categoryId: string | null } | null>(null);
  const [error, setError] = useState("");
  const categories = useCategories();
  const activate = useActivateCategory();
  const deactivate = useDeactivateCategory();
  const rows = useMemo(() => {
    const term = search.trim().toLowerCase();
    return (categories.data?.categories ?? [])
      .filter((c) => filter === "all" || c.is_active === (filter === "active"))
      .filter((c) => !term || `${c.name} ${c.description ?? ""}`.toLowerCase().includes(term))
      .sort((a, b) => a.name.localeCompare(b.name, "en-IN"));
  }, [categories.data, filter, search]);

  if (!authentication) return null;
  if (!canRead) return <div className="nx-card"><EmptyState icon={Tags} title="Categories unavailable" description="Your role does not include the products.read permission." /></div>;

  async function toggle(c: CategorySummary) {
    const on = !c.is_active;
    if (!(await confirmAction(on ? `Turn on ${c.name}? It can be chosen for items again.` : `Turn off ${c.name}? Existing items keep it, but it can't be chosen for new items.`))) return;
    setError("");
    try {
      await (on ? activate : deactivate).mutateAsync(c.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not update the category.");
    }
  }

  return (
    <>
      <ListScreen<Filter>
        title="Categories & units"
        subtitle="Group your items and choose the units you sell them in."
        primary={canCreate ? { label: "New category", icon: Plus, onClick: () => setDialog({ categoryId: null }) } : null}
        onRefresh={() => void categories.refetch()}
        refreshing={categories.isFetching}
        search={{ value: search, onChange: setSearch, placeholder: "Search categories", label: "Search categories" }}
        chips={{ options: filters, value: filter, onChange: setFilter, label: "Category status" }}
        above={<div className="mb-4"><UnitSettings canCreate={canCreate} /></div>}
      >
        {error ? <p role="alert" className="nxl-error">{error}</p> : null}
        <ListState loading={categories.isPending} error={categories.error} onRetry={() => void categories.refetch()} isEmpty={!rows.length} emptyIcon={Tags}
          emptyTitle={search ? "No categories match" : "No categories here"}
          emptyAction={canCreate && !search ? <button type="button" className="nx-button" onClick={() => setDialog({ categoryId: null })}><Plus size={16} />New category</button> : null}>
          <CompactList label="Categories" columns={[{ label: "Category" }, { label: "Status" }]}>
            {rows.map((c) => {
              const actions: ListAction[] = canUpdate ? [
                { icon: Pencil, label: `Edit ${c.name}`, onClick: () => setDialog({ categoryId: c.id }) },
                { icon: c.is_active ? PowerOff : Power, label: `${c.is_active ? "Turn off" : "Turn on"} ${c.name}`, onClick: () => void toggle(c) },
              ] : [];
              return (
                <CompactRow key={c.id} title={c.name} subtitle={c.description || "No description"}
                  badge={c.is_active ? <Badge tone="success">Active</Badge> : <Badge tone="neutral">Off</Badge>}
                  actions={actions} onOpen={canUpdate ? () => setDialog({ categoryId: c.id }) : undefined} openLabel={`Edit ${c.name}`} />
              );
            })}
          </CompactList>
        </ListState>
      </ListScreen>
      <CategoryDialog open={Boolean(dialog)} categoryId={dialog?.categoryId ?? null} onClose={() => setDialog(null)} />
    </>
  );
}

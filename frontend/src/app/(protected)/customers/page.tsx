"use client";

import { useMemo, useState } from "react";
import { FileSpreadsheet, MessageCircle, Pencil, Phone, Plus, Power, PowerOff, Users } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, useDebounced, type ListAction } from "@/components/list/list-kit";
import { Badge } from "@/components/ui/badge";
import EmptyState from "@/components/ui/empty-state";
import { confirmAction, notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import CustomerDialog from "@/features/customers/components/customer-dialog";
import { useActivateCustomer, useCustomerList, useDeactivateCustomer } from "@/features/customers/hooks";
import type { CustomerSummary } from "@/features/customers/types";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { whatsappNumber } from "@/lib/phone";

type ActiveFilter = "" | "active" | "inactive";
const chips: Array<{ value: ActiveFilter; label: string }> = [
  { value: "", label: "All" },
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
];

export default function CustomersPage() {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, "customers.read");
  const canCreate = hasPermission(permissions, "customers.create");
  const canUpdate = hasPermission(permissions, "customers.update");

  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [activeFilter, setActiveFilter] = useState<ActiveFilter>("");
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const activateMutation = useActivateCustomer();
  const deactivateMutation = useDeactivateCustomer();
  const pending = activateMutation.isPending || deactivateMutation.isPending;

  const listParameters = useMemo(
    () => ({ page, page_size: 25, search: search || undefined, is_active: activeFilter === "" ? undefined : activeFilter === "active", sort: "name" }),
    [activeFilter, page, search],
  );
  const query = useCustomerList(listParameters);
  const customers = query.data?.customers ?? [];

  if (!authentication) return null;
  if (!canRead) {
    return <div className="nx-card"><EmptyState icon={Users} title="Customer access restricted" description="Your role does not include the customers.read permission." /></div>;
  }

  const openCreate = () => { setEditingId(null); setDialogOpen(true); };
  const openEdit = (id: string) => { setEditingId(id); setDialogOpen(true); };

  async function toggleActive(customer: CustomerSummary) {
    const activating = !customer.is_active;
    const message = activating ? `Activate ${customer.name}?` : `Deactivate ${customer.name}?\n\nThe customer remains available in historical records.`;
    if (!(await confirmAction(message))) return;
    try {
      await (activating ? activateMutation : deactivateMutation).mutateAsync(customer.id);
      notify(`${customer.name} ${activating ? "activated" : "deactivated"}.`);
    } catch (error) {
      notify(error instanceof Error ? error.message : `Unable to ${activating ? "activate" : "deactivate"} customer.`, "error");
    }
  }

  function rowActions(c: CustomerSummary): ListAction[] {
    const actions: ListAction[] = [];
    const phone = c.phone?.trim();
    const wa = whatsappNumber(phone);
    if (phone) actions.push({ icon: Phone, label: `Call ${c.name}`, onClick: () => { window.location.href = `tel:${phone.replace(/[^\d+]/g, "")}`; } });
    if (wa) actions.push({ icon: MessageCircle, label: `WhatsApp ${c.name}`, onClick: () => window.open(`https://wa.me/${wa}`, "_blank", "noopener,noreferrer") });
    if (canUpdate && c.is_active) actions.push({ icon: Pencil, label: `Edit ${c.name}`, disabled: pending, onClick: () => openEdit(c.id) });
    if (canUpdate) actions.push({ icon: c.is_active ? PowerOff : Power, label: `${c.is_active ? "Deactivate" : "Activate"} ${c.name}`, disabled: pending, onClick: () => void toggleActive(c) });
    return actions;
  }

  function exportCsv() {
    void downloadCsv(`NexEase-customers-page-${page}`, customers, [
      { header: "Code", value: (c) => c.code },
      { header: "Name", value: (c) => c.name },
      { header: "Phone", value: (c) => c.phone },
      { header: "Email", value: (c) => c.email },
      { header: "GSTIN", value: (c) => c.gstin },
      { header: "City", value: (c) => c.city },
      { header: "State", value: (c) => c.state },
      { header: "Status", value: (c) => (c.is_active ? "Active" : "Inactive") },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  const filtered = Boolean(search || activeFilter);
  return (
    <>
      <ListScreen
        title="Customers"
        primary={canCreate ? { label: "New customer", icon: Plus, onClick: openCreate } : null}
        actions={[{ icon: FileSpreadsheet, label: "Export this page to CSV", onClick: exportCsv, disabled: !customers.length }]}
        onRefresh={() => void query.refetch()}
        refreshing={query.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search name, phone or GSTIN", label: "Search customers" }}
        chips={{ options: chips, value: activeFilter, label: "Filter by status", onChange: (v) => { setActiveFilter(v); setPage(1); } }}
        footer={<Pager pagination={query.data?.pagination} noun="customers" onPage={setPage} />}
      >
        <ListState
          loading={query.isPending}
          error={query.error}
          onRetry={() => void query.refetch()}
          isEmpty={!customers.length}
          emptyIcon={Users}
          emptyTitle={filtered ? "No customers match" : "No customers yet"}
          emptyDescription={filtered ? "Try a different search or filter." : "Add a customer by name, or fetch details from a GSTIN."}
          emptyAction={canCreate && !filtered ? <button type="button" className="nx-button" onClick={openCreate}><Plus size={16} />New customer</button> : null}
        >
          <CompactList label="Customers" columns={[{ label: "Customer" }, { label: "Phone" }, { label: "GSTIN" }, { label: "Location" }]}>
            {customers.map((c) => (
              <CompactRow
                key={c.id}
                openLabel={canUpdate && c.is_active ? `Open ${c.name}` : undefined}
                onOpen={canUpdate && c.is_active ? () => openEdit(c.id) : undefined}
                title={c.name}
                subtitle={[c.code, c.phone, c.gstin].filter(Boolean).join(" · ")}
                meta={[c.phone ?? "—", c.gstin ?? "—"]}
                amount={<span className="nxl-hide-sm text-[13px] font-medium">{[c.city, c.state].filter(Boolean).join(", ") || c.country || "—"}</span>}
                badge={c.is_active ? undefined : <Badge tone="neutral">Inactive</Badge>}
                actions={rowActions(c)}
              />
            ))}
          </CompactList>
        </ListState>
      </ListScreen>
      <CustomerDialog open={dialogOpen} customerId={editingId} onClose={() => { setDialogOpen(false); setEditingId(null); }} />
    </>
  );
}

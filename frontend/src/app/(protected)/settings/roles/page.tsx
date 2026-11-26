"use client";

import { useState } from "react";
import { KeyRound, Lock, Pencil, Plus, Power, PowerOff, UserCog } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, useDebounced, type ListAction } from "@/components/list/list-kit";
import { Badge } from "@/components/ui/badge";
import EmptyState from "@/components/ui/empty-state";
import { useAuth } from "@/features/auth/auth-context";
import { RoleDialog } from "@/features/roles/components/role-dialog";
import { RolePermissionsDialog } from "@/features/roles/components/role-permissions-dialog";
import { RoleStatusDialog } from "@/features/roles/components/role-status-dialog";
import { useRoleList } from "@/features/roles/hooks";
import type { RoleSummary } from "@/features/roles/types";
import { hasPermission } from "@/lib/authorization/permissions";

type Filter = "active" | "inactive" | "all";
const filters: Array<{ value: Filter; label: string }> = [{ value: "active", label: "Active" }, { value: "inactive", label: "Inactive" }, { value: "all", label: "All" }];

export default function RolesPage() {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const can = (code: string) => hasPermission(permissions, code);
  const [filter, setFilter] = useState<Filter>("active");
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<RoleSummary | null>(null);
  const [permissionRole, setPermissionRole] = useState<RoleSummary | null>(null);
  const [status, setStatus] = useState<{ role: RoleSummary; action: "activate" | "deactivate" } | null>(null);
  const canRead = can("roles.read");
  const roles = useRoleList({ page, page_size: 25, search: search || undefined, is_active: filter === "all" ? undefined : filter === "active", sort: "name" }, canRead);

  if (!authentication) return null;
  if (!canRead) return <div className="nx-card"><EmptyState icon={UserCog} title="Roles unavailable" description="Your role does not include the roles.read permission." /></div>;
  const rows = roles.data?.roles ?? [];

  return (
    <>
      <ListScreen<Filter>
        title="Roles"
        subtitle="A role is a set of permissions. Give each user the smallest role they need."
        primary={can("roles.create") ? { label: "New role", icon: Plus, onClick: () => setCreating(true) } : null}
        onRefresh={() => void roles.refetch()}
        refreshing={roles.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search roles", label: "Search roles" }}
        chips={{ options: filters, value: filter, onChange: (v) => { setFilter(v); setPage(1); }, label: "Role status" }}
        footer={<Pager pagination={roles.data?.pagination} noun="roles" onPage={setPage} />}
      >
        <ListState loading={roles.isPending} error={roles.error} onRetry={() => void roles.refetch()} isEmpty={!rows.length} emptyIcon={UserCog} emptyTitle={search ? "No roles match" : "No roles here"}>
          <CompactList label="Roles" columns={[{ label: "Role" }, { label: "Type" }, { label: "Permissions" }]}>
            {rows.map((r) => {
              const custom = !r.is_system;
              const actions: ListAction[] = [
                ...(custom && can("roles.assign_permissions") ? [{ icon: KeyRound, label: `Permissions for ${r.name}`, onClick: () => setPermissionRole(r) }] : []),
                ...(custom && can("roles.update") ? [{ icon: Pencil, label: `Edit ${r.name}`, onClick: () => setEditing(r) }] : []),
                ...(custom && (r.is_active ? can("roles.deactivate") : can("roles.activate"))
                  ? [{ icon: r.is_active ? PowerOff : Power, label: `${r.is_active ? "Turn off" : "Turn on"} ${r.name}`, onClick: () => setStatus({ role: r, action: r.is_active ? "deactivate" : "activate" }) }]
                  : []),
              ];
              return (
                <CompactRow
                  key={r.id}
                  title={<span className="inline-flex items-center gap-2">{r.is_system ? <Lock size={14} aria-label="Built-in role" /> : null}{r.name}</span>}
                  subtitle={r.description || (r.is_system ? "Built-in role. It cannot be changed; create a custom role instead." : "Custom role")}
                  meta={[r.is_system ? "Built-in" : "Custom"]}
                  amount={`${r.permission_count} permission${r.permission_count === 1 ? "" : "s"}`}
                  badge={r.is_active ? <Badge tone="success">Active</Badge> : <Badge tone="neutral">Off</Badge>}
                  actions={actions}
                  onOpen={custom && can("roles.assign_permissions") ? () => setPermissionRole(r) : undefined}
                  openLabel={`Permissions for ${r.name}`}
                />
              );
            })}
          </CompactList>
        </ListState>
      </ListScreen>
      <RoleDialog open={creating || Boolean(editing)} role={editing} onClose={() => { setCreating(false); setEditing(null); }} />
      <RolePermissionsDialog open={Boolean(permissionRole)} role={permissionRole} onClose={() => setPermissionRole(null)} />
      <RoleStatusDialog open={Boolean(status)} role={status?.role ?? null} action={status?.action ?? "deactivate"} onClose={() => setStatus(null)} />
    </>
  );
}

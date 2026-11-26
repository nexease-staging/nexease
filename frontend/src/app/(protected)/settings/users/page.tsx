"use client";

import { useState } from "react";
import { Pencil, Power, PowerOff, UserPlus, Users } from "lucide-react";
import { confirmAction } from "@/components/nex-feedback";
import { CompactList, CompactRow, ListScreen, ListState, Pager, useDebounced, type ListAction } from "@/components/list/list-kit";
import { Badge } from "@/components/ui/badge";
import EmptyState from "@/components/ui/empty-state";
import { useAuth } from "@/features/auth/auth-context";
import UserDialog from "@/features/users/components/user-dialog";
import { useActivateUser, useDeactivateUser, useUserList } from "@/features/users/hooks";
import type { UserSummary } from "@/features/users/types";
import { hasPermission } from "@/lib/authorization/permissions";

type Filter = "active" | "inactive" | "all";
const filters: Array<{ value: Filter; label: string }> = [{ value: "active", label: "Active" }, { value: "inactive", label: "Inactive" }, { value: "all", label: "All" }];
const initials = (u: UserSummary) => ((u.first_name?.[0] ?? "") + (u.last_name?.[0] ?? "") || u.email[0]).toUpperCase();

export default function UsersPage() {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const can = (code: string) => hasPermission(permissions, code);
  const [filter, setFilter] = useState<Filter>("active");
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [dialog, setDialog] = useState<{ userId: string | null } | null>(null);
  const [error, setError] = useState("");
  const users = useUserList({ page, page_size: 25, search: search || undefined, is_active: filter === "all" ? undefined : filter === "active", sort: "email" });
  const activate = useActivateUser();
  const deactivate = useDeactivateUser();

  if (!authentication) return null;
  if (!can("users.read")) return <div className="nx-card"><EmptyState icon={Users} title="Users unavailable" description="Your role does not include the users.read permission." /></div>;

  async function toggle(user: UserSummary) {
    const name = user.full_name || user.email;
    const on = !user.is_active;
    if (!(await confirmAction(on ? `Turn on access for ${name}? They will be able to sign in again.` : `Turn off access for ${name}? They will be signed out and cannot sign in.`))) return;
    setError("");
    try {
      await (on ? activate : deactivate).mutateAsync(user.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not update the user.");
    }
  }

  const rows = users.data?.users ?? [];
  const me = authentication.user?.id;
  return (
    <>
      <ListScreen<Filter>
        title="Users"
        subtitle="Everyone who can sign in to your business, and their role."
        primary={can("users.create") ? { label: "Invite user", icon: UserPlus, onClick: () => setDialog({ userId: null }) } : null}
        onRefresh={() => void users.refetch()}
        refreshing={users.isFetching}
        search={{ value: searchInput, onChange: (v) => { setSearchInput(v); setPage(1); }, placeholder: "Search name or email", label: "Search users" }}
        chips={{ options: filters, value: filter, onChange: (v) => { setFilter(v); setPage(1); }, label: "Access filter" }}
        footer={<Pager pagination={users.data?.pagination} noun="users" onPage={setPage} />}
      >
        {error ? <p role="alert" className="nxl-error">{error}</p> : null}
        <ListState loading={users.isPending} error={users.error} onRetry={() => void users.refetch()} isEmpty={!rows.length} emptyIcon={Users}
          emptyTitle={search ? "No users match" : filter === "inactive" ? "No users with access turned off" : "No users yet"} emptyDescription={search ? "Try another name or email." : undefined}>
          <CompactList label="Users" columns={[{ label: "User" }, { label: "Role" }, { label: "Access" }]}>
            {rows.map((u) => {
              const self = u.id === me;
              const actions: ListAction[] = [
                ...(can("users.update") ? [{ icon: Pencil, label: `Edit ${u.full_name || u.email}`, onClick: () => setDialog({ userId: u.id }) }] : []),
                ...(!self && (u.is_active ? can("users.deactivate") : can("users.activate"))
                  ? [{ icon: u.is_active ? PowerOff : Power, label: `${u.is_active ? "Turn off" : "Turn on"} access for ${u.full_name || u.email}`, onClick: () => void toggle(u), busy: (activate.isPending || deactivate.isPending) && (activate.variables === u.id || deactivate.variables === u.id) }]
                  : []),
              ];
              return (
                <CompactRow
                  key={u.id}
                  title={<span className="inline-flex items-center gap-2.5"><span className="nxs-avatar" aria-hidden="true">{initials(u)}</span>{u.full_name || u.email}{self ? <Badge tone="info">You</Badge> : null}</span>}
                  subtitle={u.email}
                  meta={[u.role?.name ?? "No role"]}
                  badge={u.is_active ? <Badge tone="success">Active</Badge> : <Badge tone="neutral">Off</Badge>}
                  actions={actions}
                  onOpen={can("users.update") ? () => setDialog({ userId: u.id }) : undefined}
                  openLabel={`Open ${u.full_name || u.email}`}
                />
              );
            })}
          </CompactList>
        </ListState>
      </ListScreen>
      <UserDialog open={Boolean(dialog)} userId={dialog?.userId ?? null} onClose={() => setDialog(null)} />
    </>
  );
}

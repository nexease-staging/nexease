"use client";

import { useMemo, useState } from "react";
import { KeyRound, Search } from "lucide-react";
import EmptyState from "@/components/ui/empty-state";
import { useAuth } from "@/features/auth/auth-context";
import { useQuery } from "@tanstack/react-query";
import { listPermissions } from "@/features/roles/api";
import type { PermissionDetail } from "@/features/roles/types";
import { hasPermission } from "@/lib/authorization/permissions";

/** Read-only catalogue of permissions, grouped by module, so admins know what roles can grant. */
export default function PermissionsPage() {
  const { authentication } = useAuth();
  const canRead = hasPermission(authentication?.role.permissions ?? [], "permissions.read");
  const [search, setSearch] = useState("");
  const [module, setModule] = useState("");
  // The API serves at most 100 per page; load every page so the catalogue is complete.
  const list = useQuery({
    queryKey: ["permissions", "all"],
    enabled: canRead,
    staleTime: 300_000,
    queryFn: async () => {
      const found: PermissionDetail[] = [];
      for (let page = 1; page <= 20; page += 1) {
        const data = await listPermissions({ page, page_size: 100, sort: "module,code" });
        found.push(...data.permissions);
        if (!data.pagination.has_next) break;
      }
      return found;
    },
  });
  const all = useMemo(() => list.data ?? [], [list.data]);
  const term = search.trim().toLowerCase();
  const groups = useMemo(() => {
    const map = new Map<string, typeof all>();
    for (const p of all) {
      if (module && p.module !== module) continue;
      if (term && !`${p.code} ${p.name} ${p.description ?? ""}`.toLowerCase().includes(term)) continue;
      map.set(p.module, [...(map.get(p.module) ?? []), p]);
    }
    return [...map.entries()];
  }, [all, module, term]);
  if (!authentication) return null;
  if (!canRead) return <div className="nx-card"><EmptyState icon={KeyRound} title="Permissions unavailable" description="Your role does not include the permissions.read permission." /></div>;
  const modules = [...new Set(all.map((p) => p.module))];
  const label = (m: string) => m.replaceAll("_", " ").replace(/^\w/, (c) => c.toUpperCase());

  return (
    <div className="nxl-screen">
      <header className="nxl-header">
        <div className="min-w-0">
          <h1>Permissions</h1>
          <p className="nx-muted">{all.length} permissions in {modules.length} modules. Give them to people through Roles.</p>
        </div>
      </header>
      <section className="nxl-panel">
        <div className="nxl-filters">
          <label className="nxl-search"><Search size={16} aria-hidden="true" /><input type="search" aria-label="Search permissions" placeholder="Search, e.g. invoice, payroll, export" value={search} onChange={(e) => setSearch(e.target.value)} /></label>
        </div>
        <div className="nx-chip-row nxl-chips" role="group" aria-label="Module">
          <button type="button" className="nx-chip" aria-pressed={!module} onClick={() => setModule("")}>All</button>
          {modules.map((m) => <button key={m} type="button" className="nx-chip" aria-pressed={module === m} onClick={() => setModule(m)}>{label(m)}</button>)}
        </div>
        {list.isPending ? <div className="nx-skeleton m-3 h-40" aria-busy="true" /> : list.error ? <p role="alert" className="nxl-error">{list.error.message}</p> : !groups.length ? (
          <EmptyState icon={KeyRound} title="No permission matches" description="Try another word or module." />
        ) : groups.map(([m, perms]) => (
          <div key={m} className="nxs-perm-group">
            <h3>{label(m)}<span>{perms.length}</span></h3>
            <div className="nxs-chips">
              {perms.map((p) => <span key={p.id} title={p.description ?? undefined} data-off={!p.is_active || undefined}>{p.name}<small>{p.code}</small></span>)}
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}

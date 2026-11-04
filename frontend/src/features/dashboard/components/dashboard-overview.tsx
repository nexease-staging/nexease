"use client";

import Link from "next/link";
import { useAuth } from "@/features/auth/auth-context";
import type { MainDashboard } from "@/features/dashboard/types";
import { hasPermission } from "@/lib/authorization/permissions";
import { quickCreateActions } from "@/components/layout/quick-create";

/** Greeting and quick actions; KPI grid and charts remain in the parent dashboard. */
export default function DashboardOverview(_props: { data?: MainDashboard; isLoading: boolean }) {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const actions = quickCreateActions.filter((a) => hasPermission(permissions, a.permission));
  return (
    <div className="space-y-5">
      <header>
        <p className="nx-muted text-[11px] font-bold uppercase tracking-[.14em]">{authentication?.organization?.name ?? "NexEase"}</p>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
          Welcome back{authentication?.user?.first_name ? `, ${authentication.user?.first_name}` : ""}
        </h1>
      </header>

      {actions.length ? (
        <nav aria-label="Quick actions" className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {actions.map(({ label, hint, href, icon: Icon }) => (
            <Link key={href} href={href} className="nx-card nx-card-link flex items-center gap-3 p-3.5">
              <span className="nx-icon-chip" data-tone="success"><Icon size={20} aria-hidden="true" /></span>
              <span className="min-w-0"><strong className="block truncate text-sm">{label}</strong><small className="nx-muted hidden truncate text-xs sm:block">{hint}</small></span>
            </Link>
          ))}
        </nav>
      ) : null}


    </div>
  );
}

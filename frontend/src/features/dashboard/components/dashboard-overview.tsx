"use client";

import Link from "next/link";
import { AlertTriangle, CheckCircle2, CircleDollarSign, Landmark, Package, ReceiptText, type LucideIcon } from "lucide-react";
import { useAuth } from "@/features/auth/auth-context";
import type { DashboardActivityType, MainDashboard } from "@/features/dashboard/types";
import { hasPermission } from "@/lib/authorization/permissions";
import { formatDate, formatMoney } from "@/lib/format";
import { quickCreateActions } from "@/components/layout/quick-create";

const activityMeta: Record<DashboardActivityType, { label: string; href: string; icon: LucideIcon }> = {
  INVOICE: { label: "Invoice", href: "/invoices", icon: CircleDollarSign },
  VENDOR_BILL: { label: "Vendor bill", href: "/vendor-bills", icon: ReceiptText },
  BANK_TRANSACTION: { label: "Bank", href: "/banking", icon: Landmark },
  STOCK_MOVEMENT: { label: "Stock", href: "/inventory", icon: Package },
};

/** Replaces the old dark hero: greeting, one-tap actions, attention list, recent activity. The existing KPI grid and charts stay below it. */
export default function DashboardOverview({ data, isLoading }: { data?: MainDashboard; isLoading: boolean }) {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const actions = quickCreateActions.filter((a) => hasPermission(permissions, a.permission));
  const alerts = data?.alerts;

  const attention = [
    { label: "Overdue invoices", count: alerts?.overdue_invoices ?? 0, href: "/invoices?status=ISSUED", hint: "Customers to chase" },
    { label: "Overdue vendor bills", count: alerts?.overdue_bills ?? 0, href: "/vendor-bills", hint: "Payments due to suppliers" },
    { label: "Out-of-stock items", count: alerts?.out_of_stock_items ?? 0, href: "/inventory", hint: "Reorder soon" },
  ].filter((a) => a.count > 0);

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

      <div className="grid gap-5 lg:grid-cols-5">
        <section className="nx-card p-4 lg:col-span-2" aria-label="Needs attention">
          <h2 className="nx-section-title mb-3">Needs attention</h2>
          {isLoading ? <div className="nx-skeleton h-20" aria-busy="true" /> : attention.length === 0 ? (
            <p className="flex items-center gap-2 text-sm" style={{ color: "var(--nx-success-fg)" }}><CheckCircle2 size={18} aria-hidden="true" />You are all caught up.</p>
          ) : (
            <ul className="space-y-2">
              {attention.map((a) => (
                <li key={a.label}>
                  <Link href={a.href} className="nx-menu-item">
                    <span className="nx-icon-chip" data-tone="warning"><AlertTriangle size={18} aria-hidden="true" /></span>
                    <span className="flex-1"><strong className="text-sm">{a.label}</strong><small>{a.hint}</small></span>
                    <span className="nx-badge" data-tone="warning">{a.count}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="nx-card p-4 lg:col-span-3" aria-label="Recent activity">
          <h2 className="nx-section-title mb-3">Recent activity</h2>
          {isLoading ? <div className="nx-skeleton h-32" aria-busy="true" /> : !data?.recent_activity.length ? (
            <p className="nx-muted text-sm">Activity will appear here as you create invoices, bills and stock movements.</p>
          ) : (
            <ul>
              {data.recent_activity.slice(0, 6).map((a) => {
                const m = activityMeta[a.activity_type] ?? activityMeta.INVOICE;
                return (
                  <li key={`${a.activity_type}-${a.reference_id}`}>
                    <Link href={m.href} className="nx-menu-item">
                      <span className="nx-icon-chip" data-tone="neutral"><m.icon size={18} aria-hidden="true" /></span>
                      <span className="min-w-0 flex-1"><strong className="block truncate text-sm">{a.reference_number} · {m.label}</strong><small className="truncate">{a.description} · {formatDate(a.activity_date)}</small></span>
                      {a.amount ? <span className="text-sm font-semibold tabular-nums">{formatMoney(a.amount)}</span> : null}
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

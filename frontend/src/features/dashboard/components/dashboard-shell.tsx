"use client";
import { useMemo, useState } from "react";
import Link from "next/link";
import { CalendarRange, RefreshCw } from "lucide-react";
import { useAuth } from "@/features/auth/auth-context";
import { hasPermission } from "@/lib/authorization/permissions";
import { quickCreateActions } from "@/components/layout/quick-create";
import { useMainDashboard } from "@/features/dashboard/hooks";
import { greeting, longDate, num, PRESETS, presetRange, type PresetKey } from "@/features/dashboard/format";
import BusinessSetupCard from "./business-setup-card";
import { CashFlowChart, TradeChart } from "./dashboard-charts";
import { ActivityFeed, AgingCard, AttentionStrip, MoneyBand, StatusCard, TopList } from "./dashboard-parts";
import DashboardLoadingSkeleton from "./dashboard-loading-skeleton";

export default function DashboardShell() {
  const { authentication } = useAuth();
  const [preset, setPreset] = useState<PresetKey>("fy");
  const [range, setRange] = useState(() => presetRange("fy"));
  const parameters = useMemo(() => ({ ...range }), [range]);
  const { data: dashboard, isLoading, isFetching, isError, error, refetch, dataUpdatedAt } = useMainDashboard(parameters);
  const permissions = authentication?.role.permissions ?? [];
  const actions = quickCreateActions.filter((a) => hasPermission(permissions, a.permission));
  const name = authentication?.user?.first_name;
  const choose = (key: PresetKey) => {
    setPreset(key);
    if (key !== "custom") setRange(presetRange(key));
  };
  const updated = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit" }) : null;

  return (
    <div className="nxd">
      <header className="nxd-top">
        <div className="nxd-hello">
          <h1>{greeting()}{name ? `, ${name}` : ""}</h1>
          <p>
            Here is how <strong>{authentication?.organization?.name ?? "your business"}</strong> is doing
            {dashboard ? <> from {longDate(dashboard.period.start_date)} to {longDate(dashboard.period.end_date)}</> : null}.
          </p>
        </div>
        <div className="nxd-period">
          <div className="nxd-seg" role="group" aria-label="Reporting period">
            {PRESETS.map((p) => (
              <button key={p.key} type="button" aria-pressed={preset === p.key} onClick={() => choose(p.key)}>{p.label}</button>
            ))}
            <button type="button" aria-pressed={preset === "custom"} onClick={() => choose("custom")}><CalendarRange size={14} aria-hidden="true" />Custom</button>
          </div>
          <button type="button" className="nxd-refresh" aria-label="Refresh" title={updated ? `Updated ${updated}` : "Refresh"} disabled={isFetching} onClick={() => void refetch()}>
            <RefreshCw size={15} className={isFetching ? "animate-spin" : ""} aria-hidden="true" />
          </button>
        </div>
      </header>

      {preset === "custom" ? (
        <div className="nxd-custom">
          <label>From<input type="date" required value={range.start_date} max={range.end_date} onChange={(e) => { const v = e.target.value; if (v) setRange((r) => ({ ...r, start_date: v })); }} className="nx-input" /></label>
          <label>To<input type="date" required value={range.end_date} min={range.start_date} onChange={(e) => { const v = e.target.value; if (v) setRange((r) => ({ ...r, end_date: v })); }} className="nx-input" /></label>
        </div>
      ) : null}

      {actions.length ? (
        <nav className="nxd-actions" aria-label="Quick actions">
          {actions.map(({ label, href, icon: Icon }) => (
            <Link key={href} href={href}><Icon size={16} aria-hidden="true" />{label}</Link>
          ))}
        </nav>
      ) : null}

      <BusinessSetupCard />

      {isLoading ? <DashboardLoadingSkeleton /> : null}
      {isError ? (
        <section role="alert" className="nxd-error">
          <h2>The dashboard could not load</h2>
          <p>{error instanceof Error ? error.message : "Something went wrong while fetching your figures."} Check your connection and try again.</p>
          <button type="button" className="nx-button nx-secondary" onClick={() => void refetch()}><RefreshCw size={14} aria-hidden="true" />Try again</button>
        </section>
      ) : null}

      {dashboard ? (
        <div className="nxd-body" aria-busy={isFetching}>
          <MoneyBand kpis={dashboard.kpis} />
          <AttentionStrip alerts={dashboard.alerts} />
          <div className="nxd-grid">
            <TradeChart sales={dashboard.sales_trend} purchases={dashboard.purchase_trend} />
            <AgingCard aging={dashboard.receivable_aging} />
            <CashFlowChart points={dashboard.cash_flow} />
            <StatusCard invoices={dashboard.invoice_status} bills={dashboard.bill_status} inventory={dashboard.inventory_status} />
            <TopList title="Top customers" hint="Who bought the most in this period." href="/customers" total={num(dashboard.kpis.total_sales)} empty="No sales in this period yet."
              rows={dashboard.top_customers.map((c) => ({ id: c.customer_id, name: c.customer_name, amount: num(c.amount) }))} />
            <TopList title="Top suppliers" hint="Where most of your purchases went." href="/suppliers" total={num(dashboard.kpis.total_purchases)} empty="No purchases in this period yet."
              rows={dashboard.top_suppliers.map((s) => ({ id: s.supplier_id, name: s.supplier_name, amount: num(s.amount) }))} />
            <ActivityFeed items={dashboard.recent_activity} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

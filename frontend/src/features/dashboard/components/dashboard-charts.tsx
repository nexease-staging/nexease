"use client";
import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DashboardCashFlowPoint as CashFlowPoint, DashboardTrendPoint as TrendPoint } from "@/features/dashboard/types";
import { axis, compact, num, periodLabel, rupees } from "@/features/dashboard/format";

type TipRow = { label: string; value: number; swatch?: string };
function Tip({ active, title, rows }: { active?: boolean; title?: string; rows: TipRow[] }) {
  if (!active || !rows.length) return null;
  return (
    <div className="nxd-tip" role="tooltip">
      <strong>{title}</strong>
      {rows.map((r) => (
        <span key={r.label}>{r.swatch ? <i style={{ background: r.swatch }} aria-hidden="true" /> : null}{r.label}<b>{rupees(r.value)}</b></span>
      ))}
    </div>
  );
}

const tick = { fontSize: 11, fill: "var(--nx-text-muted)" };

export function TradeChart({ sales, purchases }: { sales: TrendPoint[]; purchases: TrendPoint[] }) {
  const data = useMemo(() => {
    const map = new Map<string, { period: string; sales: number; purchases: number }>();
    for (const p of sales) map.set(p.period, { period: p.period, sales: num(p.amount), purchases: 0 });
    for (const p of purchases) {
      const row = map.get(p.period) ?? { period: p.period, sales: 0, purchases: 0 };
      row.purchases = num(p.amount);
      map.set(p.period, row);
    }
    return [...map.values()].sort((a, b) => a.period.localeCompare(b.period));
  }, [sales, purchases]);
  const totalSales = data.reduce((s, r) => s + r.sales, 0);
  const totalPurchases = data.reduce((s, r) => s + r.purchases, 0);
  const spread = totalSales - totalPurchases;

  return (
    <section className="nxd-card nxd-span-2" aria-labelledby="nxd-trade">
      <header className="nxd-card-head">
        <div>
          <h2 id="nxd-trade">Sales and purchases</h2>
          <p>Invoices raised against bills received, month by month.</p>
        </div>
      </header>
      <dl className="nxd-legend-totals">
        <div><dt><i className="nxd-sw" data-s="sales" aria-hidden="true" />Sales</dt><dd title={rupees(totalSales)}>{compact(totalSales)}</dd></div>
        <div><dt><i className="nxd-sw" data-s="purchases" aria-hidden="true" />Purchases</dt><dd title={rupees(totalPurchases)}>{compact(totalPurchases)}</dd></div>
        <div><dt>Sales minus purchases</dt><dd title={rupees(spread)} data-sign={spread < 0 ? "neg" : "pos"}>{spread > 0 ? "+" : ""}{compact(spread)}</dd></div>
      </dl>
      {data.length ? (
        <div className="nxd-plot" role="img" aria-label={`Sales ${rupees(totalSales)} and purchases ${rupees(totalPurchases)} across ${data.length} periods`}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} barGap={2} barCategoryGap="22%" margin={{ top: 8, right: 4, bottom: 0, left: -8 }}>
              <CartesianGrid vertical={false} stroke="var(--nx-border)" />
              <XAxis dataKey="period" tickFormatter={periodLabel} tick={tick} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={8} />
              <YAxis tickFormatter={axis} tick={tick} tickLine={false} axisLine={false} width={48} />
              <Tooltip cursor={{ fill: "var(--nx-surface-muted)" }} content={({ active, payload, label }) => (
                <Tip active={active} title={periodLabel(String(label))} rows={payload?.length ? [
                  { label: "Sales", value: Number(payload[0]?.payload.sales), swatch: "var(--nxd-sales)" },
                  { label: "Purchases", value: Number(payload[0]?.payload.purchases), swatch: "var(--nxd-purchases)" },
                ] : []} />
              )} />
              <Bar dataKey="sales" name="Sales" fill="var(--nxd-sales)" radius={[4, 4, 0, 0]} maxBarSize={22} isAnimationActive={false} />
              <Bar dataKey="purchases" name="Purchases" fill="var(--nxd-purchases)" radius={[4, 4, 0, 0]} maxBarSize={22} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : <p className="nxd-empty">No sales or purchases in this period yet.</p>}
    </section>
  );
}

export function CashFlowChart({ points }: { points: CashFlowPoint[] }) {
  const data = useMemo(() => points.map((p) => ({ period: p.period, inflow: num(p.inflow), outflow: num(p.outflow), net: num(p.net) })), [points]);
  const inflow = data.reduce((s, r) => s + r.inflow, 0);
  const outflow = data.reduce((s, r) => s + r.outflow, 0);
  const net = inflow - outflow;
  return (
    <section className="nxd-card nxd-span-2" aria-labelledby="nxd-cash">
      <header className="nxd-card-head">
        <div>
          <h2 id="nxd-cash">Cash flow</h2>
          <p>Money that came in minus money that went out. Bars below the line are months you spent more than you received.</p>
        </div>
      </header>
      <dl className="nxd-legend-totals">
        <div><dt>Money in</dt><dd title={rupees(inflow)}>{compact(inflow)}</dd></div>
        <div><dt>Money out</dt><dd title={rupees(outflow)}>{compact(outflow)}</dd></div>
        <div><dt>Net cash</dt><dd title={rupees(net)} data-sign={net < 0 ? "neg" : "pos"}>{net > 0 ? "+" : ""}{compact(net)}</dd></div>
      </dl>
      {data.length ? (
        <div className="nxd-plot nxd-plot-short" role="img" aria-label={`Net cash ${rupees(net)} across ${data.length} periods`}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} barCategoryGap="28%" margin={{ top: 8, right: 4, bottom: 0, left: -8 }}>
              <CartesianGrid vertical={false} stroke="var(--nx-border)" />
              <XAxis dataKey="period" tickFormatter={periodLabel} tick={tick} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={8} />
              <YAxis tickFormatter={axis} tick={tick} tickLine={false} axisLine={false} width={48} />
              <ReferenceLine y={0} stroke="var(--nx-border-strong)" />
              <Tooltip cursor={{ fill: "var(--nx-surface-muted)" }} content={({ active, payload, label }) => {
                const r = payload?.[0]?.payload as { inflow: number; outflow: number; net: number } | undefined;
                return <Tip active={active} title={periodLabel(String(label))} rows={r ? [{ label: "Money in", value: r.inflow }, { label: "Money out", value: r.outflow }, { label: "Net", value: r.net, swatch: r.net < 0 ? "var(--nxd-neg)" : "var(--nxd-pos)" }] : []} />;
              }} />
              <Bar dataKey="net" name="Net cash" radius={[4, 4, 4, 4]} maxBarSize={28} isAnimationActive={false}>
                {data.map((r) => <Cell key={r.period} fill={r.net < 0 ? "var(--nxd-neg)" : "var(--nxd-pos)"} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : <p className="nxd-empty">No bank or cash movement recorded in this period.</p>}
    </section>
  );
}

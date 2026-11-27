"use client";

import Link from "next/link";
import { ArrowDownLeft, ArrowUpRight, ChevronRight, MessageCircle, RefreshCw } from "lucide-react";
import { openShare } from "@/features/share/api";
import { inr, useDashboard } from "./api";
import { ErrorState, Loading } from "./bits";

function Trend({ points }: { points: { label: string; sales: number; purchases: number | null }[] }) {
  const W = 300, H = 140, L = 18, R = 18, T = 14, B = 26;
  const max = Math.max(1, ...points.map((p) => Math.max(p.sales, p.purchases ?? 0)));
  const x = (i: number) => L + (i * (W - L - R)) / Math.max(1, points.length - 1);
  const y = (v: number) => T + (H - T - B) * (1 - v / max);
  const line = (key: "sales" | "purchases") => points.map((p, i) => `${x(i)},${y((p[key] as number) ?? 0)}`).join(" ");
  const hasBuy = points.some((p) => p.purchases !== null && p.purchases > 0);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="nxp-chart" role="img" aria-label={`Sales for the last ${points.length} months`}>
      <line x1={L} x2={W - R} y1={H - B} y2={H - B} className="nxp-axis" />
      {hasBuy ? <polyline points={line("purchases")} className="nxp-line buy" /> : null}
      <polyline points={line("sales")} className="nxp-line" />
      {points.map((p, i) => <circle key={i} cx={x(i)} cy={y(p.sales)} r={i === points.length - 1 ? 4.5 : 3} className="nxp-dot" />)}
      {points.map((p, i) => <text key={p.label} x={x(i)} y={H - 7} textAnchor="middle" className="nxp-tick">{p.label}</text>)}
    </svg>
  );
}

export default function PhoneDashboard() {
  const q = useDashboard();
  if (q.isPending) return <div className="nxp-page"><Loading /></div>;
  if (q.error) return <div className="nxp-page"><ErrorState error={q.error} retry={() => void q.refetch()} /></div>;
  const d = q.data;
  const pts = d.trend.map((t) => ({ label: new Date(t.month + "-01T00:00:00").toLocaleString("en", { month: "short" }), sales: Number(t.sales ?? 0), purchases: t.purchases === null ? null : Number(t.purchases) }));
  const change = d.sales_prev && Number(d.sales_prev) ? ((Number(d.sales_month) - Number(d.sales_prev)) / Number(d.sales_prev)) * 100 : null;
  const cash = d.banks.reduce((s, b) => s + Number(b.balance || 0), 0);
  return (
    <div className="nxp-page">
      <div className="nxp-two">
        {d.receivable !== null ? <Link href="/accounts-receivable" className="nxp-card nxp-stat"><span className="nxp-mute">You’ll get</span><b className="get">{inr(d.receivable)}</b>{Number(d.overdue_receivable) > 0 ? <small className="give">{inr(d.overdue_receivable)} overdue</small> : <small className="nxp-mute">Nothing overdue</small>}</Link> : null}
        {d.payable !== null ? <Link href="/accounts-payable" className="nxp-card nxp-stat"><span className="nxp-mute">You’ll give</span><b className="give">{inr(d.payable)}</b><small className="nxp-mute">To suppliers</small></Link> : null}
      </div>
      {d.sales_month !== null ? (
        <div className="nxp-card">
          <span className="nxp-mute">Sales this month</span>
          <div className="nxp-big">{inr(d.sales_month)}</div>
          {change !== null ? <small className={change >= 0 ? "get" : "give"}>{change >= 0 ? "▲" : "▼"} {Math.abs(change).toFixed(0)}% vs last month</small> : null}
          <Trend points={pts} />
          <div className="nxp-legend"><span><i className="s" />Sales</span>{pts.some((p) => p.purchases) ? <span><i className="p" />Purchases</span> : null}</div>
        </div>
      ) : null}
      {d.banks.length ? (
        <div className="nxp-card nxp-list">
          <div className="nxp-cardhead"><b>Cash & bank</b><span>{inr(cash)}</span></div>
          {d.banks.map((b) => <div className="nxp-row" key={b.id}><div className="nxp-g"><b>{b.name}</b><small>{b.type === "CASH" ? "Cash" : "Bank"}</small></div><div className="nxp-amt">{inr(b.balance)}</div></div>)}
        </div>
      ) : null}
      {d.top_dues.length ? (
        <div className="nxp-card nxp-list">
          <div className="nxp-cardhead"><b>Collect next</b><Link href="/accounts-receivable">All</Link></div>
          {d.top_dues.map((p) => (
            <div className="nxp-row" key={p.id}>
              <div className="nxp-g"><b>{p.name}</b><small>{Number(p.overdue) > 0 ? `${inr(p.overdue)} overdue` : "Not yet due"}</small></div>
              <div className="nxp-amt get">{inr(p.balance)}</div>
              <button type="button" className="nxp-ic tint" aria-label={`Send statement to ${p.name}`} onClick={() => openShare({ kind: "statement", id: p.id, side: "customer", title: p.name })}><MessageCircle size={18} /></button>
            </div>
          ))}
        </div>
      ) : null}
      <div className="nxp-card nxp-list">
        <Link href="/reports" className="nxp-row nxp-link"><div className="nxp-g"><b>All reports</b><small>Profit and loss, balance sheet, GST, stock and more</small></div><ChevronRight size={18} /></Link>
        <Link href="/payments" className="nxp-row nxp-link"><div className="nxp-g"><b>Payments</b><small>Money in and money out</small></div><span className="nxp-pair"><ArrowDownLeft size={16} className="get" /><ArrowUpRight size={16} className="give" /></span></Link>
        {d.tally ? <Link href="/tally" className="nxp-row nxp-link"><div className="nxp-g"><b>Tally · {d.tally.company}</b><small>{d.tally.last_seen ? `Last synced ${new Date(d.tally.last_seen).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" })}` : "Waiting for the connector"}</small></div><RefreshCw size={18} /></Link> : null}
      </div>
    </div>
  );
}

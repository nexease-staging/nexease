"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { AlertTriangle, ArrowDownRight, ArrowRight, ArrowUpRight, BookOpen, ChartNoAxesCombined, FileSpreadsheet, Info, Landmark, ListTree, ReceiptText, Scale, ShieldCheck, Wallet, Waves } from "lucide-react";
import StatCard from "@/components/ui/stat-card";
import ReportChart from "@/features/reports/components/report-chart";
import { formatDate } from "@/lib/format";
import { change, inr, presets, useFinanceOverview } from "./api";

const TOOLS = [
  { href: "/profit-and-loss", label: "Profit & loss", hint: "Income, costs and profit", icon: ChartNoAxesCombined },
  { href: "/balance-sheet", label: "Balance sheet", hint: "Assets, liabilities, capital", icon: Scale },
  { href: "/cash-flow", label: "Cash flow", hint: "Where cash came from and went", icon: Waves },
  { href: "/trial-balance", label: "Trial balance", hint: "Every account, debits = credits", icon: ListTree },
  { href: "/general-ledger", label: "General ledger", hint: "Account-wise entries", icon: BookOpen },
  { href: "/journal-entries", label: "Journals / day book", hint: "Manual and automatic entries", icon: ReceiptText },
  { href: "/chart-of-accounts", label: "Chart of accounts", hint: "Add and organise accounts", icon: FileSpreadsheet },
  { href: "/banking", label: "Banking", hint: "Statements and reconciliation", icon: Landmark },
  { href: "/finance-audit", label: "Finance audit", hint: "Who changed what, and when", icon: ShieldCheck },
];

function Delta({ value, good = "up" }: { value: number | null; good?: "up" | "down" }) {
  if (value === null || !Number.isFinite(value)) return <span className="nxfn-delta">No earlier figure</span>;
  const up = value >= 0;
  const positive = good === "up" ? up : !up;
  return <span className="nxfn-delta" data-tone={positive ? "good" : "bad"}>{up ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}{Math.abs(value).toFixed(1)}% vs previous period</span>;
}

export default function FinanceHub() {
  const options = useMemo(() => presets(), []);
  const [preset, setPreset] = useState("fy");
  const [custom, setCustom] = useState({ from: options[0].from, to: options[0].to });
  const period = preset === "custom" ? custom : options.find((o) => o.key === preset)!;
  const q = useFinanceOverview(period.from, period.to);
  const d = q.data;

  return (
    <div className="nxl-screen nxfn">
      <header className="nxl-header">
        <div className="min-w-0">
          <h1>Finance</h1>
          <p className="nx-muted">{d ? `${formatDate(d.from)} – ${formatDate(d.to)} · compared with ${formatDate(d.previous.from)} – ${formatDate(d.previous.to)}` : "Your books at a glance"}</p>
        </div>
        <div className="nxfn-period nxr-keep">
          <select aria-label="Period" value={preset} onChange={(e) => setPreset(e.target.value)}>
            {options.map((o) => <option key={o.key} value={o.key}>{o.label}</option>)}
            <option value="custom">Custom dates</option>
          </select>
          {preset === "custom" ? <>
            <input type="date" aria-label="From" value={custom.from} max={custom.to} onChange={(e) => setCustom({ ...custom, from: e.target.value })} />
            <input type="date" aria-label="To" value={custom.to} min={custom.from} onChange={(e) => setCustom({ ...custom, to: e.target.value })} />
          </> : null}
        </div>
      </header>

      {q.isPending ? <div className="nxfn-skeleton"><i /><i /><i /></div> : q.error ? (
        <div className="nxf-error" role="alert">{(q.error as Error).message}<button type="button" className="nx-button nx-secondary" onClick={() => void q.refetch()}>Try again</button></div>
      ) : d ? (
        <div className="nxfn-stack">
          {d.alerts.length ? (
            <ul className="nxfn-alerts">{d.alerts.map((a) => <li key={a.text} data-tone={a.tone}>{a.tone === "info" ? <Info size={16} /> : <AlertTriangle size={16} />}<span>{a.text}</span><Link href={a.href}>Open<ArrowRight size={14} /></Link></li>)}</ul>
          ) : null}

          <div className="nx-kpi-strip" data-cols="4">
            <StatCard label="Cash & bank" value={inr(d.cash_bank)} hint="Ledger balance today" icon={Wallet} tone={Number(d.cash_bank) < 0 ? "danger" : "success"} />
            <StatCard label="Customers owe you" value={inr(d.receivable)} hint={d.ratios.receivable_days ? `≈ ${Math.round(Number(d.ratios.receivable_days))} days of sales` : "Accounts receivable"} icon={ArrowDownRight} href="/accounts-receivable" />
            <StatCard label="You owe suppliers" value={inr(d.payable)} hint={d.ratios.payable_days ? `≈ ${Math.round(Number(d.ratios.payable_days))} days of costs` : "Accounts payable"} icon={ArrowUpRight} href="/accounts-payable" />
            <StatCard label={Number(d.gst_position) >= 0 ? "GST payable (net)" : "GST credit (net)"} value={inr(Math.abs(Number(d.gst_position)))} hint="Output GST less input GST in your books" icon={ReceiptText} href="/taxation" />
          </div>

          <section className="nxfn-pl">
            <div><span>Income</span><strong>{inr(d.income)}</strong><Delta value={change(d.income, d.previous_income)} /></div>
            <div><span>Expenses</span><strong>{inr(d.expenses)}</strong><Delta value={change(d.expenses, d.previous_expenses)} good="down" /></div>
            <div data-tone={Number(d.net_profit) >= 0 ? "good" : "bad"}><span>{Number(d.net_profit) >= 0 ? "Net profit" : "Net loss"}</span><strong>{inr(Math.abs(Number(d.net_profit)))}</strong><Delta value={change(d.net_profit, d.previous_net_profit)} /></div>
            <Link href="/profit-and-loss" className="nxfn-more">Full profit & loss<ArrowRight size={14} /></Link>
          </section>

          <div className="nxfn-grid">
            <section className="nxfn-card nxfn-wide">
              <h2>Income and expenses, last 12 months</h2>
              <ReportChart title="Income and expenses" chart={{ type: "bar", x: "period", y: ["income", "expense"] }} rows={d.trend} columns={[{ key: "period", label: "Month", type: "text" }, { key: "income", label: "Income", type: "money" }, { key: "expense", label: "Expenses", type: "money" }]} />
            </section>
            <section className="nxfn-card">
              <h2>Where the money went</h2>
              {d.top_expenses.length ? (
                <ul className="nxfn-bars">
                  {d.top_expenses.map((e) => (
                    <li key={e.account_id}>
                      <Link href={`/general-ledger?account=${e.account_id}`}><span>{e.name}</span><b>{inr(e.amount)}</b></Link>
                      <div className="nxfn-bar" role="img" aria-label={`${e.share}% of expenses`}><i style={{ width: `${Math.max(2, Number(e.share))}%` }} /></div>
                    </li>
                  ))}
                </ul>
              ) : <p className="nx-muted">No expenses in this period.</p>}
            </section>
          </div>
          <div className="nxfn-grid2">
            <section className="nxfn-card">
              <h2>Health check</h2>
              <dl className="nxfn-ratios">
                <div><dt>Gross margin</dt><dd>{d.ratios.gross_margin ? `${d.ratios.gross_margin}%` : "—"}</dd><small>Profit after cost of goods, per ₹100 of sales</small></div>
                <div><dt>Net margin</dt><dd>{d.ratios.net_margin ? `${d.ratios.net_margin}%` : "—"}</dd><small>Profit kept from every ₹100 of sales</small></div>
                <div><dt>Current ratio</dt><dd>{d.ratios.current_ratio ?? "—"}</dd><small>Short-term assets per ₹1 of short-term dues (1.5+ is comfortable)</small></div>
                <div><dt>Collection period</dt><dd>{d.ratios.receivable_days ? `${Math.round(Number(d.ratios.receivable_days))} days` : "—"}</dd><small>How long customers take to pay</small></div>
              </dl>
            </section>
            <section className="nxfn-card">
              <h2>Bank and cash accounts</h2>
              {d.bank_accounts.length ? (
                <ul className="nxfn-banks">{d.bank_accounts.map((b) => <li key={b.id}><span><strong>{b.name}</strong><small>{b.type === "CASH" ? "Cash" : [b.bank, b.number ? `•• ${b.number}` : ""].filter(Boolean).join(" ")}</small></span><b>{inr(b.balance, 2)}</b></li>)}</ul>
              ) : <p className="nx-muted">No bank accounts yet.</p>}
              <Link className="nxfn-more" href="/banking">{d.unreconciled ? `${d.unreconciled} to reconcile` : "Open banking"}<ArrowRight size={14} /></Link>
            </section>
          </div>

          <section>
            <h2 className="nxfn-h2">Books and reports</h2>
            <div className="nxfn-tools">{TOOLS.map((t) => <Link key={t.href} href={t.href}><t.icon size={19} /><span><strong>{t.label}</strong><small>{t.hint}</small></span></Link>)}</div>
          </section>
        </div>
      ) : null}
    </div>
  );
}

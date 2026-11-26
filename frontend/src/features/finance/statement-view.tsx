"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { BadgeCheck, ChevronDown, Download, TriangleAlert } from "lucide-react";
import { exportWorkbook } from "@/features/business/workspace";
import { formatDate } from "@/lib/format";
import { inr, presets, statementExport, useStatement, type BalanceSheet, type ProfitAndLoss, type StatementSection } from "./api";

type Kind = "profit-and-loss" | "balance-sheet";

function Section({ s, compare, percent, open, toggle }: { s: StatementSection; compare: boolean; percent: boolean; open: boolean; toggle: () => void }) {
  return (
    <tbody className="nxfn-sec" data-open={open || undefined}>
      <tr className="nxfn-sec-head">
        <th scope="rowgroup"><button type="button" aria-expanded={open} onClick={toggle}><ChevronDown size={15} />{s.label}</button></th>
        <td className="num"><b>{inr(s.total, 2)}</b></td>
        {compare ? <td className="num muted">{inr(s.previous, 2)}</td> : null}
        {percent ? <td className="num muted">{s.percent ? `${s.percent}%` : ""}</td> : null}
      </tr>
      {open ? s.rows.map((r) => (
        <tr key={r.account_id || r.name} className="nxfn-acc">
          <td>{r.account_id ? <Link href={`/general-ledger?account=${r.account_id}`}><span className="code">{r.code}</span>{r.name}</Link> : <em>{r.name}</em>}</td>
          <td className="num">{inr(r.amount, 2)}</td>
          {compare ? <td className="num muted">{inr(r.previous, 2)}</td> : null}
          {percent ? <td className="num muted">{r.percent ? `${r.percent}%` : ""}</td> : null}
        </tr>
      )) : null}
      {open && !s.rows.length ? <tr className="nxfn-acc"><td colSpan={4} className="muted">No balances</td></tr> : null}
    </tbody>
  );
}

function Subtotal({ label, amount, previous, pct, compare, percent, strong }: { label: string; amount: string; previous?: string | null; pct?: string | null; compare: boolean; percent: boolean; strong?: boolean }) {
  return (
    <tbody><tr className="nxfn-sub" data-strong={strong || undefined} data-negative={Number(amount) < 0 || undefined}>
      <th scope="row">{label}</th>
      <td className="num">{inr(amount, 2)}</td>
      {compare ? <td className="num muted">{inr(previous, 2)}</td> : null}
      {percent ? <td className="num muted">{pct ? `${pct}%` : ""}</td> : null}
    </tr></tbody>
  );
}

export default function StatementView({ kind }: { kind: Kind }) {
  const pl = kind === "profit-and-loss";
  const options = useMemo(() => presets(), []);
  const [preset, setPreset] = useState("fy");
  const [custom, setCustom] = useState({ from: options[0].from, to: options[0].to });
  const [compare, setCompare] = useState(true);
  const [closed, setClosed] = useState<Set<string>>(new Set());
  const period = preset === "custom" ? custom : options.find((o) => o.key === preset)!;
  const params = pl ? { from: period.from, to: period.to, compare } : { to: period.to, compare };
  const q = useStatement<ProfitAndLoss | BalanceSheet>(kind, params);
  const toggle = (key: string) => setClosed((c) => { const n = new Set(c); if (n.has(key)) n.delete(key); else n.add(key); return n; });
  const d = q.data;

  const heading = pl ? "Profit & loss" : "Balance sheet";
  const sub = d ? (d.statement === "pl" ? `${formatDate(d.from)} – ${formatDate(d.to)}` : `As of ${formatDate(d.as_of)}`) : "";
  const compareLabel = d ? (d.statement === "pl" ? (d.previous_period ? `${formatDate(d.previous_period.from)} – ${formatDate(d.previous_period.to)}` : "") : d.previous_date ? `As of ${formatDate(d.previous_date)}` : "") : "";

  return (
    <div className="nxl-screen nxfn">
      <header className="nxl-header">
        <div className="min-w-0"><h1>{heading}</h1><p className="nx-muted">{sub || "From your posted journals"}</p></div>
        <div className="nxfn-period nxr-keep">
          <select aria-label="Period" value={preset} onChange={(e) => setPreset(e.target.value)}>
            {options.map((o) => <option key={o.key} value={o.key}>{pl ? o.label : `End of ${o.label.toLowerCase()}`}</option>)}
            <option value="custom">{pl ? "Custom dates" : "Custom date"}</option>
          </select>
          {preset === "custom" ? <>
            {pl ? <input type="date" aria-label="From" value={custom.from} max={custom.to} onChange={(e) => setCustom({ ...custom, from: e.target.value })} /> : null}
            <input type="date" aria-label={pl ? "To" : "As of"} value={custom.to} onChange={(e) => setCustom({ ...custom, to: e.target.value })} />
          </> : null}
          <label className="nxfn-check"><input type="checkbox" checked={compare} onChange={(e) => setCompare(e.target.checked)} />Compare</label>
          <button type="button" className="nx-button nx-secondary" onClick={() => void exportWorkbook(statementExport(kind, params), `NexEase-${heading.replace(/\W+/g, "-")}-${period.to}.xlsx`)}><Download size={16} />Excel</button>
        </div>
      </header>

      {q.isPending ? <div className="nxfn-skeleton"><i /><i /><i /></div> : q.error ? <p className="nxf-error" role="alert">{(q.error as Error).message}</p> : d ? (
        <div className="nxfn-stack">
          {d.statement === "bs" ? (
            d.balanced ? <p className="nxfn-ok"><BadgeCheck size={16} />Assets equal liabilities plus capital.</p>
              : <p className="nxfn-warn"><TriangleAlert size={16} />Out of balance by {inr(d.totals.difference, 2)}. An account may have the wrong type; check the trial balance.</p>
          ) : null}
          {d.statement === "pl" ? (
            <div className="nxfn-pl">
              {d.subtotals.map((s) => <div key={s.key} data-tone={s.key === "net_profit" ? (Number(s.amount) >= 0 ? "good" : "bad") : undefined}><span>{s.label}</span><strong>{inr(s.amount)}</strong><span className="nxfn-delta">{s.percent ? `${s.percent}% of revenue` : ""}</span></div>)}
            </div>
          ) : (
            <div className="nxfn-pl">
              <div><span>Total assets</span><strong>{inr(d.totals.assets)}</strong></div>
              <div><span>Total liabilities</span><strong>{inr(d.totals.liabilities)}</strong></div>
              <div data-tone={Number(d.totals.equity_total) >= 0 ? "good" : "bad"}><span>Capital and reserves</span><strong>{inr(d.totals.equity_total)}</strong></div>
            </div>
          )}
          <div className="nxfn-card nxfn-statement">
            <table>
              <thead><tr><th>Account</th><th className="num">{d.statement === "pl" ? "This period" : `As of ${formatDate(d.as_of)}`}</th>{compare ? <th className="num">{compareLabel}</th> : null}{pl ? <th className="num">% of revenue</th> : null}</tr></thead>
              {d.statement === "pl" ? (() => {
                const s = Object.fromEntries(d.sections.map((x) => [x.key, x]));
                const t = Object.fromEntries(d.subtotals.map((x) => [x.key, x]));
                const sec = (k: string) => <Section key={k} s={s[k]} compare={compare} percent open={!closed.has(k)} toggle={() => toggle(k)} />;
                const tot = (k: string, strong = false) => <Subtotal key={k} label={t[k].label} amount={t[k].amount} previous={t[k].previous} pct={t[k].percent} compare={compare} percent strong={strong} />;
                return [sec("revenue"), sec("cost_of_sales"), tot("gross_profit"), sec("operating_expenses"), tot("operating_profit"), sec("other_income"), sec("other_expenses"), tot("net_profit", true)];
              })() : (() => {
                const s = Object.fromEntries(d.sections.map((x) => [x.key, x]));
                const pt = d.previous_totals ?? {};
                const sec = (k: string) => <Section key={k} s={s[k]} compare={compare} percent={false} open={!closed.has(k)} toggle={() => toggle(k)} />;
                return [
                  <tbody key="h1"><tr className="nxfn-group"><th colSpan={3}>Assets</th></tr></tbody>, sec("current_assets"), sec("non_current_assets"),
                  <Subtotal key="ta" label="Total assets" amount={d.totals.assets} previous={pt.assets} compare={compare} percent={false} strong />,
                  <tbody key="h2"><tr className="nxfn-group"><th colSpan={3}>Liabilities and capital</th></tr></tbody>, sec("current_liabilities"), sec("non_current_liabilities"),
                  <Subtotal key="tl" label="Total liabilities" amount={d.totals.liabilities} previous={pt.liabilities} compare={compare} percent={false} />, sec("equity"),
                  <Subtotal key="tle" label="Total liabilities and capital" amount={String(Number(d.totals.liabilities) + Number(d.totals.equity_total))} previous={pt.liabilities !== undefined ? String(Number(pt.liabilities) + Number(pt.equity_total)) : null} compare={compare} percent={false} strong />,
                ];
              })()}
            </table>
          </div>
          <p className="nxfn-fine">Built from posted journal entries. Draft journals are not included. Click an account to open its ledger.{d.statement === "bs" ? " Profit to date is shown under capital until the year is closed." : ""}</p>
        </div>
      ) : null}
    </div>
  );
}

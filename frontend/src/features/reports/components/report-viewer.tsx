"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowDown, ArrowLeft, ArrowUp, FileSpreadsheet, MessageCircle, Printer, RefreshCw, Search, Star, TrendingDown, TrendingUp } from "lucide-react";
import { ActionIcon } from "@/components/list/list-kit";
import EmptyState from "@/components/ui/empty-state";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import { downloadCsv } from "@/lib/export-csv";
import { change, formatValue, periodLabel, periodPresets, useReport, type ReportColumn, type ReportData, type ReportRow } from "../api";
import { favourites, findReport, recent } from "../catalog";
import ReportChart from "./report-chart";

const KPI_ORDER = ["total", "sales", "profit", "net", "amount", "value", "tax", "cost", "discount", "result", "expenses", "purchases", "qty", "documents", "count", "short"];

// For these a rise is not good news, so the change is coloured the other way round.
const COST_KEYS = new Set(["purchases", "expenses", "cost", "discount", "short"]);

function pickKpis(data: ReportData): ReportColumn[] {
  const available = data.columns.filter((c) => data.totals[c.key] !== undefined && c.key !== "share");
  // Month-by-month reports read best in their own column order (sales, purchases, expenses…).
  if (data.columns[0]?.key === "period" && available.length <= 4) return available;
  const ordered = [...available].sort((a, b) => {
    const ia = KPI_ORDER.indexOf(a.key), ib = KPI_ORDER.indexOf(b.key);
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
  });
  const picked = ordered.slice(0, 3);
  const margin = data.columns.find((c) => c.key === "margin");
  return margin ? [...picked, margin] : ordered.slice(0, 4);
}

function shortRange(from: string, to: string) {
  const f = new Date(from + "T00:00:00"), t = new Date(to + "T00:00:00");
  const opts: Intl.DateTimeFormatOptions = { day: "numeric", month: "short", year: "numeric" };
  return `${f.toLocaleDateString("en-IN", opts)} – ${t.toLocaleDateString("en-IN", opts)}`;
}

function cellText(row: ReportRow, column: ReportColumn) {
  const value = row[column.key];
  return column.key === "period" ? periodLabel(String(value)) : formatValue(value, column.type);
}

export default function ReportViewer({ id }: { id: string }) {
  const { authentication } = useAuth();
  const presets = useMemo(() => periodPresets(), []);
  const [range, setRange] = useState({ from: presets[0].from, to: presets[0].to });
  const [compare, setCompare] = useState(true);
  const [sort, setSort] = useState<{ key: string; dir: 1 | -1 } | null>(null);
  const [filter, setFilter] = useState("");
  const [starred, setStarred] = useState(() => (typeof window === "undefined" ? false : favourites.list().includes(id)));
  const entry = findReport(id);
  const report = useReport(id, range.from, range.to, compare);
  const data = report.data;
  const business = authentication?.organization?.name ?? "";

  // Remember what was opened, for the "Recently opened" row on the hub.
  useEffect(() => recent.add(id), [id]);

  const rows = useMemo(() => {
    if (!data) return [];
    const term = filter.trim().toLowerCase();
    let list = term ? data.rows.filter((r) => data.columns.some((c) => (c.type === "text" || c.type === "date") && String(r[c.key] ?? "").toLowerCase().includes(term))) : data.rows;
    if (sort) {
      const column = data.columns.find((c) => c.key === sort.key);
      const numeric = column && column.type !== "text" && column.type !== "date";
      list = [...list].sort((a, b) => {
        const x = a[sort.key], y = b[sort.key];
        const cmp = numeric ? Number(x) - Number(y) : String(x ?? "").localeCompare(String(y ?? ""), "en-IN", { numeric: true });
        return cmp * sort.dir;
      });
    }
    return list;
  }, [data, filter, sort]);

  if (!entry) {
    return <div className="nx-card"><EmptyState icon={FileSpreadsheet} title="Report not found" description="This report link is not valid." action={<Link className="nx-button" href="/reports">All reports</Link>} /></div>;
  }

  const kpis = data ? pickKpis(data) : [];
  const activePreset = presets.find((p) => p.from === range.from && p.to === range.to)?.key;
  const fileName = `NexEase-${entry.title.replace(/[^A-Za-z0-9]+/g, "-")}-${data?.period.from ?? range.from}-to-${data?.period.to ?? range.to}`;

  function exportCsv() {
    if (!data) return;
    const columns = data.columns.map((c) => ({ header: c.label, value: (r: ReportRow) => (c.type === "percent" || c.type === "money" || c.type === "qty" ? String(r[c.key] ?? "") : r[c.key]) }));
    const totalRow = Object.fromEntries(data.columns.map((c, i) => [c.key, i === 0 ? "Total" : data.totals[c.key] ?? ""])) as ReportRow;
    void downloadCsv(fileName, [...rows, totalRow], columns).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  function share() {
    if (!data) return;
    const lines = [`${entry!.title}${business ? ` — ${business}` : ""}`, data.dated ? shortRange(data.period.from, data.period.to) : "Current stock", ""];
    for (const k of kpis) lines.push(`${k.label}: ${formatValue(data.totals[k.key], k.type)}`);
    const top = rows.slice(0, 5);
    const first = data.columns[0], money = data.columns.find((c) => c.type === "money");
    if (top.length && money && first.key !== "period") {
      lines.push("", "Top entries:");
      for (const r of top) lines.push(`• ${r[first.key]}: ${formatValue(r[money.key], "money")}`);
    }
    window.open(`https://wa.me/?text=${encodeURIComponent(lines.join("\n"))}`, "_blank", "noopener,noreferrer");
  }

  const toggleSort = (key: string) => setSort((s) => (s?.key === key ? (s.dir === -1 ? { key, dir: 1 } : null) : { key, dir: -1 }));
  const numeric = (c: ReportColumn) => c.type !== "text" && c.type !== "date";
  const primary = data?.columns.find((c) => c.type === "money") ?? data?.columns.find((c) => c.type === "qty");
  const [titleCol, subCol] = data ? data.columns.filter((c) => !numeric(c)) : [];

  return (
    <div className="nxl-screen nxr-print">
      <header className="nxl-header">
        <div className="min-w-0">
          <Link href="/reports" className="nxr-back nxr-noprint"><ArrowLeft size={15} aria-hidden="true" />Reports</Link>
          <h1>{entry.title}</h1>
          <p className="nx-muted">{data ? (data.dated ? shortRange(data.period.from, data.period.to) : "Current stock, all warehouses") : entry.description}{business ? ` · ${business}` : ""}</p>
        </div>
        <div className="nxl-toolbar nxr-noprint">
          <ActionIcon icon={Star} label={starred ? "Remove from favourites" : "Add to favourites"} onClick={() => setStarred(favourites.toggle(id).includes(id))} />
          <ActionIcon icon={FileSpreadsheet} label="Export CSV" onClick={exportCsv} disabled={!data?.rows.length} />
          <ActionIcon icon={Printer} label="Print or save as PDF" onClick={() => window.print()} disabled={!data} />
          <ActionIcon icon={MessageCircle} label="Share summary on WhatsApp" onClick={share} disabled={!data} />
          <ActionIcon icon={RefreshCw} label="Refresh report" onClick={() => void report.refetch()} busy={report.isFetching} />
        </div>
      </header>

      {data?.dated !== false ? (
        <section className="nxl-panel nxr-controls nxr-noprint" aria-label="Report period">
          <div className="nx-chip-row" role="group" aria-label="Period">
            {presets.map((p) => <button key={p.key} type="button" className="nx-chip" aria-pressed={activePreset === p.key} onClick={() => setRange({ from: p.from, to: p.to })}>{p.label}</button>)}
          </div>
          <div className="nxr-dates">
            <label>From<input type="date" className="nx-input" aria-label="From date" value={range.from} max={range.to} onChange={(e) => e.target.value && setRange((r) => ({ ...r, from: e.target.value }))} /></label>
            <label>To<input type="date" className="nx-input" aria-label="To date" value={range.to} min={range.from} onChange={(e) => e.target.value && setRange((r) => ({ ...r, to: e.target.value }))} /></label>
            <label className="nxr-compare"><input type="checkbox" checked={compare} onChange={(e) => setCompare(e.target.checked)} />Compare with previous period</label>
          </div>
        </section>
      ) : null}

      {report.error ? (
        <div role="alert" className="nxl-error nxl-panel">
          <span>{report.error.message}</span>
          <button type="button" className="nx-button nx-secondary nx-btn-sm" onClick={() => void report.refetch()}>Retry</button>
        </div>
      ) : !data ? (
        <div className="space-y-3" aria-busy="true" aria-label="Loading report"><div className="nx-skeleton h-24" /><div className="nx-skeleton h-64" /></div>
      ) : (
        <>
          {kpis.length ? (
            <div className="nxr-kpis" data-count={kpis.length}>
              {kpis.map((k) => {
                const delta = data.previous ? change(data.totals[k.key], data.previous.totals[k.key]) : null;
                const Trend = delta !== null && delta < 0 ? TrendingDown : TrendingUp;
                return (
                  <div key={k.key} className="nxr-kpi">
                    <span>{k.label}</span>
                    <strong>{formatValue(data.totals[k.key], k.type)}</strong>
                    {data.previous ? (
                      <em data-dir={delta === null || delta === 0 ? undefined : (delta > 0) !== COST_KEYS.has(k.key) ? "good" : "bad"}>
                        {delta === null ? "No earlier figure" : <><Trend size={13} aria-hidden="true" />{`${delta >= 0 ? "+" : ""}${delta.toFixed(1)}% vs previous`}</>}
                      </em>
                    ) : null}
                  </div>
                );
              })}
            </div>
          ) : null}

          {data.chart && data.rows.length ? <section className="nxl-panel nxr-chart-panel"><ReportChart chart={data.chart} rows={data.rows} columns={data.columns} title={entry.title} /></section> : null}

          <section className="nxl-panel">
            {data.rows.length > 8 ? (
              <div className="nxl-filters nxr-noprint">
                <label className="nxl-search"><Search size={16} aria-hidden="true" /><input type="search" aria-label="Filter rows" placeholder="Filter rows" value={filter} onChange={(e) => setFilter(e.target.value)} /></label>
              </div>
            ) : null}
            {!data.rows.length ? (
              <EmptyState icon={FileSpreadsheet} title="Nothing in this period" description={data.dated ? "Try a longer period, such as this financial year." : "No matching items right now."} />
            ) : (
              <>
                <div className="nxr-table-wrap">
                  <table className="nxr-table" aria-label={entry.title}>
                    <thead>
                      <tr>
                        {data.columns.map((c) => (
                          <th key={c.key} data-num={numeric(c) || undefined} aria-sort={sort?.key === c.key ? (sort.dir === 1 ? "ascending" : "descending") : undefined}>
                            <button type="button" onClick={() => toggleSort(c.key)}>
                              {c.label}
                              {sort?.key === c.key ? (sort.dir === 1 ? <ArrowUp size={12} aria-hidden="true" /> : <ArrowDown size={12} aria-hidden="true" />) : null}
                            </button>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((r, i) => (
                        <tr key={i}>{data.columns.map((c) => <td key={c.key} data-num={numeric(c) || undefined}>{cellText(r, c)}</td>)}</tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr>
                        {data.columns.map((c, i) => <td key={c.key} data-num={numeric(c) || undefined}>{i === 0 ? `Total · ${data.rows.length} row${data.rows.length === 1 ? "" : "s"}` : data.totals[c.key] !== undefined ? formatValue(data.totals[c.key], c.type) : ""}</td>)}
                      </tr>
                    </tfoot>
                  </table>
                </div>
                <ul className="nxr-cards" aria-label={`${entry.title} rows`}>
                  {rows.map((r, i) => (
                    <li key={i}>
                      <div>
                        <strong>{titleCol ? cellText(r, titleCol) : ""}</strong>
                        {subCol ? <span>{cellText(r, subCol)}</span> : null}
                        <dl>
                          {data.columns.filter((c) => numeric(c) && c !== primary).slice(0, 4).map((c) => <div key={c.key}><dt>{c.label}</dt><dd>{cellText(r, c)}</dd></div>)}
                        </dl>
                      </div>
                      {primary ? <b>{cellText(r, primary)}</b> : null}
                    </li>
                  ))}
                  {primary ? <li className="nxr-card-total"><strong>Total · {data.rows.length} rows</strong><b>{formatValue(data.totals[primary.key], primary.type)}</b></li> : null}
                </ul>
              </>
            )}
          </section>

          {data.notes.length ? <ul className="nxr-notes">{data.notes.map((n) => <li key={n}>{n}</li>)}</ul> : null}
        </>
      )}
    </div>
  );
}

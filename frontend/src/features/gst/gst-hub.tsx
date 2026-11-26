"use client";

import Link from "next/link";
import { Suspense, useMemo, useRef, useState, type ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, ArrowRight, BadgeCheck, CalendarClock, Check, CircleSlash, Clock3, Download, FileSpreadsheet, FileUp, Info, Landmark, Link2, ListChecks, ReceiptIndianRupee, RefreshCw, Scale, Sparkles, X } from "lucide-react";
import { Badge, type Tone } from "@/components/ui/badge";
import StatCard from "@/components/ui/stat-card";
import { useAuth } from "@/features/auth/auth-context";
import GstSourceReview from "@/features/business/gst-source-review";
import BusinessWorkspace, { exportWorkbook } from "@/features/business/workspace";
import { downloadBlob } from "@/lib/browser/download";
import { hasPermission } from "@/lib/authorization/permissions";
import { formatDate } from "@/lib/format";
import {
  ACTION_LABEL, MATCH_LABEL, inr, lastMonth, periodLabel, portalChecklist, taxOf, useGstr1, useGstr3b, useImport, useIms, useImsAction, useLinkBill, useOverview,
  type ImsAction, type InwardRecord, type MatchStatus,
} from "./api";

const TABS = [
  { key: "overview", label: "Overview", icon: Landmark },
  { key: "ims", label: "IMS inbox", icon: ListChecks },
  { key: "reconcile", label: "Reconciliation", icon: Scale },
  { key: "gstr1", label: "GSTR-1", icon: FileSpreadsheet },
  { key: "gstr3b", label: "GSTR-3B", icon: ReceiptIndianRupee },
  { key: "settings", label: "Register & settings", icon: BadgeCheck },
] as const;
type Tab = (typeof TABS)[number]["key"];

const ACTION_TONE: Record<ImsAction, Tone> = { accept: "success", reject: "danger", pending: "warning", none: "neutral" };
const MATCH_TONE: Record<MatchStatus, Tone> = { matched: "success", date_mismatch: "info", mismatch: "warning", only_in_2b: "danger", note: "violet" };

function daysUntil(day: string) {
  const ms = new Date(day + "T00:00:00").getTime() - new Date(new Date().toDateString()).getTime();
  return Math.round(ms / 86_400_000);
}

function State({ loading, error, onRetry, children }: { loading: boolean; error: unknown; onRetry: () => void; children: ReactNode }) {
  if (loading) return <div className="nxg-skeleton" aria-label="Loading"><i /><i /><i /></div>;
  if (error) return <div className="nxg-error" role="alert">{(error as Error).message || "Could not load."}<button type="button" onClick={onRetry}><RefreshCw size={14} />Try again</button></div>;
  return <>{children}</>;
}

function TaxTable({ rows, first, count = false }: { rows: { key: string; label: ReactNode; taxable?: string; igst: string; cgst: string; sgst: string; cess?: string; count?: number }[]; first: string; count?: boolean }) {
  return (
    <div className="nxg-table-wrap">
      <table className="nxg-table">
        <thead><tr><th>{first}</th>{count ? <th className="num">Docs</th> : null}<th className="num">Taxable value</th><th className="num">IGST</th><th className="num">CGST</th><th className="num">SGST/UTGST</th><th className="num">Cess</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key}><td>{r.label}</td>{count ? <td className="num">{r.count ?? 0}</td> : null}<td className="num">{r.taxable === undefined ? "" : inr(r.taxable)}</td><td className="num">{inr(r.igst)}</td><td className="num">{inr(r.cgst)}</td><td className="num">{inr(r.sgst)}</td><td className="num">{inr(r.cess ?? "0")}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------
// Overview
// ---------------------------------------------------------------------------------------------

function OverviewPanel({ period, go }: { period: string; go: (tab: Tab) => void }) {
  const q = useOverview(period);
  const d = q.data;
  return (
    <State loading={q.isPending} error={q.error} onRetry={() => void q.refetch()}>
      {d ? (
        <div className="nxg-stack">
          {d.alerts.length ? (
            <ul className="nxg-alerts">
              {d.alerts.map((a) => (
                <li key={a.text} data-tone={a.tone}>
                  {a.tone === "info" ? <Info size={16} /> : <AlertTriangle size={16} />}
                  <span>{a.text}</span>
                  <button type="button" onClick={() => go((new URLSearchParams(a.href.split("?")[1] ?? "").get("tab") as Tab) || "overview")}>Open<ArrowRight size={14} /></button>
                </li>
              ))}
            </ul>
          ) : <p className="nxg-ok"><BadgeCheck size={16} />Nothing needs your attention for {periodLabel(period)}.</p>}
          <div className="nx-kpi-strip" data-cols="4">
            <StatCard label="Output tax" value={inr(taxOf(d.gstr3b.liability))} hint="Sales less credit notes, plus reverse charge" icon={ReceiptIndianRupee} />
            <StatCard label="ITC available" value={inr(taxOf(d.gstr3b.itc))} hint="From GSTR-2B after reversals" icon={BadgeCheck} tone="success" />
            <StatCard label="Cash to pay" value={inr(taxOf(d.gstr3b.cash))} hint="After using ITC in the legal order" icon={Landmark} tone={taxOf(d.gstr3b.cash) > 0 ? "warning" : "success"} />
            <StatCard label="IMS: no action" value={String(d.ims.none)} hint={`${d.ims.accept} accepted · ${d.ims.pending} pending · ${d.ims.reject} rejected`} icon={ListChecks} tone={d.ims.none ? "warning" : "neutral"} />
          </div>
          <div className="nxg-grid2">
            <section className="nxg-card">
              <h3><CalendarClock size={17} />Due dates for {periodLabel(period)}</h3>
              <ol className="nxg-timeline">
                {d.deadlines.map((x) => {
                  const left = daysUntil(x.date);
                  return (
                    <li key={x.key} data-state={left < 0 ? "past" : left <= 3 ? "soon" : "later"}>
                      <div><strong>{x.label}</strong><span>{x.note}</span></div>
                      <div className="nxg-date"><b>{formatDate(x.date)}</b><small>{left < 0 ? `${-left} days ago` : left === 0 ? "Today" : `in ${left} days`}</small></div>
                    </li>
                  );
                })}
              </ol>
            </section>
            <section className="nxg-card">
              <h3><Scale size={17} />Purchases vs GSTR-2B</h3>
              <dl className="nxg-counts">
                {(Object.keys(MATCH_LABEL) as MatchStatus[]).map((k) => <div key={k}><dt><Badge tone={MATCH_TONE[k]}>{MATCH_LABEL[k]}</Badge></dt><dd>{d.reconciliation[k] ?? 0}</dd></div>)}
                <div><dt><Badge tone="warning">In books, not in GSTR-2B</Badge></dt><dd>{d.missing_in_2b}</dd></div>
              </dl>
              <div className="nxg-actions">
                <button type="button" className="nx-button" onClick={() => go("ims")}><FileUp size={16} />Upload GSTR-2B</button>
                <button type="button" className="nx-button nx-secondary" onClick={() => go("reconcile")}>Open reconciliation</button>
              </div>
            </section>
          </div>
          <section className="nxg-card">
            <h3><FileSpreadsheet size={17} />GSTR-1 at a glance</h3>
            <TaxTable first="Table" count rows={d.gstr1.tables.map((t, i) => ({ ...t, key: String(i), label: <><b>{t.table}</b> {t.label}</> }))} />
            <p className="nxg-muted">Invoices {d.gstr1.documents.from || "—"} to {d.gstr1.documents.to || "—"} · {d.gstr1.documents.issued} issued · {d.gstr1.documents.cancelled} cancelled</p>
          </section>
        </div>
      ) : null}
    </State>
  );
}

// ---------------------------------------------------------------------------------------------
// IMS inbox
// ---------------------------------------------------------------------------------------------

function ImsPanel({ period, canManage }: { period: string; canManage: boolean }) {
  const q = useIms(period);
  const act = useImsAction();
  const upload = useImport();
  const link = useLinkBill();
  const fileRef = useRef<HTMLInputElement>(null);
  const [filter, setFilter] = useState<ImsAction | "all">("all");
  const [match, setMatch] = useState<MatchStatus | "">("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [open, setOpen] = useState<string | null>(null);
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const [reduce, setReduce] = useState<Record<string, string>>({});

  const all = useMemo(() => q.data?.records ?? [], [q.data]);
  const rows = useMemo(() => all.filter((r) => (filter === "all" || r.action === filter) && (!match || r.match.status === match)
    && (!search || (r.supplier_name + " " + r.supplier_gstin + " " + r.doc_number).toLowerCase().includes(search.toLowerCase()))), [all, filter, match, search]);
  const counts = useMemo(() => all.reduce((c, r) => ({ ...c, [r.action]: (c[r.action] ?? 0) + 1 }), {} as Record<string, number>), [all]);
  const actionable = rows.filter((r) => !r.rcm);
  const chosen = actionable.filter((r) => selected.has(r.id));

  function toggle(id: string) {
    setSelected((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  }

  async function run(ids: string[], action: ImsAction, extra: { reason?: string; itc_reduce?: string } = {}) {
    if (!ids.length) return;
    // The API layer shows the success or error message.
    try {
      await act.mutateAsync({ ids, action, ...extra });
      setSelected(new Set()); setRejecting(false); setReason("");
    } catch {
      /* message already shown */
    }
  }

  async function applySuggestions() {
    const target = (chosen.length ? chosen : actionable.filter((r) => r.action === "none")).filter((r) => r.suggested !== "none");
    const groups: Partial<Record<ImsAction, string[]>> = {};
    for (const r of target) (groups[r.suggested] ??= []).push(r.id);
    for (const [action, ids] of Object.entries(groups) as [ImsAction, string[]][]) {
      await run(ids, action, action === "pending" ? { reason: "Needs checking against books (NexEase suggestion)" } : {});
    }
  }

  async function onFile(file?: File) {
    if (!file) return;
    try {
      await upload.mutateAsync({ file, period });
    } catch {
      /* message already shown */
    } finally {
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <div className="nxg-stack">
      <section className="nxg-card nxg-upload">
        <div>
          <h3><FileUp size={17} />Bring in supplier documents</h3>
          <p className="nxg-muted">On the GST portal open <b>Returns → GSTR-2B</b> (or IMS) for {periodLabel(period)}, download the <b>JSON</b>, and upload it here. You can also fill the CSV template. Re-uploading refreshes amounts and keeps your decisions.</p>
        </div>
        {canManage ? (
          <div className="nxg-actions">
            <input ref={fileRef} type="file" hidden accept=".json,.csv,application/json,text/csv" aria-label="GSTR-2B JSON or CSV" onChange={(e) => void onFile(e.target.files?.[0])} />
            <button type="button" className="nx-button" disabled={upload.isPending} onClick={() => fileRef.current?.click()}><FileUp size={16} />{upload.isPending ? "Uploading…" : "Upload JSON / CSV"}</button>
            <button type="button" className="nx-button nx-secondary" onClick={() => void exportWorkbook("/business/gst/ims/template/", "NexEase-IMS-template.csv")}><Download size={16} />CSV template</button>
          </div>
        ) : null}
      </section>

      <div className="nxg-toolbar">
        <div className="nxg-chips" role="tablist" aria-label="Filter by IMS action">
          {(["all", "none", "accept", "pending", "reject"] as const).map((k) => (
            <button key={k} type="button" role="tab" aria-selected={filter === k} onClick={() => setFilter(k)}>{k === "all" ? "All" : ACTION_LABEL[k]}<span>{k === "all" ? all.length : counts[k] ?? 0}</span></button>
          ))}
        </div>
        <select aria-label="Filter by match" value={match} onChange={(e) => setMatch(e.target.value as MatchStatus | "")}>
          <option value="">Any match status</option>
          {(Object.keys(MATCH_LABEL) as MatchStatus[]).map((k) => <option key={k} value={k}>{MATCH_LABEL[k]}</option>)}
        </select>
        <input className="nxg-search" aria-label="Search supplier or number" placeholder="Search supplier, GSTIN, number" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      {canManage && actionable.length ? (
        <div className="nxg-bulk" data-active={chosen.length > 0 || undefined}>
          <label><input type="checkbox" aria-label="Select all shown" checked={chosen.length > 0 && chosen.length === actionable.length} onChange={(e) => setSelected(e.target.checked ? new Set(actionable.map((r) => r.id)) : new Set())} />{chosen.length ? `${chosen.length} selected` : "Select"}</label>
          <button type="button" disabled={!chosen.length || act.isPending} onClick={() => void run(chosen.map((r) => r.id), "accept")}><Check size={15} />Accept</button>
          <button type="button" disabled={!chosen.length || act.isPending} onClick={() => void run(chosen.map((r) => r.id), "pending", { reason: "Kept pending for review" })}><Clock3 size={15} />Pending</button>
          <button type="button" disabled={!chosen.length || act.isPending} onClick={() => setRejecting(true)}><CircleSlash size={15} />Reject</button>
          <button type="button" disabled={act.isPending} onClick={() => void applySuggestions()} title="Accept matches, keep differences pending"><Sparkles size={15} />Apply suggestions{chosen.length ? "" : " to no-action"}</button>
          <button type="button" onClick={() => void downloadBlob(new Blob([portalChecklist(all)], { type: "text/csv" }), `IMS-actions-${period}.csv`)}><Download size={15} />Portal checklist</button>
          {rejecting ? (
            <form className="nxg-reason" onSubmit={(e) => { e.preventDefault(); void run(chosen.map((r) => r.id), "reject", { reason }); }}>
              <input autoFocus aria-label="Reason for rejecting" placeholder="Reason (e.g. goods not received, wrong GSTIN)" value={reason} onChange={(e) => setReason(e.target.value)} />
              <button type="submit" disabled={!reason.trim()}>Reject {chosen.length}</button>
              <button type="button" aria-label="Cancel reject" onClick={() => setRejecting(false)}><X size={15} /></button>
            </form>
          ) : null}
        </div>
      ) : null}

      <State loading={q.isPending} error={q.error} onRetry={() => void q.refetch()}>
        {rows.length === 0 ? (
          <div className="nxg-empty"><ListChecks size={26} /><p>{all.length ? "No documents match these filters." : `No supplier documents for ${periodLabel(period)} yet. Upload the GSTR-2B JSON to begin.`}</p></div>
        ) : (
          <ul className="nxg-ims">
            {rows.map((r) => (
              <li key={r.id} data-open={open === r.id || undefined}>
                <div className="nxg-ims-row">
                  {canManage && !r.rcm ? <input type="checkbox" aria-label={`Select ${r.doc_number}`} checked={selected.has(r.id)} onChange={() => toggle(r.id)} /> : <span className="nxg-gap" />}
                  <button type="button" className="nxg-ims-main" aria-expanded={open === r.id} onClick={() => setOpen(open === r.id ? null : r.id)}>
                    <span className="nxg-ims-who"><strong>{r.supplier_name || r.supplier_gstin}</strong><small>{r.supplier_gstin} · {r.doc_type === "INV" ? "Invoice" : r.doc_type === "CN" ? "Credit note" : "Debit note"} {r.doc_number} · {formatDate(r.doc_date)}</small></span>
                    <span className="nxg-ims-tags">
                      {r.rcm ? <Badge tone="violet">Reverse charge</Badge> : <Badge tone={MATCH_TONE[r.match.status]}>{MATCH_LABEL[r.match.status]}</Badge>}
                      <Badge tone={ACTION_TONE[r.action]}>{r.rcm ? "Not in IMS" : ACTION_LABEL[r.action]}</Badge>
                    </span>
                    <span className="nxg-ims-amt"><strong>{inr(r.total_tax)}</strong><small>on {inr(r.taxable)}</small></span>
                  </button>
                </div>
                {open === r.id ? (
                  <div className="nxg-ims-detail">
                    <dl className="nxg-heads">{(["taxable", "igst", "cgst", "sgst", "cess"] as const).map((k) => <div key={k}><dt>{k === "taxable" ? "Taxable" : k.toUpperCase()}</dt><dd>{inr(r[k])}</dd></div>)}</dl>
                    {r.match.bill ? <p className="nxg-muted"><Link2 size={14} />Purchase bill <Link href={`/vendor-bills?view=${r.match.bill.id}`}>{r.match.bill.number}</Link> (supplier no. {r.match.bill.supplier_invoice}, {formatDate(r.match.bill.date)}) · tax {inr(r.match.bill.total_tax)}</p> : null}
                    {r.match.differences.length ? (
                      <table className="nxg-table nxg-diff"><thead><tr><th>Field</th><th className="num">GSTR-2B</th><th className="num">Your books</th><th className="num">Difference</th></tr></thead>
                        <tbody>{r.match.differences.map((x) => <tr key={x.field}><td>{x.field === "taxable" ? "Taxable" : x.field.toUpperCase()}</td><td className="num">{x.field === "date" ? formatDate(x.portal) : inr(x.portal)}</td><td className="num">{x.field === "date" ? formatDate(x.books) : inr(x.books)}</td><td className="num">{x.difference ? inr(x.difference) : ""}</td></tr>)}</tbody></table>
                    ) : null}
                    <p className="nxg-suggest"><Sparkles size={14} />{r.suggestion}</p>
                    {r.reason ? <p className="nxg-muted">Reason recorded: {r.reason}</p> : null}
                    {r.itc_reduce ? <p className="nxg-muted">ITC to reduce declared: {inr(r.itc_reduce)}</p> : null}
                    {canManage && !r.rcm ? (
                      <div className="nxg-actions">
                        {r.doc_type === "CN" ? <label className="nxg-reduce">ITC to reduce<input type="number" min="0" max={r.total_tax} step="0.01" placeholder={r.total_tax} value={reduce[r.id] ?? ""} onChange={(e) => setReduce((x) => ({ ...x, [r.id]: e.target.value }))} /></label> : null}
                        <button type="button" className="nx-button" disabled={act.isPending} onClick={() => void run([r.id], "accept", r.doc_type === "CN" && reduce[r.id] ? { itc_reduce: reduce[r.id] } : {})}>Accept</button>
                        <button type="button" className="nx-button nx-secondary" disabled={act.isPending} onClick={() => void run([r.id], "pending", { reason: "Kept pending for review" })}>Keep pending</button>
                        <button type="button" className="nx-button nx-secondary" disabled={act.isPending} onClick={() => { setSelected(new Set([r.id])); setRejecting(true); }}>Reject…</button>
                        {r.action !== "none" ? <button type="button" className="nxg-link" onClick={() => void run([r.id], "none")}>Clear action</button> : null}
                        {r.match.bill ? <button type="button" className="nxg-link" onClick={() => void link.mutateAsync({ record_id: r.id, bill_id: "" }).catch(() => {})}>Unlink bill</button> : null}
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </State>
      <p className="nxg-fine">NexEase does not change anything on the GST portal. After deciding here, take the same actions in IMS on the portal (the portal checklist lists them), then recompute GSTR-2B if it was already generated.</p>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------
// Reconciliation
// ---------------------------------------------------------------------------------------------

function ReconcilePanel({ period, canManage }: { period: string; canManage: boolean }) {
  const q = useIms(period);
  const link = useLinkBill();
  const [linking, setLinking] = useState<string | null>(null);
  const records = useMemo(() => q.data?.records ?? [], [q.data]);
  const by = (s: MatchStatus) => records.filter((r) => r.match.status === s && !r.rcm);
  const missing = q.data?.missing_in_2b ?? [];
  const portalTax = records.filter((r) => !r.rcm && r.doc_type !== "CN").reduce((s, r) => s + Number(r.total_tax), 0) - records.filter((r) => r.doc_type === "CN").reduce((s, r) => s + Number(r.total_tax), 0);
  const booksTax = records.reduce((s, r) => s + Number(r.match.bill?.total_tax ?? 0), 0) + missing.reduce((s, b) => s + Number(b.total_tax), 0);

  async function connect(recordId: string, billId: string) {
    try {
      await link.mutateAsync({ record_id: recordId, bill_id: billId });
      setLinking(null);
    } catch {
      /* message already shown */
    }
  }

  const issues: { title: string; tone: Tone; rows: InwardRecord[]; help: string }[] = [
    { title: "Amounts differ", tone: "warning", rows: by("mismatch"), help: "Ask the supplier to amend in GSTR-1A, or correct your bill. Keep these pending meanwhile." },
    { title: "In GSTR-2B but not in your books", tone: "danger", rows: by("only_in_2b"), help: "Record the purchase bill if it is yours, or reject it in IMS if it is not." },
    { title: "Dates differ", tone: "info", rows: by("date_mismatch"), help: "Amounts match. Check the bill date so your registers agree." },
  ];

  return (
    <State loading={q.isPending} error={q.error} onRetry={() => void q.refetch()}>
      <div className="nxg-stack">
        <div className="nx-kpi-strip" data-cols="4">
          <StatCard label="Matched" value={String(by("matched").length)} icon={BadgeCheck} tone="success" />
          <StatCard label="Need attention" value={String(by("mismatch").length + by("only_in_2b").length + by("date_mismatch").length)} icon={AlertTriangle} tone="warning" />
          <StatCard label="Not in GSTR-2B" value={String(missing.length)} hint="Supplier has not reported these" icon={Clock3} tone={missing.length ? "danger" : "neutral"} />
          <StatCard label="Tax: 2B vs books" value={inr(portalTax - booksTax)} hint={`${inr(portalTax)} in 2B · ${inr(booksTax)} in books`} icon={Scale} />
        </div>
        {issues.map((g) => g.rows.length ? (
          <section key={g.title} className="nxg-card">
            <h3><Badge tone={g.tone}>{g.rows.length}</Badge>{g.title}</h3>
            <p className="nxg-muted">{g.help}</p>
            <div className="nxg-table-wrap">
              <table className="nxg-table">
                <thead><tr><th>Supplier</th><th>Document</th><th className="num">Tax in 2B</th><th className="num">Tax in books</th><th>Difference</th>{canManage ? <th /> : null}</tr></thead>
                <tbody>
                  {g.rows.map((r) => (
                    <tr key={r.id}>
                      <td><strong>{r.supplier_name}</strong><small className="nxg-block">{r.supplier_gstin}</small></td>
                      <td>{r.doc_number}<small className="nxg-block">{formatDate(r.doc_date)}</small></td>
                      <td className="num">{inr(r.total_tax)}</td>
                      <td className="num">{r.match.bill ? inr(r.match.bill.total_tax) : "—"}</td>
                      <td>{r.match.differences.map((d) => `${d.field === "taxable" ? "Taxable" : d.field.toUpperCase()} ${d.difference ? inr(d.difference) : formatDate(d.books)}`).join(" · ") || "—"}</td>
                      {canManage ? (
                        <td>
                          {r.match.status === "only_in_2b" && missing.length ? (linking === r.id ? (
                            <select aria-label={`Link ${r.doc_number} to a bill`} defaultValue="" onChange={(e) => e.target.value && void connect(r.id, e.target.value)}>
                              <option value="">Choose bill…</option>
                              {missing.map((b) => <option key={b.id} value={b.id}>{b.bill_number} · {b.supplier_name} · {inr(b.total_tax)}</option>)}
                            </select>
                          ) : <button type="button" className="nxg-link" onClick={() => setLinking(r.id)}><Link2 size={14} />Link bill</button>) : null}
                        </td>
                      ) : null}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null)}
        <section className="nxg-card">
          <h3><Badge tone="warning">{missing.length}</Badge>In your books but not in GSTR-2B</h3>
          <p className="nxg-muted">You cannot claim ITC on these until the supplier reports them in GSTR-1 (Rule 36(4)). Remind the supplier; the credit can be claimed in a later month up to the Section 16(4) deadline.</p>
          {missing.length ? (
            <div className="nxg-table-wrap"><table className="nxg-table"><thead><tr><th>Supplier</th><th>Bill</th><th>Date</th><th className="num">Taxable</th><th className="num">Tax</th></tr></thead>
              <tbody>{missing.map((b) => <tr key={b.id}><td><strong>{b.supplier_name}</strong><small className="nxg-block">{b.supplier_gstin || "No GSTIN on bill"}</small></td><td><Link href={`/vendor-bills?view=${b.id}`}>{b.bill_number}</Link><small className="nxg-block">{b.number}</small></td><td>{formatDate(b.date)}</td><td className="num">{inr(b.taxable)}</td><td className="num">{inr(b.total_tax)}</td></tr>)}</tbody></table></div>
          ) : <p className="nxg-ok"><BadgeCheck size={16} />Every purchase bill of {periodLabel(period)} is in GSTR-2B.</p>}
        </section>
      </div>
    </State>
  );
}

// ---------------------------------------------------------------------------------------------
// Returns
// ---------------------------------------------------------------------------------------------

function Gstr1Panel({ period }: { period: string }) {
  const q = useGstr1(period);
  const d = q.data;
  return (
    <State loading={q.isPending} error={q.error} onRetry={() => void q.refetch()}>
      {d ? (
        <div className="nxg-stack">
          <div className="nxg-head-row">
            <p className="nxg-muted">Sales from {formatDate(d.from)} to {formatDate(d.to)}. File on the GST portal by the due date; GSTR-1 fills Table 3 of GSTR-3B automatically.</p>
            <button type="button" className="nx-button nx-secondary" onClick={() => void exportWorkbook(`/business/gst/returns/gstr1/?period=${period}&format=xlsx`, `NexEase-GSTR1-${period}.xlsx`)}><Download size={16} />Excel</button>
          </div>
          {d.review_count ? <p className="nxg-warn"><AlertTriangle size={15} />{d.review_count} invoices have no reviewed GST classification. They are included using the tax on the invoice; review them in Sales.</p> : null}
          <section className="nxg-card"><h3>Summary by table</h3><TaxTable first="Table" count rows={d.tables.map((t, i) => ({ ...t, key: String(i), label: <><b>{t.table}</b> {t.label}</> }))} /></section>
          {d.b2cs.length ? <section className="nxg-card"><h3>Table 7: B2C others by place of supply and rate</h3><TaxTable first="Place of supply · rate" rows={d.b2cs.map((r) => ({ key: r.pos + r.rate, label: `${r.pos} ${r.state} · ${r.rate}%`, ...r }))} /></section> : null}
          <section className="nxg-card">
            <h3>Table 12: HSN / SAC summary</h3>
            <div className="nxg-table-wrap"><table className="nxg-table"><thead><tr><th>Section</th><th>HSN / SAC</th><th className="num">Rate</th><th className="num">Quantity</th><th className="num">Taxable value</th><th className="num">Tax</th></tr></thead>
              <tbody>{d.hsn.length ? d.hsn.map((r) => <tr key={r.section + r.hsn + r.rate} data-warn={r.hsn === "—" || undefined}><td>{r.section}</td><td>{r.hsn === "—" ? "Missing HSN" : r.hsn}</td><td className="num">{r.rate}%</td><td className="num">{r.quantity}</td><td className="num">{inr(r.taxable)}</td><td className="num">{inr(r.tax)}</td></tr>) : <tr><td colSpan={6}>No sales in this period.</td></tr>}</tbody></table></div>
          </section>
          <section className="nxg-card"><h3>Table 13: Documents issued</h3><p>Invoices {d.documents.from || "—"} to {d.documents.to || "—"} · <b>{d.documents.issued}</b> issued · <b>{d.documents.cancelled}</b> cancelled · <b>{d.documents.issued - d.documents.cancelled}</b> net</p></section>
        </div>
      ) : null}
    </State>
  );
}

function Gstr3bPanel({ period }: { period: string }) {
  const q = useGstr3b(period);
  const d = q.data;
  const heads = ["igst", "cgst", "sgst", "cess"] as const;
  return (
    <State loading={q.isPending} error={q.error} onRetry={() => void q.refetch()}>
      {d ? (
        <div className="nxg-stack">
          <div className="nxg-head-row">
            <p className="nxg-muted">{d.periods.length > 1 ? `Quarter ${formatDate(d.from)} to ${formatDate(d.to)}` : periodLabel(period)} · IMS: {d.ims_counts.accept} accepted, {d.ims_counts.none} no action (counted as accepted), {d.ims_counts.pending} pending, {d.ims_counts.reject} rejected.</p>
            <button type="button" className="nx-button nx-secondary" onClick={() => void exportWorkbook(`/business/gst/returns/gstr3b/?period=${period}&format=xlsx`, `NexEase-GSTR3B-${period}.xlsx`)}><Download size={16} />Excel</button>
          </div>
          <div className="nx-kpi-strip" data-cols="3">
            <StatCard label="Tax liability" value={inr(taxOf(d.liability))} icon={ReceiptIndianRupee} />
            <StatCard label="Net ITC" value={inr(taxOf(d.table_4.net))} hint={`Books show ${inr(taxOf({ ...d.table_4.books, cess: "0" }))}`} icon={BadgeCheck} tone="success" />
            <StatCard label="Cash to pay" value={inr(taxOf(d.payment.cash))} icon={Landmark} tone={taxOf(d.payment.cash) ? "warning" : "success"} />
          </div>
          <section className="nxg-card"><h3>3.1 Outward supplies and reverse charge</h3><TaxTable first="Row" rows={d.table_3_1.map((r) => ({ ...r, key: r.row!, label: <><b>{r.row}</b> {r.label}</> }))} /></section>
          {d.table_3_2.length ? (
            <section className="nxg-card"><h3>3.2 Inter-state supplies to unregistered persons</h3>
              <div className="nxg-table-wrap"><table className="nxg-table"><thead><tr><th>Place of supply</th><th className="num">Taxable value</th><th className="num">IGST</th></tr></thead><tbody>{d.table_3_2.map((r) => <tr key={r.pos}><td>{r.pos} {r.state}</td><td className="num">{inr(r.taxable)}</td><td className="num">{inr(r.igst)}</td></tr>)}</tbody></table></div>
            </section>
          ) : null}
          <section className="nxg-card">
            <h3>4 Eligible ITC</h3>
            <TaxTable first="Row" rows={[
              { key: "a3", label: <><b>4(A)(3)</b> Inward supplies liable to reverse charge</>, ...d.table_4.a3_reverse_charge },
              { key: "a5", label: <><b>4(A)(5)</b> All other ITC (from GSTR-2B)</>, ...d.table_4.a5_all_other_itc },
              { key: "b2", label: <><b>4(B)(2)</b> Reversal: unpaid over 180 days (Rule 37)</>, ...d.table_4.b2_rule37_reversal },
              { key: "net", label: <b>Net ITC (excluding reverse charge)</b>, ...d.table_4.net },
              { key: "books", label: <span className="nxg-muted">For comparison: ITC in your purchase books</span>, ...d.table_4.books, cess: "0" },
            ]} />
            {d.rule37_bills.length ? (
              <details className="nxg-details"><summary>{d.rule37_bills.length} unpaid bills older than 180 days</summary>
                <ul>{d.rule37_bills.map((b) => <li key={b.id}><Link href={`/vendor-bills?view=${b.id}`}>{b.number}</Link> · {b.supplier} · {formatDate(b.date)} · due {inr(b.balance)} · ITC {inr(b.itc)}</li>)}</ul>
              </details>
            ) : null}
          </section>
          <section className="nxg-card">
            <h3>6.1 Payment of tax</h3>
            <div className="nxg-table-wrap"><table className="nxg-table"><thead><tr><th>Head</th><th className="num">Liability</th><th className="num">Paid by ITC</th><th className="num">Cash to pay</th><th className="num">ITC carried forward</th></tr></thead>
              <tbody>{heads.map((h) => {
                const viaItc = d.payment.utilised.filter((u) => u.against === h).reduce((s, u) => s + Number(u.amount), 0);
                return <tr key={h}><td>{h.toUpperCase()}</td><td className="num">{inr(d.liability[h])}</td><td className="num">{inr(viaItc)}</td><td className="num"><b>{inr(d.payment.cash[h])}</b></td><td className="num">{inr(d.payment.carry_forward[h])}</td></tr>;
              })}</tbody></table></div>
            {d.payment.utilised.length ? <p className="nxg-muted">ITC used in the legal order: {d.payment.utilised.map((u) => `${u.credit.toUpperCase()} → ${u.against.toUpperCase()} ${inr(u.amount)}`).join(" · ")}</p> : null}
          </section>
          <ul className="nxg-notes">{d.notes.map((n) => <li key={n}><Info size={14} />{n}</li>)}</ul>
        </div>
      ) : null}
    </State>
  );
}

function SettingsPanel() {
  return (
    <div className="nxg-stack">
      <div className="nxg-head-row"><p className="nxg-muted">Your GST registration drives due dates, CGST/SGST vs IGST and the GSTR-2B check. The review register keeps manual GST classifications.</p><Link className="nx-button nx-secondary" href="/taxation/workpapers"><FileSpreadsheet size={16} />Tax workpapers</Link></div>
      <BusinessWorkspace kinds={["gst_settings", "gst_adjustments"]} title="GST registration & review register" description="Registration details and reviewed tax classifications." />
      <GstSourceReview />
    </div>
  );
}

// ---------------------------------------------------------------------------------------------
// Hub
// ---------------------------------------------------------------------------------------------

function Hub() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const { authentication } = useAuth();
  const canManage = hasPermission(authentication?.role.permissions ?? [], "taxation.manage");
  const tab = (TABS.some((t) => t.key === params.get("tab")) ? params.get("tab") : "overview") as Tab;
  const period = /^\d{4}-\d{2}$/.test(params.get("period") ?? "") ? params.get("period")! : lastMonth();
  const reg = useOverview(period).data?.registration;

  function set(next: { tab?: Tab; period?: string }) {
    const p = new URLSearchParams(params.toString());
    if (next.tab) p.set("tab", next.tab);
    if (next.period) p.set("period", next.period);
    router.replace(`${pathname}?${p.toString()}`, { scroll: false });
  }

  return (
    <div className="nxl-screen nxg">
      <header className="nxl-header">
        <div className="min-w-0">
          <h1>GST &amp; taxation</h1>
          <p className="nx-muted">{reg?.configured ? `${reg.gstin} · ${reg.legal_name} · ${reg.frequency === "quarterly" ? "Quarterly (QRMP)" : "Monthly"} returns` : "IMS, GSTR-2B reconciliation, GSTR-1 and GSTR-3B in one place"}</p>
        </div>
        <label className="nxg-period nxr-keep">Tax period<input type="month" value={period} max={new Date().toISOString().slice(0, 7)} onChange={(e) => e.target.value && set({ period: e.target.value })} /></label>
      </header>
      <nav className="nxg-tabs" role="tablist" aria-label="Taxation sections">
        {TABS.map((t) => <button key={t.key} type="button" role="tab" aria-selected={tab === t.key} onClick={() => set({ tab: t.key })}><t.icon size={16} />{t.label}</button>)}
      </nav>
      {tab === "overview" ? <OverviewPanel period={period} go={(t) => set({ tab: t })} /> : null}
      {tab === "ims" ? <ImsPanel period={period} canManage={canManage} /> : null}
      {tab === "reconcile" ? <ReconcilePanel period={period} canManage={canManage} /> : null}
      {tab === "gstr1" ? <Gstr1Panel period={period} /> : null}
      {tab === "gstr3b" ? <Gstr3bPanel period={period} /> : null}
      {tab === "settings" ? <SettingsPanel /> : null}
    </div>
  );
}

/** useSearchParams needs a Suspense boundary for the static export used by the mobile build. */
export default function GstHub() {
  return <Suspense fallback={<div className="nxg-skeleton"><i /><i /></div>}><Hub /></Suspense>;
}

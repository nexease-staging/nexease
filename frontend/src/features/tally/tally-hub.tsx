"use client";

import Link from "next/link";
import { Suspense, useEffect, useMemo, useState, type ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  AlertTriangle, ArrowDownUp, BookOpen, Boxes, Check, CheckCircle2, CircleDot, Copy, Download, FileSpreadsheet, HandCoins, Landmark, Laptop, Link2, MessageCircle,
  Package, PauseCircle, PlayCircle, Plug, ReceiptIndianRupee, RefreshCw, Search, Settings2, ShoppingCart, Users, Wallet, X,
} from "lucide-react";
import { Badge, type Tone } from "@/components/ui/badge";
import StatCard from "@/components/ui/stat-card";
import { exportWorkbook } from "@/features/business/workspace";
import ReportChart from "@/features/reports/components/report-chart";
import { formatDate } from "@/lib/format";
import {
  MAPPING_LABELS, WRITE_LABELS, ago, exportPath, fyStart, inr, today, useCompany, useDaybook, useIssues, useJobs, useOverview, usePair, useParties,
  useRegister, useResync, useRetryIssues, useRetryJob, useRevoke, useSaveSettings, useSettings, useStatement, useStatus, useStock, useTrialBalance, useVoucher,
  whatsappLink, type Status, type SyncSettings, type Voucher,
} from "./api";

const TABS = [
  { key: "overview", label: "Overview", icon: Landmark },
  { key: "parties", label: "Parties", icon: Users },
  { key: "stock", label: "Stock", icon: Boxes },
  { key: "daybook", label: "Day book", icon: BookOpen },
  { key: "reports", label: "Reports", icon: FileSpreadsheet },
  { key: "sync", label: "Sync & settings", icon: Settings2 },
] as const;
type Tab = (typeof TABS)[number]["key"];

function State({ q, children }: { q: { isPending: boolean; error: unknown; refetch: () => unknown }; children: ReactNode }) {
  if (q.isPending) return <div className="nxty-skeleton" aria-label="Loading"><i /><i /><i /></div>;
  if (q.error) return <div className="nxty-error" role="alert">{(q.error as Error).message || "Could not load."}<button type="button" onClick={() => void q.refetch()}><RefreshCw size={14} />Try again</button></div>;
  return <>{children}</>;
}

function download(path: string, name: string) {
  void exportWorkbook(path, name);
}

function Modal({ title, onClose, children, wide = false }: { title: ReactNode; onClose: () => void; children: ReactNode; wide?: boolean }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="nxty-modal" role="dialog" aria-modal="true" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="nxty-modal-box" data-wide={wide || undefined}>
        <header><strong>{title}</strong><button type="button" className="nxty-close" aria-label="Close" onClick={onClose}><X size={18} /></button></header>
        <div className="nxty-modal-body">{children}</div>
      </div>
    </div>
  );
}

function Pill({ status }: { status: Status }) {
  const [tone, text]: [Tone, string] = !status.connected ? ["neutral", "Not connected"] : status.paused ? ["warning", "Paused"] : !status.online ? ["danger", "Connector offline"]
    : !status.tally_ok ? ["warning", "Tally closed"] : status.pending ? ["info", "Syncing…"] : ["success", "In sync"];
  return <span className="nxty-pill" data-tone={tone}><CircleDot size={12} />{text}{status.last_sync ? <em>· {ago(status.last_sync)}</em> : null}</span>;
}

// ---------------------------------------------------------------------------------------------
// Connect
// ---------------------------------------------------------------------------------------------

function ConnectPanel({ status }: { status: Status }) {
  const pair = usePair();
  const code = pair.data?.code as string | undefined;
  const [copied, setCopied] = useState(false);
  return (
    <div className="nxty-connect">
      <section className="nxty-card nxty-hero">
        <span className="nxty-hero-icon"><ArrowDownUp size={26} /></span>
        <div>
          <h2>Connect Tally to NexEase</h2>
          <p className="nxty-muted">Keep Tally as your main books and see everything here, live: parties, outstanding, stock, day book, registers and trial balance. Entries you make in NexEase go straight into Tally, and Tally entries show up here within a minute.</p>
        </div>
      </section>
      <ol className="nxty-steps">
        <li className="nxty-card">
          <b>1</b>
          <div>
            <h3>Turn on Tally&apos;s connection port</h3>
            <p className="nxty-muted">In TallyPrime press <kbd>F1</kbd> Help → Settings → Connectivity → <em>Client/Server configuration</em>. Set <em>TallyPrime acts as</em> to <strong>Both</strong>, <em>Enable ODBC</em> to <strong>Yes</strong> and <em>Port</em> to <strong>9000</strong>. Restart Tally and open your company.</p>
          </div>
        </li>
        <li className="nxty-card">
          <b>2</b>
          <div>
            <h3>Install the NexEase Tally Connector</h3>
            <p className="nxty-muted">On the same Windows computer where Tally runs. It is a small app that relays data between Tally and NexEase; nothing else is installed in Tally.</p>
            <a className="nx-button nxty-inline" href={status.download_url} target="_blank" rel="noreferrer"><Download size={16} />Download for Windows</a>
          </div>
        </li>
        <li className="nxty-card">
          <b>3</b>
          <div>
            <h3>Pair it with this account</h3>
            <p className="nxty-muted">Open the connector and enter this code. It works once and expires in 15 minutes.</p>
            {status.can_manage ? (
              code ? (
                <div className="nxty-code">
                  <output aria-label="Pairing code">{code}</output>
                  <button type="button" className="nx-button nx-secondary nxty-inline" onClick={() => { void navigator.clipboard?.writeText(code); setCopied(true); }}>{copied ? <Check size={16} /> : <Copy size={16} />}{copied ? "Copied" : "Copy"}</button>
                  <button type="button" className="nxty-link" onClick={() => pair.mutate()}>New code</button>
                </div>
              ) : <button type="button" className="nx-button nxty-inline" disabled={pair.isPending} onClick={() => pair.mutate()}><Link2 size={16} />{pair.isPending ? "Creating…" : "Create pairing code"}</button>
            ) : <p className="nxty-warn"><AlertTriangle size={16} />Ask an admin of this account to create the pairing code.</p>}
          </div>
        </li>
      </ol>
      {status.connected ? <p className="nxty-ok"><CheckCircle2 size={16} />Connector paired. Waiting for Tally — keep Tally open with your company loaded.</p> : null}
      <section className="nxty-card">
        <h3>What syncs</h3>
        <div className="nxty-two">
          <div><Badge tone="info">Tally → NexEase</Badge><p className="nxty-muted">Companies, groups, ledgers with balances and GSTIN, stock items, units, godowns, voucher types and every voucher. Debtors become customers, creditors suppliers, stock items products. Deletions are detected.</p></div>
          <div><Badge tone="violet">NexEase → Tally</Badge><p className="nxty-muted">Customers, suppliers, products, sales invoices, purchase bills, receipts, payments, credit and debit notes, orders, expenses and manual journals. Edits update the same Tally voucher; cancellations cancel it.</p></div>
        </div>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------
// Overview
// ---------------------------------------------------------------------------------------------

function trendNote(v: number, p: number) {
  if (!p) return "This month";
  const pct = ((v - p) / Math.abs(p)) * 100;
  return `${pct >= 0 ? "▲" : "▼"} ${Math.abs(pct).toFixed(0)}% vs last month`;
}

function VoucherRows({ rows, onOpen, balance = false }: { rows: (Voucher & { debit?: number; credit?: number; balance?: number; particulars?: string })[]; onOpen: (g: string) => void; balance?: boolean }) {
  if (!rows.length) return <p className="nxty-empty">No vouchers in this period.</p>;
  return (
    <div className="nxty-table-wrap">
      <table className="nxty-table">
        <thead><tr><th>Date</th><th>Type</th><th>No.</th><th>{balance ? "Particulars" : "Party"}</th>{balance ? <><th className="num">Debit</th><th className="num">Credit</th><th className="num">Balance</th></> : <th className="num">Amount</th>}</tr></thead>
        <tbody>
          {rows.map((v) => (
            <tr key={v.guid} onClick={() => onOpen(v.guid)} tabIndex={0} onKeyDown={(e) => e.key === "Enter" && onOpen(v.guid)}>
              <td>{formatDate(v.date)}</td>
              <td><span className="nxty-type">{v.type}</span>{v.from_nexease ? <span className="nxty-tag" title="Entered in NexEase">NX</span> : null}</td>
              <td>{v.number}</td>
              <td className="nxty-party">{balance ? v.particulars || v.narration || v.type : v.party || v.narration}</td>
              {balance ? <><td className="num">{v.debit ? inr(v.debit, 2) : ""}</td><td className="num">{v.credit ? inr(v.credit, 2) : ""}</td><td className="num">{inr(Math.abs(v.balance ?? 0), 2)} {(v.balance ?? 0) >= 0 ? "Dr" : "Cr"}</td></>
                : <td className="num">{inr(v.amount, 2)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function OverviewPanel({ enabled, company, openParty, openVoucher, go }: { enabled: boolean; company: string; openParty: (g: string) => void; openVoucher: (g: string) => void; go: (t: Tab) => void }) {
  const q = useOverview(enabled);
  const d = q.data;
  return (
    <State q={q}>
      {d ? (
        <div className="nxty-stack">
          <div className="nx-kpi-strip nxty-kpis">
            <StatCard label="Sales this month" value={inr(d.kpis.sales.value)} hint={trendNote(d.kpis.sales.value, d.kpis.sales.previous)} icon={ReceiptIndianRupee} tone="success" />
            <StatCard label="Purchases this month" value={inr(d.kpis.purchase.value)} hint={trendNote(d.kpis.purchase.value, d.kpis.purchase.previous)} icon={ShoppingCart} tone="info" />
            <StatCard label="Receivable" value={inr(d.receivable)} hint={`Collected ${inr(d.kpis.receipts.value)} this month`} icon={HandCoins} tone="warning" />
            <StatCard label="Payable" value={inr(d.payable)} hint={`Paid ${inr(d.kpis.payments.value)} this month`} icon={Wallet} tone="danger" />
            <StatCard label="Cash & bank" value={inr(d.cash + d.bank)} hint={`Cash ${inr(d.cash)} · Bank ${inr(d.bank)}`} icon={Landmark} tone="violet" />
            <StatCard label="Stock value" value={inr(d.stock_value)} icon={Package} tone="neutral" />
          </div>
          <div className="nxty-grid2">
            <section className="nxty-card">
              <h3>Sales and purchases · last 12 months</h3>
              <ReportChart title="Sales and purchases" chart={{ type: "bar", x: "period", y: ["sales", "purchase"] }} rows={d.trend.map((t) => ({ ...t, period: t.month }))}
                columns={[{ key: "period", label: "Month", type: "text" }, { key: "sales", label: "Sales", type: "money" }, { key: "purchase", label: "Purchases", type: "money" }]} />
            </section>
            <section className="nxty-card">
              <div className="nxty-head-row"><h3>Who owes you</h3><button type="button" className="nxty-link" onClick={() => go("parties")}>All parties</button></div>
              {d.top_debtors.length ? (
                <ul className="nxty-list">
                  {d.top_debtors.map((p) => (
                    <li key={p.guid}>
                      <button type="button" onClick={() => openParty(p.guid)}><span>{p.name}</span><strong>{inr(p.balance)}</strong></button>
                      {p.phone ? <a className="nxty-wa" href={whatsappLink(p.phone, p.name, p.balance, company)} target="_blank" rel="noreferrer" aria-label={`Remind ${p.name} on WhatsApp`}><MessageCircle size={16} /></a> : null}
                    </li>
                  ))}
                </ul>
              ) : <p className="nxty-empty">Nothing outstanding.</p>}
              {d.cash_bank.length ? <><h3 className="nxty-sub">Cash and bank</h3><ul className="nxty-list">{d.cash_bank.map((b) => <li key={b.name}><span className="nxty-li"><span>{b.name}</span><strong>{inr(b.balance)}</strong></span></li>)}</ul></> : null}
            </section>
          </div>
          <section className="nxty-card">
            <div className="nxty-head-row"><h3>Latest entries in Tally</h3><button type="button" className="nxty-link" onClick={() => go("daybook")}>Open day book</button></div>
            <VoucherRows rows={d.recent} onOpen={openVoucher} />
          </section>
        </div>
      ) : null}
    </State>
  );
}

// ---------------------------------------------------------------------------------------------
// Parties and statement
// ---------------------------------------------------------------------------------------------

function PartiesPanel({ openParty, company }: { openParty: (g: string) => void; company: string }) {
  const [side, setSide] = useState("debtors");
  const [q, setQ] = useState("");
  const parties = useParties(side, q);
  return (
    <div className="nxty-stack">
      <div className="nxty-toolbar">
        <div className="nxty-seg" role="tablist">{[["debtors", "Customers (debtors)"], ["creditors", "Suppliers (creditors)"]].map(([k, l]) => <button key={k} type="button" role="tab" aria-selected={side === k} onClick={() => setSide(k)}>{l}</button>)}</div>
        <label className="nxty-search"><Search size={16} /><input placeholder="Name, GSTIN or phone" value={q} onChange={(e) => setQ(e.target.value)} /></label>
        <button type="button" className="nx-button nx-secondary nxty-inline" onClick={() => download(exportPath("parties/", { side, q }), "tally-parties.xlsx")}><Download size={16} />Excel</button>
      </div>
      <State q={parties}>
        {parties.data ? (
          <>
            <p className="nxty-muted">{parties.data.count} parties · total {side === "debtors" ? "receivable" : "payable"} <strong>{inr(parties.data.total)}</strong></p>
            <div className="nxty-table-wrap">
              <table className="nxty-table">
                <thead><tr><th>Party</th><th>GSTIN</th><th>Phone</th><th className="num">Balance</th><th aria-label="Actions" /></tr></thead>
                <tbody>
                  {parties.data.parties.map((p) => (
                    <tr key={p.guid} onClick={() => openParty(p.guid)} tabIndex={0} onKeyDown={(e) => e.key === "Enter" && openParty(p.guid)}>
                      <td className="nxty-party"><strong>{p.name}</strong><span className="nxty-fine">{p.parent}{p.state ? ` · ${p.state}` : ""}</span></td>
                      <td>{p.gstin || "—"}</td>
                      <td>{p.phone || "—"}</td>
                      <td className="num" data-neg={p.balance < 0 || undefined}>{inr(p.balance, 2)}</td>
                      <td className="nxty-actions" onClick={(e) => e.stopPropagation()}>
                        {p.phone && p.balance > 0 && side === "debtors" ? <a className="nxty-wa" href={whatsappLink(p.phone, p.name, p.balance, company)} target="_blank" rel="noreferrer" aria-label={`Remind ${p.name} on WhatsApp`}><MessageCircle size={16} /></a> : null}
                        {p.nexease_id ? <Link className="nxty-link" href={p.nexease_model === "supplier" ? "/suppliers" : "/customers"} title="Also in NexEase">NexEase</Link> : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!parties.data.parties.length ? <p className="nxty-empty">No parties match.</p> : null}
          </>
        ) : null}
      </State>
    </div>
  );
}

function StatementModal({ guid, onClose, openVoucher, company }: { guid: string; onClose: () => void; openVoucher: (g: string) => void; company: string }) {
  const [from, setFrom] = useState(fyStart());
  const [to, setTo] = useState(today());
  const q = useStatement(guid, from, to);
  const d = q.data;
  const owed = d ? (d.group === "creditors" ? -d.closing : d.closing) : 0;
  return (
    <Modal title={d?.name ?? "Ledger"} onClose={onClose} wide>
      <State q={q}>
        {d ? (
          <div className="nxty-stack">
            <div className="nxty-head-row">
              <p className="nxty-muted">{[d.parent, d.gstin, d.phone, d.state].filter(Boolean).join(" · ")}</p>
              <div className="nxty-actions">
                {d.phone && owed > 0 && d.group === "debtors" ? <a className="nx-button nx-secondary nxty-inline" href={whatsappLink(d.phone, d.name, owed, company)} target="_blank" rel="noreferrer"><MessageCircle size={16} />Remind</a> : null}
                <button type="button" className="nx-button nx-secondary nxty-inline" onClick={() => download(exportPath(`parties/${guid}/`, { from, to }), `${d.name}-statement.xlsx`)}><Download size={16} />Excel</button>
              </div>
            </div>
            <div className="nxty-mini">
              <div><span>Closing balance</span><strong>{inr(Math.abs(d.closing), 2)} {d.closing >= 0 ? "Dr" : "Cr"}</strong></div>
              <div><span>Open bills</span><strong>{d.bills.length}</strong></div>
              <div><span>Overdue</span><strong>{inr(d.bills.filter((b) => b.overdue_days > 0).reduce((s, b) => s + Math.abs(b.amount), 0))}</strong></div>
              {d.credit_days ? <div><span>Credit period</span><strong>{d.credit_days} days</strong></div> : null}
            </div>
            {d.bills.length ? (
              <section>
                <h3 className="nxty-sub">Outstanding bills</h3>
                <div className="nxty-table-wrap"><table className="nxty-table"><thead><tr><th>Bill</th><th>Date</th><th>Due</th><th className="num">Overdue</th><th className="num">Pending</th></tr></thead>
                  <tbody>{d.bills.map((b) => <tr key={b.name}><td>{b.name}</td><td>{formatDate(b.date)}</td><td>{formatDate(b.due)}</td><td className="num">{b.overdue_days ? <Badge tone={b.overdue_days > 30 ? "danger" : "warning"}>{b.overdue_days} days</Badge> : "—"}</td><td className="num">{inr(Math.abs(b.amount), 2)}</td></tr>)}</tbody></table></div>
              </section>
            ) : null}
            <section>
              <div className="nxty-head-row"><h3 className="nxty-sub">Ledger statement</h3><div className="nxty-dates"><input type="date" aria-label="From" value={from} onChange={(e) => setFrom(e.target.value)} /><input type="date" aria-label="To" value={to} onChange={(e) => setTo(e.target.value)} /></div></div>
              <p className="nxty-fine">Opening balance {inr(Math.abs(d.opening), 2)} {d.opening >= 0 ? "Dr" : "Cr"}</p>
              <VoucherRows rows={d.rows} onOpen={openVoucher} balance />
            </section>
          </div>
        ) : null}
      </State>
    </Modal>
  );
}

function VoucherModal({ guid, onClose }: { guid: string; onClose: () => void }) {
  const q = useVoucher(guid);
  const d = q.data;
  return (
    <Modal title={d ? `${d.type} ${d.number}` : "Voucher"} onClose={onClose}>
      <State q={q}>
        {d ? (
          <div className="nxty-stack">
            <div className="nxty-mini">
              <div><span>Date</span><strong>{formatDate(d.date)}</strong></div>
              <div><span>Party</span><strong>{d.party || "—"}</strong></div>
              <div><span>Amount</span><strong>{inr(d.amount, 2)}</strong></div>
              {d.from_nexease ? <div><span>Source</span><strong>Entered in NexEase</strong></div> : null}
            </div>
            {d.cancelled || d.deleted ? <p className="nxty-warn"><AlertTriangle size={16} />{d.deleted ? "Deleted in Tally." : "Cancelled in Tally."}</p> : null}
            {d.inventory.length ? (
              <div className="nxty-table-wrap"><table className="nxty-table"><thead><tr><th>Item</th><th className="num">Qty</th><th className="num">Rate</th><th className="num">Amount</th></tr></thead>
                <tbody>{d.inventory.map((i, n) => <tr key={n}><td>{i.item}</td><td className="num">{i.qty} {i.unit}</td><td className="num">{inr(i.rate, 2)}</td><td className="num">{inr(i.amount, 2)}</td></tr>)}</tbody></table></div>
            ) : null}
            <div className="nxty-table-wrap"><table className="nxty-table"><thead><tr><th>Ledger</th><th className="num">Debit</th><th className="num">Credit</th></tr></thead>
              <tbody>{d.entries.map((e, n) => <tr key={n}><td>{e.ledger}</td><td className="num">{e.debit ? inr(e.debit, 2) : ""}</td><td className="num">{e.credit ? inr(e.credit, 2) : ""}</td></tr>)}</tbody></table></div>
            {d.narration ? <p className="nxty-muted"><strong>Narration:</strong> {d.narration}</p> : null}
          </div>
        ) : null}
      </State>
    </Modal>
  );
}

// ---------------------------------------------------------------------------------------------
// Stock, day book, reports
// ---------------------------------------------------------------------------------------------

function StockPanel() {
  const [q, setQ] = useState("");
  const stock = useStock(q);
  return (
    <div className="nxty-stack">
      <div className="nxty-toolbar">
        <label className="nxty-search"><Search size={16} /><input placeholder="Item or HSN" value={q} onChange={(e) => setQ(e.target.value)} /></label>
        <button type="button" className="nx-button nx-secondary nxty-inline" onClick={() => download(exportPath("stock/", { q }), "tally-stock.xlsx")}><Download size={16} />Excel</button>
      </div>
      <State q={stock}>
        {stock.data ? (
          <>
            <p className="nxty-muted">{stock.data.count} items · closing value <strong>{inr(stock.data.value)}</strong>{stock.data.negative ? <> · <Badge tone="danger">{stock.data.negative} negative</Badge></> : null}</p>
            <div className="nxty-table-wrap">
              <table className="nxty-table">
                <thead><tr><th>Item</th><th>HSN</th><th className="num">GST</th><th className="num">Closing qty</th><th className="num">Rate</th><th className="num">Value</th></tr></thead>
                <tbody>{stock.data.items.map((i) => (
                  <tr key={i.guid}><td className="nxty-party"><strong>{i.name}</strong><span className="nxty-fine">{i.group}</span></td><td>{i.hsn || "—"}</td><td className="num">{i.gst_rate ? `${i.gst_rate}%` : "—"}</td>
                    <td className="num" data-neg={i.qty < 0 || undefined}>{i.qty} {i.unit}</td><td className="num">{inr(i.rate, 2)}</td><td className="num">{inr(i.value)}</td></tr>
                ))}</tbody>
              </table>
            </div>
            {!stock.data.items.length ? <p className="nxty-empty">No stock items in Tally.</p> : null}
          </>
        ) : null}
      </State>
    </div>
  );
}

function DaybookPanel({ openVoucher }: { openVoucher: (g: string) => void }) {
  const [from, setFrom] = useState(today());
  const [to, setTo] = useState(today());
  const [type, setType] = useState("");
  const [q, setQ] = useState("");
  const book = useDaybook(from, to, type, q);
  return (
    <div className="nxty-stack">
      <div className="nxty-toolbar">
        <div className="nxty-dates"><input type="date" aria-label="From" value={from} onChange={(e) => setFrom(e.target.value)} /><input type="date" aria-label="To" value={to} onChange={(e) => setTo(e.target.value)} /></div>
        <select className="nxty-select" aria-label="Voucher type" value={type} onChange={(e) => setType(e.target.value)}>
          <option value="">All voucher types</option>{(book.data?.types ?? []).map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <label className="nxty-search"><Search size={16} /><input placeholder="Party, number or narration" value={q} onChange={(e) => setQ(e.target.value)} /></label>
        <button type="button" className="nx-button nx-secondary nxty-inline" onClick={() => download(exportPath("daybook/", { from, to, type, q }), "tally-daybook.xlsx")}><Download size={16} />Excel</button>
      </div>
      <State q={book}>
        {book.data ? (
          <>
            {Object.keys(book.data.by_type).length ? <div className="nxty-chips">{Object.entries(book.data.by_type).map(([k, v]) => <span key={k}>{k} <strong>{inr(v)}</strong></span>)}</div> : null}
            <VoucherRows rows={book.data.vouchers} onOpen={openVoucher} />
          </>
        ) : null}
      </State>
    </div>
  );
}

const REGISTERS = ["Sales", "Purchase", "Receipt", "Payment", "Journal", "Contra", "Credit Note", "Debit Note", "Sales Order", "Purchase Order"];

function ReportsPanel({ openVoucher }: { openVoucher: (g: string) => void }) {
  const [report, setReport] = useState("Sales");
  const [from, setFrom] = useState(fyStart());
  const [to, setTo] = useState(today());
  const reg = useRegister(report, from, to);
  const tb = useTrialBalance();
  const [open, setOpen] = useState<string | null>(null);
  return (
    <div className="nxty-stack">
      <div className="nxty-toolbar">
        <select className="nxty-select" aria-label="Report" value={report} onChange={(e) => setReport(e.target.value)}>
          <option value="tb">Trial balance</option>{REGISTERS.map((r) => <option key={r} value={r}>{r} register</option>)}
        </select>
        {report !== "tb" ? <div className="nxty-dates"><input type="date" aria-label="From" value={from} onChange={(e) => setFrom(e.target.value)} /><input type="date" aria-label="To" value={to} onChange={(e) => setTo(e.target.value)} /></div> : null}
        <button type="button" className="nx-button nx-secondary nxty-inline" onClick={() => report === "tb" ? download(exportPath("trial-balance/"), "tally-trial-balance.xlsx") : download(exportPath("registers/", { type: report, from, to }), `tally-${report}.xlsx`)}><Download size={16} />Excel</button>
      </div>
      {report === "tb" ? (
        <State q={tb}>
          {tb.data ? (
            <section className="nxty-card">
              <div className="nxty-head-row"><h3>Trial balance (closing, from Tally)</h3>{Math.abs(tb.data.difference) < 1 ? <Badge tone="success" icon={Check}>Balanced</Badge> : <Badge tone="danger">Difference {inr(tb.data.difference, 2)}</Badge>}</div>
              <div className="nxty-table-wrap">
                <table className="nxty-table nxty-tb">
                  <thead><tr><th>Particulars</th><th className="num">Debit</th><th className="num">Credit</th></tr></thead>
                  <tbody>
                    {tb.data.groups.map((g) => (
                      <GroupRows key={g.code} g={g} open={open === g.code} toggle={() => setOpen(open === g.code ? null : g.code)} />
                    ))}
                  </tbody>
                  <tfoot><tr><th>Total</th><th className="num">{inr(tb.data.debit, 2)}</th><th className="num">{inr(tb.data.credit, 2)}</th></tr></tfoot>
                </table>
              </div>
            </section>
          ) : null}
        </State>
      ) : (
        <State q={reg}>
          {reg.data ? (
            <>
              <div className="nxty-grid2">
                <section className="nxty-card">
                  <div className="nxty-head-row"><h3>{report} by month</h3><strong>{inr(reg.data.total)}</strong></div>
                  {reg.data.months.length ? <ReportChart title={`${report} by month`} chart={{ type: "bar", x: "period", y: ["amount"] }} rows={reg.data.months.map((m) => ({ period: m.month, amount: m.amount }))}
                    columns={[{ key: "period", label: "Month", type: "text" }, { key: "amount", label: report, type: "money" }]} /> : <p className="nxty-empty">No {report.toLowerCase()} vouchers in this period.</p>}
                </section>
                <section className="nxty-card">
                  <h3>By ledger</h3>
                  <ul className="nxty-list">{reg.data.ledgers.map((l) => <li key={l.ledger}><span className="nxty-li"><span>{l.ledger}</span><strong>{inr(l.amount)}</strong></span></li>)}</ul>
                </section>
              </div>
              <section className="nxty-card"><h3>{reg.data.count} vouchers</h3><VoucherRows rows={reg.data.vouchers} onOpen={openVoucher} /></section>
            </>
          ) : null}
        </State>
      )}
    </div>
  );
}

function GroupRows({ g, open, toggle }: { g: { code: string; label: string; debit: number; credit: number; ledgers: { guid: string; name: string; debit: number; credit: number }[] }; open: boolean; toggle: () => void }) {
  return (
    <>
      <tr className="nxty-group" onClick={toggle} aria-expanded={open}><td><strong>{open ? "▾" : "▸"} {g.label}</strong></td><td className="num"><strong>{g.debit ? inr(g.debit, 2) : ""}</strong></td><td className="num"><strong>{g.credit ? inr(g.credit, 2) : ""}</strong></td></tr>
      {open ? g.ledgers.map((l) => <tr key={l.guid} className="nxty-leaf"><td>{l.name}</td><td className="num">{l.debit ? inr(l.debit, 2) : ""}</td><td className="num">{l.credit ? inr(l.credit, 2) : ""}</td></tr>) : null}
    </>
  );
}

// ---------------------------------------------------------------------------------------------
// Sync & settings
// ---------------------------------------------------------------------------------------------

const JOB_TONE: Record<string, Tone> = { done: "success", failed: "danger", queued: "neutral", sent: "info", cancelled: "neutral" };

function SyncPanel({ status }: { status: Status }) {
  const settings = useSettings();
  const save = useSaveSettings();
  const company = useCompany();
  const revoke = useRevoke();
  const resync = useResync();
  const issues = useIssues();
  const retryIssues = useRetryIssues();
  const [jobFilter, setJobFilter] = useState("");
  const jobs = useJobs(jobFilter);
  const retryJob = useRetryJob();
  const pair = usePair();
  const [draft, setDraft] = useState<Partial<SyncSettings> | null>(null);
  const s = settings.data?.settings;
  const opts = settings.data?.options;
  const view: SyncSettings | undefined = s ? { ...s, ...draft } as SyncSettings : undefined;
  const canManage = status.can_manage;
  const set = (patch: Partial<SyncSettings>) => setDraft((d) => ({ ...(d ?? {}), ...patch }));
  const ledgerOptions = (groups: string[]) => {
    const first = groups.flatMap((g) => opts?.by_group[g] ?? []);
    return [...first, ...(opts?.ledgers ?? []).filter((l) => !first.includes(l))];
  };
  const missing = view ? ["sales", "purchase", "cgst_out", "sgst_out", "igst_out", "cgst_in", "sgst_in", "igst_in", "round_off", "cash", "bank"].filter((k) => !view.mapping[k]) : [];

  return (
    <div className="nxty-stack">
      <div className="nxty-status-grid">
        <div className="nxty-card nxty-stat" data-ok={status.tally_ok || undefined}><Plug size={18} /><div><span>Tally</span><strong>{status.tally_ok ? "Connected" : status.online ? "Not reachable" : "—"}</strong>{status.tally_error ? <em>{status.tally_error}</em> : null}</div></div>
        <div className="nxty-card nxty-stat" data-ok={status.online || undefined}><Laptop size={18} /><div><span>Connector</span><strong>{status.online ? "Online" : status.connected ? "Offline" : "Not paired"}</strong><em>Checks every {status.interval} s</em></div></div>
        <div className="nxty-card nxty-stat"><RefreshCw size={18} /><div><span>Last sync</span><strong>{ago(status.last_sync)}</strong><em>{status.pending ? `${status.pending} in progress` : "Up to date"}</em></div></div>
        <div className="nxty-card nxty-stat" data-bad={status.issues || undefined}><AlertTriangle size={18} /><div><span>Needs attention</span><strong>{status.issues}</strong><em>{status.pushed} NexEase entries in Tally</em></div></div>
      </div>

      {canManage ? (
        <div className="nxty-actions">
          <button type="button" className="nx-button nx-secondary nxty-inline" onClick={() => save.mutate({ paused: !status.paused })}>{status.paused ? <PlayCircle size={16} /> : <PauseCircle size={16} />}{status.paused ? "Resume sync" : "Pause sync"}</button>
          <button type="button" className="nx-button nx-secondary nxty-inline" onClick={() => window.confirm("Fetch all Tally data again? Use this if something looks out of date.") && resync.mutate("all")}><RefreshCw size={16} />Full refresh from Tally</button>
          <a className="nx-button nx-secondary nxty-inline" href={status.download_url} target="_blank" rel="noreferrer"><Download size={16} />Connector for Windows</a>
        </div>
      ) : null}

      {issues.data?.issues.length ? (
        <section className="nxty-card">
          <div className="nxty-head-row"><h3><AlertTriangle size={16} />Not sent to Tally yet</h3>{canManage ? <button type="button" className="nx-button nx-secondary nxty-inline" onClick={() => retryIssues.mutate(undefined)}><RefreshCw size={16} />Retry all</button> : null}</div>
          <ul className="nxty-issues">{issues.data.issues.map((i) => (
            <li key={i.model + i.id}><div><strong>{i.label}</strong><span>{i.error}</span></div>{canManage ? <button type="button" className="nxty-link" onClick={() => retryIssues.mutate(i.id)}>Retry</button> : null}</li>
          ))}</ul>
        </section>
      ) : null}

      <section className="nxty-card">
        <h3>Tally companies</h3>
        {status.companies.length ? (
          <ul className="nxty-companies">{status.companies.map((c) => (
            <li key={c.id} data-on={c.enabled || undefined}>
              <div>
                <strong>{c.name}</strong>
                <span className="nxty-fine">{[c.gstin, c.state, c.books_from && `Books from ${formatDate(c.books_from)}`, !c.open && "Not open in Tally"].filter(Boolean).join(" · ")}</span>
                {c.enabled ? <span className="nxty-fine">{c.counts.ledger ?? 0} ledgers · {c.counts.stockitem ?? 0} items · {c.counts.voucher ?? 0} vouchers</span> : null}
                {c.enabled && c.progress < 100 ? <div className="nxty-progress" role="progressbar" aria-valuenow={c.progress} aria-valuemin={0} aria-valuemax={100}><i style={{ width: `${c.progress}%` }} /><span>First sync {c.progress}%</span></div> : null}
              </div>
              {c.enabled ? <Badge tone="success" icon={Check}>Syncing</Badge> : canManage ? <button type="button" className="nx-button nx-secondary nxty-inline" onClick={() => company.mutate({ id: c.id, enabled: true })}>Sync this company</button> : null}
            </li>
          ))}</ul>
        ) : <p className="nxty-empty">Open a company in Tally; it will appear here within a minute.</p>}
      </section>

      <State q={settings}>
        {view && opts ? (
          <>
            <section className="nxty-card">
              <div className="nxty-head-row">
                <h3>Ledger mapping for NexEase entries</h3>
                {canManage && opts.suggested ? <button type="button" className="nxty-link" onClick={() => set({ mapping: { ...Object.fromEntries(Object.entries(opts.suggested).filter(([, v]) => v)), ...Object.fromEntries(Object.entries(view.mapping).filter(([, v]) => v)) } })}>Fill suggestions</button> : null}
              </div>
              <p className="nxty-muted">Which Tally ledgers NexEase invoices, bills and payments post to. Parties and stock items are matched by name automatically.</p>
              {missing.length ? <p className="nxty-warn"><AlertTriangle size={16} />Choose {missing.map((k) => MAPPING_LABELS[k].label).join(", ")} so entries can go to Tally.</p> : null}
              <div className="nxty-form">
                {settings.data!.mapping_keys.map((k) => (
                  <label key={k}>{MAPPING_LABELS[k]?.label ?? k}
                    <select className="nxty-select" disabled={!canManage} value={view.mapping[k] ?? ""} onChange={(e) => set({ mapping: { ...view.mapping, [k]: e.target.value } })}>
                      <option value="">{opts.suggested[k] ? `Not set (suggested: ${opts.suggested[k]})` : "Not set"}</option>
                      {ledgerOptions(MAPPING_LABELS[k]?.groups ?? []).map((l) => <option key={l} value={l}>{l}</option>)}
                    </select>
                  </label>
                ))}
              </div>
              {opts.bank_accounts.length ? (
                <>
                  <h4 className="nxty-sub">Bank accounts</h4>
                  <div className="nxty-form">{opts.bank_accounts.filter((b) => b.type !== "CASH").map((b) => (
                    <label key={b.id}>{b.name}<select className="nxty-select" disabled={!canManage} value={view.bank_ledgers[b.id] ?? ""} onChange={(e) => set({ bank_ledgers: { ...view.bank_ledgers, [b.id]: e.target.value } })}>
                      <option value="">Default bank ledger</option>{ledgerOptions(["bank"]).map((l) => <option key={l} value={l}>{l}</option>)}</select></label>
                  ))}</div>
                </>
              ) : null}
              {opts.expense_categories.length ? (
                <>
                  <h4 className="nxty-sub">Expense categories</h4>
                  <div className="nxty-form">{opts.expense_categories.map((c) => (
                    <label key={c}>{c}<select className="nxty-select" disabled={!canManage} value={view.expense_ledgers[c] ?? ""} onChange={(e) => set({ expense_ledgers: { ...view.expense_ledgers, [c]: e.target.value } })}>
                      <option value="">Default expense ledger</option>{ledgerOptions(["indirect_expense", "direct_expense"]).map((l) => <option key={l} value={l}>{l}</option>)}</select></label>
                  ))}</div>
                </>
              ) : null}
            </section>

            <section className="nxty-card">
              <h3>What goes from NexEase to Tally</h3>
              <div className="nxty-toggles">
                {settings.data!.write_kinds.map((k) => (
                  <label key={k} className="nxty-toggle"><input type="checkbox" disabled={!canManage} checked={view.write_back[k] !== false} onChange={(e) => set({ write_back: { ...view.write_back, [k]: e.target.checked } })} />{WRITE_LABELS[k] ?? k}</label>
                ))}
              </div>
              <div className="nxty-form">
                <label>Send entries dated or changed from<input type="date" className="nxty-select" disabled={!canManage} value={view.push_from} onChange={(e) => set({ push_from: e.target.value })} /></label>
                <label>Invoice lines in Tally<select className="nxty-select" disabled={!canManage} value={view.invoice_mode} onChange={(e) => set({ invoice_mode: e.target.value as SyncSettings["invoice_mode"] })}>
                  <option value="auto">Automatic (items if Tally keeps stock)</option><option value="item">Item invoice (with stock items)</option><option value="accounting">Accounting invoice (ledgers only)</option></select></label>
                <label>New customers go under<select className="nxty-select" disabled={!canManage} value={view.debtors_group} onChange={(e) => set({ debtors_group: e.target.value })}>{["Sundry Debtors", view.debtors_group].filter((v, i, a) => a.indexOf(v) === i).map((g) => <option key={g}>{g}</option>)}</select></label>
                <label>New suppliers go under<select className="nxty-select" disabled={!canManage} value={view.creditors_group} onChange={(e) => set({ creditors_group: e.target.value })}>{["Sundry Creditors", view.creditors_group].filter((v, i, a) => a.indexOf(v) === i).map((g) => <option key={g}>{g}</option>)}</select></label>
              </div>
              <label className="nxty-toggle"><input type="checkbox" disabled={!canManage} checked={view.import_masters} onChange={(e) => set({ import_masters: e.target.checked })} />Create NexEase customers, suppliers and products from Tally parties and stock items</label>
            </section>
            {canManage ? (
              <div className="nxty-savebar" data-dirty={draft ? true : undefined}>
                <span className="nxty-muted">{draft ? "Unsaved changes" : "Settings saved"}</span>
                <button type="button" className="nx-button nx-secondary" disabled={!draft} onClick={() => setDraft(null)}>Discard</button>
                <button type="button" className="nx-button" disabled={!draft || save.isPending} onClick={() => draft && save.mutate(draft, { onSuccess: () => setDraft(null) })}>{save.isPending ? "Saving…" : "Save settings"}</button>
              </div>
            ) : null}
          </>
        ) : null}
      </State>

      <section className="nxty-card">
        <div className="nxty-head-row">
          <h3>Sync activity</h3>
          <select className="nxty-select" aria-label="Filter activity" value={jobFilter} onChange={(e) => setJobFilter(e.target.value)}><option value="">All</option><option value="failed">Problems</option><option value="queued">Waiting</option><option value="done">Done</option></select>
        </div>
        <State q={jobs}>
          {jobs.data?.jobs.length ? (
            <ul className="nxty-jobs">{jobs.data.jobs.slice(0, 60).map((j) => (
              <li key={j.id}>
                <Badge tone={JOB_TONE[j.status] ?? "neutral"}>{j.status}</Badge>
                <div><strong>{j.type === "push" ? `→ Tally: ${j.label}` : j.type === "pull" ? `← ${j.label || j.kind}${j.result.received !== undefined ? ` (${j.result.received})` : ""}` : j.type === "index" ? `Deletion check: ${j.kind}${j.result.deleted ? ` (${j.result.deleted} deleted)` : ""}` : "Companies"}</strong>{j.error ? <span className="nxty-err">{j.error}</span> : null}</div>
                <time>{ago(j.done_at || j.created_at)}</time>
                {j.status === "failed" && canManage ? <button type="button" className="nxty-link" onClick={() => retryJob.mutate(j.id)}>Retry</button> : null}
              </li>
            ))}</ul>
          ) : <p className="nxty-empty">No activity yet.</p>}
        </State>
      </section>

      <section className="nxty-card">
        <div className="nxty-head-row"><h3>Connected computers</h3>{canManage ? <button type="button" className="nxty-link" onClick={() => pair.mutate()}>Pair another computer</button> : null}</div>
        {pair.data?.code ? <p className="nxty-ok">Pairing code <strong className="nxty-mono">{String(pair.data.code)}</strong> — enter it in the connector within 15 minutes.</p> : null}
        <ul className="nxty-companies">{status.devices.map((d) => (
          <li key={d.id}>
            <div><strong>{d.name}</strong><span className="nxty-fine">{d.online ? "Online" : `Last seen ${ago(d.last_seen)}`}{d.info.version ? ` · v${d.info.version}` : ""}{d.info.os ? ` · ${d.info.os}` : ""}</span></div>
            {canManage ? <button type="button" className="nxty-link" onClick={() => window.confirm(`Remove ${d.name}? It stops syncing until paired again.`) && revoke.mutate(d.id)}>Remove</button> : null}
          </li>
        ))}</ul>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------

function Hub() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const status = useStatus();
  const tab = (TABS.some((t) => t.key === params.get("tab")) ? params.get("tab") : "overview") as Tab;
  const [party, setParty] = useState<string | null>(null);
  const [voucher, setVoucher] = useState<string | null>(null);
  const s = status.data;
  const active = useMemo(() => s?.companies.find((c) => c.enabled), [s]);
  const go = (next: Tab) => {
    const p = new URLSearchParams(params.toString());
    p.set("tab", next);
    router.replace(`${pathname}?${p.toString()}`, { scroll: false });
  };
  const hasData = !!active && (active.counts.ledger ?? 0) > 0;

  return (
    <div className="nxl-screen nxty">
      <header className="nxl-header">
        <div className="min-w-0">
          <h1>Tally</h1>
          <p className="nx-muted">{active ? `${active.name}${active.gstin ? ` · ${active.gstin}` : ""} · live from TallyPrime` : "Two-way, real-time sync with TallyPrime"}</p>
        </div>
        {s ? <Pill status={s} /> : null}
      </header>
      <State q={status}>
        {s ? (
          !hasData && tab !== "sync" ? (
            <>
              <ConnectPanel status={s} />
              {s.connected ? <p className="nxty-fine nxty-center"><button type="button" className="nxty-link" onClick={() => go("sync")}>Open sync &amp; settings</button></p> : null}
            </>
          ) : (
            <>
              <nav className="nxty-tabs" role="tablist" aria-label="Tally sections">
                {TABS.map((t) => <button key={t.key} type="button" role="tab" aria-selected={tab === t.key} onClick={() => go(t.key)}><t.icon size={16} />{t.label}{t.key === "sync" && s.issues ? <span className="nxty-count">{s.issues}</span> : null}</button>)}
              </nav>
              {active && active.progress < 100 && tab !== "sync" ? <p className="nxty-warn"><RefreshCw size={16} />First sync in progress ({active.progress}%). Figures fill in as Tally data arrives.</p> : null}
              {tab === "overview" ? <OverviewPanel enabled={hasData} company={active?.name ?? ""} openParty={setParty} openVoucher={setVoucher} go={go} /> : null}
              {tab === "parties" ? <PartiesPanel openParty={setParty} company={active?.name ?? ""} /> : null}
              {tab === "stock" ? <StockPanel /> : null}
              {tab === "daybook" ? <DaybookPanel openVoucher={setVoucher} /> : null}
              {tab === "reports" ? <ReportsPanel openVoucher={setVoucher} /> : null}
              {tab === "sync" ? <SyncPanel status={s} /> : null}
            </>
          )
        ) : null}
      </State>
      {party ? <StatementModal guid={party} onClose={() => setParty(null)} openVoucher={setVoucher} company={active?.name ?? ""} /> : null}
      {voucher ? <VoucherModal guid={voucher} onClose={() => setVoucher(null)} /> : null}
    </div>
  );
}

/** useSearchParams needs a Suspense boundary for the static export used by the mobile build. */
export default function TallyHub() {
  return <Suspense fallback={<div className="nxty-skeleton"><i /><i /></div>}><Hub /></Suspense>;
}


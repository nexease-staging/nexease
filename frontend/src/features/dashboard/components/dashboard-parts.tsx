"use client";
import Link from "next/link";
import { AlertOctagon, ArrowDownLeft, ArrowUpRight, Boxes, CheckCircle2, FileText, Landmark, PackageX, ReceiptText, Truck } from "lucide-react";
import type {
  DashboardAlerts,
  DashboardBillStatus,
  DashboardInventoryStatus,
  DashboardInvoiceStatus,
  DashboardKPIs,
  DashboardReceivableAging,
  DashboardRecentActivity,
} from "@/features/dashboard/types";
import { compact, num, relativeDay, rupees } from "@/features/dashboard/format";

const pct = (part: number, whole: number) => (whole > 0 ? Math.round((part / whole) * 100) : 0);

/** The headline: what you hold, what you are owed and what you owe. */
export function MoneyBand({ kpis }: { kpis: DashboardKPIs }) {
  const bank = num(kpis.bank_balance);
  const owed = num(kpis.receivables);
  const owe = num(kpis.payables);
  const stock = num(kpis.inventory_value);
  const net = owed - owe;
  const total = owed + owe;
  const owedShare = total > 0 ? (owed / total) * 100 : 50;
  return (
    <section className="nxd-band" aria-label="Money position">
      <div className="nxd-band-cash">
        <h2>Cash and bank</h2>
        <p className="nxd-band-hero" title={rupees(bank)}>{rupees(bank)}</p>
        <p className="nxd-band-sub">
          <Boxes size={14} aria-hidden="true" /> Stock on hand worth <strong title={rupees(stock)}>{compact(stock)}</strong>
        </p>
      </div>
      <div className="nxd-band-balance">
        <div className="nxd-band-sides">
          <Link href="/accounts-receivable" className="nxd-side">
            <span><ArrowDownLeft size={14} aria-hidden="true" />Customers owe you</span>
            <strong title={rupees(owed)}>{compact(owed)}</strong>
          </Link>
          <Link href="/accounts-payable" className="nxd-side nxd-side-end">
            <span>You owe suppliers<ArrowUpRight size={14} aria-hidden="true" /></span>
            <strong title={rupees(owe)}>{compact(owe)}</strong>
          </Link>
        </div>
        <div className="nxd-scale" role="img" aria-label={`Receivables ${rupees(owed)}, payables ${rupees(owe)}`}>
          <span className="nxd-scale-in" style={{ width: `${owedShare}%` }} />
          <span className="nxd-scale-out" style={{ width: `${100 - owedShare}%` }} />
        </div>
        <p className="nxd-band-net">
          {total === 0
            ? "No money is owed either way right now."
            : net >= 0
              ? <>After everyone settles up you are ahead by <strong title={rupees(net)}>{compact(net)}</strong>.</>
              : <>You owe <strong title={rupees(-net)}>{compact(-net)}</strong> more than customers owe you.</>}
        </p>
      </div>
    </section>
  );
}

export function AttentionStrip({ alerts }: { alerts: DashboardAlerts }) {
  const items = [
    { n: alerts.overdue_invoices, text: (n: number) => `${n} ${n === 1 ? "invoice is" : "invoices are"} past due`, action: "Follow up", href: "/accounts-receivable", icon: FileText },
    { n: alerts.overdue_bills, text: (n: number) => `${n} supplier ${n === 1 ? "bill is" : "bills are"} past due`, action: "Plan payments", href: "/accounts-payable", icon: ReceiptText },
    { n: alerts.out_of_stock_items, text: (n: number) => `${n} ${n === 1 ? "item is" : "items are"} out of stock`, action: "Restock", href: "/inventory", icon: PackageX },
  ].filter((i) => i.n > 0);
  if (!items.length) {
    return (
      <section className="nxd-attention nxd-attention-clear" aria-label="Needs attention">
        <CheckCircle2 size={18} aria-hidden="true" /> Nothing needs your attention right now. No overdue invoices or bills, and everything is in stock.
      </section>
    );
  }
  return (
    <section className="nxd-attention" aria-label="Needs attention">
      <h2><AlertOctagon size={16} aria-hidden="true" />Needs attention</h2>
      <ul>
        {items.map(({ n, text, action, href, icon: Icon }) => (
          <li key={href}>
            <Link href={href}>
              <Icon size={16} aria-hidden="true" />
              <span>{text(n)}</span>
              <em>{action}</em>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

const AGING: { key: keyof DashboardReceivableAging; label: string }[] = [
  { key: "current", label: "Not yet due" },
  { key: "1_30", label: "1–30 days late" },
  { key: "31_60", label: "31–60 days late" },
  { key: "61_90", label: "61–90 days late" },
  { key: "90_plus", label: "Over 90 days late" },
];

export function AgingCard({ aging }: { aging: DashboardReceivableAging }) {
  const rows = AGING.map((b, i) => ({ ...b, step: i, value: num(aging[b.key]) }));
  const total = rows.reduce((s, r) => s + r.value, 0);
  const old = rows.slice(3).reduce((s, r) => s + r.value, 0);
  return (
    <section className="nxd-card" aria-labelledby="nxd-aging">
      <header className="nxd-card-head">
        <div>
          <h2 id="nxd-aging">Who owes you, by age</h2>
          <p>Unpaid invoice value grouped by how late it is.</p>
        </div>
        <Link href="/accounts-receivable" className="nxd-link">Receivables</Link>
      </header>
      {total > 0 ? (
        <>
          <div className="nxd-stack" role="img" aria-label={`Outstanding ${rupees(total)}`}>
            {rows.filter((r) => r.value > 0).map((r) => <span key={r.key} data-step={r.step} style={{ flexGrow: r.value }} title={`${r.label}: ${rupees(r.value)}`} />)}
          </div>
          <table className="nxd-table">
            <caption className="sr-only">Receivables by age</caption>
            <tbody>
              {rows.map((r) => (
                <tr key={r.key}>
                  <th scope="row"><i className="nxd-dot" data-step={r.step} aria-hidden="true" />{r.label}</th>
                  <td title={rupees(r.value)}>{compact(r.value)}</td>
                  <td className="nxd-share">{pct(r.value, total)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="nxd-note">
            {old > 0 ? <><strong>{compact(old)}</strong> ({pct(old, total)}%) is more than 60 days late. These are the hardest to recover, so call these customers first.</> : "Nothing is more than 60 days late. Collections are in good shape."}
          </p>
        </>
      ) : <p className="nxd-empty">No unpaid invoices. Every customer is settled.</p>}
    </section>
  );
}

type Seg = { label: string; value: number; tone: "good" | "partial" | "open" | "late" };
function StatusBar({ title, total, segs, href }: { title: string; total: number; segs: Seg[]; href: string }) {
  return (
    <div className="nxd-status">
      <div className="nxd-status-head"><Link href={href}>{title}</Link><span>{total} total</span></div>
      {total > 0 ? (
        <div className="nxd-stack nxd-stack-thin" role="img" aria-label={`${title}: ${segs.map((s) => `${s.value} ${s.label}`).join(", ")}`}>
          {segs.filter((s) => s.value > 0).map((s) => <span key={s.label} data-tone={s.tone} style={{ flexGrow: s.value }} title={`${s.label}: ${s.value}`} />)}
        </div>
      ) : <div className="nxd-stack nxd-stack-thin nxd-stack-empty" />}
      <ul className="nxd-status-keys">
        {segs.map((s) => <li key={s.label}><i className="nxd-dot" data-tone={s.tone} aria-hidden="true" />{s.label}<b>{s.value}</b></li>)}
      </ul>
    </div>
  );
}

export function StatusCard({ invoices, bills, inventory }: { invoices: DashboardInvoiceStatus; bills: DashboardBillStatus; inventory: DashboardInventoryStatus }) {
  const inv: Seg[] = [
    { label: "Paid", value: invoices.paid, tone: "good" },
    { label: "Part paid", value: invoices.partially_paid, tone: "partial" },
    { label: "Unpaid", value: invoices.issued, tone: "open" },
    { label: "Overdue", value: invoices.overdue, tone: "late" },
  ];
  const bil: Seg[] = [
    { label: "Paid", value: bills.paid, tone: "good" },
    { label: "Part paid", value: bills.partially_paid, tone: "partial" },
    { label: "Unpaid", value: bills.posted, tone: "open" },
    { label: "Overdue", value: bills.overdue, tone: "late" },
  ];
  const stock: Seg[] = [
    { label: "In stock", value: inventory.in_stock, tone: "good" },
    { label: "Out of stock", value: inventory.out_of_stock, tone: "late" },
  ];
  const sum = (s: Seg[]) => s.reduce((t, x) => t + x.value, 0);
  return (
    <section className="nxd-card" aria-labelledby="nxd-status">
      <header className="nxd-card-head">
        <div>
          <h2 id="nxd-status">Documents and stock</h2>
          <p>How many invoices, bills and items are in each state.</p>
        </div>
      </header>
      <StatusBar title="Sales invoices" total={sum(inv)} segs={inv} href="/invoices" />
      <StatusBar title="Supplier bills" total={sum(bil)} segs={bil} href="/vendor-bills" />
      <StatusBar title="Stock items" total={sum(stock)} segs={stock} href="/inventory" />
    </section>
  );
}

export function TopList({ title, hint, rows, total, href, empty }: { title: string; hint: string; rows: { id: string; name: string; amount: number }[]; total: number; href: string; empty: string }) {
  const max = Math.max(...rows.map((r) => r.amount), 1);
  const id = `nxd-${href.replace(/\W/g, "")}`;
  return (
    <section className="nxd-card" aria-labelledby={id}>
      <header className="nxd-card-head">
        <div><h2 id={id}>{title}</h2><p>{hint}</p></div>
        <Link href={href} className="nxd-link">View all</Link>
      </header>
      {rows.length ? (
        <ol className="nxd-rank">
          {rows.map((r) => (
            <li key={r.id}>
              <span className="nxd-rank-name">{r.name}</span>
              <span className="nxd-rank-amt" title={rupees(r.amount)}>{compact(r.amount)}{total > 0 ? <small>{pct(r.amount, total)}%</small> : null}</span>
              <span className="nxd-rank-bar" aria-hidden="true"><span style={{ width: `${(r.amount / max) * 100}%` }} /></span>
            </li>
          ))}
        </ol>
      ) : <p className="nxd-empty">{empty}</p>}
    </section>
  );
}

const ACT = {
  INVOICE: { icon: FileText, label: "Invoice", href: (id: string) => `/invoices?view=${id}` },
  VENDOR_BILL: { icon: ReceiptText, label: "Supplier bill", href: (id: string) => `/vendor-bills?view=${id}` },
  BANK_TRANSACTION: { icon: Landmark, label: "Bank", href: () => "/banking" },
  STOCK_MOVEMENT: { icon: Truck, label: "Stock", href: () => "/stock-movements" },
} as const;

export function ActivityFeed({ items }: { items: DashboardRecentActivity[] }) {
  return (
    <section className="nxd-card" aria-labelledby="nxd-activity">
      <header className="nxd-card-head"><div><h2 id="nxd-activity">Recent activity</h2><p>The latest entries across sales, purchases, bank and stock.</p></div></header>
      {items.length ? (
        <ul className="nxd-feed">
          {items.slice(0, 8).map((a) => {
            const meta = ACT[a.activity_type] ?? ACT.INVOICE;
            const Icon = meta.icon;
            const amount = a.amount === null ? null : num(a.amount);
            return (
              <li key={`${a.activity_type}-${a.reference_id}`}>
                <Link href={meta.href(a.reference_id)}>
                  <span className="nxd-feed-icon" data-type={a.activity_type}><Icon size={15} aria-hidden="true" /></span>
                  <span className="nxd-feed-text"><strong>{a.description}</strong><small>{meta.label} {a.reference_number} <span aria-hidden="true">|</span> {relativeDay(a.activity_date)}</small></span>
                  <span className="nxd-feed-amt">{amount === null ? (a.quantity ? `${num(a.quantity)} units` : "") : rupees(amount)}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      ) : <p className="nxd-empty">Nothing recorded in this period yet. Create an invoice to get started.</p>}
    </section>
  );
}

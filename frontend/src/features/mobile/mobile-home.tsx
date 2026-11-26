"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ArrowDownLeft, ArrowUpRight, ChevronRight, CloudOff, Eye, EyeOff, FileText, Package, ReceiptText, RefreshCw, ShoppingCart, UserPlus, Users, Wallet } from "lucide-react";
import { useAuth } from "@/features/auth/auth-context";
import { hasPermission } from "@/lib/authorization/permissions";
import { formatDate } from "@/lib/format";
import { methodLabel } from "@/features/payments/api";
import { rupees, savedAt, useMobileHome, useSaved, type FeedRow, type MobileHome as Home } from "./api";
import { runQuick, type QuickAction } from "./quick-actions";

const FEED_LABEL: Record<FeedRow["type"], string> = { sale: "Sale", purchase: "Purchase", payment_in: "Payment in", payment_out: "Payment out", expense: "Expense" };
const FILTERS: { key: string; label: string; types: FeedRow["type"][] }[] = [
  { key: "all", label: "All", types: ["sale", "purchase", "payment_in", "payment_out", "expense"] },
  { key: "sale", label: "Sales", types: ["sale"] },
  { key: "purchase", label: "Purchases", types: ["purchase"] },
  { key: "payments", label: "Payments", types: ["payment_in", "payment_out"] },
  { key: "expense", label: "Expenses", types: ["expense"] },
];

const ACTIONS: { action: QuickAction; label: string; icon: typeof FileText; tone: string; permission: string }[] = [
  { action: "sale", label: "Add sale", icon: FileText, tone: "mint", permission: "invoices.create" },
  { action: "payment_in", label: "Payment in", icon: ArrowDownLeft, tone: "blue", permission: "invoices.record_payment" },
  { action: "purchase", label: "Purchase", icon: ShoppingCart, tone: "peach", permission: "bills.create" },
  { action: "payment_out", label: "Payment out", icon: ArrowUpRight, tone: "rose", permission: "bills.record_payment" },
  { action: "expense", label: "Expense", icon: ReceiptText, tone: "violet", permission: "expenses.manage" },
  { action: "customer", label: "Add party", icon: UserPlus, tone: "blue", permission: "customers.create" },
  { action: "item", label: "Add item", icon: Package, tone: "mint", permission: "products.create" },
];

/** A sale or bill is "unpaid" while money is still due; payments and expenses are always settled. */
function feedState(row: FeedRow) {
  if (row.type === "sale" || row.type === "purchase") {
    if (row.status === "DRAFT") return { label: "Draft", tone: "neutral" };
    if (row.status === "CANCELLED") return { label: "Cancelled", tone: "neutral" };
    if (Number(row.balance ?? 0) <= 0) return { label: "Paid", tone: "good" };
    return { label: row.status === "PARTIALLY_PAID" ? "Partly paid" : "Unpaid", tone: "warn" };
  }
  return null;
}

export default function MobileHome() {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const can = (p: string) => hasPermission(permissions, p);
  const [hide, setHide] = useState(false);
  const [filter, setFilter] = useState("all");
  const q = useMobileHome();
  const saved = useSaved<Home>("home");
  const offline = !q.data && q.isError && saved;
  const data = q.data ?? (q.isError ? saved?.data : undefined);
  const rows = useMemo(() => (data?.transactions ?? []).filter((r) => FILTERS.find((f) => f.key === filter)!.types.includes(r.type)), [data, filter]);
  const money = (v: string | null | undefined) => rupees(v, hide);
  const name = authentication?.organization?.name || "Your business";

  return (
    <div className="nxm-page">
      <header className="nxm-hello">
        <div className="min-w-0">
          <p>Welcome back</p>
          <h1>{name}</h1>
        </div>
        <button type="button" className="nxm-round" aria-label={hide ? "Show amounts" : "Hide amounts"} onClick={() => setHide(!hide)}>{hide ? <EyeOff size={19} /> : <Eye size={19} />}</button>
      </header>

      {offline ? <p className="nxm-offline" role="status"><CloudOff size={15} />Offline — showing saved figures from {savedAt(saved.at)}.</p> : null}
      {q.isError && !saved ? (
        <div role="alert" className="nxm-error">We couldn’t load your summary. Your records have not changed.<button type="button" onClick={() => void q.refetch()}><RefreshCw size={15} />Try again</button></div>
      ) : null}

      <section className="nxm-balance" aria-label="Balances">
        <Link href="/accounts-receivable" className="nxm-get">
          <span>You’ll get</span>
          <strong aria-live="polite">{data ? money(data.receivable) : "…"}</strong>
          <small>From customers <ChevronRight size={14} /></small>
        </Link>
        <Link href="/accounts-payable" className="nxm-pay">
          <span>You’ll pay</span>
          <strong>{data ? money(data.payable) : "…"}</strong>
          <small>To suppliers <ChevronRight size={14} /></small>
        </Link>
      </section>

      <section className="nxm-strip" aria-label="This month">
        <div><span>Today’s sale</span><strong>{data ? money(data.sales_today) : "…"}</strong></div>
        <div><span>Sale this month</span><strong>{data ? money(data.sales_month) : "…"}</strong></div>
        <div><span>Money in (month)</span><strong>{data ? money(data.money_in_month) : "…"}</strong></div>
        <div><span>Purchase (month)</span><strong>{data ? money(data.purchases_month) : "…"}</strong></div>
      </section>

      <section className="nxm-section">
        <h2>Quick actions</h2>
        <div className="nxm-actions">
          {ACTIONS.filter((a) => can(a.permission)).map((a) => (
            <button key={a.action} type="button" onClick={() => runQuick(a.action)}>
              <span className={"nxm-action-icon " + a.tone}><a.icon size={20} /></span>
              <span>{a.label}</span>
            </button>
          ))}
          <Link href="/parties"><span className="nxm-action-icon neutral"><Users size={20} /></span><span>Parties</span></Link>
        </div>
      </section>

      <section className="nxm-section">
        <div className="nxm-section-head"><h2>Transactions</h2>{q.isFetching ? <span className="nxm-live">Updating…</span> : null}</div>
        <div className="nxm-chips" role="tablist" aria-label="Filter transactions">
          {FILTERS.map((f) => <button key={f.key} type="button" role="tab" aria-selected={filter === f.key} onClick={() => setFilter(f.key)}>{f.label}</button>)}
        </div>
        {q.isPending && !data ? <div className="nxm-skeleton" aria-label="Loading transactions"><i /><i /><i /></div> : rows.length === 0 ? (
          <div className="nxm-empty"><Wallet size={26} /><p>No transactions yet.</p>{can("invoices.create") ? <button type="button" className="nx-button" onClick={() => runQuick("sale")}>Add your first sale</button> : null}</div>
        ) : (
          <ul className="nxm-feed">
            {rows.map((r) => {
              const state = feedState(r);
              return (
                <li key={r.type + r.id}>
                  <Link href={r.href}>
                    <div className="nxm-feed-main">
                      <strong>{r.party || FEED_LABEL[r.type]}</strong>
                      <span>{FEED_LABEL[r.type]}{r.number ? " · " + r.number : ""}{r.date ? " · " + formatDate(r.date) : ""}</span>
                    </div>
                    <div className="nxm-feed-amount" data-type={r.type}>
                      <strong>{money(r.amount)}</strong>
                      {state ? <span data-tone={state.tone}>{state.label}{state.tone === "warn" && r.balance ? " · " + money(r.balance) : ""}</span> : <span>{r.type === "expense" ? r.status : methodLabel(r.status)}</span>}
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}

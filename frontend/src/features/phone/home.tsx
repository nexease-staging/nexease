"use client";

import { useMemo, useState } from "react";
import { ArrowDownLeft, ArrowUpRight, FileText, Receipt, Search, Users, Wallet } from "lucide-react";
import { useAuth } from "@/features/auth/auth-context";
import { runQuick } from "@/features/mobile/quick-actions";
import { useParties, type Party } from "@/features/mobile/api";
import { hasPermission } from "@/lib/authorization/permissions";
import { useDebounced } from "@/components/list/list-kit";
import { STATUS_LABEL, day, inr, useTransactions, type TxRow, type TxType } from "./api";
import { DocSheet, PartySheet } from "./sheets";
import { Empty, ErrorState, Loading } from "./bits";

type Seg = "sale" | "purchase" | "expense" | "party";
const SORTS = [["new", "Newest first"], ["old", "Oldest first"], ["high", "Amount high–low"], ["name", "Name A–Z"]] as const;

export function TxList({ type, onOpen, emptyText, emptyCta, onEmptyCta }: { type: TxType; onOpen?: (r: TxRow) => void; emptyText: string; emptyCta?: string; onEmptyCta?: () => void }) {
  const [term, setTerm] = useState("");
  const [sort, setSort] = useState<(typeof SORTS)[number][0]>("new");
  const [status, setStatus] = useState("");
  const search = useDebounced(term.trim(), 300);
  const q = useTransactions(type, search, status);
  const rows = useMemo(() => {
    const all = q.data?.pages.flatMap((p) => p.rows) ?? [];
    const by = {
      new: (a: TxRow, b: TxRow) => (b.date ?? "").localeCompare(a.date ?? ""),
      old: (a: TxRow, b: TxRow) => (a.date ?? "").localeCompare(b.date ?? ""),
      high: (a: TxRow, b: TxRow) => Number(b.amount) - Number(a.amount),
      name: (a: TxRow, b: TxRow) => a.party.localeCompare(b.party),
    }[sort];
    return [...all].sort(by);
  }, [q.data, sort]);
  const docs = type === "sale" || type === "purchase";
  const chips: [string, string][] = docs ? [["", "All"], ["due", "Unpaid"], ["paid", "Paid"], ["draft", "Draft"], ["cancelled", "Cancelled"]] : [];

  if (q.isPending) return <Loading />;
  if (q.error) return <ErrorState error={q.error} retry={() => void q.refetch()} />;
  if (!rows.length && !search && !status) return <Empty icon={type === "expense" ? Wallet : FileText} text={emptyText} cta={emptyCta} onCta={onEmptyCta} />;
  return (
    <>
      <div className="nxp-tools">
        <div className="nxp-toolrow">
          <label className="nxp-search"><Search size={18} /><input aria-label="Search this list" placeholder="Search" value={term} onChange={(e) => setTerm(e.target.value)} /></label>
          <select className="nxp-sort" aria-label="Sort order" value={sort} onChange={(e) => setSort(e.target.value as typeof sort)}>{SORTS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
        </div>
        {chips.length ? <div className="nxp-chips">{chips.map(([k, l]) => <button key={k} type="button" className={status === k ? "on" : ""} onClick={() => setStatus(k)}>{l}</button>)}</div> : null}
      </div>
      {rows.length ? rows.map((r) => (
        <div key={r.type + r.id} className="nxp-row" role={onOpen ? "button" : undefined} tabIndex={onOpen ? 0 : undefined} onClick={() => onOpen?.(r)} onKeyDown={(e) => e.key === "Enter" && onOpen?.(r)}>
          <div className="nxp-g">
            <b>{r.party || (type === "expense" ? "Expense" : "—")}</b>
            <small>
              {r.status ? <span className={"nxp-chip" + (type === "purchase" || type === "expense" || type === "payment_out" ? " red" : "")}>{STATUS_LABEL[r.status] ?? r.status}</span> : null}
              {[r.number, day(r.date)].filter(Boolean).join(" · ")}
            </small>
          </div>
          <div className={"nxp-amt" + (type === "payment_in" ? " get" : type === "payment_out" ? " give" : "")}>
            {inr(r.amount)}
            <small>{r.balance !== null ? (Number(r.balance) > 0 ? "Due " + inr(r.balance) : "Paid") : r.mode || r.note || ""}</small>
          </div>
        </div>
      )) : <div className="nxp-empty nxp-empty-sm">No results. Clear the search or filter.</div>}
      {q.hasNextPage ? <button type="button" className="nxp-more" disabled={q.isFetchingNextPage} onClick={() => void q.fetchNextPage()}>{q.isFetchingNextPage ? "Loading…" : "Show more"}</button> : null}
    </>
  );
}

function PartyRows({ side, onOpen }: { side: "customers" | "suppliers"; onOpen: (p: Party, side: "customers" | "suppliers") => void }) {
  const [term, setTerm] = useState("");
  const search = useDebounced(term.trim(), 300);
  const q = useParties(side, search);
  const customers = side === "customers";
  if (q.isPending) return <Loading />;
  if (q.error) return <ErrorState error={q.error} retry={() => void q.refetch()} />;
  const rows = q.data?.parties ?? [];
  if (!rows.length && !search) return <Empty icon={Users} text={customers ? "Add customers by GST number or name." : "Add suppliers by GST number or name."} cta={customers ? "Add customer" : "Add supplier"} onCta={() => runQuick(customers ? "customer" : "supplier")} />;
  return (
    <>
      {rows.length >= 3 || search ? <div className="nxp-tools"><label className="nxp-search"><Search size={18} /><input aria-label={`Search ${side}`} placeholder={`Search ${side}`} value={term} onChange={(e) => setTerm(e.target.value)} /></label></div> : null}
      {rows.map((p) => {
        const due = Number(p.balance ?? 0) > 0;
        return (
          <div key={p.id} className="nxp-row" role="button" tabIndex={0} onClick={() => onOpen(p, side)} onKeyDown={(e) => e.key === "Enter" && onOpen(p, side)}>
            <div className="nxp-g"><b>{p.name}</b><small>{p.gstin || p.phone || p.city || "No GSTIN"}</small></div>
            <div className={"nxp-amt" + (due ? (customers ? " get" : " give") : "")}>{p.balance === null ? "" : inr(p.balance)}<small>{p.balance === null ? "" : due ? (customers ? "You’ll get" : "You’ll give") : "Settled"}</small></div>
          </div>
        );
      })}
      {!rows.length ? <div className="nxp-empty nxp-empty-sm">No party matches.</div> : null}
    </>
  );
}

export default function PhoneHome() {
  const { authentication } = useAuth();
  const perms = authentication?.role.permissions ?? [];
  const can = (p: string) => hasPermission(perms, p);
  const segs = ([["sale", "Sales", "invoices.read"], ["purchase", "Purchases", "bills.read"], ["expense", "Expenses", "expenses.read"], ["party", "Parties", "customers.read"]] as const)
    .filter(([, , p]) => can(p) || (p === "expenses.read" && can("expenses.manage")) || (p === "customers.read" && can("suppliers.read")));
  const [seg, setSeg] = useState<Seg>(segs[0]?.[0] ?? "sale");
  const [doc, setDoc] = useState<{ type: "sale" | "purchase"; id: string } | null>(null);
  const [party, setParty] = useState<{ p: Party; side: "customers" | "suppliers" } | null>(null);
  const quick = ([["sale", "Sale", FileText, "invoices.create"], ["payment_in", "Money in", ArrowDownLeft, "invoices.record_payment"], ["purchase", "Purchase", Receipt, "bills.create"], ["payment_out", "Money out", ArrowUpRight, "bills.record_payment"]] as const)
    .filter(([, , , p]) => can(p));

  return (
    <div className="nxp-page">
      <div className="nxp-seg" role="tablist">{segs.map(([k, l]) => <button key={k} type="button" role="tab" aria-selected={seg === k} className={seg === k ? "on" : ""} onClick={() => setSeg(k)}>{l}</button>)}</div>
      {quick.length ? <div className="nxp-quick">{quick.map(([k, l, I]) => <button key={k} type="button" onClick={() => runQuick(k)}><span className="nxp-qi"><I size={19} /></span>{l}</button>)}</div> : null}
      <div className="nxp-card nxp-list">
        {seg === "sale" ? <TxList type="sale" onOpen={(r) => setDoc({ type: "sale", id: r.id })} emptyText="No invoices yet. Create your first sale." emptyCta="New sale" onEmptyCta={() => runQuick("sale")} /> : null}
        {seg === "purchase" ? <TxList type="purchase" onOpen={(r) => setDoc({ type: "purchase", id: r.id })} emptyText="No purchases yet. Record your first purchase bill." emptyCta="New purchase" onEmptyCta={() => runQuick("purchase")} /> : null}
        {seg === "expense" ? <TxList type="expense" emptyText="No expenses recorded yet." emptyCta="Add expense" onEmptyCta={() => runQuick("expense")} /> : null}
        {seg === "party" ? (
          <>
            {can("customers.read") ? <><h3 className="nxp-group">Customers</h3><PartyRows side="customers" onOpen={(p, side) => setParty({ p, side })} /></> : null}
            {can("suppliers.read") ? <><h3 className="nxp-group">Suppliers</h3><PartyRows side="suppliers" onOpen={(p, side) => setParty({ p, side })} /></> : null}
          </>
        ) : null}
      </div>
      {doc ? <DocSheet type={doc.type} id={doc.id} onClose={() => setDoc(null)} /> : null}
      {party ? <PartySheet party={party.p} side={party.side} onClose={() => setParty(null)} /> : null}
    </div>
  );
}

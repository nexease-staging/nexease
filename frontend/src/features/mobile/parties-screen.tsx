"use client";

import Link from "next/link";
import { useState } from "react";
import { CloudOff, MessageCircle, Phone, Plus, RefreshCw, Search, Users } from "lucide-react";
import { useAuth } from "@/features/auth/auth-context";
import { hasPermission } from "@/lib/authorization/permissions";
import { useDebounced } from "@/components/list/list-kit";
import { usePartyOutstanding } from "@/features/payments/api";
import { formatDate } from "@/lib/format";
import { whatsappNumber } from "@/lib/phone";
import { rupees, savedAt, useParties, useSaved, type Party, type PartyList } from "./api";
import { runQuick } from "./quick-actions";

const initials = (name: string) => name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase() || "?";

export function whatsappLink(phone: string, text: string) {
  const number = whatsappNumber(phone);
  return number ? `https://wa.me/${number}?text=${encodeURIComponent(text)}` : null;
}

/** Open invoices (or bills) for one party, shown when its row is expanded. */
function OpenDocuments({ side, partyId }: { side: "receivable" | "payable"; partyId: string }) {
  const q = usePartyOutstanding(side, partyId);
  if (q.isPending) return <p className="nxm-docs-note">Loading open {side === "receivable" ? "invoices" : "bills"}…</p>;
  if (q.isError) return <p className="nxm-docs-note">Couldn’t load documents.</p>;
  const docs = q.data?.documents ?? [];
  if (!docs.length) return <p className="nxm-docs-note">Nothing outstanding.</p>;
  return (
    <ul className="nxm-docs">
      {docs.map((d) => (
        <li key={d.id}>
          <Link href={(side === "receivable" ? "/invoices?view=" : "/vendor-bills?view=") + d.id}>
            <span><strong>{d.number}</strong><small>{d.days_overdue > 0 ? `${d.days_overdue} days overdue` : d.due_date ? "Due " + formatDate(d.due_date) : ""}</small></span>
            <span data-overdue={d.days_overdue > 0 || undefined}>{rupees(d.outstanding)}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

export function reminderText(party: Party, business: string, customers: boolean) {
  const amount = rupees(party.balance);
  return customers
    ? `Hello ${party.name}, this is a gentle reminder from ${business} that ${amount} is due on your account. Please let us know once it is paid. Thank you!`
    : `Hello ${party.name}, ${business} here. Sharing an update on our account with you (balance ${amount}).`;
}

export default function PartiesScreen() {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canCustomers = hasPermission(permissions, "customers.read");
  const canSuppliers = hasPermission(permissions, "suppliers.read");
  const [side, setSide] = useState<"customers" | "suppliers">(canCustomers || !canSuppliers ? "customers" : "suppliers");
  const [input, setInput] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const search = useDebounced(input.trim());
  const q = useParties(side, search);
  const saved = useSaved<PartyList>(`parties:${side}`);
  const offline = !q.data && q.isError && !search && saved;
  const data = q.data ?? (q.isError && !search ? saved?.data : undefined);
  const customers = side === "customers";
  const business = authentication?.organization?.name || "us";
  const canSettle = hasPermission(permissions, customers ? "invoices.record_payment" : "bills.record_payment");
  const canAdd = hasPermission(permissions, customers ? "customers.create" : "suppliers.create");

  return (
    <div className="nxm-page">
      <header className="nxm-title">
        <h1>Parties</h1>
        {canAdd ? <button type="button" className="nx-button" onClick={() => runQuick(customers ? "customer" : "supplier")}><Plus size={16} />Add {customers ? "customer" : "supplier"}</button> : null}
      </header>
      <div className="nxm-segment" role="tablist" aria-label="Party type">
        {canCustomers ? <button type="button" role="tab" aria-selected={customers} onClick={() => setSide("customers")}>Customers</button> : null}
        {canSuppliers ? <button type="button" role="tab" aria-selected={!customers} onClick={() => setSide("suppliers")}>Suppliers</button> : null}
      </div>

      {data?.total_balance != null ? (
        <div className={customers ? "nxm-total nxm-get" : "nxm-total nxm-pay"}>
          <span>{customers ? "You’ll get" : "You’ll pay"}</span>
          <strong>{rupees(data.total_balance)}</strong>
          <small>{data.with_balance} of {data.count} {customers ? "customers" : "suppliers"} with a balance</small>
        </div>
      ) : null}

      <label className="nxm-search"><Search size={18} /><input aria-label="Search parties" placeholder="Search name, phone, GSTIN" value={input} onChange={(e) => setInput(e.target.value)} /></label>
      {offline ? <p className="nxm-offline" role="status"><CloudOff size={15} />Offline — showing the list saved {savedAt(saved.at)}.</p> : null}
      {q.isError && !data ? <div role="alert" className="nxm-error">Couldn’t load parties.<button type="button" onClick={() => void q.refetch()}><RefreshCw size={15} />Try again</button></div> : null}

      {q.isPending && !data ? <div className="nxm-skeleton" aria-label="Loading parties"><i /><i /><i /></div> : data && data.parties.length === 0 ? (
        <div className="nxm-empty"><Users size={26} /><p>{search ? "No party matches your search." : `No ${side} yet.`}</p></div>
      ) : (
        <ul className="nxm-parties">
          {data?.parties.map((p) => {
            const due = Number(p.balance ?? 0) > 0;
            return (
              <li key={p.id}>
                <button type="button" className="nxm-party-main" aria-expanded={expanded === p.id} onClick={() => setExpanded(expanded === p.id ? null : p.id)}>
                  <span className="nxm-avatar" aria-hidden>{initials(p.name)}</span>
                  <span className="min-w-0">
                    <strong>{p.name}</strong>
                    <small>{[p.phone, p.city].filter(Boolean).join(" · ") || p.code}</small>
                  </span>
                  <span className="nxm-party-balance" data-side={customers ? "get" : "pay"} data-due={due || undefined}>
                    <strong>{p.balance == null ? "" : rupees(p.balance)}</strong>
                    <small>{p.balance == null ? "" : due ? (customers ? "You’ll get" : "You’ll pay") : "Settled"}</small>
                  </span>
                </button>
                {expanded === p.id && p.balance != null ? <OpenDocuments side={customers ? "receivable" : "payable"} partyId={p.id} /> : null}
                <div className="nxm-party-actions">
                  {p.phone ? <a href={`tel:${p.phone.replace(/[^\d+]/g, "")}`} aria-label={`Call ${p.name}`}><Phone size={16} />Call</a> : null}
                  {p.phone && whatsappLink(p.phone, "") ? <a href={whatsappLink(p.phone, reminderText(p, business, customers))!} target="_blank" rel="noopener noreferrer" aria-label={`WhatsApp ${p.name}`}><MessageCircle size={16} />{customers && due ? "Remind" : "WhatsApp"}</a> : null}
                  {canSettle && due ? <button type="button" onClick={() => runQuick(customers ? "payment_in" : "payment_out", p.id)}>{customers ? "Receive" : "Pay"}</button> : null}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

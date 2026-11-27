"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowDownLeft, ArrowUpRight, Download, ExternalLink, FileText, Loader2, Mail, MessageCircle, Phone, Send } from "lucide-react";
import { notify } from "@/components/nex-feedback";
import { runQuick } from "@/features/mobile/quick-actions";
import type { Party } from "@/features/mobile/api";
import { fetchPdf, openShare, waLink } from "@/features/share/api";
import { downloadBlob } from "@/lib/browser/download";
import { STATUS_LABEL, day, inr, useDocument } from "./api";
import { ErrorState, Loading, Sheet } from "./bits";

function Action({ icon: Icon, label, onClick, href, busy, external }: { icon: typeof Send; label: string; onClick?: () => void; href?: string; busy?: boolean; external?: boolean }) {
  const inner = <><span className="nxp-qi">{busy ? <Loader2 size={19} className="animate-spin" /> : <Icon size={19} />}</span>{label}</>;
  if (href) return external ? <a href={href} target="_blank" rel="noopener noreferrer">{inner}</a> : <Link href={href}>{inner}</Link>;
  return <button type="button" onClick={onClick} disabled={busy}>{inner}</button>;
}

export function DocSheet({ type, id, onClose }: { type: "sale" | "purchase"; id: string; onClose: () => void }) {
  const q = useDocument(type, id);
  const d = q.data;
  const [busy, setBusy] = useState(false);
  const kind = type === "sale" ? "invoice" : "bill";
  const pdf = async () => {
    setBusy(true);
    try {
      const r = await fetchPdf({ kind, id });
      await downloadBlob(r.blob, r.filename || `${d?.number || "document"}.pdf`);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Could not prepare the PDF.", "error");
    } finally {
      setBusy(false);
    }
  };
  return (
    <Sheet title={d ? `${type === "sale" ? "Invoice" : "Bill"} ${d.number}` : "Loading…"} sub={d ? d.party.name : undefined} onClose={onClose}>
      {q.isPending ? <Loading /> : q.error ? <ErrorState error={q.error} retry={() => void q.refetch()} /> : d ? (
        <div className="nxp-stack">
          <div className="nxp-meta">
            <span className={"nxp-chip" + (d.status === "CANCELLED" ? " red" : "")}>{STATUS_LABEL[d.status] ?? d.status}</span>
            <span>{day(d.date)}{d.due_date ? ` · due ${day(d.due_date)}` : ""}</span>
          </div>
          <div className="nxp-tot">
            <div><span>Total</span><b>{inr(d.total)}</b></div>
            <div><span>{type === "sale" ? "Received" : "Paid"}</span><b>{inr(d.paid)}</b></div>
            <div><span>Balance</span><b className={Number(d.balance) > 0 ? (type === "sale" ? "get" : "give") : ""}>{inr(d.balance)}</b></div>
          </div>
          <div className="nxp-grid3 nxp-actions">
            <Action icon={MessageCircle} label="WhatsApp" onClick={() => openShare({ kind, id, channel: "whatsapp", title: d.number })} />
            <Action icon={Mail} label="Email" onClick={() => openShare({ kind, id, channel: "email", title: d.number })} />
            <Action icon={Download} label="PDF" onClick={() => void pdf()} busy={busy} />
            {d.can_pay ? <Action icon={type === "sale" ? ArrowDownLeft : ArrowUpRight} label={type === "sale" ? "Receive payment" : "Make payment"} onClick={() => { onClose(); runQuick(type === "sale" ? "payment_in" : "payment_out", d.party.id); }} /> : null}
            {d.party.phone ? <Action icon={Phone} label="Call" href={`tel:${d.party.phone.replace(/[^\d+]/g, "")}`} external /> : null}
            <Action icon={ExternalLink} label="Open full" href={d.href} />
          </div>
          {d.lines.length ? (
            <div>
              <h3 className="nxp-group">Items</h3>
              {d.lines.map((l, i) => (
                <div className="nxp-row" key={i}>
                  <div className="nxp-g"><b>{l.name}</b><small>{l.qty} {l.unit} × {inr(l.rate)}{Number(l.tax_rate) ? ` · GST ${l.tax_rate}%` : ""}</small></div>
                  <div className="nxp-amt">{inr(l.amount)}</div>
                </div>
              ))}
              <div className="nxp-sum">
                <div><span>Taxable</span><span>{inr(d.subtotal)}</span></div>
                {Number(d.discount) ? <div><span>Discount</span><span>−{inr(d.discount)}</span></div> : null}
                <div><span>GST</span><span>{inr(d.tax)}</span></div>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </Sheet>
  );
}

export function PartySheet({ party, side, onClose }: { party: Party; side: "customers" | "suppliers"; onClose: () => void }) {
  const customers = side === "customers";
  const due = Number(party.balance ?? 0) > 0;
  const tel = party.phone.replace(/[^\d+]/g, "");
  return (
    <Sheet title={party.name} sub={[party.gstin, party.phone, party.city].filter(Boolean).join(" · ") || party.code} onClose={onClose}>
      <div className="nxp-stack">
        {party.balance !== null ? (
          <div className="nxp-tot">
            <div><span>{due ? (customers ? "You’ll get" : "You’ll give") : "Balance"}</span><b className={due ? (customers ? "get" : "give") : ""}>{inr(party.balance)}</b></div>
            {Number(party.overdue ?? 0) > 0 ? <div><span>Overdue</span><b className="give">{inr(party.overdue)}</b></div> : null}
          </div>
        ) : null}
        <div className="nxp-grid3 nxp-actions">
          <Action icon={FileText} label="Share statement" onClick={() => openShare({ kind: "statement", id: party.id, side: customers ? "customer" : "supplier", title: party.name })} />
          {due ? <Action icon={customers ? ArrowDownLeft : ArrowUpRight} label={customers ? "Receive payment" : "Make payment"} onClick={() => { onClose(); runQuick(customers ? "payment_in" : "payment_out", party.id); }} /> : null}
          {customers ? <Action icon={Send} label="New sale" onClick={() => { onClose(); runQuick("sale"); }} /> : <Action icon={Send} label="New purchase" onClick={() => { onClose(); runQuick("purchase"); }} />}
          {tel ? <Action icon={Phone} label="Call" href={`tel:${tel}`} external /> : null}
          {tel ? <Action icon={MessageCircle} label="WhatsApp" href={waLink(party.phone, `Dear ${party.name},`)} external /> : null}
          <Action icon={ExternalLink} label="Open full" href={customers ? "/customers" : "/suppliers"} />
        </div>
      </div>
    </Sheet>
  );
}

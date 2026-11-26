"use client";

import { useMemo, useState } from "react";
import { AlarmClock, CheckCircle2, FileSpreadsheet, HandCoins, IndianRupee, Mail, MessageCircle, Users, Wallet } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, type ListAction } from "@/components/list/list-kit";
import { Badge } from "@/components/ui/badge";
import EmptyState from "@/components/ui/empty-state";
import StatCard from "@/components/ui/stat-card";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import { apiRequest } from "@/lib/api/client";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { whatsappNumber } from "@/lib/phone";
import { formatCompactMoney, formatDate, formatMoney } from "@/lib/format";
import { BUCKETS, usePartyOutstanding, useOutstanding, type PartySummary, type Side } from "../api";
import { mailtoUrl, openExternal, reminderText, whatsappUrl } from "../reminder";
import SettleSheet from "./settle-sheet";

type View = "all" | "overdue" | "d90";
const views: Array<{ value: View; label: string }> = [
  { value: "all", label: "All" },
  { value: "overdue", label: "Overdue" },
  { value: "d90", label: "90+ days" },
];

function AgingBar({ party }: { party: PartySummary }) {
  const total = Number(party.outstanding) || 1;
  return (
    <span className="nxp-aging" aria-hidden="true">
      {BUCKETS.map((b) => {
        const share = (Number(party.buckets[b.key]) / total) * 100;
        return share > 0 ? <span key={b.key} data-b={b.key} style={{ width: `${share}%` }} /> : null;
      })}
    </span>
  );
}

function OpenDocuments({ side, party, children }: { side: Side; party: PartySummary; children?: React.ReactNode }) {
  const docs = usePartyOutstanding(side, party.id);
  if (docs.isLoading) return <div className="nx-skeleton h-16" aria-busy="true" />;
  if (docs.error) return <p role="alert" className="nxl-error">{docs.error.message}</p>;
  return (
    <ul className="nxp-docs" aria-label={`Open ${side === "receivable" ? "invoices" : "bills"} for ${party.name}`}>
      {(docs.data?.documents ?? []).map((d) => (
        <li key={d.id}>
          <span>
            <strong>{d.number}</strong>{" · "}
            <span data-late={d.days_overdue > 0 || undefined}>{d.days_overdue > 0 ? `${d.days_overdue} days overdue` : d.due_date ? `due ${formatDate(d.due_date)}` : formatDate(d.date)}</span>
          </span>
          <span>{formatMoney(d.outstanding)}</span>
        </li>
      ))}
      {children ? <li className="nxp-docs-actions">{children}</li> : null}
    </ul>
  );
}

/** Receivables (customers who owe you) and payables (suppliers you owe), one shared screen. */
export default function OutstandingScreen({ side }: { side: Side }) {
  const receivable = side === "receivable";
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canRead = hasPermission(permissions, receivable ? "invoices.read" : "bills.read");
  const canSettle = hasPermission(permissions, receivable ? "invoices.record_payment" : "bills.record_payment");
  const business = authentication?.organization?.name ?? "";

  const [view, setView] = useState<View>("all");
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const [settling, setSettling] = useState<{ partyId?: string } | null>(null);
  const data = useOutstanding(side, canRead);

  const parties = useMemo(() => {
    const term = search.trim().toLowerCase();
    return (data.data?.parties ?? []).filter((p) =>
      (!term || `${p.name} ${p.code} ${p.phone}`.toLowerCase().includes(term))
      && (view === "all" || (view === "overdue" ? Number(p.overdue) > 0 : Number(p.buckets.d90_plus) > 0)));
  }, [data.data, search, view]);

  if (!authentication) return null;
  const title = receivable ? "Receivables" : "Payables";
  if (!canRead) {
    return <div className="nx-card"><EmptyState icon={Wallet} title={`${title} unavailable`} description={`Your role does not include the ${receivable ? "invoices.read" : "bills.read"} permission.`} /></div>;
  }

  const totals = data.data?.totals;
  const partyWord = receivable ? "customer" : "supplier";

  function exportCsv() {
    void downloadCsv(`NexEase-${receivable ? "receivables" : "payables"}-aging-${data.data?.as_of ?? ""}`, parties, [
      { header: receivable ? "Customer" : "Supplier", value: (p) => p.name },
      { header: "Code", value: (p) => p.code },
      { header: "Phone", value: (p) => p.phone },
      { header: "Open documents", value: (p) => p.open_count },
      ...BUCKETS.map((b) => ({ header: b.label, value: (p: PartySummary) => p.buckets[b.key] })),
      { header: "Overdue", value: (p) => p.overdue },
      { header: "Outstanding", value: (p) => p.outstanding },
      { header: "Oldest due", value: (p) => p.oldest_due },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  async function remind(party: PartySummary, channel: "whatsapp" | "email") {
    let docs: Parameters<typeof reminderText>[2] = [];
    try {
      docs = (await apiRequest<{ documents: Parameters<typeof reminderText>[2] }>(`/business/payments/outstanding/?side=receivable&party_id=${party.id}`)).data.documents;
    } catch {
      docs = [];
    }
    const text = reminderText(party, business, docs);
    openExternal(channel === "whatsapp" ? whatsappUrl(party.phone, text) : mailtoUrl(party.email, `Payment reminder from ${business || "us"}`, text));
  }

  const cards = (
    <div className="nx-kpi-strip" data-cols="4">
      <div><StatCard label={receivable ? "To collect" : "To pay"} icon={IndianRupee} tone="info" loading={data.isLoading} value={formatCompactMoney(totals?.outstanding)} title={formatMoney(totals?.outstanding)} hint={`${data.data?.document_count ?? 0} open ${receivable ? "invoices" : "bills"}`} /></div>
      <button type="button" className="text-left" aria-label={`Show overdue ${partyWord}s`} onClick={() => setView("overdue")}>
        <StatCard label="Overdue" icon={AlarmClock} tone={Number(totals?.overdue) ? "danger" : "success"} loading={data.isLoading} value={formatCompactMoney(totals?.overdue)} title={formatMoney(totals?.overdue)} hint="Past the due date" />
      </button>
      <button type="button" className="text-left" aria-label={`Show ${partyWord}s 90+ days overdue`} onClick={() => setView("d90")}>
        <StatCard label="90+ days" icon={AlarmClock} tone={Number(totals?.buckets.d90_plus) ? "warning" : "success"} loading={data.isLoading} value={formatCompactMoney(totals?.buckets.d90_plus)} title={formatMoney(totals?.buckets.d90_plus)} hint={receivable ? "Follow up first" : "Oldest dues"} />
      </button>
      <div><StatCard label={receivable ? "Customers" : "Suppliers"} icon={Users} tone="violet" loading={data.isLoading} value={String(data.data?.party_count ?? 0)} hint={`with ${receivable ? "money due" : "bills to pay"}`} /></div>
    </div>
  );

  const legend = (
    <div className="nxp-legend" aria-label="Aging colours">
      {BUCKETS.map((b) => <span key={b.key}><i data-b={b.key} />{b.label} {formatCompactMoney(totals?.buckets[b.key])}</span>)}
    </div>
  );

  return (
    <>
      <ListScreen<View>
        title={title}
        subtitle={receivable ? "Who owes you, how late, and one tap to collect." : "What you owe suppliers, oldest first."}
        primary={canSettle ? { label: receivable ? "Receive payment" : "Pay supplier", icon: receivable ? HandCoins : Wallet, onClick: () => setSettling({}) } : null}
        actions={[{ icon: FileSpreadsheet, label: `Export ${title.toLowerCase()} aging`, onClick: exportCsv, disabled: !parties.length }]}
        onRefresh={() => void data.refetch()}
        refreshing={data.isFetching}
        above={cards}
        search={{ value: search, onChange: setSearch, placeholder: `Search ${partyWord}s`, label: `Search ${partyWord}s` }}
        chips={{ options: views, value: view, onChange: setView, label: `${title} filter` }}
      >
        {data.data?.document_count ? legend : null}
        <ListState loading={data.isPending} error={data.error} onRetry={() => void data.refetch()} isEmpty={!parties.length} emptyIcon={CheckCircle2}
          emptyTitle={search || view !== "all" ? `No ${partyWord}s match` : receivable ? "Nothing to collect" : "Nothing to pay"}
          emptyDescription={search || view !== "all" ? "Try another search or filter." : receivable ? "Every issued invoice is paid." : "Every posted bill is paid."}>
          <CompactList label={title} columns={[{ label: receivable ? "Customer" : "Supplier" }, { label: "Overdue" }, { label: "Oldest due" }, { label: "Outstanding" }]}>
            {parties.map((p) => {
              const late = p.max_days_overdue;
              const actions: ListAction[] = [
                ...(canSettle ? [{ icon: receivable ? HandCoins : Wallet, label: `${receivable ? "Receive from" : "Pay"} ${p.name}`, onClick: () => setSettling({ partyId: p.id }) }] : []),
                ...(receivable && whatsappNumber(p.phone) ? [{ icon: MessageCircle, label: `WhatsApp reminder to ${p.name}`, onClick: () => void remind(p, "whatsapp") }] : []),
                ...(receivable && p.email ? [{ icon: Mail, label: `Email reminder to ${p.name}`, onClick: () => void remind(p, "email") }] : []),
              ];
              return (
                <CompactRow
                  key={p.id}
                  title={p.name}
                  subtitle={<>{p.open_count} open {receivable ? "invoice" : "bill"}{p.open_count === 1 ? "" : "s"}{late > 0 ? ` · ${late} days late` : ""}<AgingBar party={p} /></>}
                  meta={[Number(p.overdue) ? formatMoney(p.overdue) : "—", p.oldest_due ? formatDate(p.oldest_due) : "—"]}
                  amount={formatMoney(p.outstanding)}
                  amountTone={Number(p.overdue) ? "danger" : undefined}
                  badge={late > 90 ? <Badge tone="danger">90+ days</Badge> : late > 0 ? <Badge tone="warning">Overdue</Badge> : <Badge tone="success">Not due</Badge>}
                  actions={actions}
                  onOpen={() => setOpen(open === p.id ? null : p.id)}
                  openLabel={`${open === p.id ? "Hide" : "Show"} open ${receivable ? "invoices" : "bills"} for ${p.name}`}
                  expanded={open === p.id}
                >
                  <OpenDocuments side={side} party={p}>
                    {actions.map((a) => (
                      <button key={a.label} type="button" className="nx-button nx-secondary nx-btn-sm" onClick={a.onClick}>
                        <a.icon size={15} aria-hidden="true" />
                        {a.label.startsWith("WhatsApp") ? "WhatsApp reminder" : a.label.startsWith("Email") ? "Email reminder" : receivable ? "Receive payment" : "Pay"}
                      </button>
                    ))}
                  </OpenDocuments>
                </CompactRow>
              );
            })}
          </CompactList>
        </ListState>
        {data.data?.truncated ? <p className="nxf-hint p-3">Showing the oldest 5,000 open documents.</p> : null}
      </ListScreen>
      {settling ? <SettleSheet side={side} partyId={settling.partyId} onClose={() => setSettling(null)} /> : null}
    </>
  );
}

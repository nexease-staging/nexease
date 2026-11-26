"use client";

import { useState } from "react";
import { ArrowDownLeft, ArrowUpRight, FileSpreadsheet, FileText, HandCoins, IndianRupee, MessageCircle, Scale, Wallet } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager, useDebounced, type ListAction } from "@/components/list/list-kit";
import EmptyState from "@/components/ui/empty-state";
import FilterSheet from "@/components/ui/filter-sheet";
import StatCard from "@/components/ui/stat-card";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import CustomerPaymentDetailDialog from "@/features/customer-payments/components/customer-payment-detail-dialog";
import { apiRequest } from "@/lib/api/client";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadCsv } from "@/lib/export-csv";
import { formatCompactMoney, formatDate, formatMoney } from "@/lib/format";
import { whatsappNumber } from "@/lib/phone";
import { METHODS, methodLabel, useOutstanding, usePaymentRegister, type Direction, type RegisterData, type RegisterPayment, type RegisterParams } from "../api";
import { openExternal, whatsappUrl } from "../reminder";
import SettleSheet from "./settle-sheet";

const directions: Array<{ value: Direction; label: string }> = [
  { value: "all", label: "All" },
  { value: "in", label: "Money in" },
  { value: "out", label: "Money out" },
];

/** Financial year in India runs April to March. */
function periods() {
  const now = new Date(Date.now() + 330 * 60_000);
  const iso = (d: Date) => d.toISOString().slice(0, 10);
  const y = now.getUTCFullYear(), m = now.getUTCMonth();
  const fyStart = m >= 3 ? y : y - 1;
  return [
    { label: "This month", from: iso(new Date(Date.UTC(y, m, 1))), to: "" },
    { label: "Last month", from: iso(new Date(Date.UTC(y, m - 1, 1))), to: iso(new Date(Date.UTC(y, m, 0))) },
    { label: `FY ${fyStart}-${String(fyStart + 1).slice(2)}`, from: `${fyStart}-04-01`, to: "" },
    { label: "All time", from: "", to: "" },
  ];
}

function receiptText(p: RegisterPayment, business: string) {
  const docs = p.documents.map((d) => d.number).filter(Boolean).join(", ");
  return [`Namaste ${p.party.name},`, "", `We have received ${formatMoney(p.amount)} by ${methodLabel(p.method)} on ${formatDate(p.date)}.`,
    `Receipt: ${p.number}${docs ? ` · Against: ${docs}` : ""}${p.reference ? ` · Ref: ${p.reference}` : ""}`, "", `Thank you! — ${business || "Team"}`].join("\n");
}

export default function RegisterScreen({ title, subtitle, initialDirection = "all", lockDirection = false }: {
  title: string;
  subtitle: string;
  initialDirection?: Direction;
  lockDirection?: boolean;
}) {
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const canIn = hasPermission(permissions, "invoices.read") || hasPermission(permissions, "customer_payments.read");
  const canOut = hasPermission(permissions, "bills.read");
  const canReceive = hasPermission(permissions, "invoices.record_payment");
  const canPay = hasPermission(permissions, "bills.record_payment");
  const business = authentication?.organization?.name ?? "";

  const [chosenDirection, setDirection] = useState<Direction>(initialDirection);
  // Without permission for one side, "all" quietly means the side the user can see.
  const direction: Direction = chosenDirection === "all" && !(canIn && canOut) ? (canIn ? "in" : "out") : chosenDirection;
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounced(searchInput.trim());
  const [method, setMethod] = useState("");
  const [range, setRange] = useState({ from: "", to: "" });
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<string | null>(null);
  const [settling, setSettling] = useState<"receivable" | "payable" | null>(null);

  const allowed = direction === "in" ? canIn : direction === "out" ? canOut : canIn || canOut;
  const params: RegisterParams = { direction, page, search: search || undefined, method: method || undefined, from: range.from || undefined, to: range.to || undefined };
  const register = usePaymentRegister(params, allowed);
  const receivables = useOutstanding("receivable", canIn && direction !== "out");
  const payables = useOutstanding("payable", canOut && direction === "out");

  if (!authentication) return null;
  if (!allowed) {
    return <div className="nx-card"><EmptyState icon={Wallet} title={`${title} unavailable`} description="Your role does not include permission to read payments." /></div>;
  }

  const data = register.data;
  const summary = data?.summary;
  const rows = data?.payments ?? [];
  const filtersActive = Boolean(method || range.from || range.to);
  const reset = (fn: () => void) => { fn(); setPage(1); };
  const pagination = data ? { page: data.pagination.page, total_pages: data.pagination.pages, total_items: data.pagination.total, has_next: data.pagination.page < data.pagination.pages, has_previous: data.pagination.page > 1 } : null;

  async function exportCsv() {
    try {
      const all: RegisterPayment[] = [];
      for (let p = 1; p <= 50; p += 1) {
        const query = new URLSearchParams(Object.entries({ ...params, page: String(p), page_size: "100" }).filter(([, v]) => v !== undefined && v !== "") as Array<[string, string]>);
        const chunk = (await apiRequest<RegisterData>(`/business/payments/register/?${query}`)).data;
        all.push(...chunk.payments);
        if (p >= chunk.pagination.pages) break;
      }
      await downloadCsv(`NexEase-payments-${range.from || "all"}-${range.to || "today"}`, all, [
        { header: "Date", value: (r) => r.date }, { header: "Number", value: (r) => r.number },
        { header: "Direction", value: (r) => (r.direction === "in" ? "Money in" : "Money out") },
        { header: "Party", value: (r) => r.party.name }, { header: "Method", value: (r) => methodLabel(r.method) },
        { header: "Account", value: (r) => r.account.name }, { header: "Reference", value: (r) => r.reference },
        { header: "Against", value: (r) => r.documents.map((d) => d.number).join(" ") },
        { header: "Amount", value: (r) => (r.direction === "in" ? r.amount : `-${r.amount}`) },
      ]);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Export failed.", "error");
    }
  }

  const topMethod = summary ? Object.entries(summary.by_method).sort((a, b) => Number(b[1].in) + Number(b[1].out) - Number(a[1].in) - Number(a[1].out))[0] : undefined;
  const cards = (
    <div className="nx-kpi-strip" data-cols="4">
      {direction !== "out" ? (
        <button type="button" className="text-left" aria-label="Show money in" disabled={lockDirection} onClick={() => reset(() => setDirection("in"))}>
          <StatCard label="Money in" icon={ArrowDownLeft} tone="success" loading={register.isLoading} value={formatCompactMoney(summary?.money_in)} title={formatMoney(summary?.money_in)} hint="Received from customers" />
        </button>
      ) : null}
      {direction !== "in" ? (
        <button type="button" className="text-left" aria-label="Show money out" disabled={lockDirection} onClick={() => reset(() => setDirection("out"))}>
          <StatCard label="Money out" icon={ArrowUpRight} tone="danger" loading={register.isLoading} value={formatCompactMoney(summary?.money_out)} title={formatMoney(summary?.money_out)} hint="Paid to suppliers" />
        </button>
      ) : null}
      {direction === "all" ? (
        <div><StatCard label="Net" icon={Scale} tone={Number(summary?.net) < 0 ? "warning" : "info"} loading={register.isLoading} value={Number(summary?.net) < 0 ? `−${formatCompactMoney(Math.abs(Number(summary?.net)))}` : formatCompactMoney(summary?.net)} title={formatMoney(summary?.net)} hint={`${summary?.count ?? 0} payments`} /></div>
      ) : (
        <div><StatCard label="Payments" icon={FileText} tone="info" loading={register.isLoading} value={String(summary?.count ?? 0)} hint={topMethod ? `Mostly ${methodLabel(topMethod[0])}` : "In this period"} /></div>
      )}
      {canIn && direction !== "out" ? <div><StatCard label="To collect" icon={IndianRupee} tone="violet" href="/accounts-receivable" loading={receivables.isLoading} value={formatCompactMoney(receivables.data?.totals.outstanding)} hint={`${formatCompactMoney(receivables.data?.totals.overdue)} overdue`} /></div> : null}
      {direction === "out" && canOut ? <div><StatCard label="To pay" icon={Wallet} tone="warning" href="/accounts-payable" loading={payables.isLoading} value={formatCompactMoney(payables.data?.totals.outstanding)} hint={`${formatCompactMoney(payables.data?.totals.overdue)} overdue`} /></div> : null}
    </div>
  );

  const primary = canReceive && direction !== "out" ? { label: "Receive payment", icon: HandCoins, onClick: () => setSettling("receivable" as const) }
    : canPay && direction !== "in" ? { label: "Pay supplier", icon: Wallet, onClick: () => setSettling("payable" as const) } : null;
  const actions: ListAction[] = [
    ...(primary?.label === "Receive payment" && canPay && direction === "all" ? [{ icon: Wallet, label: "Pay supplier", onClick: () => setSettling("payable") }] : []),
    { icon: FileSpreadsheet, label: "Export payments CSV", onClick: () => void exportCsv(), disabled: !rows.length },
  ];

  return (
    <>
      <ListScreen<Direction>
        title={title}
        subtitle={subtitle}
        primary={primary}
        actions={actions}
        onRefresh={() => void register.refetch()}
        refreshing={register.isFetching}
        above={cards}
        search={{ value: searchInput, onChange: (v) => reset(() => setSearchInput(v)), placeholder: "Search party, number or reference", label: "Search payments" }}
        onOpenFilters={() => setFiltersOpen(true)}
        filtersActive={filtersActive}
        chips={lockDirection || !(canIn && canOut) ? undefined : { options: directions, value: direction, onChange: (v) => reset(() => setDirection(v)), label: "Payment direction" }}
        footer={<Pager pagination={pagination} noun="payments" onPage={setPage} />}
      >
        <ListState loading={register.isPending} error={register.error} onRetry={() => void register.refetch()} isEmpty={!rows.length} emptyIcon={Wallet}
          emptyTitle={search || filtersActive ? "No payments match" : "No payments yet"}
          emptyDescription={search || filtersActive ? "Try another search, period or method." : "Payments you receive or make show up here."}
          emptyAction={!search && !filtersActive && primary ? <button type="button" className="nx-button" onClick={primary.onClick}><primary.icon size={16} />{primary.label}</button> : null}>
          <CompactList label={title} columns={[{ label: "Party / payment" }, { label: "Against" }, { label: "Account" }, { label: "Amount" }]}>
            {rows.map((p) => {
              const incoming = p.direction === "in";
              const docs = p.documents.map((d) => d.number).filter(Boolean);
              const rowActions: ListAction[] = [
                ...(incoming ? [{ icon: FileText, label: `Open receipt ${p.number}`, onClick: () => setReceipt(p.id) }] : []),
                ...(incoming && whatsappNumber(p.party.phone) ? [{ icon: MessageCircle, label: `Share receipt ${p.number} on WhatsApp`, onClick: () => openExternal(whatsappUrl(p.party.phone, receiptText(p, business))) }] : []),
              ];
              return (
                <CompactRow
                  key={`${p.direction}-${p.id}`}
                  title={<span className="inline-flex items-center gap-1.5">{incoming ? <ArrowDownLeft size={15} aria-label="Money in" style={{ color: "var(--nx-success-fg)" }} /> : <ArrowUpRight size={15} aria-label="Money out" style={{ color: "var(--nx-danger-fg)" }} />}{p.party.name || "—"}</span>}
                  subtitle={`${p.number} · ${formatDate(p.date)} · ${methodLabel(p.method)}`}
                  meta={[docs.length ? (docs.length > 2 ? `${docs.slice(0, 2).join(", ")} +${docs.length - 2}` : docs.join(", ")) : "—", p.account.name || "—"]}
                  amount={`${incoming ? "+" : "−"} ${formatMoney(p.amount)}`}
                  amountTone={incoming ? "success" : "danger"}
                  amountHint={p.reference || undefined}
                  actions={rowActions}
                  onOpen={() => setExpanded(expanded === p.id ? null : p.id)}
                  openLabel={`${expanded === p.id ? "Hide" : "Show"} details of ${p.number}`}
                  expanded={expanded === p.id}
                >
                  <ul className="nxp-docs" aria-label={`${p.number} details`}>
                    {p.documents.map((d) => <li key={d.id}><span>{incoming ? "Invoice" : "Bill"} {d.number || "—"}</span><span>{formatMoney(d.amount)}</span></li>)}
                    {p.reference ? <li><span>Reference</span><span>{p.reference}</span></li> : null}
                    {p.notes ? <li><span>Notes</span><span className="font-normal">{p.notes}</span></li> : null}
                  </ul>
                </CompactRow>
              );
            })}
          </CompactList>
        </ListState>
      </ListScreen>

      <FilterSheet open={filtersOpen} onClose={() => setFiltersOpen(false)}>
        <div>
          <p className="mb-2 text-sm font-semibold">Period</p>
          <div className="nx-chip-row" role="group" aria-label="Period">
            {periods().map((p) => <button key={p.label} type="button" className="nx-chip" aria-pressed={range.from === p.from && range.to === p.to} onClick={() => reset(() => setRange({ from: p.from, to: p.to }))}>{p.label}</button>)}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm font-semibold">From<input className="nx-input mt-1" type="date" aria-label="From date" value={range.from} onChange={(e) => reset(() => setRange((r) => ({ ...r, from: e.target.value })))} /></label>
          <label className="text-sm font-semibold">To<input className="nx-input mt-1" type="date" aria-label="To date" value={range.to} onChange={(e) => reset(() => setRange((r) => ({ ...r, to: e.target.value })))} /></label>
        </div>
        <label className="block text-sm font-semibold">Method
          <select className="nx-input mt-1" aria-label="Payment method filter" value={method} onChange={(e) => reset(() => setMethod(e.target.value))}>
            <option value="">All methods</option>
            {METHODS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select>
        </label>
        {filtersActive ? <button type="button" className="nx-button nx-secondary" onClick={() => reset(() => { setMethod(""); setRange({ from: "", to: "" }); })}>Clear filters</button> : null}
      </FilterSheet>

      <CustomerPaymentDetailDialog open={Boolean(receipt)} paymentId={receipt} onClose={() => setReceipt(null)} />
      {settling ? <SettleSheet side={settling} onClose={() => setSettling(null)} /> : null}
    </>
  );
}

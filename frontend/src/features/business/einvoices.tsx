"use client";

import { useState, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Ban, CheckCircle2, Clock, Download, FileText, Layers, RefreshCw, Send, ShieldCheck, Truck } from "lucide-react";
import PasswordInput from "@/components/password-input";
import { CompactList, CompactRow, ListScreen, ListState, useDebounced, type ListAction } from "@/components/list/list-kit";
import { Badge, type Tone } from "@/components/ui/badge";
import StatCard from "@/components/ui/stat-card";
import { FormSheet } from "@/components/form/form-sheet";
import { confirmAction, notify } from "@/components/nex-feedback";
import { formatDate } from "@/lib/format";
import { apiBinaryRequest, apiRequest } from "@/lib/api/client";
import { downloadBlob } from "@/lib/browser/download";

export type Kind = "invoice" | "credit_note";
export type Row = {
  id: string; kind: Kind; number: string; date: string; customer: string; invoice_status: string; total: string; category: string;
  days_left: number | null; late: boolean; status?: string; irn?: string; ack_no?: string; ack_date?: string; cancel_date?: string;
  invoice_number?: string; invoice_irn?: string; export?: boolean; auto_error?: string;
};
export type Listing = {
  records: Row[]; summary: { to_register: number; due_soon: number; late: number; pending: number };
  configured: boolean; gstin: string; environment: string; preferences: { turnover_10cr: boolean; auto_generate: boolean };
  categories: Record<string, string>; reporting_days: number; bulk_limit: number;
  can_configure: boolean; can_issue: boolean; can_cancel: boolean;
};
type BulkResult = { id: string; number?: string; ok: boolean; message?: string };

const path = "/business/e-invoices/";
const input = "nx-input w-full";
const IRN_STATUS: Record<string, { label: string; tone: Tone }> = {
  registered: { label: "IRN registered", tone: "success" }, pending: { label: "Check status", tone: "warning" },
  cancel_pending: { label: "Cancelling", tone: "warning" }, cancelled: { label: "IRN cancelled", tone: "danger" },
};

export function deadline(row: Pick<Row, "days_left" | "status" | "invoice_status">, strict: boolean): { label: string; tone: Tone } | null {
  if (row.status || row.days_left === null || row.invoice_status === "CANCELLED") return null;
  const d = row.days_left;
  if (d < 0) return { label: strict ? "Past 30 days" : `${-d} day${d === -1 ? "" : "s"} past 30`, tone: strict ? "danger" : "warning" };
  if (d === 0) return { label: "Last day", tone: "danger" };
  if (d <= 5) return { label: `${d} day${d === 1 ? "" : "s"} left`, tone: "warning" };
  return { label: `${d} days left`, tone: "neutral" };
}

function GenerateSheet({ row, data, busy, onClose, onSubmit }: { row: Row; data: Listing; busy: boolean; onClose: () => void; onSubmit: (body: Record<string, unknown>) => void }) {
  const [category, setCategory] = useState(row.kind === "credit_note" ? row.category || "B2B" : row.export ? "EXPWOP" : "B2B");
  const exportSupply = category.startsWith("EXP");
  const submit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.currentTarget).entries()) as Record<string, string>;
    onSubmit({ action: "generate", id: row.id, kind: row.kind, category, ...(exportSupply ? { export: { country: f.country, currency: f.currency, port: f.port, shipping_bill: f.shipping_bill, shipping_bill_date: f.shipping_bill_date } } : {}) });
  };
  return (
    <FormSheet title={`Register ${row.number} with the IRP`} subtitle={`${row.customer} · ${formatDate(row.date)} · ${data.environment === "live" ? "LIVE IRP" : "TEST IRP"}`} onClose={onClose} busy={busy} size="md">
      <form onSubmit={submit}>
        {row.kind === "invoice" ? (
          <div className="nxf-grid">
            <label className="sm:col-span-2">Type of supply
              <select className={input} value={category} onChange={(e) => setCategory(e.target.value)}>
                {Object.entries(data.categories).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </label>
            {exportSupply ? (
              <>
                <label>Destination country code<input required className={input} name="country" maxLength={2} placeholder="AE" /></label>
                <label>Currency (optional)<input className={input} name="currency" maxLength={3} placeholder="USD" /></label>
                <label>Port code (optional)<input className={input} name="port" maxLength={10} placeholder="INNSA1" /></label>
                <label>Shipping bill number (optional)<input className={input} name="shipping_bill" maxLength={20} /></label>
                <label>Shipping bill date<input className={input} name="shipping_bill_date" type="date" /></label>
              </>
            ) : null}
          </div>
        ) : (
          <p className="nx-panel text-sm">Credit note against <b>{row.invoice_number}</b>{row.invoice_irn ? " (IRN registered)" : ""}. It is reported with the same type of supply as the original invoice.</p>
        )}
        <p className="nx-muted text-sm" style={{ marginTop: 12 }}>
          {category.endsWith("WOP") ? "Without payment means supplied under LUT or bond: every line must have 0% GST." : category.startsWith("SEZ") || exportSupply ? "IGST is applied on the whole document." : "The buyer GSTIN, HSN codes and totals are checked before anything is sent."}
        </p>
        <div className="nxf-actions"><span /><div className="nxf-buttons">
          <button type="button" className="nx-button nx-secondary nxf-secondary-sm" disabled={busy} onClick={onClose}>Cancel</button>
          <button className="nx-button" disabled={busy}>{busy ? "Submitting…" : "Submit to IRP"}</button>
        </div></div>
      </form>
    </FormSheet>
  );
}

export default function EInvoices() {
  const params = useSearchParams();
  const router = useRouter();
  const qc = useQueryClient();
  const [kind, setKind] = useState<Kind>("invoice");
  const [search, setSearch] = useState(params.get("invoice") || "");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [connect, setConnect] = useState(false);
  const [generate, setGenerate] = useState<Row>();
  const [cancel, setCancel] = useState<Row>();
  const [bulk, setBulk] = useState<BulkResult[]>();
  const query = useDebounced(search.trim());
  const list = useQuery({
    queryKey: ["einvoices", kind, query],
    queryFn: async () => (await apiRequest<Listing>(`${path}?kind=${kind}&search=${encodeURIComponent(query)}`)).data,
    retry: false,
  });
  const data = list.data;
  const strict = !!data?.preferences.turnover_10cr;

  async function send(body: Record<string, unknown>, done?: string) {
    setBusy(true); setMessage("");
    try {
      const res = await apiRequest<Row & { results?: BulkResult[]; registered?: number }>(path, { method: "POST", body: { ...body, confirm: true } });
      if (done) notify(done);
      setGenerate(undefined); setCancel(undefined); setConnect(false);
      return res.data;
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Request failed.");
      return null;
    } finally {
      await qc.invalidateQueries({ queryKey: ["einvoices"] });
      setBusy(false);
    }
  }

  const ready = (data?.records ?? []).filter((r) => !r.status && r.invoice_status !== "CANCELLED" && !r.export && !(strict && r.late));
  async function registerAll() {
    if (!data) return;
    const ids = ready.slice(0, data.bulk_limit).map((r) => r.id);
    if (!(await confirmAction(`Register ${ids.length} ${kind === "invoice" ? "B2B invoice" : "credit note"}${ids.length === 1 ? "" : "s"} with the ${data.environment === "live" ? "LIVE" : "TEST"} IRP? Exports and SEZ supplies are left for you to submit one by one.`))) return;
    const res = await send({ action: "generate-bulk", kind, ids });
    if (res?.results) {
      setBulk(res.results);
      notify(`${res.registered ?? 0} of ${res.results.length} registered.`, res.registered === res.results.length ? "success" : "error");
    }
  }

  async function quick(row: Row, action: "recover" | "check-cancellation") {
    if (await confirmAction(action === "recover" ? `Check the IRP for ${row.number} and save its IRN?` : `Check whether the IRN for ${row.number} is cancelled?`)) {
      await send({ id: row.id, kind: row.kind, action }, "IRP status updated.");
    }
  }

  async function pdf(row: Row) {
    try {
      const file = await apiBinaryRequest(`/business/e-invoices/${row.id}/pdf/`);
      await downloadBlob(file.blob, file.filename || `${row.number}.pdf`);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Could not download PDF.", "error");
    }
  }

  async function setPref(key: "turnover_10cr" | "auto_generate", value: boolean) {
    const text = key === "auto_generate"
      ? value ? "Register new B2B invoices with the IRP automatically after you issue them? Invoices issued before now are not touched." : "Stop automatic IRN generation?"
      : value ? "Turn on the 30-day limit? NexEase will stop documents older than 30 days from being sent, as the IRP rejects them." : "Turn off the 30-day limit?";
    if (await confirmAction(text)) await send({ action: "preferences", [key]: value });
  }

  function actions(row: Row): ListAction[] {
    if (!data) return [];
    const a: ListAction[] = [];
    const late = strict && row.late;
    if (!row.status && data.can_issue && data.configured && row.invoice_status !== "CANCELLED") {
      a.push({ icon: Send, label: late ? `${row.number} is past the 30-day limit` : `Register ${row.number}`, disabled: busy || late, onClick: () => { setMessage(""); setGenerate(row); } });
    }
    if (row.status === "pending" && data.can_issue) a.push({ icon: RefreshCw, label: `Recover IRN for ${row.number}`, disabled: busy, onClick: () => void quick(row, "recover") });
    if (row.status === "cancel_pending" && data.can_cancel) a.push({ icon: RefreshCw, label: `Check cancellation for ${row.number}`, disabled: busy, onClick: () => void quick(row, "check-cancellation") });
    if (row.kind === "invoice") a.push({ icon: Download, label: `Download invoice PDF ${row.number}`, onClick: () => void pdf(row) });
    if (row.status === "registered" && data.can_cancel) a.push({ icon: Ban, label: `Cancel IRN for ${row.number}`, disabled: busy, onClick: () => setCancel(row) });
    return a;
  }

  return (
    <ListScreen
      title="GST e-invoices"
      subtitle="Register invoices and credit notes with the IRP. The signed QR prints on the PDF."
      primary={data?.can_configure ? { label: data.configured ? "Update IRP login" : "Connect IRP", icon: ShieldCheck, onClick: () => { setMessage(""); setConnect(true); } } : null}
      actions={[{ icon: FileText, label: "Sales invoices", onClick: () => router.push("/invoices") }, { icon: Truck, label: "E-way bills", onClick: () => router.push("/e-way-bills") }]}
      onRefresh={() => void list.refetch()} refreshing={list.isFetching}
      chips={{ label: "Document type", value: kind, onChange: (v) => { setKind(v); setBulk(undefined); }, options: [{ value: "invoice", label: "Invoices" }, { value: "credit_note", label: "Credit notes" }] }}
      search={{ value: search, onChange: setSearch, placeholder: kind === "invoice" ? "Search invoice number" : "Search credit note number" }}
      above={<>
        {data ? (
          <p className="nx-panel flex flex-wrap items-center gap-2 text-sm">
            <Badge tone={data.environment === "live" ? "success" : "warning"}>{data.environment === "live" ? "LIVE IRP" : "TEST IRP · not a legal invoice"}</Badge>
            <span>{data.gstin || "Set your GSTIN in Taxation"}</span>
            <span className="nx-muted">· {data.configured ? "Credentials saved" : "IRP credentials not connected"}</span>
          </p>
        ) : null}
        {data ? (
          <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(min(160px,45%),1fr))" }}>
            <StatCard label="To register" value={String(data.summary.to_register)} hint={kind === "invoice" ? "Invoices without an IRN" : "Credit notes without an IRN"} icon={Send} tone="info" />
            <StatCard label="Due in 5 days" value={String(data.summary.due_soon)} hint={`Of the ${data.reporting_days}-day reporting window`} icon={Clock} tone={data.summary.due_soon ? "warning" : "neutral"} />
            <StatCard label="Past 30 days" value={String(data.summary.late)} hint={strict ? "The IRP no longer accepts these" : "Matters if turnover is ₹10 crore+"} icon={AlertTriangle} tone={data.summary.late && strict ? "danger" : "neutral"} />
            <StatCard label="Needs a status check" value={String(data.summary.pending)} hint="Sent, but the reply was not confirmed" icon={RefreshCw} tone={data.summary.pending ? "warning" : "neutral"} />
          </div>
        ) : null}
        {data?.configured ? (
          <div className="nx-panel flex flex-wrap items-center gap-x-6 gap-y-3 text-sm">
            <label className="flex items-center gap-2"><input type="checkbox" checked={data.preferences.turnover_10cr} disabled={!data.can_configure || busy} onChange={(e) => void setPref("turnover_10cr", e.target.checked)} />
              Turnover of ₹10 crore or more (30-day reporting limit applies)</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={data.preferences.auto_generate} disabled={!data.can_configure || busy} onChange={(e) => void setPref("auto_generate", e.target.checked)} />
              Register new B2B invoices automatically</label>
            {data.can_issue && ready.length ? (
              <button type="button" className="nx-button" style={{ marginLeft: "auto" }} disabled={busy} onClick={() => void registerAll()}>
                <Layers size={16} />Register {Math.min(ready.length, data.bulk_limit)} ready
              </button>
            ) : null}
          </div>
        ) : null}
        {bulk ? (
          <div className="nx-panel text-sm" role="status">
            <div className="flex items-center justify-between"><b>Bulk registration</b><button type="button" className="nx-link" onClick={() => setBulk(undefined)}>Close</button></div>
            <ul className="mt-2 space-y-1">{bulk.map((r) => <li key={r.id} className="flex gap-2">{r.ok ? <CheckCircle2 size={16} color="var(--nx-success-fg)" /> : <AlertTriangle size={16} color="var(--nx-danger-fg)" />}<span><b>{r.number ?? r.id}</b>{r.ok ? " registered" : ` · ${r.message}`}</span></li>)}</ul>
          </div>
        ) : null}
        {connect ? (
          <FormSheet title="Connect IRP" subtitle="Your IRP API login for the seller GSTIN. The password is encrypted on the server." onClose={() => setConnect(false)} busy={busy} size="md">
            <form onSubmit={(e) => { e.preventDefault(); void send({ ...Object.fromEntries(new FormData(e.currentTarget).entries()), action: "configure" }, "IRP credentials saved."); }}>
              <div className="nxf-grid">
                <label>IRP API username<input required className={input} name="username" maxLength={100} /></label>
                <label>IRP API password<PasswordInput required className={input} name="password" type="password" autoComplete="new-password" maxLength={200} /></label>
                <label>Registered seller address<input required className={input} name="address" maxLength={100} /></label>
                <label>Seller city<input required className={input} name="city" maxLength={50} /></label>
                <label>Seller PIN code<input required className={input} name="pincode" pattern="[1-9][0-9]{5}" inputMode="numeric" /></label>
              </div>
              {message ? <p role="alert" className="nxf-error">{message}</p> : null}
              <div className="nxf-actions"><span /><div className="nxf-buttons"><button className="nx-button" disabled={busy}>{busy ? "Saving…" : "Save IRP login"}</button></div></div>
            </form>
          </FormSheet>
        ) : null}
        {generate && data ? <GenerateSheet row={generate} data={data} busy={busy} onClose={() => setGenerate(undefined)} onSubmit={(b) => void send(b, `${generate.number} registered with the IRP.`)} /> : null}
        {cancel ? (
          <form className="nx-panel flex flex-wrap items-end gap-3" onSubmit={(e) => {
            e.preventDefault();
            const f = Object.fromEntries(new FormData(e.currentTarget).entries());
            void confirmAction(`Cancel the IRN for ${cancel.number}? This cannot be undone. The IRP allows cancellation only within 24 hours of registration.`).then((yes) => { if (yes) void send({ id: cancel.id, kind: cancel.kind, action: "cancel", ...f }, "IRN cancellation submitted."); });
          }}>
            <label>Cancellation reason<select className={input} name="reason" defaultValue="2">{["Duplicate", "Data entry mistake", "Order cancelled", "Other"].map((v, i) => <option key={v} value={i + 1}>{v}</option>)}</select></label>
            <label>Remarks<input required className={input} name="remarks" minLength={3} maxLength={100} /></label>
            <button className="nx-button" disabled={busy}>Cancel IRN for {cancel.number}</button>
            <button type="button" className="nx-button nx-secondary" onClick={() => setCancel(undefined)}>Back</button>
          </form>
        ) : null}
        {message && !connect ? <p role="alert" className="nx-panel" style={{ color: "var(--nx-danger-fg)" }}>{message}</p> : null}
      </>}
    >
      <ListState loading={list.isLoading} error={list.error} onRetry={() => void list.refetch()} isEmpty={!data?.records.length}
        emptyIcon={ShieldCheck} emptyTitle={query ? "No matching documents" : kind === "invoice" ? "No invoices to register yet" : "No credit notes to register yet"}
        emptyDescription={query ? "Try a different number." : kind === "invoice" ? "Issued B2B, SEZ and export invoices appear here." : "Issued credit notes against GST invoices appear here."}>
        <CompactList label="E-invoices" columns={[{ label: kind === "invoice" ? "Customer / invoice" : "Customer / credit note" }, { label: "IRN" }, { label: "Deadline" }, { label: "Status" }]}>
          {(data?.records ?? []).map((row) => {
            const due = deadline(row, strict);
            const st = IRN_STATUS[row.status ?? ""];
            return (
              <CompactRow key={row.id}
                title={row.customer || "—"}
                subtitle={<>{row.number} · {formatDate(row.date)}{row.kind === "credit_note" && row.invoice_number ? ` · against ${row.invoice_number}` : ""}{row.category && row.category !== "B2B" ? ` · ${row.category}` : ""}</>}
                meta={[
                  row.irn ? <span key="irn" title={row.irn}>{row.irn.slice(0, 14)}… · Ack {row.ack_no}</span> : row.auto_error ? <span key="auto" title={row.auto_error} style={{ color: "var(--nx-danger-fg)" }}>Auto IRN failed: {row.auto_error.slice(0, 60)}</span> : "—",
                  due ? <Badge key="due" tone={due.tone} icon={due.tone === "danger" ? AlertTriangle : Clock}>{due.label}</Badge> : "—",
                ]}
                amount={`₹${Number(row.total).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`}
                badge={<Badge tone={st?.tone ?? "neutral"}>{st?.label ?? (row.invoice_status === "CANCELLED" ? "Document cancelled" : "Not registered")}</Badge>}
                actions={actions(row)} />
            );
          })}
        </CompactList>
      </ListState>
    </ListScreen>
  );
}

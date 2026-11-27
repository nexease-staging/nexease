"use client";

import { useState, type FormEvent, type ReactNode } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Ban, CalendarClock, ClipboardCheck, FileText, Layers, Plus, ShieldCheck, Truck } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, type ListAction } from "@/components/list/list-kit";
import { Badge, type Tone } from "@/components/ui/badge";
import StatCard from "@/components/ui/stat-card";
import { FormSheet } from "@/components/form/form-sheet";
import { confirmAction, notify } from "@/components/nex-feedback";
import { apiRequest } from "@/lib/api/client";

type Source = { id: string; kind: "invoice" | "challan"; document: string; customer: string; irp?: string; reason?: string };
export type Bill = {
  source_id: string; kind: Source["kind"]; document: string; status: string; number?: string; generated_at?: string; valid_until?: string;
  vehicle?: string; distance?: number; extensions?: number; consolidated?: string; cancellable: boolean; extendable: boolean;
  can_cancel_until?: string | null; extend_opens?: string | null; history: { at: string; kind: string; text: string }[];
};
type Consolidated = { number: string; date: string; vehicle: string; bills: string[] };
type Data = {
  sources: Source[]; records: Bill[]; consolidated: Consolidated[]; configured: boolean; environment: string; state_code: string;
  can_issue: boolean; can_cancel: boolean; reasons: { cancel: Record<string, string>; vehicle: Record<string, string>; extend: Record<string, string> };
};
type Dialog = { type: "new" } | { type: "cancel" | "vehicle" | "extend" | "record"; bill: Bill } | { type: "consolidate" };

const path = "/business/e-way-bills/";
const input = "nx-input w-full";
export const STATUS: Record<string, { label: string; tone: Tone }> = {
  generated: { label: "Active", tone: "success" }, pending: { label: "Check portal", tone: "warning" }, cancelled: { label: "Cancelled", tone: "danger" },
  portal_recorded: { label: "Recorded from portal", tone: "info" }, portal_cancelled: { label: "Cancelled on portal", tone: "danger" },
};
const when = (iso?: string | null) => (iso ? new Date(iso).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" }) : "");

function Transport({ mode, setMode, children }: { mode: string; setMode: (m: string) => void; children?: ReactNode }) {
  return (
    <div className="nxf-grid">
      <label>Mode<select className={input} value={mode} onChange={(e) => setMode(e.target.value)}><option value="1">Road</option><option value="2">Rail</option><option value="3">Air</option><option value="4">Ship</option></select></label>
      {mode === "1" ? <>
        <label>Vehicle number<input className={input} required name="vehicle" maxLength={18} placeholder="MH12AB1234" /></label>
        <label>Vehicle type<select className={input} name="vehicle_type"><option value="R">Regular</option><option value="O">Over-dimensional cargo</option></select></label>
      </> : null}
      <label>Transport document number{mode === "1" ? " (optional)" : ""}<input className={input} required={mode !== "1"} name="transport_doc" maxLength={15} /></label>
      <label>Transport document date<input className={input} required={mode !== "1"} name="transport_date" type="date" /></label>
      {children}
    </div>
  );
}

function Actions({ busy, label, onClose }: { busy: boolean; label: string; onClose: () => void }) {
  return <div className="nxf-actions"><span /><div className="nxf-buttons">
    <button type="button" className="nx-button nx-secondary nxf-secondary-sm" disabled={busy} onClick={onClose}>Cancel</button>
    <button className="nx-button" disabled={busy}>{busy ? "Working…" : label}</button>
  </div></div>;
}

export default function EWayBills() {
  const params = useSearchParams();
  const router = useRouter();
  const qc = useQueryClient();
  const query = useQuery({ queryKey: ["eway-bills"], queryFn: async () => (await apiRequest<Data>(path)).data, retry: false });
  const data = query.data;
  const [dialog, setDialog] = useState<Dialog | null>(() => (params.get("invoice") ? { type: "new" } : null));
  const [selected, setSelected] = useState(() => { const id = params.get("invoice"); return id ? "invoice:" + id : ""; });
  const [mode, setMode] = useState("1");
  const [combined, setCombined] = useState(true);
  const [auto, setAuto] = useState(true);
  const [picked, setPicked] = useState<string[]>([]);
  const [open, setOpen] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const env = data?.environment === "live" ? "LIVE" : "TEST";
  const source = data?.sources.find((s) => s.kind + ":" + s.id === selected);
  const join = source?.kind === "invoice" && combined && !source.irp;

  async function post(body: Record<string, unknown>, url = path) {
    setBusy(true); setMessage("");
    try {
      const res = await apiRequest<{ number?: string }>(url, { method: "POST", body: { ...body, confirm: true } });
      setDialog(null); setPicked([]);
      return res.data;
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Request could not be confirmed.");
      return null;
    } finally {
      await Promise.all([qc.invalidateQueries({ queryKey: ["eway-bills"] }), qc.invalidateQueries({ queryKey: ["einvoices"] })]);
      setBusy(false);
    }
  }
  const fields = (e: FormEvent<HTMLFormElement>) => { e.preventDefault(); return Object.fromEntries(new FormData(e.currentTarget).entries()) as Record<string, string>; };

  async function generate(e: FormEvent<HTMLFormElement>) {
    const f = fields(e);
    if (!source) return;
    if (!(await confirmAction(`${join ? "Generate the IRN and e-way bill" : "Generate the e-way bill"} for ${source.document} on the ${env} portal?`))) return;
    const transport = { ...f, mode, auto_distance: auto };
    const res = join
      ? await post({ action: "generate", id: source.id, transport }, "/business/e-invoices/")
      : await post({ ...transport, kind: source.kind, id: source.id, action: "generate", no_irn_required: f.no_irn_required === "on" });
    if (res) notify(res.number ? `E-way bill ${res.number} generated.` : "Submitted. Check the status in the list.");
  }

  async function update(bill: Bill, action: "cancel" | "vehicle" | "extend" | "record" | "record-cancellation", f: Record<string, string>, question: string, done: string) {
    if (!(await confirmAction(question))) return;
    const res = await post({ ...f, mode, kind: bill.kind, id: bill.source_id, action, portal_verified: f.portal_verified === "on" });
    if (res) notify(done);
  }

  async function consolidate(e: FormEvent<HTMLFormElement>) {
    const f = fields(e);
    if (!(await confirmAction(`Put ${picked.length} e-way bills on vehicle ${f.vehicle ?? ""} as one consolidated e-way bill?`))) return;
    const res = await post({ ...f, mode, action: "consolidate", numbers: picked });
    if (res?.number) notify(`Consolidated e-way bill ${res.number} generated.`);
  }

  const active = (data?.records ?? []).filter((r) => r.status === "generated");
  function rowActions(bill: Bill): ListAction[] {
    if (!data) return [];
    const a: ListAction[] = [];
    if (bill.status === "generated" && data.can_issue) {
      a.push({ icon: Truck, label: `Change vehicle for ${bill.number}`, disabled: busy, onClick: () => { setMessage(""); setMode("1"); setDialog({ type: "vehicle", bill }); } });
      a.push({ icon: CalendarClock, label: bill.extendable ? `Extend ${bill.number}` : `Extension opens ${when(bill.extend_opens)}`, disabled: busy || !bill.extendable, onClick: () => { setMessage(""); setMode("1"); setDialog({ type: "extend", bill }); } });
    }
    if (bill.cancellable && data.can_cancel) a.push({ icon: Ban, label: `Cancel ${bill.number}`, disabled: busy, onClick: () => { setMessage(""); setDialog({ type: "cancel", bill }); } });
    if ((bill.status === "pending" || bill.status === "portal_recorded") && data.can_issue) a.push({ icon: ClipboardCheck, label: `Record portal outcome for ${bill.document}`, disabled: busy, onClick: () => { setMessage(""); setDialog({ type: "record", bill }); } });
    return a;
  }

  const d = dialog;
  return (
    <ListScreen
      title="E-way bills"
      subtitle="Generate, change vehicle, extend, cancel and consolidate e-way bills without leaving NexEase."
      primary={data?.can_issue ? { label: "New e-way bill", icon: Plus, onClick: () => { setMessage(""); setDialog({ type: "new" }); } } : null}
      actions={[
        ...(active.length >= 2 && data?.can_issue ? [{ icon: Layers, label: "Consolidate e-way bills", onClick: () => { setMessage(""); setMode("1"); setPicked([]); setDialog({ type: "consolidate" }); } }] : []),
        { icon: ShieldCheck, label: "E-invoices and API login", onClick: () => router.push("/e-invoices") },
        { icon: FileText, label: "Delivery challans", onClick: () => router.push("/delivery-challans") },
      ]}
      onRefresh={() => void query.refetch()} refreshing={query.isFetching}
      above={<>
        {data ? <p className="nx-panel flex flex-wrap items-center gap-2 text-sm">
          <Badge tone={data.environment === "live" ? "success" : "warning"}>{data.environment === "live" ? "LIVE portal" : "TEST · not for actual dispatch"}</Badge>
          <span className="nx-muted">{data.configured ? "Seller API login saved" : "Connect the seller API login under E-invoices first"}</span>
        </p> : null}
        {data ? <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(min(160px,45%),1fr))" }}>
          <StatCard label="Active" value={String(active.length)} hint="Valid e-way bills" icon={Truck} tone="success" />
          <StatCard label="Extension window open" value={String(active.filter((r) => r.extendable).length)} hint="Within 8 hours of expiry" icon={CalendarClock} tone={active.some((r) => r.extendable) ? "warning" : "neutral"} />
          <StatCard label="Can still cancel" value={String(active.filter((r) => r.cancellable).length)} hint="Within 24 hours of generation" icon={Ban} tone="neutral" />
          <StatCard label="Consolidated trips" value={String(data.consolidated.length)} hint="Several bills on one vehicle" icon={Layers} tone="info" />
        </div> : null}
        {message && !d ? <p role="alert" className="nx-panel" style={{ color: "var(--nx-danger-fg)" }}>{message}</p> : null}

        {d?.type === "new" && data ? (
          <FormSheet title="New e-way bill" subtitle={`Outward movement on the ${env} portal`} onClose={() => setDialog(null)} busy={busy} size="lg">
            <form onSubmit={(e) => void generate(e)}>
              <div className="nxf-grid">
                <label className="sm:col-span-2">Invoice or delivery challan<select className={input} required value={selected} onChange={(e) => { setSelected(e.target.value); setCombined(true); }}>
                  <option value="">Choose an issued invoice or challan</option>
                  {data.sources.map((s) => <option key={s.kind + ":" + s.id} value={s.kind + ":" + s.id}>{s.kind === "invoice" ? "Invoice" : "Challan"} {s.document} · {s.customer}</option>)}
                </select></label>
              </div>
              {source?.kind === "invoice" ? (source.irp
                ? <p className="nx-panel text-sm">This invoice already has an IRN submission. Generate its e-way bill on the IRP or portal and record the number from the list.</p>
                : <label className="flex gap-2 text-sm" style={{ margin: "10px 0" }}><input type="checkbox" checked={combined} onChange={(e) => setCombined(e.target.checked)} />Generate the IRN and e-way bill together</label>) : null}
              {source?.kind === "invoice" && !combined && !source.irp ? <label className="flex gap-2 text-sm"><input required type="checkbox" name="no_irn_required" />I checked that this invoice does not need an IRN.</label> : null}
              <Transport mode={mode} setMode={setMode}>
                <label className="flex items-center gap-2 sm:col-span-2"><input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} />Let the portal calculate the distance from the PIN codes</label>
                {!auto ? <label>Distance (km)<input className={input} required type="number" name="distance" min={1} max={4000} /></label> : null}
                <label>Transporter ID (optional)<input className={input} name="transporter_id" maxLength={15} /></label>
                {source?.kind === "challan" ? <>
                  <label>Delivery city<input className={input} required name="destination_city" maxLength={50} /></label>
                  <label>Delivery PIN<input className={input} required name="destination_pin" pattern="[1-9][0-9]{5}" inputMode="numeric" /></label>
                </> : null}
              </Transport>
              <p className="nx-muted text-sm" style={{ marginTop: 10 }}>Documents older than 180 days cannot get an e-way bill.</p>
              {message ? <p role="alert" className="nxf-error">{message}</p> : null}
              <Actions busy={busy} onClose={() => setDialog(null)} label={join ? "Generate IRN and e-way bill" : "Generate e-way bill"} />
            </form>
          </FormSheet>
        ) : null}

        {d?.type === "cancel" && data ? (
          <FormSheet title={`Cancel e-way bill ${d.bill.number}`} subtitle={`${d.bill.document} · allowed until ${when(d.bill.can_cancel_until)}`} onClose={() => setDialog(null)} busy={busy} size="md">
            <form onSubmit={(e) => { const f = fields(e); void update(d.bill, "cancel", f, `Cancel e-way bill ${d.bill.number}? This cannot be undone.`, `E-way bill ${d.bill.number} cancelled.`); }}>
              <div className="nxf-grid">
                <label>Reason<select className={input} name="reason" defaultValue="2">{Object.entries(data.reasons.cancel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
                <label>Remarks<input className={input} required name="remarks" minLength={3} maxLength={50} /></label>
              </div>
              {message ? <p role="alert" className="nxf-error">{message}</p> : null}
              <Actions busy={busy} onClose={() => setDialog(null)} label="Cancel e-way bill" />
            </form>
          </FormSheet>
        ) : null}

        {d?.type === "vehicle" && data ? (
          <FormSheet title={`Change vehicle · ${d.bill.number}`} subtitle={`${d.bill.document}${d.bill.vehicle ? ` · now on ${d.bill.vehicle}` : ""}`} onClose={() => setDialog(null)} busy={busy} size="md">
            <form onSubmit={(e) => { const f = fields(e); void update(d.bill, "vehicle", f, `Update Part-B of ${d.bill.number} on the ${env} portal?`, `Vehicle updated for ${d.bill.number}.`); }}>
              <Transport mode={mode} setMode={setMode}>
                <label>Reason<select className={input} name="reason" defaultValue="1">{Object.entries(data.reasons.vehicle).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
                <label>Current place<input className={input} required name="from_place" maxLength={50} /></label>
                <label>Current state code<input className={input} name="from_state" defaultValue={data.state_code} pattern="[0-9]{2}" inputMode="numeric" /></label>
                <label>Remarks (optional)<input className={input} name="remarks" maxLength={50} /></label>
              </Transport>
              {message ? <p role="alert" className="nxf-error">{message}</p> : null}
              <Actions busy={busy} onClose={() => setDialog(null)} label="Update vehicle" />
            </form>
          </FormSheet>
        ) : null}

        {d?.type === "extend" && data ? <ExtendSheet bill={d.bill} data={data} mode={mode} setMode={setMode} busy={busy} message={message} onClose={() => setDialog(null)}
          onSubmit={(f) => void update(d.bill, "extend", f, `Extend ${d.bill.number}? The new validity depends on the remaining distance.`, `Validity extended for ${d.bill.number}.`)} /> : null}

        {d?.type === "record" ? (
          <FormSheet title={`Record portal outcome · ${d.bill.document}`} subtitle="Only updates NexEase. Check the portal first." onClose={() => setDialog(null)} busy={busy} size="md">
            <form onSubmit={(e) => { const f = fields(e); const cancel = f.outcome === "cancelled"; void update(d.bill, cancel ? "record-cancellation" : "record", f, "Save this portal outcome in NexEase?", "Portal outcome saved."); }}>
              <div className="nxf-grid">
                <label>Outcome<select className={input} name="outcome"><option value="generated">E-way bill exists on the portal</option><option value="cancelled">It was cancelled on the portal</option></select></label>
                <label>E-way bill number<input className={input} required name="number" pattern="[0-9]{12}" inputMode="numeric" defaultValue={d.bill.number} /></label>
              </div>
              <label className="flex gap-2 text-sm" style={{ marginTop: 10 }}><input required type="checkbox" name="portal_verified" />I checked this document on the e-way bill portal.</label>
              {message ? <p role="alert" className="nxf-error">{message}</p> : null}
              <Actions busy={busy} onClose={() => setDialog(null)} label="Save outcome" />
            </form>
          </FormSheet>
        ) : null}

        {d?.type === "consolidate" && data ? (
          <FormSheet title="Consolidated e-way bill" subtitle="One trip sheet for several consignments on the same vehicle" onClose={() => setDialog(null)} busy={busy} size="lg">
            <form onSubmit={(e) => void consolidate(e)}>
              <fieldset className="nx-panel" style={{ marginBottom: 12 }}>
                <legend className="text-sm font-semibold">E-way bills on this vehicle</legend>
                {active.map((b) => (
                  <label key={b.number} className="flex items-center gap-2 text-sm" style={{ padding: "4px 0" }}>
                    <input type="checkbox" checked={picked.includes(b.number!)} onChange={(e) => setPicked((x) => (e.target.checked ? [...x, b.number!] : x.filter((n) => n !== b.number)))} />
                    <b>{b.number}</b> · {b.document}{b.vehicle ? ` · ${b.vehicle}` : ""}
                  </label>
                ))}
              </fieldset>
              <Transport mode={mode} setMode={setMode}>
                <label>Dispatch place<input className={input} required name="from_place" maxLength={50} /></label>
                <label>State code<input className={input} name="from_state" defaultValue={data.state_code} pattern="[0-9]{2}" inputMode="numeric" /></label>
              </Transport>
              {message ? <p role="alert" className="nxf-error">{message}</p> : null}
              <div className="nxf-actions"><span>{picked.length} selected</span><div className="nxf-buttons">
                <button type="button" className="nx-button nx-secondary nxf-secondary-sm" disabled={busy} onClick={() => setDialog(null)}>Cancel</button>
                <button className="nx-button" disabled={busy || picked.length < 2}>{busy ? "Working…" : "Generate consolidated e-way bill"}</button>
              </div></div>
            </form>
          </FormSheet>
        ) : null}
      </>}
    >
      <ListState loading={query.isLoading} error={query.error} onRetry={() => void query.refetch()} isEmpty={!data?.records.length}
        emptyIcon={Truck} emptyTitle="No e-way bills yet" emptyDescription="Generate one from an issued invoice or delivery challan.">
        <CompactList label="E-way bills" columns={[{ label: "Document / e-way bill" }, { label: "Vehicle" }, { label: "Valid until" }, { label: "Status" }]}>
          {(data?.records ?? []).map((b) => {
            const st = STATUS[b.status] ?? { label: b.status, tone: "neutral" as Tone };
            const key = b.kind + ":" + b.source_id;
            return (
              <CompactRow key={key}
                title={b.document}
                subtitle={<>{b.number ? `EWB ${b.number}` : "No number yet"}{b.consolidated ? ` · trip ${b.consolidated}` : ""}{b.distance ? ` · ${b.distance} km` : ""}</>}
                meta={[b.vehicle || "—", <span key="v">{b.valid_until || "—"}{b.extensions ? ` · extended ${b.extensions}×` : ""}</span>]}
                badge={b.extendable ? <Badge tone="warning" icon={CalendarClock}>Extend now</Badge> : <Badge tone={st.tone}>{st.label}</Badge>}
                actions={rowActions(b)}
                onOpen={b.history.length ? () => setOpen(open === key ? null : key) : undefined}
                openLabel={`Show history of ${b.document}`}
                expanded={open === key}>
                <ol className="space-y-1 text-sm">{b.history.slice().reverse().map((h, i) => <li key={i}><span className="nx-muted">{when(h.at)}</span> · {h.text}</li>)}</ol>
              </CompactRow>
            );
          })}
        </CompactList>
      </ListState>
    </ListScreen>
  );
}

function ExtendSheet({ bill, data, mode, setMode, busy, message, onClose, onSubmit }: {
  bill: Bill; data: Data; mode: string; setMode: (m: string) => void; busy: boolean; message: string; onClose: () => void; onSubmit: (f: Record<string, string>) => void;
}) {
  const [status, setStatus] = useState("M");
  return (
    <FormSheet title={`Extend validity · ${bill.number}`} subtitle={`${bill.document} · valid until ${bill.valid_until}`} onClose={onClose} busy={busy} size="md">
      <form onSubmit={(e) => { e.preventDefault(); onSubmit({ ...(Object.fromEntries(new FormData(e.currentTarget).entries()) as Record<string, string>), consignment_status: status }); }}>
        <div className="nxf-grid" style={{ marginBottom: 10 }}>
          <label>Goods are<select className={input} value={status} onChange={(e) => setStatus(e.target.value)}><option value="M">Moving</option><option value="T">In transit (stored)</option></select></label>
          {status === "T" ? <label>Stored at<select className={input} name="transit_type"><option value="R">Road side</option><option value="W">Warehouse</option><option value="O">Other</option></select></label> : null}
        </div>
        {status === "M" ? <Transport mode={mode} setMode={setMode} /> : null}
        <div className="nxf-grid" style={{ marginTop: 10 }}>
          <label>Reason<select className={input} name="reason" defaultValue="5">{Object.entries(data.reasons.extend).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
          <label>Remaining distance (km)<input className={input} required type="number" name="remaining_distance" min={1} max={4000} /></label>
          <label>Current place<input className={input} required name="from_place" maxLength={50} /></label>
          <label>Current PIN code<input className={input} required name="from_pin" pattern="[1-9][0-9]{5}" inputMode="numeric" /></label>
          <label>Current state code<input className={input} name="from_state" defaultValue={data.state_code} pattern="[0-9]{2}" inputMode="numeric" /></label>
          <label>Remarks (optional)<input className={input} name="remarks" maxLength={50} /></label>
        </div>
        <p className="nx-muted text-sm" style={{ marginTop: 10 }}>Extension is allowed from 8 hours before to 8 hours after expiry, and an e-way bill can stay valid for at most 360 days.</p>
        {message ? <p role="alert" className="nxf-error">{message}</p> : null}
        <Actions busy={busy} onClose={onClose} label="Extend validity" />
      </form>
    </FormSheet>
  );
}

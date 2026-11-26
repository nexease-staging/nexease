"use client";

/*
 * Shared, schema-driven register screen (employees, sites, assignments, timesheets, leave,
 * advances, pay inputs, expenses, GST review, workforce settings). The schema comes from the
 * server; record-presenters.ts decides how each register reads as a compact row and how its
 * form is grouped.
 */

import { Check, FileSpreadsheet, Pencil, Plus, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CompactList, CompactRow, ListScreen, ListState, type ListAction } from "@/components/list/list-kit";
import { FieldHint, FormActions, FormSection, FormSheet } from "@/components/form/form-sheet";
import { AI_PREFILL_EVENT, takeRecordPrefill } from "@/features/ai/handoff";
import { Badge } from "@/components/ui/badge";
import SearchSelect from "@/components/search-select";
import { useFormExitGuard } from "@/components/use-form-exit-guard";
import { useAuth } from "@/features/auth/auth-context";
import { apiRequest, apiBinaryRequest } from "@/lib/api/client";
import { hasPermission } from "@/lib/authorization/permissions";
import { downloadBlob } from "@/lib/browser/download";
import GstLookup from "./gst-lookup";
import { fallbackPresenter, matchesFilter, presenters, type Field, type Row, type Value } from "./record-presenters";

type Schema = { label: string; permission: string; fields: Record<string, Field> };
export type Configuration = { setup?: { logo: boolean; email: boolean; bank: boolean }; can_read_cost?: boolean; can_edit_issued_invoices?: boolean; can_edit_invoices?: boolean; logo?: string; modules?: Record<string, boolean>; schemas: Record<string, Schema>; scope: string; profile: { modules: string[] }; profiles: Record<string, { label: string }> };
export const getConfig = async () => (await apiRequest<Configuration>("/business/configuration/")).data;

const SUGGESTED = ["period_days", "paid_days", "hours", "overtime_hours", "advance_recovery"];
const APPROVALS: Record<string, { pending: string; permission: string }> = {
  leave_requests: { pending: "requested", permission: "payroll.manage" },
  timesheets: { pending: "draft", permission: "labour.manage" },
};

function blankDraft(schema: Schema) {
  return Object.fromEntries(Object.entries(schema.fields).map(([k, f]) => [k,
    f.type === "boolean" ? k === "active" : f.type === "select" ? f.choices?.[0] ?? "" : f.type === "number" ? (k === "billing_rate" || k === "client_ot_rate" ? "" : "0") : ""]));
}

export default function BusinessWorkspace({ kinds, title, description }: { kinds: string[]; title: string; description: string }) {
  const qc = useQueryClient();
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const config = useQuery({ queryKey: ["business-config"], queryFn: getConfig });
  const [kind, setKind] = useState(kinds[0]);
  const [draft, setDraft] = useState<Record<string, Value>>({});
  const [initialDraft, setInitialDraft] = useState("");
  const [editing, setEditing] = useState<Row | null>(null);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [suggesting, setSuggesting] = useState(false);
  const [search, setSearch] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [filter, setFilter] = useState<string | null>(null);
  const [approving, setApproving] = useState<string | null>(null);
  const saving = useRef(false);
  const dirty = open && JSON.stringify(draft) !== initialDraft;
  const closeForm = useFormExitGuard(dirty, busy, () => setOpen(false));

  useEffect(() => {
    const timer = setTimeout(() => setSearchTerm(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const schema = config.data?.schemas[kind];
  const uses = (type: string) => !!schema && Object.values(schema.fields).some((f) => f.type === type);
  const records = useQuery({ queryKey: ["business-records", kind, searchTerm], queryFn: async () => (await apiRequest<{ records: Row[]; total: number }>(`/business/records/${kind}/?search=${encodeURIComponent(searchTerm)}`)).data, enabled: !!schema });
  const employees = useQuery({ queryKey: ["business-worker-lookup"], queryFn: async () => (await apiRequest<{ records: Row[] }>("/business/workers/")).data, enabled: uses("employees") });
  const sites = useQuery({ queryKey: ["business-records", "sites"], queryFn: async () => (await apiRequest<{ records: Row[] }>("/business/records/sites/")).data, enabled: uses("sites") });
  const clients = useQuery({ queryKey: ["workforce-clients"], queryFn: async () => (await apiRequest<{ records: Row[] }>("/business/client-lookup/")).data, enabled: uses("customers") });
  const accounts = useQuery({ queryKey: ["payment-ledger-accounts"], queryFn: async () => (await apiRequest<{ records: Row[] }>("/business/payment-accounts/")).data, enabled: uses("accounts") });
  const source = (type: string) => (type === "accounts" ? accounts.data?.records : type === "customers" ? clients.data?.records : type === "employees" ? employees.data?.records : sites.data?.records);
  const name = (type: string, value: Value | undefined) => {
    if (!value) return "";
    const match = source(type)?.find((x) => (type === "customers" ? x.data.code : x.id) === value);
    return match ? String(match.data.name ?? value) : String(value);
  };

  const presenter = schema ? presenters[kind] ?? fallbackPresenter(schema.fields, schema.label) : null;
  const activeFilter = filter ?? presenter?.filters?.[0]?.[0] ?? "";
  const rows = useMemo(() => (records.data?.records ?? []).filter((r) => !presenter || matchesFilter(presenter, r.data, activeFilter)), [records.data, presenter, activeFilter]);

  // Monthly pay inputs: fill paid days, hours, overtime and advance recovery from approved work.
  useEffect(() => {
    if (!open || editing || kind !== "attendance" || !draft.employee_id || !draft.month) return;
    let live = true;
    const params = new URLSearchParams({ employee_id: String(draft.employee_id), month: String(draft.month) });
    apiRequest<{ inputs: Record<string, Value> }>(`/business/workforce/populate-inputs/?${params}`)
      .then(({ data }) => { if (live) setDraft((current) => ({ ...current, ...Object.fromEntries(SUGGESTED.map((k) => [k, data.inputs[k]])) })); })
      .catch((e: Error) => { if (live) setError("Automatic input review: " + e.message); })
      .finally(() => { if (live) setSuggesting(false); });
    return () => { live = false; };
  }, [open, editing, kind, draft.employee_id, draft.month]);

  // GST review: other screens can open a prefilled entry.
  useEffect(() => {
    if (!kinds.includes("gst_adjustments")) return;
    const prefill = (event: Event) => {
      const data = (event as CustomEvent<Record<string, Value>>).detail;
      setKind("gst_adjustments"); setEditing(null); setDraft(data); setInitialDraft(JSON.stringify(data)); setError(""); setOpen(true);
    };
    window.addEventListener("nexease:gst-prefill", prefill);
    return () => window.removeEventListener("nexease:gst-prefill", prefill);
  }, [kinds]);

  // NexEase AI: open "New …" with the values the assistant collected.
  const schemas = config.data?.schemas;
  const kindList = kinds.join(",");
  useEffect(() => {
    if (!schemas) return;
    const apply = () => {
      const handoff = takeRecordPrefill(kindList.split(","));
      const target = handoff ? schemas[handoff.kind] : undefined;
      if (!handoff || !target) return;
      const next = { ...blankDraft(target), ...Object.fromEntries(Object.entries(handoff.data).filter(([k, v]) => k in target.fields && v !== "" && (target.fields[k].type !== "select" || (target.fields[k].choices ?? []).includes(String(v))))) };
      setKind(handoff.kind); setSuggesting(false); setEditing(null); setDraft(next); setInitialDraft(JSON.stringify(blankDraft(target))); setError(""); setOpen(true);
    };
    const timer = setTimeout(apply, 0);
    window.addEventListener(AI_PREFILL_EVENT, apply);
    return () => { clearTimeout(timer); window.removeEventListener(AI_PREFILL_EVENT, apply); };
  }, [schemas, kindList]);

  function updateField(key: string, value: string) {
    const next = { ...draft, [key]: value };
    if (kind === "expenses" && key === "employee_id") next.payee = String(employees.data?.records.find((r) => r.id === value)?.data.name ?? "");
    if (kind === "attendance" && !editing && (key === "employee_id" || key === "month")) {
      for (const f of SUGGESTED) next[f] = "";
      setError("");
      setSuggesting(Boolean(next.employee_id && next.month));
    }
    setDraft(next);
  }

  function newRecord() {
    if (!schema) return;
    const next = blankDraft(schema);
    setSuggesting(false); setEditing(null); setDraft(next); setInitialDraft(JSON.stringify(next)); setError(""); setOpen(true);
  }

  function edit(r: Row) {
    setSuggesting(false); setEditing(r); setDraft(r.data); setInitialDraft(JSON.stringify(r.data)); setError(""); setOpen(true);
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (saving.current) return;
    saving.current = true; setBusy(true); setError("");
    try {
      await apiRequest(`/business/records/${kind}/${editing ? editing.id + "/" : ""}`, { method: editing ? "PATCH" : "POST", body: { data: draft, revision: editing?.revision } });
      setOpen(false);
      void qc.invalidateQueries({ queryKey: ["business-records"] }).catch(() => {});
      if (kind === "leave_requests") void qc.invalidateQueries({ queryKey: ["daily-work"] });
      void qc.invalidateQueries({ queryKey: ["employee-payables"] });
      void qc.invalidateQueries({ queryKey: ["gst-review-sources"] });
      void qc.invalidateQueries({ queryKey: ["workforce-approvals"] });
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : "Could not save.");
    } finally {
      saving.current = false; setBusy(false);
    }
  }

  async function decide(r: Row, status: string) {
    setApproving(r.id);
    try {
      const result = await apiRequest<{ failed: Array<{ message: string }> }>("/business/workforce/approvals/", { method: "POST", body: { kind, ids: [r.id], status } });
      if (result.data.failed.length) setError(result.data.failed[0].message);
      void qc.invalidateQueries({ queryKey: ["business-records"] });
      void qc.invalidateQueries({ queryKey: ["workforce-approvals"] });
      void qc.invalidateQueries({ queryKey: ["daily-work"] });
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : "Could not update.");
    } finally {
      setApproving(null);
    }
  }

  async function exportData() {
    if (!schema) return;
    if (["payroll", "labour"].includes(schema.permission)) return exportWorkbook(`/business/workforce/reports/${kind}/?format=csv`, `NexEase-${kind}.csv`);
    if (kind === "expenses") return exportWorkbook("/business/expenses-export/", "NexEase-Expenses.csv");
    const list = records.data?.records ?? [];
    const csv = [Object.values(schema.fields).map((f) => f.label), ...list.map((r) => Object.keys(schema.fields).map((k) => String(r.data[k] ?? "")))]
      .map((row) => row.map((v) => '"' + (/^[=+@-]/.test(v) ? "'" : "") + v.replaceAll('"', '""') + '"').join(",")).join("\r\n");
    await downloadBlob(new Blob(["﻿" + csv], { type: "text/csv" }), `NexEase-${kind}.csv`);
  }

  // ---------------------------------------------------------------------------------------
  const available = kinds.filter((k) => config.data?.schemas[k]);
  const noun = presenter?.noun ?? "record";
  const tabs = available.length > 1 ? (
    <div className="nxf-segment nxw-tabs" role="tablist" aria-label={`${title} registers`}>
      {available.map((k) => (
        <button key={k} type="button" role="tab" aria-selected={k === kind} onClick={() => { setKind(k); setOpen(false); setError(""); setFilter(null); }}>
          {config.data?.schemas[k].label}
        </button>
      ))}
    </div>
  ) : null;

  if (config.isLoading) return <div className="nx-skeleton h-40" aria-busy="true" aria-label="Loading workspace" />;
  if (config.error) return <p role="alert" className="nxl-error">{config.error.message}</p>;

  const fields = schema ? Object.entries(schema.fields) : [];
  const shown = fields.filter(([k]) => kind !== "expenses" || k !== "employee_id" || draft.category === "Employee advance");
  const sectioned = (() => {
    const groups = presenter?.sections ?? [[schema?.label ?? "Details", shown.map(([k]) => k)]];
    const listed = new Set(groups.flatMap(([, keys]) => keys));
    const rest = shown.filter(([k]) => !listed.has(k)).map(([k]) => k);
    return [...groups, ...(rest.length ? [["More", rest, false] as [string, string[], boolean]] : [])]
      .map(([label, keys, collapsed]) => ({ label, collapsed: Boolean(collapsed), fields: shown.filter(([k]) => keys.includes(k)) }))
      .filter((g) => g.fields.length);
  })();

  const input = ([k, f]: [string, Field]) => {
    const required = f.required || (kind === "expenses" && draft.category === "Employee advance" && k === "employee_id");
    const label = `${f.label}${required ? " *" : ""}`;
    if (f.type === "boolean") {
      return (
        <label key={k} className="nxw-switch">
          <input type="checkbox" role="switch" className="nx-toggle" checked={!!draft[k]} onChange={(e) => setDraft({ ...draft, [k]: e.target.checked })} />
          <span>{f.label}</span>
        </label>
      );
    }
    if (["select", "employees", "sites", "customers", "accounts"].includes(f.type)) {
      return (
        <label key={k} className="block">
          {label}
          <SearchSelect aria-label={label} className="nx-input" required={required} value={String(draft[k] ?? "")} onChange={(e) => updateField(k, e.target.value)}>
            <option value="">Choose…</option>
            {f.type === "select"
              ? f.choices?.map((v) => <option key={v} value={v}>{v.charAt(0).toUpperCase() + v.slice(1).replaceAll("_", " ")}</option>)
              : source(f.type)?.map((r) => <option key={r.id} value={f.type === "customers" ? String(r.data.code) : r.id}>{String(r.data.name)} · {String(r.data.code)}</option>)}
          </SearchSelect>
        </label>
      );
    }
    return (
      <label key={k} className="block">
        {label}
        <input className="nx-input" required={required} type={["number", "date", "month"].includes(f.type) ? f.type : "text"} inputMode={f.type === "number" ? "decimal" : undefined}
          min={f.type === "number" ? 0 : undefined} step={f.type === "number" ? "0.01" : undefined} value={String(draft[k] ?? "")} onChange={(e) => updateField(k, e.target.value)} />
      </label>
    );
  };

  const approval = APPROVALS[kind];
  const canDecide = approval ? hasPermission(permissions, approval.permission) : false;

  return (
    <>
      <ListScreen<string>
        title={title}
        subtitle={description}
        primary={schema ? { label: `Add ${noun}`, icon: Plus, onClick: newRecord } : null}
        actions={schema ? [{ icon: FileSpreadsheet, label: "Export CSV", onClick: () => void exportData().catch((e: Error) => setError(e.message)) }] : []}
        onRefresh={schema ? () => void records.refetch() : undefined}
        refreshing={records.isFetching}
        above={tabs}
        search={schema ? { value: search, onChange: setSearch, placeholder: `Search ${schema.label.toLowerCase()}`, label: "Search records" } : undefined}
        chips={presenter?.filters ? { options: presenter.filters.map(([value, label]) => ({ value, label })), value: activeFilter, onChange: setFilter, label: "Status filter" } : undefined}
        footer={records.data ? <p className="nxl-pager">Showing {rows.length} of {records.data.total} {records.data.total > 1000 ? "(the newest 1,000 are loaded; use Export for all)" : ""}</p> : null}
      >
        {error && !open ? <p role="alert" className="nxl-error">{error}</p> : null}
        {!schema ? (
          <p className="p-6 text-sm">Your role does not have access to this section. Ask an administrator to assign the relevant permissions.</p>
        ) : (
          <ListState loading={records.isPending} error={records.error} onRetry={() => void records.refetch()} isEmpty={!rows.length} emptyIcon={Plus}
            emptyTitle={search || activeFilter ? `No ${noun}s match` : `No ${noun}s yet`}
            emptyDescription={search || activeFilter ? "Try another search or filter." : `Add your first ${noun} to begin.`}
            emptyAction={!search && !activeFilter ? <button type="button" className="nx-button" onClick={newRecord}><Plus size={16} />Add {noun}</button> : null}>
            <CompactList label={schema.label} columns={presenter!.columns.map((label) => ({ label }))}>
              {rows.map((r) => {
                const view = presenter!.present(r.data, name, r.key);
                const pending = approval && r.data.status === approval.pending && canDecide;
                const actions: ListAction[] = [
                  ...(pending ? [{ icon: Check, label: `Approve ${view.title}`, onClick: () => void decide(r, "approved"), busy: approving === r.id }] : []),
                  ...(pending && kind === "leave_requests" ? [{ icon: X, label: `Reject ${view.title}`, onClick: () => void decide(r, "rejected"), disabled: approving === r.id }] : []),
                  { icon: Pencil, label: `Edit ${view.title}`, onClick: () => edit(r) },
                ];
                return (
                  <CompactRow key={r.id} title={view.title} subtitle={view.subtitle} meta={view.meta} amount={view.amount} amountHint={view.amountHint}
                    badge={view.status ? <Badge tone={view.status.tone}>{view.status.label}</Badge> : undefined}
                    actions={actions} onOpen={() => edit(r)} openLabel={`Open ${view.title}`} />
                );
              })}
            </CompactList>
          </ListState>
        )}
      </ListScreen>

      {open && schema ? (
        <FormSheet title={`${editing ? "Edit" : "New"} ${noun}`} subtitle={schema.label} onClose={() => void closeForm()} busy={busy} size="lg" closeLabel="Close form">
          <form onSubmit={save} aria-busy={busy} className="flex flex-col gap-3.5">
            <fieldset disabled={busy || suggesting} className="flex min-w-0 flex-col gap-3.5">
              {suggesting ? <p role="status" className="nxf-hint">Loading approved hours and leave…</p> : null}
              {kind === "gst_settings" ? (
                <GstLookup onSelect={(r) => setDraft((d) => ({ ...d, gstin: r.gstin, state_code: r.gstin.slice(0, 2), legal_name: r.legal_name || r.name, ...(r.registration_type === "Regular" ? { registration: "regular" } : r.registration_type === "Composition" ? { registration: "composition" } : {}) }))} />
              ) : null}
              {kind === "expenses" && draft.category === "Employee advance" ? (
                <p className="nxf-hint rounded-xl bg-emerald-50 p-3">This payment will be saved in the employee advance register and posted as an advance asset. It will not be counted as a daily expense.</p>
              ) : null}
              {sectioned.map((g) => (g.collapsed ? (
                <details key={g.label} className="nxf-section" open={g.fields.some(([k]) => Boolean(draft[k]) && draft[k] !== "0")}>
                  <summary>{g.label}</summary>
                  <div className="nxf-grid mt-3">{g.fields.map(input)}</div>
                </details>
              ) : (
                <FormSection key={g.label} title={sectioned.length > 1 ? g.label : undefined}>
                  <div className="nxf-grid">{g.fields.map(input)}</div>
                  {kind === "employees" && g.label === "Pay" ? <FieldHint>Monthly pay is per month; daily, hourly and piece rates are per unit of work.</FieldHint> : null}
                </FormSection>
              )))}
              {error ? <p className="nxf-error" role="alert">{error}</p> : null}
            </fieldset>
            <FormActions hint={editing ? "Changes are saved with a revision check." : undefined}>
              <button type="button" disabled={busy} className="nx-button nx-secondary" onClick={() => void closeForm()}>Cancel</button>
              <button disabled={busy || suggesting} className="nx-button">{busy ? "Saving…" : "Save record"}</button>
            </FormActions>
          </form>
        </FormSheet>
      ) : null}
    </>
  );
}

export async function exportWorkbook(path: string, name: string) {
  const x = await apiBinaryRequest(path);
  await downloadBlob(x.blob, name);
}

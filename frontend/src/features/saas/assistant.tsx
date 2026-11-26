"use client";
import { confirmAction, notify } from "@/components/nex-feedback";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getConfig } from "@/features/business/workspace";
import VoiceInput from "./voice-input";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ArrowUp, Check, ChevronDown, FileText, History, IndianRupee, Package, Paperclip, Plus, Receipt, ShoppingCart, Sparkles, SquarePen, UserPlus, Wallet, X } from "lucide-react";
import { apiRequest, apiBinaryRequest } from "@/lib/api/client";
import AiFormHost from "@/features/ai/ai-form-host";
import { stashRecordPrefill } from "@/features/ai/handoff";
import { IN_PLACE, answerLabel, applyAnswer, recordPrefill, type Entry, type Missing, type Proposal } from "@/features/ai/forms";
import type { Membership } from "./types";

type Option = { id: string; name: string };
type Message = { id: string; role: "user" | "ai"; text: string; proposalId?: string; tone?: "error" | "done" };

function confirmationMessage(proposal: Proposal) {
  const detail = proposal.result?.message;
  const reason = typeof detail === "string" ? detail.trim() : "";
  if (proposal.state === "review") return reason || "Review the entry fields before confirming again.";
  const reference = proposal.result?.reference;
  return [reason, "Check existing records before retrying this entry.", reference ? "Reference: " + String(reference) : ""].filter(Boolean).join(" ");
}

const sets: Record<string, string[]> = {
  expense: ["date", "party_name", "category", "description", "amount", "payment_mode", "payment_account", "reference", "notes"],
  advance: ["date", "employee_name", "employee_id", "amount", "payment_mode", "payment_account", "reference", "notes"],
  invoice: ["date", "due_date", "number", "party_name", "party_code", "party_gstin", "party_address", "party_state", "document_total", "notes", "supply_type", "place_of_supply", "po_number", "po_date", "service_from", "service_to", "site_name"],
  bill: ["date", "number", "party_name", "party_code", "party_gstin", "party_address", "document_total", "notes"],
  stock_adjustment: ["product_name", "sku", "warehouse_id", "quantity_change", "notes"],
  category: ["name", "description"],
  product: ["name", "sku", "item_type", "hsn_code", "category_id", "unit", "selling_price", "cost_price", "description"],
  employee: ["name", "code", "employment_type", "joining_date", "basis", "rate", "overtime_rate", "phone", "designation", "department", "active", "pf_member", "esi_member", "bank_account", "ifsc"],
  site: ["name", "code", "customer_code", "address", "start_date", "end_date", "supervisor", "billing_rate", "active"],
  assignment: ["employee_id", "site_id", "start_date", "end_date", "shift", "role", "billing_rate", "status"],
  attendance: ["employee_id", "month", "period_days", "paid_days", "hours", "units", "overtime_hours", "allowances", "bonus", "arrears", "pf_wages", "esi_wages", "esi_employee_exempt", "tds", "professional_tax", "lwf", "advance_recovery", "other_deductions"],
  timesheet: ["employee_id", "site_id", "date", "shift", "hours", "overtime_hours", "billable_units", "billing_rate", "status", "notes"],
  leave_request: ["employee_id", "start_date", "end_date", "leave_type", "days", "status", "notes"],
  customer: ["name", "phone", "email", "party_gstin", "party_address", "party_state"],
  supplier: ["name", "phone", "email", "party_gstin", "party_address", "party_state"],
  payment_in: ["party_name", "amount", "payment_mode", "date", "reference", "notes"],
  payment_out: ["party_name", "amount", "payment_mode", "date", "reference", "notes"],
};
sets.purchase_order = sets.bill;

/** Starters fill the message box so the user only types the specifics. */
const STARTERS = [
  { icon: FileText, label: "Sale invoice", text: "Invoice to " , hint: "Sharma Traders: 10 bags cement at 380, 18% GST" },
  { icon: Wallet, label: "Payment in", text: "Received ", hint: "5000 from Sharma Traders by UPI" },
  { icon: Receipt, label: "Expense", text: "Paid ", hint: "500 for petrol by UPI to HP pump" },
  { icon: ShoppingCart, label: "Purchase bill", text: "Purchase bill from ", hint: "Om Steel, bill 221: 20 rods at 650, 18% GST" },
  { icon: UserPlus, label: "Add customer", text: "Add customer ", hint: "Mehta Hardware 9876543210 from Pune" },
  { icon: Package, label: "Add item", text: "Add item ", hint: "Cement 50kg, selling price 380, HSN 2523" },
  { icon: IndianRupee, label: "Payment out", text: "Paid supplier ", hint: "Om Steel 12000 by bank transfer" },
  { icon: Plus, label: "Stock in/out", text: "Add stock ", hint: "100 Cement 50kg to Main warehouse" },
];

const THINKING = ["Reading your request…", "Finding parties and items…", "Filling the form…"];
const CONSENT_KEY = "nexease-ai-consent";
const uid = () => Math.random().toString(36).slice(2);

function readConsent() {
  try { return localStorage.getItem(CONSENT_KEY) === "yes"; } catch { return false; }
}

export default function Assistant() {
  const [clock, setClock] = useState(() => Date.now());
  useEffect(() => { const id = setInterval(() => setClock(Date.now()), 30000); return () => clearInterval(id); }, []);
  const queryClient = useQueryClient();
  const router = useRouter();
  const pathname = usePathname();
  const moduleConfig = useQuery({ queryKey: ["business-config"], queryFn: getConfig });
  const [options, setOptions] = useState<Record<string, Option[]>>({});
  const [open, setOpen] = useState(false);
  const [member, setMember] = useState<Membership | null>();
  const [text, setText] = useState("");
  const [file, setFile] = useState<File>();
  const [proposals, setProposals] = useState<Record<string, Proposal>>({});
  const [activeId, setActiveId] = useState<string>();
  const [entry, setEntry] = useState<Entry>();
  const [details, setDetails] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [history, setHistory] = useState<Proposal[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [busy, setBusy] = useState(false);
  const [thinking, setThinking] = useState(0);
  const [providerEnabled, setProviderEnabled] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [consent, setConsent] = useState(readConsent);
  const [accounts, setAccounts] = useState<Option[]>([]);
  const [employees, setEmployees] = useState<Option[]>([]);
  const [sourceUrl, setSourceUrl] = useState("");
  const [sourceType, setSourceType] = useState("");
  const [usage, setUsage] = useState<{ requests: number; pages: number }>();
  const [formFor, setFormFor] = useState<Proposal>();
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const composer = useRef<HTMLTextAreaElement>(null);
  const thread = useRef<HTMLDivElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const formSaved = useRef(false);
  const active = activeId ? proposals[activeId] : undefined;

  // Ctrl/⌘ + J opens the assistant from anywhere; Esc closes it.
  useEffect(() => {
    const onKey = (e: globalThis.KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "j") { e.preventDefault(); setOpen((v) => !v); }
      else if (e.key === "Escape" && open && !formFor) setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, formFor]);

  useEffect(() => {
    if (!open) return;
    apiRequest<{ membership: Membership | null }>("/saas/subscription/").then((r) => {
      setMember(r.data.membership);
      if (r.data.membership?.features.includes("ai")) return apiRequest<{ options: Record<string, Option[]>; enabled: boolean; history: Proposal[]; accounts: Option[]; employees: Option[]; usage: { requests: number; pages: number } }>("/saas/ai/").then((r) => {
        setOptions(r.data.options ?? {}); setProviderEnabled(r.data.enabled); setHistory(r.data.history); setAccounts(r.data.accounts); setEmployees(r.data.employees); setUsage(r.data.usage);
      });
    }).catch((e: Error) => say(e.message, undefined, "error"));
    const t = setTimeout(() => composer.current?.focus(), 50);
    return () => clearTimeout(t);
  }, [open]);

  useEffect(() => () => { if (sourceUrl) URL.revokeObjectURL(sourceUrl); }, [sourceUrl]);
  useEffect(() => { thread.current?.scrollTo?.({ top: thread.current.scrollHeight, behavior: "smooth" }); }, [messages, busy, active]);
  useEffect(() => {
    if (!busy) return;
    const id = setInterval(() => setThinking((n) => Math.min(n + 1, THINKING.length - 1)), 1400);
    return () => clearInterval(id);
  }, [busy]);

  function say(textValue: string, proposalId?: string, tone?: Message["tone"]) {
    setMessages((m) => [...m, { id: uid(), role: "ai", text: textValue, proposalId, tone }]);
  }

  function remember(p: Proposal) {
    setProposals((all) => ({ ...all, [p.id]: p }));
    setActiveId(p.id); setEntry(p.data); setDirty(false); setSourceUrl("");
    setDetails(!p.assist || (!p.assist.form && p.kind !== "question") || !!(p.assist.form && !IN_PLACE.has(p.assist.form.type) && p.assist.form.type !== "record"));
  }

  async function run(fn: () => Promise<void>) {
    setBusy(true); setThinking(0);
    try { await fn(); } catch (e) { say((e as Error).message, undefined, "error"); } finally { setBusy(false); }
  }

  function openForm(p: Proposal, data: Entry = p.data) {
    const target = p.assist?.form;
    if (!target) return;
    if (target.type === "record" && target.record_kind) {
      stashRecordPrefill({ kind: target.record_kind, data: recordPrefill(data, target.record_kind, p.id) });
      setOpen(false);
      if (target.route && pathname !== target.route) router.push(target.route);
      return;
    }
    if (IN_PLACE.has(target.type)) { formSaved.current = false; setFormFor({ ...p, data }); }
  }

  /** After each AI step: ask for what is missing, or open the form when everything is there. */
  function respond(p: Proposal) {
    remember(p);
    const a = p.assist;
    say(a?.reply ?? (p.kind === "question" ? p.data.questions.join(" ") : "Here is what I prepared. Check the details below."), p.id);
    if (a?.ready && a.form && a.missing.length === 0 && (IN_PLACE.has(a.form.type) || a.form.type === "record")) setTimeout(() => openForm(p), 450);
  }

  async function send(raw?: string) {
    const message = (raw ?? text).trim();
    if (busy || !providerEnabled || !consent || (!message && !file)) return;
    // A reply to a question continues the same entry; anything else starts a new one.
    const continuing = active?.state === "review" && (active.assist?.missing.length ?? 0) > 0;
    setMessages((m) => [...m, { id: uid(), role: "user", text: message || (file ? "📎 " + file.name : "") }]);
    setText(""); setShowHistory(false);
    await run(async () => {
      if (dirty && active && entry) { await apiRequest(`/saas/ai/${active.id}/review/`, { method: "POST", body: { data: entry } }); setDirty(false); }
      let body: unknown;
      const previous = continuing || (file && active?.state === "review") ? active?.id : undefined;
      if (file) { const f = new FormData(); f.append("file", file); f.append("message", message); f.append("request_key", crypto.randomUUID()); if (previous) f.append("previous_id", previous); body = f; }
      else body = { message, request_key: crypto.randomUUID(), previous_id: previous };
      const r = await apiRequest<Proposal>("/saas/ai/", { method: "POST", body });
      setFile(undefined);
      setHistory((h) => [r.data, ...h.filter((x) => x.id !== r.data.id)].slice(0, 10));
      setUsage((u) => (u ? { ...u, requests: u.requests + (file ? 0 : 1) } : u));
      respond(r.data);
    });
  }

  /** Quick answers update the entry directly — no second AI call, so they feel instant. */
  async function answer(m: Missing, value: string) {
    if (!active || !entry || !value.trim()) return;
    const next = applyAnswer(entry, m.field, value.trim());
    setMessages((all) => [...all, { id: uid(), role: "user", text: answerLabel(m, value.trim()) }]);
    setAnswers((a) => ({ ...a, [m.field]: "" }));
    setEntry(next);
    await run(async () => {
      const r = await apiRequest<Proposal>(`/saas/ai/${active.id}/review/`, { method: "POST", body: { data: next } });
      respond(r.data);
    });
  }

  async function saveDetails() {
    if (!active || !entry) return;
    await run(async () => { const r = await apiRequest<Proposal>(`/saas/ai/${active.id}/review/`, { method: "POST", body: { data: entry } }); respond(r.data); });
  }

  async function quickSave() {
    if (!active) return;
    if (!(await confirmAction("Save this entry now? Stock changes update inventory and the ledger. Expenses and advances post to books; bills and invoices stay drafts."))) return;
    await run(async () => {
      if (dirty && entry) { await apiRequest(`/saas/ai/${active.id}/review/`, { method: "POST", body: { data: entry } }); setDirty(false); }
      const r = await apiRequest<Proposal>(`/saas/ai/${active.id}/confirm/`, { method: "POST", body: { confirm: true } });
      setProposals((all) => ({ ...all, [r.data.id]: r.data }));
      if (r.data.state === "saved") {
        await queryClient.invalidateQueries();
        notify(r.data.kind === "stock_adjustment" ? "Stock updated successfully." : "Entry saved successfully.");
        say(r.data.kind === "stock_adjustment" ? "Done — stock updated and recorded in the ledger. What next?" : "Saved. Invoices and bills stay as drafts until you issue them. What next?", r.data.id, "done");
      } else say(confirmationMessage(r.data), r.data.id, "error");
    });
  }

  function reset() {
    setActiveId(undefined); setEntry(undefined); setFile(undefined); setText(""); setSourceUrl(""); setDirty(false); setDetails(false); setMessages([]);
    composer.current?.focus();
  }

  function starter(s: (typeof STARTERS)[number]) {
    setText(s.text);
    requestAnimationFrame(() => { const el = composer.current; if (el) { el.focus(); el.setSelectionRange(s.text.length, s.text.length); } });
  }

  function onComposerKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); if (!e.repeat) void send(); }
  }

  const allowed = member?.features.includes("ai") && ["active", "trial"].includes(member.status) && new Date(member.end + "Z").getTime() > clock && !member.suspended;

  function field(k: string, v: string, onChange: (s: string) => void) {
    const label = k.replaceAll("_", " ");
    if (["employee_id", "payment_account", "site_id", "category_id", "warehouse_id"].includes(k)) {
      const list = k === "employee_id" ? employees : k === "site_id" ? options.sites ?? [] : k === "category_id" ? options.categories ?? [] : k === "warehouse_id" ? options.warehouses ?? [] : accounts;
      return <label key={k}>{label}<select value={v} onChange={(e) => onChange(e.target.value)}><option value="">{k === "payment_account" ? "Default control account" : "Choose record"}</option>{list.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select></label>;
    }
    return <label key={k}>{label}<input type={["date", "due_date"].includes(k) ? "date" : "text"} value={v} onChange={(e) => onChange(e.target.value)} /></label>;
  }

  function updateEntry(next: Entry) { setEntry(next); setDirty(true); }

  if (moduleConfig.data?.modules?.ai === false) return null;

  const canSend = !busy && providerEnabled && consent && Boolean(text.trim() || file);
  const lastAiFor = (pid: string) => [...messages].reverse().find((m) => m.role === "ai" && m.proposalId === pid)?.id;

  function card(p: Proposal) {
    const a = p.assist;
    const current = p.id === activeId && entry ? entry : p.data;
    const editable = p.state === "review";
    const required = a?.missing.filter((m) => m.required) ?? [];
    const form = a?.form;
    const opensForm = !!form && (IN_PLACE.has(form.type) || form.type === "record");
    return (
      <div className="nxai-card" data-state={p.state}>
        <div className="nxai-card-head">
          <span className="nxai-kind">{a?.label ?? p.kind.replaceAll("_", " ")}</span>
          <span className="nxai-state" data-tone={p.state === "saved" ? "done" : required.length ? "warn" : "ok"}>{p.state === "saved" ? "Saved" : p.state !== "review" ? p.state.replaceAll("_", " ") : required.length ? `${required.length} detail${required.length > 1 ? "s" : ""} needed` : "Ready"}</span>
        </div>
        {a?.summary.length ? <dl className="nxai-summary">{a.summary.map((row) => <div key={row.label}><dt>{row.label}</dt><dd>{row.value}</dd></div>)}</dl> : null}
        {p.kind === "stock_adjustment" && <p className="nxai-note">This changes stock of an existing item; no new item is created.</p>}
        {a?.notes?.length ? <ul className="nxai-notes">{a.notes.map((n) => <li key={n}>{n}</li>)}</ul> : null}
        {editable && a?.missing.length ? (
          <div className="nxai-asks">
            {a.missing.map((m) => (
              <div key={m.field} className="nxai-ask">
                <p>{m.question}{!m.required && <span> · optional</span>}</p>
                {m.choices.length ? (
                  <div className="nxai-chips">{m.choices.map((c) => <button key={c} type="button" disabled={busy} onClick={() => void answer(m, c)}>{m.label.includes("GST") ? c + "%" : c}</button>)}</div>
                ) : (
                  <form className="nxai-inline" onSubmit={(e) => { e.preventDefault(); void answer(m, answers[m.field] ?? ""); }}>
                    <input aria-label={m.label} type={m.input === "number" ? "number" : m.input === "date" ? "date" : "text"} step={m.input === "number" ? "any" : undefined} value={answers[m.field] ?? ""} placeholder={m.label} onChange={(e) => setAnswers((x) => ({ ...x, [m.field]: e.target.value }))} />
                    <button type="submit" aria-label={`Answer ${m.label}`} disabled={busy || !(answers[m.field] ?? "").trim()}><Check size={16} /></button>
                  </form>
                )}
              </div>
            ))}
          </div>
        ) : null}
        {editable && (
          <div className="nxai-actions">
            {opensForm && <button type="button" className="nx-button" disabled={busy} onClick={() => openForm(p, current)}><SquarePen size={16} />{required.length ? "Open form anyway" : "Open form"}</button>}
            {a?.quick_save !== false && p.kind !== "question" && (!opensForm || !required.length) && (
              <button type="button" className={opensForm ? "nx-button nx-secondary" : "nx-button"} disabled={busy || (opensForm && dirty)} onClick={() => void quickSave()}>{p.kind === "stock_adjustment" ? "Confirm stock update" : opensForm ? "Quick save" : "Confirm & save"}</button>
            )}
            {p.kind !== "question" && <button type="button" className="nxai-link" aria-expanded={details && p.id === activeId} onClick={() => { setActiveId(p.id); setEntry(p.data); setDetails((d) => (p.id === activeId ? !d : true)); }}>Details<ChevronDown size={14} /></button>}
          </div>
        )}
        {editable && details && p.id === activeId && entry && (
          <div className="nxai-details">
            <div className="nxai-grid">
              {Array.from(new Set([...(sets[entry.kind] ?? []), ...Object.keys(entry.fields).filter((k) => entry.fields[k] !== "" && !(entry.kind === "stock_adjustment" && ["product_id", "warehouse_name"].includes(k)))])).map((k) =>
                field(k, entry.fields[k] ?? "", (v) => updateEntry({ ...entry, fields: { ...entry.fields, [k]: v, ...(entry.kind === "stock_adjustment" && k === "product_name" ? { product_id: "", sku: "" } : entry.kind === "stock_adjustment" && k === "sku" ? { product_id: "", product_name: "" } : entry.kind === "stock_adjustment" && k === "warehouse_id" ? { warehouse_name: "" } : {}) } })))}
            </div>
            {entry.kind !== "stock_adjustment" && entry.items?.map((item, i) => (
              <fieldset key={i} className="nxai-line">
                <legend>Item {i + 1}</legend>
                <div className="nxai-grid">{Object.keys(item).map((k) => field(k, item[k], (v) => updateEntry({ ...entry, items: entry.items.map((x, j) => (j === i ? { ...x, [k]: v } : x)) })))}</div>
                <button type="button" className="nxai-link nxai-danger" onClick={() => updateEntry({ ...entry, items: entry.items.filter((_, j) => j !== i) })}>Remove line</button>
              </fieldset>
            ))}
            {["invoice", "bill", "purchase_order"].includes(entry.kind) && <button type="button" className="nxai-link" onClick={() => updateEntry({ ...entry, items: [...entry.items, { item_type: "goods", hsn_code: "", sku: "", name: "", unit: "", quantity: "", unit_price: "", tax_rate: "", discount: "" }] })} title="Add item" aria-label="Add item"><Plus size={14} />Add line</button>}
            <div className="nxai-actions">
              <button type="button" className="nx-button nx-secondary" disabled={busy || !dirty} onClick={() => void saveDetails()}>Save changes</button>
              <button type="button" className="nxai-link" onClick={() => void run(async () => { const r = await apiBinaryRequest(`/saas/ai/${p.id}/source/`); setSourceType(r.contentType); setSourceUrl(URL.createObjectURL(r.blob)); })}>View uploaded source</button>
            </div>
            {sourceUrl && (sourceType.includes("pdf") ? <iframe title="Uploaded invoice" src={sourceUrl} className="nxai-source" /> : <img alt="Uploaded bill" src={sourceUrl} className="nxai-source" />)}
          </div>
        )}
        {!editable && p.state !== "saved" && Object.keys(p.result ?? {}).length > 0 && <div className="nxai-note">{Object.entries(p.result).map(([k, v]) => <p key={k}><b>{k}:</b> {typeof v === "object" ? JSON.stringify(v) : String(v)}</p>)}</div>}
      </div>
    );
  }

  return (
    <>
      <button aria-label="Open NexEase AI" title="NexEase AI (Ctrl+J)" className="nxai-fab" data-open={open || undefined} onClick={() => setOpen(true)}><Sparkles size={19} /><span>NexEase AI</span></button>
      {open && (
        <aside aria-label="NexEase AI assistant" className="nxai-panel" hidden={Boolean(formFor)}>
          <header className="nxai-head">
            <div className="nxai-avatar"><Sparkles size={18} /></div>
            <div className="min-w-0">
              <h2>NexEase AI</h2>
              <p>{busy ? THINKING[thinking] : providerEnabled ? "Tell me what to record — I fill the form for you" : "Prepare · Review · Save"}</p>
            </div>
            <div className="nxai-head-actions">
              {allowed && history.length > 0 && <button type="button" aria-label="Recent entries" aria-pressed={showHistory} onClick={() => setShowHistory((v) => !v)}><History size={18} /></button>}
              {allowed && <button type="button" aria-label="New request" disabled={busy} onClick={reset}><SquarePen size={18} /></button>}
              <button type="button" aria-label="Close assistant" onClick={() => setOpen(false)}><X size={20} /></button>
            </div>
          </header>
          {!allowed ? (
            <div className="nxai-body"><div className="nxai-locked"><Sparkles size={28} /><h3>Included with NexEase Pro</h3><p>An active Pro subscription or trial is required.</p><Link href="/subscription" className="nx-button" onClick={() => setOpen(false)}>View subscription</Link></div></div>
          ) : (
            <>
              <div className="nxai-body" ref={thread}>
                {!providerEnabled && <p className="nxai-banner">The owner must configure and enable the AI provider before preparing new entries.</p>}
                {showHistory && (
                  <div className="nxai-history">
                    <h3>Recent entries</h3>
                    {history.map((p) => <button key={p.id} type="button" onClick={() => { remember(p); setShowHistory(false); setMessages((m) => [...m, { id: uid(), role: "ai", text: p.assist?.reply ?? "Reopened " + (p.kind || "entry").replaceAll("_", " ") + ".", proposalId: p.id }]); }}><span>{p.assist?.label ?? (p.kind || "Extraction").replaceAll("_", " ")}</span><small>{p.state} · {p.id.slice(-6)}</small></button>)}
                  </div>
                )}
                {messages.length === 0 && !showHistory && (
                  <div className="nxai-welcome">
                    <h3>What would you like to record?</h3>
                    <p>Type or speak in English, Hindi or Hinglish. I open the right form already filled in, and ask if anything is missing.</p>
                    <div className="nxai-starters">{STARTERS.map((s) => <button key={s.label} type="button" onClick={() => starter(s)}><s.icon size={17} /><span>{s.label}</span></button>)}</div>
                    <p className="nxai-usage">Used this period: {usage?.requests ?? 0} chats · {usage?.pages ?? 0} scan pages</p>
                  </div>
                )}
                {messages.map((m) => (
                  <div key={m.id} className="nxai-msg" data-role={m.role} data-tone={m.tone}>
                    {m.role === "ai" && <span className="nxai-msg-avatar"><Sparkles size={13} /></span>}
                    <div>
                      <p className="nxai-bubble">{m.text}</p>
                      {m.role === "ai" && m.proposalId && proposals[m.proposalId] && lastAiFor(m.proposalId) === m.id && card(proposals[m.proposalId])}
                    </div>
                  </div>
                ))}
                {active && !messages.some((m) => m.proposalId === active.id) && card(active)}
                {busy && <div className="nxai-msg" data-role="ai"><span className="nxai-msg-avatar"><Sparkles size={13} /></span><p className="nxai-bubble nxai-typing" role="status"><i /><i /><i /><span>{THINKING[thinking]}</span></p></div>}
              </div>
              <footer className="nxai-composer">
                {!consent && <label className="nxai-consent"><input type="checkbox" checked={consent} onChange={(e) => { setConsent(e.target.checked); try { localStorage.setItem(CONSENT_KEY, e.target.checked ? "yes" : "no"); } catch { /* storage unavailable */ } }} />I am authorized to send this content to the configured AI provider.</label>}
                {file && <p className="nxai-file"><Paperclip size={14} />{file.name}<button type="button" aria-label="Remove attachment" onClick={() => setFile(undefined)}><X size={14} /></button></p>}
                <div className="nxai-input">
                  <button type="button" className="nxai-icon" aria-label="Attach bill (PDF, JPG or PNG)" title="Attach bill · PDF/JPG/PNG · 8 MB · up to 10 pages" onClick={() => fileInput.current?.click()}><Paperclip size={18} /></button>
                  <input ref={fileInput} hidden aria-label="Upload invoice or bill" type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => { setFile(e.target.files?.[0]); e.target.value = ""; }} />
                  <textarea ref={composer} aria-label="AI instruction" rows={1} value={text} onKeyDown={onComposerKey} onChange={(e) => setText(e.target.value)} placeholder={active?.assist?.missing.length ? "Answer here, or tap a choice above…" : "e.g. Invoice Sharma Traders 10 cement at 380, 18% GST"} />
                  <VoiceInput compact onError={(m) => say(m, undefined, "error")} onText={(value) => setText((t) => t + (t ? " " : "") + value)} />
                  <button type="button" className="nxai-send" aria-label="Prepare entry" disabled={!canSend} onClick={() => void send()}><ArrowUp size={18} /></button>
                </div>
                <p className="nxai-hint">Enter to send · Shift+Enter new line · Ctrl+J to open · Nothing is saved until you confirm.</p>
              </footer>
            </>
          )}
        </aside>
      )}
      {formFor && (
        <AiFormHost
          key={formFor.id}
          proposal={formFor}
          onClose={() => { setFormFor(undefined); if (!formSaved.current) say("Form closed. If you saved it, it is in your records now. Anything else?"); formSaved.current = false; }}
          onSaved={(what) => { formSaved.current = true; setFormFor(undefined); void queryClient.invalidateQueries(); say(what + " What next?", undefined, "done"); }}
        />
      )}
    </>
  );
}

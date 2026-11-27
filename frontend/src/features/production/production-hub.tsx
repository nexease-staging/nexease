"use client";

import Link from "next/link";
import { Suspense, useEffect, useMemo, useState, useSyncExternalStore, type FormEvent, type ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  AlertTriangle, Boxes, Check, ChevronRight, CircleDollarSign, ClipboardList, Factory, FileText, Hammer, Kanban, LayoutList, ListChecks, MessageCircle,
  PackageCheck, PauseCircle, Phone, PlayCircle, Plus, ReceiptIndianRupee, RefreshCw, Search, Settings2, Trash2, Truck, Undo2, Users, X, XCircle,
} from "lucide-react";
import SearchSelect from "@/components/search-select";
import StatCard from "@/components/ui/stat-card";
import { Badge, type Tone } from "@/components/ui/badge";
import { useAuth } from "@/features/auth/auth-context";
import { hasPermission } from "@/lib/authorization/permissions";
import {
  PRIORITY_LABEL, STATUS_LABEL, dueText, inr, qty, today, useBoard, useCreateJob, useDeleteRecipe, useInvoiceJob, useJob, useJobAction, useRecipe, useRecipes,
  useSaveRecipe, useSaveStages, useStageSettings, useWarehouses, type Filters, type Job, type JobRow, type JobStatus, type Priority, type Recipe, type Stage,
} from "./api";

const TABS = [
  { key: "jobs", label: "Jobs", icon: ClipboardList },
  { key: "recipes", label: "Recipes & made to order", icon: ListChecks },
  { key: "batches", label: "Batch production", icon: Factory },
] as const;
type Tab = (typeof TABS)[number]["key"];

const STATUS_TONE: Record<JobStatus, Tone> = { open: "info", on_hold: "warning", completed: "success", delivered: "violet", cancelled: "neutral" };

function usePerms() {
  const { authentication } = useAuth();
  const can = (p: string) => hasPermission(authentication?.role.permissions ?? [], p);
  return { manage: can("manufacturing.manage"), stock: can("inventory.adjust"), invoice: can("invoices.create") };
}

const PHONE = "(max-width: 640px)";
function useIsPhone() {
  return useSyncExternalStore(
    (cb) => { const m = typeof window !== "undefined" ? window.matchMedia?.(PHONE) : null; m?.addEventListener?.("change", cb); return () => m?.removeEventListener?.("change", cb); },
    () => (typeof window !== "undefined" && window.matchMedia ? window.matchMedia(PHONE).matches : false),
    () => false,
  );
}

function errorText(e: unknown) {
  return (e as Error)?.message || "Something went wrong. Try again.";
}

// ---------------------------------------------------------------------------------------------
// Shell bits
// ---------------------------------------------------------------------------------------------

function Sheet({ title, sub, onClose, children, footer, wide = false }: { title: ReactNode; sub?: ReactNode; onClose: () => void; children: ReactNode; footer?: ReactNode; wide?: boolean }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", onKey); document.body.style.overflow = prev; };
  }, [onClose]);
  return (
    <div className="nxpr-overlay" role="dialog" aria-modal="true" aria-label={typeof title === "string" ? title : undefined} onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="nxpr-sheet" data-wide={wide || undefined}>
        <header className="nxpr-sheet-head">
          <div className="min-w-0"><h2>{title}</h2>{sub ? <p>{sub}</p> : null}</div>
          <button type="button" className="nxpr-icon" aria-label="Close" onClick={onClose}><X size={18} /></button>
        </header>
        <div className="nxpr-sheet-body">{children}</div>
        {footer ? <footer className="nxpr-sheet-foot">{footer}</footer> : null}
      </div>
    </div>
  );
}

function Field({ label, hint, children, wide = false }: { label: string; hint?: string; children: ReactNode; wide?: boolean }) {
  return <label className="nxpr-field" data-wide={wide || undefined}><span>{label}</span>{children}{hint ? <em>{hint}</em> : null}</label>;
}

function Priority({ value }: { value: Priority }) {
  return <span className="nxpr-priority" data-p={value}>{PRIORITY_LABEL[value]}</span>;
}

function Track({ index, total, done }: { index: number; total: number; done: boolean }) {
  return (
    <span className="nxpr-track" aria-hidden="true">
      {Array.from({ length: total }, (_, i) => <i key={i} data-on={done || i < index ? "done" : i === index ? "now" : undefined} />)}
    </span>
  );
}

function initials(name: string) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join("");
}

// ---------------------------------------------------------------------------------------------
// Jobs board
// ---------------------------------------------------------------------------------------------

function JobTicket({ row, total, onOpen }: { row: JobRow; total: number; onOpen: () => void }) {
  const costShare = Number(row.quoted) ? Math.min(100, (100 * Number(row.cost)) / Number(row.quoted)) : 0;
  return (
    <button type="button" className="nxpr-ticket" data-status={row.status} data-late={row.overdue || undefined} onClick={onOpen}>
      <span className="nxpr-stub">
        <b>{row.number.replace("JOB-", "")}</b>
        <small>{row.due ? new Date(row.due).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : "—"}</small>
      </span>
      <span className="nxpr-ticket-main">
        <span className="nxpr-ticket-top">
          <Priority value={row.priority} />
          {row.status === "on_hold" ? <Badge tone="warning" icon={PauseCircle}>On hold</Badge> : null}
          {row.invoice ? <Badge tone="success" icon={ReceiptIndianRupee}>Invoiced</Badge> : null}
        </span>
        <strong>{row.title}</strong>
        <span className="nxpr-ticket-sub">
          {row.customer?.name ?? "No customer"}{row.product ? ` · ${qty(row.quantity)} ${row.unit}` : ""}
        </span>
        <Track index={row.stage_index} total={total} done={row.status === "completed" || row.status === "delivered"} />
        <span className="nxpr-ticket-foot">
          <span className="nxpr-due" data-late={row.overdue || undefined}>{row.overdue ? <AlertTriangle size={13} /> : null}{dueText(row)}</span>
          <span className="nxpr-people">{row.assignees.slice(0, 3).map((a) => <i key={a} title={a}>{initials(a)}</i>)}</span>
        </span>
        {Number(row.quoted) ? (
          <span className="nxpr-costbar" title={`Cost ${inr(row.cost)} of ${inr(row.quoted)} quoted`}>
            <i style={{ width: `${costShare}%` }} data-over={Number(row.cost) > Number(row.quoted) || undefined} />
          </span>
        ) : null}
      </span>
    </button>
  );
}

function JobsPanel({ onOpen, onNew }: { onOpen: (id: string) => void; onNew: () => void }) {
  const [f, setF] = useState<Filters>({ status: "active", stage: "", search: "", priority: "", overdue: false });
  const [search, setSearch] = useState("");
  const phone = useIsPhone();
  const [chosen, setView] = useState<"board" | "list" | null>(null);
  const view = chosen ?? (phone ? "list" : "board");
  const [stagesOpen, setStagesOpen] = useState(false);
  const perms = usePerms();
  useEffect(() => {
    const t = setTimeout(() => setF((x) => ({ ...x, search })), 250);
    return () => clearTimeout(t);
  }, [search]);
  const board = useBoard(f);
  const d = board.data;
  const s = d?.summary;
  const stages = useMemo(() => d?.stages ?? [], [d]);
  const columns = useMemo(() => stages.map((st) => ({ ...st, rows: (d?.rows ?? []).filter((r) => r.stage === st.key) })), [d, stages]);
  const boardMode = view === "board" && f.status === "active" && !f.stage;

  return (
    <div className="nxpr-stack">
      <div className="nxpr-kpis">
        <StatCard label="Active jobs" value={String(s?.active ?? 0)} hint={s?.on_hold ? `${s.on_hold} on hold` : "In the workshop now"} icon={Hammer} tone="info" loading={!s} />
        <StatCard label="Late" value={String(s?.overdue ?? 0)} hint={`${s?.due_week ?? 0} due in the next 7 days`} icon={AlertTriangle} tone={s?.overdue ? "danger" : "neutral"} loading={!s} />
        <StatCard label="Work in progress" value={inr(s?.wip_value)} hint="Material, labour and costs so far" icon={Boxes} tone="violet" loading={!s} />
        <StatCard label="Margin, last 30 days" value={inr(s?.margin_30d)} hint={`${s?.completed_30d ?? 0} jobs finished${s?.margin_pct_30d ? ` · ${s.margin_pct_30d}%` : ""}`} icon={CircleDollarSign} tone="success" loading={!s} />
        <StatCard label="Ready to invoice" value={String(s?.to_invoice ?? 0)} hint="Finished jobs without an invoice" icon={ReceiptIndianRupee} tone={s?.to_invoice ? "warning" : "neutral"} loading={!s} />
      </div>

      <nav className="nxpr-rail" aria-label="Filter by stage">
        <button type="button" aria-pressed={!f.stage} onClick={() => setF((x) => ({ ...x, stage: "" }))}><span>All stages</span><b>{s?.active ?? 0}</b></button>
        {(s?.by_stage ?? []).map((st, i) => (
          <button key={st.key} type="button" aria-pressed={f.stage === st.key} onClick={() => setF((x) => ({ ...x, stage: x.stage === st.key ? "" : st.key, status: "active" }))}>
            <span><small>{i + 1}</small>{st.label}</span><b>{st.count}</b>
          </button>
        ))}
        {perms.manage ? <button type="button" className="nxpr-rail-edit" onClick={() => setStagesOpen(true)} aria-label="Edit stages"><Settings2 size={15} /></button> : null}
      </nav>

      <div className="nxpr-toolbar">
        <label className="nxpr-search"><Search size={16} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search job, customer, item or worker" aria-label="Search jobs" /></label>
        <select className="nxpr-select" aria-label="Status" value={f.status} onChange={(e) => setF((x) => ({ ...x, status: e.target.value }))}>
          <option value="active">Active</option><option value="on_hold">On hold</option><option value="done">Finished</option><option value="cancelled">Cancelled</option><option value="all">All jobs</option>
        </select>
        <select className="nxpr-select" aria-label="Priority" value={f.priority} onChange={(e) => setF((x) => ({ ...x, priority: e.target.value }))}>
          <option value="">Any priority</option>{(["urgent", "high", "normal", "low"] as Priority[]).map((p) => <option key={p} value={p}>{PRIORITY_LABEL[p]}</option>)}
        </select>
        <label className="nxpr-check"><input type="checkbox" checked={f.overdue} onChange={(e) => setF((x) => ({ ...x, overdue: e.target.checked }))} />Late only</label>
        <div className="nxpr-seg" role="group" aria-label="View">
          <button type="button" aria-pressed={view === "board"} onClick={() => setView("board")} aria-label="Board view"><Kanban size={16} /></button>
          <button type="button" aria-pressed={view === "list"} onClick={() => setView("list")} aria-label="List view"><LayoutList size={16} /></button>
        </div>
      </div>

      {board.isPending ? <div className="nxpr-skeleton"><i /><i /><i /></div> : board.error ? (
        <div className="nxpr-error" role="alert">{errorText(board.error)}<button type="button" onClick={() => void board.refetch()}><RefreshCw size={14} />Try again</button></div>
      ) : !d?.rows.length ? (
        <div className="nxpr-empty">
          <ClipboardList size={30} />
          <h3>{f.search || f.stage || f.overdue || f.status !== "active" ? "No jobs match these filters" : "No jobs in the workshop"}</h3>
          <p>Open a job card for each order you make: an almirah, a set of racks, a shop counter. Track its stage, the material it uses, labour and cost against your price.</p>
          {perms.manage ? <button type="button" className="nx-button" onClick={onNew}><Plus size={16} />New job</button> : null}
        </div>
      ) : boardMode ? (
        <div className="nxpr-board">
          {columns.map((c) => (
            <section key={c.key} className="nxpr-col" aria-label={c.label}>
              <header><span>{c.label}</span><b>{c.rows.length}</b></header>
              <div className="nxpr-col-body">
                {c.rows.map((r) => <JobTicket key={r.id} row={r} total={stages.length} onOpen={() => onOpen(r.id)} />)}
                {!c.rows.length ? <p className="nxpr-col-empty">Nothing here</p> : null}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="nxpr-list" role="table" aria-label="Jobs">
          <div className="nxpr-list-head" role="row"><span>Job</span><span>Stage</span><span>Due</span><span>Quoted</span><span>Cost so far</span><span>Status</span></div>
          {d.rows.map((r) => (
            <button key={r.id} type="button" className="nxpr-list-row" role="row" onClick={() => onOpen(r.id)} data-late={r.overdue || undefined}>
              <span className="nxpr-list-job"><b>{r.number}</b><strong>{r.title}</strong><small>{r.customer?.name ?? "No customer"}{r.product ? ` · ${qty(r.quantity)} ${r.unit}` : ""}</small></span>
              <span className="nxpr-list-stage"><small>{r.stage_label}</small><Track index={r.stage_index} total={stages.length} done={r.status === "completed" || r.status === "delivered"} /></span>
              <span className="nxpr-due" data-late={r.overdue || undefined}>{dueText(r)}</span>
              <span className="nxpr-num">{inr(r.quoted)}</span>
              <span className="nxpr-num">{inr(r.cost)}</span>
              <span><Badge tone={STATUS_TONE[r.status]}>{STATUS_LABEL[r.status]}</Badge></span>
            </button>
          ))}
        </div>
      )}
      {d && d.count > d.rows.length ? <p className="nxpr-fine">Showing {d.rows.length} of {d.count}. Search or filter to narrow down.</p> : null}
      {stagesOpen ? <StagesSheet onClose={() => setStagesOpen(false)} /> : null}
    </div>
  );
}

// ---------------------------------------------------------------------------------------------
// Job card (detail)
// ---------------------------------------------------------------------------------------------

function MaterialRow({ m, job, act, busy, canStock }: { m: Job["materials"][number]; job: Job; act: (b: Record<string, unknown>) => Promise<unknown>; busy: boolean; canStock: boolean }) {
  const [amount, setAmount] = useState("");
  const open = job.status === "open" || job.status === "on_hold";
  const short = Number(m.pending) > Number(m.available);
  const go = async (action: "issue" | "return") => {
    if (!amount) return;
    await act({ action, product: m.product, quantity: amount });
    setAmount("");
  };
  return (
    <div className="nxpr-mat">
      <div className="nxpr-mat-name"><strong>{m.name}</strong><small>{inr(m.rate, 2)} / {m.unit}</small></div>
      <div className="nxpr-mat-figs">
        <span><small>Planned</small>{qty(m.planned)}</span>
        <span><small>Issued</small><b>{qty(m.issued)}</b></span>
        <span data-short={short || undefined}><small>In stock</small>{qty(m.available)}</span>
        <span><small>Value</small>{inr(m.value)}</span>
      </div>
      {open && canStock ? (
        <div className="nxpr-mat-act">
          <input className="nx-input" inputMode="decimal" aria-label={`Quantity of ${m.name}`} placeholder={Number(m.pending) ? qty(m.pending) : "Qty"} value={amount} onChange={(e) => setAmount(e.target.value)} />
          <button type="button" className="nx-button" disabled={busy || !amount} onClick={() => void go("issue")} aria-label={`Issue ${m.name}`}>Issue</button>
          <button type="button" className="nxpr-ghost" disabled={busy || !amount || !Number(m.issued)} onClick={() => void go("return")} aria-label={`Return ${m.name}`}><Undo2 size={15} /></button>
        </div>
      ) : null}
    </div>
  );
}

function CostBox({ job }: { job: Job }) {
  const c = job.costs;
  const total = Number(c.total), quoted = Number(c.quoted);
  const parts = [["Material", c.material, "m"], ["Labour", c.labour, "l"], ["Other costs", c.expenses, "e"]] as const;
  return (
    <section className="nxpr-box nxpr-costs">
      <h3>Cost against price</h3>
      <div className="nxpr-cost-figs">
        <div><small>Quoted price</small><strong>{inr(c.quoted)}</strong></div>
        <div><small>Cost so far</small><strong>{inr(c.total)}</strong></div>
        <div data-neg={Number(c.margin) < 0 || undefined}><small>Margin</small><strong>{inr(c.margin)}</strong>{c.margin_pct ? <em>{c.margin_pct}%</em> : null}</div>
      </div>
      <div className="nxpr-stackbar" aria-hidden="true">
        {parts.map(([, v, k]) => <i key={k} data-k={k} style={{ width: `${Math.max(quoted, total) ? (100 * Number(v)) / Math.max(quoted, total) : 0}%` }} />)}
      </div>
      <ul className="nxpr-legend">
        {parts.map(([label, v, k]) => <li key={k} data-k={k}>{label}<b>{inr(v)}</b></li>)}
        <li>Planned material<b>{inr(c.planned_material)}</b></li>
        {c.unit_cost ? <li>Cost per unit<b>{inr(c.unit_cost, 2)}</b></li> : null}
      </ul>
    </section>
  );
}

function AddCost({ job, act, busy }: { job: Job; act: (b: Record<string, unknown>) => Promise<unknown>; busy: boolean }) {
  const [mode, setMode] = useState<"labour" | "expense">("labour");
  const [form, setForm] = useState({ worker: "", hours: "", rate: "", amount: "", kind: "machine", note: "" });
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm((x) => ({ ...x, [k]: e.target.value }));
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    await act(mode === "labour"
      ? { action: "labour", worker: form.worker, hours: form.hours, rate: form.rate, amount: form.amount, note: form.note }
      : { action: "expense", kind: form.kind, amount: form.amount, note: form.note });
    setForm((x) => ({ ...x, hours: "", amount: "", note: "" }));
  };
  const computed = Number(form.hours) * Number(form.rate);
  return (
    <form className="nxpr-addcost" onSubmit={(e) => void submit(e)}>
      <div className="nxpr-seg" role="group" aria-label="Cost type">
        <button type="button" aria-pressed={mode === "labour"} onClick={() => setMode("labour")}><Users size={14} />Labour</button>
        <button type="button" aria-pressed={mode === "expense"} onClick={() => setMode("expense")}><Truck size={14} />Other cost</button>
      </div>
      {mode === "labour" ? (
        <div className="nxpr-grid">
          <Field label="Worker"><input className="nx-input" value={form.worker} onChange={set("worker")} list="nxpr-workers" required /></Field>
          <Field label="Hours"><input className="nx-input" inputMode="decimal" value={form.hours} onChange={set("hours")} /></Field>
          <Field label="Rate / hour"><input className="nx-input" inputMode="decimal" value={form.rate} onChange={set("rate")} /></Field>
          <Field label="Amount" hint={computed ? `${inr(computed)} from hours × rate` : "Or enter a fixed amount"}><input className="nx-input" inputMode="decimal" value={form.amount} onChange={set("amount")} /></Field>
          <datalist id="nxpr-workers">{job.assignees.map((a) => <option key={a} value={a} />)}</datalist>
        </div>
      ) : (
        <div className="nxpr-grid">
          <Field label="Type"><select className="nx-input" value={form.kind} onChange={set("kind")}>{Object.entries(job.expense_kinds).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></Field>
          <Field label="Amount"><input className="nx-input" inputMode="decimal" value={form.amount} onChange={set("amount")} required /></Field>
        </div>
      )}
      <Field label="Note" wide><input className="nx-input" value={form.note} onChange={set("note")} placeholder={mode === "labour" ? "e.g. welding frame" : "e.g. powder coating outsourced"} /></Field>
      <button type="submit" className="nx-button" disabled={busy}><Plus size={15} />Add {mode === "labour" ? "labour" : "cost"}</button>
    </form>
  );
}

function InvoiceSheet({ job, onClose }: { job: Job; onClose: () => void }) {
  const invoice = useInvoiceJob();
  const [price, setPrice] = useState(() => (Number(job.quoted) && Number(job.quantity) ? (Number(job.quoted) / Number(job.quantity)).toFixed(2) : ""));
  const [tax, setTax] = useState("18");
  const [when, setWhen] = useState(today());
  const [done, setDone] = useState<{ id: string; invoice_number: string } | null>(null);
  const total = Number(price) * Number(job.quantity) * (1 + Number(tax) / 100);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      setDone(await invoice.mutateAsync({ job, unit_price: price, tax_rate: tax, invoice_date: when }));
    } catch { /* toast shown by the API client */ }
  };
  return (
    <Sheet title={done ? "Invoice created" : `Invoice ${job.number}`} sub={job.customer?.name} onClose={onClose}
      footer={done ? <Link className="nx-button" href="/invoices">Open invoices<ChevronRight size={16} /></Link> : <button type="submit" form="nxpr-inv" className="nx-button" disabled={invoice.isPending || !price}>{invoice.isPending ? "Creating…" : "Create draft invoice"}</button>}>
      {done ? (
        <div className="nxpr-done"><PackageCheck size={34} /><p>Draft invoice <b>{done.invoice_number}</b> is ready. Review it and issue it from Invoices.</p>
          {job.made_to_order ? <p className="nxpr-fine">No raw materials were taken out again. This job already used them.</p> : null}</div>
      ) : (
        <form id="nxpr-inv" className="nxpr-form" onSubmit={(e) => void submit(e)}>
          <div className="nxpr-inv-line"><strong>{job.product?.name}</strong><span>{qty(job.quantity)} {job.unit}</span></div>
          <div className="nxpr-grid">
            <Field label="Price per unit"><input className="nx-input" inputMode="decimal" value={price} onChange={(e) => setPrice(e.target.value)} required /></Field>
            <Field label="GST %"><select className="nx-input" value={tax} onChange={(e) => setTax(e.target.value)}>{["0", "5", "12", "18", "28"].map((r) => <option key={r}>{r}</option>)}</select></Field>
            <Field label="Invoice date"><input className="nx-input" type="date" value={when} onChange={(e) => setWhen(e.target.value)} required /></Field>
          </div>
          <p className="nxpr-total">Total with GST <b>{inr(total, 2)}</b></p>
          <p className="nxpr-fine">{job.made_to_order ? "Made to order: the invoice won't touch stock. The job's material is already accounted for." : "The finished item is taken out of stock when you issue the invoice."}</p>
        </form>
      )}
    </Sheet>
  );
}

function JobSheet({ id, onClose }: { id: string; onClose: () => void }) {
  const job = useJob(id);
  const action = useJobAction(id);
  const perms = usePerms();
  const [note, setNote] = useState("");
  const [invoicing, setInvoicing] = useState(false);
  const [editing, setEditing] = useState(false);
  const j = job.data;
  const act = async (body: Record<string, unknown>) => {
    if (!j) return;
    try {
      await action.mutateAsync({ ...body, revision: j.revision });
      return true;
    } catch { return false; }
  };
  const busy = action.isPending;
  const open = j && (j.status === "open" || j.status === "on_hold");

  const head = j ? (
    <span className="nxpr-head-title"><small>{j.number}</small>{j.title}</span>
  ) : "Job";

  return (
    <Sheet wide title={head} sub={j ? <span className="nxpr-head-sub"><Badge tone={STATUS_TONE[j.status]}>{STATUS_LABEL[j.status]}</Badge><Priority value={j.priority} /><span>{dueText(j)}</span></span> : undefined} onClose={onClose}
      footer={j && perms.manage ? (
        <div className="nxpr-foot-actions">
          {open ? (
            <>
              {j.status === "on_hold"
                ? <button type="button" className="nxpr-ghost" disabled={busy} onClick={() => void act({ action: "resume" })}><PlayCircle size={16} />Resume</button>
                : <button type="button" className="nxpr-ghost" disabled={busy} onClick={() => { const reason = window.prompt("Why is this job on hold? (optional)") ?? ""; void act({ action: "hold", reason }); }}><PauseCircle size={16} />Hold</button>}
              <button type="button" className="nxpr-ghost" onClick={() => setEditing(true)}><FileText size={16} />Edit</button>
              <button type="button" className="nx-button" disabled={busy} onClick={() => { if (window.confirm(j.made_to_order ? "Complete this job? Its cost goes to the sale. It won't be added to stock (made to order)." : `Complete this job and add ${qty(j.quantity)} ${j.unit} to ${j.warehouse.name}?`)) void act({ action: "complete" }); }}><Check size={16} />Complete job</button>
            </>
          ) : null}
          {j.status === "completed" ? <button type="button" className="nxpr-ghost" disabled={busy} onClick={() => void act({ action: "deliver" })}><Truck size={16} />Mark delivered</button> : null}
          {!j.invoice && j.status !== "cancelled" && j.product && j.customer && perms.invoice && (j.made_to_order || !open)
            ? <button type="button" className="nx-button" onClick={() => setInvoicing(true)}><ReceiptIndianRupee size={16} />Create invoice</button> : null}
          {open && !j.invoice ? <button type="button" className="nxpr-ghost nxpr-danger" disabled={busy} onClick={() => { if (window.confirm("Cancel this job?")) void act({ action: "cancel" }); }}><XCircle size={16} />Cancel job</button> : null}
        </div>
      ) : undefined}>
      {job.isPending ? <div className="nxpr-skeleton"><i /><i /><i /></div> : job.error || !j ? (
        <div className="nxpr-error" role="alert">{errorText(job.error)}<button type="button" onClick={() => void job.refetch()}><RefreshCw size={14} />Try again</button></div>
      ) : (
        <div className="nxpr-detail">
          <ol className="nxpr-stepper" aria-label="Stages">
            {j.stages.map((st, i) => {
              const state = j.status === "completed" || j.status === "delivered" || i < j.stage_index ? "done" : i === j.stage_index ? "now" : "todo";
              return (
                <li key={st.key} data-state={state}>
                  <button type="button" disabled={!open || !perms.manage || busy || st.key === j.stage} onClick={() => void act({ action: "stage", stage: st.key })} aria-current={state === "now" ? "step" : undefined}>
                    <i>{state === "done" ? <Check size={12} /> : i + 1}</i><span>{st.label}</span>
                  </button>
                </li>
              );
            })}
          </ol>

          <div className="nxpr-detail-grid">
            <div className="nxpr-stack">
              <section className="nxpr-box nxpr-facts">
                <dl>
                  <div><dt>Customer</dt><dd>{j.customer ? <>{j.customer.name}{j.customer.phone ? <span className="nxpr-contact"><a href={`tel:${j.customer.phone}`} aria-label="Call"><Phone size={14} /></a><a href={`https://wa.me/91${j.customer.phone.replace(/\D/g, "").slice(-10)}`} target="_blank" rel="noreferrer" aria-label="WhatsApp"><MessageCircle size={14} /></a></span> : null}</> : "Not set"}</dd></div>
                  <div><dt>Making</dt><dd>{j.product ? `${j.product.name} × ${qty(j.quantity)} ${j.unit}` : `${j.title} × ${qty(j.quantity)}`}{j.made_to_order ? <Badge tone="violet">Made to order</Badge> : null}</dd></div>
                  <div><dt>Due</dt><dd>{j.due ? new Date(j.due).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short", year: "numeric" }) : "No due date"}</dd></div>
                  <div><dt>Team</dt><dd>{j.assignees.length ? j.assignees.join(", ") : "Not assigned"}</dd></div>
                  <div><dt>Material from</dt><dd>{j.warehouse.name}</dd></div>
                  {j.sales_order ? <div><dt>Sales order</dt><dd>{j.sales_order.number}</dd></div> : null}
                  {j.invoice ? <div><dt>Invoice</dt><dd><Link className="nxpr-link" href="/invoices">{j.invoice.number} · {inr(j.invoice.total)}</Link></dd></div> : null}
                </dl>
                {j.specification ? <div className="nxpr-spec"><h4>Specification</h4><p>{j.specification}</p></div> : null}
              </section>

              <section className="nxpr-box">
                <div className="nxpr-box-head"><h3>Material</h3><span className="nxpr-fine">From {j.warehouse.name}</span></div>
                {j.materials.length ? j.materials.map((m) => <MaterialRow key={m.product} m={m} job={j} act={act} busy={busy} canStock={perms.stock && perms.manage} />)
                  : <p className="nxpr-fine">No material planned. Issue material below, or set up a recipe for the item so the plan fills in by itself.</p>}
                {open && perms.manage && perms.stock ? <IssueOther act={act} busy={busy} /> : null}
              </section>

              <section className="nxpr-box">
                <div className="nxpr-box-head"><h3>Labour and other costs</h3></div>
                {[...j.labour.map((x) => ({ ...x, kind: "labour" as const, title: x.worker, sub: Number(x.hours) ? `${qty(x.hours)} h × ${inr(x.rate)}` : "Fixed amount" })),
                  ...j.expenses.map((x) => ({ ...x, kind: "expenses" as const, title: x.label, sub: "" }))]
                  .sort((a, b) => b.date.localeCompare(a.date))
                  .map((x) => (
                    <div key={x.id} className="nxpr-entry">
                      <span className="nxpr-entry-ico" data-k={x.kind}>{x.kind === "labour" ? <Users size={14} /> : <Truck size={14} />}</span>
                      <span className="min-w-0 flex-1"><strong>{x.title}</strong><small>{[new Date(x.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" }), x.sub, x.note].filter(Boolean).join(" · ")}</small></span>
                      <b className="nxpr-num">{inr(x.amount)}</b>
                      {open && perms.manage ? <button type="button" className="nxpr-icon" aria-label="Remove entry" disabled={busy} onClick={() => void act({ action: "remove_entry", kind: x.kind, id: x.id })}><Trash2 size={14} /></button> : null}
                    </div>
                  ))}
                {!j.labour.length && !j.expenses.length ? <p className="nxpr-fine">No labour or costs yet.</p> : null}
                {open && perms.manage ? <AddCost job={j} act={act} busy={busy} /> : null}
              </section>
            </div>

            <div className="nxpr-stack">
              <CostBox job={j} />
              <section className="nxpr-box">
                <h3>Activity</h3>
                {perms.manage ? (
                  <form className="nxpr-note" onSubmit={(e) => { e.preventDefault(); if (note.trim()) void act({ action: "note", text: note }).then((ok) => ok && setNote("")); }}>
                    <input className="nx-input" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Add a note for the team" aria-label="Note" />
                    <button type="submit" className="nxpr-ghost" disabled={busy || !note.trim()}>Add</button>
                  </form>
                ) : null}
                <ol className="nxpr-timeline">
                  {j.events.map((e, i) => (
                    <li key={i} data-k={e.kind}><i /><div><p>{e.text}</p><small>{new Date(e.at).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" })}{e.by ? ` · ${e.by}` : ""}</small></div></li>
                  ))}
                </ol>
              </section>
            </div>
          </div>
        </div>
      )}
      {invoicing && j ? <InvoiceSheet job={j} onClose={() => setInvoicing(false)} /> : null}
      {editing && j ? <JobForm job={j} onClose={() => setEditing(false)} onSaved={() => setEditing(false)} /> : null}
    </Sheet>
  );
}

function IssueOther({ act, busy }: { act: (b: Record<string, unknown>) => Promise<unknown>; busy: boolean }) {
  const [product, setProduct] = useState("");
  const [amount, setAmount] = useState("");
  return (
    <div className="nxpr-issue-other">
      <span className="nxpr-fine">Issue other material</span>
      <div className="nxpr-row">
        <div className="min-w-0 flex-1"><SearchSelect name="product_id" aria-label="Material" value={product} onChange={(e) => setProduct(e.target.value)}><option value="">Select…</option></SearchSelect></div>
        <input className="nx-input nxpr-qty" inputMode="decimal" aria-label="Quantity" placeholder="Qty" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <button type="button" className="nx-button" disabled={busy || !product || !amount} onClick={() => void act({ action: "issue", product, quantity: amount }).then(() => { setAmount(""); })}>Issue</button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------
// New / edit job
// ---------------------------------------------------------------------------------------------

function JobForm({ job, onClose, onSaved }: { job?: Job; onClose: () => void; onSaved: (id: string) => void }) {
  const create = useCreateJob();
  const update = useJobAction(job?.id ?? null);
  const warehouses = useWarehouses(true);
  const [f, setF] = useState(() => ({
    product_id: job?.product?.id ?? "", title: job?.title ?? "", quantity: job?.quantity ?? "1", customer_id: job?.customer?.id ?? "", due: job?.due ?? "",
    priority: job?.priority ?? "normal", assignees: job?.assignees.join(", ") ?? "", quoted: job?.quoted ?? "", warehouse_id: job?.warehouse.id ?? "", specification: job?.specification ?? "",
  }));
  const recipe = useRecipe(f.product_id || null);
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF((x) => ({ ...x, [k]: e.target.value }));
  const r = recipe.data;
  const suggested = r && Number(r.selling_price) ? (Number(r.selling_price) * Number(f.quantity || 0)).toFixed(2) : "";
  const busy = create.isPending || update.isPending;
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const body: Record<string, unknown> = { ...f, quoted: f.quoted || suggested || "0" };
    if (!f.warehouse_id) delete body.warehouse_id;
    try {
      if (job) {
        delete body.product_id;
        const saved = await update.mutateAsync({ action: "update", revision: job.revision, ...body });
        onSaved(saved.id);
      } else {
        const saved = await create.mutateAsync(body);
        onSaved(saved.id);
      }
    } catch { /* toast shown by the API client */ }
  };
  return (
    <Sheet title={job ? `Edit ${job.number}` : "New job"} sub={job ? undefined : "One job card for each order you make"} onClose={onClose}
      footer={<button type="submit" form="nxpr-job" className="nx-button" disabled={busy}>{busy ? "Saving…" : job ? "Save changes" : "Open job"}</button>}>
      <form id="nxpr-job" className="nxpr-form" onSubmit={(e) => void submit(e)}>
        <div className="nxpr-grid">
          {!job ? (
            <Field label="Item to make" hint="Pick the item you'll invoice. Leave empty for a one-off job and add the item later." wide>
              <SearchSelect name="product_id" aria-label="Item to make" value={f.product_id} onChange={set("product_id")}><option value="">No item yet</option></SearchSelect>
            </Field>
          ) : null}
          <Field label="Job name" hint={f.product_id ? "Optional. Uses the item name if empty." : undefined} wide><input className="nx-input" value={f.title} onChange={set("title")} placeholder="e.g. Almirah for Patil Builders, 6 ft" required={!f.product_id} /></Field>
          <Field label="Quantity"><input className="nx-input" inputMode="decimal" value={f.quantity} onChange={set("quantity")} required /></Field>
          <Field label="Due date"><input className="nx-input" type="date" value={f.due ?? ""} onChange={set("due")} /></Field>
          <Field label="Customer" wide>
            <SearchSelect name="customer_id" aria-label="Customer" value={f.customer_id} onChange={set("customer_id")}><option value="">{job?.customer?.name ?? "No customer"}</option>{job?.customer ? <option value={job.customer.id}>{job.customer.name}</option> : null}</SearchSelect>
          </Field>
          <Field label="Priority">
            <select className="nx-input" value={f.priority} onChange={set("priority")}>{(["low", "normal", "high", "urgent"] as Priority[]).map((p) => <option key={p} value={p}>{PRIORITY_LABEL[p]}</option>)}</select>
          </Field>
          <Field label="Quoted price (total)" hint={suggested && !f.quoted ? `${inr(suggested)} from the item's selling price` : undefined}><input className="nx-input" inputMode="decimal" value={f.quoted} onChange={set("quoted")} placeholder={suggested || "0"} /></Field>
          <Field label="Team" hint="Names separated by commas" wide><input className="nx-input" value={f.assignees} onChange={set("assignees")} placeholder="Raju, Imran" /></Field>
          <Field label="Take material from" wide>
            <select className="nx-input" value={f.warehouse_id} onChange={set("warehouse_id")}><option value="">{job?.warehouse.name ?? "Main warehouse"}</option>{(warehouses.data ?? []).map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}</select>
          </Field>
          <Field label="Specification" hint="Size, colour, finish, design notes" wide><textarea className="nx-input" rows={3} value={f.specification} onChange={set("specification")} /></Field>
        </div>
        {!job && f.product_id && r ? (
          <div className="nxpr-recipe-preview">
            {r.materials.length ? (
              <>
                <h4>{r.made_to_order ? "Made to order. " : ""}Material plan for {qty(f.quantity || 0)} {r.unit}</h4>
                <ul>{r.materials.map((m) => <li key={m.product}><span>{m.name}</span><b>{qty(Number(m.per_unit) * Number(f.quantity || 0))} {m.unit}</b></li>)}</ul>
                <p className="nxpr-fine">Estimated cost {inr(Number(r.unit_cost) * Number(f.quantity || 0))}. You can issue more or different material later.</p>
              </>
            ) : <p className="nxpr-fine">This item has no recipe yet. Add one under Recipes so the material plan fills in by itself. You can still issue material by hand.</p>}
          </div>
        ) : null}
      </form>
    </Sheet>
  );
}

// ---------------------------------------------------------------------------------------------
// Recipes
// ---------------------------------------------------------------------------------------------

function RecipeForm({ product, onClose }: { product: string | null; onClose: () => void }) {
  const [item, setItem] = useState(product ?? "");
  const current = useRecipe(item || null);
  const save = useSaveRecipe();
  const remove = useDeleteRecipe();
  const [mto, setMto] = useState(true);
  const [lines, setLines] = useState<{ product: string; per_unit: string; label?: string }[]>([{ product: "", per_unit: "" }]);
  const [labour, setLabour] = useState("0");
  const [notes, setNotes] = useState("");
  const [loadedFor, setLoadedFor] = useState("");
  const c = current.data;
  if (c && loadedFor !== c.product) {
    setLoadedFor(c.product);
    setMto(c.materials.length ? c.made_to_order : true);
    setLines(c.materials.length ? c.materials.map((m) => ({ product: m.product, per_unit: m.per_unit, label: m.name })) : [{ product: "", per_unit: "" }]);
    setLabour(c.labour_per_unit);
    setNotes(c.notes);
  }
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await save.mutateAsync({ product: item, made_to_order: mto, materials: lines.filter((l) => l.product).map(({ product: p, per_unit }) => ({ product: p, per_unit })), labour_per_unit: labour || "0", notes });
      onClose();
    } catch { /* toast shown */ }
  };
  return (
    <Sheet title={product ? `Recipe: ${c?.name ?? ""}` : "New recipe"} sub="Raw materials used to make one unit" onClose={onClose}
      footer={<>
        {product && c?.updated_at ? <button type="button" className="nxpr-ghost nxpr-danger" disabled={remove.isPending} onClick={() => { if (window.confirm("Remove this recipe? Past invoices keep the recipe they used.")) void remove.mutateAsync(item).then(onClose); }}><Trash2 size={15} />Remove</button> : null}
        <button type="submit" form="nxpr-recipe" className="nx-button" disabled={save.isPending || !item}>{save.isPending ? "Saving…" : "Save recipe"}</button>
      </>}>
      <form id="nxpr-recipe" className="nxpr-form" onSubmit={(e) => void submit(e)}>
        {!product ? (
          <Field label="Item" hint="The finished item you sell, e.g. Steel almirah 6 ft" wide>
            <SearchSelect name="product_id" aria-label="Finished item" value={item} onChange={(e) => setItem(e.target.value)}><option value="">Select…</option></SearchSelect>
          </Field>
        ) : null}
        <label className="nxpr-toggle">
          <input type="checkbox" checked={mto} onChange={(e) => setMto(e.target.checked)} />
          <span><strong>Made to order</strong><em>Never kept in stock. Selling it, by sales order or invoice, uses up these raw materials instead of finished stock. Use this for custom items like a made-to-measure almirah.</em></span>
        </label>
        <div className="nxpr-lines">
          <div className="nxpr-lines-head"><span>Raw material</span><span>Per unit</span><span /></div>
          {lines.map((l, i) => (
            <div key={i} className="nxpr-line">
              <SearchSelect name="product_id" aria-label={`Raw material ${i + 1}`} value={l.product} onChange={(e) => setLines((x) => x.map((y, k) => (k === i ? { ...y, product: e.target.value } : y)))}>
                <option value="">Select…</option>{l.label ? <option value={l.product}>{l.label}</option> : null}
              </SearchSelect>
              <input className="nx-input" inputMode="decimal" aria-label={`Quantity per unit ${i + 1}`} value={l.per_unit} onChange={(e) => setLines((x) => x.map((y, k) => (k === i ? { ...y, per_unit: e.target.value } : y)))} placeholder="0" />
              <button type="button" className="nxpr-icon" aria-label="Remove line" onClick={() => setLines((x) => (x.length > 1 ? x.filter((_, k) => k !== i) : [{ product: "", per_unit: "" }]))}><Trash2 size={14} /></button>
            </div>
          ))}
          <button type="button" className="nxpr-link" onClick={() => setLines((x) => [...x, { product: "", per_unit: "" }])}><Plus size={14} />Add raw material</button>
        </div>
        <div className="nxpr-grid">
          <Field label="Labour per unit (estimate)"><input className="nx-input" inputMode="decimal" value={labour} onChange={(e) => setLabour(e.target.value)} /></Field>
          <Field label="Notes" wide><input className="nx-input" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="e.g. sizes up to 6 ft" /></Field>
        </div>
        {c && c.materials.length ? <p className="nxpr-fine">Material cost per unit {inr(c.material_cost, 2)} · with labour {inr(c.unit_cost, 2)}{c.can_make !== null ? ` · enough stock for ${c.can_make}` : ""}</p> : null}
      </form>
    </Sheet>
  );
}

function RecipesPanel() {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState<string | null | undefined>(undefined);
  const recipes = useRecipes(search);
  const perms = usePerms();
  const rows = recipes.data?.rows ?? [];
  return (
    <div className="nxpr-stack">
      <section className="nxpr-explain">
        <Hammer size={22} />
        <div>
          <h3>Sell custom items without stocking them</h3>
          <p>Give an item a recipe: the raw materials that go into one unit. Mark it <b>made to order</b> and NexEase never asks for finished stock. Sales orders go through, and invoices use up the raw materials. Jobs plan material from the recipe too.</p>
        </div>
      </section>
      <div className="nxpr-toolbar">
        <label className="nxpr-search"><Search size={16} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search items with recipes" aria-label="Search recipes" /></label>
        {perms.manage ? <button type="button" className="nx-button" onClick={() => setOpen(null)}><Plus size={16} />New recipe</button> : null}
      </div>
      {recipes.isPending ? <div className="nxpr-skeleton"><i /><i /></div> : !rows.length ? (
        <div className="nxpr-empty"><ListChecks size={30} /><h3>No recipes yet</h3><p>Start with the item that gave you trouble, like an almirah you make to order. Add its raw materials once and selling it works from then on.</p>
          {perms.manage ? <button type="button" className="nx-button" onClick={() => setOpen(null)}><Plus size={16} />New recipe</button> : null}</div>
      ) : (
        <div className="nxpr-recipes">
          {rows.map((r: Recipe) => (
            <button key={r.product} type="button" className="nxpr-recipe" onClick={() => perms.manage && setOpen(r.product)} disabled={!perms.manage}>
              <span className="nxpr-recipe-top"><strong>{r.name}</strong>{r.made_to_order ? <Badge tone="violet">Made to order</Badge> : <Badge>Kept in stock</Badge>}</span>
              <span className="nxpr-fine">{r.sku}</span>
              <ul>{r.materials.slice(0, 4).map((m) => <li key={m.product}><span>{m.name}</span><b>{qty(m.per_unit)} {m.unit}</b></li>)}{r.materials.length > 4 ? <li><span>+{r.materials.length - 4} more</span></li> : null}</ul>
              <span className="nxpr-recipe-foot">
                <span><small>Cost / unit</small><b>{inr(r.unit_cost)}</b></span>
                <span><small>Sells at</small><b>{inr(r.selling_price)}</b></span>
                <span data-low={r.can_make === 0 || undefined}><small>Can make now</small><b>{r.can_make ?? "—"}</b></span>
              </span>
            </button>
          ))}
        </div>
      )}
      {open !== undefined ? <RecipeForm product={open} onClose={() => setOpen(undefined)} /> : null}
    </div>
  );
}

// ---------------------------------------------------------------------------------------------
// Stages
// ---------------------------------------------------------------------------------------------

function StagesSheet({ onClose }: { onClose: () => void }) {
  const settings = useStageSettings();
  const save = useSaveStages();
  const [rows, setRows] = useState<Stage[] | null>(null);
  const list = rows ?? settings.data?.stages ?? [];
  const move = (i: number, d: number) => setRows(() => { const x = [...list]; const [it] = x.splice(i, 1); x.splice(i + d, 0, it); return x; });
  return (
    <Sheet title="Production stages" sub="The steps every job goes through in your workshop" onClose={onClose}
      footer={<button type="button" className="nx-button" disabled={save.isPending || !rows} onClick={() => void save.mutateAsync(list.filter((s) => s.label.trim())).then(() => onClose()).catch(() => undefined)}>Save stages</button>}>
      <div className="nxpr-stages">
        {list.map((s, i) => (
          <div key={s.key || i} className="nxpr-stage-row">
            <b>{i + 1}</b>
            <input className="nx-input" value={s.label} aria-label={`Stage ${i + 1}`} onChange={(e) => setRows(list.map((x, k) => (k === i ? { ...x, label: e.target.value } : x)))} />
            <button type="button" className="nxpr-icon" aria-label="Move up" disabled={!i} onClick={() => move(i, -1)}>↑</button>
            <button type="button" className="nxpr-icon" aria-label="Move down" disabled={i === list.length - 1} onClick={() => move(i, 1)}>↓</button>
            <button type="button" className="nxpr-icon" aria-label="Remove stage" disabled={list.length <= 2} onClick={() => setRows(list.filter((_, k) => k !== i))}><Trash2 size={14} /></button>
          </div>
        ))}
        <button type="button" className="nxpr-link" disabled={list.length >= 15} onClick={() => setRows([...list, { key: "", label: "" }])}><Plus size={14} />Add stage</button>
        <p className="nxpr-fine">Furniture example: Design, Cutting, Assembly, Polish, Quality check, Ready. Fabrication: Cutting, Welding, Grinding, Painting, Packing.</p>
      </div>
    </Sheet>
  );
}

// ---------------------------------------------------------------------------------------------
// Hub
// ---------------------------------------------------------------------------------------------

function Hub() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const perms = usePerms();
  const tab = (TABS.some((t) => t.key === params.get("tab")) ? params.get("tab") : "jobs") as Tab;
  const jobId = params.get("job");
  const [creating, setCreating] = useState(() => params.get("new") === "1");
  const setParam = (key: string, value: string | null) => {
    const p = new URLSearchParams(params.toString());
    if (value) p.set(key, value); else p.delete(key);
    router.replace(`${pathname}${p.toString() ? `?${p}` : ""}`, { scroll: false });
  };
  useEffect(() => {
    if (params.get("sales_order")) router.replace(`/manufacturing/batches?${params.toString()}`);
    if (params.get("new") === "1") setParam("new", null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="nxl-screen nxpr">
      <header className="nxl-header">
        <div className="min-w-0">
          <h1>Manufacturing</h1>
          <p className="nx-muted">Job cards, material, labour and cost for everything you make</p>
        </div>
        {perms.manage && tab === "jobs" ? <button type="button" className="nx-button nxl-primary" onClick={() => setCreating(true)}><Plus size={17} />New job</button> : null}
      </header>
      <nav className="nxpr-tabs" role="tablist" aria-label="Production sections">
        {TABS.map((t) => t.key === "batches"
          ? <Link key={t.key} href="/manufacturing/batches" role="tab" aria-selected={false}><t.icon size={16} />{t.label}</Link>
          : <button key={t.key} type="button" role="tab" aria-selected={tab === t.key} onClick={() => setParam("tab", t.key === "jobs" ? null : t.key)}><t.icon size={16} />{t.label}</button>)}
      </nav>
      {tab === "jobs" ? <JobsPanel onOpen={(id) => setParam("job", id)} onNew={() => setCreating(true)} /> : null}
      {tab === "recipes" ? <RecipesPanel /> : null}
      {jobId ? <JobSheet id={jobId} onClose={() => setParam("job", null)} /> : null}
      {creating ? <JobForm onClose={() => setCreating(false)} onSaved={(id) => { setCreating(false); setParam("job", id); }} /> : null}
    </div>
  );
}

export default function ProductionHub() {
  return <Suspense fallback={<div className="nxpr-skeleton"><i /><i /></div>}><Hub /></Suspense>;
}

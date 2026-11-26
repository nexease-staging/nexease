"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Eye, FileText, Loader2, Palette, QrCode, Save, Stamp, X } from "lucide-react";
import { apiBinaryRequest, apiRequest } from "@/lib/api/client";

type Settings = Record<string, string>;
type Template = { id: string; name: string; color: string; layout: string; description: string };

const KINDS = [
  { id: "invoice", label: "Tax invoice" },
  { id: "quotation", label: "Estimate / quotation" },
  { id: "sales_order", label: "Proforma / sales order" },
  { id: "credit_note", label: "Credit note" },
  { id: "delivery_challan", label: "Delivery challan" },
];
const SWATCHES = ["#1f2937", "#0f766e", "#006b58", "#1d4ed8", "#6d28d9", "#b45309", "#be123c"];
const UPI = /^[A-Za-z0-9._-]{2,64}@[A-Za-z][A-Za-z0-9.-]{1,64}$/;

/** A small drawing of each layout so formats can be told apart at a glance. */
function Thumb({ t, accent }: { t: Template; accent: string }) {
  const band = t.layout === "modern";
  const boxed = t.layout === "gst_classic" || t.layout === "retail";
  const thermal = t.layout === "thermal";
  return (
    <div className="nxt-thumb" data-layout={t.layout} aria-hidden>
      <div className="nxt-sheet" style={thermal ? { width: "46%" } : undefined}>
        <div className="nxt-top" style={band ? { background: accent } : { borderBottom: `2px solid ${t.layout === "minimal" ? "#111827" : accent}` }}>
          <i style={{ background: band ? "#fff" : accent, width: thermal ? "70%" : "45%" }} />
          {!thermal ? <b style={{ background: band ? "#ffffffaa" : "#11182766" }} /> : null}
        </div>
        <div className="nxt-parties"><i /><i /><i /></div>
        <div className="nxt-rows" data-boxed={boxed || undefined}>
          <span style={{ background: boxed || band ? (t.layout === "gst_classic" ? "#111827" : accent) : "transparent", borderBottom: boxed || band ? undefined : `1.5px solid ${accent}` }} />
          {[0, 1, 2].map((i) => <span key={i} style={band && i % 2 ? { background: "#f1f5f9" } : undefined} />)}
        </div>
        <div className="nxt-foot"><i /><em style={{ background: accent }} /></div>
      </div>
    </div>
  );
}

export default function InvoiceFormats() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["invoice-settings"], queryFn: async () => (await apiRequest<{ settings: Settings; templates: Template[] }>("/business/invoice-settings/")).data });
  const [draft, setDraft] = useState<Settings | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<{ template: string; kind: string } | null>(null);
  const d: Settings = draft ?? q.data?.settings ?? { template: "gst_classic" };
  const templates = q.data?.templates ?? [];
  const current = templates.find((t) => t.id === d.template) ?? templates[0];
  const accent = d.accent_color || current?.color || "#1f2937";
  const dirty = draft !== null;
  const upiError = d.upi_id && !UPI.test(d.upi_id.trim()) ? "Enter a UPI ID like business@okhdfcbank." : "";

  const set = (patch: Settings) => setDraft({ ...d, ...patch });

  async function save() {
    if (upiError) return;
    setBusy(true);
    setError("");
    try {
      const allowed = ["template", "logo", "accent_color", "bank_details", "payment_terms", "terms", "signatory", "payslip_template", "document_style", "upi_id"];
      await apiRequest("/business/invoice-settings/", { method: "POST", body: Object.fromEntries(Object.entries(d).filter(([k, v]) => allowed.includes(k) && typeof v === "string")) });
      await qc.invalidateQueries({ queryKey: ["invoice-settings"] });
      await qc.invalidateQueries({ queryKey: ["business-config"] });
      setDraft(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="nxt">
      <header className="nxl-header">
        <div className="min-w-0">
          <h1>Invoice formats</h1>
          <p className="nx-muted">Pick one design. It is used for every tax invoice, bill of supply, estimate, proforma, credit note and delivery challan — new and old.</p>
        </div>
        <button type="button" className="nx-button nxr-keep" disabled={busy || !dirty || !!upiError} onClick={() => void save()}>{busy ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}{busy ? "Saving…" : dirty ? "Save changes" : "Saved"}</button>
      </header>
      {q.error ? <p className="nxf-error" role="alert">{(q.error as Error).message}</p> : null}
      {error ? <p className="nxf-error" role="alert">{error}</p> : null}

      <section className="nxt-gallery" aria-label="Templates">
        {templates.map((t) => {
          const chosen = d.template === t.id;
          return (
            <article key={t.id} className="nxt-card" data-chosen={chosen || undefined}>
              <button type="button" className="nxt-pick" aria-pressed={chosen} aria-label={`Use ${t.name}`} onClick={() => set({ template: t.id })}>
                <Thumb t={t} accent={d.accent_color || t.color} />
                <span className="nxt-name">{chosen ? <Check size={15} /> : null}{t.name}</span>
                <span className="nxt-desc">{t.description}</span>
              </button>
              <button type="button" className="nxt-preview" onClick={() => setPreview({ template: t.id, kind: "invoice" })}><Eye size={15} />Preview</button>
            </article>
          );
        })}
      </section>

      <div className="nxt-grid">
        <section className="nxt-panel">
          <h2><Palette size={17} />Look</h2>
          <div className="nxt-swatches" role="radiogroup" aria-label="Accent colour">
            {SWATCHES.map((c) => <button key={c} type="button" role="radio" aria-checked={accent.toLowerCase() === c} aria-label={`Colour ${c}`} style={{ background: c }} onClick={() => set({ accent_color: c })} />)}
            <label className="nxt-custom">Custom<input type="color" aria-label="Custom accent colour" value={accent} onChange={(e) => set({ accent_color: e.target.value })} /></label>
            {d.accent_color ? <button type="button" className="nxt-link" onClick={() => set({ accent_color: "" })}>Use template colour</button> : null}
          </div>
          <label className="nxt-field">Business logo (PNG or JPG, up to 250 KB)
            <input type="file" accept="image/png,image/jpeg" onChange={(e) => { const f = e.target.files?.[0]; if (!f) return; if (f.size > 250000) { setError("Choose a logo below 250 KB."); return; } const r = new FileReader(); r.onload = () => set({ logo: String(r.result) }); r.readAsDataURL(f); }} />
          </label>
          {d.logo ? (
            <div className="nxt-logo">
              {/* A data URL from the user's own file; next/image adds nothing here. */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={d.logo} alt="Business logo" />
              <button type="button" className="nxt-link" onClick={() => set({ logo: "" })}>Remove logo</button>
            </div>
          ) : null}
        </section>

        <section className="nxt-panel">
          <h2><QrCode size={17} />Get paid faster</h2>
          <label className="nxt-field">UPI ID for the pay-by-QR code
            <input value={d.upi_id ?? ""} placeholder="business@okhdfcbank" aria-invalid={!!upiError || undefined} onChange={(e) => set({ upi_id: e.target.value })} />
            {upiError ? <span className="nxf-error">{upiError}</span> : <span className="nxf-hint">Invoices, estimates and proformas show a UPI QR for the amount due. Leave blank to hide it.</span>}
          </label>
          <label className="nxt-field">Bank details<textarea rows={3} maxLength={1000} value={d.bank_details ?? ""} placeholder="Bank, account number, IFSC, branch" onChange={(e) => set({ bank_details: e.target.value })} /></label>
          <label className="nxt-field">Payment terms<textarea rows={2} maxLength={1000} value={d.payment_terms ?? ""} placeholder="e.g. Payment within 15 days" onChange={(e) => set({ payment_terms: e.target.value })} /></label>
        </section>

        <section className="nxt-panel">
          <h2><Stamp size={17} />Terms & signature</h2>
          <label className="nxt-field">Terms & conditions<textarea rows={4} maxLength={2000} value={d.terms ?? ""} placeholder={"1. Goods once sold will not be taken back.\n2. Subject to local jurisdiction."} onChange={(e) => set({ terms: e.target.value })} /></label>
          <label className="nxt-field">Authorised signatory name<input maxLength={200} value={d.signatory ?? ""} placeholder="Name and designation" onChange={(e) => set({ signatory: e.target.value })} /></label>
        </section>

        <section className="nxt-panel">
          <h2><FileText size={17} />Other documents</h2>
          <label className="nxt-field">Payslip format<select value={d.payslip_template || "professional"} onChange={(e) => set({ payslip_template: e.target.value })}><option value="professional">Professional earnings / deductions</option><option value="classic">Classic component register</option></select></label>
          <label className="nxt-field">Purchase documents heading<select value={d.document_style || "classic"} onChange={(e) => set({ document_style: e.target.value })}><option value="classic">Classic</option><option value="letterhead">Formal letterhead</option><option value="minimal">Minimal divider</option></select></label>
          <p className="nxf-hint">Every format shows GSTIN, HSN/SAC, CGST/SGST or IGST, an HSN tax summary, amount in words and, for e-invoices, the IRN and QR.</p>
        </section>
      </div>

      {preview ? <Preview template={preview.template} kind={preview.kind} accent={d.accent_color} upi={UPI.test((d.upi_id ?? "").trim()) ? d.upi_id : ""} names={templates} onKind={(kind) => setPreview({ ...preview, kind })} onUse={() => { set({ template: preview.template }); setPreview(null); }} onClose={() => setPreview(null)} /> : null}
    </div>
  );
}

/** Sample document in the chosen template, rendered by the same code that prints real documents. */
function Preview({ template, kind, accent, upi, names, onKind, onUse, onClose }: { template: string; kind: string; accent?: string; upi?: string; names: Template[]; onKind: (k: string) => void; onUse: () => void; onClose: () => void }) {
  const params = new URLSearchParams({ template, kind, ...(accent ? { accent } : {}), ...(upi ? { upi } : {}) });
  const q = useQuery({ queryKey: ["template-preview", params.toString()], queryFn: async () => (await apiBinaryRequest(`/business/invoice-templates/preview/?${params}`)).blob, staleTime: 60_000 });
  const url = useMemo(() => (q.data ? URL.createObjectURL(q.data) : ""), [q.data]);
  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);
  const name = names.find((t) => t.id === template)?.name ?? template;
  return (
    <div className="nxt-modal" role="dialog" aria-modal="true" aria-label={`Preview ${name}`}>
      <div className="nxt-modal-box">
        <header>
          <strong>{name}</strong>
          <div className="nxt-kinds" role="tablist" aria-label="Document type">{KINDS.map((k) => <button key={k.id} type="button" role="tab" aria-selected={kind === k.id} onClick={() => onKind(k.id)}>{k.label}</button>)}</div>
          <button type="button" className="nx-button" onClick={onUse}><Check size={16} />Use this format</button>
          <button type="button" className="nxt-close" aria-label="Close preview" onClick={onClose}><X size={18} /></button>
        </header>
        {q.isPending ? <p className="nxt-wait"><Loader2 size={18} className="animate-spin" />Preparing sample…</p> : q.error ? <p className="nxf-error" role="alert">{(q.error as Error).message}</p> : url ? <iframe title={`${name} sample`} src={url} /> : null}
      </div>
    </div>
  );
}

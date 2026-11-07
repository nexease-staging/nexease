"use client";

/**
 * Fast invoice: one scrollable screen — customer, items, totals, save/issue, share.
 * Uses the same backend endpoint and payload as the "Quick / direct invoice" dialog
 * (POST /business/direct-invoices/), so no backend change is needed.
 */
import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Check, ChevronLeft, Eye, FilePlus2, MessageCircle, Minus, Plus, Trash2 } from "lucide-react";

import { apiRequest } from "@/lib/api/client";
import { useAuth } from "@/features/auth/auth-context";
import { hasPermission } from "@/lib/authorization/permissions";
import { useInvoice, useIssueInvoice } from "@/features/invoices/hooks";
import MasterEntry from "@/components/master-entry";
import type { Master } from "@/components/master-lookup";
import GstLookup from "@/features/business/gst-lookup";
import BarcodeScan from "@/features/business/barcode-scan";
import DocumentActions from "@/features/documents/components/document-actions";
import { InvoiceStatusBadge } from "@/components/ui/badge";
import { formatMoney } from "@/lib/format";

type Line = {
  item_type: string;
  hsn_code: string;
  sku: string;
  name: string;
  unit: string;
  quantity: string;
  unit_price: string;
  tax_rate: string;
  discount: string;
};

const GST_SLABS = ["0", "0.25", "3", "5", "12", "18", "28"];

const emptyLine = (): Line => ({
  item_type: "goods",
  hsn_code: "",
  sku: "",
  name: "",
  unit: "PCS",
  quantity: "1",
  unit_price: "0",
  tax_rate: "0",
  discount: "0",
});

function today(): string {
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

const num = (v: string): number => {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
};

function lineAmounts(l: Line) {
  const base = Math.max(0, num(l.quantity) * num(l.unit_price) - num(l.discount));
  const tax = (base * num(l.tax_rate)) / 100;
  return { base, tax, total: base + tax };
}

export function whatsappLink(phone: string, text: string): string {
  const digits = phone.replace(/\D/g, "");
  const national = digits.length === 10 ? `91${digits}` : digits.replace(/^0+/, "");
  return `https://wa.me/${national}?text=${encodeURIComponent(text)}`;
}

function fromMaster(r: Master): Partial<Line> {
  return {
    sku: r.code,
    name: r.name,
    item_type: r.item_type || "goods",
    hsn_code: r.hsn_code || "",
    unit: r.unit || "PCS",
    unit_price: r.selling_price || "0",
  };
}

export default function FastInvoice({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated?: (id: string) => void;
}) {
  const qc = useQueryClient();
  const { authentication } = useAuth();
  const canIssue = hasPermission(authentication?.role.permissions ?? [], "invoices.issue");

  const [date, setDate] = useState(today());
  const [due, setDue] = useState("");
  const [notes, setNotes] = useState("");
  const [customer, setCustomer] = useState<Record<string, string>>({});
  const [lines, setLines] = useState<Line[]>([emptyLine()]);
  const [supply, setSupply] = useState("taxable");
  const [place, setPlace] = useState("");
  const [placeEdited, setPlaceEdited] = useState(false);
  const [busy, setBusy] = useState<"" | "draft" | "issue">("");
  const [message, setMessage] = useState("");
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [result, setResult] = useState<{ id: string; warning: string } | null>(null);
  const [phone, setPhone] = useState<string | null>(null);
  const scroller = useRef<HTMLDivElement>(null);

  // Place of supply defaults to the customer's GSTIN state code, until the user edits it.
  const gstinState = /^\d{2}/.test(customer.gstin ?? "") ? (customer.gstin ?? "").slice(0, 2) : "";
  const placeOfSupply = placeEdited ? place : gstinState || place;

  const dirty = Boolean(customer.name?.trim()) || lines.some((l) => l.name.trim());

  function requestClose() {
    if (result || !dirty || window.confirm("Discard this invoice? Nothing has been saved.")) onClose();
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && !busy) requestClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  });

  const totals = useMemo(() => {
    let subtotal = 0;
    let tax = 0;
    let discount = 0;
    for (const l of lines) {
      const a = lineAmounts(l);
      subtotal += num(l.quantity) * num(l.unit_price);
      discount += num(l.discount);
      tax += a.tax;
    }
    return { subtotal, discount, tax, total: subtotal - discount + tax };
  }, [lines]);

  function patchLine(i: number, patch: Partial<Line>) {
    setLines((prev) => prev.map((l, j) => (j === i ? { ...l, ...patch } : l)));
  }

  function validate(): string {
    if (!customer.name?.trim()) return "Choose a customer or type a new customer name.";
    const filled = lines.filter((l) => l.name.trim());
    if (filled.length === 0) return "Add at least one item.";
    if (filled.some((l) => num(l.quantity) <= 0)) return "Every item needs a quantity above zero.";
    if (filled.some((l) => num(l.unit_price) < 0 || num(l.discount) < 0)) return "Rate and discount cannot be negative.";
    if (supply === "taxable" && !/^\d{2}$/.test(placeOfSupply.trim())) {
      return "Enter the 2-digit state code for place of supply, e.g. 27.";
    }
    return "";
  }

  async function save(issue: boolean) {
    const problem = validate();
    if (problem) {
      setMessage(problem);
      const container = scroller.current;
      if (container) {
        if (typeof container.scrollTo === "function") container.scrollTo({ top: 0, behavior: "smooth" });
        else container.scrollTop = 0;
      }
      return;
    }
    setBusy(issue ? "issue" : "draft");
    setMessage("");
    try {
      const created = await apiRequest<{ id: string }>("/business/direct-invoices/", {
        method: "POST",
        body: {
          invoice_date: date,
          due_date: due,
          notes,
          billing_details: { supply_type: supply, place_of_supply: placeOfSupply.trim() },
          invoice_number: "",
          customer,
          items: lines.filter((l) => l.name.trim()),
        },
      });
      const id = created.data.id;
      let warning = "";
      if (issue) {
        try {
          await apiRequest(`/invoices/${id}/issue/`, { method: "POST", body: {} });
        } catch (e) {
          warning = `Saved as a draft, but it could not be issued: ${(e as Error).message}`;
        }
      }
      await qc.invalidateQueries();
      setPhone(customer.phone?.trim() || null);
      setResult({ id, warning });
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy("");
    }
  }

  function reset() {
    setResult(null);
    setPhone(null);
    setCustomer({});
    setLines([emptyLine()]);
    setNotes("");
    setDue("");
    setPlace("");
    setPlaceEdited(false);
    setSupply("taxable");
    setMessage("");
    setDate(today());
  }

  const shell = "fixed inset-0 z-[90] flex flex-col bg-slate-50 text-slate-900";
  const shellStyle = { paddingTop: "env(safe-area-inset-top, 0px)" };

  if (result) {
    return (
      <SuccessScreen
        className={shell}
        style={shellStyle}
        invoiceId={result.id}
        warning={result.warning}
        phone={phone}
        onPhone={setPhone}
        canIssue={canIssue}
        onNew={reset}
        onView={() => {
          onCreated?.(result.id);
          onClose();
        }}
        onClose={onClose}
      />
    );
  }

  return (
    <div role="dialog" aria-modal="true" aria-label="Quick invoice" className={shell} style={shellStyle}>
      <header className="flex items-center gap-3 border-b border-slate-200 bg-white px-3 py-2">
        <button type="button" aria-label="Back" className="nx-secondary rounded-full border p-2" onClick={requestClose}>
          <ChevronLeft size={20} />
        </button>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-lg font-semibold">New invoice</h2>
          <p className="text-xs text-slate-500">Customer, items, done.</p>
        </div>
        <label className="text-xs text-slate-500">
          <span className="sr-only">Invoice date</span>
          <input
            type="date"
            aria-label="Invoice date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="nx-input !mt-0 !w-auto"
          />
        </label>
      </header>

      <div ref={scroller} className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 pb-6 pt-4">
        <div className="mx-auto max-w-3xl space-y-4">
          {message && (
            <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">
              {message}
            </p>
          )}

          <section className="nx-panel space-y-3" aria-labelledby="fi-customer">
            <h3 id="fi-customer" className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Customer
            </h3>
            <MasterEntry
              kind="customers"
              label="Customer name *"
              placeholder="Search customer or type a new name"
              required
              value={customer.name || ""}
              onChange={(name) => setCustomer(customer.id ? { name } : { ...customer, name, id: "", code: "" })}
              onSelect={(r) =>
                setCustomer({
                  id: r.id,
                  code: r.code,
                  name: r.name,
                  address: r.billing_address || "",
                  state: r.state || "",
                  gstin: r.gstin || "",
                  phone: r.phone || "",
                  email: r.email || "",
                })
              }
            />
            {(customer.gstin || customer.phone) && (
              <p className="text-xs text-slate-500">
                {[customer.gstin && `GSTIN ${customer.gstin}`, customer.phone].filter(Boolean).join(" · ")}
              </p>
            )}
            <GstLookup onSelect={(r) => setCustomer({ ...customer, id: "", code: "", ...r })} />
            <details>
              <summary className="cursor-pointer text-sm font-medium">Address &amp; contact details</summary>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                {(
                  [
                    ["address", "Billing address"],
                    ["gstin", "GSTIN"],
                    ["state", "State"],
                    ["phone", "Phone"],
                    ["email", "Email"],
                  ] as const
                ).map(([k, label]) => (
                  <label key={k} className="text-sm">
                    {label}
                    <input
                      className="nx-input"
                      type={k === "email" ? "email" : "text"}
                      value={customer[k] || ""}
                      onChange={(e) => setCustomer({ ...customer, [k]: e.target.value })}
                    />
                  </label>
                ))}
              </div>
            </details>
          </section>

          <section className="nx-panel space-y-3" aria-labelledby="fi-items">
            <h3 id="fi-items" className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Items
            </h3>
            {lines.map((line, i) => {
              const amounts = lineAmounts(line);
              const slabs = GST_SLABS.includes(line.tax_rate) ? GST_SLABS : [...GST_SLABS, line.tax_rate];
              return (
                <div key={i} className="space-y-3 rounded-xl border border-slate-200 p-3">
                  <div className="flex items-center justify-between">
                    <strong className="text-sm">Item {i + 1}</strong>
                    <button
                      type="button"
                      aria-label={`Remove line ${i + 1}`}
                      disabled={lines.length === 1}
                      className="rounded-lg p-2 text-slate-500"
                      onClick={() => setLines((prev) => prev.filter((_, j) => j !== i))}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>

                  <BarcodeScan
                    onSelect={(r) => patchLine(i, fromMaster(r))}
                    renderInput={(scan, inputRef, ready) => (
                      <MasterEntry
                        kind="products"
                        label={`name line ${i + 1}`}
                        placeholder="Search or add item"
                        required
                        value={line.name}
                        inputRef={inputRef}
                        scanMode={ready}
                        onScan={scan}
                        onChange={(name) =>
                          setLines((prev) =>
                            prev.map((l, j) =>
                              j !== i ? l : l.sku ? { ...emptyLine(), quantity: l.quantity, name } : { ...l, name },
                            ),
                          )
                        }
                        onSelect={(r) => patchLine(i, fromMaster(r))}
                      />
                    )}
                  />

                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    <div className="text-sm">
                      <span>Qty</span>
                      <div className="mt-1.5 flex items-stretch gap-1">
                        <button
                          type="button"
                          aria-label={`Decrease quantity line ${i + 1}`}
                          className="nx-secondary rounded-lg border px-2"
                          onClick={() => patchLine(i, { quantity: String(Math.max(0, num(line.quantity) - 1)) })}
                        >
                          <Minus size={14} />
                        </button>
                        <input
                          aria-label={`quantity line ${i + 1}`}
                          inputMode="decimal"
                          type="number"
                          min="0.01"
                          step="0.01"
                          className="nx-input !mt-0 min-w-0 text-center"
                          value={line.quantity}
                          onChange={(e) => patchLine(i, { quantity: e.target.value })}
                        />
                        <button
                          type="button"
                          aria-label={`Increase quantity line ${i + 1}`}
                          className="nx-secondary rounded-lg border px-2"
                          onClick={() => patchLine(i, { quantity: String(num(line.quantity) + 1) })}
                        >
                          <Plus size={14} />
                        </button>
                      </div>
                    </div>
                    <label className="text-sm">
                      Rate (₹)
                      <input
                        aria-label={`unit_price line ${i + 1}`}
                        inputMode="decimal"
                        type="number"
                        min="0"
                        step="0.01"
                        className="nx-input"
                        value={line.unit_price}
                        onChange={(e) => patchLine(i, { unit_price: e.target.value })}
                      />
                    </label>
                    <label className="text-sm">
                      GST %
                      <select
                        aria-label={`tax_rate line ${i + 1}`}
                        className="nx-input"
                        value={line.tax_rate}
                        onChange={(e) => patchLine(i, { tax_rate: e.target.value })}
                      >
                        {slabs.map((s) => (
                          <option key={s} value={s}>
                            {s}%
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="text-sm">
                      Discount (₹)
                      <input
                        aria-label={`discount line ${i + 1}`}
                        inputMode="decimal"
                        type="number"
                        min="0"
                        step="0.01"
                        className="nx-input"
                        value={line.discount}
                        onChange={(e) => patchLine(i, { discount: e.target.value })}
                      />
                    </label>
                  </div>

                  <div className="flex items-center justify-between gap-3">
                    <details className="text-sm">
                      <summary className="cursor-pointer text-slate-600">Type, HSN/SAC &amp; unit</summary>
                      <div className="mt-3 grid grid-cols-3 gap-3">
                        <label className="text-sm">
                          Type
                          <select
                            aria-label={`item_type line ${i + 1}`}
                            className="nx-input"
                            value={line.item_type}
                            onChange={(e) => patchLine(i, { item_type: e.target.value })}
                          >
                            <option value="goods">Goods</option>
                            <option value="service">Service</option>
                          </select>
                        </label>
                        <label className="text-sm">
                          HSN/SAC
                          <input
                            aria-label={`hsn_code line ${i + 1}`}
                            className="nx-input"
                            value={line.hsn_code}
                            onChange={(e) => patchLine(i, { hsn_code: e.target.value })}
                          />
                        </label>
                        <label className="text-sm">
                          Unit
                          <input
                            aria-label={`unit line ${i + 1}`}
                            className="nx-input"
                            value={line.unit}
                            onChange={(e) => patchLine(i, { unit: e.target.value })}
                          />
                        </label>
                      </div>
                    </details>
                    <span className="shrink-0 text-sm font-semibold tabular-nums">{formatMoney(amounts.total)}</span>
                  </div>
                </div>
              );
            })}
            <button
              type="button"
              className="nx-button nx-secondary w-full"
              onClick={() => setLines((prev) => [...prev, emptyLine()])}
            >
              <Plus size={16} aria-hidden="true" /> Add item
            </button>
          </section>

          <section className="nx-panel space-y-3" aria-labelledby="fi-tax">
            <h3 id="fi-tax" className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Tax &amp; terms
            </h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-sm">
                GST treatment
                <select className="nx-input" value={supply} onChange={(e) => setSupply(e.target.value)}>
                  <option value="taxable">With GST — taxable</option>
                  <option value="exempt">Without GST — exempt supply</option>
                  <option value="nil_rated">Without GST — nil rated</option>
                  <option value="non_gst">Non-GST supply</option>
                  <option value="unregistered">Supplier is not GST registered</option>
                </select>
              </label>
              <label className="text-sm">
                Place of supply {supply === "taxable" ? "*" : ""}
                <input
                  className="nx-input"
                  inputMode="numeric"
                  maxLength={2}
                  placeholder="State code, e.g. 27"
                  value={placeOfSupply}
                  onChange={(e) => {
                    setPlace(e.target.value);
                    setPlaceEdited(true);
                  }}
                />
              </label>
            </div>
            <details>
              <summary className="cursor-pointer text-sm font-medium">Due date &amp; notes</summary>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <label className="text-sm">
                  Due date
                  <input type="date" className="nx-input" value={due} onChange={(e) => setDue(e.target.value)} />
                </label>
                <label className="text-sm sm:col-span-2">
                  Notes
                  <textarea className="nx-input" value={notes} onChange={(e) => setNotes(e.target.value)} />
                </label>
              </div>
            </details>
          </section>
        </div>
      </div>

      <footer
        className="border-t border-slate-200 bg-white px-3 pt-2"
        style={{ paddingBottom: "calc(8px + env(safe-area-inset-bottom, 0px))" }}
      >
        <div className="mx-auto max-w-3xl">
          <button
            type="button"
            className="flex w-full items-baseline justify-between text-left"
            aria-expanded={showBreakdown}
            onClick={() => setShowBreakdown((v) => !v)}
          >
            <span className="text-xs text-slate-500">Estimated total {showBreakdown ? "▾" : "▸"}</span>
            <strong className="text-xl tabular-nums">{formatMoney(totals.total)}</strong>
          </button>
          {showBreakdown && (
            <dl className="mb-2 grid grid-cols-[1fr_auto] gap-x-4 text-sm text-slate-600">
              <dt>Subtotal</dt>
              <dd className="tabular-nums">{formatMoney(totals.subtotal)}</dd>
              <dt>Discount</dt>
              <dd className="tabular-nums">− {formatMoney(totals.discount)}</dd>
              <dt>GST</dt>
              <dd className="tabular-nums">{formatMoney(totals.tax)}</dd>
            </dl>
          )}
          <div className="mt-2 flex gap-2">
            <button
              type="button"
              className="nx-button nx-secondary flex-1"
              disabled={busy !== ""}
              onClick={() => void save(false)}
            >
              {busy === "draft" ? "Saving…" : "Save draft"}
            </button>
            {canIssue && (
              <button type="button" className="nx-button flex-1" disabled={busy !== ""} onClick={() => void save(true)}>
                {busy === "issue" ? "Issuing…" : "Save & issue"}
              </button>
            )}
          </div>
          <p className="mt-1 text-center text-[11px] text-slate-500">
            Final amounts are calculated when the invoice is saved. Direct invoices do not dispatch stock.
          </p>
        </div>
      </footer>
    </div>
  );
}

function SuccessScreen({
  className,
  style,
  invoiceId,
  warning,
  phone,
  onPhone,
  canIssue,
  onNew,
  onView,
  onClose,
}: {
  className: string;
  style: CSSProperties;
  invoiceId: string;
  warning: string;
  phone: string | null;
  onPhone: (v: string) => void;
  canIssue: boolean;
  onNew: () => void;
  onView: () => void;
  onClose: () => void;
}) {
  const query = useInvoice(invoiceId);
  const issue = useIssueInvoice();
  const inv = query.data;
  // Null means no manual choice yet. A typed value (including an empty string)
  // always wins over the saved customer number, without a post-render seeding race.
  const sharePhone = phone ?? inv?.customer.phone ?? "";
  const isDraft = !inv || inv.status === "DRAFT";
  const digits = sharePhone.replace(/\D/g, "");
  const text = inv
    ? `Hello ${inv.customer.name}, your invoice ${inv.invoice_number} dated ${inv.invoice_date ?? ""} ` +
      `is for ${formatMoney(inv.total_amount)}. Balance due: ${formatMoney(inv.balance_due)}. Thank you!`
    : "";

  return (
    <div role="dialog" aria-modal="true" aria-label="Invoice saved" className={className} style={style}>
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-8">
        <div className="mx-auto max-w-md space-y-5 text-center">
          <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-emerald-100 text-emerald-700">
            <Check size={32} aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-2xl font-semibold">{isDraft ? "Draft saved" : "Invoice issued"}</h2>
            {inv ? (
              <p className="mt-1 text-sm text-slate-600">
                {inv.invoice_number} · {inv.customer.name}
              </p>
            ) : (
              <p className="mt-1 text-sm text-slate-500">Loading invoice…</p>
            )}
            {inv && (
              <p className="mt-2 text-3xl font-bold tabular-nums">{formatMoney(inv.total_amount)}</p>
            )}
            {inv && (
              <div className="mt-2 flex justify-center">
                <InvoiceStatusBadge status={inv.status} />
              </div>
            )}
          </div>

          {warning && (
            <p role="alert" className="rounded-xl bg-amber-50 p-3 text-left text-sm text-amber-800">
              {warning}
            </p>
          )}
          {query.isError && (
            <p role="alert" className="rounded-xl bg-red-50 p-3 text-left text-sm text-red-700">
              Saved, but the invoice could not be loaded. Open it from the invoice list.
            </p>
          )}

          {inv && isDraft && canIssue && (
            <div className="space-y-2">
              <button
                type="button"
                className="nx-button w-full"
                disabled={issue.isPending}
                onClick={() => issue.mutate(invoiceId)}
              >
                {issue.isPending ? "Issuing…" : "Issue invoice"}
              </button>
              {issue.isError && (
                <p role="alert" className="text-sm text-red-700">
                  {issue.error.message}
                </p>
              )}
              <p className="text-xs text-slate-500">Issue the invoice to share it with your customer.</p>
            </div>
          )}

          {inv && !isDraft && (
            <section className="nx-panel space-y-3 text-left" aria-label="Share invoice">
              <label className="text-sm">
                Customer WhatsApp number
                <input
                  className="nx-input"
                  inputMode="tel"
                  placeholder="10-digit mobile number"
                  value={sharePhone}
                  onChange={(e) => onPhone(e.target.value)}
                />
              </label>
              <div className="flex flex-wrap items-center gap-2">
                {digits.length >= 10 ? (
                  <a
                    href={whatsappLink(sharePhone, text)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="nx-button"
                  >
                    <MessageCircle size={16} aria-hidden="true" /> WhatsApp
                  </a>
                ) : (
                  <button type="button" className="nx-button" disabled>
                    <MessageCircle size={16} aria-hidden="true" /> WhatsApp
                  </button>
                )}
                <DocumentActions
                  documentType="INVOICE"
                  documentId={inv.id}
                  documentNumber={inv.invoice_number}
                  defaultRecipient={inv.customer.email}
                />
              </div>
              <p className="text-xs text-slate-500">
                WhatsApp sends the invoice summary. Use the download button to get the PDF and attach or share it.
              </p>
            </section>
          )}
        </div>
      </div>

      <footer
        className="border-t border-slate-200 bg-white px-3 pt-2"
        style={{ paddingBottom: "calc(8px + env(safe-area-inset-bottom, 0px))" }}
      >
        <div className="mx-auto flex max-w-md gap-2">
          <button type="button" className="nx-button nx-secondary flex-1" onClick={onNew}>
            <FilePlus2 size={16} aria-hidden="true" /> New invoice
          </button>
          <button type="button" className="nx-button nx-secondary flex-1" onClick={onView}>
            <Eye size={16} aria-hidden="true" /> View
          </button>
          <button type="button" className="nx-button flex-1" onClick={onClose}>
            Done
          </button>
        </div>
      </footer>
    </div>
  );
}

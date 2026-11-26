"use client";

import { useRef, useState, type FormEvent } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { FileText, Package, Plus, Save, StickyNote, Trash2, UserRound } from "lucide-react";
import { FieldHint, FormActions, FormSection, FormSheet } from "@/components/form/form-sheet";
import MasterEntry from "@/components/master-entry";
import { useAuth } from "@/features/auth/auth-context";
import BarcodeScan from "@/features/business/barcode-scan";
import GstLookup from "@/features/business/gst-lookup";
import { TaxSelection, invoiceDetailFields } from "@/features/business/invoice-settings";
import { createInvoice, issueInvoice, recordInvoicePayment } from "@/features/invoices/api";
import { useSalesOrderList } from "@/features/sales-orders/hooks";
import { apiRequest } from "@/lib/api/client";
import { hasPermission } from "@/lib/authorization/permissions";
import { formatMoney } from "@/lib/format";
import { discountedPayload, previewDiscount } from "../discount";
import { hsnRequired, isNonTaxable, saleProblem, type SaleProblem } from "../direct-invoice-rules";
import { useInvoiceBankAccounts } from "../hooks";
import type { Quotation } from "../quotation";
import DiscountMode from "./discount-mode";
import ItemCategory from "./item-category";

type Line = {
  product_id?: string;
  category_name?: string;
  item_type: string;
  hsn_code: string;
  sku: string;
  name: string;
  unit: string;
  quantity: string;
  unit_price: string;
  tax_rate: string;
  discount: string;
  discount_mode?: "amount" | "percent";
};
type Master = { id: string; code: string; name: string; item_type?: string; hsn_code?: string; unit?: string; selling_price?: string };

const empty = (): Line => ({ item_type: "goods", hsn_code: "", sku: "", name: "", unit: "PCS", quantity: "1", unit_price: "0", tax_rate: "0", discount: "0" });
const today = () => {
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
};
const fromMaster = (r: Master): Partial<Line> => ({ product_id: r.id, sku: r.code, name: r.name, item_type: r.item_type || "goods", hsn_code: r.hsn_code || "", unit: r.unit || "PCS", unit_price: r.selling_price || "0" });
const cents = (line: Line) => {
  const subtotal = Math.round(Number(line.quantity) * Number(line.unit_price) * 100 + 1e-8);
  const discount = Math.round(previewDiscount(line) * 100);
  return { subtotal, discount, tax: Math.round(((subtotal - discount) * Number(line.tax_rate)) / 100 + 1e-8) };
};
const money = (c: number) => formatMoney(String(c / 100));

export default function InvoiceDialog(props: {
  sourceQuote?: Quotation;
  quotation?: boolean;
  open: boolean;
  onClose: () => void;
  onCreated?: (id: string) => void;
  initialMode?: "direct" | "order";
}) {
  // Remount on every open so each invoice starts from a clean form.
  if (!props.open) return null;
  return <InvoiceForm {...props} />;
}

function InvoiceForm({
  onClose,
  onCreated,
  initialMode = "order",
  quotation = false,
  sourceQuote,
}: {
  sourceQuote?: Quotation;
  quotation?: boolean;
  onClose: () => void;
  onCreated?: (id: string) => void;
  initialMode?: "direct" | "order";
}) {
  const [mode, setMode] = useState<"direct" | "order">(initialMode);
  const [supply, setSupply] = useState("");
  const [customer, setCustomer] = useState<Record<string, string>>(() => sourceQuote?.customer_details ?? (sourceQuote ? { name: sourceQuote.customer } : {}));
  const [details, setDetails] = useState<Record<string, string>>({});
  const [lines, setLines] = useState<Line[]>(() => sourceQuote?.items.map((item) => ({ ...empty(), ...item })) ?? [empty()]);
  const [message, setMessage] = useState("");
  const [notice, setNotice] = useState("");
  const [problem, setProblem] = useState<SaleProblem | null>(null);
  const [busy, setBusy] = useState(false);
  const [cash, setCash] = useState(false);
  const [savedCash, setSavedCash] = useState("");
  const savedRates = useRef<string[] | null>(null);
  const submitting = useRef(false);
  const { authentication } = useAuth();
  const permissions = authentication?.role.permissions ?? [];
  const accounts = useInvoiceBankAccounts(cash);
  const qc = useQueryClient();
  const orders = useSalesOrderList({ page: 1, page_size: 100, status: "FULFILLED", sort: "-created_at" });

  const update = (i: number, patch: Partial<Line>) => {
    setLines((prev) => prev.map((line, j) => (j === i ? { ...line, ...patch } : line)));
    if (problem?.line === i) setProblem(null);
  };

  function changeSupply(next: string) {
    const wasTaxable = !isNonTaxable(supply);
    if (isNonTaxable(next) && lines.some((l) => Number(l.tax_rate || 0) !== 0)) {
      if (wasTaxable) savedRates.current = lines.map((l) => l.tax_rate);
      setLines((prev) => prev.map((l) => ({ ...l, tax_rate: "0" })));
      setNotice("GST set to 0% on every line because this sale is without GST.");
    } else if (!isNonTaxable(next) && savedRates.current) {
      const rates = savedRates.current;
      setLines((prev) => prev.map((l, i) => ({ ...l, tax_rate: rates[i] ?? l.tax_rate })));
      savedRates.current = null;
      setNotice("Previous GST rates restored.");
    } else setNotice("");
    setSupply(next);
    setProblem(null);
  }

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (submitting.current) return;
    const f = new FormData(e.currentTarget);
    const invoiceDate = String(f.get("date"));
    if (mode === "direct") {
      const found = saleProblem(lines, { invoiceDate, dueDate: String(f.get("due") || ""), supply, placeOfSupply: details.place_of_supply, quotation });
      setProblem(found);
      if (found) {
        setMessage(found.message);
        const selector = found.line !== undefined ? `[aria-label="${found.field} line ${found.line + 1}"]` : found.field === "place_of_supply" ? "#invoice-place-of-supply" : null;
        if (selector) {
          const el = document.querySelector<HTMLElement>(selector);
          el?.closest("details")?.setAttribute("open", "");
          el?.focus();
        }
        return;
      }
    }
    submitting.current = true;
    setBusy(true);
    setMessage("");
    try {
      const common = { invoice_date: invoiceDate, due_date: String(f.get("due") || ""), notes: String(f.get("notes") || ""), billing_details: { ...details, supply_type: supply } };
      if (quotation) {
        await apiRequest("/business/quotations/", { method: "POST", body: { ...common, customer, items: lines.map(discountedPayload) } });
        await qc.invalidateQueries({ queryKey: ["quotations"] });
        onClose();
        return;
      }
      if (savedCash) {
        onClose();
        onCreated?.(savedCash);
        return;
      }
      let id = "";
      if (mode === "order") id = (await createInvoice({ ...common, sales_order_id: String(f.get("order")) })).id;
      else {
        const r = await apiRequest<{ id: string }>("/business/direct-invoices/" + (sourceQuote ? "?quotation=" + encodeURIComponent(sourceQuote.number) : ""), {
          method: "POST",
          body: {
            ...common,
            invoice_number: String(f.get("number") || ""),
            customer: cash && !customer.name?.trim() ? { name: "Walk-in cash customer", code: "WALK-IN-CASH" } : customer,
            sale_mode: cash ? "cash" : "credit",
            items: lines.map(discountedPayload),
          },
        });
        id = r.data.id;
      }
      if (cash) {
        setSavedCash(id);
        try {
          const issued = await issueInvoice(id);
          if (Number(issued.balance_due) > 0)
            await recordInvoicePayment(id, { amount: issued.balance_due, payment_method: "CASH", bank_account_id: String(f.get("cash_account")), payment_date: common.invoice_date, request_key: "cash-sale-" + id });
        } catch (error) {
          await qc.invalidateQueries();
          setMessage("Invoice saved. Open it to review the issue or payment status: " + (error as Error).message);
          return;
        }
      }
      await qc.invalidateQueries().catch(() => {});
      onClose();
      onCreated?.(id);
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }

  const totals = lines.reduce((sum, line) => {
    const c = cents(line);
    return { subtotal: sum.subtotal + c.subtotal, discount: sum.discount + c.discount, tax: sum.tax + c.tax };
  }, { subtotal: 0, discount: 0, tax: 0 });
  const grand = totals.subtotal - totals.discount + totals.tax;
  const noGst = isNonTaxable(supply);
  const hsnLabel = hsnRequired(supply) ? "HSN/SAC *" : "HSN/SAC (optional)";
  const invalid = (line: number, field: SaleProblem["field"]) => (problem?.line === line && problem.field === field) || undefined;
  const title = quotation ? "New quotation" : mode === "direct" ? (cash ? "Cash sale" : "New sale invoice") : "Invoice from sales order";
  const canCash = hasPermission(permissions, "invoices.issue") && hasPermission(permissions, "invoices.record_payment");

  return (
    <FormSheet title={title} subtitle={sourceQuote ? `From quotation ${sourceQuote.number}. Check the customer and item matches before saving.` : undefined} onClose={onClose} busy={busy} size="xl" closeLabel="Close invoice">
      <form onSubmit={submit}>
        {!sourceQuote && !quotation ? (
          <div className="flex flex-wrap items-center gap-2">
            <div className="nxf-segment" role="group" aria-label="Payment terms">
              {["Credit", "Cash"].map((label) => (
                <button key={label} type="button" disabled={busy || !!savedCash} aria-pressed={cash === (label === "Cash")} onClick={() => { setCash(label === "Cash"); if (label === "Cash") setMode("direct"); }}>{label}</button>
              ))}
            </div>
            {!cash ? (
              <div className="nxf-segment" role="group" aria-label="Invoice source">
                {(["direct", "order"] as const).map((value) => (
                  <button key={value} type="button" aria-pressed={mode === value} onClick={() => setMode(value)}>{value === "direct" ? "Direct invoice" : "From sales order"}</button>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}

        <div className="grid gap-3.5 lg:grid-cols-2">
          <FormSection title="Customer" icon={UserRound}>
            {mode === "order" ? (
              <label>Fulfilled sales order *
                <select name="order" required>
                  <option value="">Choose an order</option>
                  {orders.data?.sales_orders.map((o) => <option value={o.id} key={o.id}>{o.so_number} · {o.customer.name}</option>)}
                </select>
                {orders.error ? <span role="alert" className="nxf-field-hint">{orders.error.message}</span> : null}
              </label>
            ) : (
              <>
                <MasterEntry
                  kind="customers"
                  label={cash ? "Customer (optional)" : "Customer name *"}
                  required={!cash}
                  value={customer.name || ""}
                  onChange={(name) => setCustomer(customer.id ? { name } : { ...customer, name, id: "", code: "" })}
                  onSelect={(r) => setCustomer({ id: r.id, code: r.code, name: r.name, address: r.billing_address || "", state: r.state || "", gstin: r.gstin || "", phone: r.phone || "", email: r.email || "" })}
                />
                <FieldHint>Pick a saved customer, or type a new name to add one when saving.</FieldHint>
                {cash ? (
                  <label>Cash received into *
                    <select name="cash_account" required>
                      <option value="">Select account</option>
                      {accounts.data?.bank_accounts.map((a) => <option key={a.id} value={a.id}>{a.account_name}</option>)}
                    </select>
                  </label>
                ) : null}
                <details>
                  <summary>Fill from GSTIN</summary>
                  <div className="mt-3"><GstLookup onSelect={(r) => setCustomer({ ...customer, id: "", code: "", ...r })} /></div>
                </details>
                <details>
                  <summary>Address &amp; contact</summary>
                  <div className="nxf-grid mt-3">
                    {[["address", "Billing address"], ["gstin", "GSTIN"], ["state", "State"], ["phone", "Phone"], ["email", "Email"], ["code", "Customer code (automatic if blank)"]].map(([key, label]) => (
                      <label key={key}>{label}<input type={key === "email" ? "email" : "text"} value={customer[key] || ""} onChange={(e) => setCustomer({ ...customer, [key]: e.target.value })} /></label>
                    ))}
                  </div>
                </details>
              </>
            )}
          </FormSection>

          <FormSection title={quotation ? "Quotation" : "Invoice"} icon={FileText}>
            <div className="nxf-grid">
              <label>{quotation ? "Quotation date" : "Invoice date"} *<input name="date" type="date" required defaultValue={today()} /></label>
              <label>{quotation ? "Valid until" : "Due date"}<input name="due" type="date" aria-invalid={problem?.field === "due" || undefined} /></label>
              {mode === "direct" && !quotation ? <label className="nxf-span">Invoice number<input name="number" placeholder="Automatic" /></label> : null}
              {!quotation ? <TaxSelection value={supply} onChange={changeSupply} /> : null}
              {!quotation ? (
                <label>Place of supply {supply && supply !== "unregistered" ? "*" : ""}
                  <input
                    id="invoice-place-of-supply"
                    inputMode="numeric"
                    maxLength={2}
                    placeholder="State code, e.g. 27"
                    required={!!supply && supply !== "unregistered"}
                    aria-invalid={problem?.field === "place_of_supply" || undefined}
                    value={details.place_of_supply || ""}
                    onChange={(e) => { setDetails({ ...details, place_of_supply: e.target.value }); if (problem?.field === "place_of_supply") setProblem(null); }}
                  />
                </label>
              ) : null}
            </div>
            {notice ? <p role="status" className="nxf-field-hint">{notice}</p> : null}
            {!quotation ? <FieldHint>{noGst ? "Without GST: HSN/SAC is optional and every line is 0% GST." : "Saved as a draft for review before issuing. Goods are deducted from stock when saved."}</FieldHint> : null}
          </FormSection>
        </div>

        {mode === "direct" ? (
          <FormSection title="Items" icon={Package} aside={<span className="nxf-field-hint">{lines.length} / 100</span>}>
            <div className="nxf-line-head" aria-hidden="true">
              <span>Item</span><span>Qty</span><span>Rate ₹</span><span>Discount</span><span>GST %</span><span className="text-right">Amount</span><span />
            </div>
            <div className="nxf-lines">
              {lines.map((line, i) => {
                const c = cents(line);
                const lineHsnMissing = hsnRequired(supply) && !line.hsn_code.trim() && !!line.name.trim();
                return (
                  <div className="nxf-line" key={i}>
                    <div className="min-w-0">
                      <BarcodeScan
                        onSelect={(r) => update(i, fromMaster(r))}
                        renderInput={(scan, inputRef, ready) => (
                          <MasterEntry
                            kind="products"
                            label={"name line " + (i + 1)}
                            placeholder="Search, scan or type an item"
                            required
                            value={line.name}
                            inputRef={inputRef}
                            scanMode={ready}
                            onScan={scan}
                            onChange={(name) => setLines((prev) => prev.map((l, j) => (i === j ? (l.sku ? { ...empty(), quantity: l.quantity, tax_rate: l.tax_rate, name } : { ...l, name }) : l)))}
                            onSelect={(r) => update(i, fromMaster(r))}
                          />
                        )}
                      />
                      {!quotation && !line.sku && hasPermission(permissions, "products.create") ? <ItemCategory value={line.category_name || ""} onChange={(category_name) => update(i, { category_name })} /> : null}
                    </div>
                    {(["quantity", "unit_price", "discount", "tax_rate"] as const).map((key) => (
                      <label key={key}>
                        <span className="nxf-mobile-label">{{ quantity: "Qty", unit_price: "Rate ₹", discount: "Discount", tax_rate: "GST %" }[key]}</span>
                        {key === "discount" ? <DiscountMode label={"Discount mode line " + (i + 1)} value={line.discount_mode} onChange={(discount_mode) => update(i, { discount_mode })} /> : null}
                        <input
                          aria-label={key + " line " + (i + 1)}
                          aria-invalid={key === "discount" ? undefined : invalid(i, key)}
                          value={line[key]}
                          required={key === "quantity" || key === "unit_price"}
                          disabled={key === "tax_rate" && noGst}
                          title={key === "tax_rate" && noGst ? "No GST on this sale" : undefined}
                          type="number"
                          inputMode="decimal"
                          min={key === "quantity" ? "0.01" : "0"}
                          max={key === "tax_rate" ? 100 : undefined}
                          step="0.01"
                          onChange={(e) => update(i, { [key]: e.target.value })}
                        />
                      </label>
                    ))}
                    <span className="nxf-line-total">{money(c.subtotal - c.discount + c.tax)}</span>
                    <button type="button" className="nxf-close nxf-line-remove" aria-label={"Remove line " + (i + 1)} disabled={lines.length === 1} onClick={() => setLines((prev) => prev.filter((_, j) => j !== i))}><Trash2 size={17} /></button>
                    <details className="nxf-span" style={{ gridColumn: "1 / -1" }} open={lineHsnMissing && problem?.line === i ? true : undefined}>
                      <summary>{lineHsnMissing ? "Add HSN/SAC (required for taxable sales)" : "Type, HSN/SAC, SKU & unit"}</summary>
                      <div className="nxf-line-extra mt-2">
                        <label>Type<select aria-label={"item_type line " + (i + 1)} value={line.item_type} onChange={(e) => update(i, { item_type: e.target.value })}><option value="goods">Goods</option><option value="service">Service</option></select></label>
                        <label>{hsnLabel}<input aria-label={"hsn_code line " + (i + 1)} aria-invalid={invalid(i, "hsn_code")} inputMode="numeric" maxLength={8} value={line.hsn_code} onChange={(e) => update(i, { hsn_code: e.target.value.replace(/\D/g, "") })} /></label>
                        <label>SKU (auto)<input aria-label={"sku line " + (i + 1)} value={line.sku} onChange={(e) => update(i, { sku: e.target.value })} /></label>
                        <label>Unit<input aria-label={"unit line " + (i + 1)} value={line.unit} onChange={(e) => update(i, { unit: e.target.value })} /></label>
                      </div>
                    </details>
                  </div>
                );
              })}
            </div>
            <button type="button" className="nx-button nx-secondary self-start" disabled={lines.length >= 100} onClick={() => setLines((prev) => [...prev, empty()])}><Plus size={16} />Add item</button>
            <dl className="ml-auto grid w-full max-w-xs grid-cols-2 gap-y-1 text-sm tabular-nums">
              <dt className="nx-muted">Subtotal</dt><dd className="text-right">{money(totals.subtotal)}</dd>
              <dt className="nx-muted">Discount</dt><dd className="text-right">− {money(totals.discount)}</dd>
              <dt className="nx-muted">Taxable value</dt><dd className="text-right">{money(totals.subtotal - totals.discount)}</dd>
              <dt className="nx-muted">GST</dt><dd className="text-right">{money(totals.tax)}</dd>
            </dl>
          </FormSection>
        ) : null}

        <FormSection title="Notes & more" icon={StickyNote}>
          <label>Notes<textarea name="notes" defaultValue={sourceQuote?.notes} placeholder={quotation ? "Quotation terms or notes" : "A note printed on this invoice"} /></label>
          <details>
            <summary>PO, service period, delivery &amp; terms</summary>
            <div className="nxf-grid mt-3">
              {invoiceDetailFields.filter(([key]) => key !== "place_of_supply").map(([key, label]) => (
                <label key={key}>{label}<input type={["po_date", "service_from", "service_to"].includes(key) ? "date" : "text"} value={details[key] || ""} onChange={(e) => setDetails({ ...details, [key]: e.target.value })} /></label>
              ))}
            </div>
          </details>
        </FormSection>

        {message ? <p role="alert" className="nxf-error">{message}</p> : null}

        <FormActions total={mode === "direct" ? <output aria-label="Estimated total">{money(grand)}</output> : undefined} hint={quotation ? "Estimate only" : "Draft first. Review before issuing."}>
          <button type="button" disabled={busy} className="nx-button nx-secondary nxf-secondary-sm" onClick={onClose}>Cancel</button>
          <button className="nx-button" disabled={busy || (cash && !savedCash && !canCash)}>
            <Save size={17} />
            {busy ? "Saving…" : savedCash ? "Open saved invoice" : quotation ? "Save quotation" : cash ? "Save cash sale" : "Save draft invoice"}
          </button>
        </FormActions>
      </form>
    </FormSheet>
  );
}

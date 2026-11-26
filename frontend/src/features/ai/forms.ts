/**
 * Maps a NexEase AI proposal onto the app's real forms.
 * The server decides which form fits and what is missing (`assist`); this file only translates
 * field names so each form opens already filled in.
 */
import type { InvoicePrefill } from "@/features/invoices/components/invoice-dialog";
import type { PurchasePrefill } from "@/features/business/quick-purchase";
import type { SettlePrefill } from "@/features/payments/components/settle-sheet";

export type Entry = { kind: string; fields: Record<string, string>; items: Record<string, string>[]; questions: string[]; warnings: string[] };

export type Missing = { field: string; label: string; question: string; required: boolean; choices: string[]; input: "text" | "number" | "date" | "choice" };

export type FormTarget = { type: "invoice" | "purchase" | "payment" | "customer" | "supplier" | "product" | "stock_adjustment" | "category" | "record"; route?: string | null; record_kind?: string };

export type Assist = {
  kind: string;
  label: string;
  form: FormTarget | null;
  missing: Missing[];
  ready: boolean;
  summary: { label: string; value: string }[];
  reply: string;
  notes?: string[];
  refs: Record<string, string>;
  quick_save: boolean;
};

export type Proposal = { id: string; state: string; kind: string; data: Entry; warnings: string[]; result: Record<string, unknown>; assist?: Assist | null };

/** Forms that open on top of the current screen; the rest open on their own screen. */
export const IN_PLACE = new Set(["invoice", "purchase", "payment", "customer", "supplier", "product"]);

export const today = () => new Date(Date.now() + 330 * 60_000).toISOString().slice(0, 10);

const ITEM_KEYS = ["item_type", "hsn_code", "sku", "name", "unit", "quantity", "unit_price", "tax_rate", "discount"];
const blankLine = () => Object.fromEntries(ITEM_KEYS.map((k) => [k, ""]));

const filled = (o: Record<string, string | undefined>) => Object.fromEntries(Object.entries(o).filter(([, v]) => v !== undefined && v !== "")) as Record<string, string>;

/** Apply a quick answer ("items.0.unit_price" = "380") to the proposal without another AI call. */
export function applyAnswer(entry: Entry, field: string, value: string): Entry {
  const line = /^items\.(\d+)\.(\w+)$/.exec(field);
  if (line) {
    const index = Number(line[1]);
    const items = entry.items.map((x) => ({ ...x }));
    while (items.length <= index) items.push(blankLine());
    items[index][line[2]] = value;
    return { ...entry, items };
  }
  const fields = { ...entry.fields, [field]: value };
  if (field === "name" && ["customer", "supplier"].includes(entry.kind)) fields.party_name = value;
  return { ...entry, fields };
}

function lines(entry: Entry) {
  return entry.items
    .filter((l) => l.name || l.sku)
    .map((l) => filled(Object.fromEntries(ITEM_KEYS.map((k) => [k, l[k]]))));
}

export function invoicePrefill(entry: Entry): InvoicePrefill {
  const f = entry.fields;
  return {
    customer: filled({ name: f.party_name, code: f.party_code, gstin: f.party_gstin, address: f.party_address, state: f.party_state }),
    items: lines(entry),
    date: f.date || undefined,
    due_date: f.due_date || undefined,
    number: f.number || undefined,
    notes: f.notes || undefined,
    supply: f.supply_type || undefined,
    details: filled({ place_of_supply: f.place_of_supply, po_number: f.po_number, po_date: f.po_date, service_from: f.service_from, service_to: f.service_to, site_name: f.site_name }),
  };
}

export function purchasePrefill(entry: Entry): PurchasePrefill {
  const f = entry.fields;
  return {
    header: filled({ number: f.number, date: f.date || today(), code: f.party_code, name: f.party_name, address: f.party_address, gstin: f.party_gstin, state: f.party_state }),
    items: lines(entry),
  };
}

const METHOD: Record<string, string> = { cash: "CASH", upi: "UPI", "bank transfer": "BANK_TRANSFER", bank: "BANK_TRANSFER", neft: "BANK_TRANSFER", cheque: "CHEQUE", card: "CARD", "debit card": "CARD", "credit card": "CARD" };

export function paymentPrefill(entry: Entry): SettlePrefill {
  const f = entry.fields;
  return filled({ amount: f.amount, method: METHOD[(f.payment_mode || "").toLowerCase()], date: f.date, reference: f.reference, notes: f.notes });
}

export function customerPrefill(entry: Entry) {
  const f = entry.fields;
  return filled({ name: f.name || f.party_name, phone: f.phone, email: f.email, gstin: f.party_gstin, billing_address: f.party_address || f.address, state: f.party_state });
}

export function supplierPrefill(entry: Entry) {
  const f = entry.fields;
  return filled({ name: f.name || f.party_name, phone: f.phone, email: f.email, gstin: f.party_gstin, address: f.party_address || f.address, state: f.party_state });
}

export function productPrefill(entry: Entry) {
  const f = entry.fields;
  return filled({ name: f.name, sku: f.sku, item_type: f.item_type === "service" ? "service" : f.item_type ? "goods" : undefined, hsn_code: f.hsn_code, selling_price: f.selling_price, cost_price: f.cost_price, description: f.description, category_id: f.category_id });
}

const RECORD_MODE: Record<string, string> = { card: "Debit card", cheque: "Bank transfer", bank: "Bank transfer" };

/** Values for a BusinessWorkspace record form. Unknown keys are dropped by the form itself. */
export function recordPrefill(entry: Entry, recordKind: string, proposalId?: string): Record<string, string> {
  const f = { ...entry.fields };
  if (f.payment_mode) f.payment_mode = RECORD_MODE[f.payment_mode.toLowerCase()] ?? f.payment_mode;
  const data: Record<string, string> = { ...filled(f) };
  if (recordKind === "expenses") {
    if (f.party_name) data.payee = f.party_name;
    if (!f.description && f.category) data.description = f.category;
  }
  if (!data.date && ["expenses", "advances", "timesheets"].includes(recordKind)) data.date = today();
  // Same system reference the one-tap save uses, so the required field is never a dead end.
  if (!data.reference && proposalId && ["expenses", "advances"].includes(recordKind)) data.reference = "AI-" + proposalId.slice(-8).toUpperCase();
  return data;
}

/** Plain-language description of a missing answer, for the chat bubble. */
export function answerLabel(m: Missing, value: string) {
  return m.input === "choice" && m.label.includes("GST") ? `${value}% GST` : value;
}

/**
 * Client-side mirror of the server rules for direct sales invoices
 * (apps/business/direct_entry.py and billing.clean_details). Checking here means the user sees
 * the problem on the line before saving instead of a rejected request afterwards.
 */
export interface DirectLine {
  sku: string;
  name: string;
  quantity: string;
  unit_price: string;
  tax_rate?: string;
  item_type?: string;
  hsn_code?: string;
}

export interface SaleContext {
  invoiceDate: string;
  dueDate: string;
  /** GST treatment; "" when not chosen yet (quotations have none). */
  supply?: string;
  placeOfSupply?: string;
  /** Quotations skip GST classification rules. */
  quotation?: boolean;
}

export interface SaleProblem {
  message: string;
  line?: number;
  field?: "quantity" | "unit_price" | "tax_rate" | "hsn_code" | "place_of_supply" | "due";
}

const TWO_DECIMALS = /^\d+(\.\d{1,2})?$/;
const HSN = /^(?:\d{4}|\d{6}|\d{8})$/;

/** HSN/SAC is mandatory only on taxable supplies, matching billing.HSN_REQUIRED_SUPPLIES. */
export const hsnRequired = (supply?: string) => supply === "taxable";
export const isNonTaxable = (supply?: string) => !!supply && supply !== "taxable";

export function hsnProblem(hsn: string | undefined, itemType: string | undefined, supply?: string): string {
  const code = (hsn ?? "").trim();
  if (!code) return hsnRequired(supply) ? "HSN/SAC is required for taxable sales." : "";
  if (!HSN.test(code)) return "HSN/SAC must have 4, 6 or 8 digits.";
  if (itemType === "service" && code.length !== 6) return "Services need a 6-digit SAC.";
  return "";
}

export function saleProblem(lines: readonly DirectLine[], ctx: SaleContext): SaleProblem | null {
  const filled = lines.map((line, index) => ({ line, index })).filter(({ line }) => line.name.trim());
  for (const { line, index } of filled) {
    const label = line.name.trim();
    if (!TWO_DECIMALS.test(line.quantity.trim())) return { message: `${label}: quantity can have at most 2 decimal places.`, line: index, field: "quantity" };
    if (!TWO_DECIMALS.test(line.unit_price.trim())) return { message: `${label}: rate can have at most 2 decimal places (for example 84.75).`, line: index, field: "unit_price" };
  }
  const seen = new Set<string>();
  for (const { line, index } of filled) {
    const sku = line.sku.trim().toUpperCase();
    if (!sku) continue;
    if (seen.has(sku)) return { message: `${line.name.trim()} is added twice. Increase the quantity on one line instead.`, line: index, field: "quantity" };
    seen.add(sku);
  }
  if (ctx.dueDate && ctx.invoiceDate && ctx.dueDate < ctx.invoiceDate) return { message: "Due date cannot be before the invoice date.", field: "due" };
  if (ctx.quotation || !ctx.supply) return null;

  if (ctx.supply !== "unregistered" && !/^\d{2}$/.test((ctx.placeOfSupply ?? "").trim())) {
    return { message: "Enter the 2-digit place-of-supply state code, for example 27.", field: "place_of_supply" };
  }
  if (isNonTaxable(ctx.supply)) {
    const taxed = filled.find(({ line }) => Number(line.tax_rate || 0) !== 0);
    if (taxed) return { message: `${taxed.line.name.trim()}: set GST to 0% for a sale without GST, or choose "With GST — taxable".`, line: taxed.index, field: "tax_rate" };
  }
  for (const { line, index } of filled) {
    const problem = hsnProblem(line.hsn_code, line.item_type, ctx.supply);
    if (problem) return { message: `${line.name.trim()}: ${problem}`, line: index, field: "hsn_code" };
  }
  return null;
}

/** Back-compatible string form used by the (currently unused) quick invoice screen. */
export function directInvoiceProblem(lines: readonly DirectLine[], invoiceDate: string, dueDate: string): string {
  return saleProblem(lines, { invoiceDate, dueDate })?.message ?? "";
}

/**
 * Client-side mirror of the server rules in apps/business/direct_entry.py (POST /business/direct-invoices/).
 * Without these checks the form accepted values the server rejects, so users only saw a 400 after saving.
 */
export interface DirectLine {
  sku: string;
  name: string;
  quantity: string;
  unit_price: string;
}

const TWO_DECIMALS = /^\d+(\.\d{1,2})?$/;

export function directInvoiceProblem(lines: readonly DirectLine[], invoiceDate: string, dueDate: string): string {
  const filled = lines.filter((l) => l.name.trim());
  for (const [index, line] of filled.entries()) {
    const label = line.name.trim() || `line ${index + 1}`;
    if (!TWO_DECIMALS.test(line.quantity.trim())) return `${label}: quantity can have at most 2 decimal places.`;
    if (!TWO_DECIMALS.test(line.unit_price.trim())) return `${label}: rate can have at most 2 decimal places (for example 84.75).`;
  }
  const seen = new Map<string, string>();
  for (const line of filled) {
    const sku = line.sku.trim().toUpperCase();
    if (!sku) continue;
    if (seen.has(sku)) return `${line.name.trim()} is added twice. Increase the quantity on one line instead.`;
    seen.set(sku, line.name);
  }
  if (dueDate && invoiceDate && dueDate < invoiceDate) return "Due date cannot be before the invoice date.";
  return "";
}

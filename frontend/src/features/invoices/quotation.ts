export interface Quotation {
  number: string;
  customer: string;
  customer_details?: Record<string,string>;
  date: string;
  valid_until: string;
  notes: string;
  total: string;
  conversion?: {kind:"order"|"invoice"; status:string; id?:string; number?:string};
  linked_invoice?: {id:string; number:string};
  items: {name:string; quantity:string; unit_price:string; tax_rate:string; discount:string; total:string;
    product_id?:string; sku?:string; unit?:string; item_type?:string; hsn_code?:string}[];
}

function today(): string {
  return new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" });
}

/** Display state for a quotation row. Dates compare in IST, the app's billing timezone. */
export function quotationState(q: Quotation, now = today()): { label: string; tone: "success" | "warning" | "danger" | "info" } {
  if (q.conversion?.id) return { label: q.conversion.kind === "order" ? "Ordered" : "Invoiced", tone: "success" };
  if (q.conversion) return { label: "Converting", tone: "warning" };
  if (q.valid_until && q.valid_until.slice(0, 10) < now) return { label: "Expired", tone: "danger" };
  return { label: "Open", tone: "info" };
}

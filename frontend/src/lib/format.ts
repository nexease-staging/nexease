const money2 = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2, maximumFractionDigits: 2 });
const money0 = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
const compact = new Intl.NumberFormat("en-IN", { notation: "compact", maximumFractionDigits: 1 });
const dateFmt = new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" });

export function toNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function formatMoney(value: string | number | null | undefined, decimals: 0 | 2 = 2): string {
  const n = toNumber(value);
  if (n === null) return "—";
  return (decimals === 0 ? money0 : money2).format(n);
}

/** Short form for KPI tiles, e.g. ₹1.2L or ₹3.4Cr. */
export function formatCompactMoney(value: string | number | null | undefined): string {
  const n = toNumber(value);
  return n === null ? "—" : "₹" + compact.format(n);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : dateFmt.format(d);
}

function localIsoDate(d: Date): string {
  const p = (x: number) => String(x).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/** Unpaid and past its due date (compares calendar dates in the user's timezone). */
export function isInvoiceOverdue(
  invoice: { status: string; due_date: string | null; balance_due: string },
  today: Date = new Date(),
): boolean {
  if (!invoice.due_date) return false;
  if (invoice.status !== "ISSUED" && invoice.status !== "PARTIALLY_PAID") return false;
  if ((toNumber(invoice.balance_due) ?? 0) <= 0) return false;
  return invoice.due_date.slice(0, 10) < localIsoDate(today);
}

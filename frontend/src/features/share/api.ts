import { apiBinaryRequest, apiRequest } from "@/lib/api/client";
import type { DocumentType } from "@/features/documents/types";

export type ShareKind =
  | "invoice" | "sales_order" | "credit_note" | "receipt" | "purchase_order" | "bill" | "debit_note" | "payment" | "goods_receipt"
  | "quotation" | "statement" | "tally_ledger" | "tally_voucher";
export type Channel = "whatsapp" | "email" | "link";

export interface ShareTarget {
  kind: ShareKind;
  id: string;
  /** statements: side and period */
  side?: "customer" | "supplier";
  from?: string;
  to?: string;
  channel?: Channel;
  /** shown while loading */
  title?: string;
}

export interface Prepared {
  kind: ShareKind; id: string; label: string; number: string; filename: string;
  recipient: { name: string; phone: string; email: string };
  amount: number | null; whatsapp: string; subject: string; body: string;
  link: { token: string; url: string; expires: string; views: number } | null;
  extra: { from?: string; to?: string; side?: string; balance?: number; open_bills?: number; due_date?: string };
  history: { channel: string; recipients: string[]; at: string; by_name: string }[];
}

export const DOC_KIND: Record<DocumentType, ShareKind> = {
  INVOICE: "invoice", SALES_ORDER: "sales_order", CREDIT_NOTE: "credit_note", CUSTOMER_PAYMENT: "receipt", PURCHASE_ORDER: "purchase_order",
  VENDOR_BILL: "bill", VENDOR_DEBIT_NOTE: "debit_note", SUPPLIER_PAYMENT: "payment", GOODS_RECEIPT: "goods_receipt",
};

export const STATEMENT_KINDS: ShareKind[] = ["statement", "tally_ledger"];

export function query(t: ShareTarget) {
  const p = new URLSearchParams({ kind: t.kind, id: t.id });
  if (t.side) p.set("side", t.side);
  if (t.from) p.set("from", t.from);
  if (t.to) p.set("to", t.to);
  return p.toString();
}

export const prepare = async (t: ShareTarget) => (await apiRequest<Prepared>(`/business/share/prepare/?${query(t)}`)).data;
export const fetchPdf = (t: ShareTarget) => apiBinaryRequest(`/business/share/pdf/?${query(t)}`);
export const sendEmail = (t: ShareTarget, body: { recipients: string; cc: string; subject: string; message: string; attach: boolean; link: boolean }) =>
  apiRequest<{ sent_to: string[] }>("/business/share/email/", { method: "POST", body: { kind: t.kind, id: t.id, side: t.side, from: t.from, to: t.to, ...body } });
export const logShare = (t: ShareTarget, channel: string, recipient = "", number = "") =>
  apiRequest("/business/share/log/", { method: "POST", body: { kind: t.kind, id: t.id, side: t.side, from: t.from, to: t.to, channel, recipient, number } }).catch(() => undefined);
export const revokeLink = (token: string) => apiRequest(`/business/share/links/${token}/revoke/`, { method: "POST", body: {} });

/** Indian numbers without a country code get +91. Returns digits only, or "" when unusable. */
export function waNumber(phone: string) {
  const digits = (phone || "").replace(/\D/g, "").replace(/^0+/, "");
  if (digits.length === 10) return "91" + digits;
  return digits.length >= 11 && digits.length <= 15 ? digits : "";
}

export function waLink(phone: string, text: string) {
  const n = waNumber(phone);
  return `https://wa.me/${n}?text=${encodeURIComponent(text)}`;
}

const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

export function periods(now = new Date()) {
  const fy = now.getMonth() >= 3 ? now.getFullYear() : now.getFullYear() - 1;
  const today = iso(now);
  const month = iso(new Date(now.getFullYear(), now.getMonth(), 1));
  const lastMonthStart = iso(new Date(now.getFullYear(), now.getMonth() - 1, 1));
  const lastMonthEnd = iso(new Date(now.getFullYear(), now.getMonth(), 0));
  return [
    { key: "fy", label: "This financial year", from: `${fy}-04-01`, to: today },
    { key: "month", label: "This month", from: month, to: today },
    { key: "last_month", label: "Last month", from: lastMonthStart, to: lastMonthEnd },
    { key: "last_fy", label: "Last financial year", from: `${fy - 1}-04-01`, to: `${fy}-03-31` },
  ];
}

const EVENT = "nexease:share";

/** Opens the share sheet from anywhere (rows, detail screens, Tally, phone parties). */
export function openShare(target: ShareTarget) {
  window.dispatchEvent(new CustomEvent(EVENT, { detail: target }));
}

export const SHARE_EVENT = EVENT;

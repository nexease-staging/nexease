import { Ban, CheckCircle2, CircleDashed, PackageCheck, PieChart, Send, Truck, type LucideIcon } from "lucide-react";
import type { StatusStyle } from "@/components/list/list-kit";
import type { CreditNoteStatus } from "@/features/credit-notes/types";
import type { InvoiceStatus } from "@/features/invoices/types";
import type { SalesOrderStatus } from "@/features/sales-orders/types";
import type { SalesReturnStatus } from "@/features/sales-returns/types";

const s = (label: string, tone: StatusStyle["tone"], icon?: LucideIcon): StatusStyle => ({ label, tone, icon });

export const invoiceStatus: Record<InvoiceStatus, StatusStyle> = {
  DRAFT: s("Draft", "neutral", CircleDashed),
  ISSUED: s("Unpaid", "violet", Send),
  PARTIALLY_PAID: s("Partly paid", "info", PieChart),
  PAID: s("Paid", "success", CheckCircle2),
  CANCELLED: s("Cancelled", "danger", Ban),
};

export const salesOrderStatus: Record<SalesOrderStatus, StatusStyle> = {
  DRAFT: s("Draft", "neutral", CircleDashed),
  CONFIRMED: s("Confirmed", "violet", Send),
  PARTIALLY_FULFILLED: s("Part delivered", "info", Truck),
  FULFILLED: s("Delivered", "success", PackageCheck),
  CANCELLED: s("Cancelled", "danger", Ban),
};

export const salesReturnStatus: Record<SalesReturnStatus, StatusStyle> = {
  DRAFT: s("Draft", "neutral", CircleDashed),
  CONFIRMED: s("Confirmed", "success", CheckCircle2),
  CANCELLED: s("Cancelled", "danger", Ban),
};

export const creditNoteStatus: Record<CreditNoteStatus, StatusStyle> = {
  DRAFT: s("Draft", "neutral", CircleDashed),
  ISSUED: s("Issued", "success", CheckCircle2),
  CANCELLED: s("Cancelled", "danger", Ban),
};

export const challanStatus: Record<string, StatusStyle> = {
  issued: s("Issued", "success", CheckCircle2),
  cancelled: s("Cancelled", "danger", Ban),
};

/** Status chip options with an "All" entry first. */
export function statusChips<S extends string>(map: Record<S, StatusStyle>): Array<{ value: S | ""; label: string }> {
  return [{ value: "", label: "All" }, ...(Object.keys(map) as S[]).map((value) => ({ value, label: map[value].label }))];
}

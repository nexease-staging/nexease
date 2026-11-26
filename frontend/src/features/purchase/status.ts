import { Ban, CheckCircle2, CircleDashed, PackageCheck, PieChart, Send, Truck, BookCheck } from "lucide-react";
import type { StatusStyle } from "@/components/list/list-kit";
import type { PurchaseOrderStatus } from "@/features/purchase-orders/types";
import type { PurchaseReturnStatus } from "@/features/purchase-returns/types";
import type { VendorBillStatus } from "@/features/vendor-bills/types";
import type { VendorDebitNoteStatus } from "@/features/vendor-debit-notes/types";

export const purchaseOrderStatus: Record<PurchaseOrderStatus, StatusStyle> = {
  DRAFT: { label: "Draft", tone: "neutral", icon: CircleDashed },
  CONFIRMED: { label: "Ordered", tone: "violet", icon: Send },
  PARTIALLY_RECEIVED: { label: "Part received", tone: "info", icon: Truck },
  RECEIVED: { label: "Received", tone: "success", icon: PackageCheck },
  CANCELLED: { label: "Cancelled", tone: "danger", icon: Ban },
};

export const vendorBillStatus: Record<VendorBillStatus, StatusStyle> = {
  DRAFT: { label: "Draft", tone: "neutral", icon: CircleDashed },
  POSTED: { label: "To pay", tone: "violet", icon: BookCheck },
  PARTIALLY_PAID: { label: "Part paid", tone: "info", icon: PieChart },
  PAID: { label: "Paid", tone: "success", icon: CheckCircle2 },
  CANCELLED: { label: "Cancelled", tone: "danger", icon: Ban },
};

export const purchaseReturnStatus: Record<PurchaseReturnStatus, StatusStyle> = {
  DRAFT: { label: "Draft", tone: "neutral", icon: CircleDashed },
  CONFIRMED: { label: "Confirmed", tone: "success", icon: CheckCircle2 },
  CANCELLED: { label: "Cancelled", tone: "danger", icon: Ban },
};

export const debitNoteStatus: Record<VendorDebitNoteStatus, StatusStyle> = {
  DRAFT: { label: "Draft", tone: "neutral", icon: CircleDashed },
  ISSUED: { label: "Issued", tone: "success", icon: CheckCircle2 },
  CANCELLED: { label: "Cancelled", tone: "danger", icon: Ban },
};

/** A posted or part-paid bill whose due date has passed. Dates compare in IST. */
export function isBillOverdue(bill: { status: VendorBillStatus; due_date: string | null; balance_due: string }, today = new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" })): boolean {
  return (bill.status === "POSTED" || bill.status === "PARTIALLY_PAID") && Number(bill.balance_due) > 0 && !!bill.due_date && bill.due_date.slice(0, 10) < today;
}

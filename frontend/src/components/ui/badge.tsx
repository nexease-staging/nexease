import type { ReactNode } from "react";
import { AlertTriangle, Ban, CheckCircle2, CircleDashed, PieChart, Send, type LucideIcon } from "lucide-react";
import type { InvoiceStatus } from "@/features/invoices/types";

export type Tone = "success" | "info" | "warning" | "danger" | "violet" | "neutral";

export function Badge({ tone = "neutral", icon: Icon, children }: { tone?: Tone; icon?: LucideIcon; children: ReactNode }) {
  return (
    <span className="nx-badge" data-tone={tone}>
      {Icon ? <Icon size={12} aria-hidden="true" /> : null}
      {children}
    </span>
  );
}

const invoiceStatus: Record<InvoiceStatus, { label: string; tone: Tone; icon: LucideIcon }> = {
  DRAFT: { label: "Draft", tone: "neutral", icon: CircleDashed },
  ISSUED: { label: "Issued", tone: "violet", icon: Send },
  PARTIALLY_PAID: { label: "Partially paid", tone: "info", icon: PieChart },
  PAID: { label: "Paid", tone: "success", icon: CheckCircle2 },
  CANCELLED: { label: "Cancelled", tone: "danger", icon: Ban },
};

export function InvoiceStatusBadge({ status, overdue = false }: { status: InvoiceStatus; overdue?: boolean }) {
  const s = invoiceStatus[status] ?? invoiceStatus.DRAFT;
  return (
    <span className="inline-flex flex-wrap items-center gap-1">
      <Badge tone={s.tone} icon={s.icon}>{s.label}</Badge>
      {overdue ? <Badge tone="warning" icon={AlertTriangle}>Overdue</Badge> : null}
    </span>
  );
}

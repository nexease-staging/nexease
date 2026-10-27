import type {
  CustomerSummary,
} from "@/features/customers/types";

import type {
  InvoiceStatus,
} from "@/features/invoices/types";

export interface CustomerReceivableSummary {
  customer: CustomerSummary;
  invoice_count: number;
  overdue_invoice_count: number;
  total_outstanding: string;
  total_overdue: string;
}

export interface AccountsReceivableSummary {
  as_of: string | null;
  invoice_count: number;
  overdue_invoice_count: number;
  customer_count: number;
  total_outstanding: string;
  total_current: string;
  total_overdue: string;
  customers:
    CustomerReceivableSummary[];
}

export interface AccountsReceivableData {
  accounts_receivable:
    AccountsReceivableSummary;
}

export type ReceivableAgingBucketKey =
  | "current"
  | "days_1_30"
  | "days_31_60"
  | "days_61_90"
  | "days_over_90";

export interface ReceivableAgingBucket {
  label: string;
  minimum_days: number | null;
  maximum_days: number | null;
  invoice_count: number;
  amount: string;
}

export interface ReceivableAgingInvoice {
  id: string;
  invoice_number: string;
  status: InvoiceStatus;
  invoice_date: string | null;
  due_date: string | null;
  total_amount: string;
  amount_paid: string;
  balance_due: string;
}

export interface ReceivableAgingItem {
  invoice:
    ReceivableAgingInvoice;
  customer: CustomerSummary;
  net_receivable: string;
  overdue_days: number;
  is_overdue: boolean;
  bucket:
    ReceivableAgingBucketKey;
}

export interface ReceivableAgingSummary {
  as_of: string | null;
  invoice_count: number;
  total_outstanding: string;
  buckets: Record<
    ReceivableAgingBucketKey,
    ReceivableAgingBucket
  >;
  invoices: ReceivableAgingItem[];
}

export interface ReceivableAgingData {
  aging: ReceivableAgingSummary;
}
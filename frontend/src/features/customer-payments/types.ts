import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

import type {
  CustomerSummary,
} from "@/features/customers/types";

import type {
  BankAccountLookup,
  InvoiceCreator,
  InvoicePaymentMethod,
  InvoiceStatus,
} from "@/features/invoices/types";

export interface PaymentInvoiceSummary {
  id: string;
  invoice_number: string;
  status: InvoiceStatus;
  invoice_date: string | null;
  total_amount: string;
  balance_due: string;
}

export interface CustomerPaymentAllocation {
  invoice: PaymentInvoiceSummary;
  amount: string;
}

export interface CustomerPaymentSummary {
  id: string;
  payment_number: string;
  customer: CustomerSummary;
  payment_date: string | null;
  amount: string;
  payment_method:
    InvoicePaymentMethod;
  bank_account:
    BankAccountLookup | null;
  reference_number: string | null;
  allocation_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface CustomerPaymentDetail
  extends CustomerPaymentSummary {
  allocations:
    CustomerPaymentAllocation[];
  notes: string | null;
  created_by: InvoiceCreator | null;
}

export interface CustomerPaymentListData {
  payments: CustomerPaymentSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface CustomerPaymentData {
  payment: CustomerPaymentDetail;
}

export interface CustomerPaymentListParameters {
  page?: number;
  page_size?: number;
  customer_id?: string;
  invoice_id?: string;
  bank_account_id?: string;
  payment_method?:
    InvoicePaymentMethod;
  search?: string;
  sort?: string;
}
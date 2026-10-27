import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

import type {
  CustomerSummary,
} from "@/features/customers/types";

export type InvoiceStatus =
  | "DRAFT"
  | "ISSUED"
  | "PARTIALLY_PAID"
  | "PAID"
  | "CANCELLED";

export type InvoicePaymentMethod =
  | "CASH"
  | "BANK_TRANSFER"
  | "UPI"
  | "CHEQUE"
  | "CARD"
  | "OTHER";

export interface InvoiceSalesOrderSummary {
  id: string;
  so_number: string;
  status: string;
}

export interface InvoiceProductSummary {
  id: string;
  sku: string;
  name: string;
  unit: string;
}

export interface InvoiceItem {
  description?: string;
  show_description?: boolean;
  product: InvoiceProductSummary;
  quantity: string;
  unit_price: string;
  tax_rate: string;
  discount: string;
  line_subtotal: string;
  line_tax: string;
  line_total: string;
}

export interface InvoiceCreator {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface InvoiceBillingAddress {
  name: string;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  pincode: string | null;
  gstin: string | null;
}

export interface InvoiceSummary {
  id: string;
  invoice_number: string;
  sales_order:
    InvoiceSalesOrderSummary | null;
  customer: CustomerSummary;
  status: InvoiceStatus;
  invoice_date: string | null;
  due_date: string | null;
  subtotal: string;
  tax_amount: string;
  discount_amount: string;
  total_amount: string;
  amount_paid: string;
  balance_due: string;
  item_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface InvoiceDetail
  extends InvoiceSummary {
  items: InvoiceItem[];
  billing: InvoiceBillingAddress;
  notes: string | null;
  created_by: InvoiceCreator | null;
  issued_at: string | null;
  paid_at: string | null;
  cancelled_at: string | null;
}

export interface InvoiceListData {
  invoices: InvoiceSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface InvoiceData {
  invoice: InvoiceDetail;
}

export interface InvoiceListParameters {
  page?: number;
  page_size?: number;
  customer_id?: string;
  sales_order_id?: string;
  status?: InvoiceStatus;
  search?: string;
  sort?: string;
}

export interface CreateInvoiceInput {
  sales_order_id: string;
  invoice_date?: string;
  due_date?: string;
  notes?: string;
}

export interface BankAccountLookup {
  id: string;
  account_name: string;
  account_type: string;
  bank_name: string | null;
  masked_account_number: string | null;
  currency: string;
  is_active: boolean;
}

export interface BankAccountLookupListData {
  bank_accounts: BankAccountLookup[];
  count: number;
}

export interface PaymentInvoiceSummary {
  id: string;
  invoice_number: string;
}

export interface CustomerPaymentAllocation {
  invoice: PaymentInvoiceSummary;
  amount: string;
}

export interface CustomerPaymentDetail {
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
  allocations:
    CustomerPaymentAllocation[];
  notes: string | null;
  created_by: InvoiceCreator | null;
  created_at: string | null;
}

export interface InvoicePaymentData {
  invoice: InvoiceDetail;
  payment: CustomerPaymentDetail;
}

export interface RecordInvoicePaymentInput {
  amount: string;
  payment_method:
    InvoicePaymentMethod;
  bank_account_id: string;
  payment_date?: string;
  reference_number?: string;
  notes?: string;
}
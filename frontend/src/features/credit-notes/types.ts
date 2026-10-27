import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

import type {
  CustomerSummary,
} from "@/features/customers/types";

import type {
  InvoiceStatus,
} from "@/features/invoices/types";

import type {
  SalesReturnStatus,
} from "@/features/sales-returns/types";

export type CreditNoteStatus =
  | "DRAFT"
  | "ISSUED"
  | "CANCELLED";

export interface CreditNoteProduct {
  id: string;
  sku: string;
  name: string;
  unit: string;
}

export interface CreditNoteItem {
  product: CreditNoteProduct;
  quantity: string;
  unit_price: string;
  tax_rate: string;
  discount: string;
  line_subtotal: string;
  line_tax: string;
  line_total: string;
}

export interface CreditNoteInvoice {
  id: string;
  invoice_number: string;
  status: InvoiceStatus;
}

export interface CreditNoteSalesReturn {
  id: string;
  return_number: string;
  status: SalesReturnStatus;
}

export interface CreditNoteCreator {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface CreditNoteSummary {
  id: string;
  credit_note_number: string;
  invoice: CreditNoteInvoice;
  sales_return:
    CreditNoteSalesReturn;
  customer: CustomerSummary;
  status: CreditNoteStatus;
  credit_note_date: string | null;
  subtotal: string;
  tax_amount: string;
  discount_amount: string;
  total_amount: string;
  applied_amount: string;
  remaining_credit: string;
  item_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface CreditNoteDetail
  extends CreditNoteSummary {
  items: CreditNoteItem[];
  reason: string | null;
  notes: string | null;
  created_by:
    CreditNoteCreator | null;
  issued_at: string | null;
  cancelled_at: string | null;
}

export interface CreditNoteListData {
  credit_notes:
    CreditNoteSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface CreditNoteData {
  credit_note: CreditNoteDetail;
}

export interface CreditNoteListParameters {
  page?: number;
  page_size?: number;
  customer_id?: string;
  invoice_id?: string;
  sales_return_id?: string;
  status?: CreditNoteStatus;
  search?: string;
  sort?: string;
}

export interface CreateCreditNoteInput {
  sales_return_id: string;
  credit_note_date?: string;
  reason?: string;
  notes?: string;
}
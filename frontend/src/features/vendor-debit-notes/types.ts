import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

import type {
  PurchaseOrderStatus,
} from "@/features/purchase-orders/types";

import type {
  PurchaseReturnStatus,
} from "@/features/purchase-returns/types";

import type {
  SupplierSummary,
} from "@/features/suppliers/types";

import type {
  VendorBillStatus,
} from "@/features/vendor-bills/types";

export type VendorDebitNoteStatus =
  | "DRAFT"
  | "ISSUED"
  | "CANCELLED";

export interface VendorDebitNoteProduct {
  id: string;
  sku: string;
  name: string;
  unit: string;
}

export interface VendorDebitNoteItem {
  product: VendorDebitNoteProduct;
  quantity: string;
  unit_price: string;
  tax_rate: string;
  discount: string;
  line_subtotal: string;
  line_tax: string;
  line_total: string;
}

export interface DebitNotePurchaseReturn {
  id: string;
  return_number: string;
  status: PurchaseReturnStatus;
  total_amount: string;
}

export interface DebitNoteVendorBill {
  id: string;
  bill_number: string;
  status: VendorBillStatus;
  total_amount: string;
  balance_due: string;
}

export interface DebitNotePurchaseOrder {
  id: string;
  po_number: string;
  status: PurchaseOrderStatus;
}

export interface VendorDebitNoteCreator {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface VendorDebitNoteSummary {
  id: string;
  debit_note_number: string;
  purchase_return:
    DebitNotePurchaseReturn;
  vendor_bill:
    DebitNoteVendorBill;
  purchase_order:
    DebitNotePurchaseOrder;
  supplier: SupplierSummary;
  status: VendorDebitNoteStatus;
  debit_note_date: string | null;
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

export interface VendorDebitNoteDetail
  extends VendorDebitNoteSummary {
  items: VendorDebitNoteItem[];
  reason: string | null;
  notes: string | null;
  created_by:
    VendorDebitNoteCreator | null;
  issued_at: string | null;
  cancelled_at: string | null;
}

export interface VendorDebitNoteListData {
  vendor_debit_notes:
    VendorDebitNoteSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface VendorDebitNoteData {
  vendor_debit_note:
    VendorDebitNoteDetail;
}

export interface VendorDebitNoteListParameters {
  page?: number;
  page_size?: number;
  supplier_id?: string;
  purchase_order_id?: string;
  purchase_return_id?: string;
  vendor_bill_id?: string;
  status?: VendorDebitNoteStatus;
  search?: string;
  sort?: string;
}

export interface CreateVendorDebitNoteInput {
  purchase_return_id: string;
  debit_note_date?: string;
  reason?: string;
  notes?: string;
}
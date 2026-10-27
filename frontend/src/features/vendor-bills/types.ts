import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

import type {
  SupplierSummary,
} from "@/features/suppliers/types";

export type VendorBillStatus =
  | "DRAFT"
  | "POSTED"
  | "PARTIALLY_PAID"
  | "PAID"
  | "CANCELLED";

export type SupplierPaymentMethod =
  | "CASH"
  | "BANK_TRANSFER"
  | "CHEQUE"
  | "UPI"
  | "CARD"
  | "OTHER";

export interface VendorBillPurchaseOrder {
  id: string;
  po_number: string;
  status: string;
}

export interface VendorBillProduct {
  id: string;
  sku: string;
  name: string;
  unit: string;
}

export interface VendorBillItem {
  product: VendorBillProduct;
  quantity: string;
  unit_price: string;
  tax_rate: string;
  discount: string;
  line_subtotal: string;
  line_tax: string;
  line_total: string;
}

export interface VendorBillCreator {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface VendorBillSupplierSnapshot {
  name: string;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  pincode: string | null;
  gstin: string | null;
}

export interface VendorBillSummary {
  id: string;
  bill_number: string;
  supplier_invoice_number:
    string | null;
  purchase_order:
    VendorBillPurchaseOrder | null;
  supplier: SupplierSummary;
  status: VendorBillStatus;
  bill_date: string | null;
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

export interface VendorBillDetail
  extends VendorBillSummary {
  items: VendorBillItem[];
  supplier_snapshot:
    VendorBillSupplierSnapshot;
  notes: string | null;
  created_by:
    VendorBillCreator | null;
  posted_at: string | null;
  paid_at: string | null;
  cancelled_at: string | null;
}

export interface VendorBillListData {
  vendor_bills:
    VendorBillSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface VendorBillData {
  vendor_bill:
    VendorBillDetail;
}

export interface VendorBillListParameters {
  page?: number;
  page_size?: number;
  supplier_id?: string;
  purchase_order_id?: string;
  status?: VendorBillStatus;
  search?: string;
  sort?: string;
}

export interface CreateVendorBillInput {
  purchase_order_id: string;
  supplier_invoice_number?: string;
  bill_date?: string;
  due_date?: string;
  notes?: string;
}

export interface VendorBillBankAccount {
  id: string;
  account_name: string;
  account_type: string;
  bank_name: string | null;
  masked_account_number:
    string | null;
  currency: string;
  is_active: boolean;
}

export interface VendorBillBankAccountListData {
  bank_accounts:
    VendorBillBankAccount[];
}

export interface SupplierPaymentBillSummary {
  id: string;
  bill_number: string;
  status: VendorBillStatus;
  bill_date: string | null;
  total_amount: string;
  balance_due: string;
}

export interface SupplierPaymentAllocation {
  vendor_bill:
    SupplierPaymentBillSummary;
  amount: string;
}

export interface SupplierPaymentDetail {
  id: string;
  payment_number: string;
  supplier: SupplierSummary;
  payment_date: string | null;
  amount: string;
  payment_method:
    SupplierPaymentMethod;
  bank_account:
    VendorBillBankAccount | null;
  reference_number: string | null;
  allocation_count: number;
  allocations:
    SupplierPaymentAllocation[];
  notes: string | null;
  created_by:
    VendorBillCreator | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface VendorBillPaymentData {
  vendor_bill:
    VendorBillDetail;
  payment:
    SupplierPaymentDetail;
}

export interface RecordVendorBillPaymentInput {
  amount: string;
  payment_method:
    SupplierPaymentMethod;
  bank_account_id: string;
  payment_date?: string;
  reference_number?: string;
  notes?: string;
}

export interface AccountsPayableSummary {
  bill_count: number;
  supplier_count: number;
  total_outstanding: string;
  vendor_bills:
    VendorBillSummary[];
}

export interface AccountsPayableData {
  accounts_payable:
    AccountsPayableSummary;
}
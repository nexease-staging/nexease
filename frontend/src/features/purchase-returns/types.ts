import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

import type {
  PurchaseOrderStatus,
} from "@/features/purchase-orders/types";

import type {
  SupplierSummary,
} from "@/features/suppliers/types";

import type {
  VendorBillStatus,
} from "@/features/vendor-bills/types";

import type {
  WarehouseSummary,
} from "@/features/warehouses/types";

export type PurchaseReturnStatus =
  | "DRAFT"
  | "CONFIRMED"
  | "CANCELLED";

export interface PurchaseReturnProduct {
  id: string;
  sku: string;
  name: string;
  unit: string;
}

export interface PurchaseReturnItem {
  product: PurchaseReturnProduct;
  quantity: string;
  unit_price: string;
  tax_rate: string;
  discount: string;
  line_subtotal: string;
  line_tax: string;
  line_total: string;
  reason: string | null;
}

export interface PurchaseReturnPurchaseOrder {
  id: string;
  po_number: string;
  status: PurchaseOrderStatus;
}

export interface PurchaseReturnVendorBill {
  id: string;
  bill_number: string;
  status: VendorBillStatus;
  total_amount: string;
  balance_due: string;
}

export interface PurchaseReturnCreator {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface PurchaseReturnSummary {
  id: string;
  return_number: string;
  purchase_order:
    PurchaseReturnPurchaseOrder;
  vendor_bill:
    PurchaseReturnVendorBill;
  supplier: SupplierSummary;
  warehouse: WarehouseSummary;
  status: PurchaseReturnStatus;
  return_date: string | null;
  subtotal: string;
  tax_amount: string;
  discount_amount: string;
  total_amount: string;
  item_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface PurchaseReturnDetail
  extends PurchaseReturnSummary {
  items: PurchaseReturnItem[];
  reason: string | null;
  notes: string | null;
  created_by:
    PurchaseReturnCreator | null;
  confirmed_at: string | null;
  cancelled_at: string | null;
}

export interface PurchaseReturnListData {
  purchase_returns:
    PurchaseReturnSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface PurchaseReturnData {
  purchase_return:
    PurchaseReturnDetail;
}

export interface PurchaseReturnListParameters {
  page?: number;
  page_size?: number;
  supplier_id?: string;
  purchase_order_id?: string;
  vendor_bill_id?: string;
  warehouse_id?: string;
  status?: PurchaseReturnStatus;
  search?: string;
  sort?: string;
}

export interface PurchaseReturnItemInput {
  product_id: string;
  quantity: string;
  reason?: string;
}

export interface CreatePurchaseReturnInput {
  purchase_order_id: string;
  vendor_bill_id: string;
  warehouse_id: string;
  return_date?: string;
  items: PurchaseReturnItemInput[];
  reason?: string;
  notes?: string;
}
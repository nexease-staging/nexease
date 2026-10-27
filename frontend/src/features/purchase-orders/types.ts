import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

import type {
  SupplierSummary,
} from "@/features/suppliers/types";

export type PurchaseOrderStatus =
  | "DRAFT"
  | "CONFIRMED"
  | "PARTIALLY_RECEIVED"
  | "RECEIVED"
  | "CANCELLED";

export interface PurchaseOrderProductSummary {
  id: string;
  sku: string;
  name: string;
  unit: string;
  is_active: boolean;
}

export interface PurchaseOrderItem {
  product:
    PurchaseOrderProductSummary;
  quantity: string;
  received_quantity: string;
  remaining_quantity: string;
  unit_price: string;
  tax_rate: string;
  discount: string;
  subtotal: string;
  tax_amount: string;
  total: string;
}

export interface PurchaseOrderCreator {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface PurchaseOrderSummary {
  id: string;
  po_number: string;
  supplier: SupplierSummary;
  status: PurchaseOrderStatus;
  order_date: string;
  expected_delivery_date:
    string | null;
  subtotal: string;
  tax_amount: string;
  discount_amount: string;
  total_amount: string;
  item_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface PurchaseOrderDetail
  extends PurchaseOrderSummary {
  items: PurchaseOrderItem[];
  notes: string | null;
  created_by:
    PurchaseOrderCreator | null;
  confirmed_at: string | null;
  cancelled_at: string | null;
}

export interface PurchaseOrderListData {
  purchase_orders:
    PurchaseOrderSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface PurchaseOrderData {
  purchase_order:
    PurchaseOrderDetail;
}

export interface PurchaseOrderListParameters {
  page?: number;
  page_size?: number;
  supplier_id?: string;
  status?: PurchaseOrderStatus;
  search?: string;
  sort?: string;
}

export interface PurchaseOrderLineInput {
  product_id: string;
  quantity: string;
  unit_price: string;
  tax_rate?: string;
  discount?: string;
}

export interface CreatePurchaseOrderInput {
  supplier_id: string;
  order_date: string;
  expected_delivery_date?: string;
  items: PurchaseOrderLineInput[];
  notes?: string;
}

export type UpdatePurchaseOrderInput =
  Partial<CreatePurchaseOrderInput>;
import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

import type {
  CustomerSummary,
} from "@/features/customers/types";

import type {
  WarehouseSummary,
} from "@/features/warehouses/types";

export type SalesOrderStatus =
  | "DRAFT"
  | "CONFIRMED"
  | "PARTIALLY_FULFILLED"
  | "FULFILLED"
  | "CANCELLED";

export interface SalesOrderProductSummary {
  id: string;
  sku: string;
  name: string;
  unit: string;
  is_active: boolean;
}

export interface SalesOrderItem {
  product: SalesOrderProductSummary;
  quantity: string;
  fulfilled_quantity: string;
  remaining_quantity: string;
  unit_price: string;
  tax_rate: string;
  discount: string;
  line_subtotal: string;
  line_tax: string;
  line_total: string;
}

export interface SalesOrderCreator {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface SalesOrderSummary {
  id: string;
  so_number: string;
  customer: CustomerSummary;
  warehouse: WarehouseSummary;
  status: SalesOrderStatus;
  order_date: string | null;
  expected_delivery_date: string | null;
  subtotal: string;
  tax_amount: string;
  discount_amount: string;
  total_amount: string;
  item_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface SalesOrderDetail
  extends SalesOrderSummary {
  items: SalesOrderItem[];
  notes: string | null;
  created_by: SalesOrderCreator | null;
  confirmed_at: string | null;
  fulfilled_at: string | null;
  cancelled_at: string | null;
}

export interface SalesOrderListData {
  sales_orders: SalesOrderSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface SalesOrderData {
  sales_order: SalesOrderDetail;
}

export interface SalesOrderListParameters {
  page?: number;
  page_size?: number;
  customer_id?: string;
  warehouse_id?: string;
  status?: SalesOrderStatus;
  search?: string;
  sort?: string;
}

export interface SalesOrderLineInput {
  product_id: string;
  quantity: string;
  unit_price: string;
  tax_rate?: string;
  discount?: string;
}

export interface CreateSalesOrderInput {
  customer_id: string;
  warehouse_id: string;
  order_date: string;
  expected_delivery_date?: string;
  items: SalesOrderLineInput[];
  notes?: string;
}

export type UpdateSalesOrderInput =
  Partial<CreateSalesOrderInput>;

export interface FulfillSalesOrderLineInput {
  product_id: string;
  quantity: string;
}

export interface FulfillSalesOrderInput {
  items: FulfillSalesOrderLineInput[];
  notes?: string;
}
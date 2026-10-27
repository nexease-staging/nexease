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
  SalesOrderStatus,
} from "@/features/sales-orders/types";

import type {
  WarehouseSummary,
} from "@/features/warehouses/types";

export type SalesReturnStatus =
  | "DRAFT"
  | "CONFIRMED"
  | "CANCELLED";

export interface SalesReturnProduct {
  id: string;
  sku: string;
  name: string;
  unit: string;
}

export interface SalesReturnItem {
  product: SalesReturnProduct;
  quantity: string;
  unit_price: string;
  tax_rate: string;
  discount: string;
  line_subtotal: string;
  line_tax: string;
  line_total: string;
  reason: string | null;
}

export interface SalesReturnSalesOrder {
  id: string;
  so_number: string;
  status: SalesOrderStatus;
}

export interface SalesReturnInvoice {
  id: string;
  invoice_number: string;
  status: InvoiceStatus;
}

export interface SalesReturnCreator {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface SalesReturnSummary {
  id: string;
  return_number: string;
  sales_order:
    SalesReturnSalesOrder;
  invoice: SalesReturnInvoice;
  customer: CustomerSummary;
  warehouse: WarehouseSummary;
  status: SalesReturnStatus;
  return_date: string | null;
  subtotal: string;
  tax_amount: string;
  discount_amount: string;
  total_amount: string;
  item_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface SalesReturnDetail
  extends SalesReturnSummary {
  items: SalesReturnItem[];
  reason: string | null;
  notes: string | null;
  created_by:
    SalesReturnCreator | null;
  confirmed_at: string | null;
  cancelled_at: string | null;
}

export interface SalesReturnListData {
  sales_returns:
    SalesReturnSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface SalesReturnData {
  sales_return:
    SalesReturnDetail;
}

export interface SalesReturnListParameters {
  page?: number;
  page_size?: number;
  customer_id?: string;
  sales_order_id?: string;
  invoice_id?: string;
  warehouse_id?: string;
  status?: SalesReturnStatus;
  search?: string;
  sort?: string;
}

export interface SalesReturnItemInput {
  product_id: string;
  quantity: string;
  reason?: string;
}

export interface CreateSalesReturnInput {
  invoice_id: string;
  return_date?: string;
  items: SalesReturnItemInput[];
  reason?: string;
  notes?: string;
}
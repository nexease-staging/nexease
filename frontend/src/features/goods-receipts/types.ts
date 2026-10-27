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

export interface GoodsReceiptProduct {
  id: string;
  sku: string;
  name: string;
  unit: string;
}

export interface GoodsReceiptItem {
  product: GoodsReceiptProduct;
  quantity_received: string;
}

export interface GoodsReceiptPurchaseOrder {
  id: string;
  po_number: string;
  status: PurchaseOrderStatus;
}

export interface GoodsReceiptWarehouse {
  id: string;
  code: string;
  name: string;
}

export interface GoodsReceiptReceiver {
  id: string;
  email: string;
}

export interface GoodsReceiptSummary {
  id: string;
  grn_number: string;
  purchase_order:
    GoodsReceiptPurchaseOrder;
  supplier: SupplierSummary;
  warehouse: GoodsReceiptWarehouse;
  item_count: number;
  received_at: string | null;
  created_at: string | null;
}

export interface GoodsReceiptDetail
  extends GoodsReceiptSummary {
  items: GoodsReceiptItem[];
  notes: string | null;
  received_by:
    GoodsReceiptReceiver | null;
}

export interface GoodsReceiptListData {
  goods_receipts:
    GoodsReceiptSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface GoodsReceiptData {
  goods_receipt:
    GoodsReceiptDetail;
}

export interface GoodsReceiptListParameters {
  page?: number;
  page_size?: number;
  search?: string;
  sort?: string;
}

export interface ReceiveGoodsItemInput {
  product_id: string;
  quantity_received: string;
}

export interface CreateGoodsReceiptInput {
  purchase_order_id: string;
  warehouse_id: string;
  items: ReceiveGoodsItemInput[];
  notes?: string;
}
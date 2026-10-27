import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

import type {
  WarehouseSummary,
} from "@/features/warehouses/types";

export interface InventoryProductSummary {
  id: string;
  sku: string;
  name: string;
  unit: string;
  is_active?: boolean;
}

export interface InventorySummary {
  id: string;
  product: InventoryProductSummary;
  warehouse: WarehouseSummary;
  quantity: string;
  reserved_quantity: string;
  available_quantity: string;
}

export interface InventoryDetail
  extends InventorySummary {
  created_at: string | null;
  updated_at: string | null;
}

export interface InventoryListData {
  inventory: InventorySummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface InventoryData {
  inventory: InventoryDetail;
}

export interface InventoryListParameters {
  page?: number;
  page_size?: number;
  product_id?: string;
  warehouse_id?: string;
  sort?: string;
}

export interface CreateInventoryInput {
  product_id: string;
  warehouse_id: string;
  quantity?: string;
}

export interface AdjustInventoryInput {
  quantity_change: string;
  reference_type?: string;
  reference_id?: string;
  notes?: string;
}

export interface ProductLookupSummary {
  id: string;
  sku: string;
  name: string;
  unit: string;
  is_active: boolean;
}

export interface ProductLookupListData {
  products: ProductLookupSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface ProductLookupParameters {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  sort?: string;
}

export type StockMovementType =
  | "OPENING_STOCK"
  | "STOCK_IN"
  | "STOCK_OUT"
  | "ADJUSTMENT_IN"
  | "ADJUSTMENT_OUT"
  | "RESERVATION"
  | "RESERVATION_RELEASE"
  | "TRANSFER_OUT"
  | "TRANSFER_IN"
  | "SALES_RETURN"
  | "PURCHASE_RETURN";

export interface StockMovementReference {
  type: string | null;
  id: string | null;
}

export interface StockMovementCreator {
  id: string;
  email: string;
}

export interface StockMovementSummary {
  id: string;
  inventory_id: string;
  movement_type: StockMovementType;
  quantity: string;
  quantity_before: string;
  quantity_after: string;
  reserved_before: string;
  reserved_after: string;
  product: InventoryProductSummary;
  warehouse: WarehouseSummary;
  reference: StockMovementReference;
  created_by: StockMovementCreator | null;
  created_at: string | null;
}

export interface StockMovementDetail
  extends StockMovementSummary {
  notes: string | null;
}

export interface StockMovementListData {
  movements: StockMovementSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface StockMovementData {
  movement: StockMovementDetail;
}

export interface StockMovementListParameters {
  page?: number;
  page_size?: number;
  inventory_id?: string;
  product_id?: string;
  warehouse_id?: string;
  movement_type?: StockMovementType;
  reference_type?: string;
  reference_id?: string;
  search?: string;
  sort?: string;
}

export type StockTransferStatus =
  | "DRAFT"
  | "COMPLETED"
  | "CANCELLED";

export interface StockTransferSummary {
  id: string;
  transfer_number: string;
  product: InventoryProductSummary;
  source_warehouse: WarehouseSummary;
  destination_warehouse: WarehouseSummary;
  quantity: string;
  status: StockTransferStatus;
  created_by: StockMovementCreator | null;
  created_at: string | null;
  completed_at: string | null;
}

export interface StockTransferDetail
  extends StockTransferSummary {
  source_inventory_id: string;
  destination_inventory_id: string;
  notes: string | null;
}

export interface StockTransferListData {
  transfers: StockTransferSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface StockTransferData {
  transfer: StockTransferDetail;
}

export interface StockTransferListParameters {
  page?: number;
  page_size?: number;
  product_id?: string;
  source_warehouse_id?: string;
  destination_warehouse_id?: string;
  status?: StockTransferStatus;
  search?: string;
  sort?: string;
}

export interface CreateStockTransferInput {
  product_id: string;
  source_warehouse_id: string;
  destination_warehouse_id: string;
  quantity: string;
  notes?: string;
}
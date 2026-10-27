import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

export interface WarehouseSummary {
  id: string;
  code: string;
  name: string;
  city: string | null;
  state: string | null;
  country: string | null;
  is_active: boolean;
}

export interface WarehouseDetail
  extends WarehouseSummary {
  address: string | null;
  pincode: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface WarehouseListData {
  warehouses: WarehouseSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface WarehouseData {
  warehouse: WarehouseDetail;
}

export interface WarehouseListParameters {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  country?: string;
  state?: string;
  city?: string;
  sort?: string;
}

export interface CreateWarehouseInput {
  name: string;
  code: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  pincode?: string;
}

export type UpdateWarehouseInput =
  Partial<CreateWarehouseInput>;
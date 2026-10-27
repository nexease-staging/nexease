import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

export interface SupplierSummary {
  id: string;
  code: string;
  name: string;
  email: string | null;
  phone: string | null;
  gstin: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  is_active: boolean;
}

export interface SupplierDetail
  extends SupplierSummary {
  address: string | null;
  pincode: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface SupplierListData {
  suppliers: SupplierSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface SupplierData {
  supplier: SupplierDetail;
}

export interface SupplierListParameters {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  sort?: string;
}

export interface CreateSupplierInput {
  code: string;
  name: string;
  email?: string;
  phone?: string;
  gstin?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  pincode?: string;
}

export interface UpdateSupplierInput {
  name?: string;
  email?: string;
  phone?: string;
  gstin?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  pincode?: string;
}
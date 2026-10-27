import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

export interface CustomerSummary {
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

export interface CustomerDetail
  extends CustomerSummary {
  billing_address: string | null;
  shipping_address: string | null;
  pincode: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface CustomerListData {
  customers: CustomerSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface CustomerData {
  customer: CustomerDetail;
}

export interface CustomerListParameters {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  sort?: string;
}

export interface CreateCustomerInput {
  code: string;
  name: string;
  email?: string;
  phone?: string;
  gstin?: string;
  billing_address?: string;
  shipping_address?: string;
  city?: string;
  state?: string;
  country?: string;
  pincode?: string;
}

export interface UpdateCustomerInput {
  name?: string;
  email?: string;
  phone?: string;
  gstin?: string;
  billing_address?: string;
  shipping_address?: string;
  city?: string;
  state?: string;
  country?: string;
  pincode?: string;
}
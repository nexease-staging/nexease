import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

export interface ProductCategorySummary {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
}

export interface ProductCategoryDetail
  extends ProductCategorySummary {
  created_at: string | null;
  updated_at: string | null;
}

export interface ProductSummary {
  id: string;
  sku: string;
  name: string;
  category: ProductCategorySummary;
  brand: string | null;
  unit: string;
  cost_price: string;
  selling_price: string;
  barcode: string | null;
  is_active: boolean;
}

export interface ProductDetail
  extends ProductSummary {
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ProductListData {
  products: ProductSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface ProductData {
  product: ProductDetail;
}

export interface ProductCategoryListData {
  categories: ProductCategorySummary[];
  count: number;
}

export interface ProductListParameters {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  sort?: string;
}

export interface CreateProductInput {
  sku: string;
  name: string;
  category_id: string;
  unit: string;
  description?: string;
  brand?: string;
  cost_price?: string;
  selling_price?: string;
  barcode?: string;
}

export interface UpdateProductInput {
  sku?: string;
  name?: string;
  category_id?: string;
  unit?: string;
  description?: string;
  brand?: string;
  cost_price?: string;
  selling_price?: string;
  barcode?: string;
}
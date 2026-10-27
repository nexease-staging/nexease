export interface CategorySummary {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
}

export interface CategoryDetail extends CategorySummary {
  created_at: string;
  updated_at: string;
}

export interface CategoryListResponse {
  categories: CategorySummary[];
  count: number;
}

export interface CategoryDetailResponse {
  category: CategoryDetail;
}

export interface CreateCategoryPayload {
  name: string;
  description?: string;
}

export interface UpdateCategoryPayload {
  name?: string;
  description?: string;
}
import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CategoryDetail,
  CategoryDetailResponse,
  CategoryListResponse,
  CreateCategoryPayload,
  UpdateCategoryPayload,
} from "@/features/categories/types";


export async function listCategories():
  Promise<CategoryListResponse> {
  const response =
    await apiRequest<CategoryListResponse>(
      "/categories/",
    );

  return response.data;
}


export async function getCategory(
  categoryId: string,
): Promise<CategoryDetail> {
  const response =
    await apiRequest<CategoryDetailResponse>(
      `/categories/${categoryId}/`,
    );

  return response.data.category;
}


export async function createCategory(
  payload: CreateCategoryPayload,
): Promise<CategoryDetail> {
  const response =
    await apiRequest<CategoryDetailResponse>(
      "/categories/",
      {
        method: "POST",
        body: payload,
      },
    );

  return response.data.category;
}


export async function updateCategory(
  categoryId: string,
  payload: UpdateCategoryPayload,
): Promise<CategoryDetail> {
  const response =
    await apiRequest<CategoryDetailResponse>(
      `/categories/${categoryId}/`,
      {
        method: "PATCH",
        body: payload,
      },
    );

  return response.data.category;
}


export async function activateCategory(
  categoryId: string,
): Promise<CategoryDetail> {
  const response =
    await apiRequest<CategoryDetailResponse>(
      `/categories/${categoryId}/activate/`,
      {
        method: "POST",
      },
    );

  return response.data.category;
}


export async function deactivateCategory(
  categoryId: string,
): Promise<CategoryDetail> {
  const response =
    await apiRequest<CategoryDetailResponse>(
      `/categories/${categoryId}/deactivate/`,
      {
        method: "POST",
      },
    );

  return response.data.category;
}
import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CreateProductInput,
  ProductCategoryListData,
  ProductData,
  ProductDetail,
  ProductListData,
  ProductListParameters,
  UpdateProductInput,
} from "@/features/products/types";

type QueryValue =
  | string
  | number
  | boolean
  | undefined;

function buildQuery(
  parameters: Record<
    string,
    QueryValue
  >,
): string {
  const searchParameters =
    new URLSearchParams();

  for (
    const [
      key,
      value,
    ]
    of Object.entries(
      parameters,
    )
  ) {
    if (
      value === undefined
      ||
      value === ""
    ) {
      continue;
    }

    searchParameters.set(
      key,
      String(value),
    );
  }

  const query =
    searchParameters.toString();

  return query
    ? `?${query}`
    : "";
}

export async function listProducts(
  parameters:
    ProductListParameters = {},
): Promise<ProductListData> {
  const response =
    await apiRequest<ProductListData>(
      (
        "/products/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          search:
            parameters.search,
          is_active:
            parameters.is_active,
          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}

export async function getProduct(
  productId: string,
): Promise<ProductDetail> {
  const response =
    await apiRequest<ProductData>(
      `/products/${productId}/`,
    );

  return response.data.product;
}

export async function createProduct(
  input: CreateProductInput,
): Promise<ProductDetail> {
  const response =
    await apiRequest<ProductData>(
      "/products/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.product;
}

export async function updateProduct(
  productId: string,
  input: UpdateProductInput,
): Promise<ProductDetail> {
  const response =
    await apiRequest<ProductData>(
      `/products/${productId}/`,
      {
        method: "PATCH",
        body: input,
      },
    );

  return response.data.product;
}

export async function activateProduct(
  productId: string,
): Promise<ProductDetail> {
  const response =
    await apiRequest<ProductData>(
      `/products/${productId}/activate/`,
      {
        method: "POST",
      },
    );

  return response.data.product;
}

export async function deactivateProduct(
  productId: string,
): Promise<ProductDetail> {
  const response =
    await apiRequest<ProductData>(
      `/products/${productId}/deactivate/`,
      {
        method: "POST",
      },
    );

  return response.data.product;
}

export async function listProductCategories():
  Promise<ProductCategoryListData> {
  const response =
    await apiRequest<ProductCategoryListData>(
      "/categories/",
    );

  return response.data;
}
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  activateProduct,
  createProduct,
  deactivateProduct,
  getProduct,
  listProductCategories,
  listProducts,
  updateProduct,
} from "@/features/products/api";

import {
  productQueryKeys,
} from "@/features/products/query-keys";

import type {
  CreateProductInput,
  ProductListParameters,
  UpdateProductInput,
} from "@/features/products/types";

export function useProductList(
  parameters:
    ProductListParameters,
  enabled = true,
) {
  return useQuery({
    queryKey:
      productQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listProducts(
        parameters,
      ),

    enabled,

    staleTime: 15_000,
  });
}

export function useProduct(
  productId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      productQueryKeys.detail(
        productId,
      ),

    queryFn: () =>
      getProduct(
        productId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        productId,
      ),

    staleTime: 30_000,
  });
}

export function useProductCategories() {
  return useQuery({
    queryKey:
      productQueryKeys.categories(),

    queryFn:
      listProductCategories,

    staleTime: 60_000,
  });
}

export function useCreateProduct() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateProductInput,
    ) =>
      createProduct(
        input,
      ),

    onSuccess: async (
      product,
    ) => {
      queryClient.setQueryData(
        productQueryKeys.detail(
          product.id,
        ),
        product,
      );

      await queryClient.invalidateQueries({
        queryKey:
          productQueryKeys.lists(),
      });
    },
  });
}

export function useUpdateProduct() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      productId,
      input,
    }: {
      productId: string;
      input: UpdateProductInput;
    }) =>
      updateProduct(
        productId,
        input,
      ),

    onSuccess: async (
      product,
    ) => {
      queryClient.setQueryData(
        productQueryKeys.detail(
          product.id,
        ),
        product,
      );

      await queryClient.invalidateQueries({
        queryKey:
          productQueryKeys.lists(),
      });
    },
  });
}

export function useActivateProduct() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      productId: string,
    ) =>
      activateProduct(
        productId,
      ),

    onSuccess: async (
      product,
    ) => {
      queryClient.setQueryData(
        productQueryKeys.detail(
          product.id,
        ),
        product,
      );

      await queryClient.invalidateQueries({
        queryKey:
          productQueryKeys.lists(),
      });
    },
  });
}

export function useDeactivateProduct() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      productId: string,
    ) =>
      deactivateProduct(
        productId,
      ),

    onSuccess: async (
      product,
    ) => {
      queryClient.setQueryData(
        productQueryKeys.detail(
          product.id,
        ),
        product,
      );

      await queryClient.invalidateQueries({
        queryKey:
          productQueryKeys.lists(),
      });
    },
  });
}
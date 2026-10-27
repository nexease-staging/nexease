import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  activateCategory,
  createCategory,
  deactivateCategory,
  getCategory,
  listCategories,
  updateCategory,
} from "@/features/categories/api";

import { categoryQueryKeys } from "@/features/categories/query-keys";

import type {
  CreateCategoryPayload,
  UpdateCategoryPayload,
} from "@/features/categories/types";

export function useCategories() {
  return useQuery({
    queryKey: categoryQueryKeys.list(),
    queryFn: listCategories,
  });
}

export function useCategory(categoryId: string) {
  return useQuery({
    queryKey: categoryQueryKeys.detail(categoryId),
    queryFn: () => getCategory(categoryId),
    enabled: Boolean(categoryId),
  });
}

export function useCreateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateCategoryPayload) =>
      createCategory(payload),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: categoryQueryKeys.list(),
      });
    },
  });
}

export function useUpdateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      categoryId,
      payload,
    }: {
      categoryId: string;
      payload: UpdateCategoryPayload;
    }) => updateCategory(categoryId, payload),

    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: categoryQueryKeys.list(),
      });

      queryClient.invalidateQueries({
        queryKey: categoryQueryKeys.detail(
          variables.categoryId,
        ),
      });
    },
  });
}

export function useActivateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: activateCategory,

    onSuccess: (_data, categoryId) => {
      queryClient.invalidateQueries({
        queryKey: categoryQueryKeys.list(),
      });

      queryClient.invalidateQueries({
        queryKey: categoryQueryKeys.detail(categoryId),
      });
    },
  });
}

export function useDeactivateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deactivateCategory,

    onSuccess: (_data, categoryId) => {
      queryClient.invalidateQueries({
        queryKey: categoryQueryKeys.list(),
      });

      queryClient.invalidateQueries({
        queryKey: categoryQueryKeys.detail(categoryId),
      });
    },
  });
}
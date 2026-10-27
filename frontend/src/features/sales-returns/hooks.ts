import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  cancelSalesReturn,
  confirmSalesReturn,
  createSalesReturn,
  getSalesReturn,
  listSalesReturns,
} from "@/features/sales-returns/api";

import {
  salesReturnQueryKeys,
} from "@/features/sales-returns/query-keys";

import type {
  CreateSalesReturnInput,
  SalesReturnListParameters,
} from "@/features/sales-returns/types";

export function useSalesReturnList(
  parameters:
    SalesReturnListParameters,
) {
  return useQuery({
    queryKey:
      salesReturnQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listSalesReturns(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useSalesReturn(
  salesReturnId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      salesReturnQueryKeys.detail(
        salesReturnId,
      ),

    queryFn: () =>
      getSalesReturn(
        salesReturnId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        salesReturnId,
      ),

    staleTime: 30_000,
  });
}

export function useCreateSalesReturn() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateSalesReturnInput,
    ) =>
      createSalesReturn(
        input,
      ),

    onSuccess: async (
      salesReturn,
    ) => {
      queryClient.setQueryData(
        salesReturnQueryKeys.detail(
          salesReturn.id,
        ),
        salesReturn,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            salesReturnQueryKeys
            .lists(),
        });
    },
  });
}

export function useConfirmSalesReturn() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      salesReturnId: string,
    ) =>
      confirmSalesReturn(
        salesReturnId,
      ),

    onSuccess: async (
      salesReturn,
    ) => {
      queryClient.setQueryData(
        salesReturnQueryKeys.detail(
          salesReturn.id,
        ),
        salesReturn,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            salesReturnQueryKeys
            .lists(),
        });
    },
  });
}

export function useCancelSalesReturn() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      salesReturnId: string,
    ) =>
      cancelSalesReturn(
        salesReturnId,
      ),

    onSuccess: async (
      salesReturn,
    ) => {
      queryClient.setQueryData(
        salesReturnQueryKeys.detail(
          salesReturn.id,
        ),
        salesReturn,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            salesReturnQueryKeys
            .lists(),
        });
    },
  });
}
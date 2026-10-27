"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  cancelSalesOrder,
  confirmSalesOrder,
  createSalesOrder,
  fulfillSalesOrder,
  getSalesOrder,
  listSalesOrders,
  updateSalesOrder,
} from "@/features/sales-orders/api";

import {
  salesOrderQueryKeys,
} from "@/features/sales-orders/query-keys";

import {
  inventoryQueryKeys,
  stockMovementQueryKeys,
} from "@/features/inventory/query-keys";

import type {
  CreateSalesOrderInput,
  FulfillSalesOrderInput,
  SalesOrderListParameters,
  UpdateSalesOrderInput,
} from "@/features/sales-orders/types";

export function useSalesOrderList(
  parameters:
    SalesOrderListParameters,
) {
  return useQuery({
    queryKey:
      salesOrderQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listSalesOrders(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useSalesOrder(
  salesOrderId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      salesOrderQueryKeys.detail(
        salesOrderId,
      ),

    queryFn: () =>
      getSalesOrder(
        salesOrderId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        salesOrderId
      ),

    staleTime: 15_000,
  });
}

export function useCreateSalesOrder() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateSalesOrderInput,
    ) =>
      createSalesOrder(
        input,
      ),

    onSuccess: async (
      salesOrder,
    ) => {
      queryClient.setQueryData(
        salesOrderQueryKeys.detail(
          salesOrder.id,
        ),
        salesOrder,
      );

      await queryClient.invalidateQueries({
        queryKey:
          salesOrderQueryKeys.lists(),
      });
    },
  });
}

export function useUpdateSalesOrder() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      salesOrderId,
      input,
    }: {
      salesOrderId: string;
      input: UpdateSalesOrderInput;
    }) =>
      updateSalesOrder(
        salesOrderId,
        input,
      ),

    onSuccess: async (
      salesOrder,
    ) => {
      queryClient.setQueryData(
        salesOrderQueryKeys.detail(
          salesOrder.id,
        ),
        salesOrder,
      );

      await queryClient.invalidateQueries({
        queryKey:
          salesOrderQueryKeys.lists(),
      });
    },
  });
}

export function useConfirmSalesOrder() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      salesOrderId: string,
    ) =>
      confirmSalesOrder(
        salesOrderId,
      ),

    onSuccess: async (
      salesOrder,
    ) => {
      queryClient.setQueryData(
        salesOrderQueryKeys.detail(
          salesOrder.id,
        ),
        salesOrder,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            salesOrderQueryKeys.lists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            inventoryQueryKeys.lists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            stockMovementQueryKeys
            .lists(),
        }),
      ]);
    },
  });
}

export function useCancelSalesOrder() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      salesOrderId: string,
    ) =>
      cancelSalesOrder(
        salesOrderId,
      ),

    onSuccess: async (
      salesOrder,
    ) => {
      queryClient.setQueryData(
        salesOrderQueryKeys.detail(
          salesOrder.id,
        ),
        salesOrder,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            salesOrderQueryKeys.lists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            inventoryQueryKeys.lists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            stockMovementQueryKeys
            .lists(),
        }),
      ]);
    },
  });
}

export function useFulfillSalesOrder() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      salesOrderId,
      input,
    }: {
      salesOrderId: string;
      input: FulfillSalesOrderInput;
    }) =>
      fulfillSalesOrder(
        salesOrderId,
        input,
      ),

    onSuccess: async (
      salesOrder,
    ) => {
      queryClient.setQueryData(
        salesOrderQueryKeys.detail(
          salesOrder.id,
        ),
        salesOrder,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            salesOrderQueryKeys.lists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            inventoryQueryKeys.lists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            stockMovementQueryKeys
            .lists(),
        }),
      ]);
    },
  });
}
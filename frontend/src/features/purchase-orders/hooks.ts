import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  cancelPurchaseOrder,
  confirmPurchaseOrder,
  createPurchaseOrder,
  getPurchaseOrder,
  listPurchaseOrders,
  updatePurchaseOrder,
} from "@/features/purchase-orders/api";

import {
  purchaseOrderQueryKeys,
} from "@/features/purchase-orders/query-keys";

import type {
  CreatePurchaseOrderInput,
  PurchaseOrderListParameters,
  UpdatePurchaseOrderInput,
} from "@/features/purchase-orders/types";

export function usePurchaseOrderList(
  parameters:
    PurchaseOrderListParameters,
) {
  return useQuery({
    queryKey:
      purchaseOrderQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listPurchaseOrders(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function usePurchaseOrder(
  purchaseOrderId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      purchaseOrderQueryKeys.detail(
        purchaseOrderId,
      ),

    queryFn: () =>
      getPurchaseOrder(
        purchaseOrderId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        purchaseOrderId,
      ),

    staleTime: 30_000,
  });
}

export function useCreatePurchaseOrder() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreatePurchaseOrderInput,
    ) =>
      createPurchaseOrder(
        input,
      ),

    onSuccess: async (
      purchaseOrder,
    ) => {
      queryClient.setQueryData(
        purchaseOrderQueryKeys.detail(
          purchaseOrder.id,
        ),
        purchaseOrder,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            purchaseOrderQueryKeys
            .lists(),
        });
    },
  });
}

interface UpdatePurchaseOrderVariables {
  purchaseOrderId: string;
  input: UpdatePurchaseOrderInput;
}

export function useUpdatePurchaseOrder() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      purchaseOrderId,
      input,
    }: UpdatePurchaseOrderVariables) =>
      updatePurchaseOrder(
        purchaseOrderId,
        input,
      ),

    onSuccess: async (
      purchaseOrder,
    ) => {
      queryClient.setQueryData(
        purchaseOrderQueryKeys.detail(
          purchaseOrder.id,
        ),
        purchaseOrder,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            purchaseOrderQueryKeys
            .lists(),
        });
    },
  });
}

export function useConfirmPurchaseOrder() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      purchaseOrderId: string,
    ) =>
      confirmPurchaseOrder(
        purchaseOrderId,
      ),

    onSuccess: async (
      purchaseOrder,
    ) => {
      queryClient.setQueryData(
        purchaseOrderQueryKeys.detail(
          purchaseOrder.id,
        ),
        purchaseOrder,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            purchaseOrderQueryKeys
            .lists(),
        });
    },
  });
}

export function useCancelPurchaseOrder() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      purchaseOrderId: string,
    ) =>
      cancelPurchaseOrder(
        purchaseOrderId,
      ),

    onSuccess: async (
      purchaseOrder,
    ) => {
      queryClient.setQueryData(
        purchaseOrderQueryKeys.detail(
          purchaseOrder.id,
        ),
        purchaseOrder,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            purchaseOrderQueryKeys
            .lists(),
        });
    },
  });
}
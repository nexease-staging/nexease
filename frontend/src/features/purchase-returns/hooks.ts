import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  cancelPurchaseReturn,
  confirmPurchaseReturn,
  createPurchaseReturn,
  getPurchaseReturn,
  listPurchaseReturns,
} from "@/features/purchase-returns/api";

import {
  purchaseReturnQueryKeys,
} from "@/features/purchase-returns/query-keys";

import type {
  CreatePurchaseReturnInput,
  PurchaseReturnListParameters,
} from "@/features/purchase-returns/types";

export function usePurchaseReturnList(
  parameters:
    PurchaseReturnListParameters,
) {
  return useQuery({
    queryKey:
      purchaseReturnQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listPurchaseReturns(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function usePurchaseReturn(
  purchaseReturnId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      purchaseReturnQueryKeys.detail(
        purchaseReturnId,
      ),

    queryFn: () =>
      getPurchaseReturn(
        purchaseReturnId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        purchaseReturnId,
      ),

    staleTime: 30_000,
  });
}

export function useCreatePurchaseReturn() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreatePurchaseReturnInput,
    ) =>
      createPurchaseReturn(
        input,
      ),

    onSuccess: async (
      purchaseReturn,
    ) => {
      queryClient.setQueryData(
        purchaseReturnQueryKeys.detail(
          purchaseReturn.id,
        ),
        purchaseReturn,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            purchaseReturnQueryKeys
            .lists(),
        }),

        queryClient.invalidateQueries({
          queryKey: [
            "inventory",
          ],
        }),

        queryClient.invalidateQueries({
          queryKey: [
            "vendor-debit-notes",
          ],
        }),
      ]);
    },
  });
}

export function useConfirmPurchaseReturn() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      purchaseReturnId: string,
    ) =>
      confirmPurchaseReturn(
        purchaseReturnId,
      ),

    onSuccess: async (
      purchaseReturn,
    ) => {
      queryClient.setQueryData(
        purchaseReturnQueryKeys.detail(
          purchaseReturn.id,
        ),
        purchaseReturn,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            purchaseReturnQueryKeys
            .lists(),
        }),

        queryClient.invalidateQueries({
          queryKey: [
            "inventory",
          ],
        }),

        queryClient.invalidateQueries({
          queryKey: [
            "stock-movements",
          ],
        }),
      ]);
    },
  });
}

export function useCancelPurchaseReturn() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      purchaseReturnId: string,
    ) =>
      cancelPurchaseReturn(
        purchaseReturnId,
      ),

    onSuccess: async (
      purchaseReturn,
    ) => {
      queryClient.setQueryData(
        purchaseReturnQueryKeys.detail(
          purchaseReturn.id,
        ),
        purchaseReturn,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            purchaseReturnQueryKeys
            .lists(),
        });
    },
  });
}
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createGoodsReceipt,
  getGoodsReceipt,
  listGoodsReceipts,
} from "@/features/goods-receipts/api";

import {
  goodsReceiptQueryKeys,
} from "@/features/goods-receipts/query-keys";

import {
  inventoryQueryKeys,
} from "@/features/inventory/query-keys";

import {
  purchaseOrderQueryKeys,
} from "@/features/purchase-orders/query-keys";

import {
  stockMovementQueryKeys,
} from "@/features/inventory/query-keys";

import type {
  CreateGoodsReceiptInput,
  GoodsReceiptListParameters,
} from "@/features/goods-receipts/types";

export function useGoodsReceiptList(
  parameters:
    GoodsReceiptListParameters,
) {
  return useQuery({
    queryKey:
      goodsReceiptQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listGoodsReceipts(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useGoodsReceipt(
  goodsReceiptId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      goodsReceiptQueryKeys.detail(
        goodsReceiptId,
      ),

    queryFn: () =>
      getGoodsReceipt(
        goodsReceiptId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        goodsReceiptId,
      ),

    staleTime: 30_000,
  });
}

export function useCreateGoodsReceipt() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateGoodsReceiptInput,
    ) =>
      createGoodsReceipt(
        input,
      ),

    onSuccess: async (
      goodsReceipt,
    ) => {
      queryClient.setQueryData(
        goodsReceiptQueryKeys.detail(
          goodsReceipt.id,
        ),
        goodsReceipt,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            goodsReceiptQueryKeys
            .lists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            purchaseOrderQueryKeys
            .all,
        }),

        queryClient.invalidateQueries({
          queryKey:
            inventoryQueryKeys.all,
        }),

        queryClient.invalidateQueries({
          queryKey:
            stockMovementQueryKeys
            .all,
        }),
      ]);
    },
  });
}
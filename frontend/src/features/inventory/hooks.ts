"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  adjustInventory,
  createInventory,
  createStockTransfer,
  getInventory,
  getStockMovement,
  getStockTransfer,
  listInventory,
  listProductLookup,
  listStockMovements,
  listStockTransfers,
} from "@/features/inventory/api";

import {
  inventoryQueryKeys,
  productLookupQueryKeys,
  stockMovementQueryKeys,
  stockTransferQueryKeys,
} from "@/features/inventory/query-keys";

import type {
  AdjustInventoryInput,
  CreateInventoryInput,
  CreateStockTransferInput,
  InventoryListParameters,
  ProductLookupParameters,
  StockMovementListParameters,
  StockTransferListParameters,
} from "@/features/inventory/types";

export function useInventoryList(
  parameters: InventoryListParameters,
) {
  return useQuery({
    queryKey:
      inventoryQueryKeys.list(
        parameters,
      ),
    queryFn: () =>
      listInventory(
        parameters,
      ),
    staleTime: 20_000,
  });
}

export function useInventory(
  inventoryId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      inventoryQueryKeys.detail(
        inventoryId,
      ),
    queryFn: () =>
      getInventory(
        inventoryId,
      ),
    enabled:
      enabled
      &&
      Boolean(
        inventoryId
      ),
    staleTime: 20_000,
  });
}

export function useProductLookup(
  parameters: ProductLookupParameters,
) {
  return useQuery({
    queryKey:
      productLookupQueryKeys.list(
        parameters,
      ),
    queryFn: () =>
      listProductLookup(
        parameters,
      ),
    staleTime: 30_000,
  });
}

export function useStockMovementList(
  parameters:
    StockMovementListParameters,
) {
  return useQuery({
    queryKey:
      stockMovementQueryKeys.list(
        parameters,
      ),
    queryFn: () =>
      listStockMovements(
        parameters,
      ),
    staleTime: 15_000,
  });
}

export function useStockMovement(
  movementId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      stockMovementQueryKeys.detail(
        movementId,
      ),
    queryFn: () =>
      getStockMovement(
        movementId,
      ),
    enabled:
      enabled
      &&
      Boolean(
        movementId
      ),
    staleTime: 30_000,
  });
}

export function useStockTransferList(
  parameters:
    StockTransferListParameters,
) {
  return useQuery({
    queryKey:
      stockTransferQueryKeys.list(
        parameters,
      ),
    queryFn: () =>
      listStockTransfers(
        parameters,
      ),
    staleTime: 15_000,
  });
}

export function useStockTransfer(
  transferId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      stockTransferQueryKeys.detail(
        transferId,
      ),
    queryFn: () =>
      getStockTransfer(
        transferId,
      ),
    enabled:
      enabled
      &&
      Boolean(
        transferId
      ),
    staleTime: 30_000,
  });
}

export function useCreateInventory() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateInventoryInput,
    ) =>
      createInventory(
        input,
      ),

    onSuccess: async (
      inventory,
    ) => {
      queryClient.setQueryData(
        inventoryQueryKeys.detail(
          inventory.id,
        ),
        inventory,
      );

      await Promise.all([
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

export function useAdjustInventory() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      inventoryId,
      input,
    }: {
      inventoryId: string;
      input: AdjustInventoryInput;
    }) =>
      adjustInventory({
        inventoryId,
        input,
      }),

    onSuccess: async (
      inventory,
    ) => {
      queryClient.setQueryData(
        inventoryQueryKeys.detail(
          inventory.id,
        ),
        inventory,
      );

      await Promise.all([
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

export function useCreateStockTransfer() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateStockTransferInput,
    ) =>
      createStockTransfer(
        input,
      ),

    onSuccess: async (
      transfer,
    ) => {
      queryClient.setQueryData(
        stockTransferQueryKeys.detail(
          transfer.id,
        ),
        transfer,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            inventoryQueryKeys.lists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            stockMovementQueryKeys
            .lists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            stockTransferQueryKeys
            .lists(),
        }),
      ]);
    },
  });
}
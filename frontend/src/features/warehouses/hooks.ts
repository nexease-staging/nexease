"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  activateWarehouse,
  createWarehouse,
  deactivateWarehouse,
  getWarehouse,
  listWarehouses,
  updateWarehouse,
} from "@/features/warehouses/api";

import {
  warehouseQueryKeys,
} from "@/features/warehouses/query-keys";

import type {
  CreateWarehouseInput,
  UpdateWarehouseInput,
  WarehouseListParameters,
} from "@/features/warehouses/types";

export function useWarehouseList(
  parameters: WarehouseListParameters,
) {
  return useQuery({
    queryKey:
      warehouseQueryKeys.list(
        parameters,
      ),
    queryFn: () =>
      listWarehouses(
        parameters,
      ),
    staleTime: 30_000,
  });
}

export function useWarehouse(
  warehouseId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      warehouseQueryKeys.detail(
        warehouseId,
      ),
    queryFn: () =>
      getWarehouse(
        warehouseId,
      ),
    enabled:
      enabled
      &&
      Boolean(
        warehouseId
      ),
    staleTime: 30_000,
  });
}

export function useCreateWarehouse() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateWarehouseInput,
    ) =>
      createWarehouse(
        input,
      ),

    onSuccess: async (
      warehouse,
    ) => {
      queryClient.setQueryData(
        warehouseQueryKeys.detail(
          warehouse.id,
        ),
        warehouse,
      );

      await queryClient.invalidateQueries({
        queryKey:
          warehouseQueryKeys.lists(),
      });
    },
  });
}

export function useUpdateWarehouse() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      warehouseId,
      input,
    }: {
      warehouseId: string;
      input: UpdateWarehouseInput;
    }) =>
      updateWarehouse({
        warehouseId,
        input,
      }),

    onSuccess: async (
      warehouse,
    ) => {
      queryClient.setQueryData(
        warehouseQueryKeys.detail(
          warehouse.id,
        ),
        warehouse,
      );

      await queryClient.invalidateQueries({
        queryKey:
          warehouseQueryKeys.lists(),
      });
    },
  });
}

export function useActivateWarehouse() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      warehouseId: string,
    ) =>
      activateWarehouse(
        warehouseId,
      ),

    onSuccess: async (
      warehouse,
    ) => {
      queryClient.setQueryData(
        warehouseQueryKeys.detail(
          warehouse.id,
        ),
        warehouse,
      );

      await queryClient.invalidateQueries({
        queryKey:
          warehouseQueryKeys.lists(),
      });
    },
  });
}

export function useDeactivateWarehouse() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      warehouseId: string,
    ) =>
      deactivateWarehouse(
        warehouseId,
      ),

    onSuccess: async (
      warehouse,
    ) => {
      queryClient.setQueryData(
        warehouseQueryKeys.detail(
          warehouse.id,
        ),
        warehouse,
      );

      await queryClient.invalidateQueries({
        queryKey:
          warehouseQueryKeys.lists(),
      });
    },
  });
}
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  activateSupplier,
  createSupplier,
  deactivateSupplier,
  getSupplier,
  listSuppliers,
  updateSupplier,
} from "@/features/suppliers/api";

import {
  supplierQueryKeys,
} from "@/features/suppliers/query-keys";

import type {
  CreateSupplierInput,
  SupplierListParameters,
  UpdateSupplierInput,
} from "@/features/suppliers/types";

export function useSupplierList(
  parameters:
    SupplierListParameters,
) {
  return useQuery({
    queryKey:
      supplierQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listSuppliers(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useSupplier(
  supplierId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      supplierQueryKeys.detail(
        supplierId,
      ),

    queryFn: () =>
      getSupplier(
        supplierId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        supplierId,
      ),

    staleTime: 30_000,
  });
}

export function useCreateSupplier() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateSupplierInput,
    ) =>
      createSupplier(
        input,
      ),

    onSuccess: async (
      supplier,
    ) => {
      queryClient.setQueryData(
        supplierQueryKeys.detail(
          supplier.id,
        ),
        supplier,
      );

      await queryClient.invalidateQueries({
        queryKey:
          supplierQueryKeys.lists(),
      });
    },
  });
}

export function useUpdateSupplier() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      supplierId,
      input,
    }: {
      supplierId: string;
      input: UpdateSupplierInput;
    }) =>
      updateSupplier(
        supplierId,
        input,
      ),

    onSuccess: async (
      supplier,
    ) => {
      queryClient.setQueryData(
        supplierQueryKeys.detail(
          supplier.id,
        ),
        supplier,
      );

      await queryClient.invalidateQueries({
        queryKey:
          supplierQueryKeys.lists(),
      });
    },
  });
}

export function useActivateSupplier() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      supplierId: string,
    ) =>
      activateSupplier(
        supplierId,
      ),

    onSuccess: async (
      supplier,
    ) => {
      queryClient.setQueryData(
        supplierQueryKeys.detail(
          supplier.id,
        ),
        supplier,
      );

      await queryClient.invalidateQueries({
        queryKey:
          supplierQueryKeys.lists(),
      });
    },
  });
}

export function useDeactivateSupplier() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      supplierId: string,
    ) =>
      deactivateSupplier(
        supplierId,
      ),

    onSuccess: async (
      supplier,
    ) => {
      queryClient.setQueryData(
        supplierQueryKeys.detail(
          supplier.id,
        ),
        supplier,
      );

      await queryClient.invalidateQueries({
        queryKey:
          supplierQueryKeys.lists(),
      });
    },
  });
}
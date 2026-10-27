import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  activateCustomer,
  createCustomer,
  deactivateCustomer,
  getCustomer,
  listCustomers,
  updateCustomer,
} from "@/features/customers/api";

import {
  customerQueryKeys,
} from "@/features/customers/query-keys";

import type {
  CreateCustomerInput,
  CustomerListParameters,
  UpdateCustomerInput,
} from "@/features/customers/types";

export function useCustomerList(
  parameters:
    CustomerListParameters,
  enabled = true,
) {
  return useQuery({
    queryKey:
      customerQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listCustomers(
        parameters,
      ),

    enabled,

    staleTime: 15_000,
  });
}

export function useCustomer(
  customerId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      customerQueryKeys.detail(
        customerId,
      ),

    queryFn: () =>
      getCustomer(
        customerId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        customerId,
      ),

    staleTime: 30_000,
  });
}

export function useCreateCustomer() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateCustomerInput,
    ) =>
      createCustomer(
        input,
      ),

    onSuccess: async (
      customer,
    ) => {
      queryClient.setQueryData(
        customerQueryKeys.detail(
          customer.id,
        ),
        customer,
      );

      await queryClient.invalidateQueries({
        queryKey:
          customerQueryKeys.lists(),
      });
    },
  });
}

export function useUpdateCustomer() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      customerId,
      input,
    }: {
      customerId: string;
      input: UpdateCustomerInput;
    }) =>
      updateCustomer(
        customerId,
        input,
      ),

    onSuccess: async (
      customer,
    ) => {
      queryClient.setQueryData(
        customerQueryKeys.detail(
          customer.id,
        ),
        customer,
      );

      await queryClient.invalidateQueries({
        queryKey:
          customerQueryKeys.lists(),
      });
    },
  });
}

export function useActivateCustomer() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      customerId: string,
    ) =>
      activateCustomer(
        customerId,
      ),

    onSuccess: async (
      customer,
    ) => {
      queryClient.setQueryData(
        customerQueryKeys.detail(
          customer.id,
        ),
        customer,
      );

      await queryClient.invalidateQueries({
        queryKey:
          customerQueryKeys.lists(),
      });
    },
  });
}

export function useDeactivateCustomer() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      customerId: string,
    ) =>
      deactivateCustomer(
        customerId,
      ),

    onSuccess: async (
      customer,
    ) => {
      queryClient.setQueryData(
        customerQueryKeys.detail(
          customer.id,
        ),
        customer,
      );

      await queryClient.invalidateQueries({
        queryKey:
          customerQueryKeys.lists(),
      });
    },
  });
}
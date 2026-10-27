import {
  useQuery,
} from "@tanstack/react-query";

import {
  getCustomerPayment,
  listCustomerPayments,
} from "@/features/customer-payments/api";

import {
  customerPaymentQueryKeys,
} from "@/features/customer-payments/query-keys";

import type {
  CustomerPaymentListParameters,
} from "@/features/customer-payments/types";

export function useCustomerPaymentList(
  parameters:
    CustomerPaymentListParameters,
) {
  return useQuery({
    queryKey:
      customerPaymentQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listCustomerPayments(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useCustomerPayment(
  paymentId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      customerPaymentQueryKeys.detail(
        paymentId,
      ),

    queryFn: () =>
      getCustomerPayment(
        paymentId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        paymentId,
      ),

    staleTime: 30_000,
  });
}
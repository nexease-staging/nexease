import type {
  CustomerPaymentListParameters,
} from "@/features/customer-payments/types";

export const customerPaymentQueryKeys = {
  all: [
    "customer-payments",
  ] as const,

  lists: () => [
    ...customerPaymentQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      CustomerPaymentListParameters,
  ) => [
    ...customerPaymentQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...customerPaymentQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    paymentId: string,
  ) => [
    ...customerPaymentQueryKeys.details(),
    paymentId,
  ] as const,
};
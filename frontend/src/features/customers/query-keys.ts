import type {
  CustomerListParameters,
} from "@/features/customers/types";

export const customerQueryKeys = {
  all: [
    "customers",
  ] as const,

  lists: () => [
    ...customerQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      CustomerListParameters,
  ) => [
    ...customerQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...customerQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    customerId: string,
  ) => [
    ...customerQueryKeys.details(),
    customerId,
  ] as const,
};
import type {
  SalesReturnListParameters,
} from "@/features/sales-returns/types";

export const salesReturnQueryKeys = {
  all: [
    "sales-returns",
  ] as const,

  lists: () => [
    ...salesReturnQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      SalesReturnListParameters,
  ) => [
    ...salesReturnQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...salesReturnQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    salesReturnId: string,
  ) => [
    ...salesReturnQueryKeys.details(),
    salesReturnId,
  ] as const,
};
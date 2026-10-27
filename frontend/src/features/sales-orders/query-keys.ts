import type {
  SalesOrderListParameters,
} from "@/features/sales-orders/types";

export const salesOrderQueryKeys = {
  all: [
    "sales-orders",
  ] as const,

  lists: () => [
    ...salesOrderQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      SalesOrderListParameters,
  ) => [
    ...salesOrderQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...salesOrderQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    salesOrderId: string,
  ) => [
    ...salesOrderQueryKeys.details(),
    salesOrderId,
  ] as const,
};
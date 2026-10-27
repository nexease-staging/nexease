import type {
  PurchaseOrderListParameters,
} from "@/features/purchase-orders/types";

export const purchaseOrderQueryKeys = {
  all: [
    "purchase-orders",
  ] as const,

  lists: () => [
    ...purchaseOrderQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      PurchaseOrderListParameters,
  ) => [
    ...purchaseOrderQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...purchaseOrderQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    purchaseOrderId: string,
  ) => [
    ...purchaseOrderQueryKeys.details(),
    purchaseOrderId,
  ] as const,
};
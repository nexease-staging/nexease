import type {
  PurchaseReturnListParameters,
} from "@/features/purchase-returns/types";

export const purchaseReturnQueryKeys = {
  all: [
    "purchase-returns",
  ] as const,

  lists: () => [
    ...purchaseReturnQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      PurchaseReturnListParameters,
  ) => [
    ...purchaseReturnQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...purchaseReturnQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    purchaseReturnId: string,
  ) => [
    ...purchaseReturnQueryKeys.details(),
    purchaseReturnId,
  ] as const,
};
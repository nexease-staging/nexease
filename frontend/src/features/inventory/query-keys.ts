import type {
  InventoryListParameters,
  ProductLookupParameters,
  StockMovementListParameters,
  StockTransferListParameters,
} from "@/features/inventory/types";

export const inventoryQueryKeys = {
  all: [
    "inventory",
  ] as const,

  lists: () => [
    ...inventoryQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters: InventoryListParameters,
  ) => [
    ...inventoryQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...inventoryQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    inventoryId: string,
  ) => [
    ...inventoryQueryKeys.details(),
    inventoryId,
  ] as const,
};

export const productLookupQueryKeys = {
  all: [
    "product-lookup",
  ] as const,

  list: (
    parameters: ProductLookupParameters,
  ) => [
    ...productLookupQueryKeys.all,
    parameters,
  ] as const,
};

export const stockMovementQueryKeys = {
  all: [
    "stock-movements",
  ] as const,

  lists: () => [
    ...stockMovementQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters: StockMovementListParameters,
  ) => [
    ...stockMovementQueryKeys.lists(),
    parameters,
  ] as const,

  detail: (
    movementId: string,
  ) => [
    ...stockMovementQueryKeys.all,
    "detail",
    movementId,
  ] as const,
};

export const stockTransferQueryKeys = {
  all: [
    "stock-transfers",
  ] as const,

  lists: () => [
    ...stockTransferQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters: StockTransferListParameters,
  ) => [
    ...stockTransferQueryKeys.lists(),
    parameters,
  ] as const,

  detail: (
    transferId: string,
  ) => [
    ...stockTransferQueryKeys.all,
    "detail",
    transferId,
  ] as const,
};
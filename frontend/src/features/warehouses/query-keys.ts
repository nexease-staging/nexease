import type {
  WarehouseListParameters,
} from "@/features/warehouses/types";

export const warehouseQueryKeys = {
  all: [
    "warehouses",
  ] as const,

  lists: () => [
    ...warehouseQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters: WarehouseListParameters,
  ) => [
    ...warehouseQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...warehouseQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    warehouseId: string,
  ) => [
    ...warehouseQueryKeys.details(),
    warehouseId,
  ] as const,
};
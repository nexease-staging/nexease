import type {
  SupplierListParameters,
} from "@/features/suppliers/types";

export const supplierQueryKeys = {
  all: [
    "suppliers",
  ] as const,

  lists: () => [
    ...supplierQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      SupplierListParameters,
  ) => [
    ...supplierQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...supplierQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    supplierId: string,
  ) => [
    ...supplierQueryKeys.details(),
    supplierId,
  ] as const,
};
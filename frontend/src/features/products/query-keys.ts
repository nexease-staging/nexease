import type {
  ProductListParameters,
} from "@/features/products/types";

export const productQueryKeys = {
  all: [
    "products",
  ] as const,

  lists: () => [
    ...productQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      ProductListParameters,
  ) => [
    ...productQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...productQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    productId: string,
  ) => [
    ...productQueryKeys.details(),
    productId,
  ] as const,

  categories: () => [
    ...productQueryKeys.all,
    "categories",
  ] as const,
};
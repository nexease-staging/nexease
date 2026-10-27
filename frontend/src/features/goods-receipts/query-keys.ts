import type {
  GoodsReceiptListParameters,
} from "@/features/goods-receipts/types";

export const goodsReceiptQueryKeys = {
  all: [
    "goods-receipts",
  ] as const,

  lists: () => [
    ...goodsReceiptQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      GoodsReceiptListParameters,
  ) => [
    ...goodsReceiptQueryKeys
      .lists(),
    parameters,
  ] as const,

  details: () => [
    ...goodsReceiptQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    goodsReceiptId: string,
  ) => [
    ...goodsReceiptQueryKeys
      .details(),
    goodsReceiptId,
  ] as const,
};
import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CreateGoodsReceiptInput,
  GoodsReceiptData,
  GoodsReceiptDetail,
  GoodsReceiptListData,
  GoodsReceiptListParameters,
} from "@/features/goods-receipts/types";

type QueryValue =
  | string
  | number
  | undefined;

function buildQuery(
  parameters: Record<
    string,
    QueryValue
  >,
): string {
  const searchParameters =
    new URLSearchParams();

  for (
    const [
      key,
      value,
    ]
    of Object.entries(
      parameters,
    )
  ) {
    if (
      value === undefined
      ||
      value === ""
    ) {
      continue;
    }

    searchParameters.set(
      key,
      String(value),
    );
  }

  const query =
    searchParameters.toString();

  return query
    ? `?${query}`
    : "";
}

export async function listGoodsReceipts(
  parameters:
    GoodsReceiptListParameters = {},
): Promise<GoodsReceiptListData> {
  const response =
    await apiRequest<GoodsReceiptListData>(
      (
        "/goods-receipts/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          search:
            parameters.search,
          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}

export async function getGoodsReceipt(
  goodsReceiptId: string,
): Promise<GoodsReceiptDetail> {
  const response =
    await apiRequest<GoodsReceiptData>(
      (
        "/goods-receipts/"
        +
        `${goodsReceiptId}/`
      ),
    );

  return response.data.goods_receipt;
}

export async function createGoodsReceipt(
  input: CreateGoodsReceiptInput,
): Promise<GoodsReceiptDetail> {
  const response =
    await apiRequest<GoodsReceiptData>(
      "/goods-receipts/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.goods_receipt;
}
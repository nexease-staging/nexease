import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CreatePurchaseReturnInput,
  PurchaseReturnData,
  PurchaseReturnDetail,
  PurchaseReturnListData,
  PurchaseReturnListParameters,
} from "@/features/purchase-returns/types";

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

export async function listPurchaseReturns(
  parameters:
    PurchaseReturnListParameters = {},
): Promise<PurchaseReturnListData> {
  const response =
    await apiRequest<PurchaseReturnListData>(
      (
        "/purchase-returns/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          supplier_id:
            parameters.supplier_id,
          purchase_order_id:
            parameters.purchase_order_id,
          vendor_bill_id:
            parameters.vendor_bill_id,
          warehouse_id:
            parameters.warehouse_id,
          status:
            parameters.status,
          search:
            parameters.search,
          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}

export async function getPurchaseReturn(
  purchaseReturnId: string,
): Promise<PurchaseReturnDetail> {
  const response =
    await apiRequest<PurchaseReturnData>(
      (
        "/purchase-returns/"
        +
        `${purchaseReturnId}/`
      ),
    );

  return response.data.purchase_return;
}

export async function createPurchaseReturn(
  input: CreatePurchaseReturnInput,
): Promise<PurchaseReturnDetail> {
  const response =
    await apiRequest<PurchaseReturnData>(
      "/purchase-returns/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.purchase_return;
}

export async function confirmPurchaseReturn(
  purchaseReturnId: string,
): Promise<PurchaseReturnDetail> {
  const response =
    await apiRequest<PurchaseReturnData>(
      (
        "/purchase-returns/"
        +
        `${purchaseReturnId}/confirm/`
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response.data.purchase_return;
}

export async function cancelPurchaseReturn(
  purchaseReturnId: string,
): Promise<PurchaseReturnDetail> {
  const response =
    await apiRequest<PurchaseReturnData>(
      (
        "/purchase-returns/"
        +
        `${purchaseReturnId}/cancel/`
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response.data.purchase_return;
}
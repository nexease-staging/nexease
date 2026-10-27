import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CreatePurchaseOrderInput,
  PurchaseOrderData,
  PurchaseOrderDetail,
  PurchaseOrderListData,
  PurchaseOrderListParameters,
  UpdatePurchaseOrderInput,
} from "@/features/purchase-orders/types";

type QueryValue =
  | string
  | number
  | boolean
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
      String(
        value,
      ),
    );
  }

  const query =
    searchParameters.toString();

  return query
    ? `?${query}`
    : "";
}

export async function listPurchaseOrders(
  parameters:
    PurchaseOrderListParameters = {},
): Promise<PurchaseOrderListData> {
  const response =
    await apiRequest<
      PurchaseOrderListData
    >(
      (
        "/purchase-orders/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          supplier_id:
            parameters.supplier_id,
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

export async function getPurchaseOrder(
  purchaseOrderId: string,
): Promise<PurchaseOrderDetail> {
  const response =
    await apiRequest<
      PurchaseOrderData
    >(
      (
        `/purchase-orders/`
        +
        `${purchaseOrderId}/`
      ),
    );

  return response
    .data
    .purchase_order;
}

export async function createPurchaseOrder(
  input: CreatePurchaseOrderInput,
): Promise<PurchaseOrderDetail> {
  const response =
    await apiRequest<
      PurchaseOrderData
    >(
      "/purchase-orders/",
      {
        method: "POST",
        body: input,
      },
    );

  return response
    .data
    .purchase_order;
}

export async function updatePurchaseOrder(
  purchaseOrderId: string,
  input: UpdatePurchaseOrderInput,
): Promise<PurchaseOrderDetail> {
  const response =
    await apiRequest<
      PurchaseOrderData
    >(
      (
        `/purchase-orders/`
        +
        `${purchaseOrderId}/`
      ),
      {
        method: "PATCH",
        body: input,
      },
    );

  return response
    .data
    .purchase_order;
}

export async function confirmPurchaseOrder(
  purchaseOrderId: string,
): Promise<PurchaseOrderDetail> {
  const response =
    await apiRequest<
      PurchaseOrderData
    >(
      (
        `/purchase-orders/`
        +
        `${purchaseOrderId}/`
        +
        "confirm/"
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response
    .data
    .purchase_order;
}

export async function cancelPurchaseOrder(
  purchaseOrderId: string,
): Promise<PurchaseOrderDetail> {
  const response =
    await apiRequest<
      PurchaseOrderData
    >(
      (
        `/purchase-orders/`
        +
        `${purchaseOrderId}/`
        +
        "cancel/"
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response
    .data
    .purchase_order;
}
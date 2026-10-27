import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CreateSalesOrderInput,
  FulfillSalesOrderInput,
  SalesOrderData,
  SalesOrderDetail,
  SalesOrderListData,
  SalesOrderListParameters,
  UpdateSalesOrderInput,
} from "@/features/sales-orders/types";

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
        value
      ),
    );
  }

  const query =
    searchParameters.toString();

  return query
    ? `?${query}`
    : "";
}

export async function listSalesOrders(
  parameters:
    SalesOrderListParameters = {},
): Promise<SalesOrderListData> {
  const response =
    await apiRequest<SalesOrderListData>(
      (
        "/sales-orders/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          customer_id:
            parameters.customer_id,
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

export async function getSalesOrder(
  salesOrderId: string,
): Promise<SalesOrderDetail> {
  const response =
    await apiRequest<SalesOrderData>(
      (
        "/sales-orders/"
        +
        `${salesOrderId}/`
      ),
    );

  return response.data.sales_order;
}

export async function createSalesOrder(
  input: CreateSalesOrderInput,
): Promise<SalesOrderDetail> {
  const response =
    await apiRequest<SalesOrderData>(
      "/sales-orders/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.sales_order;
}

export async function updateSalesOrder(
  salesOrderId: string,
  input: UpdateSalesOrderInput,
): Promise<SalesOrderDetail> {
  const response =
    await apiRequest<SalesOrderData>(
      (
        "/sales-orders/"
        +
        `${salesOrderId}/`
      ),
      {
        method: "PUT",
        body: input,
      },
    );

  return response.data.sales_order;
}

export async function confirmSalesOrder(
  salesOrderId: string,
): Promise<SalesOrderDetail> {
  const response =
    await apiRequest<SalesOrderData>(
      (
        "/sales-orders/"
        +
        `${salesOrderId}/confirm/`
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response.data.sales_order;
}

export async function cancelSalesOrder(
  salesOrderId: string,
): Promise<SalesOrderDetail> {
  const response =
    await apiRequest<SalesOrderData>(
      (
        "/sales-orders/"
        +
        `${salesOrderId}/cancel/`
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response.data.sales_order;
}

export async function fulfillSalesOrder(
  salesOrderId: string,
  input: FulfillSalesOrderInput,
): Promise<SalesOrderDetail> {
  const response =
    await apiRequest<SalesOrderData>(
      (
        "/sales-orders/"
        +
        `${salesOrderId}/fulfill/`
      ),
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.sales_order;
}
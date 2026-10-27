import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CreateSalesReturnInput,
  SalesReturnData,
  SalesReturnDetail,
  SalesReturnListData,
  SalesReturnListParameters,
} from "@/features/sales-returns/types";

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

export async function listSalesReturns(
  parameters:
    SalesReturnListParameters = {},
): Promise<SalesReturnListData> {
  const response =
    await apiRequest<SalesReturnListData>(
      (
        "/sales-returns/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          customer_id:
            parameters.customer_id,
          sales_order_id:
            parameters.sales_order_id,
          invoice_id:
            parameters.invoice_id,
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

export async function getSalesReturn(
  salesReturnId: string,
): Promise<SalesReturnDetail> {
  const response =
    await apiRequest<SalesReturnData>(
      (
        "/sales-returns/"
        +
        `${salesReturnId}/`
      ),
    );

  return response.data.sales_return;
}

export async function createSalesReturn(
  input: CreateSalesReturnInput,
): Promise<SalesReturnDetail> {
  const response =
    await apiRequest<SalesReturnData>(
      "/sales-returns/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.sales_return;
}

export async function confirmSalesReturn(
  salesReturnId: string,
): Promise<SalesReturnDetail> {
  const response =
    await apiRequest<SalesReturnData>(
      (
        "/sales-returns/"
        +
        `${salesReturnId}/confirm/`
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response.data.sales_return;
}

export async function cancelSalesReturn(
  salesReturnId: string,
): Promise<SalesReturnDetail> {
  const response =
    await apiRequest<SalesReturnData>(
      (
        "/sales-returns/"
        +
        `${salesReturnId}/cancel/`
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response.data.sales_return;
}
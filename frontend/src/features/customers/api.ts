import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CreateCustomerInput,
  CustomerData,
  CustomerDetail,
  CustomerListData,
  CustomerListParameters,
  UpdateCustomerInput,
} from "@/features/customers/types";

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
      String(value),
    );
  }

  const query =
    searchParameters.toString();

  return query
    ? `?${query}`
    : "";
}

export async function listCustomers(
  parameters:
    CustomerListParameters = {},
): Promise<CustomerListData> {
  const response =
    await apiRequest<CustomerListData>(
      (
        "/customers/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          search:
            parameters.search,
          is_active:
            parameters.is_active,
          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}

export async function getCustomer(
  customerId: string,
): Promise<CustomerDetail> {
  const response =
    await apiRequest<CustomerData>(
      `/customers/${customerId}/`,
    );

  return response.data.customer;
}

export async function createCustomer(
  input: CreateCustomerInput,
): Promise<CustomerDetail> {
  const response =
    await apiRequest<CustomerData>(
      "/customers/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.customer;
}

export async function updateCustomer(
  customerId: string,
  input: UpdateCustomerInput,
): Promise<CustomerDetail> {
  const response =
    await apiRequest<CustomerData>(
      `/customers/${customerId}/`,
      {
        method: "PATCH",
        body: input,
      },
    );

  return response.data.customer;
}

export async function activateCustomer(
  customerId: string,
): Promise<CustomerDetail> {
  const response =
    await apiRequest<CustomerData>(
      `/customers/${customerId}/activate/`,
      {
        method: "POST",
      },
    );

  return response.data.customer;
}

export async function deactivateCustomer(
  customerId: string,
): Promise<CustomerDetail> {
  const response =
    await apiRequest<CustomerData>(
      `/customers/${customerId}/deactivate/`,
      {
        method: "POST",
      },
    );

  return response.data.customer;
}
import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CreateSupplierInput,
  SupplierData,
  SupplierDetail,
  SupplierListData,
  SupplierListParameters,
  UpdateSupplierInput,
} from "@/features/suppliers/types";

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

export async function listSuppliers(
  parameters:
    SupplierListParameters = {},
): Promise<SupplierListData> {
  const response =
    await apiRequest<SupplierListData>(
      (
        "/suppliers/"
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

export async function getSupplier(
  supplierId: string,
): Promise<SupplierDetail> {
  const response =
    await apiRequest<SupplierData>(
      `/suppliers/${supplierId}/`,
    );

  return response.data.supplier;
}

export async function createSupplier(
  input: CreateSupplierInput,
): Promise<SupplierDetail> {
  const response =
    await apiRequest<SupplierData>(
      "/suppliers/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.supplier;
}

export async function updateSupplier(
  supplierId: string,
  input: UpdateSupplierInput,
): Promise<SupplierDetail> {
  const response =
    await apiRequest<SupplierData>(
      `/suppliers/${supplierId}/`,
      {
        method: "PATCH",
        body: input,
      },
    );

  return response.data.supplier;
}

export async function activateSupplier(
  supplierId: string,
): Promise<SupplierDetail> {
  const response =
    await apiRequest<SupplierData>(
      `/suppliers/${supplierId}/activate/`,
      {
        method: "POST",
      },
    );

  return response.data.supplier;
}

export async function deactivateSupplier(
  supplierId: string,
): Promise<SupplierDetail> {
  const response =
    await apiRequest<SupplierData>(
      `/suppliers/${supplierId}/deactivate/`,
      {
        method: "POST",
      },
    );

  return response.data.supplier;
}
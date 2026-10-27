import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CreateWarehouseInput,
  UpdateWarehouseInput,
  WarehouseData,
  WarehouseDetail,
  WarehouseListData,
  WarehouseListParameters,
} from "@/features/warehouses/types";

function buildWarehouseQuery(
  parameters: WarehouseListParameters,
): string {
  const searchParameters =
    new URLSearchParams();

  if (parameters.page !== undefined) {
    searchParameters.set(
      "page",
      String(
        parameters.page,
      ),
    );
  }

  if (
    parameters.page_size !== undefined
  ) {
    searchParameters.set(
      "page_size",
      String(
        parameters.page_size,
      ),
    );
  }

  if (parameters.search?.trim()) {
    searchParameters.set(
      "search",
      parameters.search.trim(),
    );
  }

  if (
    parameters.is_active !== undefined
  ) {
    searchParameters.set(
      "is_active",
      String(
        parameters.is_active,
      ),
    );
  }

  if (parameters.country?.trim()) {
    searchParameters.set(
      "country",
      parameters.country.trim(),
    );
  }

  if (parameters.state?.trim()) {
    searchParameters.set(
      "state",
      parameters.state.trim(),
    );
  }

  if (parameters.city?.trim()) {
    searchParameters.set(
      "city",
      parameters.city.trim(),
    );
  }

  if (parameters.sort?.trim()) {
    searchParameters.set(
      "sort",
      parameters.sort.trim(),
    );
  }

  const query =
    searchParameters.toString();

  return query
    ? `?${query}`
    : "";
}

export async function listWarehouses(
  parameters: WarehouseListParameters = {},
): Promise<WarehouseListData> {
  const response =
    await apiRequest<WarehouseListData>(
      (
        "/warehouses/"
        +
        buildWarehouseQuery(
          parameters,
        )
      ),
    );

  return response.data;
}

export async function getWarehouse(
  warehouseId: string,
): Promise<WarehouseDetail> {
  const response =
    await apiRequest<WarehouseData>(
      `/warehouses/${warehouseId}/`,
    );

  return response.data.warehouse;
}

export async function createWarehouse(
  input: CreateWarehouseInput,
): Promise<WarehouseDetail> {
  const response =
    await apiRequest<WarehouseData>(
      "/warehouses/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.warehouse;
}

export async function updateWarehouse({
  warehouseId,
  input,
}: {
  warehouseId: string;
  input: UpdateWarehouseInput;
}): Promise<WarehouseDetail> {
  const response =
    await apiRequest<WarehouseData>(
      `/warehouses/${warehouseId}/`,
      {
        method: "PATCH",
        body: input,
      },
    );

  return response.data.warehouse;
}

export async function activateWarehouse(
  warehouseId: string,
): Promise<WarehouseDetail> {
  const response =
    await apiRequest<WarehouseData>(
      (
        `/warehouses/${warehouseId}`
        +
        "/activate/"
      ),
      {
        method: "POST",
      },
    );

  return response.data.warehouse;
}

export async function deactivateWarehouse(
  warehouseId: string,
): Promise<WarehouseDetail> {
  const response =
    await apiRequest<WarehouseData>(
      (
        `/warehouses/${warehouseId}`
        +
        "/deactivate/"
      ),
      {
        method: "POST",
      },
    );

  return response.data.warehouse;
}
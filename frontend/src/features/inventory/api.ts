import {
  apiRequest,
} from "@/lib/api/client";

import type {
  AdjustInventoryInput,
  CreateInventoryInput,
  CreateStockTransferInput,
  InventoryData,
  InventoryDetail,
  InventoryListData,
  InventoryListParameters,
  ProductLookupListData,
  ProductLookupParameters,
  StockMovementData,
  StockMovementDetail,
  StockMovementListData,
  StockMovementListParameters,
  StockTransferData,
  StockTransferDetail,
  StockTransferListData,
  StockTransferListParameters,
} from "@/features/inventory/types";

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

export async function listInventory(
  parameters: InventoryListParameters = {},
): Promise<InventoryListData> {
  const response =
    await apiRequest<InventoryListData>(
      (
        "/inventory/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          product_id:
            parameters.product_id,
          warehouse_id:
            parameters.warehouse_id,
          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}

export async function getInventory(
  inventoryId: string,
): Promise<InventoryDetail> {
  const response =
    await apiRequest<InventoryData>(
      `/inventory/${inventoryId}/`,
    );

  return response.data.inventory;
}

export async function createInventory(
  input: CreateInventoryInput,
): Promise<InventoryDetail> {
  const response =
    await apiRequest<InventoryData>(
      "/inventory/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.inventory;
}

export async function adjustInventory({
  inventoryId,
  input,
}: {
  inventoryId: string;
  input: AdjustInventoryInput;
}): Promise<InventoryDetail> {
  const response =
    await apiRequest<InventoryData>(
      (
        `/inventory/${inventoryId}`
        +
        "/adjust/"
      ),
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.inventory;
}

export async function listProductLookup(
  parameters: ProductLookupParameters = {},
): Promise<ProductLookupListData> {
  const response =
    await apiRequest<ProductLookupListData>(
      (
        "/products/"
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

export async function listStockMovements(
  parameters:
    StockMovementListParameters = {},
): Promise<StockMovementListData> {
  const response =
    await apiRequest<StockMovementListData>(
      (
        "/stock-movements/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          inventory_id:
            parameters.inventory_id,
          product_id:
            parameters.product_id,
          warehouse_id:
            parameters.warehouse_id,
          movement_type:
            parameters.movement_type,
          reference_type:
            parameters.reference_type,
          reference_id:
            parameters.reference_id,
          search:
            parameters.search,
          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}

export async function getStockMovement(
  movementId: string,
): Promise<StockMovementDetail> {
  const response =
    await apiRequest<StockMovementData>(
      (
        `/stock-movements/`
        +
        `${movementId}/`
      ),
    );

  return response.data.movement;
}

export async function listStockTransfers(
  parameters:
    StockTransferListParameters = {},
): Promise<StockTransferListData> {
  const response =
    await apiRequest<StockTransferListData>(
      (
        "/stock-transfers/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          product_id:
            parameters.product_id,
          source_warehouse_id:
            parameters
              .source_warehouse_id,
          destination_warehouse_id:
            parameters
              .destination_warehouse_id,
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

export async function getStockTransfer(
  transferId: string,
): Promise<StockTransferDetail> {
  const response =
    await apiRequest<StockTransferData>(
      (
        `/stock-transfers/`
        +
        `${transferId}/`
      ),
    );

  return response.data.transfer;
}

export async function createStockTransfer(
  input: CreateStockTransferInput,
): Promise<StockTransferDetail> {
  const response =
    await apiRequest<StockTransferData>(
      "/stock-transfers/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.transfer;
}
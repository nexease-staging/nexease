"use client";
import SearchSelect from "@/components/search-select";


import {
  useMemo,
  useState,
} from "react";

import {
  Boxes,
  Plus,
  RefreshCw,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import OpeningInventoryDialog from "@/features/inventory/components/opening-inventory-dialog";
import StockAdjustmentDialog from "@/features/inventory/components/stock-adjustment-dialog";
import {
  useInventoryList,
} from "@/features/inventory/hooks";

import type {
  InventorySummary,
} from "@/features/inventory/types";

import {
  useWarehouseList,
} from "@/features/warehouses/hooks";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

function formatQuantity(
  value: string,
): string {
  const quantity = Number(
    value
  );

  if (!Number.isFinite(quantity)) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      maximumFractionDigits: 2,
      minimumFractionDigits: 0,
    },
  ).format(
    quantity
  );
}


export default function InventoryPage() {
  const {
    authentication,
  } = useAuth();

  const [
    warehouseId,
    setWarehouseId,
  ] = useState("");

  const [
    page,
    setPage,
  ] = useState(1);

  const [
    openingDialogOpen,
    setOpeningDialogOpen,
  ] = useState(false);

  const [
    adjustmentInventory,
    setAdjustmentInventory,
  ] = useState<InventorySummary | null>(
    null,
  );

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const canRead = hasPermission(
    permissions,
    "inventory.read",
  );

  const canCreate = hasPermission(
    permissions,
    "inventory.create",
  );

  const canAdjust = hasPermission(
    permissions,
    "inventory.adjust",
  );

  const listParameters = useMemo(
    () => ({
      page,
      page_size: 20,
      warehouse_id:
        warehouseId
        ||
        undefined,
      sort: "-updated_at",
    }),
    [
      page,
      warehouseId,
    ],
  );

  const inventoryQuery =
    useInventoryList(
      listParameters,
    );

  const warehouseQuery =
    useWarehouseList({
      page: 1,
      page_size: 100,
      is_active: true,
      sort: "name",
    });

  if (!authentication) {
    return null;
  }

  if (!canRead) {
    return (
      <section
        className="
          rounded-2xl border
          border-amber-200 bg-amber-50
          p-6
        "
      >
        <h1
          className="
            text-lg font-semibold
            text-amber-900
          "
        >
          Inventory access restricted
        </h1>

        <p
          className="
            mt-2 text-sm text-amber-800
          "
        >
          Your role does not include the
          inventory.read permission.
        </p>
      </section>
    );
  }

  const inventoryItems =
    inventoryQuery.data
      ?.inventory
    ??
    [];

  const pagination =
    inventoryQuery.data
      ?.pagination;

  const warehouses =
    warehouseQuery.data
      ?.warehouses
    ??
    [];

  const visibleTotals =
    inventoryItems.reduce(
      (
        totals,
        inventory,
      ) => ({
        physical:
          totals.physical
          +
          Number(
            inventory.quantity
          ),
        reserved:
          totals.reserved
          +
          Number(
            inventory
              .reserved_quantity
          ),
        available:
          totals.available
          +
          Number(
            inventory
              .available_quantity
          ),
      }),
      {
        physical: 0,
        reserved: 0,
        available: 0,
      },
    );

  return (
    <section className="space-y-6">
      <div
        className="
          flex flex-col gap-4
          sm:flex-row sm:items-center
          sm:justify-between
        "
      >
        <div>
          <div
            className="
              flex items-center gap-2
            "
          >
            <Boxes
              size={25}
              className="text-blue-600"
            />

            <h1
              className="
                text-2xl font-bold
                text-slate-900
              "
            >
              Inventory
            </h1>
          </div>

          <p
            className="
              mt-1 text-sm text-slate-600
            "
          >
            Physical, reserved, and
            available stock by warehouse.
          </p>
        </div>

        <div
          className="
            flex flex-col gap-2
            sm:flex-row
          "
        >
          <button
            type="button"
            disabled={
              inventoryQuery.isFetching
            }
            onClick={() => {
              void inventoryQuery.refetch();
            }}
            className="
              inline-flex items-center
              justify-center gap-2
              rounded-lg border
              border-slate-300 bg-white
              px-4 py-2 text-sm
              font-semibold text-slate-700
              hover:bg-slate-50
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >
            <RefreshCw
              size={16}
              className={
                inventoryQuery.isFetching
                  ? "animate-spin"
                  : undefined
              }
            />

            Refresh
          </button>

          {canCreate ? (
            <button
              type="button"
              onClick={() => {
                setOpeningDialogOpen(
                  true
                );
              }}
              className="
                inline-flex items-center
                justify-center gap-2
                rounded-lg bg-blue-600
                px-4 py-2 text-sm
                font-semibold text-white
                hover:bg-blue-700
              "
            >
              <Plus size={17} />

              Opening inventory
            </button>
          ) : null}
        </div>
      </div>

      <div
        className="
          grid gap-4 sm:grid-cols-3
        "
      >
        {[
          {
            label:
              "Visible physical stock",
            value:
              visibleTotals.physical,
            color:
              "text-blue-700",
            background:
              "bg-blue-50",
          },
          {
            label:
              "Visible reserved stock",
            value:
              visibleTotals.reserved,
            color:
              "text-amber-700",
            background:
              "bg-amber-50",
          },
          {
            label:
              "Visible available stock",
            value:
              visibleTotals.available,
            color:
              "text-emerald-700",
            background:
              "bg-emerald-50",
          },
        ].map(
          (item) => (
            <article
              key={item.label}
              className={`
                rounded-2xl border
                border-slate-200 p-5
                ${item.background}
              `}
            >
              <p
                className="
                  text-sm font-medium
                  text-slate-600
                "
              >
                {item.label}
              </p>

              <p
                className={`
                  mt-2 text-2xl
                  font-bold
                  ${item.color}
                `}
              >
                {
                  formatQuantity(
                    String(
                      item.value
                    ),
                  )
                }
              </p>
            </article>
          ),
        )}
      </div>

      <div
        className="
          rounded-2xl border
          border-slate-200 bg-white
          p-4 shadow-sm
        "
      >
        <label
          className="
            block max-w-sm space-y-1.5
          "
        >
          <span
            className="
              text-sm font-semibold
              text-slate-700
            "
          >
            Warehouse
          </span>

          <SearchSelect
            value={warehouseId}
            disabled={
              warehouseQuery.isPending
            }
            onChange={(event) => {
              setWarehouseId(
                event.target.value,
              );

              setPage(1);
            }}
            className="
              h-10 w-full rounded-lg
              border border-slate-300
              bg-white px-3 text-sm
              text-slate-900 outline-none
              focus:border-blue-500
              focus:ring-2
              focus:ring-blue-100
              disabled:opacity-50
            "
          >
            <option value="">
              All warehouses
            </option>

            {warehouses.map(
              (warehouse) => (
                <option
                  key={warehouse.id}
                  value={warehouse.id}
                >
                  {warehouse.code}
                  {" — "}
                  {warehouse.name}
                </option>
              ),
            )}
          </SearchSelect>
        </label>
      </div>

      <div
        className="
          overflow-hidden rounded-2xl
          border border-slate-200
          bg-white shadow-sm
        "
      >
        {inventoryQuery.isPending ? (
          <div
            className="
              flex min-h-72 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading inventory…
          </div>
        ) : inventoryQuery.isError ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              gap-3 p-6 text-center
            "
          >
            <p
              className="
                text-sm font-medium
                text-red-700
              "
            >
              {
                inventoryQuery
                  .error
                  .message
              }
            </p>

            <button
              type="button"
              onClick={() => {
                void inventoryQuery.refetch();
              }}
              className="
                rounded-lg bg-slate-900
                px-4 py-2 text-sm
                font-semibold text-white
                hover:bg-slate-700
              "
            >
              Try again
            </button>
          </div>
        ) : inventoryItems.length === 0 ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              p-6 text-center
            "
          >
            <Boxes
              size={36}
              className="text-slate-300"
            />

            <h2
              className="
                mt-3 font-semibold
                text-slate-900
              "
            >
              No inventory balances found
            </h2>

            <p
              className="
                mt-1 max-w-md text-sm
                text-slate-500
              "
            >
              Select another warehouse or
              create opening inventory for a
              product and warehouse.
            </p>
            {canCreate ? (
              <button
                type="button"
                onClick={() => {
                  setOpeningDialogOpen(
                    true
                  );
                }}
                className="
                  mt-4 inline-flex
                  items-center gap-2
                  rounded-lg bg-blue-600
                  px-4 py-2 text-sm
                  font-semibold text-white
                  hover:bg-blue-700
                "
              >
                <Plus size={16} />

                Create opening inventory
              </button>
            ) : null}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table
              className="
                min-w-full divide-y
                divide-slate-200
              "
            >
              <thead className="bg-slate-50">
                <tr>
                  {[
                    "SKU",
                    "Product",
                    "Warehouse",
                    "Physical",
                    "Reserved",
                    "Available",
                    ...(canAdjust
                      ? ["Actions"]
                      : []),
                  ].map(
                    (heading) => (
                      <th
                        key={heading}
                        scope="col"
                        className="
                          whitespace-nowrap
                          px-4 py-3 text-left
                          text-xs font-semibold
                          uppercase tracking-wide
                          text-slate-500
                        "
                      >
                        {heading}
                      </th>
                    ),
                  )}
                </tr>
              </thead>

              <tbody
                className="
                  divide-y divide-slate-100
                "
              >
                {inventoryItems.map(
                  (inventory) => (
                    <tr
                      key={inventory.id}
                      className="
                        hover:bg-slate-50
                      "
                    >
                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          font-semibold
                          text-slate-900
                        "
                      >
                        {inventory.product.sku}
                      </td>

                      <td
                        className="
                          px-4 py-4 text-sm
                          text-slate-700
                        "
                      >
                        <p className="font-medium">
                          {inventory.product.name}
                        </p>

                        <p
                          className="
                            mt-0.5 text-xs
                            text-slate-500
                          "
                        >
                          Unit:{" "}
                          {inventory.product.unit}
                        </p>
                      </td>

                      <td
                        className="
                          px-4 py-4 text-sm
                          text-slate-600
                        "
                      >
                        <p>
                          {inventory.warehouse.name}
                        </p>

                        <p
                          className="
                            mt-0.5 text-xs
                            text-slate-500
                          "
                        >
                          {inventory.warehouse.code}
                        </p>
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          font-semibold
                          text-blue-700
                        "
                      >
                        {
                          formatQuantity(
                            inventory.quantity,
                          )
                        }
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          font-semibold
                          text-amber-700
                        "
                      >
                        {
                          formatQuantity(
                            inventory
                              .reserved_quantity,
                          )
                        }
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          font-semibold
                          text-emerald-700
                        "
                      >
                        {
                          formatQuantity(
                            inventory
                              .available_quantity,
                          )
                        }
                      </td>
                      {canAdjust ? (
                        <td
                          className="
                            whitespace-nowrap
                            px-4 py-4
                          "
                        >
                          <button
                            type="button"
                            onClick={() => {
                              setAdjustmentInventory(
                                inventory,
                              );
                            }}
                            className="
                              rounded-lg border
                              border-blue-200
                              bg-blue-50
                              px-3 py-1.5
                              text-sm font-semibold
                              text-blue-700
                              hover:border-blue-300
                              hover:bg-blue-100
                            "
                          >
                            Adjust
                          </button>
                        </td>
                      ) : null}
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}

        {pagination ? (
          <div
            className="
              flex flex-col gap-3
              border-t border-slate-200
              px-4 py-3
              sm:flex-row sm:items-center
              sm:justify-between
            "
          >
            <p
              className="
                text-sm text-slate-600
              "
            >
              Page {pagination.page} of{" "}
              {pagination.total_pages || 1}
              {" · "}
              {pagination.total_items} balances
            </p>

            <div className="flex gap-2">
              <button
                type="button"
                disabled={
                  !pagination.has_previous
                  ||
                  inventoryQuery.isFetching
                }
                onClick={() => {
                  setPage(
                    (current) =>
                      Math.max(
                        1,
                        current - 1,
                      ),
                  );
                }}
                className="
                  rounded-lg border
                  border-slate-300 bg-white
                  px-3 py-1.5 text-sm
                  font-semibold text-slate-700
                  hover:bg-slate-50
                  disabled:cursor-not-allowed
                  disabled:opacity-40
                "
              >
                Previous
              </button>

              <button
                type="button"
                disabled={
                  !pagination.has_next
                  ||
                  inventoryQuery.isFetching
                }
                onClick={() => {
                  setPage(
                    (current) =>
                      current + 1,
                  );
                }}
                className="
                  rounded-lg border
                  border-slate-300 bg-white
                  px-3 py-1.5 text-sm
                  font-semibold text-slate-700
                  hover:bg-slate-50
                  disabled:cursor-not-allowed
                  disabled:opacity-40
                "
              >
                Next
              </button>
            </div>
          </div>
        ) : null}
      </div>
      <OpeningInventoryDialog
        open={
          openingDialogOpen
        }
        onClose={() => {
          setOpeningDialogOpen(
            false
          );
        }}
      />
      <StockAdjustmentDialog
        open={
          Boolean(
            adjustmentInventory,
          )
        }
        inventory={
          adjustmentInventory
        }
        onClose={() => {
          setAdjustmentInventory(
            null,
          );
        }}
      />
    </section>
  );
}
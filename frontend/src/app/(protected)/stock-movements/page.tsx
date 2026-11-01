"use client";
import SearchSelect from "@/components/search-select";


import {
  useMemo,
  useState,
} from "react";

import {
  ArrowDownUp,
  RefreshCw,
  Search,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  useStockMovementList,
} from "@/features/inventory/hooks";

import type {
  StockMovementType,
} from "@/features/inventory/types";

import {
  useWarehouseList,
} from "@/features/warehouses/hooks";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

const movementTypeOptions: Array<{
  value: StockMovementType;
  label: string;
}> = [
  {
    value: "OPENING_STOCK",
    label: "Opening stock",
  },
  {
    value: "STOCK_IN",
    label: "Stock in",
  },
  {
    value: "STOCK_OUT",
    label: "Stock out",
  },
  {
    value: "ADJUSTMENT_IN",
    label: "Adjustment in",
  },
  {
    value: "ADJUSTMENT_OUT",
    label: "Adjustment out",
  },
  {
    value: "RESERVATION",
    label: "Reservation",
  },
  {
    value: "RESERVATION_RELEASE",
    label: "Reservation release",
  },
  {
    value: "TRANSFER_OUT",
    label: "Transfer out",
  },
  {
    value: "TRANSFER_IN",
    label: "Transfer in",
  },
  {
    value: "SALES_RETURN",
    label: "Sales return",
  },
  {
    value: "PURCHASE_RETURN",
    label: "Purchase return",
  },
];

function formatQuantity(
  value: string,
): string {
  const quantity = Number(value);

  if (!Number.isFinite(quantity)) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    },
  ).format(quantity);
}

function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}

function movementLabel(
  movementType: StockMovementType,
): string {
  return (
    movementTypeOptions.find(
      (option) =>
        option.value === movementType,
    )?.label
    ??
    movementType
  );
}

function movementColor(
  movementType: StockMovementType,
): string {
  if (
    movementType.endsWith("_IN")
    ||
    movementType === "OPENING_STOCK"
    ||
    movementType === "SALES_RETURN"
  ) {
    return (
      "bg-emerald-50 text-emerald-700 "
      +
      "border-emerald-200"
    );
  }

  if (
    movementType.endsWith("_OUT")
    ||
    movementType === "PURCHASE_RETURN"
  ) {
    return (
      "bg-red-50 text-red-700 "
      +
      "border-red-200"
    );
  }

  if (
    movementType === "RESERVATION"
    ||
    movementType
    ===
    "RESERVATION_RELEASE"
  ) {
    return (
      "bg-amber-50 text-amber-700 "
      +
      "border-amber-200"
    );
  }

  return (
    "bg-blue-50 text-blue-700 "
    +
    "border-blue-200"
  );
}

export default function StockMovementsPage() {
  const {
    authentication,
  } = useAuth();

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    warehouseId,
    setWarehouseId,
  ] = useState("");

  const [
    movementType,
    setMovementType,
  ] = useState<
    StockMovementType | ""
  >("");

  const [
    page,
    setPage,
  ] = useState(1);

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

  const listParameters = useMemo(
    () => ({
      page,
      page_size: 20,
      search:
        search.trim()
        ||
        undefined,
      warehouse_id:
        warehouseId
        ||
        undefined,
      movement_type:
        movementType
        ||
        undefined,
      sort: "-created_at",
    }),
    [
      movementType,
      page,
      search,
      warehouseId,
    ],
  );

  const movementQuery =
    useStockMovementList(
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
          Stock movement access restricted
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

  const movements =
    movementQuery.data
      ?.movements
    ??
    [];

  const pagination =
    movementQuery.data
      ?.pagination;

  const warehouses =
    warehouseQuery.data
      ?.warehouses
    ??
    [];

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
            <ArrowDownUp
              size={25}
              className="text-blue-600"
            />

            <h1
              className="
                text-2xl font-bold
                text-slate-900
              "
            >
              Stock movements
            </h1>
          </div>

          <p
            className="
              mt-1 text-sm text-slate-600
            "
          >
            Complete stock movement history
            across products and warehouses.
          </p>
        </div>

        <button
          type="button"
          disabled={
            movementQuery.isFetching
          }
          onClick={() => {
            void movementQuery.refetch();
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
              movementQuery.isFetching
                ? "animate-spin"
                : undefined
            }
          />

          Refresh
        </button>
      </div>

      <div
        className="nx-list-filters
          grid gap-4 rounded-2xl
          border border-slate-200
          bg-white p-4 shadow-sm
          md:grid-cols-3
        "
      >
        <label className="space-y-1.5">
          <span
            className="
              text-sm font-semibold
              text-slate-700
            "
          >
            Search
          </span>

          <div className="relative">
            <Search
              size={17}
              className="
                pointer-events-none
                absolute left-3 top-1/2
                -translate-y-1/2
                text-slate-400
              "
            />

            <input
              type="search"
              value={search}
              placeholder="SKU, product or reference"
              onChange={(event) => {
                setSearch(
                  event.target.value,
                );
                setPage(1);
              }}
              className="
                h-10 w-full rounded-lg
                border border-slate-300
                bg-white pl-9 pr-3
                text-sm text-slate-900
                placeholder:text-slate-400
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            />
          </div>
        </label>

        <label className="space-y-1.5">
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

        <label className="space-y-1.5">
          <span
            className="
              text-sm font-semibold
              text-slate-700
            "
          >
            Movement type
          </span>

          <SearchSelect
            value={movementType}
            onChange={(event) => {
              setMovementType(
                event.target.value as (
                  StockMovementType | ""
                ),
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
            "
          >
            <option value="">
              All movement types
            </option>

            {movementTypeOptions.map(
              (option) => (
                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label}
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
        {movementQuery.isPending ? (
          <div
            className="
              flex min-h-72 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading stock movements…
          </div>
        ) : movementQuery.isError ? (
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
              {movementQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void movementQuery.refetch();
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
        ) : movements.length === 0 ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              p-6 text-center
            "
          >
            <ArrowDownUp
              size={36}
              className="text-slate-300"
            />

            <h2
              className="
                mt-3 font-semibold
                text-slate-900
              "
            >
              No stock movements found
            </h2>

            <p
              className="
                mt-1 max-w-md text-sm
                text-slate-500
              "
            >
              Change the filters or create an
              opening inventory, adjustment,
              or stock transfer.
            </p>
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
                    "Date",
                    "Type",
                    "Product",
                    "Warehouse",
                    "Quantity",
                    "Stock change",
                    "Reference",
                    "Created by",
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
                {movements.map(
                  (movement) => (
                    <tr
                      key={movement.id}
                      className="
                        hover:bg-slate-50
                      "
                    >
                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          text-slate-600
                        "
                      >
                        {
                          formatDate(
                            movement.created_at,
                          )
                        }
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                        "
                      >
                        <span
                          className={`
                            inline-flex rounded-full
                            border px-2.5 py-1
                            text-xs font-semibold
                            ${movementColor(
                              movement
                                .movement_type,
                            )}
                          `}
                        >
                          {
                            movementLabel(
                              movement
                                .movement_type,
                            )
                          }
                        </span>
                      </td>

                      <td
                        className="
                          px-4 py-4 text-sm
                          text-slate-700
                        "
                      >
                        <p
                          className="
                            font-semibold
                            text-slate-900
                          "
                        >
                          {movement.product.name}
                        </p>

                        <p
                          className="
                            mt-0.5 text-xs
                            text-slate-500
                          "
                        >
                          {movement.product.sku}
                        </p>
                      </td>

                      <td
                        className="
                          px-4 py-4 text-sm
                          text-slate-700
                        "
                      >
                        <p>
                          {movement.warehouse.name}
                        </p>

                        <p
                          className="
                            mt-0.5 text-xs
                            text-slate-500
                          "
                        >
                          {movement.warehouse.code}
                        </p>
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          font-bold text-slate-900
                        "
                      >
                        {
                          formatQuantity(
                            movement.quantity,
                          )
                        }
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          text-slate-700
                        "
                      >
                        {
                          formatQuantity(
                            movement
                              .quantity_before,
                          )
                        }
                        {" → "}
                        {
                          formatQuantity(
                            movement
                              .quantity_after,
                          )
                        }
                      </td>

                      <td
                        className="
                          px-4 py-4 text-sm
                          text-slate-600
                        "
                      >
                        <p>
                          {
                            movement.reference.type
                            ??
                            "—"
                          }
                        </p>

                        {movement.reference.id ? (
                          <p
                            className="
                              mt-0.5 max-w-40
                              truncate text-xs
                              text-slate-500
                            "
                            title={
                              movement.reference.id
                            }
                          >
                            {movement.reference.id}
                          </p>
                        ) : null}
                      </td>

                      <td
                        className="
                          px-4 py-4 text-sm
                          text-slate-600
                        "
                      >
                        {
                          movement.created_by
                            ?.email
                          ??
                          "System"
                        }
                      </td>
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
              {pagination.total_items} movements
            </p>

            <div className="flex gap-2">
              <button
                type="button"
                disabled={
                  !pagination.has_previous
                  ||
                  movementQuery.isFetching
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
                  movementQuery.isFetching
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
    </section>
  );
}
"use client";
import SearchSelect from "@/components/search-select";


import {
  useMemo,
  useState,
} from "react";

import {
  ArrowRight,
  Plus,
  RefreshCw,
  Search,
  Truck,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import StockTransferDialog from "@/features/inventory/components/stock-transfer-dialog";

import {
  useStockTransferList,
} from "@/features/inventory/hooks";

import type {
  StockTransferStatus,
} from "@/features/inventory/types";

import {
  useWarehouseList,
} from "@/features/warehouses/hooks";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

const statusOptions: Array<{
  value: StockTransferStatus;
  label: string;
}> = [
  {
    value: "DRAFT",
    label: "Draft",
  },
  {
    value: "COMPLETED",
    label: "Completed",
  },
  {
    value: "CANCELLED",
    label: "Cancelled",
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

function statusColor(
  status: StockTransferStatus,
): string {
  if (status === "COMPLETED") {
    return (
      "border-emerald-200 "
      +
      "bg-emerald-50 "
      +
      "text-emerald-700"
    );
  }

  if (status === "CANCELLED") {
    return (
      "border-red-200 "
      +
      "bg-red-50 "
      +
      "text-red-700"
    );
  }

  return (
    "border-amber-200 "
    +
    "bg-amber-50 "
    +
    "text-amber-700"
  );
}

export default function StockTransfersPage() {
  const {
    authentication,
  } = useAuth();

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    sourceWarehouseId,
    setSourceWarehouseId,
  ] = useState("");

  const [
    destinationWarehouseId,
    setDestinationWarehouseId,
  ] = useState("");

  const [
    status,
    setStatus,
  ] = useState<
    StockTransferStatus | ""
  >("");

  const [
    page,
    setPage,
  ] = useState(1);

  const [
    transferDialogOpen,
    setTransferDialogOpen,
  ] = useState(false);

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

  const canTransfer = hasPermission(
    permissions,
    "inventory.transfer",
  );

  const listParameters = useMemo(
    () => ({
      page,
      page_size: 20,
      search:
        search.trim()
        ||
        undefined,
      source_warehouse_id:
        sourceWarehouseId
        ||
        undefined,
      destination_warehouse_id:
        destinationWarehouseId
        ||
        undefined,
      status:
        status
        ||
        undefined,
      sort: "-created_at",
    }),
    [
      destinationWarehouseId,
      page,
      search,
      sourceWarehouseId,
      status,
    ],
  );

  const transferQuery =
    useStockTransferList(
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
          Stock transfer access restricted
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

  const transfers =
    transferQuery.data
      ?.transfers
    ??
    [];

  const pagination =
    transferQuery.data
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
            <Truck
              size={25}
              className="text-blue-600"
            />

            <h1
              className="
                text-2xl font-bold
                text-slate-900
              "
            >
              Stock transfers
            </h1>
          </div>

          <p
            className="
              mt-1 text-sm text-slate-600
            "
          >
            Move stock safely between
            organization warehouses.
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
              transferQuery.isFetching
            }
            onClick={() => {
              void transferQuery.refetch();
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
                transferQuery.isFetching
                  ? "animate-spin"
                  : undefined
              }
            />

            Refresh
          </button>

          {canTransfer ? (
            <button title="New transfer"
              type="button"
              onClick={() => {
                setTransferDialogOpen(
                  true,
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
              <Plus size={17} /><span className="sr-only">New transfer</span></button>
          ) : null}
        </div>
      </div>

      <div
        className="nx-list-filters
          grid gap-4 rounded-2xl
          border border-slate-200
          bg-white p-4 shadow-sm
          md:grid-cols-2
          xl:grid-cols-4
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
              placeholder="Transfer number or product"
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
            Source warehouse
          </span>

          <SearchSelect
            value={sourceWarehouseId}
            disabled={
              warehouseQuery.isPending
            }
            onChange={(event) => {
              setSourceWarehouseId(
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
              All source warehouses
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
            Destination warehouse
          </span>

          <SearchSelect
            value={
              destinationWarehouseId
            }
            disabled={
              warehouseQuery.isPending
            }
            onChange={(event) => {
              setDestinationWarehouseId(
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
              All destination warehouses
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
            Status
          </span>

          <SearchSelect
            value={status}
            onChange={(event) => {
              setStatus(
                event.target.value as (
                  StockTransferStatus | ""
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
              All statuses
            </option>

            {statusOptions.map(
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
        {transferQuery.isPending ? (
          <div
            className="
              flex min-h-72 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading stock transfers…
          </div>
        ) : transferQuery.isError ? (
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
              {transferQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void transferQuery.refetch();
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
        ) : transfers.length === 0 ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              p-6 text-center
            "
          >
            <Truck
              size={36}
              className="text-slate-300"
            />

            <h2
              className="
                mt-3 font-semibold
                text-slate-900
              "
            >
              No stock transfers found
            </h2>

            <p
              className="
                mt-1 max-w-md text-sm
                text-slate-500
              "
            >
              Change the filters or create
              your first warehouse transfer.
            </p>

            {canTransfer ? (
              <button title="Create stock transfer"
                type="button"
                onClick={() => {
                  setTransferDialogOpen(
                    true,
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
                <Plus size={16} /><span className="sr-only">Create stock transfer</span></button>
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
                    "Transfer",
                    "Product",
                    "Route",
                    "Quantity",
                    "Status",
                    "Created",
                    "Completed",
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
                {transfers.map(
                  (transfer) => (
                    <tr
                      key={transfer.id}
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
                        {
                          transfer
                            .transfer_number
                        }
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
                          {transfer.product.name}
                        </p>

                        <p
                          className="
                            mt-0.5 text-xs
                            text-slate-500
                          "
                        >
                          {transfer.product.sku}
                        </p>
                      </td>

                      <td
                        className="
                          min-w-64 px-4 py-4
                          text-sm text-slate-700
                        "
                      >
                        <div
                          className="
                            flex items-center gap-2
                          "
                        >
                          <span>
                            {
                              transfer
                                .source_warehouse
                                .code
                            }
                          </span>

                          <ArrowRight
                            size={15}
                            className="
                              shrink-0
                              text-blue-500
                            "
                          />

                          <span>
                            {
                              transfer
                                .destination_warehouse
                                .code
                            }
                          </span>
                        </div>

                        <p
                          className="
                            mt-1 text-xs
                            text-slate-500
                          "
                        >
                          {
                            transfer
                              .source_warehouse
                              .name
                          }
                          {" → "}
                          {
                            transfer
                              .destination_warehouse
                              .name
                          }
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
                            transfer.quantity,
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
                            ${statusColor(
                              transfer.status,
                            )}
                          `}
                        >
                          {transfer.status}
                        </span>
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          text-slate-600
                        "
                      >
                        {
                          formatDate(
                            transfer.created_at,
                          )
                        }
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          text-slate-600
                        "
                      >
                        {
                          formatDate(
                            transfer.completed_at,
                          )
                        }
                      </td>

                      <td
                        className="
                          px-4 py-4 text-sm
                          text-slate-600
                        "
                      >
                        {
                          transfer.created_by
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
            <p className="text-sm text-slate-600">
              Page {pagination.page} of{" "}
              {pagination.total_pages || 1}
              {" · "}
              {pagination.total_items} transfers
            </p>

            <div className="flex gap-2">
              <button
                type="button"
                disabled={
                  !pagination.has_previous
                  ||
                  transferQuery.isFetching
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
                  transferQuery.isFetching
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
                  disabled:opacity-40
                "
              >
                Next
              </button>
            </div>
          </div>
        ) : null}
      </div>

      <StockTransferDialog
        open={
          transferDialogOpen
        }
        onClose={() => {
          setTransferDialogOpen(
            false,
          );
        }}
      />
    </section>
  );
}
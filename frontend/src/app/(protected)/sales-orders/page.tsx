"use client";
import SearchSelect from "@/components/search-select";


import {
  useMemo,
  useState,
} from "react";

import {
  Eye,
  Plus,
  RefreshCw,
  Search,
  ShoppingCart,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  useCustomerList,
} from "@/features/customers/hooks";

import SalesOrderDetailDialog from "@/features/sales-orders/components/sales-order-detail-dialog";
import SalesOrderDialog from "@/features/sales-orders/components/sales-order-dialog";
import SalesOrderFulfillmentDialog from "@/features/sales-orders/components/sales-order-fulfillment-dialog";

import {
  useSalesOrderList,
} from "@/features/sales-orders/hooks";

import type {
  SalesOrderStatus,
} from "@/features/sales-orders/types";

import {
  useWarehouseList,
} from "@/features/warehouses/hooks";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

const statusOptions: Array<{
  value: SalesOrderStatus;
  label: string;
}> = [
  {
    value: "DRAFT",
    label: "Draft",
  },
  {
    value: "CONFIRMED",
    label: "Confirmed",
  },
  {
    value: "PARTIALLY_FULFILLED",
    label: "Partially fulfilled",
  },
  {
    value: "FULFILLED",
    label: "Fulfilled",
  },
  {
    value: "CANCELLED",
    label: "Cancelled",
  },
];

function formatAmount(
  value: string,
): string {
  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(amount);
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
      date.getTime()
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      dateStyle: "medium",
    },
  ).format(date);
}

function statusClassName(
  status: SalesOrderStatus,
): string {
  if (status === "FULFILLED") {
    return (
      "border-emerald-200 "
      +
      "bg-emerald-50 "
      +
      "text-emerald-700"
    );
  }

  if (
    status
    ===
    "PARTIALLY_FULFILLED"
  ) {
    return (
      "border-blue-200 "
      +
      "bg-blue-50 "
      +
      "text-blue-700"
    );
  }

  if (status === "CONFIRMED") {
    return (
      "border-violet-200 "
      +
      "bg-violet-50 "
      +
      "text-violet-700"
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

export default function SalesOrdersPage() {
  const {
    authentication,
  } = useAuth();

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    customerId,
    setCustomerId,
  ] = useState("");

  const [
    warehouseId,
    setWarehouseId,
  ] = useState("");

  const [
    status,
    setStatus,
  ] = useState<
    SalesOrderStatus | ""
  >("");

  const [
    page,
    setPage,
  ] = useState(1);

  const [
    formOpen,
    setFormOpen,
  ] = useState(false);

  const [
    editingSalesOrderId,
    setEditingSalesOrderId,
  ] = useState<string | null>(
    null
  );

  const [
    detailSalesOrderId,
    setDetailSalesOrderId,
  ] = useState<string | null>(
    null
  );

  const [
    fulfillmentSalesOrderId,
    setFulfillmentSalesOrderId,
  ] = useState<string | null>(
    null
  );

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const canRead =
    hasPermission(
      permissions,
      "sales_orders.read",
    );

  const canCreate =
    hasPermission(
      permissions,
      "sales_orders.create",
    );

const canCreateCustomer =
  hasPermission(
    permissions,
    "customers.create",
  );

const canCreateProduct =
  hasPermission(
    permissions,
    "products.create",
  );

  const listParameters =
    useMemo(
      () => ({
        page,
        page_size: 25,
        search:
          search.trim()
          ||
          undefined,
        customer_id:
          customerId
          ||
          undefined,
        warehouse_id:
          warehouseId
          ||
          undefined,
        status:
          status
          ||
          undefined,
        sort:
          "-created_at",
      }),
      [
        customerId,
        page,
        search,
        status,
        warehouseId,
      ],
    );

  const salesOrderQuery =
    useSalesOrderList(
      listParameters
    );

  const customerQuery =
    useCustomerList({
      page: 1,
      page_size: 100,
      is_active: true,
      sort: "name",
    });

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
          Sales Orders unavailable
        </h1>

        <p className="mt-2 text-sm text-amber-800">
          You do not have permission
          to view Sales Orders.
        </p>
      </section>
    );
  }

  const salesOrders =
    salesOrderQuery.data
      ?.sales_orders
    ??
    [];

  const pagination =
    salesOrderQuery.data
      ?.pagination;

  const customers =
    customerQuery.data
      ?.customers
    ??
    [];

  const warehouses =
    warehouseQuery.data
      ?.warehouses
    ??
    [];

  function openCreateDialog():
    void {
    setEditingSalesOrderId(
      null
    );

    setFormOpen(
      true
    );
  }

  function openEditDialog(
    salesOrderId: string,
  ): void {
    setDetailSalesOrderId(
      null
    );

    setEditingSalesOrderId(
      salesOrderId
    );

    setFormOpen(
      true
    );
  }

  function openFulfillmentDialog(
    salesOrderId: string,
  ): void {
    setDetailSalesOrderId(
      null
    );

    setFulfillmentSalesOrderId(
      salesOrderId
    );
  }

  return (
    <section className="space-y-6">
      <div
        className="
          flex flex-col gap-4
          lg:flex-row
          lg:items-center
          lg:justify-between
        "
      >
        <div>
          <div
            className="
              flex items-center gap-3
            "
          >
            <div
              className="
                rounded-xl bg-blue-100
                p-2.5 text-blue-700
              "
            >
              <ShoppingCart size={23} />
            </div>

            <div>
              <h1
                className="
                  text-2xl font-bold
                  text-slate-900
                "
              >
                Sales Orders
              </h1>

              <p className="text-sm text-slate-500">
                Create, confirm, dispatch,
                and track customer orders.
              </p>
            </div>
          </div>
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
              salesOrderQuery.isFetching
            }
            onClick={() => {
              void salesOrderQuery.refetch();
            }}
            className="
              inline-flex items-center
              justify-center gap-2
              rounded-lg border
              border-slate-300 bg-white
              px-4 py-2 text-sm
              font-semibold text-slate-700
              hover:bg-slate-50
              disabled:opacity-50
            "
          >
            <RefreshCw
              size={17}
              className={
                salesOrderQuery.isFetching
                  ? "animate-spin"
                  : undefined
              }
            />
            Refresh
          </button>

          {canCreate ? (
            <button
              type="button"
              onClick={
                openCreateDialog
              }
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
              New Sales Order
            </button>
          ) : null}
        </div>
      </div>

      <div
        className="
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
                absolute left-3 top-1/2
                -translate-y-1/2
                text-slate-400
              "
            />

            <input
              type="search"
              value={search}
              onChange={(event) => {
                setSearch(
                  event.target.value
                );
                setPage(1);
              }}
              placeholder="SO number, customer…"
              className="
                h-10 w-full rounded-lg
                border border-slate-300
                bg-white pl-9 pr-3
                text-sm text-slate-900
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
            Customer
          </span>

          <SearchSelect
            value={customerId}
            onChange={(event) => {
              setCustomerId(
                event.target.value
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
              All customers
            </option>

            {customers.map(
              (customer) => (
                <option
                  key={customer.id}
                  value={customer.id}
                >
                  {customer.code}
                  {" — "}
                  {customer.name}
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
            Warehouse
          </span>

          <SearchSelect
            value={warehouseId}
            onChange={(event) => {
              setWarehouseId(
                event.target.value
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
            Status
          </span>

          <SearchSelect
            value={status}
            onChange={(event) => {
              setStatus(
                event.target.value as (
                  SalesOrderStatus | ""
                )
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
        {salesOrderQuery.isPending ? (
          <div
            className="
              flex min-h-72 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading Sales Orders…
          </div>
        ) : salesOrderQuery.isError ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              gap-3 p-6
            "
          >
            <p className="text-sm text-red-700">
              {salesOrderQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void salesOrderQuery.refetch();
              }}
              className="
                rounded-lg bg-slate-900
                px-4 py-2 text-sm
                font-semibold text-white
              "
            >
              Try again
            </button>
          </div>
        ) : !salesOrders.length ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              p-6 text-center
            "
          >
            <ShoppingCart
              size={32}
              className="text-slate-300"
            />

            <h2
              className="
                mt-3 font-semibold
                text-slate-900
              "
            >
              No Sales Orders found
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Change the filters or create
              the first customer order.
            </p>

            {canCreate ? (
              <button
                type="button"
                onClick={
                  openCreateDialog
                }
                className="
                  mt-4 inline-flex
                  items-center gap-2
                  rounded-lg bg-blue-600
                  px-4 py-2 text-sm
                  font-semibold text-white
                "
              >
                <Plus size={16} />
                Create Sales Order
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
                    "Sales Order",
                    "Customer",
                    "Warehouse",
                    "Order date",
                    "Status",
                    "Items",
                    "Total",
                    "Actions",
                  ].map(
                    (heading) => (
                      <th
                        key={heading}
                        className="
                          whitespace-nowrap
                          px-4 py-3 text-left
                          text-xs font-bold
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
                {salesOrders.map(
                  (salesOrder) => (
                    <tr
                      key={salesOrder.id}
                      className="
                        hover:bg-slate-50
                      "
                    >
                      <td className="whitespace-nowrap px-4 py-4">
                        <p className="font-semibold text-slate-900">
                          {salesOrder.so_number}
                        </p>

                        <p className="text-xs text-slate-500">
                          Delivery:
                          {" "}
                          {formatDate(
                            salesOrder
                              .expected_delivery_date
                          )}
                        </p>
                      </td>

                      <td className="px-4 py-4">
                        <p className="font-medium text-slate-900">
                          {salesOrder.customer.name}
                        </p>

                        <p className="text-xs text-slate-500">
                          {salesOrder.customer.code}
                        </p>
                      </td>

                      <td className="px-4 py-4">
                        <p className="font-medium text-slate-900">
                          {salesOrder.warehouse.name}
                        </p>

                        <p className="text-xs text-slate-500">
                          {salesOrder.warehouse.code}
                        </p>
                      </td>

                      <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-700">
                        {formatDate(
                          salesOrder.order_date
                        )}
                      </td>

                      <td className="whitespace-nowrap px-4 py-4">
                        <span
                          className={`
                            rounded-full border
                            px-2.5 py-1 text-xs
                            font-bold
                            ${statusClassName(
                              salesOrder.status
                            )}
                          `}
                        >
                          {
                            salesOrder.status
                              .replaceAll(
                                "_",
                                " ",
                              )
                          }
                        </span>
                      </td>

                      <td className="whitespace-nowrap px-4 py-4 text-sm">
                        {salesOrder.item_count}
                      </td>

                      <td className="whitespace-nowrap px-4 py-4 font-semibold text-slate-900">
                        {formatAmount(
                          salesOrder.total_amount
                        )}
                      </td>

                      <td className="whitespace-nowrap px-4 py-4">
                        <button
                          type="button"
                          title="View Sales Order"
                          onClick={() => {
                            setDetailSalesOrderId(
                              salesOrder.id
                            );
                          }}
                          className="
                            rounded-lg border
                            border-slate-300
                            bg-white p-2
                            text-slate-600
                            hover:text-blue-700
                          "
                        >
                          <Eye size={16} />
                        </button>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>

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
                <p className="text-sm text-slate-500">
                  Page {pagination.page}
                  {" of "}
                  {pagination.total_pages}
                  {" · "}
                  {pagination.total_items}
                  {" Sales Orders"}
                </p>

                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={
                      !pagination.has_previous
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
                      border-slate-300 px-3
                      py-1.5 text-sm
                      font-semibold text-slate-700
                      disabled:opacity-40
                    "
                  >
                    Previous
                  </button>

                  <button
                    type="button"
                    disabled={
                      !pagination.has_next
                    }
                    onClick={() => {
                      setPage(
                        (current) =>
                          current + 1,
                      );
                    }}
                    className="
                      rounded-lg border
                      border-slate-300 px-3
                      py-1.5 text-sm
                      font-semibold text-slate-700
                      disabled:opacity-40
                    "
                  >
                    Next
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>

        <SalesOrderDialog
          open={formOpen}
          salesOrderId={
            editingSalesOrderId
          }
          canCreateCustomer={
            canCreateCustomer
          }
          canCreateProduct={
            canCreateProduct
          }
          onClose={() => {
          setFormOpen(
            false
          );

          setEditingSalesOrderId(
            null
          );
        }}
      />

      <SalesOrderDetailDialog
        open={
          Boolean(
            detailSalesOrderId
          )
        }
        salesOrderId={
          detailSalesOrderId
        }
        onClose={() => {
          setDetailSalesOrderId(
            null
          );
        }}
        onEdit={
          openEditDialog
        }
        onFulfill={
          openFulfillmentDialog
        }
      />

      <SalesOrderFulfillmentDialog
        open={
          Boolean(
            fulfillmentSalesOrderId
          )
        }
        salesOrderId={
          fulfillmentSalesOrderId
        }
        onClose={() => {
          setFulfillmentSalesOrderId(
            null
          );
        }}
      />
    </section>
  );
}
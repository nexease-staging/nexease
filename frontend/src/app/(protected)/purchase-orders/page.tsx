"use client";
import SearchSelect from "@/components/search-select";

import QuickPurchase from "@/features/business/quick-purchase";

import {
  useDeferredValue,
  useState,
} from "react";

import {
  ChevronLeft,
  ChevronRight,
  Eye,
  FilePlus2,
  PackageCheck,
  Search,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import PurchaseOrderDetailDialog from "@/features/purchase-orders/components/purchase-order-detail-dialog";
import PurchaseOrderDialog from "@/features/purchase-orders/components/purchase-order-dialog";

import {
  usePurchaseOrderList,
} from "@/features/purchase-orders/hooks";

import type {
  PurchaseOrderDetail,
  PurchaseOrderStatus,
  PurchaseOrderSummary,
} from "@/features/purchase-orders/types";

import {
  useSupplierList,
} from "@/features/suppliers/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

const PAGE_SIZE = 25;

const statusOptions:
  Array<{
    value: PurchaseOrderStatus;
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
      value: "PARTIALLY_RECEIVED",
      label: "Partially received",
    },
    {
      value: "RECEIVED",
      label: "Received",
    },
    {
      value: "CANCELLED",
      label: "Cancelled",
    },
  ];

const statusStyles:
  Record<
    PurchaseOrderStatus,
    string
  > = {
    DRAFT:
      "bg-slate-100 text-slate-700",
    CONFIRMED:
      "bg-blue-100 text-blue-700",
    PARTIALLY_RECEIVED:
      "bg-amber-100 text-amber-700",
    RECEIVED:
      "bg-emerald-100 text-emerald-700",
    CANCELLED:
      "bg-red-100 text-red-700",
  };

function formatStatus(
  status: PurchaseOrderStatus,
): string {
  const option =
    statusOptions.find(
      (item) =>
        item.value === status,
    );

  return option?.label ?? status;
}

function formatAmount(
  value: string,
): string {
  const amount =
    Number(value);

  if (
    Number.isNaN(amount)
  ) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(
    amount,
  );
}

function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  const parsedDate =
    new Date(value);

  if (
    Number.isNaN(
      parsedDate.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  ).format(
    parsedDate,
  );
}

function getErrorMessage(
  error: unknown,
): string {
  if (
    error
    instanceof
    APIRequestError
  ) {
    return error.message;
  }

  if (
    error
    instanceof
    Error
  ) {
    return error.message;
  }

  return (
    "Unable to load purchase orders."
  );
}

export default function PurchaseOrdersPage() {
  const {
    authentication,
  } = useAuth();

  const [
    page,
    setPage,
  ] = useState(1);

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    supplierId,
    setSupplierId,
  ] = useState("");

  const [
    status,
    setStatus,
  ] = useState<
    PurchaseOrderStatus | ""
  >("");

  const [
    sort,
    setSort,
  ] = useState(
    "-created_at",
  );

  const [
    formOpen,
    setFormOpen,
  ] = useState(false);

  const [
    editingPurchaseOrderId,
    setEditingPurchaseOrderId,
  ] = useState<string | null>(
    null,
  );

  const [
    detailOpen,
    setDetailOpen,
  ] = useState(false);

  const [
    selectedPurchaseOrderId,
    setSelectedPurchaseOrderId,
  ] = useState("");

  const deferredSearch =
    useDeferredValue(
      search.trim(),
    );

  const permissions =
    authentication
      ?.role
      .permissions
      ??
      [];

  const canCreate =
    permissions.includes(
      "purchase_orders.create",
    );

  const purchaseOrderQuery =
    usePurchaseOrderList({
      page,
      page_size: PAGE_SIZE,
      supplier_id:
        supplierId
        ||
        undefined,
      status:
        status
        ||
        undefined,
      search:
        deferredSearch
        ||
        undefined,
      sort,
    });

  const supplierQuery =
    useSupplierList({
      page: 1,
      page_size: 100,
      is_active: true,
      sort: "name",
    });

  const purchaseOrders =
    purchaseOrderQuery
      .data
      ?.purchase_orders
      ??
      [];

  const pagination =
    purchaseOrderQuery
      .data
      ?.pagination;

  function openCreateDialog():
    void {
    setEditingPurchaseOrderId(
      null,
    );

    setDetailOpen(false);
    setFormOpen(true);
  }

  function openDetailDialog(
    purchaseOrderId: string,
  ): void {
    setSelectedPurchaseOrderId(
      purchaseOrderId,
    );

    setFormOpen(false);
    setDetailOpen(true);
  }

  function openEditDialog(
    purchaseOrder:
      PurchaseOrderDetail,
  ): void {
    setEditingPurchaseOrderId(
      purchaseOrder.id,
    );

    setDetailOpen(false);
    setFormOpen(true);
  }

  function handleSaved(
    purchaseOrderId: string,
  ): void {
    setFormOpen(false);
    setEditingPurchaseOrderId(
      null,
    );

    setSelectedPurchaseOrderId(
      purchaseOrderId,
    );

    setDetailOpen(true);
  }

  function handleStatusChange(
    value: string,
  ): void {
    setStatus(
      value as (
        PurchaseOrderStatus | ""
      ),
    );

    setPage(1);
  }

  return (
    <>
<QuickPurchase kind="purchase_order" />
      <div className="space-y-6">
        <header
          className="
            flex flex-col gap-4
            sm:flex-row
            sm:items-start
            sm:justify-between
          "
        >
          <div>
            <p
              className="
                text-sm font-semibold
                text-blue-600
              "
            >
              Purchasing
            </p>

            <h1
              className="
                mt-1 text-2xl
                font-bold tracking-tight
                text-slate-950
                sm:text-3xl
              "
            >
              Purchase Orders
            </h1>

            <p
              className="
                mt-2 max-w-2xl
                text-sm text-slate-600
              "
            >
              Create, confirm and monitor
              supplier purchase orders and
              expected deliveries.
            </p>
          </div>

          {canCreate
            ? (
              <button
                type="button"
                onClick={
                  openCreateDialog
                }
                className="
                  inline-flex items-center
                  justify-center gap-2
                  rounded-lg bg-blue-600
                  px-4 py-2.5 text-sm
                  font-semibold text-white
                  shadow-sm
                  hover:bg-blue-700
                "
              >
                <FilePlus2 size={18} />
                New purchase order
              </button>
            )
            : null}
        </header>

        <section
          className="
            rounded-xl border
            border-slate-200 bg-white
            p-4 shadow-sm
          "
        >
          <div
            className="nx-list-filters
              grid gap-3
              md:grid-cols-2
              xl:grid-cols-4
            "
          >
            <label
              className="
                relative block
                md:col-span-2
                xl:col-span-1
              "
            >
              <span className="sr-only">
                Search purchase orders
              </span>

              <Search
                size={18}
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
                placeholder="
                  Search PO number or supplier
                "
                onChange={(event) => {
                  setSearch(
                    event.currentTarget
                      .value,
                  );

                  setPage(1);
                }}
                className="
                  h-11 w-full rounded-lg
                  border border-slate-300
                  bg-white py-2 pl-10
                  pr-3 text-sm
                  text-slate-950
                  outline-none
                  placeholder:text-slate-400
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />
            </label>

            <label>
              <span className="sr-only">
                Filter by supplier
              </span>

              <SearchSelect
                value={supplierId}
                onChange={(event) => {
                  setSupplierId(
                    event.currentTarget
                      .value,
                  );

                  setPage(1);
                }}
                className="
                  h-11 w-full rounded-lg
                  border border-slate-300
                  bg-white px-3 text-sm
                  text-slate-950
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              >
                <option value="">
                  All suppliers
                </option>

                {supplierQuery
                  .data
                  ?.suppliers
                  .map(
                    (supplier) => (
                      <option
                        key={supplier.id}
                        value={supplier.id}
                      >
                        {supplier.name}
                      </option>
                    ),
                  )}
              </SearchSelect>
            </label>

            <label>
              <span className="sr-only">
                Filter by status
              </span>

              <SearchSelect
                value={status}
                onChange={(event) => {
                  handleStatusChange(
                    event.currentTarget
                      .value,
                  );
                }}
                className="
                  h-11 w-full rounded-lg
                  border border-slate-300
                  bg-white px-3 text-sm
                  text-slate-950
                  outline-none
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

            <label>
              <span className="sr-only">
                Sort purchase orders
              </span>

              <SearchSelect
                value={sort}
                onChange={(event) => {
                  setSort(
                    event.currentTarget
                      .value,
                  );

                  setPage(1);
                }}
                className="
                  h-11 w-full rounded-lg
                  border border-slate-300
                  bg-white px-3 text-sm
                  text-slate-950
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              >
                <option value="-created_at">
                  Newest first
                </option>

                <option value="created_at">
                  Oldest first
                </option>

                <option value="-order_date">
                  Latest order date
                </option>

                <option value="order_date">
                  Earliest order date
                </option>

                <option value="expected_delivery_date">
                  Delivery date
                </option>

                <option value="-total_amount">
                  Highest amount
                </option>

                <option value="total_amount">
                  Lowest amount
                </option>

                <option value="po_number">
                  PO number
                </option>
              </SearchSelect>
            </label>
          </div>
        </section>

        {purchaseOrderQuery.isLoading
          ? (
            <section
              className="
                rounded-xl border
                border-slate-200 bg-white
                px-5 py-14 text-center
                text-sm text-slate-600
                shadow-sm
              "
            >
              Loading purchase orders…
            </section>
          )
          : null}

        {purchaseOrderQuery.isError
          ? (
            <section
              className="
                rounded-xl border
                border-red-200 bg-red-50
                px-5 py-4 text-sm
                text-red-700
              "
            >
              <p>
                {getErrorMessage(
                  purchaseOrderQuery
                    .error,
                )}
              </p>

              <button
                type="button"
                onClick={() => {
                  void purchaseOrderQuery
                    .refetch();
                }}
                className="
                  mt-3 font-semibold
                  text-red-700 underline
                "
              >
                Try again
              </button>
            </section>
          )
          : null}

        {!purchaseOrderQuery.isLoading
        &&
        !purchaseOrderQuery.isError
        &&
        purchaseOrders.length === 0
          ? (
            <section
              className="
                rounded-xl border
                border-dashed
                border-slate-300 bg-white
                px-5 py-14 text-center
                shadow-sm
              "
            >
              <PackageCheck
                size={38}
                className="
                  mx-auto text-slate-400
                "
              />

              <h2
                className="
                  mt-4 font-bold
                  text-slate-950
                "
              >
                No purchase orders found
              </h2>

              <p
                className="
                  mx-auto mt-2
                  max-w-md text-sm
                  text-slate-600
                "
              >
                {search
                ||
                supplierId
                ||
                status
                  ? (
                    "No purchase orders match "
                    +
                    "the selected filters."
                  )
                  : (
                    "Create your first purchase "
                    +
                    "order to begin purchasing "
                    +
                    "stock from suppliers."
                  )}
              </p>

              {canCreate
              &&
              !search
              &&
              !supplierId
              &&
              !status
                ? (
                  <button
                    type="button"
                    onClick={
                      openCreateDialog
                    }
                    className="
                      mt-5 inline-flex
                      items-center gap-2
                      rounded-lg
                      bg-blue-600 px-4
                      py-2.5 text-sm
                      font-semibold
                      text-white
                      hover:bg-blue-700
                    "
                  >
                    <FilePlus2
                      size={18}
                    />
                    New purchase order
                  </button>
                )
                : null}
            </section>
          )
          : null}

        {purchaseOrders.length > 0
          ? (
            <>
              <section
                className="
                  space-y-3 lg:hidden
                "
              >
                {purchaseOrders.map(
                  (purchaseOrder) => (
                    <PurchaseOrderCard
                      key={
                        purchaseOrder.id
                      }
                      purchaseOrder={
                        purchaseOrder
                      }
                      onOpen={() => {
                        openDetailDialog(
                          purchaseOrder.id,
                        );
                      }}
                    />
                  ),
                )}
              </section>

              <section
                className="
                  hidden overflow-hidden
                  rounded-xl border
                  border-slate-200
                  bg-white shadow-sm
                  lg:block
                "
              >
                <div
                  className="
                    overflow-x-auto
                  "
                >
                  <table
                    className="
                      min-w-full divide-y
                      divide-slate-200
                    "
                  >
                    <thead
                      className="
                        bg-slate-50
                      "
                    >
                      <tr>
                        {[
                          "Purchase order",
                          "Supplier",
                          "Order date",
                          "Expected delivery",
                          "Items",
                          "Status",
                          "Total",
                          "Actions",
                        ].map(
                          (heading) => (
                            <th
                              key={heading}
                              className="
                                whitespace-nowrap
                                px-4 py-3
                                text-left text-xs
                                font-semibold
                                uppercase
                                tracking-wide
                                text-slate-600
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
                        divide-y
                        divide-slate-200
                        bg-white
                      "
                    >
                      {purchaseOrders.map(
                        (
                          purchaseOrder,
                        ) => (
                          <tr
                            key={
                              purchaseOrder
                                .id
                            }
                            className="
                              hover:bg-slate-50
                            "
                          >
                            <td
                              className="
                                whitespace-nowrap
                                px-4 py-4
                              "
                            >
                              <button
                                type="button"
                                onClick={() => {
                                  openDetailDialog(
                                    purchaseOrder
                                      .id,
                                  );
                                }}
                                className="
                                  font-semibold
                                  text-blue-700
                                  hover:underline
                                "
                              >
                                {
                                  purchaseOrder
                                    .po_number
                                }
                              </button>

                              <p
                                className="
                                  mt-1 text-xs
                                  text-slate-500
                                "
                              >
                                Created{" "}
                                {formatDate(
                                  purchaseOrder
                                    .created_at,
                                )}
                              </p>
                            </td>

                            <td
                              className="
                                min-w-48
                                px-4 py-4
                              "
                            >
                              <p
                                className="
                                  font-medium
                                  text-slate-950
                                "
                              >
                                {
                                  purchaseOrder
                                    .supplier
                                    .name
                                }
                              </p>

                              <p
                                className="
                                  mt-1 text-xs
                                  text-slate-500
                                "
                              >
                                {
                                  purchaseOrder
                                    .supplier
                                    .code
                                }
                              </p>
                            </td>

                            <td
                              className="
                                whitespace-nowrap
                                px-4 py-4
                                text-sm
                                text-slate-700
                              "
                            >
                              {formatDate(
                                purchaseOrder
                                  .order_date,
                              )}
                            </td>

                            <td
                              className="
                                whitespace-nowrap
                                px-4 py-4
                                text-sm
                                text-slate-700
                              "
                            >
                              {formatDate(
                                purchaseOrder
                                  .expected_delivery_date,
                              )}
                            </td>

                            <td
                              className="
                                px-4 py-4
                                text-sm
                                text-slate-700
                              "
                            >
                              {
                                purchaseOrder
                                  .item_count
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
                                  rounded-full
                                  px-2.5 py-1
                                  text-xs
                                  font-semibold
                                  ${
                                    statusStyles[
                                      purchaseOrder
                                        .status
                                    ]
                                  }
                                `}
                              >
                                {formatStatus(
                                  purchaseOrder
                                    .status,
                                )}
                              </span>
                            </td>

                            <td
                              className="
                                whitespace-nowrap
                                px-4 py-4
                                text-sm
                                font-semibold
                                text-slate-950
                              "
                            >
                              {formatAmount(
                                purchaseOrder
                                  .total_amount,
                              )}
                            </td>

                            <td
                              className="
                                px-4 py-4
                              "
                            >
                              <button
                                type="button"
                                aria-label={
                                  (
                                    "View "
                                    +
                                    purchaseOrder
                                      .po_number
                                  )
                                }
                                title="View details"
                                onClick={() => {
                                  openDetailDialog(
                                    purchaseOrder
                                      .id,
                                  );
                                }}
                                className="
                                  rounded-lg p-2
                                  text-slate-500
                                  hover:bg-blue-50
                                  hover:text-blue-700
                                "
                              >
                                <Eye size={18} />
                              </button>
                            </td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )
          : null}

        {pagination
        &&
        pagination.total_pages > 1
          ? (
            <nav
              aria-label="
                Purchase-order pagination
              "
              className="
                flex flex-col gap-3
                rounded-xl border
                border-slate-200 bg-white
                px-4 py-3 shadow-sm
                sm:flex-row
                sm:items-center
                sm:justify-between
              "
            >
              <p
                className="
                  text-sm text-slate-600
                "
              >
                Page{" "}
                <span
                  className="
                    font-semibold
                    text-slate-950
                  "
                >
                  {pagination.page}
                </span>{" "}
                of{" "}
                <span
                  className="
                    font-semibold
                    text-slate-950
                  "
                >
                  {
                    pagination
                      .total_pages
                  }
                </span>
                {" · "}
                {
                  pagination
                    .total_items
                }{" "}
                purchase orders
              </p>

              <div
                className="
                  flex items-center gap-2
                "
              >
                <button
                  type="button"
                  disabled={
                    !pagination
                      .has_previous
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
                    inline-flex items-center
                    gap-1 rounded-lg
                    border border-slate-300
                    bg-white px-3 py-2
                    text-sm font-semibold
                    text-slate-700
                    hover:bg-slate-50
                    disabled:cursor-not-allowed
                    disabled:opacity-50
                  "
                >
                  <ChevronLeft
                    size={17}
                  />
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
                    inline-flex items-center
                    gap-1 rounded-lg
                    border border-slate-300
                    bg-white px-3 py-2
                    text-sm font-semibold
                    text-slate-700
                    hover:bg-slate-50
                    disabled:cursor-not-allowed
                    disabled:opacity-50
                  "
                >
                  Next
                  <ChevronRight
                    size={17}
                  />
                </button>
              </div>
            </nav>
          )
          : null}
      </div>

      <PurchaseOrderDialog
        open={formOpen}
        purchaseOrderId={
          editingPurchaseOrderId
        }
        onClose={() => {
          setFormOpen(false);
          setEditingPurchaseOrderId(
            null,
          );
        }}
        onSaved={handleSaved}
      />

      <PurchaseOrderDetailDialog
        open={detailOpen}
        purchaseOrderId={
          selectedPurchaseOrderId
        }
        onClose={() => {
          setDetailOpen(false);
        }}
        onEdit={openEditDialog}
      />
    </>
  );
}

interface PurchaseOrderCardProps {
  purchaseOrder:
    PurchaseOrderSummary;
  onOpen: () => void;
}

function PurchaseOrderCard({
  purchaseOrder,
  onOpen,
}: PurchaseOrderCardProps) {
  return (
    <article
      className="
        rounded-xl border
        border-slate-200 bg-white
        p-4 shadow-sm
      "
    >
      <div
        className="
          flex items-start
          justify-between gap-3
        "
      >
        <div className="min-w-0">
          <button
            type="button"
            onClick={onOpen}
            className="
              truncate text-left
              font-bold text-blue-700
              hover:underline
            "
          >
            {purchaseOrder.po_number}
          </button>

          <p
            className="
              mt-1 truncate text-sm
              font-medium text-slate-950
            "
          >
            {
              purchaseOrder
                .supplier.name
            }
          </p>

          <p
            className="
              mt-1 text-xs
              text-slate-500
            "
          >
            {
              purchaseOrder
                .supplier.code
            }
          </p>
        </div>

        <span
          className={`
            shrink-0 rounded-full
            px-2.5 py-1
            text-xs font-semibold
            ${
              statusStyles[
                purchaseOrder.status
              ]
            }
          `}
        >
          {formatStatus(
            purchaseOrder.status,
          )}
        </span>
      </div>

      <dl
        className="
          mt-4 grid grid-cols-2
          gap-3 text-sm
        "
      >
        <div>
          <dt
            className="
              text-xs text-slate-500
            "
          >
            Order date
          </dt>

          <dd
            className="
              mt-1 font-medium
              text-slate-900
            "
          >
            {formatDate(
              purchaseOrder.order_date,
            )}
          </dd>
        </div>

        <div>
          <dt
            className="
              text-xs text-slate-500
            "
          >
            Expected delivery
          </dt>

          <dd
            className="
              mt-1 font-medium
              text-slate-900
            "
          >
            {formatDate(
              purchaseOrder
                .expected_delivery_date,
            )}
          </dd>
        </div>

        <div>
          <dt
            className="
              text-xs text-slate-500
            "
          >
            Items
          </dt>

          <dd
            className="
              mt-1 font-medium
              text-slate-900
            "
          >
            {
              purchaseOrder
                .item_count
            }
          </dd>
        </div>

        <div>
          <dt
            className="
              text-xs text-slate-500
            "
          >
            Total
          </dt>

          <dd
            className="
              mt-1 font-bold
              text-slate-950
            "
          >
            {formatAmount(
              purchaseOrder
                .total_amount,
            )}
          </dd>
        </div>
      </dl>

      <button
        type="button"
        onClick={onOpen}
        className="
          mt-4 inline-flex w-full
          items-center justify-center
          gap-2 rounded-lg
          border border-slate-300
          bg-white px-4 py-2
          text-sm font-semibold
          text-slate-700
          hover:bg-slate-50
        "
      >
        <Eye size={17} />
        View details
      </button>
    </article>
  );
}
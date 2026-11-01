"use client";
import SearchSelect from "@/components/search-select";


import {
  useDeferredValue,
  useState,
} from "react";

import {
  ChevronLeft,
  ChevronRight,
  Eye,
  Plus,
  RotateCcw,
  Search,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import PurchaseReturnDetailDialog from "@/features/purchase-returns/components/purchase-return-detail-dialog";
import PurchaseReturnDialog from "@/features/purchase-returns/components/purchase-return-dialog";

import {
  usePurchaseReturnList,
} from "@/features/purchase-returns/hooks";

import type {
  PurchaseReturnStatus,
  PurchaseReturnSummary,
} from "@/features/purchase-returns/types";

import {
  useSupplierList,
} from "@/features/suppliers/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

const PAGE_SIZE = 25;

const statuses:
  Array<{
    value: PurchaseReturnStatus;
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
      value: "CANCELLED",
      label: "Cancelled",
    },
  ];

const statusStyles:
  Record<
    PurchaseReturnStatus,
    string
  > = {
    DRAFT:
      "bg-amber-100 text-amber-700",
    CONFIRMED:
      "bg-emerald-100 text-emerald-700",
    CANCELLED:
      "bg-red-100 text-red-700",
  };

function formatStatus(
  status: PurchaseReturnStatus,
): string {
  return (
    statuses.find(
      (item) =>
        item.value === status,
    )
    ?.label
    ??
    status
  );
}

function formatAmount(
  value: string,
): string {
  const amount = Number(value);

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
    },
  ).format(amount);
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
    "Unable to load purchase returns."
  );
}

export default function PurchaseReturnsPage() {
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
    PurchaseReturnStatus | ""
  >("");

  const [
    sort,
    setSort,
  ] = useState(
    "-return_date",
  );

  const [
    createOpen,
    setCreateOpen,
  ] = useState(false);

  const [
    detailOpen,
    setDetailOpen,
  ] = useState(false);

  const [
    selectedPurchaseReturnId,
    setSelectedPurchaseReturnId,
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
      "purchase_returns.create",
    );

  const canConfirm =
    permissions.includes(
      "purchase_returns.confirm",
    );

  const canCancel =
    permissions.includes(
      "purchase_returns.cancel",
    );

  const supplierQuery =
    useSupplierList({
      page: 1,
      page_size: 100,
      is_active: true,
      sort: "name",
    });

  const purchaseReturnQuery =
    usePurchaseReturnList({
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

  const purchaseReturns =
    purchaseReturnQuery
      .data
      ?.purchase_returns
      ??
      [];

  const pagination =
    purchaseReturnQuery
      .data
      ?.pagination;

  function openDetail(
    purchaseReturnId: string,
  ): void {
    setSelectedPurchaseReturnId(
      purchaseReturnId,
    );

    setCreateOpen(false);
    setDetailOpen(true);
  }

  function handleCreated(
    purchaseReturnId: string,
  ): void {
    setCreateOpen(false);

    setSelectedPurchaseReturnId(
      purchaseReturnId,
    );

    setDetailOpen(true);
  }

  return (
    <>
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
              Purchase returns
            </h1>

            <p
              className="
                mt-2 max-w-2xl
                text-sm text-slate-600
              "
            >
              Return received inventory to suppliers and track the resulting stock reversal.
            </p>
          </div>

          {canCreate
            ? (
              <button title="New purchase return"
                type="button"
                onClick={() => {
                  setCreateOpen(true);
                  setDetailOpen(false);
                }}
                className="
                  inline-flex items-center
                  justify-center gap-2
                  rounded-lg bg-blue-600
                  px-4 py-2.5
                  text-sm font-semibold
                  text-white shadow-sm
                  hover:bg-blue-700
                "
              >
                <Plus size={18} /><span className="sr-only">New purchase return</span></button>
            )
            : null}
        </header>

        <section
          className="
            rounded-xl border
            border-slate-200
            bg-white p-4 shadow-sm
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
              "
            >
              <span className="sr-only">
                Search purchase returns
              </span>

              <Search
                size={17}
                className="
                  pointer-events-none
                  absolute left-3 top-3
                  text-slate-400
                "
              />

              <input
                type="search"
                value={search}
                placeholder="Search return number or notes"
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
                  bg-white pl-10 pr-3
                  text-sm text-slate-950
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />
            </label>

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
                h-11 rounded-lg border
                border-slate-300
                bg-white px-3 text-sm
                text-slate-950 outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            >
              <option value="">
                All suppliers
              </option>

              {(
                supplierQuery
                  .data
                  ?.suppliers
                ??
                []
              ).map(
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

            <SearchSelect
              value={status}
                onChange={(event) => {
                const nextStatus = (event.currentTarget.value as PurchaseReturnStatus | "");

                setStatus(nextStatus);
                setPage(1);
                }}
              className="
                h-11 rounded-lg border
                border-slate-300
                bg-white px-3 text-sm
                text-slate-950 outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            >
              <option value="">
                All statuses
              </option>

              {statuses.map(
                (item) => (
                  <option
                    key={item.value}
                    value={item.value}
                  >
                    {item.label}
                  </option>
                ),
              )}
            </SearchSelect>

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
                h-11 rounded-lg border
                border-slate-300
                bg-white px-3 text-sm
                text-slate-950 outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            >
              <option value="-return_date">
                Newest return date
              </option>

              <option value="return_date">
                Oldest return date
              </option>

              <option value="-total_amount">
                Highest amount
              </option>

              <option value="return_number">
                Return number
              </option>
            </SearchSelect>
          </div>
        </section>

        {purchaseReturnQuery.error
          ? (
            <div
              className="
                rounded-xl border
                border-red-200 bg-red-50
                px-4 py-3 text-sm
                text-red-700
              "
            >
              {getErrorMessage(
                purchaseReturnQuery.error,
              )}
            </div>
          )
          : null}

        <section
          className="
            overflow-hidden rounded-xl
            border border-slate-200
            bg-white shadow-sm
          "
        >
          <div
            className="
              flex items-center
              justify-between gap-4
              border-b border-slate-200
              px-4 py-4 sm:px-5
            "
          >
            <div>
              <h2
                className="
                  font-bold text-slate-950
                "
              >
                Return history
              </h2>

              <p
                className="
                  mt-1 text-xs
                  text-slate-500
                "
              >
                {pagination
                  ? (
                    `${pagination.total_items} purchase returns`
                  )
                  : "Loading purchase returns"}
              </p>
            </div>

            {purchaseReturnQuery
              .isFetching
              ? (
                <RotateCcw
                  size={18}
                  className="
                    animate-spin
                    text-blue-600
                  "
                />
              )
              : null}
          </div>

          {purchaseReturnQuery.isLoading
            ? (
              <div
                className="
                  p-10 text-center
                  text-sm text-slate-500
                "
              >
                Loading purchase returns…
              </div>
            )
            : null}

          {!purchaseReturnQuery.isLoading
            &&
            !purchaseReturns.length
            ? (
              <div
                className="
                  p-10 text-center
                "
              >
                <RotateCcw
                  size={30}
                  className="
                    mx-auto text-slate-300
                  "
                />

                <p
                  className="
                    mt-3 font-semibold
                    text-slate-800
                  "
                >
                  No purchase returns found
                </p>

                <p
                  className="
                    mt-1 text-sm
                    text-slate-500
                  "
                >
                  Create a return after inventory has been received.
                </p>
              </div>
            )
            : null}

          {purchaseReturns.length
            ? (
              <>
                <div
                  className="
                    divide-y divide-slate-200
                    lg:hidden
                  "
                >
                  {purchaseReturns.map(
                    (
                      purchaseReturn:
                        PurchaseReturnSummary,
                    ) => (
                      <button
                        type="button"
                        key={
                          purchaseReturn.id
                        }
                        onClick={() => {
                          openDetail(
                            purchaseReturn.id,
                          );
                        }}
                        className="
                          block w-full p-4
                          text-left
                          hover:bg-slate-50
                        "
                      >
                        <div
                          className="
                            flex items-start
                            justify-between gap-3
                          "
                        >
                          <div>
                            <p
                              className="
                                font-semibold
                                text-slate-950
                              "
                            >
                              {
                                purchaseReturn
                                  .return_number
                              }
                            </p>

                            <p
                              className="
                                mt-1 text-sm
                                text-slate-600
                              "
                            >
                              {
                                purchaseReturn
                                  .supplier.name
                              }
                            </p>
                          </div>

                          <span
                            className={`
                              rounded-full
                              px-2.5 py-1
                              text-xs font-bold
                              ${
                                statusStyles[
                                  purchaseReturn
                                    .status
                                ]
                              }
                            `}
                          >
                            {formatStatus(
                              purchaseReturn
                                .status,
                            )}
                          </span>
                        </div>

                        <div
                          className="
                            mt-3 grid
                            grid-cols-2 gap-3
                            text-xs
                          "
                        >
                          <div>
                            <p
                              className="
                                text-slate-500
                              "
                            >
                              Return date
                            </p>

                            <p
                              className="
                                mt-1 font-semibold
                                text-slate-800
                              "
                            >
                              {formatDate(
                                purchaseReturn
                                  .return_date,
                              )}
                            </p>
                          </div>

                          <div>
                            <p
                              className="
                                text-slate-500
                              "
                            >
                              Total
                            </p>

                            <p
                              className="
                                mt-1 font-semibold
                                text-slate-800
                              "
                            >
                              {formatAmount(
                                purchaseReturn
                                  .total_amount,
                              )}
                            </p>
                          </div>
                        </div>
                      </button>
                    ),
                  )}
                </div>

                <div
                  className="
                    hidden overflow-x-auto
                    lg:block
                  "
                >
                  <table
                    className="
                      min-w-full
                      divide-y
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
                          "Return",
                          "Supplier",
                          "Purchase order",
                          "Return date",
                          "Amount",
                          "Status",
                          "",
                        ].map(
                          (heading) => (
                            <th
                              key={heading}
                              className="
                                px-4 py-3
                                text-left text-xs
                                font-bold uppercase
                                tracking-wide
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
                        divide-y
                        divide-slate-200
                      "
                    >
                      {purchaseReturns.map(
                        (purchaseReturn) => (
                          <tr
                            key={
                              purchaseReturn.id
                            }
                            className="
                              hover:bg-slate-50
                            "
                          >
                            <td
                              className="
                                px-4 py-4
                                text-sm font-semibold
                                text-slate-950
                              "
                            >
                              {
                                purchaseReturn
                                  .return_number
                              }
                            </td>

                            <td
                              className="
                                px-4 py-4
                                text-sm
                                text-slate-700
                              "
                            >
                              {
                                purchaseReturn
                                  .supplier.name
                              }
                            </td>

                            <td
                              className="
                                px-4 py-4
                                text-sm
                                text-slate-700
                              "
                            >
                              {
                                purchaseReturn
                                  .purchase_order
                                  .po_number
                              }
                            </td>

                            <td
                              className="
                                px-4 py-4
                                text-sm
                                text-slate-700
                              "
                            >
                              {formatDate(
                                purchaseReturn
                                  .return_date,
                              )}
                            </td>

                            <td
                              className="
                                px-4 py-4
                                text-sm font-semibold
                                text-slate-950
                              "
                            >
                              {formatAmount(
                                purchaseReturn
                                  .total_amount,
                              )}
                            </td>

                            <td
                              className="
                                px-4 py-4
                              "
                            >
                              <span
                                className={`
                                  rounded-full
                                  px-2.5 py-1
                                  text-xs font-bold
                                  ${
                                    statusStyles[
                                      purchaseReturn
                                        .status
                                    ]
                                  }
                                `}
                              >
                                {formatStatus(
                                  purchaseReturn
                                    .status,
                                )}
                              </span>
                            </td>

                            <td
                              className="
                                px-4 py-4
                                text-right
                              "
                            >
                              <button
                                type="button"
                                onClick={() => {
                                  openDetail(
                                    purchaseReturn.id,
                                  );
                                }}
                                className="
                                  inline-flex
                                  items-center gap-2
                                  rounded-lg border
                                  border-slate-300
                                  px-3 py-2
                                  text-xs font-semibold
                                  text-slate-700
                                  hover:bg-slate-100
                                "
                              >
                                <Eye size={15} />
                                View
                              </button>
                            </td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            )
            : null}

          {pagination
            &&
            pagination.total_pages
            >
            1
            ? (
              <footer
                className="
                  flex items-center
                  justify-between gap-4
                  border-t border-slate-200
                  px-4 py-4 sm:px-5
                "
              >
                <p
                  className="
                    text-sm text-slate-600
                  "
                >
                  Page {pagination.page} of{" "}
                  {pagination.total_pages}
                </p>

                <div
                  className="
                    flex items-center gap-2
                  "
                >
                  <button
                    type="button"
                    aria-label="Previous page"
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
                      rounded-lg border
                      border-slate-300
                      p-2 text-slate-700
                      hover:bg-slate-50
                      disabled:opacity-40
                    "
                  >
                    <ChevronLeft
                      size={18}
                    />
                  </button>

                  <button
                    type="button"
                    aria-label="Next page"
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
                      border-slate-300
                      p-2 text-slate-700
                      hover:bg-slate-50
                      disabled:opacity-40
                    "
                  >
                    <ChevronRight
                      size={18}
                    />
                  </button>
                </div>
              </footer>
            )
            : null}
        </section>
      </div>

      <PurchaseReturnDialog
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
        }}
        onCreated={handleCreated}
      />

      <PurchaseReturnDetailDialog
        open={detailOpen}
        purchaseReturnId={
          selectedPurchaseReturnId
          ||
          null
        }
        canConfirm={canConfirm}
        canCancel={canCancel}
        onClose={() => {
          setDetailOpen(false);
        }}
        onChanged={() => {
          void purchaseReturnQuery
            .refetch();
        }}
      />
    </>
  );
}
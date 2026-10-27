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
  Search,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  useSupplierList,
} from "@/features/suppliers/hooks";

import VendorBillDetailDialog from "@/features/vendor-bills/components/vendor-bill-detail-dialog";
import VendorBillDialog from "@/features/vendor-bills/components/vendor-bill-dialog";

import {
  useVendorBillList,
} from "@/features/vendor-bills/hooks";

import type {
  VendorBillStatus,
  VendorBillSummary,
} from "@/features/vendor-bills/types";

import {
  APIRequestError,
} from "@/lib/api/client";

const PAGE_SIZE = 25;

const statuses:
  Array<{
    value: VendorBillStatus;
    label: string;
  }> = [
    {
      value: "DRAFT",
      label: "Draft",
    },
    {
      value: "POSTED",
      label: "Posted",
    },
    {
      value: "PARTIALLY_PAID",
      label: "Partially paid",
    },
    {
      value: "PAID",
      label: "Paid",
    },
    {
      value: "CANCELLED",
      label: "Cancelled",
    },
  ];

const statusStyles:
  Record<
    VendorBillStatus,
    string
  > = {
    DRAFT:
      "bg-slate-100 text-slate-700",
    POSTED:
      "bg-blue-100 text-blue-700",
    PARTIALLY_PAID:
      "bg-amber-100 text-amber-700",
    PAID:
      "bg-emerald-100 text-emerald-700",
    CANCELLED:
      "bg-red-100 text-red-700",
  };

function formatStatus(
  status: VendorBillStatus,
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

  return "Unable to load vendor bills.";
}

export default function VendorBillsPage() {
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
    VendorBillStatus | ""
  >("");

  const [
    sort,
    setSort,
  ] = useState(
    "-created_at",
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
    selectedBillId,
    setSelectedBillId,
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
      "bills.create",
    );

  const vendorBillQuery =
    useVendorBillList({
      page,
      page_size: PAGE_SIZE,
      search:
        deferredSearch
        ||
        undefined,
      supplier_id:
        supplierId
        ||
        undefined,
      status:
        status
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

  const vendorBills =
    vendorBillQuery
      .data
      ?.vendor_bills
      ??
      [];

  const pagination =
    vendorBillQuery
      .data
      ?.pagination;

  function openDetail(
    billId: string,
  ): void {
    setSelectedBillId(
      billId,
    );

    setCreateOpen(false);
    setDetailOpen(true);
  }

  function handleCreated(
    billId: string,
  ): void {
    setCreateOpen(false);
    openDetail(billId);
  }

  function handleStatusChange(
    value: string,
  ): void {
    setStatus(
      value as (
        VendorBillStatus | ""
      ),
    );

    setPage(1);
  }

  return (
    <>
<QuickPurchase kind="bill" />
      <div className="space-y-6">
        <header
          className="
            flex flex-col gap-4
            sm:flex-row sm:items-start
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
                text-slate-950 sm:text-3xl
              "
            >
              Vendor Bills
            </h1>

            <p
              className="
                mt-2 max-w-2xl
                text-sm text-slate-600
              "
            >
              Generate supplier bills,
              post payable accounting and
              record outgoing payments.
            </p>
          </div>

          {canCreate
            ? (
              <button
                type="button"
                onClick={() => {
                  setDetailOpen(false);
                  setCreateOpen(true);
                }}
                className="
                  inline-flex items-center
                  justify-center gap-2
                  rounded-lg bg-blue-600
                  px-4 py-2.5 text-sm
                  font-semibold text-white
                  hover:bg-blue-700
                "
              >
                <FilePlus2 size={18} />
                New vendor bill
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
            className="
              grid gap-3
              md:grid-cols-2
              xl:grid-cols-4
            "
          >
            <label className="relative">
              <span className="sr-only">
                Search vendor bills
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
                  Search bill or supplier invoice
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

            <SearchSelect
              aria-label="Filter supplier"
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
                border-slate-300 bg-white
                px-3 text-sm
                text-slate-950
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

            <SearchSelect
              aria-label="Filter status"
              value={status}
              onChange={(event) => {
                handleStatusChange(
                  event.currentTarget
                    .value,
                );
              }}
              className="
                h-11 rounded-lg border
                border-slate-300 bg-white
                px-3 text-sm
                text-slate-950
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
              aria-label="Sort vendor bills"
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
                border-slate-300 bg-white
                px-3 text-sm
                text-slate-950
              "
            >
              <option value="-created_at">
                Newest first
              </option>
              <option value="created_at">
                Oldest first
              </option>
              <option value="-bill_date">
                Latest bill date
              </option>
              <option value="due_date">
                Due date
              </option>
              <option value="-total_amount">
                Highest amount
              </option>
              <option value="-balance_due">
                Highest balance
              </option>
              <option value="bill_number">
                Bill number
              </option>
            </SearchSelect>
          </div>
        </section>

        {vendorBillQuery.isLoading
          ? (
            <section
              className="
                rounded-xl border
                border-slate-200 bg-white
                px-5 py-14 text-center
                text-sm text-slate-600
              "
            >
              Loading vendor bills…
            </section>
          )
          : null}

        {vendorBillQuery.isError
          ? (
            <section
              className="
                rounded-xl border
                border-red-200 bg-red-50
                px-5 py-4 text-sm
                text-red-700
              "
            >
              {getErrorMessage(
                vendorBillQuery.error,
              )}
            </section>
          )
          : null}

        {!vendorBillQuery.isLoading
        &&
        !vendorBillQuery.isError
        &&
        vendorBills.length === 0
          ? (
            <section
              className="
                rounded-xl border
                border-dashed
                border-slate-300 bg-white
                px-5 py-14 text-center
              "
            >
              <FilePlus2
                size={40}
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
                No vendor bills found
              </h2>

              <p
                className="
                  mt-2 text-sm
                  text-slate-600
                "
              >
                Generate a bill from a fully
                received purchase order.
              </p>
            </section>
          )
          : null}

        {vendorBills.length > 0
          ? (
            <>
              <section
                className="
                  space-y-3 lg:hidden
                "
              >
                {vendorBills.map(
                  (vendorBill) => (
                    <VendorBillCard
                      key={vendorBill.id}
                      vendorBill={
                        vendorBill
                      }
                      onOpen={() => {
                        openDetail(
                          vendorBill.id,
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
                  bg-white lg:block
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
                          "Bill",
                          "Supplier",
                          "Bill date",
                          "Due date",
                          "Status",
                          "Total",
                          "Balance",
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
                      "
                    >
                      {vendorBills.map(
                        (vendorBill) => (
                          <tr
                            key={vendorBill.id}
                            className="
                              hover:bg-slate-50
                            "
                          >
                            <td
                              className="
                                px-4 py-4
                              "
                            >
                              <button
                                type="button"
                                onClick={() => {
                                  openDetail(
                                    vendorBill.id,
                                  );
                                }}
                                className="
                                  font-semibold
                                  text-blue-700
                                  hover:underline
                                "
                              >
                                {
                                  vendorBill
                                    .bill_number
                                }
                              </button>

                              <p
                                className="
                                  mt-1 text-xs
                                  text-slate-500
                                "
                              >
                                {
                                  vendorBill
                                    .supplier_invoice_number
                                  ??
                                  "No supplier reference"
                                }
                              </p>
                            </td>

                            <td
                              className="
                                min-w-48 px-4 py-4
                              "
                            >
                              <p
                                className="
                                  text-sm font-medium
                                  text-slate-950
                                "
                              >
                                {
                                  vendorBill
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
                                  vendorBill
                                    .supplier.code
                                }
                              </p>
                            </td>

                            <td
                              className="
                                whitespace-nowrap
                                px-4 py-4 text-sm
                                text-slate-700
                              "
                            >
                              {formatDate(
                                vendorBill.bill_date,
                              )}
                            </td>

                            <td
                              className="
                                whitespace-nowrap
                                px-4 py-4 text-sm
                                text-slate-700
                              "
                            >
                              {formatDate(
                                vendorBill.due_date,
                              )}
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
                                  text-xs font-semibold
                                  ${
                                    statusStyles[
                                      vendorBill
                                        .status
                                    ]
                                  }
                                `}
                              >
                                {formatStatus(
                                  vendorBill
                                    .status,
                                )}
                              </span>
                            </td>

                            <td
                              className="
                                whitespace-nowrap
                                px-4 py-4 text-sm
                                font-semibold
                                text-slate-950
                              "
                            >
                              {formatAmount(
                                vendorBill
                                  .total_amount,
                              )}
                            </td>

                            <td
                              className="
                                whitespace-nowrap
                                px-4 py-4 text-sm
                                font-semibold
                                text-slate-950
                              "
                            >
                              {formatAmount(
                                vendorBill
                                  .balance_due,
                              )}
                            </td>

                            <td
                              className="
                                px-4 py-4
                              "
                            >
                              <button
                                type="button"
                                onClick={() => {
                                  openDetail(
                                    vendorBill.id,
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
              className="
                flex flex-col gap-3
                rounded-xl border
                border-slate-200 bg-white
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
                {pagination.total_pages}
                {" · "}
                {pagination.total_items} bills
              </p>

              <div
                className="
                  flex gap-2
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
                    gap-1 rounded-lg border
                    border-slate-300
                    px-3 py-2 text-sm
                    font-semibold
                    text-slate-700
                    disabled:opacity-50
                  "
                >
                  <ChevronLeft size={17} />
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
                    gap-1 rounded-lg border
                    border-slate-300
                    px-3 py-2 text-sm
                    font-semibold
                    text-slate-700
                    disabled:opacity-50
                  "
                >
                  Next
                  <ChevronRight size={17} />
                </button>
              </div>
            </nav>
          )
          : null}
      </div>

      <VendorBillDialog
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
        }}
        onCreated={handleCreated}
      />

      <VendorBillDetailDialog
        open={detailOpen}
        billId={selectedBillId}
        onClose={() => {
          setDetailOpen(false);
        }}
      />
    </>
  );
}

interface VendorBillCardProps {
  vendorBill: VendorBillSummary;
  onOpen: () => void;
}

function VendorBillCard({
  vendorBill,
  onOpen,
}: VendorBillCardProps) {
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
        <div>
          <button
            type="button"
            onClick={onOpen}
            className="
              font-bold text-blue-700
              hover:underline
            "
          >
            {vendorBill.bill_number}
          </button>

          <p
            className="
              mt-1 text-sm font-medium
              text-slate-950
            "
          >
            {vendorBill.supplier.name}
          </p>
        </div>

        <span
          className={`
            rounded-full px-2.5 py-1
            text-xs font-semibold
            ${
              statusStyles[
                vendorBill.status
              ]
            }
          `}
        >
          {formatStatus(
            vendorBill.status,
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
            Bill date
          </dt>
          <dd
            className="
              mt-1 font-medium
              text-slate-900
            "
          >
            {formatDate(
              vendorBill.bill_date,
            )}
          </dd>
        </div>

        <div>
          <dt
            className="
              text-xs text-slate-500
            "
          >
            Due date
          </dt>
          <dd
            className="
              mt-1 font-medium
              text-slate-900
            "
          >
            {formatDate(
              vendorBill.due_date,
            )}
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
              vendorBill.total_amount,
            )}
          </dd>
        </div>

        <div>
          <dt
            className="
              text-xs text-slate-500
            "
          >
            Balance
          </dt>
          <dd
            className="
              mt-1 font-bold
              text-slate-950
            "
          >
            {formatAmount(
              vendorBill.balance_due,
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
          gap-2 rounded-lg border
          border-slate-300 px-4 py-2
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
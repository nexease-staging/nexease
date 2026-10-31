"use client";
import {InvoiceZip} from "@/features/business/operations-panels";
import SearchSelect from "@/components/search-select";

import DirectInvoice from "@/features/business/direct-invoice";

import {
  useMemo,
  useState,
} from "react";

import {
  CircleDollarSign,
  Eye,
  Plus,
  ReceiptText,
  RefreshCw,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  useCustomerList,
} from "@/features/customers/hooks";

import InvoiceDetailDialog from "@/features/invoices/components/invoice-detail-dialog";
import InvoiceDialog from "@/features/invoices/components/invoice-dialog";
import InvoicePaymentDialog from "@/features/invoices/components/invoice-payment-dialog";

import {
  useInvoiceList,
} from "@/features/invoices/hooks";

import type {
  InvoiceStatus,
  InvoiceSummary,
} from "@/features/invoices/types";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

const statusOptions: Array<{
  value: InvoiceStatus;
  label: string;
}> = [
  {
    value: "DRAFT",
    label: "Draft",
  },
  {
    value: "ISSUED",
    label: "Issued",
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

function formatAmount(
  value: string,
): string {
  const amount =
    Number(
      value,
    );

  if (
    !Number.isFinite(
      amount,
    )
  ) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
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

  const date =
    new Date(
      value,
    );

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
    },
  ).format(
    date,
  );
}

function displayStatus(
  status: InvoiceStatus,
): string {
  return status
    .replaceAll(
      "_",
      " ",
    )
    .toLowerCase()
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase(),
    );
}

function statusClassName(
  status: InvoiceStatus,
): string {
  if (status === "PAID") {
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
    "PARTIALLY_PAID"
  ) {
    return (
      "border-blue-200 "
      +
      "bg-blue-50 "
      +
      "text-blue-700"
    );
  }

  if (status === "ISSUED") {
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

export default function InvoicesPage() {
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
    status,
    setStatus,
  ] = useState<
    InvoiceStatus | ""
  >("");

  const [
    customerId,
    setCustomerId,
  ] = useState("");

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
    detailInvoiceId,
    setDetailInvoiceId,
  ] = useState<
    string | null
  >(null);

  const [
    paymentInvoice,
    setPaymentInvoice,
  ] = useState<
    InvoiceSummary | null
  >(null);

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const canRead =
    hasPermission(
      permissions,
      "invoices.read",
    );

  const canCreate =
    hasPermission(
      permissions,
      "invoices.create",
    );

  const canRecordPayment =
    hasPermission(
      permissions,
      "invoices.record_payment",
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
        status:
          status
          ||
          undefined,
        sort,
      }),
      [
        customerId,
        page,
        search,
        sort,
        status,
      ],
    );

  const invoiceQuery =
    useInvoiceList(
      listParameters,
    );

  const customerQuery =
    useCustomerList({
      page: 1,
      page_size: 100,
      is_active: true,
      sort: "name",
    });

  if (!canRead) {
    return (
      <section
        className="
          rounded-2xl border
          border-amber-200
          bg-amber-50 p-6
        "
      >

        <h1
          className="
            text-lg font-semibold
            text-amber-900
          "
        >
          Invoice access unavailable
        </h1>

        <p
          className="
            mt-2 text-sm
            text-amber-800
          "
        >
          Your role does not include the
          invoices.read permission.
        </p>
      </section>
    );
  }

  const invoices =
    invoiceQuery.data
      ?.invoices
    ??
    [];

  const pagination =
    invoiceQuery.data
      ?.pagination;

  const customers =
    customerQuery.data
      ?.customers
    ??
    [];

  function resetPage():
    void {
    setPage(
      1,
    );
  }

  function openPayment(
    invoice: InvoiceSummary,
  ): void {
    setDetailInvoiceId(
      null,
    );

    setPaymentInvoice(
      invoice,
    );
  }

  return (
    <>
<DirectInvoice /><InvoiceZip invoices={invoices}/>
      <section className="space-y-5">
        <div
          className="
            flex flex-col gap-4
            sm:flex-row
            sm:items-start
            sm:justify-between
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
                  flex size-11
                  items-center
                  justify-center
                  rounded-xl bg-blue-100
                  text-blue-700
                "
              >
                <ReceiptText size={22} />
              </div>

              <div>
                <h1
                  className="
                    text-2xl font-bold
                    text-slate-950
                  "
                >
                  Invoices
                </h1>

                <p
                  className="
                    mt-1 text-sm
                    text-slate-600
                  "
                >
                  Issue customer invoices and
                  record incoming payments.
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
              onClick={() => {
                void invoiceQuery.refetch();
              }}
              className="
                inline-flex items-center
                justify-center gap-2
                rounded-lg border
                border-slate-300
                bg-white px-4 py-2.5
                text-sm font-semibold
                text-slate-700
                hover:bg-slate-50
              "
            >
              <RefreshCw
                size={17}
                className={
                  invoiceQuery.isFetching
                    ? "animate-spin"
                    : ""
                }
              />

              Refresh
            </button>

            {canCreate ? (
              <button
                type="button"
                onClick={() => {
                  setCreateOpen(
                    true,
                  );
                }}
                className="
                  inline-flex items-center
                  justify-center gap-2
                  rounded-lg bg-blue-600
                  px-4 py-2.5
                  text-sm font-semibold
                  text-white
                  hover:bg-blue-700
                "
              >
                <Plus size={17} />
                New Invoice
              </button>
            ) : null}
          </div>
        </div>

        <div
          className="
            grid gap-4 rounded-2xl
            border border-slate-200
            bg-white p-4
            sm:grid-cols-2
            xl:grid-cols-4
          "
        >
          <div className="sm:col-span-2">
            <label
              htmlFor="invoice-search"
              className="
                text-xs font-semibold
                uppercase tracking-wide
                text-slate-600
              "
            >
              Search
            </label>

            <input
              id="invoice-search"
              type="search"
              value={search}
              onChange={(event) => {
                setSearch(
                  event.target.value,
                );

                resetPage();
              }}
              className="
                mt-1.5 w-full
                rounded-lg border
                border-slate-300
                bg-white px-3 py-2.5
                text-sm text-slate-950
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
              placeholder="Invoice, order or customer"
            />
          </div>

          <div>
            <label
              htmlFor="invoice-customer"
              className="
                text-xs font-semibold
                uppercase tracking-wide
                text-slate-600
              "
            >
              Customer
            </label>

            <SearchSelect
              id="invoice-customer"
              value={customerId}
              onChange={(event) => {
                setCustomerId(
                  event.target.value,
                );

                resetPage();
              }}
              className="
                mt-1.5 w-full
                rounded-lg border
                border-slate-300
                bg-white px-3 py-2.5
                text-sm text-slate-950
                outline-none
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
                    {customer.name}
                  </option>
                ),
              )}
            </SearchSelect>
          </div>

          <div>
            <label
              htmlFor="invoice-status"
              className="
                text-xs font-semibold
                uppercase tracking-wide
                text-slate-600
              "
            >
              Status
            </label>

            <SearchSelect
              id="invoice-status"
              value={status}
              onChange={(event) => {
                const nextStatus =
                  event.target.value;

                setStatus(
                  nextStatus === ""
                    ? ""
                    : nextStatus as InvoiceStatus,
                );

                resetPage();
              }}
              className="
                mt-1.5 w-full
                rounded-lg border
                border-slate-300
                bg-white px-3 py-2.5
                text-sm text-slate-950
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
          </div>

          <div>
            <label
              htmlFor="invoice-sort"
              className="
                text-xs font-semibold
                uppercase tracking-wide
                text-slate-600
              "
            >
              Sort
            </label>

            <SearchSelect
              id="invoice-sort"
              value={sort}
              onChange={(event) => {
                setSort(
                  event.target.value,
                );

                resetPage();
              }}
              className="
                mt-1.5 w-full
                rounded-lg border
                border-slate-300
                bg-white px-3 py-2.5
                text-sm text-slate-950
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

              <option value="due_date">
                Due date
              </option>

              <option value="-total_amount">
                Highest amount
              </option>

              <option value="-balance_due">
                Highest balance
              </option>
            </SearchSelect>
          </div>
        </div>

        {invoiceQuery.isError ? (
          <div
            className="
              rounded-xl border
              border-red-200 bg-red-50
              px-4 py-3 text-sm
              text-red-700
            "
          >
            {invoiceQuery.error
              instanceof Error
              ? invoiceQuery.error.message
              : "Unable to load invoices."}
          </div>
        ) : null}

        <div
          className="
            overflow-hidden rounded-2xl
            border border-slate-200
            bg-white
          "
        >
          {invoiceQuery.isPending ? (
            <div
              className="
                px-6 py-16 text-center
                text-sm text-slate-600
              "
            >
              Loading invoices…
            </div>
          ) : null}

          {(
            !invoiceQuery.isPending
            &&
            invoices.length === 0
          ) ? (
            <div
              className="
                px-6 py-16 text-center
              "
            >
              <ReceiptText
                className="
                  mx-auto text-slate-400
                "
                size={34}
              />

              <h2
                className="
                  mt-3 font-semibold
                  text-slate-900
                "
              >
                No invoices found
              </h2>

              <p
                className="
                  mt-1 text-sm
                  text-slate-500
                "
              >
                Change the filters or generate
                an invoice from a fulfilled order.
              </p>

              {canCreate ? (
                <button
                  type="button"
                  onClick={() => {
                    setCreateOpen(
                      true,
                    );
                  }}
                  className="
                    mt-4 inline-flex
                    items-center gap-2
                    rounded-lg bg-blue-600
                    px-4 py-2.5
                    text-sm font-semibold
                    text-white
                  "
                >
                  <Plus size={16} />
                  Create Invoice
                </button>
              ) : null}
            </div>
          ) : null}

          {invoices.length > 0 ? (
            <>
              <div
                className="
                  divide-y divide-slate-200
                  lg:hidden
                "
              >
                {invoices.map(
                  (invoice) => (
                    <article
                      key={invoice.id}
                      className="p-4"
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
                            onClick={() => {
                              setDetailInvoiceId(
                                invoice.id,
                              );
                            }}
                            className="
                              font-semibold
                              text-blue-700
                              hover:underline
                            "
                          >
                            {invoice.invoice_number}
                          </button>

                          <p
                            className="
                              mt-1 text-sm
                              text-slate-600
                            "
                          >
                            {invoice.customer.name}
                          </p>
                        </div>

                        <span
                          className={`
                            rounded-full border
                            px-2.5 py-1 text-xs
                            font-semibold
                            ${statusClassName(
                              invoice.status,
                            )}
                          `}
                        >
                          {displayStatus(
                            invoice.status,
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
                          <dt className="text-slate-500">
                            Total
                          </dt>

                          <dd
                            className="
                              font-semibold
                              text-slate-900
                            "
                          >
                            ₹
                            {formatAmount(
                              invoice.total_amount,
                            )}
                          </dd>
                        </div>

                        <div>
                          <dt className="text-slate-500">
                            Balance
                          </dt>

                          <dd
                            className="
                              font-semibold
                              text-red-700
                            "
                          >
                            ₹
                            {formatAmount(
                              invoice.balance_due,
                            )}
                          </dd>
                        </div>

                        <div>
                          <dt className="text-slate-500">
                            Invoice date
                          </dt>

                          <dd className="text-slate-700">
                            {formatDate(
                              invoice.invoice_date,
                            )}
                          </dd>
                        </div>

                        <div>
                          <dt className="text-slate-500">
                            Due date
                          </dt>

                          <dd className="text-slate-700">
                            {formatDate(
                              invoice.due_date,
                            )}
                          </dd>
                        </div>
                      </dl>

                      <div
                        className="
                          mt-4 flex gap-2
                        "
                      >
                        <button
                          type="button"
                          onClick={() => {
                            setDetailInvoiceId(
                              invoice.id,
                            );
                          }}
                          className="
                            inline-flex flex-1
                            items-center
                            justify-center gap-2
                            rounded-lg border
                            border-slate-300
                            px-3 py-2 text-sm
                            font-semibold
                            text-slate-700
                          "
                        >
                          <Eye size={16} />
                          View
                        </button>

                        {(
                          canRecordPayment
                          &&
                          (
                            invoice.status === "ISSUED"
                            ||
                            invoice.status
                            ===
                            "PARTIALLY_PAID"
                          )
                          &&
                          Number(
                            invoice.balance_due,
                          ) > 0
                        ) ? (
                          <button
                            type="button"
                            onClick={() => {
                              openPayment(
                                invoice,
                              );
                            }}
                            className="
                              inline-flex flex-1
                              items-center
                              justify-center gap-2
                              rounded-lg
                              bg-emerald-600
                              px-3 py-2 text-sm
                              font-semibold
                              text-white
                            "
                          >
                            <CircleDollarSign
                              size={16}
                            />
                            Pay
                          </button>
                        ) : null}
                      </div>
                    </article>
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
                    min-w-full divide-y
                    divide-slate-200
                  "
                >
                  <thead className="bg-slate-50">
                    <tr>
                      {[
                        "Invoice",
                        "Customer",
                        "Status",
                        "Invoice Date",
                        "Due Date",
                        "Total",
                        "Paid",
                        "Balance",
                        "Actions",
                      ].map(
                        (heading) => (
                          <th
                            key={heading}
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-left
                              text-xs font-semibold
                              uppercase tracking-wide
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
                      divide-y divide-slate-100
                    "
                  >
                    {invoices.map(
                      (invoice) => (
                        <tr
                          key={invoice.id}
                          className="
                            hover:bg-slate-50
                          "
                        >
                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3
                            "
                          >
                            <button
                              type="button"
                              onClick={() => {
                                setDetailInvoiceId(
                                  invoice.id,
                                );
                              }}
                              className="
                                text-sm font-semibold
                                text-blue-700
                                hover:underline
                              "
                            >
                              {invoice.invoice_number}
                            </button>

                            <p
                              className="
                                mt-0.5 text-xs
                                text-slate-500
                              "
                            >
                              {invoice.sales_order
                                ?.so_number
                                ??
                                "—"}
                            </p>
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              text-slate-700
                            "
                          >
                            {invoice.customer.name}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3
                            "
                          >
                            <span
                              className={`
                                rounded-full border
                                px-2.5 py-1 text-xs
                                font-semibold
                                ${statusClassName(
                                  invoice.status,
                                )}
                              `}
                            >
                              {displayStatus(
                                invoice.status,
                              )}
                            </span>
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              text-slate-700
                            "
                          >
                            {formatDate(
                              invoice.invoice_date,
                            )}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              text-slate-700
                            "
                          >
                            {formatDate(
                              invoice.due_date,
                            )}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              font-medium
                              text-slate-900
                            "
                          >
                            ₹
                            {formatAmount(
                              invoice.total_amount,
                            )}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              text-emerald-700
                            "
                          >
                            ₹
                            {formatAmount(
                              invoice.amount_paid,
                            )}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              font-semibold
                              text-red-700
                            "
                          >
                            ₹
                            {formatAmount(
                              invoice.balance_due,
                            )}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3
                            "
                          >
                            <div
                              className="
                                flex items-center gap-2
                              "
                            >
                              <button
                                type="button"
                                title="View invoice"
                                onClick={() => {
                                  setDetailInvoiceId(
                                    invoice.id,
                                  );
                                }}
                                className="
                                  rounded-lg p-2
                                  text-slate-600
                                  hover:bg-slate-100
                                  hover:text-blue-700
                                "
                              >
                                <Eye size={17} />
                              </button>

                              {(
                                canRecordPayment
                                &&
                                (
                                  invoice.status
                                  ===
                                  "ISSUED"
                                  ||
                                  invoice.status
                                  ===
                                  "PARTIALLY_PAID"
                                )
                                &&
                                Number(
                                  invoice.balance_due,
                                ) > 0
                              ) ? (
                                <button
                                  type="button"
                                  title="Record payment"
                                  onClick={() => {
                                    openPayment(
                                      invoice,
                                    );
                                  }}
                                  className="
                                    rounded-lg p-2
                                    text-emerald-700
                                    hover:bg-emerald-50
                                  "
                                >
                                  <CircleDollarSign
                                    size={17}
                                  />
                                </button>
                              ) : null}
                            </div>
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            </>
          ) : null}

          {pagination ? (
            <div
              className="
                flex flex-col gap-3
                border-t border-slate-200
                bg-slate-50 px-4 py-3
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
                Page {pagination.page} of{" "}
                {pagination.total_pages || 1}
                {" · "}
                {pagination.total_items} invoices
              </p>

              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={
                    !pagination.has_previous
                  }
                  onClick={() => {
                    setPage(
                      (
                        current,
                      ) =>
                        Math.max(
                          1,
                          current - 1,
                        ),
                    );
                  }}
                  className="
                    flex-1 rounded-lg
                    border border-slate-300
                    bg-white px-4 py-2
                    text-sm font-semibold
                    text-slate-700
                    disabled:opacity-50
                    sm:flex-none
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
                      (
                        current,
                      ) =>
                        current + 1,
                    );
                  }}
                  className="
                    flex-1 rounded-lg
                    border border-slate-300
                    bg-white px-4 py-2
                    text-sm font-semibold
                    text-slate-700
                    disabled:opacity-50
                    sm:flex-none
                  "
                >
                  Next
                </button>
              </div>
            </div>
          ) : null}
        </div>
      </section>

      <InvoiceDialog
        open={createOpen}
        onClose={() => {
          setCreateOpen(
            false,
          );
        }}
        onCreated={(
          invoiceId,
        ) => {
          setDetailInvoiceId(
            invoiceId,
          );
        }}
      />

      <InvoiceDetailDialog
        open={
          Boolean(
            detailInvoiceId,
          )
        }
        invoiceId={
          detailInvoiceId
        }
        onClose={() => {
          setDetailInvoiceId(
            null,
          );
        }}
        onRecordPayment={
          openPayment
        }
      />

      <InvoicePaymentDialog
        open={
          Boolean(
            paymentInvoice,
          )
        }
        invoice={
          paymentInvoice
        }
        onClose={() => {
          setPaymentInvoice(
            null,
          );
        }}
        onRecorded={() => {
          if (paymentInvoice) {
            setDetailInvoiceId(
              paymentInvoice.id,
            );
          }
        }}
      />
    </>
  );
}
"use client";
import SearchSelect from "@/components/search-select";


import {
  useMemo,
  useState,
} from "react";

import {
  Banknote,
  Eye,
  RefreshCw,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import CustomerPaymentDetailDialog from "@/features/customer-payments/components/customer-payment-detail-dialog";

import {
  useCustomerPaymentList,
} from "@/features/customer-payments/hooks";

import {
  useCustomerList,
} from "@/features/customers/hooks";

import type {
  InvoicePaymentMethod,
} from "@/features/invoices/types";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

const paymentMethods: Array<{
  value: InvoicePaymentMethod;
  label: string;
}> = [
  {
    value: "BANK_TRANSFER",
    label: "Bank transfer",
  },
  {
    value: "UPI",
    label: "UPI",
  },
  {
    value: "CHEQUE",
    label: "Cheque",
  },
  {
    value: "CARD",
    label: "Card",
  },
  {
    value: "CASH",
    label: "Cash",
  },
  {
    value: "OTHER",
    label: "Other",
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

function displayPaymentMethod(
  value: string,
): string {
  return value
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

export default function CustomerPaymentsPage() {
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
    customerId,
    setCustomerId,
  ] = useState("");

  const [
    paymentMethod,
    setPaymentMethod,
  ] = useState<
    InvoicePaymentMethod | ""
  >("");

  const [
    sort,
    setSort,
  ] = useState(
    "-payment_date",
  );

  const [
    detailPaymentId,
    setDetailPaymentId,
  ] = useState<
    string | null
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
      "customer_payments.read",
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
        payment_method:
          paymentMethod
          ||
          undefined,
        sort,
      }),
      [
        customerId,
        page,
        paymentMethod,
        search,
        sort,
      ],
    );

  const paymentQuery =
    useCustomerPaymentList(
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
          Payment access unavailable
        </h1>

        <p
          className="
            mt-2 text-sm
            text-amber-800
          "
        >
          Your role does not include the
          customer_payments.read permission.
        </p>
      </section>
    );
  }

  const payments =
    paymentQuery.data
      ?.payments
    ??
    [];

  const pagination =
    paymentQuery.data
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

  return (
    <>
      <section className="space-y-5">
        <div
          className="
            flex flex-col gap-4
            sm:flex-row
            sm:items-start
            sm:justify-between
          "
        >
          <div
            className="
              flex items-center gap-3
            "
          >
            <div
              className="
                flex size-11
                items-center justify-center
                rounded-xl bg-emerald-100
                text-emerald-700
              "
            >
              <Banknote size={22} />
            </div>

            <div>
              <h1
                className="
                  text-2xl font-bold
                  text-slate-950
                "
              >
                Customer Payments
              </h1>

              <p
                className="
                  mt-1 text-sm
                  text-slate-600
                "
              >
                Review customer receipts,
                payment methods and invoice
                allocations.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => {
              void paymentQuery.refetch();
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
                paymentQuery.isFetching
                  ? "animate-spin"
                  : ""
              }
            />

            Refresh
          </button>
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
              htmlFor="payment-search"
              className="
                text-xs font-semibold
                uppercase tracking-wide
                text-slate-600
              "
            >
              Search
            </label>

            <input
              id="payment-search"
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
              placeholder="Payment, customer or reference"
            />
          </div>

          <div>
            <label
              htmlFor="payment-customer"
              className="
                text-xs font-semibold
                uppercase tracking-wide
                text-slate-600
              "
            >
              Customer
            </label>

            <SearchSelect
              id="payment-customer"
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
              htmlFor="payment-method"
              className="
                text-xs font-semibold
                uppercase tracking-wide
                text-slate-600
              "
            >
              Method
            </label>

            <SearchSelect
              id="payment-method"
              value={paymentMethod}
              onChange={(event) => {
                const nextMethod =
                  event.target.value;

                setPaymentMethod(
                  nextMethod === ""
                    ? ""
                    : nextMethod as
                      InvoicePaymentMethod,
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
                All methods
              </option>

              {paymentMethods.map(
                (method) => (
                  <option
                    key={method.value}
                    value={method.value}
                  >
                    {method.label}
                  </option>
                ),
              )}
            </SearchSelect>
          </div>

          <div>
            <label
              htmlFor="payment-sort"
              className="
                text-xs font-semibold
                uppercase tracking-wide
                text-slate-600
              "
            >
              Sort
            </label>

            <SearchSelect
              id="payment-sort"
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
              <option value="-payment_date">
                Newest payment
              </option>

              <option value="payment_date">
                Oldest payment
              </option>

              <option value="-amount">
                Highest amount
              </option>

              <option value="amount">
                Lowest amount
              </option>

              <option value="payment_number">
                Payment number
              </option>
            </SearchSelect>
          </div>
        </div>

        {paymentQuery.isError ? (
          <div
            className="
              rounded-xl border
              border-red-200 bg-red-50
              px-4 py-3 text-sm
              text-red-700
            "
          >
            {paymentQuery.error
              instanceof Error
              ? paymentQuery.error.message
              : "Unable to load payments."}
          </div>
        ) : null}

        <div
          className="
            overflow-hidden rounded-2xl
            border border-slate-200
            bg-white
          "
        >
          {paymentQuery.isPending ? (
            <div
              className="
                px-6 py-16 text-center
                text-sm text-slate-600
              "
            >
              Loading customer payments…
            </div>
          ) : null}

          {(
            !paymentQuery.isPending
            &&
            payments.length === 0
          ) ? (
            <div
              className="
                px-6 py-16 text-center
              "
            >
              <Banknote
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
                No payments found
              </h2>

              <p
                className="
                  mt-1 text-sm
                  text-slate-500
                "
              >
                Payments recorded against
                invoices will appear here.
              </p>
            </div>
          ) : null}

          {payments.length > 0 ? (
            <>
              <div
                className="
                  divide-y divide-slate-200
                  lg:hidden
                "
              >
                {payments.map(
                  (payment) => (
                    <article
                      key={payment.id}
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
                              setDetailPaymentId(
                                payment.id,
                              );
                            }}
                            className="
                              font-semibold
                              text-blue-700
                              hover:underline
                            "
                          >
                            {payment.payment_number}
                          </button>

                          <p
                            className="
                              mt-1 text-sm
                              text-slate-600
                            "
                          >
                            {payment.customer.name}
                          </p>
                        </div>

                        <p
                          className="
                            text-lg font-bold
                            text-emerald-700
                          "
                        >
                          ₹
                          {formatAmount(
                            payment.amount,
                          )}
                        </p>
                      </div>

                      <dl
                        className="
                          mt-4 grid grid-cols-2
                          gap-3 text-sm
                        "
                      >
                        <div>
                          <dt className="text-slate-500">
                            Date
                          </dt>

                          <dd className="text-slate-800">
                            {formatDate(
                              payment.payment_date,
                            )}
                          </dd>
                        </div>

                        <div>
                          <dt className="text-slate-500">
                            Method
                          </dt>

                          <dd className="text-slate-800">
                            {displayPaymentMethod(
                              payment.payment_method,
                            )}
                          </dd>
                        </div>

                        <div>
                          <dt className="text-slate-500">
                            Reference
                          </dt>

                          <dd className="text-slate-800">
                            {payment.reference_number
                              ??
                              "—"}
                          </dd>
                        </div>

                        <div>
                          <dt className="text-slate-500">
                            Allocations
                          </dt>

                          <dd className="text-slate-800">
                            {payment.allocation_count}
                          </dd>
                        </div>
                      </dl>

                      <button
                        type="button"
                        onClick={() => {
                          setDetailPaymentId(
                            payment.id,
                          );
                        }}
                        className="
                          mt-4 inline-flex w-full
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
                        View Payment
                      </button>
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
                        "Payment",
                        "Customer",
                        "Date",
                        "Method",
                        "Account",
                        "Reference",
                        "Amount",
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
                    {payments.map(
                      (payment) => (
                        <tr
                          key={payment.id}
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
                                setDetailPaymentId(
                                  payment.id,
                                );
                              }}
                              className="
                                text-sm font-semibold
                                text-blue-700
                                hover:underline
                              "
                            >
                              {payment.payment_number}
                            </button>

                            <p
                              className="
                                mt-0.5 text-xs
                                text-slate-500
                              "
                            >
                              {
                                payment
                                  .allocation_count
                              } allocation(s)
                            </p>
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              text-slate-700
                            "
                          >
                            {payment.customer.name}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              text-slate-700
                            "
                          >
                            {formatDate(
                              payment.payment_date,
                            )}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              text-slate-700
                            "
                          >
                            {displayPaymentMethod(
                              payment.payment_method,
                            )}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              text-slate-700
                            "
                          >
                            {payment.bank_account
                              ?.account_name
                              ??
                              "—"}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              text-slate-700
                            "
                          >
                            {payment.reference_number
                              ??
                              "—"}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              font-semibold
                              text-emerald-700
                            "
                          >
                            ₹
                            {formatAmount(
                              payment.amount,
                            )}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3
                            "
                          >
                            <button
                              type="button"
                              title="View payment"
                              onClick={() => {
                                setDetailPaymentId(
                                  payment.id,
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
                {pagination.total_items} payments
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
                      (current) =>
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

      <CustomerPaymentDetailDialog
        open={
          Boolean(
            detailPaymentId,
          )
        }
        paymentId={
          detailPaymentId
        }
        onClose={() => {
          setDetailPaymentId(
            null,
          );
        }}
      />
    </>
  );
}
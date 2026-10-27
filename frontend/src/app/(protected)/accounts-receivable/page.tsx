"use client";

import {
  useMemo,
  useState,
} from "react";

import {
  AlertTriangle,
  ChartNoAxesCombined,
  Clock3,
  RefreshCw,
  Users,
  WalletCards,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  useAccountsReceivable,
  useReceivableAging,
} from "@/features/receivables/hooks";

import type {
  ReceivableAgingBucketKey,
} from "@/features/receivables/types";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

const bucketOrder:
  ReceivableAgingBucketKey[] = [
    "current",
    "days_1_30",
    "days_31_60",
    "days_61_90",
    "days_over_90",
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

export default function AccountsReceivablePage() {
  const {
    authentication,
  } = useAuth();

  const [
    customerSearch,
    setCustomerSearch,
  ] = useState("");

  const [
    selectedBucket,
    setSelectedBucket,
  ] = useState<
    ReceivableAgingBucketKey | ""
  >("");

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

  const receivableQuery =
    useAccountsReceivable();

  const agingQuery =
    useReceivableAging();

  const receivable =
    receivableQuery.data;

  const aging =
    agingQuery.data;

  const filteredCustomers =
    useMemo(
      () => {
        const customers =
          receivable
            ?.customers
          ??
          [];

        const search =
          customerSearch
            .trim()
            .toLowerCase();

        if (!search) {
          return customers;
        }

        return customers.filter(
          (item) => (
            item.customer.name
              .toLowerCase()
              .includes(
                search,
              )
            ||
            item.customer.code
              .toLowerCase()
              .includes(
                search,
              )
          ),
        );
      },
      [
        customerSearch,
        receivable,
      ],
    );

  const filteredAgingItems =
    useMemo(
      () => {
        const invoices =
          aging
            ?.invoices
          ??
          [];

        if (!selectedBucket) {
          return invoices;
        }

        return invoices.filter(
          (item) =>
            item.bucket
            ===
            selectedBucket,
        );
      },
      [
        aging,
        selectedBucket,
      ],
    );

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
          Receivable access unavailable
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

  const loading =
    receivableQuery.isPending
    ||
    agingQuery.isPending;

  const fetching =
    receivableQuery.isFetching
    ||
    agingQuery.isFetching;

  async function refresh():
    Promise<void> {
    await Promise.all([
      receivableQuery.refetch(),
      agingQuery.refetch(),
    ]);
  }

  return (
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
              rounded-xl bg-violet-100
              text-violet-700
            "
          >
            <ChartNoAxesCombined
              size={22}
            />
          </div>

          <div>
            <h1
              className="
                text-2xl font-bold
                text-slate-950
              "
            >
              Accounts Receivable
            </h1>

            <p
              className="
                mt-1 text-sm
                text-slate-600
              "
            >
              Monitor outstanding customer
              balances and overdue aging.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => {
            void refresh();
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
              fetching
                ? "animate-spin"
                : ""
            }
          />

          Refresh
        </button>
      </div>

      {(
        receivableQuery.isError
        ||
        agingQuery.isError
      ) ? (
        <div
          className="
            rounded-xl border
            border-red-200 bg-red-50
            px-4 py-3 text-sm
            text-red-700
          "
        >
          {receivableQuery.error
            instanceof Error
            ? receivableQuery.error.message
            : agingQuery.error
              instanceof Error
              ? agingQuery.error.message
              : "Unable to load receivables."}
        </div>
      ) : null}

      {loading ? (
        <div
          className="
            rounded-2xl border
            border-slate-200 bg-white
            px-6 py-16 text-center
            text-sm text-slate-600
          "
        >
          Loading accounts receivable…
        </div>
      ) : null}

      {receivable ? (
        <div
          className="
            grid gap-4 sm:grid-cols-2
            xl:grid-cols-4
          "
        >
          <div
            className="
              rounded-2xl border
              border-slate-200
              bg-white p-5
            "
          >
            <WalletCards
              className="text-blue-600"
              size={22}
            />

            <p
              className="
                mt-4 text-sm font-medium
                text-slate-600
              "
            >
              Total outstanding
            </p>

            <p
              className="
                mt-1 text-2xl font-bold
                text-slate-950
              "
            >
              ₹
              {formatAmount(
                receivable
                  .total_outstanding,
              )}
            </p>
          </div>

          <div
            className="
              rounded-2xl border
              border-emerald-200
              bg-emerald-50 p-5
            "
          >
            <Clock3
              className="text-emerald-700"
              size={22}
            />

            <p
              className="
                mt-4 text-sm font-medium
                text-emerald-800
              "
            >
              Current
            </p>

            <p
              className="
                mt-1 text-2xl font-bold
                text-emerald-950
              "
            >
              ₹
              {formatAmount(
                receivable.total_current,
              )}
            </p>
          </div>

          <div
            className="
              rounded-2xl border
              border-red-200
              bg-red-50 p-5
            "
          >
            <AlertTriangle
              className="text-red-700"
              size={22}
            />

            <p
              className="
                mt-4 text-sm font-medium
                text-red-800
              "
            >
              Overdue
            </p>

            <p
              className="
                mt-1 text-2xl font-bold
                text-red-950
              "
            >
              ₹
              {formatAmount(
                receivable.total_overdue,
              )}
            </p>

            <p
              className="
                mt-1 text-xs text-red-700
              "
            >
              {
                receivable
                  .overdue_invoice_count
              } overdue invoice(s)
            </p>
          </div>

          <div
            className="
              rounded-2xl border
              border-violet-200
              bg-violet-50 p-5
            "
          >
            <Users
              className="text-violet-700"
              size={22}
            />

            <p
              className="
                mt-4 text-sm font-medium
                text-violet-800
              "
            >
              Customers owing
            </p>

            <p
              className="
                mt-1 text-2xl font-bold
                text-violet-950
              "
            >
              {receivable.customer_count}
            </p>

            <p
              className="
                mt-1 text-xs
                text-violet-700
              "
            >
              {receivable.invoice_count}
              {" "}outstanding invoice(s)
            </p>
          </div>
        </div>
      ) : null}

      {aging ? (
        <div
          className="
            rounded-2xl border
            border-slate-200
            bg-white p-5
          "
        >
          <div
            className="
              flex flex-col gap-2
              sm:flex-row
              sm:items-end
              sm:justify-between
            "
          >
            <div>
              <h2
                className="
                  text-lg font-semibold
                  text-slate-950
                "
              >
                Aging Overview
              </h2>

              <p
                className="
                  mt-1 text-sm
                  text-slate-600
                "
              >
                Outstanding balances grouped
                by days past due.
              </p>
            </div>

            <p
              className="
                text-xs text-slate-500
              "
            >
              As of{" "}
              {formatDate(
                aging.as_of,
              )}
            </p>
          </div>

          <div
            className="
              mt-5 grid gap-3
              sm:grid-cols-2
              xl:grid-cols-5
            "
          >
            {bucketOrder.map(
              (bucketKey) => {
                const bucket =
                  aging.buckets[
                    bucketKey
                  ];

                const selected =
                  selectedBucket
                  ===
                  bucketKey;

                return (
                  <button
                    key={bucketKey}
                    type="button"
                    onClick={() => {
                      setSelectedBucket(
                        selected
                          ? ""
                          : bucketKey,
                      );
                    }}
                    className={`
                      rounded-xl border p-4
                      text-left transition
                      ${
                        selected
                          ? (
                            "border-blue-500 "
                            +
                            "bg-blue-50 "
                            +
                            "ring-2 "
                            +
                            "ring-blue-100"
                          )
                          : (
                            "border-slate-200 "
                            +
                            "bg-slate-50 "
                            +
                            "hover:border-slate-300"
                          )
                      }
                    `}
                  >
                    <p
                      className="
                        text-xs font-semibold
                        uppercase tracking-wide
                        text-slate-600
                      "
                    >
                      {bucket.label}
                    </p>

                    <p
                      className="
                        mt-2 text-lg font-bold
                        text-slate-950
                      "
                    >
                      ₹
                      {formatAmount(
                        bucket.amount,
                      )}
                    </p>

                    <p
                      className="
                        mt-1 text-xs
                        text-slate-500
                      "
                    >
                      {bucket.invoice_count}
                      {" "}invoice(s)
                    </p>
                  </button>
                );
              },
            )}
          </div>
        </div>
      ) : null}

      {receivable ? (
        <div
          className="
            overflow-hidden rounded-2xl
            border border-slate-200
            bg-white
          "
        >
          <div
            className="
              flex flex-col gap-3
              border-b border-slate-200
              p-4 sm:flex-row
              sm:items-center
              sm:justify-between
            "
          >
            <div>
              <h2
                className="
                  font-semibold
                  text-slate-950
                "
              >
                Customer Balances
              </h2>

              <p
                className="
                  mt-1 text-sm
                  text-slate-600
                "
              >
                Outstanding and overdue totals
                by customer.
              </p>
            </div>

            <input
              type="search"
              value={customerSearch}
              onChange={(event) => {
                setCustomerSearch(
                  event.target.value,
                );
              }}
              className="
                w-full rounded-lg border
                border-slate-300
                bg-white px-3 py-2
                text-sm text-slate-950
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
                sm:max-w-xs
              "
              placeholder="Search customer"
            />
          </div>

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
                    "Customer",
                    "Invoices",
                    "Overdue Invoices",
                    "Outstanding",
                    "Overdue",
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
                {filteredCustomers.map(
                  (item) => (
                    <tr
                      key={item.customer.id}
                    >
                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-3
                        "
                      >
                        <p
                          className="
                            text-sm font-semibold
                            text-slate-950
                          "
                        >
                          {item.customer.name}
                        </p>

                        <p
                          className="
                            mt-0.5 text-xs
                            text-slate-500
                          "
                        >
                          {item.customer.code}
                        </p>
                      </td>

                      <td
                        className="
                          px-4 py-3 text-sm
                          text-slate-700
                        "
                      >
                        {item.invoice_count}
                      </td>

                      <td
                        className="
                          px-4 py-3 text-sm
                          text-red-700
                        "
                      >
                        {
                          item
                            .overdue_invoice_count
                        }
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-3 text-sm
                          font-semibold
                          text-slate-900
                        "
                      >
                        ₹
                        {formatAmount(
                          item
                            .total_outstanding,
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
                          item.total_overdue,
                        )}
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {aging ? (
        <div
          className="
            overflow-hidden rounded-2xl
            border border-slate-200
            bg-white
          "
        >
          <div
            className="
              border-b border-slate-200
              p-4
            "
          >
            <h2
              className="
                font-semibold
                text-slate-950
              "
            >
              Outstanding Invoices
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-600
              "
            >
              {selectedBucket
                ? (
                  aging.buckets[
                    selectedBucket
                  ].label
                )
                : "All aging buckets"}
            </p>
          </div>

          {filteredAgingItems.length === 0 ? (
            <div
              className="
                px-6 py-12 text-center
                text-sm text-slate-600
              "
            >
              No invoices in this aging bucket.
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
                      "Invoice",
                      "Customer",
                      "Due Date",
                      "Days Overdue",
                      "Invoice Balance",
                      "Net Receivable",
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
                  {filteredAgingItems.map(
                    (item) => (
                      <tr
                        key={item.invoice.id}
                      >
                        <td
                          className="
                            whitespace-nowrap
                            px-4 py-3
                          "
                        >
                          <p
                            className="
                              text-sm font-semibold
                              text-blue-700
                            "
                          >
                            {
                              item.invoice
                                .invoice_number
                            }
                          </p>

                          <p
                            className="
                              mt-0.5 text-xs
                              text-slate-500
                            "
                          >
                            {formatDate(
                              item.invoice
                                .invoice_date,
                            )}
                          </p>
                        </td>

                        <td
                          className="
                            whitespace-nowrap
                            px-4 py-3 text-sm
                            text-slate-700
                          "
                        >
                          {item.customer.name}
                        </td>

                        <td
                          className="
                            whitespace-nowrap
                            px-4 py-3 text-sm
                            text-slate-700
                          "
                        >
                          {formatDate(
                            item.invoice.due_date,
                          )}
                        </td>

                        <td
                          className="
                            whitespace-nowrap
                            px-4 py-3 text-sm
                            font-semibold
                          "
                        >
                          <span
                            className={
                              item.is_overdue
                                ? "text-red-700"
                                : "text-emerald-700"
                            }
                          >
                            {item.is_overdue
                              ? (
                                `${item.overdue_days} days`
                              )
                              : "Current"}
                          </span>
                        </td>

                        <td
                          className="
                            whitespace-nowrap
                            px-4 py-3 text-sm
                            text-slate-700
                          "
                        >
                          ₹
                          {formatAmount(
                            item.invoice
                              .balance_due,
                          )}
                        </td>

                        <td
                          className="
                            whitespace-nowrap
                            px-4 py-3 text-sm
                            font-bold
                            text-red-700
                          "
                        >
                          ₹
                          {formatAmount(
                            item.net_receivable,
                          )}
                        </td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : null}
    </section>
  );
}
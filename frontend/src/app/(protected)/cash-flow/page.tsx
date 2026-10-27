"use client";

import {
  useState,
} from "react";
import ReportExportActions from "@/features/documents/components/report-export-actions";
import {
  ArrowDown,
  ArrowUp,
  Banknote,
  CalendarDays,
  RefreshCw,
} from "lucide-react";

import {
  useCashFlowReport,
} from "@/features/accounting/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

function formatAmount(
  value: string | number | null | undefined,
): string {
  const amount = Number(value ?? 0);

  if (!Number.isFinite(amount)) {
    return "₹0.00";
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
  value: string | null | undefined,
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

  return date.toLocaleDateString(
    "en-IN",
  );
}

function getErrorMessage(
  error: unknown,
): string {
  if (error instanceof APIRequestError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to load cash flow report.";
}

function getDefaultDateRange() {
  const today =
    new Date();

  const start =
    new Date(
      today.getFullYear(),
      today.getMonth(),
      1,
    );

  const toInputDate = (
    value: Date,
  ) =>
    value
      .toISOString()
      .slice(0, 10);

  return {
    startDate:
      toInputDate(start),

    endDate:
      toInputDate(today),
  };
}

export default function CashFlowPage() {
  const defaults =
    getDefaultDateRange();

  const [
    startDate,
    setStartDate,
  ] = useState(
    defaults.startDate,
  );

  const [
    endDate,
    setEndDate,
  ] = useState(
    defaults.endDate,
  );

  const [
    appliedStartDate,
    setAppliedStartDate,
  ] = useState(
    defaults.startDate,
  );

  const [
    appliedEndDate,
    setAppliedEndDate,
  ] = useState(
    defaults.endDate,
  );

  const cashFlowQuery =
    useCashFlowReport({
      start_date:
        appliedStartDate,

      end_date:
        appliedEndDate,
    });

  const report =
    cashFlowQuery.data;

  function handleApply(): void {
    setAppliedStartDate(
      startDate,
    );

    setAppliedEndDate(
      endDate,
    );
  }

  return (
    <div
      className="
        mx-auto max-w-7xl
        space-y-6
      "
    >
      <header>
        <p
          className="
            text-sm font-semibold
            text-blue-600
          "
        >
          Finance
        </p>

        <h1
          className="
            mt-1 text-3xl
            font-bold text-slate-900
          "
        >
          Cash Flow
        </h1>

        <p
          className="
            mt-2 text-sm
            text-slate-600
          "
        >
          Review cash inflows,
          outflows and bank
          transaction activity.
        </p>
      </header>

      <section
        className="
          rounded-2xl border
          border-slate-200 bg-white
          p-5 shadow-sm
        "
      >
        <div
          className="
            grid gap-4
            md:grid-cols-[1fr_1fr_auto_auto]
            md:items-end
          "
        >
          <label
            className="
              block text-sm
              font-medium text-slate-700
            "
          >
            Start date

            <input
              type="date"
              value={startDate}
              onChange={(event) => {
                setStartDate(
                  event.target.value,
                );
              }}
              className="
                mt-2 w-full
                rounded-lg border
                border-slate-300
                px-3 py-2
                text-sm text-slate-900
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            />
          </label>

          <label
            className="
              block text-sm
              font-medium text-slate-700
            "
          >
            End date

            <input
              type="date"
              value={endDate}
              onChange={(event) => {
                setEndDate(
                  event.target.value,
                );
              }}
              className="
                mt-2 w-full
                rounded-lg border
                border-slate-300
                px-3 py-2
                text-sm text-slate-900
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            />
          </label>
        <ReportExportActions
        resourceType="CASH_FLOW"
        parameters={{
            start_date:
            appliedStartDate,
            end_date:
            appliedEndDate,
        }}
        disabled={
            cashFlowQuery.isFetching
        }
        />
          <button
            type="button"
            onClick={handleApply}
            className="
              inline-flex h-10
              items-center
              justify-center gap-2
              rounded-lg
              bg-blue-600
              px-4 text-sm
              font-semibold text-white
              hover:bg-blue-700
            "
          >
            <CalendarDays
              size={17}
            />

            Apply
          </button>
        </div>
      </section>

      {cashFlowQuery.isLoading && (
        <section
          className="
            rounded-2xl border
            border-slate-200 bg-white
            p-8 shadow-sm
          "
        >
          <div
            className="
              flex items-center
              gap-2 text-slate-600
            "
          >
            <RefreshCw
              size={18}
              className="animate-spin"
            />

            Loading cash flow...
          </div>
        </section>
      )}

      {cashFlowQuery.error && (
        <section
          className="
            rounded-2xl border
            border-red-200
            bg-red-50 p-6
          "
        >
          <p
            className="
              font-semibold text-red-900
            "
          >
            Unable to load cash flow
          </p>

          <p
            className="
              mt-2 text-sm
              text-red-700
            "
          >
            {getErrorMessage(
              cashFlowQuery.error,
            )}
          </p>
        </section>
      )}

      {report && (
        <>
          <section
            className="
              grid gap-4
              sm:grid-cols-2
              xl:grid-cols-4
            "
          >
            <SummaryCard
              title="Opening Balance"
              value={formatAmount(
                report.opening_balance,
              )}
              icon={
                <Banknote size={20} />
              }
            />

            <SummaryCard
              title="Money In"
              value={formatAmount(
                report.total_in,
              )}
              icon={
                <ArrowDown size={20} />
              }
            />

            <SummaryCard
              title="Money Out"
              value={formatAmount(
                report.total_out,
              )}
              icon={
                <ArrowUp size={20} />
              }
            />

            <SummaryCard
              title="Closing Balance"
              value={formatAmount(
                report.closing_balance,
              )}
              icon={
                <Banknote size={20} />
              }
            />
          </section>

          <section
            className="
              grid gap-4
              md:grid-cols-3
            "
          >
            <SummaryCard
              title="Net Cash Flow"
              value={formatAmount(
                report.net_cash_flow,
              )}
              icon={
                <Banknote size={20} />
              }
            />

            <SummaryCard
              title="Reconciled"
              value={String(
                report.reconciled_count,
              )}
              icon={
                <Banknote size={20} />
              }
            />

            <SummaryCard
              title="Unreconciled"
              value={String(
                report.unreconciled_count,
              )}
              icon={
                <Banknote size={20} />
              }
            />
          </section>

          <section
            className="
              overflow-hidden
              rounded-2xl border
              border-slate-200
              bg-white shadow-sm
            "
          >
            <div
              className="
                border-b
                border-slate-200
                px-6 py-5
              "
            >
              <h2
                className="
                  text-lg font-semibold
                  text-slate-900
                "
              >
                Daily Summary
              </h2>

              <p
                className="
                  mt-1 text-sm
                  text-slate-500
                "
              >
                {
                  formatDate(
                    report.start_date,
                  )
                }
                {" — "}
                {
                  formatDate(
                    report.end_date,
                  )
                }
              </p>
            </div>

            <div
              className="
                overflow-x-auto
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
                    <TableHeader>
                      Date
                    </TableHeader>

                    <TableHeader>
                      Money In
                    </TableHeader>

                    <TableHeader>
                      Money Out
                    </TableHeader>

                    <TableHeader>
                      Net Cash Flow
                    </TableHeader>
                  </tr>
                </thead>

                <tbody
                  className="
                    divide-y
                    divide-slate-100
                  "
                >
                  {
                    report
                      .daily_summary
                      .length
                    === 0
                      ? (
                        <tr>
                          <td
                            colSpan={4}
                            className="
                              px-6 py-8
                              text-center
                              text-sm
                              text-slate-500
                            "
                          >
                            No daily cash
                            flow activity.
                          </td>
                        </tr>
                      )
                      : (
                        report
                          .daily_summary
                          .map(
                            (
                              row,
                              index,
                            ) => (
                              <tr
                                key={
                                  String(
                                    (
                                      row
                                        .date
                                      ??
                                      index
                                    ),
                                  )
                                }
                              >
                                <TableCell>
                                  {
                                    formatDate(
                                      typeof row.date
                                      === "string"
                                        ? row.date
                                        : null,
                                    )
                                  }
                                </TableCell>

                                <TableCell>
                                  {
                                    formatAmount(
                                      row.money_in,
                                    )
                                  }
                                </TableCell>

                                <TableCell>
                                  {
                                    formatAmount(
                                      row.money_out,
                                    )
                                  }
                                </TableCell>

                                <TableCell>
                                  {
                                    formatAmount(
                                      row.net_cash_flow,
                                    )
                                  }
                                </TableCell>
                              </tr>
                            ),
                          )
                      )
                  }
                </tbody>
              </table>
            </div>
          </section>

          <section
            className="
              overflow-hidden
              rounded-2xl border
              border-slate-200
              bg-white shadow-sm
            "
          >
            <div
              className="
                border-b
                border-slate-200
                px-6 py-5
              "
            >
              <h2
                className="
                  text-lg font-semibold
                  text-slate-900
                "
              >
                Transactions
              </h2>

              <p
                className="
                  mt-1 text-sm
                  text-slate-500
                "
              >
                {
                  report
                    .transaction_count
                }
                {" transaction(s)"}
              </p>
            </div>

            <div className="overflow-x-auto">
              <table
                className="
                  min-w-full
                  divide-y
                  divide-slate-200
                "
              >
                <thead className="bg-slate-50">
                  <tr>
                    <TableHeader>
                      Date
                    </TableHeader>

                    <TableHeader>
                      Amount
                    </TableHeader>

                    <TableHeader>
                      Signed Amount
                    </TableHeader>
                  </tr>
                </thead>

                <tbody
                  className="
                    divide-y
                    divide-slate-100
                  "
                >
                  {
                    report
                      .transactions
                      .length
                    === 0
                      ? (
                        <tr>
                          <td
                            colSpan={3}
                            className="
                              px-6 py-8
                              text-center
                              text-sm
                              text-slate-500
                            "
                          >
                            No transactions
                            found.
                          </td>
                        </tr>
                      )
                      : (
                        report
                          .transactions
                          .map(
                            (
                              transaction,
                              index,
                            ) => (
                              <tr key={index}>
                                <TableCell>
                                  {
                                    formatDate(
                                      transaction
                                        .transaction_date,
                                    )
                                  }
                                </TableCell>

                                <TableCell>
                                  {
                                    formatAmount(
                                      transaction
                                        .amount,
                                    )
                                  }
                                </TableCell>

                                <TableCell>
                                  {
                                    formatAmount(
                                      transaction
                                        .signed_amount,
                                    )
                                  }
                                </TableCell>
                              </tr>
                            ),
                          )
                      )
                  }
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function SummaryCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <div
      className="
        rounded-2xl border
        border-slate-200 bg-white
        p-5 shadow-sm
      "
    >
      <div
        className="
          flex items-start
          justify-between gap-4
        "
      >
        <div>
          <p
            className="
              text-sm font-medium
              text-slate-500
            "
          >
            {title}
          </p>

          <p
            className="
              mt-2 text-2xl
              font-bold text-slate-900
            "
          >
            {value}
          </p>
        </div>

        <div
          className="
            rounded-xl bg-slate-100
            p-3 text-slate-700
          "
        >
          {icon}
        </div>
      </div>
    </div>
  );
}

function TableHeader({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <th
      className="
        px-6 py-3 text-left
        text-xs font-semibold
        uppercase tracking-wide
        text-slate-500
      "
    >
      {children}
    </th>
  );
}

function TableCell({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <td
      className="
        whitespace-nowrap
        px-6 py-4 text-sm
        text-slate-700
      "
    >
      {children}
    </td>
  );
}
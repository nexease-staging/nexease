"use client";

import {
  useState,
} from "react";
import ReportExportActions from "@/features/documents/components/report-export-actions";
import {
  RefreshCw,
  Scale,
} from "lucide-react";

import {
  useTrialBalance,
} from "@/features/accounting/hooks";

import type {
  TrialBalanceParameters,
} from "@/features/accounting/types";

import {
  APIRequestError,
} from "@/lib/api/client";

function formatAmount(
  value: string,
): string {
  const amount =
    Number(value);

  if (
    Number.isNaN(
      amount
    )
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
    return "Latest posted entries";
  }

  const parsedDate =
    new Date(value);

  if (
    Number.isNaN(
      parsedDate.getTime()
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
    "Unable to generate the trial balance."
  );
}

export default function TrialBalancePage() {
  const [
    asOfDate,
    setAsOfDate,
  ] = useState("");

  const [
    includeZeroBalances,
    setIncludeZeroBalances,
  ] = useState(true);

  const [
    parameters,
    setParameters,
  ] = useState<
    TrialBalanceParameters
  >({
    include_zero_balances: true,
  });

  const trialBalanceQuery =
    useTrialBalance(
      parameters
    );

  const trialBalance =
    trialBalanceQuery.data;

  function generateReport(): void {
    setParameters({
      as_of_date:
        asOfDate
        ||
        undefined,
      include_zero_balances:
        includeZeroBalances,
    });
  }

  return (
    <div className="space-y-6">
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
            mt-1 text-2xl font-bold
            tracking-tight text-slate-950
            sm:text-3xl
          "
        >
          Trial Balance
        </h1>

        <p
          className="
            mt-2 max-w-2xl text-sm
            leading-6 text-slate-600
          "
        >
          Compare debit and credit balances
          from posted journals and verify that
          the accounting records remain
          balanced.
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
            flex flex-col gap-4
            md:flex-row md:items-end
            md:justify-between
          "
        >
          <div
            className="
              flex flex-col gap-4
              sm:flex-row sm:items-end
            "
          >
            <label
              className="
                block text-sm font-medium
                text-slate-700
              "
            >
              As-of date

              <input
                type="date"
                value={asOfDate}
                onChange={(event) => {
                  setAsOfDate(
                    event.target.value
                  );
                }}
                className="
                  mt-2 w-full rounded-lg
                  border border-slate-300
                  px-3 py-2 text-sm
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />
            </label>

            <label
              className="
                flex items-center gap-3
                rounded-lg border
                border-slate-200
                px-4 py-2.5
              "
            >
              <input
                type="checkbox"
                checked={
                  includeZeroBalances
                }
                onChange={(event) => {
                  setIncludeZeroBalances(
                    event.target.checked
                  );
                }}
                className="
                  size-4 rounded
                  border-slate-300
                "
              />

              <span
                className="
                  text-sm font-medium
                  text-slate-700
                "
              >
                Include zero balances
              </span>
            </label>
          </div>

        <div
          className="
            flex flex-wrap items-center
            justify-end gap-2
          "
        >
          <ReportExportActions
            resourceType="TRIAL_BALANCE"
            parameters={{
              as_of_date:
                parameters.as_of_date,
              include_zero_balances:
                parameters.include_zero_balances,
            }}
            disabled={
              trialBalanceQuery.isFetching
            }
          />
          <button
            type="button"
            disabled={
              trialBalanceQuery
                .isFetching
            }
            onClick={generateReport}
            className="
              inline-flex items-center
              justify-center gap-2
              rounded-lg bg-blue-600
              px-4 py-2.5 text-sm
              font-semibold text-white
              hover:bg-blue-700
              disabled:opacity-50
            "
          >
            <RefreshCw
              size={17}
              className={
                trialBalanceQuery
                  .isFetching
                  ? "animate-spin"
                  : ""
              }
            />
            Generate report
          </button>
</div>  
        </div>
      </section>
      {trialBalanceQuery.isLoading ? (
        <section
          className="
            rounded-2xl border
            border-slate-200 bg-white
            px-6 py-16 text-center
            text-sm text-slate-500
          "
        >
          Generating trial balance...
        </section>
      ) : trialBalanceQuery.isError ? (
        <section
          className="
            rounded-2xl border
            border-red-200 bg-red-50
            px-6 py-10 text-center
          "
        >
          <p
            className="
              text-sm font-semibold
              text-red-700
            "
          >
            {
              getErrorMessage(
                trialBalanceQuery.error
              )
            }
          </p>
        </section>
      ) : trialBalance ? (
        <>
          <section
            className="
              grid gap-4
              sm:grid-cols-2
              lg:grid-cols-4
            "
          >
            <div
              className="
                rounded-2xl border
                border-slate-200
                bg-white p-5 shadow-sm
              "
            >
              <p
                className="
                  text-xs font-semibold
                  uppercase tracking-wide
                  text-slate-500
                "
              >
                As of
              </p>

              <p
                className="
                  mt-2 text-lg font-bold
                  text-slate-950
                "
              >
                {
                  formatDate(
                    trialBalance
                      .as_of_date
                  )
                }
              </p>
            </div>

            <div
              className="
                rounded-2xl border
                border-slate-200
                bg-white p-5 shadow-sm
              "
            >
              <p
                className="
                  text-xs font-semibold
                  uppercase tracking-wide
                  text-slate-500
                "
              >
                Debit balance
              </p>

              <p
                className="
                  mt-2 text-xl font-bold
                  text-slate-950
                "
              >
                {
                  formatAmount(
                    trialBalance
                      .total_debit_balance
                  )
                }
              </p>
            </div>

            <div
              className="
                rounded-2xl border
                border-slate-200
                bg-white p-5 shadow-sm
              "
            >
              <p
                className="
                  text-xs font-semibold
                  uppercase tracking-wide
                  text-slate-500
                "
              >
                Credit balance
              </p>

              <p
                className="
                  mt-2 text-xl font-bold
                  text-slate-950
                "
              >
                {
                  formatAmount(
                    trialBalance
                      .total_credit_balance
                  )
                }
              </p>
            </div>

            <div
              className={`
                rounded-2xl border p-5
                shadow-sm
                ${
                  trialBalance.is_balanced
                    ? (
                      "border-emerald-200 "
                      +
                      "bg-emerald-50"
                    )
                    : (
                      "border-red-200 "
                      +
                      "bg-red-50"
                    )
                }
              `}
            >
              <p
                className="
                  text-xs font-semibold
                  uppercase tracking-wide
                  text-slate-500
                "
              >
                Status
              </p>

              <div
                className="
                  mt-2 flex items-center
                  gap-2
                "
              >
                <Scale
                  size={20}
                  className={
                    trialBalance
                      .is_balanced
                      ? "text-emerald-700"
                      : "text-red-700"
                  }
                />

                <p
                  className={`
                    text-lg font-bold
                    ${
                      trialBalance
                        .is_balanced
                        ? "text-emerald-800"
                        : "text-red-800"
                    }
                  `}
                >
                  {
                    trialBalance
                      .is_balanced
                    ? "Balanced"
                    : "Out of balance"
                  }
                </p>
              </div>

              <p
                className="
                  mt-1 text-sm
                  text-slate-600
                "
              >
                Difference:{" "}
                {
                  formatAmount(
                    trialBalance
                      .difference
                  )
                }
              </p>
            </div>
          </section>

          <section
            className="
              overflow-hidden rounded-2xl
              border border-slate-200
              bg-white shadow-sm
            "
          >
            {trialBalance.rows.length
              ===
              0 ? (
              <div
                className="
                  px-6 py-16 text-center
                  text-sm text-slate-500
                "
              >
                No account balances were found
                for the selected date.
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
                        "Account",
                        "Type",
                        "Total debit",
                        "Total credit",
                        "Debit balance",
                        "Credit balance",
                      ].map(
                        (heading) => (
                          <th
                            key={heading}
                            className="
                              px-4 py-3
                              text-left text-xs
                              font-semibold
                              uppercase
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
                      divide-y divide-slate-100
                    "
                  >
                    {trialBalance.rows.map(
                      (row) => (
                        <tr
                          key={
                            row.account.id
                          }
                        >
                          <td className="px-4 py-3">
                            <p
                              className="
                                text-sm
                                font-semibold
                                text-slate-900
                              "
                            >
                              {
                                row.account
                                  .account_code
                              }
                              {" — "}
                              {
                                row.account
                                  .account_name
                              }
                            </p>

                            <p
                              className="
                                mt-1 text-xs
                                text-slate-500
                              "
                            >
                              {
                                row.account
                                  .account_subtype
                                ??
                                "No subtype"
                              }
                            </p>
                          </td>

                          <td
                            className="
                              px-4 py-3 text-sm
                              text-slate-700
                            "
                          >
                            {
                              row.account
                                .account_type
                            }
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3
                              text-right text-sm
                              text-slate-700
                            "
                          >
                            {
                              formatAmount(
                                row.total_debit
                              )
                            }
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3
                              text-right text-sm
                              text-slate-700
                            "
                          >
                            {
                              formatAmount(
                                row.total_credit
                              )
                            }
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3
                              text-right text-sm
                              font-semibold
                              text-slate-950
                            "
                          >
                            {
                              formatAmount(
                                row.debit_balance
                              )
                            }
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3
                              text-right text-sm
                              font-semibold
                              text-slate-950
                            "
                          >
                            {
                              formatAmount(
                                row.credit_balance
                              )
                            }
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>

                  <tfoot
                    className="
                      border-t-2
                      border-slate-300
                      bg-slate-50
                    "
                  >
                    <tr>
                      <td
                        colSpan={4}
                        className="
                          px-4 py-4
                          text-sm font-bold
                          text-slate-900
                        "
                      >
                        Trial balance totals
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                          text-right text-sm
                          font-bold
                          text-slate-950
                        "
                      >
                        {
                          formatAmount(
                            trialBalance
                              .total_debit_balance
                          )
                        }
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                          text-right text-sm
                          font-bold
                          text-slate-950
                        "
                      >
                        {
                          formatAmount(
                            trialBalance
                              .total_credit_balance
                          )
                        }
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}
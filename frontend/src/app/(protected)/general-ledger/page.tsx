"use client";
import SearchSelect from "@/components/search-select";


import {
  useState,
} from "react";
import ReportExportActions from "@/features/documents/components/report-export-actions";
import {
  BookOpen,
  Search,
} from "lucide-react";

import {
  useChartOfAccountList,
  useGeneralLedger,
} from "@/features/accounting/hooks";

import type {
  GeneralLedgerParameters,
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
    return "—";
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
    "Unable to generate the general ledger."
  );
}

export default function GeneralLedgerPage() {
  const [
    accountSearch,
    setAccountSearch,
  ] = useState("");

  const [
    accountId,
    setAccountId,
  ] = useState("");

  const [
    startDate,
    setStartDate,
  ] = useState("");

  const [
    endDate,
    setEndDate,
  ] = useState("");

  const [
    reportParameters,
    setReportParameters,
  ] = useState<
    GeneralLedgerParameters
  >({
    account_id: "",
  });

  const accountQuery =
    useChartOfAccountList({
      page: 1,
      page_size: 100,
      search:
        accountSearch
        ||
        undefined,
      sort: "account_code",
    });

  const ledgerQuery =
    useGeneralLedger(
      reportParameters,
      Boolean(
        reportParameters.account_id
      ),
    );

  const accounts =
    accountQuery
      .data
      ?.accounts
      ??
      [];

  const ledger =
    ledgerQuery.data;

  function generateReport(): void {
    if (!accountId) {
      return;
    }

    setReportParameters({
      account_id:
        accountId,
      start_date:
        startDate
        ||
        undefined,
      end_date:
        endDate
        ||
        undefined,
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
          General Ledger
        </h1>

        <p
          className="
            mt-2 max-w-2xl text-sm
            leading-6 text-slate-600
          "
        >
          Review posted movements, opening
          balances, running balances, and
          closing balances for an account.
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
          className="nx-list-filters
            grid gap-4
            md:grid-cols-2
            xl:grid-cols-4
          "
        >
          <label
            className="
              block text-sm font-medium
              text-slate-700
            "
          >
            Find account

            <div className="relative mt-2">
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
                value={accountSearch}
                onChange={(event) => {
                  setAccountSearch(
                    event.target.value
                  );
                }}
                placeholder={
                  "Filter account list"
                }
                className="
                  w-full rounded-lg border
                  border-slate-300 py-2
                  pl-9 pr-3 text-sm
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />
            </div>
          </label>

          <label
            className="
              block text-sm font-medium
              text-slate-700
            "
          >
            Ledger account

            <SearchSelect
              value={accountId}
              disabled={
                accountQuery.isLoading
              }
              onChange={(event) => {
                setAccountId(
                  event.target.value
                );
              }}
              className="
                mt-2 w-full rounded-lg
                border border-slate-300
                bg-white px-3 py-2
                text-sm outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            >
              <option value="">
                Select account
              </option>

              {accounts.map(
                (account) => (
                  <option
                    key={account.id}
                    value={account.id}
                  >
                    {account.account_code}
                    {" — "}
                    {account.account_name}
                  </option>
                ),
              )}
            </SearchSelect>
          </label>

          <label
            className="
              block text-sm font-medium
              text-slate-700
            "
          >
            Start date

            <input
              type="date"
              value={startDate}
              onChange={(event) => {
                setStartDate(
                  event.target.value
                );
              }}
              className="
                mt-2 w-full rounded-lg
                border border-slate-300
                px-3 py-2 text-sm
                outline-none
              "
            />
          </label>

          <label
            className="
              block text-sm font-medium
              text-slate-700
            "
          >
            End date

            <input
              type="date"
              value={endDate}
              onChange={(event) => {
                setEndDate(
                  event.target.value
                );
              }}
              className="
                mt-2 w-full rounded-lg
                border border-slate-300
                px-3 py-2 text-sm
                outline-none
              "
            />
          </label>
        </div>

        {accountQuery.isError ? (
          <p
            className="
              mt-3 text-sm text-red-700
            "
          >
            Unable to load chart of accounts.
          </p>
        ) : null}

        <div
          className="
            mt-4 flex flex-wrap
            items-center justify-end gap-2
          "
        >
        {reportParameters.account_id ? (
          <ReportExportActions
            resourceType="GENERAL_LEDGER"
            parameters={{
              account_id:
                reportParameters.account_id,
              start_date:
                reportParameters.start_date,
              end_date:
                reportParameters.end_date,
            }}
            disabled={
              ledgerQuery.isFetching
            }
          />
        ) : null}
          <button
            type="button"
            disabled={
              !accountId
              ||
              ledgerQuery.isFetching
            }
            onClick={generateReport}
            className="
              inline-flex items-center
              gap-2 rounded-lg
              bg-blue-600 px-4 py-2
              text-sm font-semibold
              text-white
              hover:bg-blue-700
              disabled:opacity-50
            "
          >
            <BookOpen size={17} />
            Generate ledger
          </button>
        </div>
      </section>

      {!reportParameters.account_id ? (
        <section
          className="
            rounded-2xl border
            border-dashed
            border-slate-300 bg-white
            px-6 py-16 text-center
          "
        >
          <BookOpen
            size={34}
            className="
              mx-auto text-slate-400
            "
          />

          <p
            className="
              mt-4 font-semibold
              text-slate-800
            "
          >
            Select a ledger account
          </p>

          <p
            className="
              mt-2 text-sm text-slate-500
            "
          >
            Choose an account and optional
            date range to generate its ledger.
          </p>
        </section>
      ) : ledgerQuery.isLoading
      ||
      ledgerQuery.isFetching ? (
        <section
          className="
            rounded-2xl border
            border-slate-200 bg-white
            px-6 py-16 text-center
            text-sm text-slate-500
          "
        >
          Generating general ledger...
        </section>
      ) : ledgerQuery.isError ? (
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
                ledgerQuery.error
              )
            }
          </p>
        </section>
      ) : ledger ? (
        <>
          <section
            className="
              grid gap-4
              sm:grid-cols-2
              xl:grid-cols-4
            "
          >
            {[
              {
                label:
                  "Opening balance",
                value:
                  ledger.opening_balance,
              },
              {
                label:
                  "Total debit",
                value:
                  ledger.total_debit,
              },
              {
                label:
                  "Total credit",
                value:
                  ledger.total_credit,
              },
              {
                label:
                  "Closing balance",
                value:
                  ledger.closing_balance,
              },
            ].map(
              (item) => (
                <div
                  key={item.label}
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
                    {item.label}
                  </p>

                  <p
                    className="
                      mt-2 text-xl font-bold
                      text-slate-950
                    "
                  >
                    {
                      formatAmount(
                        item.value
                      )
                    }
                  </p>
                </div>
              ),
            )}
          </section>

          <section
            className="
              overflow-hidden rounded-2xl
              border border-slate-200
              bg-white shadow-sm
            "
          >
            <header
              className="
                border-b border-slate-200
                px-5 py-4
              "
            >
              <h2
                className="
                  font-bold text-slate-900
                "
              >
                {
                  ledger.account
                    .account_code
                }
                {" — "}
                {
                  ledger.account
                    .account_name
                }
              </h2>

              <p
                className="
                  mt-1 text-sm text-slate-500
                "
              >
                {ledger.start_date
                  ? formatDate(
                      ledger.start_date
                    )
                  : "Beginning"}
                {" to "}
                {ledger.end_date
                  ? formatDate(
                      ledger.end_date
                    )
                  : "latest"}
              </p>
            </header>

            {ledger.entries.length === 0 ? (
              <div
                className="
                  px-6 py-14 text-center
                  text-sm text-slate-500
                "
              >
                No posted movements were found
                for this account and date range.
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
                        "Date",
                        "Journal",
                        "Description",
                        "Source",
                        "Debit",
                        "Credit",
                        "Balance",
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
                    {ledger.entries.map(
                      (
                        entry,
                        index,
                      ) => (
                        <tr
                          key={
                            `${entry.journal_number}-${index}`
                          }
                        >
                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              text-slate-700
                            "
                          >
                            {
                              formatDate(
                                entry
                                  .journal_date
                              )
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
                            {
                              entry
                                .journal_number
                            }
                          </td>

                          <td
                            className="
                              px-4 py-3 text-sm
                              text-slate-600
                            "
                          >
                            {
                              entry.description
                              ??
                              "—"
                            }
                          </td>

                          <td
                            className="
                              px-4 py-3 text-sm
                              text-slate-600
                            "
                          >
                            {entry.source_type}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3
                              text-right text-sm
                              text-slate-900
                            "
                          >
                            {
                              formatAmount(
                                entry.debit
                              )
                            }
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3
                              text-right text-sm
                              text-slate-900
                            "
                          >
                            {
                              formatAmount(
                                entry.credit
                              )
                            }
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3
                              text-right text-sm
                              font-bold
                              text-slate-950
                            "
                          >
                            {
                              formatAmount(
                                entry
                                  .running_balance
                              )
                            }
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}
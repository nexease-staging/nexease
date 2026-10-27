"use client";
import SearchSelect from "@/components/search-select";


import {
  useState,
} from "react";

import {
  Ban,
  CheckCircle2,
  CircleSlash2,
  LoaderCircle,
  SearchCheck,
  X,
} from "lucide-react";

import BankPaymentSuggestionActions from "@/features/banking/components/bank-payment-suggestion-actions";

import {
  useAutoMatchStatementLine,
  useBankPaymentSuggestionList,
  useBankStatement,
  useBankTransactionList,
  useCancelBankStatement,
  useIgnoreStatementLine,
  useMatchStatementLine,
} from "@/features/banking/hooks";

interface BankStatementDetailDialogProps {
  open: boolean;
  statementId: string;
  canReconcile: boolean;
  canCancel: boolean;
  onClose: () => void;
}

function formatAmount(
  value: string,
  currency = "INR",
): string {
  const amount = Number(value);

  if (Number.isNaN(amount)) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency,
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

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  ).format(parsed);
}

function statusClass(
  status: string,
): string {
  if (
    status === "RECONCILED"
    ||
    status === "MATCHED"
  ) {
    return "bg-emerald-100 text-emerald-700";
  }

  if (
    status === "CANCELLED"
    ||
    status === "IGNORED"
  ) {
    return "bg-slate-200 text-slate-700";
  }

  if (status === "PARTIALLY_RECONCILED") {
    return "bg-blue-100 text-blue-700";
  }

  return "bg-amber-100 text-amber-700";
}

export default function BankStatementDetailDialog({
  open,
  statementId,
  canReconcile,
  canCancel,
  onClose,
}: BankStatementDetailDialogProps) {
  const [selectedTransactions, setSelectedTransactions] =
    useState<Record<number, string>>({});

  const statementQuery =
    useBankStatement(
      statementId,
      open,
    );

  const statement =
    statementQuery.data;

  const paymentSuggestionQuery =
    useBankPaymentSuggestionList({
      page_size: 100,
      statement_id:
        statementId,
      sort: "-created_at",
    });

  const paymentSuggestions =
    paymentSuggestionQuery.data
      ?.bank_payment_suggestions
    ??
    [];

  const transactionQuery =
    useBankTransactionList({
      page_size: 100,
      bank_account_id:
        statement?.bank_account.id,
      reconciliation_status:
        "UNRECONCILED",
      sort: "-transaction_date,-created_at",
    });

  const autoMatchMutation =
    useAutoMatchStatementLine();
  const matchMutation =
    useMatchStatementLine();
  const ignoreMutation =
    useIgnoreStatementLine();
  const cancelMutation =
    useCancelBankStatement();

  if (!open) {
    return null;
  }

  const isMutating =
    autoMatchMutation.isPending
    ||
    matchMutation.isPending
    ||
    ignoreMutation.isPending
    ||
    cancelMutation.isPending;

  const transactions =
    transactionQuery.data
      ?.bank_transactions
    ??
    [];

  const currency =
    statement?.bank_account.currency
    ??
    "INR";

  const completedCount =
    statement
      ? (
        statement.matched_count
        +
        statement.ignored_count
      )
      : 0;

  const progress =
    statement
    &&
    statement.line_count > 0
      ? Math.round(
        (
          completedCount
          /
          statement.line_count
        )
        *
        100,
      )
      : 0;

  const actionError =
    autoMatchMutation.error
    ??
    matchMutation.error
    ??
    ignoreMutation.error
    ??
    cancelMutation.error
    ??
    transactionQuery.error
    ??
    paymentSuggestionQuery.error;

  function getPaymentSuggestion(
    lineNumber: number,
  ) {
    return (
      paymentSuggestions.find(
        (suggestion) =>
          String(
            suggestion.line_number,
          )
          ===
          String(
            lineNumber,
          )
          &&
          suggestion.status
          !==
          "REJECTED",
      )
      ??
      paymentSuggestions.find(
        (suggestion) =>
          String(
            suggestion.line_number,
          )
          ===
          String(
            lineNumber,
          ),
      )
      ??
      null
    );
  }

function autoMatch(
  lineNumber: number,
): void {
  autoMatchMutation.mutate({
    statementId,
    lineNumber,
    dateToleranceDays: 2,
  });
}

function manualMatch(
  lineNumber: number,
): void {
  const transactionId =
    selectedTransactions[lineNumber];

  if (!transactionId) {
    return;
  }

  matchMutation.mutate(
    {
      statementId,
      lineNumber,
      transactionId,
    },
    {
      onSuccess: () => {
        setSelectedTransactions(
          (current) => ({
            ...current,
            [lineNumber]: "",
          }),
        );
      },
    },
  );
}

function ignoreLine(
  lineNumber: number,
): void {
  ignoreMutation.mutate({
    statementId,
    lineNumber,
  });
}

function cancelStatement(): void {
  cancelMutation.mutate(
    statementId,
  );
}

  return (
    <div
      className="
        fixed inset-0 z-50
        flex items-center justify-center
        bg-slate-950/50 p-3 sm:p-4
      "
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target === event.currentTarget
          &&
          !isMutating
        ) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="bank-statement-detail-title"
        className="
          max-h-[94vh] w-full max-w-7xl
          overflow-y-auto rounded-2xl
          bg-white text-slate-900
          shadow-2xl
        "
      >
        <header
          className="
            sticky top-0 z-10
            flex items-start justify-between
            gap-4 border-b border-slate-200
            bg-white px-5 py-4 sm:px-6
          "
        >
          <div>
            <p
              className="
                text-xs font-semibold uppercase
                tracking-wide text-blue-600
              "
            >
              Bank Statement
            </p>

            <h2
              id="bank-statement-detail-title"
              className="
                mt-1 text-xl font-bold
                text-slate-900
              "
            >
              {statement?.statement_number
                ??
                "Statement details"}
            </h2>
          </div>

          <button
            type="button"
            aria-label="Close dialog"
            disabled={isMutating}
            onClick={onClose}
            className="
              rounded-lg p-2 text-slate-500
              hover:bg-slate-100
              disabled:opacity-50
            "
          >
            <X size={20} />
          </button>
        </header>

        {statementQuery.isLoading ? (
          <div
            className="
              flex items-center justify-center
              gap-2 px-6 py-24
              text-sm text-slate-500
            "
          >
            <LoaderCircle
              size={18}
              className="animate-spin"
            />
            Loading statement...
          </div>
        ) : statementQuery.isError ? (
          <div
            role="alert"
            className="
              m-6 rounded-lg border
              border-red-200 bg-red-50
              px-4 py-3 text-sm text-red-700
            "
          >
            {statementQuery.error.message}
          </div>
        ) : statement ? (
          <div className="space-y-6 p-5 sm:p-6">
            <div
              className="
                flex flex-col gap-4
                lg:flex-row lg:items-start
                lg:justify-between
              "
            >
              <div>
                <p className="text-sm text-slate-500">
                  {statement.bank_account.account_name}
                  {" · "}
                  {formatDate(
                    statement.statement_start_date,
                  )}
                  {" to "}
                  {formatDate(
                    statement.statement_end_date,
                  )}
                </p>

                <div
                  className="
                    mt-2 flex flex-wrap
                    items-center gap-3
                  "
                >
                  <span
                    className={`
                      rounded-full px-3 py-1
                      text-xs font-semibold
                      ${statusClass(statement.status)}
                    `}
                  >
                    {statement.status}
                  </span>

                  <span
                    className="
                      text-sm text-slate-500
                    "
                  >
                    {statement.source_type}
                    {statement.source_filename
                      ? ` · ${statement.source_filename}`
                      : ""}
                  </span>
                </div>
              </div>

              {canCancel
                &&
                statement.status !== "RECONCILED"
                &&
                statement.status !== "CANCELLED" ? (
                  <button
                    type="button"
                    disabled={isMutating}
                    onClick={cancelStatement}
                    className="
                      inline-flex items-center
                      justify-center gap-2
                      rounded-lg border
                      border-red-200 bg-white
                      px-4 py-2 text-sm
                      font-semibold text-red-700
                      hover:bg-red-50
                      disabled:opacity-50
                    "
                  >
                    {cancelMutation.isPending ? (
                      <LoaderCircle
                        size={16}
                        className="animate-spin"
                      />
                    ) : (
                      <Ban size={16} />
                    )}
                    Cancel statement
                  </button>
                ) : null}
            </div>

            <div
              className="
                grid gap-4 sm:grid-cols-2
                xl:grid-cols-5
              "
            >
              {[
                [
                  "Opening balance",
                  formatAmount(
                    statement.opening_balance,
                    currency,
                  ),
                ],
                [
                  "Closing balance",
                  formatAmount(
                    statement.closing_balance,
                    currency,
                  ),
                ],
                [
                  "Matched lines",
                  String(statement.matched_count),
                ],
                [
                  "Unmatched lines",
                  String(statement.unmatched_count),
                ],
                [
                  "Ignored lines",
                  String(statement.ignored_count),
                ],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="
                    rounded-xl border
                    border-slate-200 bg-slate-50
                    p-4
                  "
                >
                  <p
                    className="
                      text-xs font-semibold
                      uppercase tracking-wide
                      text-slate-500
                    "
                  >
                    {label}
                  </p>

                  <p
                    className="
                      mt-2 text-lg font-bold
                      text-slate-900
                    "
                  >
                    {value}
                  </p>
                </div>
              ))}
            </div>

            <div>
              <div
                className="
                  mb-2 flex items-center
                  justify-between gap-3
                "
              >
                <p
                  className="
                    text-sm font-semibold
                    text-slate-700
                  "
                >
                  Reconciliation progress
                </p>
                <p className="text-sm text-slate-500">
                  {completedCount} of {statement.line_count}
                  {" · "}
                  {progress}%
                </p>
              </div>

              <div
                className="
                  h-2 overflow-hidden
                  rounded-full bg-slate-200
                "
              >
                <div
                  className="
                    h-full rounded-full
                    bg-emerald-500 transition-all
                  "
                  style={{
                    width: `${progress}%`,
                  }}
                />
              </div>
            </div>

            {actionError ? (
              <div
                role="alert"
                className="
                  rounded-lg border
                  border-red-200 bg-red-50
                  px-4 py-3 text-sm text-red-700
                "
              >
                {actionError.message}
              </div>
            ) : null}

            <div
              className="
                overflow-x-auto rounded-xl
                border border-slate-200
              "
            >
              <table
                className="
                  min-w-[1100px] w-full
                  text-left text-sm
                "
              >
                <thead
                  className="
                    bg-slate-50 text-xs
                    uppercase tracking-wide
                    text-slate-500
                  "
                >
                  <tr>
                    <th className="px-4 py-3">Line</th>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Description</th>
                    <th className="px-4 py-3 text-right">Debit</th>
                    <th className="px-4 py-3 text-right">Credit</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Match / action</th>
                  </tr>
                </thead>

                <tbody
                  className="
                    divide-y divide-slate-200
                    bg-white
                  "
                >
                  {statement.lines.map((line) => (
                    <tr
                      key={line.line_number}
                      className="align-top"
                    >
                      <td className="px-4 py-4 font-medium">
                        {line.line_number}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        {formatDate(line.transaction_date)}
                      </td>
                      <td className="max-w-xs px-4 py-4">
                        <p className="font-medium text-slate-900">
                          {line.description ?? "—"}
                        </p>
                        <p className="mt-1 text-xs text-slate-500">
                          {line.external_reference ?? "No reference"}
                        </p>
                        {line.matched_transaction ? (
                          <p className="mt-2 text-xs font-semibold text-emerald-700">
                            {line.matched_transaction.transaction_number}
                          </p>
                        ) : null}
                      </td>
                      <td className="px-4 py-4 text-right whitespace-nowrap">
                        {formatAmount(line.debit_amount, currency)}
                      </td>
                      <td className="px-4 py-4 text-right whitespace-nowrap">
                        {formatAmount(line.credit_amount, currency)}
                      </td>
                      <td className="px-4 py-4">
                        <span
                          className={`
                            rounded-full px-2.5 py-1
                            text-xs font-semibold
                            ${statusClass(line.match_status)}
                          `}
                        >
                          {line.match_status}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        {canReconcile
                          &&
                          line.match_status === "UNMATCHED"
                          &&
                          statement.status !== "CANCELLED" ? (
                            <div className="min-w-80 space-y-2">
                              <div className="flex gap-2">
                                <SearchSelect
                                  value={
                                    selectedTransactions[
                                      line.line_number
                                    ]
                                    ??
                                    ""
                                  }
                                    disabled={
                                      isMutating
                                      ||
                                      transactionQuery.isLoading
                                      ||
                                      transactionQuery.isError
                                      ||
                                      transactions.length === 0
                                    }
                                  onChange={(event) => {
                                    setSelectedTransactions(
                                      (current) => ({
                                        ...current,
                                        [line.line_number]:
                                          event.target.value,
                                      }),
                                    );
                                  }}
                                  className="
                                    min-w-0 flex-1 rounded-lg
                                    border border-slate-300
                                    bg-white px-3 py-2
                                    text-xs text-slate-900
                                    outline-none
                                    focus:border-blue-500
                                  "
                                >
                                  <option value="">
                                    {transactionQuery.isLoading
                                      ? "Loading transactions..."
                                      : transactionQuery.isError
                                        ? "Unable to load transactions"
                                        : transactions.length === 0
                                          ? "No unreconciled transactions"
                                          : "Select transaction"}
                                  </option>
                                  {transactions.map(
                                    (transaction) => (
                                      <option
                                        key={transaction.id}
                                        value={transaction.id}
                                      >
                                        {formatDate(
                                          transaction.transaction_date,
                                        )}
                                        {" · "}
                                        {transaction.transaction_type}
                                        {" · "}
                                        {formatAmount(
                                          transaction.amount,
                                          currency,
                                        )}
                                      </option>
                                    ),
                                  )}
                                </SearchSelect>

                                <button
                                  type="button"
                                  title="Match selected transaction"
                                  disabled={
                                    isMutating
                                    ||
                                    !selectedTransactions[
                                      line.line_number
                                    ]
                                  }
                                    onClick={() => {
                                      manualMatch(
                                        line.line_number,
                                      );
                                    }}
                                  className="
                                    rounded-lg bg-blue-600
                                    px-3 py-2 text-xs
                                    font-semibold text-white
                                    hover:bg-blue-700
                                    disabled:opacity-50
                                  "
                                >
                                  Match
                                </button>
                              </div>

                              <div className="flex flex-wrap gap-2">
                                <button
                                  type="button"
                                  disabled={isMutating}
                                  onClick={() => {
                                    autoMatch(
                                      line.line_number,
                                    );
                                  }}
                                  className="
                                    inline-flex items-center
                                    gap-1.5 rounded-lg
                                    border border-blue-200
                                    px-3 py-1.5 text-xs
                                    font-semibold text-blue-700
                                    hover:bg-blue-50
                                    disabled:opacity-50
                                  "
                                >
                                  <SearchCheck size={14} />
                                  Auto-match
                                </button>

                                <button
                                  type="button"
                                  disabled={isMutating}
                                  onClick={() => {
                                    ignoreLine(
                                      line.line_number,
                                    );
                                  }}
                                  className="
                                    inline-flex items-center
                                    gap-1.5 rounded-lg
                                    border border-slate-300
                                    px-3 py-1.5 text-xs
                                    font-semibold text-slate-700
                                    hover:bg-slate-50
                                    disabled:opacity-50
                                  "
                                >
                                  <CircleSlash2 size={14} />
                                  Ignore
                                </button>
                              </div>
                              <BankPaymentSuggestionActions
                                statementId={
                                  statement.id
                                }
                                lineNumber={
                                  line.line_number
                                }
                                currency={
                                  currency
                                }
                                suggestion={
                                  getPaymentSuggestion(
                                    line.line_number,
                                  )
                                }
                                disabled={
                                  isMutating
                                  ||
                                  paymentSuggestionQuery
                                    .isLoading
                                }
                              />
                            </div>
                          ) : (
                            <div
                              className="
                                inline-flex items-center
                                gap-2 text-xs
                                text-slate-500
                              "
                            >
                              {line.match_status === "MATCHED" ? (
                                <CheckCircle2
                                  size={15}
                                  className="text-emerald-600"
                                />
                              ) : (
                                <CircleSlash2 size={15} />
                              )}
                              {line.match_status === "MATCHED"
                                ? "Transaction matched"
                                : line.match_status === "IGNORED"
                                  ? "Line ignored"
                                  : "No action available"}
                            </div>
                          )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {statement.lines.length === 0 ? (
                <div
                  className="
                    px-6 py-16 text-center
                    text-sm text-slate-500
                  "
                >
                  This statement contains no lines.
                </div>
              ) : null}
            </div>

            <div
              className="
                flex justify-end
                border-t border-slate-200
                pt-5
              "
            >
              <button
                type="button"
                disabled={isMutating}
                onClick={onClose}
                className="
                  rounded-lg border
                  border-slate-300 bg-white
                  px-4 py-2 text-sm
                  font-semibold text-slate-700
                  hover:bg-slate-50
                  disabled:opacity-50
                "
              >
                Close
              </button>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}

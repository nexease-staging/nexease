"use client";

import {
  CheckCircle2,
  LoaderCircle,
  X,
} from "lucide-react";

import {
  useBankTransaction,
  useReconcileBankTransaction,
} from "@/features/banking/hooks";

interface BankTransactionDetailDialogProps {
  open: boolean;
  transactionId: string;
  canReconcile: boolean;
  onClose: () => void;
}

function formatAmount(
  value: string,
  currency = "INR",
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
      currency,
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

  const parsed =
    new Date(value);

  if (
    Number.isNaN(
      parsed.getTime()
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
    parsed,
  );
}

export default function BankTransactionDetailDialog({
  open,
  transactionId,
  canReconcile,
  onClose,
}: BankTransactionDetailDialogProps) {
  const transactionQuery =
    useBankTransaction(
      transactionId,
      open,
    );

  const reconcileMutation =
    useReconcileBankTransaction();

  if (!open) {
    return null;
  }

  const transaction =
    transactionQuery.data;

  async function reconcile():
    Promise<void> {
    if (!transaction) {
      return;
    }

    await reconcileMutation
      .mutateAsync(
        transaction.id,
      );
  }

  const currency =
    transaction
      ?.bank_account
      .currency
    ??
    "INR";

  return (
    <div
      className="
        fixed inset-0 z-50
        flex items-center justify-center
        bg-slate-950/50 p-4
      "
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target
          ===
          event.currentTarget
          &&
          !reconcileMutation.isPending
        ) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={
          "bank-transaction-detail-title"
        }
        className="
          max-h-[92vh] w-full
          max-w-3xl overflow-y-auto
          rounded-2xl bg-white
          text-slate-900 shadow-2xl
        "
      >
        <header
          className="
            flex items-start justify-between
            gap-4 border-b
            border-slate-200 px-6 py-4
          "
        >
          <div>
            <p
              className="
                text-xs font-semibold
                uppercase tracking-wide
                text-blue-600
              "
            >
              Bank Transaction
            </p>

            <h2
              id={
                "bank-transaction-detail-title"
              }
              className="
                mt-1 text-xl font-bold
                text-slate-900
              "
            >
              {
                transaction
                  ?.transaction_number
                ??
                "Transaction details"
              }
            </h2>
          </div>

          <button
            type="button"
            aria-label="Close dialog"
            disabled={
              reconcileMutation.isPending
            }
            onClick={onClose}
            className="
              rounded-lg p-2
              text-slate-500
              hover:bg-slate-100
              disabled:opacity-50
            "
          >
            <X size={20} />
          </button>
        </header>

        {transactionQuery.isLoading ? (
          <div
            className="
              flex items-center justify-center
              gap-2 px-6 py-20
              text-sm text-slate-500
            "
          >
            <LoaderCircle
              size={18}
              className="animate-spin"
            />
            Loading transaction...
          </div>
        ) : transactionQuery.isError ? (
          <div
            role="alert"
            className="
              m-6 rounded-lg border
              border-red-200 bg-red-50
              px-4 py-3 text-sm
              text-red-700
            "
          >
            {
              transactionQuery
                .error.message
            }
          </div>
        ) : transaction ? (
          <div className="space-y-6 p-6">
            <div
              className="
                flex flex-wrap items-center
                justify-between gap-3
              "
            >
              <div>
                <p
                  className="
                    text-sm text-slate-500
                  "
                >
                  {
                    transaction
                      .bank_account
                      .account_name
                  }
                </p>

                <p
                  className="
                    mt-1 text-2xl font-bold
                    text-slate-950
                  "
                >
                  {formatAmount(
                    transaction.amount,
                    currency,
                  )}
                </p>
              </div>

              <span
                className={`
                  rounded-full px-3 py-1
                  text-xs font-semibold
                  ${
                    transaction
                      .reconciliation_status
                    ===
                    "RECONCILED"
                      ? (
                        "bg-emerald-100 "
                        +
                        "text-emerald-700"
                      )
                      : (
                        "bg-amber-100 "
                        +
                        "text-amber-700"
                      )
                  }
                `}
              >
                {
                  transaction
                    .reconciliation_status
                }
              </span>
            </div>

            <dl
              className="
                grid gap-4 rounded-xl
                border border-slate-200
                bg-slate-50 p-5
                sm:grid-cols-2
              "
            >
              {[
                [
                  "Type",
                  transaction
                    .transaction_type,
                ],
                [
                  "Date",
                  formatDate(
                    transaction
                      .transaction_date,
                  ),
                ],
                [
                  "Balance before",
                  formatAmount(
                    transaction
                      .balance_before,
                    currency,
                  ),
                ],
                [
                  "Balance after",
                  formatAmount(
                    transaction
                      .balance_after,
                    currency,
                  ),
                ],
                [
                  "External reference",
                  transaction
                    .external_reference
                  ??
                  "—",
                ],
                [
                  "Reconciled at",
                  formatDate(
                    transaction
                      .reconciled_at,
                  ),
                ],
                [
                  "Reference type",
                  transaction
                    .reference_type
                  ??
                  "—",
                ],
                [
                  "Reference ID",
                  transaction
                    .reference_id
                  ??
                  "—",
                ],
              ].map(
                ([
                  label,
                  value,
                ]) => (
                  <div key={label}>
                    <dt
                      className="
                        text-xs font-semibold
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      {label}
                    </dt>
                    <dd
                      className="
                        mt-1 text-sm
                        font-medium
                        text-slate-900
                      "
                    >
                      {value}
                    </dd>
                  </div>
                ),
              )}
            </dl>

            <div>
              <h3
                className="
                  text-sm font-semibold
                  text-slate-700
                "
              >
                Description
              </h3>

              <p
                className="
                  mt-2 rounded-lg border
                  border-slate-200 p-4
                  text-sm leading-6
                  text-slate-600
                "
              >
                {
                  transaction.description
                  ??
                  "No description provided."
                }
              </p>
            </div>

            {reconcileMutation.error ? (
              <div
                role="alert"
                className="
                  rounded-lg border
                  border-red-200 bg-red-50
                  px-4 py-3 text-sm
                  text-red-700
                "
              >
                {
                  reconcileMutation
                    .error.message
                }
              </div>
            ) : null}

            <div
              className="
                flex justify-end gap-3
                border-t border-slate-200
                pt-5
              "
            >
              <button
                type="button"
                onClick={onClose}
                className="
                  rounded-lg border
                  border-slate-300 bg-white
                  px-4 py-2 text-sm
                  font-semibold text-slate-700
                  hover:bg-slate-50
                "
              >
                Close
              </button>

              {
                canReconcile
                &&
                transaction
                  .reconciliation_status
                ===
                "UNRECONCILED"
                ? (
                  <button
                    type="button"
                    disabled={
                      reconcileMutation
                        .isPending
                    }
                    onClick={() => {
                      void reconcile();
                    }}
                    className="
                      inline-flex items-center
                      gap-2 rounded-lg
                      bg-emerald-600
                      px-4 py-2 text-sm
                      font-semibold text-white
                      hover:bg-emerald-700
                      disabled:opacity-50
                    "
                  >
                    {
                      reconcileMutation
                        .isPending
                      ? (
                        <LoaderCircle
                          size={16}
                          className="
                            animate-spin
                          "
                        />
                      )
                      : (
                        <CheckCircle2
                          size={16}
                        />
                      )
                    }

                    Reconcile
                  </button>
                )
                : null
              }
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}
"use client";

import {
  Ban,
  CheckCircle2,
  LoaderCircle,
  X,
} from "lucide-react";

import {
  useBankTransfer,
  useCancelBankTransfer,
  usePostBankTransfer,
} from "@/features/banking/hooks";

interface BankTransferDetailDialogProps {
  open: boolean;
  transferId: string;
  canPost: boolean;
  canCancel: boolean;
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

const statusStyles = {
  DRAFT:
    "bg-slate-100 text-slate-700",
  POSTED:
    "bg-emerald-100 text-emerald-700",
  CANCELLED:
    "bg-red-100 text-red-700",
};

export default function BankTransferDetailDialog({
  open,
  transferId,
  canPost,
  canCancel,
  onClose,
}: BankTransferDetailDialogProps) {
  const transferQuery =
    useBankTransfer(
      transferId,
      open,
    );

  const postMutation =
    usePostBankTransfer();

  const cancelMutation =
    useCancelBankTransfer();

  if (!open) {
    return null;
  }

  const transfer =
    transferQuery.data;

  const pending =
    postMutation.isPending
    ||
    cancelMutation.isPending;

  async function postTransfer():
    Promise<void> {
    if (!transfer) {
      return;
    }

    await postMutation.mutateAsync(
      transfer.id,
    );
  }

  async function cancelTransfer():
    Promise<void> {
    if (!transfer) {
      return;
    }

    await cancelMutation.mutateAsync(
      transfer.id,
    );
  }

  const error =
    postMutation.error
    ??
    cancelMutation.error;

  const currency =
    transfer
      ?.source_account
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
          !pending
        ) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={
          "bank-transfer-detail-title"
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
              Bank Transfer
            </p>

            <h2
              id={
                "bank-transfer-detail-title"
              }
              className="
                mt-1 text-xl font-bold
                text-slate-900
              "
            >
              {
                transfer
                  ?.transfer_number
                ??
                "Transfer details"
              }
            </h2>
          </div>

          <button
            type="button"
            aria-label="Close dialog"
            disabled={pending}
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

        {transferQuery.isLoading ? (
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
            Loading transfer...
          </div>
        ) : transferQuery.isError ? (
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
              transferQuery
                .error.message
            }
          </div>
        ) : transfer ? (
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
                    transfer
                      .source_account
                      .account_name
                  }
                  {" → "}
                  {
                    transfer
                      .destination_account
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
                    transfer.amount,
                    currency,
                  )}
                </p>
              </div>

              <span
                className={`
                  rounded-full px-3 py-1
                  text-xs font-semibold
                  ${
                    statusStyles[
                      transfer.status
                    ]
                  }
                `}
              >
                {transfer.status}
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
                  "Transfer date",
                  formatDate(
                    transfer
                      .transfer_date,
                  ),
                ],
                [
                  "Reference",
                  transfer.reference
                  ??
                  "—",
                ],
                [
                  "Source balance",
                  formatAmount(
                    transfer
                      .source_account
                      .current_balance,
                    currency,
                  ),
                ],
                [
                  "Destination balance",
                  formatAmount(
                    transfer
                      .destination_account
                      .current_balance,
                    currency,
                  ),
                ],
                [
                  "Posted at",
                  formatDate(
                    transfer.posted_at,
                  ),
                ],
                [
                  "Cancelled at",
                  formatDate(
                    transfer
                      .cancelled_at,
                  ),
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
                Notes
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
                  transfer.notes
                  ??
                  "No notes provided."
                }
              </p>
            </div>

            {error ? (
              <div
                role="alert"
                className="
                  rounded-lg border
                  border-red-200 bg-red-50
                  px-4 py-3 text-sm
                  text-red-700
                "
              >
                {error.message}
              </div>
            ) : null}

            <div
              className="
                flex flex-wrap justify-end
                gap-3 border-t
                border-slate-200 pt-5
              "
            >
              <button
                type="button"
                disabled={pending}
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

              {
                canCancel
                &&
                transfer.status
                ===
                "DRAFT"
                ? (
                  <button
                    type="button"
                    disabled={pending}
                    onClick={() => {
                      void cancelTransfer();
                    }}
                    className="
                      inline-flex items-center
                      gap-2 rounded-lg
                      bg-red-600 px-4 py-2
                      text-sm font-semibold
                      text-white hover:bg-red-700
                      disabled:opacity-50
                    "
                  >
                    {
                      cancelMutation
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
                        <Ban size={16} />
                      )
                    }

                    Cancel transfer
                  </button>
                )
                : null
              }

              {
                canPost
                &&
                transfer.status
                ===
                "DRAFT"
                ? (
                  <button
                    type="button"
                    disabled={pending}
                    onClick={() => {
                      void postTransfer();
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
                      postMutation
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

                    Post transfer
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
"use client";

import {
  Check,
  LoaderCircle,
  Play,
  Sparkles,
  X,
} from "lucide-react";

import {
  useConfirmBankPaymentSuggestion,
  useExecuteBankPaymentSuggestion,
  useGenerateBankPaymentSuggestion,
  useRejectBankPaymentSuggestion,
} from "@/features/banking/hooks";

import type {
  BankPaymentSuggestionSummary,
} from "@/features/banking/types";

interface BankPaymentSuggestionActionsProps {
  statementId: string;
  lineNumber: number;
  currency: string;
  suggestion:
    BankPaymentSuggestionSummary | null;
  disabled?: boolean;
}

function formatAmount(
  value: string,
  currency: string,
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

function formatConfidence(
  value: string,
): string {
  const confidence = Number(value);

  if (Number.isNaN(confidence)) {
    return value;
  }

  const percentage =
    confidence <= 1
      ? confidence * 100
      : confidence;

  return `${Math.round(percentage)}%`;
}

function suggestionStatusClass(
  suggestion:
    BankPaymentSuggestionSummary,
): string {
  if (suggestion.is_executed) {
    return "bg-emerald-100 text-emerald-700";
  }

  if (suggestion.status === "CONFIRMED") {
    return "bg-blue-100 text-blue-700";
  }

  if (suggestion.status === "REJECTED") {
    return "bg-slate-200 text-slate-700";
  }

  return "bg-amber-100 text-amber-700";
}

function suggestionStatusLabel(
  suggestion:
    BankPaymentSuggestionSummary,
): string {
  if (suggestion.is_executed) {
    return "EXECUTED";
  }

  return suggestion.status;
}

export default function BankPaymentSuggestionActions({
  statementId,
  lineNumber,
  currency,
  suggestion,
  disabled = false,
}: BankPaymentSuggestionActionsProps) {
  const generateMutation =
    useGenerateBankPaymentSuggestion();

  const confirmMutation =
    useConfirmBankPaymentSuggestion();

  const rejectMutation =
    useRejectBankPaymentSuggestion();

  const executeMutation =
    useExecuteBankPaymentSuggestion();

  const isPending =
    generateMutation.isPending
    ||
    confirmMutation.isPending
    ||
    rejectMutation.isPending
    ||
    executeMutation.isPending;

  const actionError =
    generateMutation.error
    ??
    confirmMutation.error
    ??
    rejectMutation.error
    ??
    executeMutation.error;

function generateSuggestion(): void {
if (suggestion) {
    return;
}

generateMutation.mutate({
    statementId,
    lineNumber,
});
}

function confirmSuggestion(): void {
if (!suggestion) {
    return;
}

confirmMutation.mutate(
    suggestion.id,
);
}

function rejectSuggestion(): void {
if (!suggestion) {
    return;
}

rejectMutation.mutate(
    suggestion.id,
);
}

function executeSuggestion(): void {
if (!suggestion) {
    return;
}

executeMutation.mutate(
    suggestion.id,
);
}

  if (!suggestion) {
    return (
      <div>
        <button
          type="button"
          disabled={
            disabled
            ||
            isPending
          }
          onClick={generateSuggestion}
          className="
            inline-flex items-center gap-1.5
            rounded-lg border border-violet-200
            px-3 py-1.5 text-xs font-semibold
            text-violet-700
            hover:bg-violet-50
            disabled:opacity-50
          "
        >
          {generateMutation.isPending ? (
            <LoaderCircle
              size={14}
              className="animate-spin"
            />
          ) : (
            <Sparkles size={14} />
          )}
          Suggest payment
        </button>

        {actionError ? (
          <p
            role="alert"
            className="
              mt-2 max-w-80 text-xs
              text-red-600
            "
          >
            {actionError.message}
          </p>
        ) : null}
      </div>
    );
  }

  const reference =
    suggestion.invoice
      ? (
        `${suggestion.invoice.invoice_number}`
        +
        ` · ${suggestion.invoice.customer.name}`
      )
      : suggestion.vendor_bill
        ? (
          `${suggestion.vendor_bill.bill_number}`
          +
          ` · ${suggestion.vendor_bill.supplier.name}`
        )
        : "No document";

  return (
    <div
      className="
        rounded-lg border border-violet-200
        bg-violet-50/60 p-3
      "
    >
      <div
        className="
          flex flex-wrap items-start
          justify-between gap-2
        "
      >
        <div>
          <p
            className="
              text-xs font-bold
              text-violet-900
            "
          >
            {suggestion.suggestion_type
              ===
              "CUSTOMER_RECEIPT"
                ? "Customer receipt"
                : "Supplier payment"}
          </p>

          <p
            className="
              mt-1 text-xs
              text-slate-700
            "
          >
            {reference}
          </p>
        </div>

        <span
          className={`
            rounded-full px-2 py-1
            text-[11px] font-semibold
            ${suggestionStatusClass(
              suggestion,
            )}
          `}
        >
          {suggestionStatusLabel(
            suggestion,
          )}
        </span>
      </div>

      <div
        className="
          mt-2 flex flex-wrap gap-x-4
          gap-y-1 text-xs text-slate-600
        "
      >
        <span>
          Amount:{" "}
          <strong className="text-slate-900">
            {formatAmount(
              suggestion.amount,
              currency,
            )}
          </strong>
        </span>

        <span>
          Confidence:{" "}
          <strong className="text-slate-900">
            {formatConfidence(
              suggestion.confidence,
            )}
          </strong>
        </span>
      </div>

      {suggestion.match_reason ? (
        <p
          className="
            mt-2 text-xs
            text-slate-600
          "
        >
          {suggestion.match_reason}
        </p>
      ) : null}

      {!suggestion.is_executed ? (
        <div
          className="
            mt-3 flex flex-wrap gap-2
          "
        >
          {suggestion.status === "PENDING" ? (
            <>
              <button
                type="button"
                disabled={
                  disabled
                  ||
                  isPending
                }
                onClick={confirmSuggestion}
                className="
                  inline-flex items-center gap-1
                  rounded-lg bg-emerald-600
                  px-3 py-1.5 text-xs
                  font-semibold text-white
                  hover:bg-emerald-700
                  disabled:opacity-50
                "
              >
                {confirmMutation.isPending ? (
                  <LoaderCircle
                    size={13}
                    className="animate-spin"
                  />
                ) : (
                  <Check size={13} />
                )}
                Confirm
              </button>

              <button
                type="button"
                disabled={
                  disabled
                  ||
                  isPending
                }
                onClick={rejectSuggestion}
                className="
                  inline-flex items-center gap-1
                  rounded-lg border
                  border-red-200 bg-white
                  px-3 py-1.5 text-xs
                  font-semibold text-red-700
                  hover:bg-red-50
                  disabled:opacity-50
                "
              >
                {rejectMutation.isPending ? (
                  <LoaderCircle
                    size={13}
                    className="animate-spin"
                  />
                ) : (
                  <X size={13} />
                )}
                Reject
              </button>
            </>
          ) : null}

          {suggestion.status === "CONFIRMED" ? (
            <button
              type="button"
              disabled={
                disabled
                ||
                isPending
              }
              onClick={executeSuggestion}
              className="
                inline-flex items-center gap-1
                rounded-lg bg-violet-600
                px-3 py-1.5 text-xs
                font-semibold text-white
                hover:bg-violet-700
                disabled:opacity-50
              "
            >
              {executeMutation.isPending ? (
                <LoaderCircle
                  size={13}
                  className="animate-spin"
                />
              ) : (
                <Play size={13} />
              )}
              Execute payment
            </button>
          ) : null}
            {suggestion.status === "REJECTED" ? (
            <p
                className="
                text-xs font-semibold
                text-slate-600
                "
            >
                Suggestion rejected
            </p>
            ) : null}
        </div>
      ) : (
        <p
          className="
            mt-3 text-xs font-semibold
            text-emerald-700
          "
        >
          Payment created and statement line reconciled.
        </p>
      )}

      {actionError ? (
        <p
          role="alert"
          className="
            mt-2 text-xs text-red-600
          "
        >
          {actionError.message}
        </p>
      ) : null}
    </div>
  );
}
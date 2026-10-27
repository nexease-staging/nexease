"use client";

import {
  AlertTriangle,
  LoaderCircle,
} from "lucide-react";

import {
  useDeactivateBankAccount,
} from "@/features/banking/hooks";

import type {
  BankAccountSummary,
} from "@/features/banking/types";

interface BankAccountDeactivateDialogProps {
  open: boolean;
  account:
    BankAccountSummary | null;
  onClose: () => void;
}

export default function BankAccountDeactivateDialog({
  open,
  account,
  onClose,
}: BankAccountDeactivateDialogProps) {
  const deactivateMutation =
    useDeactivateBankAccount();

  if (
    !open
    ||
    !account
  ) {
    return null;
  }

  async function confirm():
    Promise<void> {
    if (!account) {
      return;
    }

    await deactivateMutation
      .mutateAsync(
        account.id,
      );

    onClose();
  }

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
          !deactivateMutation
            .isPending
        ) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={
          "bank-account-deactivate-title"
        }
        className="
          w-full max-w-md
          rounded-2xl bg-white p-6
          text-slate-900 shadow-2xl
        "
      >
        <div
          className="
            flex size-11 items-center
            justify-center rounded-full
            bg-amber-100 text-amber-700
          "
        >
          <AlertTriangle size={22} />
        </div>

        <h2
          id={
            "bank-account-deactivate-title"
          }
          className="
            mt-4 text-lg font-bold
            text-slate-900
          "
        >
          Deactivate bank account?
        </h2>

        <p
          className="
            mt-2 text-sm leading-6
            text-slate-600
          "
        >
          <strong>
            {account.account_name}
          </strong>
          {" "}will no longer accept new
          transactions or transfers.
          Existing transaction history and
          balances will remain available.
        </p>

        <div
          className="
            mt-4 rounded-lg border
            border-amber-200 bg-amber-50
            px-4 py-3 text-sm
            text-amber-800
          "
        >
          Current balance:{" "}
          <strong>
            {new Intl.NumberFormat(
              "en-IN",
              {
                style: "currency",
                currency:
                  account.currency,
              },
            ).format(
              Number(
                account.current_balance,
              ),
            )}
          </strong>
        </div>

        {deactivateMutation.error ? (
          <div
            role="alert"
            className="
              mt-4 rounded-lg border
              border-red-200 bg-red-50
              px-4 py-3 text-sm
              text-red-700
            "
          >
            {
              deactivateMutation
                .error.message
            }
          </div>
        ) : null}

        <div
          className="
            mt-6 flex justify-end gap-3
          "
        >
          <button
            type="button"
            disabled={
              deactivateMutation
                .isPending
            }
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
            Cancel
          </button>

          <button
            type="button"
            disabled={
              deactivateMutation
                .isPending
            }
            onClick={() => {
              void confirm();
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
              deactivateMutation
                .isPending
              ? (
                <LoaderCircle
                  size={16}
                  className="animate-spin"
                />
              )
              : null
            }

            Deactivate
          </button>
        </div>
      </section>
    </div>
  );
}
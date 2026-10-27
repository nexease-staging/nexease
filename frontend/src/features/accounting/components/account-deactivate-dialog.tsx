"use client";

import {
  AlertTriangle,
  LoaderCircle,
} from "lucide-react";

import {
  useDeactivateChartOfAccount,
} from "@/features/accounting/hooks";

import type {
  ChartOfAccountSummary,
} from "@/features/accounting/types";

interface AccountDeactivateDialogProps {
  open: boolean;
  account:
    ChartOfAccountSummary | null;
  onClose: () => void;
}

export default function AccountDeactivateDialog({
  open,
  account,
  onClose,
}: AccountDeactivateDialogProps) {
  const deactivateMutation =
    useDeactivateChartOfAccount();

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
        flex items-center
        justify-center bg-slate-950/50
        p-4
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
          "account-deactivate-title"
        }
        className="
          w-full max-w-md
          rounded-2xl bg-white p-6
          shadow-2xl
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
          id="account-deactivate-title"
          className="
            mt-4 text-lg font-bold
            text-slate-900
          "
        >
          Deactivate account?
        </h2>

        <p
          className="
            mt-2 text-sm leading-6
            text-slate-600
          "
        >
          <strong>
            {account.account_code}
            {" — "}
            {account.account_name}
          </strong>
          {" "}will no longer be available
          for new accounting entries.
          Existing journal history will
          remain unchanged.
        </p>

        {account.is_system_account ? (
          <div
            role="alert"
            className="
              mt-4 rounded-lg border
              border-amber-200 bg-amber-50
              px-4 py-3 text-sm
              text-amber-800
            "
          >
            System accounts are protected
            and cannot be deactivated.
          </div>
        ) : null}

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
                .error
                .message
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
              ||
              account.is_system_account
            }
            onClick={() => {
              void confirm();
            }}
            className="
              inline-flex items-center
              gap-2 rounded-lg
              bg-red-600 px-4 py-2
              text-sm font-semibold
              text-white
              hover:bg-red-700
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
"use client";
import SearchSelect from "@/components/search-select";


import {
  useState,
} from "react";

import {
  FilePlus2,
  X,
} from "lucide-react";

import {
  useCreateCreditNote,
} from "@/features/credit-notes/hooks";

import {
  useSalesReturnList,
} from "@/features/sales-returns/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

interface CreditNoteDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (
    creditNoteId: string,
  ) => void;
}

function todayValue(): string {
  const now = new Date();

  const offset =
    now.getTimezoneOffset()
    *
    60_000;

  return new Date(
    now.getTime()
    -
    offset,
  )
    .toISOString()
    .slice(
      0,
      10,
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

  return "Unable to create the credit note.";
}

export default function CreditNoteDialog({
  open,
  onClose,
  onCreated,
}: CreditNoteDialogProps) {
  const [
    salesReturnId,
    setSalesReturnId,
  ] = useState("");

  const [
    creditNoteDate,
    setCreditNoteDate,
  ] = useState(
    todayValue(),
  );

  const [
    reason,
    setReason,
  ] = useState("");

  const [
    notes,
    setNotes,
  ] = useState("");

  const [
    formError,
    setFormError,
  ] = useState<string | null>(
    null,
  );

  const salesReturnQuery =
    useSalesReturnList({
      page: 1,
      page_size: 100,
      status: "CONFIRMED",
      sort: "-return_date",
    });

  const createMutation =
    useCreateCreditNote();

  const salesReturns =
    salesReturnQuery
      .data
      ?.sales_returns
      ??
      [];

  function resetDialog(): void {
    setSalesReturnId("");
    setCreditNoteDate(
      todayValue(),
    );
    setReason("");
    setNotes("");
    setFormError(null);
  }

  function closeDialog(): void {
    if (
      createMutation.isPending
    ) {
      return;
    }

    resetDialog();
    onClose();
  }

  async function submit():
    Promise<void> {
    setFormError(null);

    if (!salesReturnId) {
      setFormError(
        "Select a confirmed sales return.",
      );
      return;
    }

    try {
      const created =
        await createMutation
          .mutateAsync({
            sales_return_id:
              salesReturnId,
            credit_note_date:
              creditNoteDate
              ||
              undefined,
            reason:
              reason.trim()
              ||
              undefined,
            notes:
              notes.trim()
              ||
              undefined,
          });

      resetDialog();

      onCreated?.(
        created.id,
      );

      onClose();

    } catch (error) {
      setFormError(
        getErrorMessage(
          error,
        ),
      );
    }
  }

  if (!open) {
    return null;
  }

  return (
    <div
      className="
        fixed inset-0 z-50
        flex items-end justify-center
        bg-slate-950/50
        sm:items-center sm:p-6
      "
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target
          ===
          event.currentTarget
        ) {
          closeDialog();
        }
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={
          "credit-note-create-title"
        }
        className="
          flex max-h-[96dvh]
          w-full flex-col
          overflow-hidden bg-white
          shadow-2xl
          sm:max-w-2xl
          sm:rounded-2xl
        "
      >
        <header
          className="
            flex items-center
            justify-between gap-4
            border-b border-slate-200
            px-4 py-4 sm:px-6
          "
        >
          <div>
            <h2
              id="credit-note-create-title"
              className="
                text-lg font-bold
                text-slate-950
              "
            >
              Create credit note
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-500
              "
            >
              Generate a draft credit note
              from a confirmed sales return.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close"
            disabled={
              createMutation.isPending
            }
            onClick={
              closeDialog
            }
            className="
              rounded-lg p-2
              text-slate-500
              hover:bg-slate-100
              disabled:opacity-50
            "
          >
            <X className="size-5" />
          </button>
        </header>

        <div
          className="
            flex-1 space-y-5
            overflow-y-auto
            px-4 py-5 sm:px-6
          "
        >
          {formError && (
            <div
              role="alert"
              className="
                rounded-xl border
                border-red-200 bg-red-50
                px-4 py-3 text-sm
                text-red-700
              "
            >
              {formError}
            </div>
          )}

          <label
            className="
              block text-sm font-semibold
              text-slate-700
            "
          >
            Confirmed sales return

            <SearchSelect
              value={salesReturnId}
              disabled={
                salesReturnQuery.isLoading
                ||
                createMutation.isPending
              }
              onChange={(event) => {
                setSalesReturnId(
                  event.currentTarget.value,
                );

                setFormError(null);
              }}
              className="
                mt-2 w-full rounded-xl
                border border-slate-300
                bg-white px-3 py-2.5
                text-sm text-slate-900
              "
            >
              <option value="">
                Select sales return
              </option>

              {salesReturns.map(
                (salesReturn) => (
                  <option
                    key={salesReturn.id}
                    value={salesReturn.id}
                  >
                    {salesReturn.return_number}
                    {" — "}
                    {salesReturn.customer.name}
                    {" — "}
                    {salesReturn.total_amount}
                  </option>
                ),
              )}
            </SearchSelect>
          </label>

          {salesReturnQuery.isError && (
            <p
              className="
                text-sm text-red-600
              "
            >
              {getErrorMessage(
                salesReturnQuery.error,
              )}
            </p>
          )}

          <label
            className="
              block text-sm font-semibold
              text-slate-700
            "
          >
            Credit note date

            <input
              type="date"
              value={creditNoteDate}
              disabled={
                createMutation.isPending
              }
              onChange={(event) => {
                setCreditNoteDate(
                  event.currentTarget.value,
                );
              }}
              className="
                mt-2 w-full rounded-xl
                border border-slate-300
                bg-white px-3 py-2.5
                text-sm text-slate-900
              "
            />
          </label>

          <label
            className="
              block text-sm font-semibold
              text-slate-700
            "
          >
            Reason

            <textarea
              rows={3}
              maxLength={500}
              value={reason}
              disabled={
                createMutation.isPending
              }
              onChange={(event) => {
                setReason(
                  event.currentTarget.value,
                );
              }}
              className="
                mt-2 w-full rounded-xl
                border border-slate-300
                bg-white px-3 py-2.5
                text-sm text-slate-900
              "
            />
          </label>

          <label
            className="
              block text-sm font-semibold
              text-slate-700
            "
          >
            Notes

            <textarea
              rows={4}
              maxLength={1000}
              value={notes}
              disabled={
                createMutation.isPending
              }
              onChange={(event) => {
                setNotes(
                  event.currentTarget.value,
                );
              }}
              className="
                mt-2 w-full rounded-xl
                border border-slate-300
                bg-white px-3 py-2.5
                text-sm text-slate-900
              "
            />
          </label>
        </div>

        <footer
          className="
            flex flex-col-reverse gap-3
            border-t border-slate-200
            px-4 py-4
            sm:flex-row sm:justify-end
            sm:px-6
          "
        >
          <button
            type="button"
            disabled={
              createMutation.isPending
            }
            onClick={
              closeDialog
            }
            className="
              rounded-xl border
              border-slate-300
              px-4 py-2.5
              text-sm font-semibold
              text-slate-700
              hover:bg-slate-50
              disabled:opacity-50
            "
          >
            Cancel
          </button>

          <button
            type="button"
            disabled={
              createMutation.isPending
            }
            onClick={() => {
              void submit();
            }}
            className="
              inline-flex items-center
              justify-center gap-2
              rounded-xl bg-blue-600
              px-4 py-2.5
              text-sm font-semibold
              text-white
              hover:bg-blue-700
              disabled:opacity-50
            "
          >
            <FilePlus2 className="size-4" />

            {createMutation.isPending
              ? "Creating…"
              : "Create credit note"}
          </button>
        </footer>
      </div>
    </div>
  );
}
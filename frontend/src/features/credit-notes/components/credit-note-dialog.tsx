"use client";
import { FormSheet } from "@/components/form/form-sheet";
import SearchSelect from "@/components/search-select";


import {
  useState,
} from "react";

import {
  FilePlus2,
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
    <FormSheet title="New credit note" subtitle="Creates a draft credit note from a confirmed sales return." titleId="credit-note-create-title" onClose={closeDialog} busy={createMutation.isPending} size="md" footer={<div className="nxf-buttons"><button type="button" className="nx-button nx-secondary nxf-secondary-sm" disabled={createMutation.isPending} onClick={closeDialog}>Cancel</button><button type="button" className="nx-button" disabled={createMutation.isPending} onClick={() => { void submit(); }}><FilePlus2 size={16} aria-hidden="true" />{createMutation.isPending ? "Creating…" : "Create credit note"}</button></div>}>
      <div className="flex flex-col gap-4">
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
    </FormSheet>
  );
}

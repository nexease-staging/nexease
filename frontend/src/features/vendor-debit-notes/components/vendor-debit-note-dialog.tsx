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
  usePurchaseReturnList,
} from "@/features/purchase-returns/hooks";

import {
  useCreateVendorDebitNote,
} from "@/features/vendor-debit-notes/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

interface VendorDebitNoteDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (
    debitNoteId: string,
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

  return (
    "Unable to create the vendor debit note."
  );
}

function formatAmount(
  value: string,
): string {
  const amount = Number(value);

  if (
    Number.isNaN(amount)
  ) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency: "INR",
    },
  ).format(amount);
}

export default function VendorDebitNoteDialog({
  open,
  onClose,
  onCreated,
}: VendorDebitNoteDialogProps) {
  const [
    purchaseReturnId,
    setPurchaseReturnId,
  ] = useState("");

  const [
    debitNoteDate,
    setDebitNoteDate,
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

  const purchaseReturnQuery =
    usePurchaseReturnList({
      page: 1,
      page_size: 100,
      status: "CONFIRMED",
      sort: "-return_date",
    });

  const createMutation =
    useCreateVendorDebitNote();

  const selectedPurchaseReturn =
    purchaseReturnQuery
      .data
      ?.purchase_returns
      .find(
        (purchaseReturn) =>
          purchaseReturn.id
          ===
          purchaseReturnId,
      );

  function resetDialog(): void {
    setPurchaseReturnId("");
    setDebitNoteDate(
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

    if (!purchaseReturnId) {
      setFormError(
        "Select a confirmed purchase return.",
      );
      return;
    }

    try {
      const debitNote =
        await createMutation
          .mutateAsync({
            purchase_return_id:
              purchaseReturnId,
            debit_note_date:
              debitNoteDate
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
        debitNote.id,
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
          "vendor-debit-note-create-title"
        }
        className="
          flex max-h-[96dvh]
          w-full flex-col
          overflow-hidden bg-slate-50
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
            bg-white px-4 py-4
            sm:px-6
          "
        >
          <div>
            <h2
              id={
                "vendor-debit-note-create-title"
              }
              className="
                text-lg font-bold
                text-slate-950
              "
            >
              Create vendor debit note
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-500
              "
            >
              Convert a confirmed purchase return into supplier credit.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close dialog"
            disabled={
              createMutation.isPending
            }
            onClick={closeDialog}
            className="
              rounded-lg p-2
              text-slate-500
              hover:bg-slate-100
              hover:text-slate-900
              disabled:opacity-50
            "
          >
            <X size={20} />
          </button>
        </header>

        <div
          className="
            flex-1 overflow-y-auto
            px-4 py-5 sm:px-6
          "
        >
          <div className="space-y-5">
            <section
              className="
                space-y-4 rounded-xl
                border border-slate-200
                bg-white p-4 shadow-sm
                sm:p-5
              "
            >
              <label
                className="
                  block text-sm
                  font-semibold
                  text-slate-800
                "
              >
                Confirmed purchase return

                <SearchSelect
                  value={purchaseReturnId}
                  disabled={
                    purchaseReturnQuery
                      .isLoading
                    ||
                    createMutation
                      .isPending
                  }
                  onChange={(event) => {
                    setPurchaseReturnId(
                      event.currentTarget
                        .value,
                    );
                    setFormError(null);
                  }}
                  className="
                    mt-2 h-11 w-full
                    rounded-lg border
                    border-slate-300
                    bg-white px-3 text-sm
                    text-slate-950
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                  "
                >
                  <option value="">
                    Select purchase return
                  </option>

                  {(
                    purchaseReturnQuery
                      .data
                      ?.purchase_returns
                    ??
                    []
                  ).map(
                    (purchaseReturn) => (
                      <option
                        key={
                          purchaseReturn.id
                        }
                        value={
                          purchaseReturn.id
                        }
                      >
                        {
                          purchaseReturn
                            .return_number
                        }
                        {" - "}
                        {
                          purchaseReturn
                            .supplier.name
                        }
                        {" - "}
                        {formatAmount(
                          purchaseReturn
                            .total_amount,
                        )}
                      </option>
                    ),
                  )}
                </SearchSelect>
              </label>

              <label
                className="
                  block text-sm
                  font-semibold
                  text-slate-800
                "
              >
                Debit note date

                <input
                  type="date"
                  value={debitNoteDate}
                  disabled={
                    createMutation.isPending
                  }
                  onChange={(event) => {
                    setDebitNoteDate(
                      event.currentTarget
                        .value,
                    );
                  }}
                  className="
                    mt-2 h-11 w-full
                    rounded-lg border
                    border-slate-300
                    bg-white px-3 text-sm
                    text-slate-950
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                  "
                />
              </label>
            </section>

            {selectedPurchaseReturn
              ? (
                <section
                  className="
                    grid gap-4 rounded-xl
                    border border-blue-200
                    bg-blue-50 p-4
                    sm:grid-cols-2
                  "
                >
                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        text-blue-700
                      "
                    >
                      Supplier
                    </p>

                    <p
                      className="
                        mt-1 font-semibold
                        text-slate-950
                      "
                    >
                      {
                        selectedPurchaseReturn
                          .supplier.name
                      }
                    </p>
                  </div>

                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        text-blue-700
                      "
                    >
                      Credit value
                    </p>

                    <p
                      className="
                        mt-1 font-bold
                        text-slate-950
                      "
                    >
                      {formatAmount(
                        selectedPurchaseReturn
                          .total_amount,
                      )}
                    </p>
                  </div>

                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        text-blue-700
                      "
                    >
                      Vendor bill
                    </p>

                    <p
                      className="
                        mt-1 text-sm
                        text-slate-800
                      "
                    >
                      {
                        selectedPurchaseReturn
                          .vendor_bill
                          .bill_number
                      }
                    </p>
                  </div>

                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        text-blue-700
                      "
                    >
                      Items
                    </p>

                    <p
                      className="
                        mt-1 text-sm
                        text-slate-800
                      "
                    >
                      {
                        selectedPurchaseReturn
                          .item_count
                      }
                    </p>
                  </div>
                </section>
              )
              : null}

            <section
              className="
                grid gap-4 rounded-xl
                border border-slate-200
                bg-white p-4 shadow-sm
                sm:grid-cols-2 sm:p-5
              "
            >
              <label
                className="
                  text-sm font-semibold
                  text-slate-800
                "
              >
                Reason

                <textarea
                  rows={4}
                  maxLength={500}
                  value={reason}
                  disabled={
                    createMutation.isPending
                  }
                  onChange={(event) => {
                    setReason(
                      event.currentTarget
                        .value,
                    );
                  }}
                  className="
                    mt-2 w-full rounded-lg
                    border border-slate-300
                    bg-white px-3 py-2
                    text-sm text-slate-950
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                  "
                />
              </label>

              <label
                className="
                  text-sm font-semibold
                  text-slate-800
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
                      event.currentTarget
                        .value,
                    );
                  }}
                  className="
                    mt-2 w-full rounded-lg
                    border border-slate-300
                    bg-white px-3 py-2
                    text-sm text-slate-950
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                  "
                />
              </label>
            </section>

            {purchaseReturnQuery.error
              ? (
                <div
                  className="
                    rounded-xl border
                    border-red-200
                    bg-red-50 px-4 py-3
                    text-sm text-red-700
                  "
                >
                  {getErrorMessage(
                    purchaseReturnQuery
                      .error,
                  )}
                </div>
              )
              : null}

            {formError
              ? (
                <div
                  className="
                    rounded-xl border
                    border-red-200
                    bg-red-50 px-4 py-3
                    text-sm text-red-700
                  "
                >
                  {formError}
                </div>
              )
              : null}
          </div>
        </div>

        <footer
          className="
            flex items-center
            justify-end gap-2
            border-t border-slate-200
            bg-white px-4 py-4
            sm:px-6
          "
        >
          <button
            type="button"
            disabled={
              createMutation.isPending
            }
            onClick={closeDialog}
            className="
              rounded-lg border
              border-slate-300
              bg-white px-4 py-2
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
              ||
              !purchaseReturnId
            }
            onClick={() => {
              void submit();
            }}
            className="
              inline-flex items-center
              gap-2 rounded-lg
              bg-blue-600 px-4 py-2
              text-sm font-semibold
              text-white
              hover:bg-blue-700
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >
            <FilePlus2 size={17} />

            {createMutation.isPending
              ? "Creating…"
              : "Create debit note"}
          </button>
        </footer>
      </div>
    </div>
  );
}
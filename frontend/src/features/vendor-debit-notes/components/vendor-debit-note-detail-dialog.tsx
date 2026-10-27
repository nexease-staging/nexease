"use client";

import {
  useState,
} from "react";

import DocumentActions from "@/features/documents/components/document-actions";

import {
  BadgeCheck,
  RotateCcw,
  X,
  XCircle,
} from "lucide-react";

import {
  useCancelVendorDebitNote,
  useIssueVendorDebitNote,
  useVendorDebitNote,
} from "@/features/vendor-debit-notes/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

interface VendorDebitNoteDetailDialogProps {
  open: boolean;
  debitNoteId: string | null;
  canIssue: boolean;
  canCancel: boolean;
  onClose: () => void;
  onChanged?: () => void;
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
    "Unable to update the vendor debit note."
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

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
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
  ).format(date);
}

function statusClass(
  status: string,
): string {
  if (status === "ISSUED") {
    return (
      "bg-emerald-100 text-emerald-700"
    );
  }

  if (status === "CANCELLED") {
    return (
      "bg-red-100 text-red-700"
    );
  }

  return (
    "bg-amber-100 text-amber-700"
  );
}

export default function VendorDebitNoteDetailDialog({
  open,
  debitNoteId,
  canIssue,
  canCancel,
  onClose,
  onChanged,
}: VendorDebitNoteDetailDialogProps) {
  const [
    actionError,
    setActionError,
  ] = useState<string | null>(
    null,
  );

  const debitNoteQuery =
    useVendorDebitNote(
      debitNoteId ?? "",
      (
        open
        &&
        Boolean(
          debitNoteId,
        )
      ),
    );

  const issueMutation =
    useIssueVendorDebitNote();

  const cancelMutation =
    useCancelVendorDebitNote();

  const debitNote =
    debitNoteQuery.data;

  const actionPending =
    issueMutation.isPending
    ||
    cancelMutation.isPending;

  function closeDialog(): void {
    if (actionPending) {
      return;
    }

    setActionError(null);
    onClose();
  }

  async function issueDebitNote():
    Promise<void> {
    if (!debitNote) {
      return;
    }

    const accepted =
      window.confirm(
        (
          "Issue this vendor debit note? "
          +
          "The available credit will reduce "
          +
          "the vendor bill payable and an "
          +
          "accounting journal will be posted."
        ),
      );

    if (!accepted) {
      return;
    }

    setActionError(null);

    try {
      await issueMutation
        .mutateAsync(
          debitNote.id,
        );

      onChanged?.();

    } catch (error) {
      setActionError(
        getErrorMessage(error),
      );
    }
  }

  async function cancelDebitNote():
    Promise<void> {
    if (!debitNote) {
      return;
    }

    const accepted =
      window.confirm(
        "Cancel this draft vendor debit note?",
      );

    if (!accepted) {
      return;
    }

    setActionError(null);

    try {
      await cancelMutation
        .mutateAsync(
          debitNote.id,
        );

      onChanged?.();

    } catch (error) {
      setActionError(
        getErrorMessage(error),
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
          "vendor-debit-note-detail-title"
        }
        className="
          flex max-h-[96dvh]
          w-full flex-col
          overflow-hidden bg-slate-50
          shadow-2xl
          sm:max-w-5xl
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
                "vendor-debit-note-detail-title"
              }
              className="
                text-lg font-bold
                text-slate-950
              "
            >
              {debitNote
                ?.debit_note_number
                ??
                "Vendor debit note"}
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-500
              "
            >
              Supplier credit and payable application details
            </p>
          </div>

          <button
            type="button"
            aria-label="Close dialog"
            disabled={actionPending}
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
          {debitNoteQuery.isLoading
            ? (
              <div
                className="
                  rounded-xl border
                  border-slate-200
                  bg-white p-8
                  text-center text-sm
                  text-slate-500
                "
              >
                Loading vendor debit note…
              </div>
            )
            : null}

          {debitNoteQuery.error
            ? (
              <div
                className="
                  rounded-xl border
                  border-red-200 bg-red-50
                  px-4 py-3 text-sm
                  text-red-700
                "
              >
                {getErrorMessage(
                  debitNoteQuery.error,
                )}
              </div>
            )
            : null}

          {debitNote
            ? (
              <div className="space-y-5">
                <section
                  className="
                    grid gap-4 rounded-xl
                    border border-slate-200
                    bg-white p-4 shadow-sm
                    sm:grid-cols-2
                    lg:grid-cols-4
                    sm:p-5
                  "
                >
                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Status
                    </p>

                    <span
                      className={`
                        mt-2 inline-flex
                        rounded-full px-3 py-1
                        text-xs font-bold
                        ${statusClass(
                          debitNote.status,
                        )}
                      `}
                    >
                      {debitNote.status}
                    </span>
                  </div>

                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Debit note date
                    </p>

                    <p
                      className="
                        mt-2 font-semibold
                        text-slate-950
                      "
                    >
                      {formatDate(
                        debitNote
                          .debit_note_date,
                      )}
                    </p>
                  </div>

                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Supplier
                    </p>

                    <p
                      className="
                        mt-2 font-semibold
                        text-slate-950
                      "
                    >
                      {debitNote.supplier.name}
                    </p>

                    <p
                      className="
                        text-xs text-slate-500
                      "
                    >
                      {debitNote.supplier.code}
                    </p>
                  </div>

                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Total credit
                    </p>

                    <p
                      className="
                        mt-2 font-bold
                        text-slate-950
                      "
                    >
                      {formatAmount(
                        debitNote.total_amount,
                      )}
                    </p>
                  </div>
                </section>

                <section
                  className="
                    grid gap-4 rounded-xl
                    border border-slate-200
                    bg-white p-4 shadow-sm
                    sm:grid-cols-2
                    lg:grid-cols-4
                    sm:p-5
                  "
                >
                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        text-slate-500
                      "
                    >
                      Purchase return
                    </p>

                    <p
                      className="
                        mt-1 font-semibold
                        text-slate-950
                      "
                    >
                      {
                        debitNote
                          .purchase_return
                          .return_number
                      }
                    </p>
                  </div>

                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        text-slate-500
                      "
                    >
                      Vendor bill
                    </p>

                    <p
                      className="
                        mt-1 font-semibold
                        text-slate-950
                      "
                    >
                      {
                        debitNote
                          .vendor_bill
                          .bill_number
                      }
                    </p>
                  </div>

                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        text-slate-500
                      "
                    >
                      Applied amount
                    </p>

                    <p
                      className="
                        mt-1 font-semibold
                        text-emerald-700
                      "
                    >
                      {formatAmount(
                        debitNote
                          .applied_amount,
                      )}
                    </p>
                  </div>

                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        text-slate-500
                      "
                    >
                      Remaining credit
                    </p>

                    <p
                      className="
                        mt-1 font-semibold
                        text-blue-700
                      "
                    >
                      {formatAmount(
                        debitNote
                          .remaining_credit,
                      )}
                    </p>
                  </div>
                </section>

                <section
                  className="
                    overflow-hidden rounded-xl
                    border border-slate-200
                    bg-white shadow-sm
                  "
                >
                  <div
                    className="
                      border-b border-slate-200
                      px-4 py-3 sm:px-5
                    "
                  >
                    <h3
                      className="
                        font-bold text-slate-950
                      "
                    >
                      Debit note items
                    </h3>
                  </div>

                  <div
                    className="
                      divide-y divide-slate-200
                    "
                  >
                    {debitNote.items.map(
                      (item) => (
                        <div
                          key={item.product.id}
                          className="
                            grid gap-3 p-4
                            md:grid-cols-[1fr_repeat(3,140px)]
                            sm:p-5
                          "
                        >
                          <div>
                            <p
                              className="
                                font-semibold
                                text-slate-950
                              "
                            >
                              {item.product.name}
                            </p>

                            <p
                              className="
                                mt-1 text-xs
                                text-slate-500
                              "
                            >
                              {item.product.sku}
                            </p>
                          </div>

                          <div>
                            <p
                              className="
                                text-xs
                                text-slate-500
                              "
                            >
                              Quantity
                            </p>

                            <p
                              className="
                                mt-1 font-semibold
                                text-slate-950
                              "
                            >
                              {item.quantity}
                              {" "}
                              {item.product.unit}
                            </p>
                          </div>

                          <div>
                            <p
                              className="
                                text-xs
                                text-slate-500
                              "
                            >
                              Tax
                            </p>

                            <p
                              className="
                                mt-1 font-semibold
                                text-slate-950
                              "
                            >
                              {item.tax_rate}%
                            </p>
                          </div>

                          <div>
                            <p
                              className="
                                text-xs
                                text-slate-500
                              "
                            >
                              Line total
                            </p>

                            <p
                              className="
                                mt-1 font-semibold
                                text-slate-950
                              "
                            >
                              {formatAmount(
                                item.line_total,
                              )}
                            </p>
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                </section>

                <section
                  className="
                    grid gap-4 rounded-xl
                    border border-slate-200
                    bg-white p-4 shadow-sm
                    sm:grid-cols-2 sm:p-5
                  "
                >
                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        text-slate-500
                      "
                    >
                      Reason
                    </p>

                    <p
                      className="
                        mt-1 text-sm
                        text-slate-800
                      "
                    >
                      {debitNote.reason ?? "—"}
                    </p>
                  </div>

                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        text-slate-500
                      "
                    >
                      Notes
                    </p>

                    <p
                      className="
                        mt-1 text-sm
                        text-slate-800
                      "
                    >
                      {debitNote.notes ?? "—"}
                    </p>
                  </div>
                </section>

                {actionError
                  ? (
                    <div
                      className="
                        rounded-xl border
                        border-red-200 bg-red-50
                        px-4 py-3 text-sm
                        text-red-700
                      "
                    >
                      {actionError}
                    </div>
                  )
                  : null}
              </div>
            )
            : null}
        </div>

        <footer
          className="
            flex flex-wrap items-center
            justify-end gap-2
            border-t border-slate-200
            bg-white px-4 py-4
            sm:px-6
          "
        >
          <button
            type="button"
            disabled={actionPending}
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
            Close
          </button>

          {debitNote ? (
            <DocumentActions
              documentType="VENDOR_DEBIT_NOTE"
              documentId={debitNote.id}
              documentNumber={
                debitNote.debit_note_number
              }
              disabled={actionPending}
            />
          ) : null}

          {debitNote?.status
            ===
            "DRAFT"
            &&
            canCancel
            ? (
              <button
                type="button"
                disabled={actionPending}
                onClick={() => {
                  void cancelDebitNote();
                }}
                className="
                  inline-flex items-center
                  gap-2 rounded-lg
                  border border-red-300
                  bg-white px-4 py-2
                  text-sm font-semibold
                  text-red-700
                  hover:bg-red-50
                  disabled:opacity-50
                "
              >
                <XCircle size={17} />
                Cancel debit note
              </button>
            )
            : null}

          {debitNote?.status
            ===
            "DRAFT"
            &&
            canIssue
            ? (
              <button
                type="button"
                disabled={actionPending}
                onClick={() => {
                  void issueDebitNote();
                }}
                className="
                  inline-flex items-center
                  gap-2 rounded-lg
                  bg-emerald-600 px-4 py-2
                  text-sm font-semibold
                  text-white
                  hover:bg-emerald-700
                  disabled:opacity-50
                "
              >
                {issueMutation.isPending
                  ? (
                    <RotateCcw
                      size={17}
                      className="animate-spin"
                    />
                  )
                  : (
                    <BadgeCheck size={17} />
                  )}

                Issue debit note
              </button>
            )
            : null}
        </footer>
      </div>
    </div>
  );
}
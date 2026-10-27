"use client";
import SearchSelect from "@/components/search-select";


import {
  useState,
} from "react";

import {
  RotateCcw,
  X,
} from "lucide-react";

import {
  useInvoice,
  useInvoiceList,
} from "@/features/invoices/hooks";

import {
  useCreateSalesReturn,
} from "@/features/sales-returns/hooks";

import type {
  SalesReturnItemInput,
} from "@/features/sales-returns/types";

import {
  APIRequestError,
} from "@/lib/api/client";

interface SalesReturnDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (
    salesReturnId: string,
  ) => void;
}

interface ReturnLine {
  product_id: string;
  quantity: string;
  reason: string;
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

  return "Unable to create the sales return.";
}

export default function SalesReturnDialog({
  open,
  onClose,
  onCreated,
}: SalesReturnDialogProps) {
  const [
    invoiceId,
    setInvoiceId,
  ] = useState("");

  const [
    returnDate,
    setReturnDate,
  ] = useState(
    todayValue(),
  );

  const [
    lines,
    setLines,
  ] = useState<ReturnLine[]>([]);

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

  const invoiceListQuery =
    useInvoiceList({
      page: 1,
      page_size: 100,
      sort: "-created_at",
    });

  const invoiceQuery =
    useInvoice(
      invoiceId,
      (
        open
        &&
        Boolean(
          invoiceId,
        )
      ),
    );

  const createMutation =
    useCreateSalesReturn();

  const invoices =
    (
      invoiceListQuery
        .data
        ?.invoices
      ??
      []
    ).filter(
      (invoice) =>
        invoice.status
        !==
        "DRAFT"
        &&
        invoice.status
        !==
        "CANCELLED",
    );

  const invoice =
    invoiceQuery.data;

  function resetDialog(): void {
    setInvoiceId("");
    setReturnDate(
      todayValue(),
    );
    setLines([]);
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

  function selectInvoice(
    value: string,
  ): void {
    setInvoiceId(
      value,
    );

    setLines([]);
    setFormError(null);
  }

  function getLine(
    productId: string,
  ): ReturnLine {
    return (
      lines.find(
        (line) =>
          line.product_id
          ===
          productId,
      )
      ??
      {
        product_id: productId,
        quantity: "",
        reason: "",
      }
    );
  }

  function updateLine(
    productId: string,
    changes: Partial<ReturnLine>,
  ): void {
    setLines(
      (current) => {
        const existing =
          current.some(
            (line) =>
              line.product_id
              ===
              productId,
          );

        if (!existing) {
          return [
            ...current,
            {
              product_id:
                productId,
              quantity: "",
              reason: "",
              ...changes,
            },
          ];
        }

        return current.map(
          (line) =>
            line.product_id
            ===
            productId
              ? {
                  ...line,
                  ...changes,
                }
              : line,
        );
      },
    );

    setFormError(null);
  }

  async function submit():
    Promise<void> {
    setFormError(null);

    if (!invoiceId) {
      setFormError(
        "Select an invoice.",
      );
      return;
    }

    const selectedItems:
      SalesReturnItemInput[] =
      lines
        .filter(
          (line) =>
            Number(
              line.quantity,
            )
            >
            0,
        )
        .map(
          (line) => ({
            product_id:
              line.product_id,
            quantity:
              line.quantity,
            reason:
              line.reason.trim()
              ||
              undefined,
          }),
        );

    if (!selectedItems.length) {
      setFormError(
        (
          "Enter a return quantity for "
          +
          "at least one item."
        ),
      );
      return;
    }

    for (
      const selectedItem
      of selectedItems
    ) {
      const invoiceItem =
        invoice
          ?.items
          .find(
            (item) =>
              item.product.id
              ===
              selectedItem.product_id,
          );

      if (!invoiceItem) {
        setFormError(
          (
            "A selected product is no "
            +
            "longer available."
          ),
        );
        return;
      }

      if (
        Number(
          selectedItem.quantity,
        )
        >
        Number(
          invoiceItem.quantity,
        )
      ) {
        setFormError(
          (
            `Return quantity for ${
              invoiceItem.product.name
            } exceeds the invoiced quantity.`
          ),
        );
        return;
      }
    }

    try {
      const created =
        await createMutation
          .mutateAsync({
            invoice_id:
              invoiceId,
            return_date:
              returnDate
              ||
              undefined,
            items:
              selectedItems,
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
          "sales-return-title"
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
              id="sales-return-title"
              className="
                text-lg font-bold
                text-slate-950
              "
            >
              Create sales return
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-500
              "
            >
              Select an invoice and enter
              the quantities returned.
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

          <div
            className="
              grid gap-4
              md:grid-cols-2
            "
          >
            <label
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Invoice

              <SearchSelect
                value={invoiceId}
                disabled={
                  invoiceListQuery.isLoading
                  ||
                  createMutation.isPending
                }
                onChange={(event) => {
                  selectInvoice(
                    event.currentTarget.value,
                  );
                }}
                className="
                  mt-2 w-full rounded-xl
                  border border-slate-300
                  bg-white px-3 py-2.5
                  text-sm text-slate-900
                "
              >
                <option value="">
                  Select invoice
                </option>

                {invoices.map(
                  (item) => (
                    <option
                      key={item.id}
                      value={item.id}
                    >
                      {item.invoice_number}
                      {" — "}
                      {item.customer.name}
                    </option>
                  ),
                )}
              </SearchSelect>
            </label>

            <label
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Return date

              <input
                type="date"
                value={returnDate}
                disabled={
                  createMutation.isPending
                }
                onChange={(event) => {
                  setReturnDate(
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

          {invoiceListQuery.isError && (
            <p className="text-sm text-red-600">
              {getErrorMessage(
                invoiceListQuery.error,
              )}
            </p>
          )}

          {invoiceId && (
            <section
              className="
                overflow-hidden rounded-xl
                border border-slate-200
                bg-white
              "
            >
              <div
                className="
                  border-b border-slate-200
                  px-4 py-3
                "
              >
                <h3
                  className="
                    font-semibold
                    text-slate-900
                  "
                >
                  Return items
                </h3>
              </div>

              {invoiceQuery.isLoading && (
                <p
                  className="
                    px-4 py-8 text-center
                    text-sm text-slate-500
                  "
                >
                  Loading invoice items…
                </p>
              )}

              {invoiceQuery.isError && (
                <p
                  className="
                    px-4 py-4 text-sm
                    text-red-600
                  "
                >
                  {getErrorMessage(
                    invoiceQuery.error,
                  )}
                </p>
              )}

              <div className="divide-y divide-slate-200">
                {invoice?.items.map(
                  (item) => {
                    const line =
                      getLine(
                        item.product.id,
                      );

                    return (
                      <div
                        key={item.product.id}
                        className="
                          grid gap-4 p-4
                          md:grid-cols-[1fr_180px_1fr]
                          md:items-end
                        "
                      >
                        <div>
                          <p
                            className="
                              font-semibold
                              text-slate-900
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
                            {" · Invoiced: "}
                            {item.quantity}
                            {" "}
                            {item.product.unit}
                          </p>

                          <button
                            type="button"
                            disabled={
                              createMutation
                                .isPending
                            }
                            onClick={() => {
                              updateLine(
                                item.product.id,
                                {
                                  quantity:
                                    item.quantity,
                                },
                              );
                            }}
                            className="
                              mt-2 text-xs
                              font-semibold
                              text-blue-700
                              hover:underline
                            "
                          >
                            Use invoiced quantity
                          </button>
                        </div>

                        <label
                          className="
                            text-xs font-semibold
                            text-slate-700
                          "
                        >
                          Return quantity

                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            max={item.quantity}
                            value={line.quantity}
                            disabled={
                              createMutation
                                .isPending
                            }
                            onChange={(event) => {
                              updateLine(
                                item.product.id,
                                {
                                  quantity:
                                    event
                                      .currentTarget
                                      .value,
                                },
                              );
                            }}
                            className="
                              mt-2 w-full
                              rounded-lg border
                              border-slate-300
                              px-3 py-2
                              text-sm
                            "
                          />
                        </label>

                        <label
                          className="
                            text-xs font-semibold
                            text-slate-700
                          "
                        >
                          Item reason

                          <input
                            type="text"
                            maxLength={500}
                            value={line.reason}
                            disabled={
                              createMutation
                                .isPending
                            }
                            onChange={(event) => {
                              updateLine(
                                item.product.id,
                                {
                                  reason:
                                    event
                                      .currentTarget
                                      .value,
                                },
                              );
                            }}
                            className="
                              mt-2 w-full
                              rounded-lg border
                              border-slate-300
                              px-3 py-2
                              text-sm
                            "
                          />
                        </label>
                      </div>
                    );
                  },
                )}
              </div>
            </section>
          )}

          <div
            className="
              grid gap-4
              md:grid-cols-2
            "
          >
            <label
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Overall reason

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
                  text-sm
                "
              />
            </label>

            <label
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Notes

              <textarea
                rows={3}
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
                  text-sm
                "
              />
            </label>
          </div>
        </div>

        <footer
          className="
            flex flex-col-reverse gap-3
            border-t border-slate-200
            bg-white px-4 py-4
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
            <RotateCcw className="size-4" />

            {createMutation.isPending
              ? "Creating…"
              : "Create sales return"}
          </button>
        </footer>
      </div>
    </div>
  );
}
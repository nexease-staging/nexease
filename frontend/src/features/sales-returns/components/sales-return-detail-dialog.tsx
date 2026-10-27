"use client";

import {
  useState,
} from "react";

import {
  CheckCircle2,
  RotateCcw,
  X,
  XCircle,
} from "lucide-react";

import {
  useCancelSalesReturn,
  useConfirmSalesReturn,
  useSalesReturn,
} from "@/features/sales-returns/hooks";

import type {
  SalesReturnStatus,
} from "@/features/sales-returns/types";

import {
  APIRequestError,
} from "@/lib/api/client";

interface SalesReturnDetailDialogProps {
  open: boolean;
  salesReturnId: string | null;
  canConfirm: boolean;
  canCancel: boolean;
  onClose: () => void;
  onChanged?: () => void;
}

const statusStyles:
  Record<SalesReturnStatus, string> = {
    DRAFT:
      "bg-amber-100 text-amber-700",
    CONFIRMED:
      "bg-emerald-100 text-emerald-700",
    CANCELLED:
      "bg-red-100 text-red-700",
  };

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

  return "Unable to update the sales return.";
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
      dateStyle: "medium",
    },
  ).format(
    date,
  );
}

export default function SalesReturnDetailDialog({
  open,
  salesReturnId,
  canConfirm,
  canCancel,
  onClose,
  onChanged,
}: SalesReturnDetailDialogProps) {
  const [
    actionError,
    setActionError,
  ] = useState<string | null>(
    null,
  );

  const salesReturnQuery =
    useSalesReturn(
      salesReturnId ?? "",
      (
        open
        &&
        Boolean(
          salesReturnId,
        )
      ),
    );

  const confirmMutation =
    useConfirmSalesReturn();

  const cancelMutation =
    useCancelSalesReturn();

  const salesReturn =
    salesReturnQuery.data;

  const actionPending =
    confirmMutation.isPending
    ||
    cancelMutation.isPending;

  function closeDialog(): void {
    if (actionPending) {
      return;
    }

    setActionError(null);
    onClose();
  }

  async function confirmReturn():
    Promise<void> {
    if (!salesReturn) {
      return;
    }

    const accepted =
      window.confirm(
        (
          "Confirm this sales return? "
          +
          "Returned stock will be restored "
          +
          "to inventory."
        ),
      );

    if (!accepted) {
      return;
    }

    setActionError(null);

    try {
      await confirmMutation
        .mutateAsync(
          salesReturn.id,
        );

      onChanged?.();

    } catch (error) {
      setActionError(
        getErrorMessage(
          error,
        ),
      );
    }
  }

  async function cancelReturn():
    Promise<void> {
    if (!salesReturn) {
      return;
    }

    const accepted =
      window.confirm(
        (
          "Cancel this draft sales return? "
          +
          "This action cannot be undone."
        ),
      );

    if (!accepted) {
      return;
    }

    setActionError(null);

    try {
      await cancelMutation
        .mutateAsync(
          salesReturn.id,
        );

      onChanged?.();

    } catch (error) {
      setActionError(
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
          "sales-return-detail-title"
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
              id="sales-return-detail-title"
              className="
                text-lg font-bold
                text-slate-950
              "
            >
              {salesReturn
                ?.return_number
                ??
                "Sales return"}
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-500
              "
            >
              Return details and lifecycle
              actions
            </p>
          </div>

          <button
            type="button"
            aria-label="Close"
            disabled={actionPending}
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
          {(
            salesReturnQuery.isLoading
          ) && (
            <p
              className="
                py-12 text-center
                text-sm text-slate-500
              "
            >
              Loading sales return…
            </p>
          )}

          {salesReturnQuery.isError && (
            <div
              role="alert"
              className="
                rounded-xl border
                border-red-200 bg-red-50
                px-4 py-3 text-sm
                text-red-700
              "
            >
              {getErrorMessage(
                salesReturnQuery.error,
              )}
            </div>
          )}

          {actionError && (
            <div
              role="alert"
              className="
                rounded-xl border
                border-red-200 bg-red-50
                px-4 py-3 text-sm
                text-red-700
              "
            >
              {actionError}
            </div>
          )}

          {salesReturn && (
            <>
              <section
                className="
                  grid gap-3
                  sm:grid-cols-2
                  lg:grid-cols-4
                "
              >
                <div
                  className="
                    rounded-xl border
                    border-slate-200
                    bg-white p-4
                  "
                >
                  <p
                    className="
                      text-xs font-semibold
                      uppercase text-slate-500
                    "
                  >
                    Status
                  </p>

                  <span
                    className={`
                      mt-2 inline-flex rounded-full
                      px-2.5 py-1 text-xs
                      font-semibold
                      ${statusStyles[
                        salesReturn.status
                      ]}
                    `}
                  >
                    {salesReturn.status}
                  </span>
                </div>

                <div
                  className="
                    rounded-xl border
                    border-slate-200
                    bg-white p-4
                  "
                >
                  <p
                    className="
                      text-xs font-semibold
                      uppercase text-slate-500
                    "
                  >
                    Customer
                  </p>

                  <p
                    className="
                      mt-2 font-semibold
                      text-slate-900
                    "
                  >
                    {salesReturn.customer.name}
                  </p>
                </div>

                <div
                  className="
                    rounded-xl border
                    border-slate-200
                    bg-white p-4
                  "
                >
                  <p
                    className="
                      text-xs font-semibold
                      uppercase text-slate-500
                    "
                  >
                    Invoice
                  </p>

                  <p
                    className="
                      mt-2 font-semibold
                      text-slate-900
                    "
                  >
                    {
                      salesReturn
                        .invoice
                        .invoice_number
                    }
                  </p>
                </div>

                <div
                  className="
                    rounded-xl border
                    border-slate-200
                    bg-white p-4
                  "
                >
                  <p
                    className="
                      text-xs font-semibold
                      uppercase text-slate-500
                    "
                  >
                    Total
                  </p>

                  <p
                    className="
                      mt-2 font-semibold
                      text-slate-900
                    "
                  >
                    {formatAmount(
                      salesReturn
                        .total_amount,
                    )}
                  </p>
                </div>
              </section>

              <section
                className="
                  grid gap-4 rounded-xl
                  border border-slate-200
                  bg-white p-4
                  sm:grid-cols-2
                  lg:grid-cols-4
                "
              >
                <div>
                  <p className="text-xs text-slate-500">
                    Return date
                  </p>
                  <p className="mt-1 text-sm font-medium">
                    {formatDate(
                      salesReturn.return_date,
                    )}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    Sales order
                  </p>
                  <p className="mt-1 text-sm font-medium">
                    {
                      salesReturn
                        .sales_order
                        .so_number
                    }
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    Warehouse
                  </p>
                  <p className="mt-1 text-sm font-medium">
                    {salesReturn.warehouse.name}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    Created by
                  </p>
                  <p className="mt-1 text-sm font-medium">
                    {salesReturn.created_by
                      ?.email
                      ??
                      "—"}
                  </p>
                </div>
              </section>

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
                  <h3 className="font-semibold text-slate-900">
                    Returned items
                  </h3>
                </div>

                <div className="overflow-x-auto">
                  <table
                    className="
                      min-w-[850px] w-full
                      text-left text-sm
                    "
                  >
                    <thead className="bg-slate-50 text-slate-600">
                      <tr>
                        <th className="px-4 py-3">
                          Product
                        </th>
                        <th className="px-4 py-3">
                          Quantity
                        </th>
                        <th className="px-4 py-3">
                          Unit price
                        </th>
                        <th className="px-4 py-3">
                          Tax
                        </th>
                        <th className="px-4 py-3">
                          Total
                        </th>
                        <th className="px-4 py-3">
                          Reason
                        </th>
                      </tr>
                    </thead>

                    <tbody className="divide-y divide-slate-200">
                      {salesReturn.items.map(
                        (item) => (
                          <tr key={item.product.id}>
                            <td className="px-4 py-3">
                              <p className="font-medium text-slate-900">
                                {item.product.name}
                              </p>
                              <p className="text-xs text-slate-500">
                                {item.product.sku}
                              </p>
                            </td>
                            <td className="px-4 py-3">
                              {item.quantity}
                            </td>
                            <td className="px-4 py-3">
                              {formatAmount(
                                item.unit_price,
                              )}
                            </td>
                            <td className="px-4 py-3">
                              {formatAmount(
                                item.line_tax,
                              )}
                            </td>
                            <td className="px-4 py-3 font-semibold">
                              {formatAmount(
                                item.line_total,
                              )}
                            </td>
                            <td className="px-4 py-3">
                              {item.reason ?? "—"}
                            </td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
              </section>

              <section
                className="
                  grid gap-4 rounded-xl
                  border border-slate-200
                  bg-white p-4
                  md:grid-cols-2
                "
              >
                <div>
                  <p className="text-xs text-slate-500">
                    Reason
                  </p>
                  <p className="mt-1 text-sm text-slate-800">
                    {salesReturn.reason ?? "—"}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    Notes
                  </p>
                  <p className="mt-1 text-sm text-slate-800">
                    {salesReturn.notes ?? "—"}
                  </p>
                </div>
              </section>
            </>
          )}
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
            disabled={actionPending}
            onClick={
              closeDialog
            }
            className="
              rounded-lg border
              border-slate-300
              px-4 py-2
              text-sm font-semibold
              text-slate-700
              hover:bg-slate-50
              disabled:opacity-50
            "
          >
            Close
          </button>

          {(
            salesReturn?.status
            ===
            "DRAFT"
            &&
            canCancel
          ) && (
            <button
              type="button"
              disabled={actionPending}
              onClick={() => {
                void cancelReturn();
              }}
              className="
                inline-flex items-center
                justify-center gap-2
                rounded-lg border
                border-red-300 px-4 py-2
                text-sm font-semibold
                text-red-700
                hover:bg-red-50
                disabled:opacity-50
              "
            >
              <XCircle className="size-4" />
              Cancel return
            </button>
          )}

          {(
            salesReturn?.status
            ===
            "DRAFT"
            &&
            canConfirm
          ) && (
            <button
              type="button"
              disabled={actionPending}
              onClick={() => {
                void confirmReturn();
              }}
              className="
                inline-flex items-center
                justify-center gap-2
                rounded-lg bg-emerald-600
                px-4 py-2
                text-sm font-semibold
                text-white
                hover:bg-emerald-700
                disabled:opacity-50
              "
            >
              {confirmMutation.isPending
                ? (
                  <RotateCcw
                    className="
                      size-4 animate-spin
                    "
                  />
                )
                : (
                  <CheckCircle2
                    className="size-4"
                  />
                )}

              Confirm return
            </button>
          )}
        </footer>
      </div>
    </div>
  );
}
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
  useCancelPurchaseReturn,
  useConfirmPurchaseReturn,
  usePurchaseReturn,
} from "@/features/purchase-returns/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

interface PurchaseReturnDetailDialogProps {
  open: boolean;
  purchaseReturnId: string | null;
  canConfirm: boolean;
  canCancel: boolean;
  onClose: () => void;
  onChanged?: () => void;
}

function errorMessage(
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

  return "Unable to update the purchase return.";
}

function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      dateStyle: "medium",
    },
  ).format(
    new Date(value),
  );
}

function formatMoney(
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

function statusClass(
  status: string,
): string {
  if (
    status === "CONFIRMED"
  ) {
    return (
      "bg-emerald-100 text-emerald-700"
    );
  }

  if (
    status === "CANCELLED"
  ) {
    return (
      "bg-red-100 text-red-700"
    );
  }

  return (
    "bg-amber-100 text-amber-700"
  );
}

export default function PurchaseReturnDetailDialog({
  open,
  purchaseReturnId,
  canConfirm,
  canCancel,
  onClose,
  onChanged,
}: PurchaseReturnDetailDialogProps) {
  const [
    actionError,
    setActionError,
  ] = useState<string | null>(
    null,
  );

  const purchaseReturnQuery =
    usePurchaseReturn(
      purchaseReturnId ?? "",
      (
        open
        &&
        Boolean(
          purchaseReturnId,
        )
      ),
    );

  const confirmMutation =
    useConfirmPurchaseReturn();

  const cancelMutation =
    useCancelPurchaseReturn();

  const purchaseReturn =
    purchaseReturnQuery.data;

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
    if (!purchaseReturn) {
      return;
    }

    const accepted =
      window.confirm(
        (
          "Confirm this purchase return? "
          +
          "Inventory will be reduced and "
          +
          "stock movements will be created."
        ),
      );

    if (!accepted) {
      return;
    }

    setActionError(null);

    try {
      await confirmMutation
        .mutateAsync(
          purchaseReturn.id,
        );

      onChanged?.();

    } catch (error) {
      setActionError(
        errorMessage(error),
      );
    }
  }

  async function cancelReturn():
    Promise<void> {
    if (!purchaseReturn) {
      return;
    }

    const accepted =
      window.confirm(
        "Cancel this draft purchase return?",
      );

    if (!accepted) {
      return;
    }

    setActionError(null);

    try {
      await cancelMutation
        .mutateAsync(
          purchaseReturn.id,
        );

      onChanged?.();

    } catch (error) {
      setActionError(
        errorMessage(error),
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
          "purchase-return-detail-title"
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
                "purchase-return-detail-title"
              }
              className="
                text-lg font-bold
                text-slate-950
              "
            >
              {purchaseReturn
                ?.return_number
                ??
                "Purchase return"}
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-500
              "
            >
              Purchase return details and inventory status
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
          {purchaseReturnQuery.isLoading
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
                Loading purchase return…
              </div>
            )
            : null}

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
                {errorMessage(
                  purchaseReturnQuery.error,
                )}
              </div>
            )
            : null}

          {purchaseReturn
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
                          purchaseReturn.status,
                        )}
                      `}
                    >
                      {purchaseReturn.status}
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
                      Return date
                    </p>

                    <p
                      className="
                        mt-2 font-semibold
                        text-slate-950
                      "
                    >
                      {formatDate(
                        purchaseReturn
                          .return_date,
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
                      {
                        purchaseReturn
                          .supplier.name
                      }
                    </p>

                    <p
                      className="
                        text-xs text-slate-500
                      "
                    >
                      {
                        purchaseReturn
                          .supplier.code
                      }
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
                      Total
                    </p>

                    <p
                      className="
                        mt-2 font-bold
                        text-slate-950
                      "
                    >
                      {formatMoney(
                        purchaseReturn
                          .total_amount,
                      )}
                    </p>
                  </div>
                </section>

                <section
                  className="
                    grid gap-4 rounded-xl
                    border border-slate-200
                    bg-white p-4 shadow-sm
                    sm:grid-cols-3 sm:p-5
                  "
                >
                  <div>
                    <p
                      className="
                        text-xs font-semibold
                        text-slate-500
                      "
                    >
                      Purchase order
                    </p>

                    <p
                      className="
                        mt-1 font-semibold
                        text-slate-950
                      "
                    >
                      {
                        purchaseReturn
                          .purchase_order
                          .po_number
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
                        purchaseReturn
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
                      Warehouse
                    </p>

                    <p
                      className="
                        mt-1 font-semibold
                        text-slate-950
                      "
                    >
                      {
                        purchaseReturn
                          .warehouse.code
                      }
                      {" - "}
                      {
                        purchaseReturn
                          .warehouse.name
                      }
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
                      Returned items
                    </h3>
                  </div>

                  <div
                    className="
                      divide-y divide-slate-200
                    "
                  >
                    {purchaseReturn.items.map(
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
                              {" · "}
                              {item.reason
                                ??
                                "No item reason"}
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
                              Unit price
                            </p>

                            <p
                              className="
                                mt-1 font-semibold
                                text-slate-950
                              "
                            >
                              {formatMoney(
                                item.unit_price,
                              )}
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
                              {formatMoney(
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
                      {purchaseReturn.reason
                        ??
                        "—"}
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
                      {purchaseReturn.notes
                        ??
                        "—"}
                    </p>
                  </div>
                </section>

                {actionError
                  ? (
                    <div
                      className="
                        rounded-xl border
                        border-red-200
                        bg-red-50 px-4 py-3
                        text-sm text-red-700
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

          {purchaseReturn?.status
            ===
            "DRAFT"
            &&
            canCancel
            ? (
              <button
                type="button"
                disabled={actionPending}
                onClick={() => {
                  void cancelReturn();
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
                Cancel return
              </button>
            )
            : null}

          {purchaseReturn?.status
            ===
            "DRAFT"
            &&
            canConfirm
            ? (
              <button
                type="button"
                disabled={actionPending}
                onClick={() => {
                  void confirmReturn();
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
                {confirmMutation.isPending
                  ? (
                    <RotateCcw
                      size={17}
                      className="animate-spin"
                    />
                  )
                  : (
                    <CheckCircle2
                      size={17}
                    />
                  )}

                Confirm return
              </button>
            )
            : null}
        </footer>
      </div>
    </div>
  );
}
"use client";

import {
  useState,
} from "react";

import DocumentActions from "@/features/documents/components/document-actions";

import {
  CalendarDays,
  CheckCircle2,
  Edit3,
  PackageCheck,
  X,
  XCircle,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  useCancelPurchaseOrder,
  useConfirmPurchaseOrder,
  usePurchaseOrder,
} from "@/features/purchase-orders/hooks";

import type {
  PurchaseOrderDetail,
  PurchaseOrderStatus,
} from "@/features/purchase-orders/types";

import {
  APIRequestError,
} from "@/lib/api/client";

interface PurchaseOrderDetailDialogProps {
  open: boolean;
  purchaseOrderId: string;
  onClose: () => void;
  onEdit: (
    purchaseOrder:
      PurchaseOrderDetail,
  ) => void;
}

const statusStyles:
  Record<
    PurchaseOrderStatus,
    string
  > = {
    DRAFT:
      "bg-slate-100 text-slate-700",
    CONFIRMED:
      "bg-blue-100 text-blue-700",
    PARTIALLY_RECEIVED:
      "bg-amber-100 text-amber-700",
    RECEIVED:
      "bg-emerald-100 text-emerald-700",
    CANCELLED:
      "bg-red-100 text-red-700",
  };

function formatStatus(
  status: PurchaseOrderStatus,
): string {
  return status
    .toLowerCase()
    .split("_")
    .map(
      (word) =>
        (
          word.charAt(0).toUpperCase()
          +
          word.slice(1)
        ),
    )
    .join(" ");
}

function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  const parsedDate =
    new Date(value);

  if (
    Number.isNaN(
      parsedDate.getTime(),
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
  ).format(
    parsedDate,
  );
}

function formatDateTime(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  const parsedDate =
    new Date(value);

  if (
    Number.isNaN(
      parsedDate.getTime(),
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
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(
    parsedDate,
  );
}

function formatAmount(
  value: string,
): string {
  const amount =
    Number(value);

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
      maximumFractionDigits: 2,
    },
  ).format(
    amount,
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
    "Unable to complete the request."
  );
}

export default function PurchaseOrderDetailDialog({
  open,
  purchaseOrderId,
  onClose,
  onEdit,
}: PurchaseOrderDetailDialogProps) {
  const {
    authentication,
  } = useAuth();

  const [
    actionError,
    setActionError,
  ] = useState<string | null>(
    null,
  );

  const purchaseOrderQuery =
    usePurchaseOrder(
      purchaseOrderId,
      (
        open
        &&
        Boolean(
          purchaseOrderId,
        )
      ),
    );

  const confirmMutation =
    useConfirmPurchaseOrder();

  const cancelMutation =
    useCancelPurchaseOrder();

  if (!open) {
    return null;
  }

  const purchaseOrder =
    purchaseOrderQuery.data;

  const permissions =
    authentication
      ?.role
      .permissions
      ??
      [];

  const canUpdate =
    permissions.includes(
      "purchase_orders.update",
    );

  const canCancel =
    permissions.includes(
      "purchase_orders.cancel",
    );

  const canEdit =
    Boolean(
      purchaseOrder
      &&
      purchaseOrder.status
      ===
      "DRAFT"
      &&
      canUpdate,
    );

  const canConfirm =
    Boolean(
      purchaseOrder
      &&
      purchaseOrder.status
      ===
      "DRAFT"
      &&
      canUpdate,
    );

  const canCancelOrder =
    Boolean(
      purchaseOrder
      &&
      (
        purchaseOrder.status
        ===
        "DRAFT"
        ||
        purchaseOrder.status
        ===
        "CONFIRMED"
      )
      &&
      canCancel,
    );

  const actionPending =
    confirmMutation.isPending
    ||
    cancelMutation.isPending;

  async function handleConfirm():
    Promise<void> {
    if (!purchaseOrder) {
      return;
    }

    const accepted =
      window.confirm(
        (
          `Confirm purchase order `
          +
          `${purchaseOrder.po_number}?`
        ),
      );

    if (!accepted) {
      return;
    }

    setActionError(null);

    try {
      await confirmMutation
        .mutateAsync(
          purchaseOrder.id,
        );
    } catch (error) {
      setActionError(
        getErrorMessage(error),
      );
    }
  }

  async function handleCancel():
    Promise<void> {
    if (!purchaseOrder) {
      return;
    }

    const accepted =
      window.confirm(
        (
          `Cancel purchase order `
          +
          `${purchaseOrder.po_number}? `
          +
          `This action cannot be undone.`
        ),
      );

    if (!accepted) {
      return;
    }

    setActionError(null);

    try {
      await cancelMutation
        .mutateAsync(
          purchaseOrder.id,
        );
    } catch (error) {
      setActionError(
        getErrorMessage(error),
      );
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="
        purchase-order-detail-title
      "
      className="
        fixed inset-0 z-50 flex
        items-end justify-center
        bg-slate-950/50
        sm:items-center sm:p-4
      "
    >
      <div
        className="
          flex max-h-[95vh] w-full
          flex-col overflow-hidden
          rounded-t-2xl bg-white
          text-slate-900 shadow-2xl
          sm:max-w-6xl sm:rounded-2xl
        "
      >
        <header
          className="
            flex items-start
            justify-between gap-4
            border-b border-slate-200
            px-4 py-4 sm:px-6
          "
        >
          <div className="min-w-0">
            <p
              className="
                text-xs font-semibold
                uppercase tracking-wide
                text-blue-600
              "
            >
              Purchase order
            </p>

            <h2
              id="
                purchase-order-detail-title
              "
              className="
                mt-1 truncate text-lg
                font-bold text-slate-950
                sm:text-xl
              "
            >
              {purchaseOrder
                ?.po_number
                ??
                "Purchase-order details"}
            </h2>
          </div>

          <button
            type="button"
            aria-label="Close dialog"
            onClick={onClose}
            className="
              rounded-lg p-2
              text-slate-500
              hover:bg-slate-100
              hover:text-slate-900
            "
          >
            <X size={20} />
          </button>
        </header>

        <div
          className="
            min-h-0 flex-1
            overflow-y-auto
            bg-slate-50 p-4 sm:p-6
          "
        >
          {purchaseOrderQuery.isLoading
            ? (
              <div
                className="
                  rounded-xl border
                  border-slate-200 bg-white
                  px-5 py-12 text-center
                  text-sm text-slate-600
                "
              >
                Loading purchase order…
              </div>
            )
            : null}

          {purchaseOrderQuery.isError
            ? (
              <div
                className="
                  rounded-xl border
                  border-red-200 bg-red-50
                  px-5 py-4 text-sm
                  text-red-700
                "
              >
                {getErrorMessage(
                  purchaseOrderQuery.error,
                )}
              </div>
            )
            : null}

          {purchaseOrder
            ? (
              <div className="space-y-5">
                <section
                  className="
                    rounded-xl border
                    border-slate-200 bg-white
                    p-4 shadow-sm sm:p-5
                  "
                >
                  <div
                    className="
                      flex flex-col gap-4
                      sm:flex-row
                      sm:items-start
                      sm:justify-between
                    "
                  >
                    <div>
                      <div
                        className="
                          flex flex-wrap
                          items-center gap-2
                        "
                      >
                        <h3
                          className="
                            text-xl font-bold
                            text-slate-950
                          "
                        >
                          {
                            purchaseOrder
                              .po_number
                          }
                        </h3>

                        <span
                          className={`
                            rounded-full
                            px-2.5 py-1
                            text-xs font-semibold
                            ${
                              statusStyles[
                                purchaseOrder
                                  .status
                              ]
                            }
                          `}
                        >
                          {formatStatus(
                            purchaseOrder
                              .status,
                          )}
                        </span>
                      </div>

                      <p
                        className="
                          mt-2 text-sm
                          text-slate-600
                        "
                      >
                        {
                          purchaseOrder
                            .supplier.name
                        }
                      </p>

                      <p
                        className="
                          mt-1 text-xs
                          text-slate-500
                        "
                      >
                        Supplier code:{" "}
                        {
                          purchaseOrder
                            .supplier.code
                        }
                      </p>
                    </div>

                    <div
                      className="
                        text-left
                        sm:text-right
                      "
                    >
                      <p
                        className="
                          text-xs font-medium
                          uppercase tracking-wide
                          text-slate-500
                        "
                      >
                        Total amount
                      </p>

                      <p
                        className="
                          mt-1 text-2xl
                          font-bold text-slate-950
                        "
                      >
                        {formatAmount(
                          purchaseOrder
                            .total_amount,
                        )}
                      </p>
                    </div>
                  </div>
                </section>

                <section
                  className="
                    grid gap-4
                    sm:grid-cols-2
                    lg:grid-cols-4
                  "
                >
                  <div
                    className="
                      rounded-xl border
                      border-slate-200 bg-white
                      p-4 shadow-sm
                    "
                  >
                    <p
                      className="
                        text-xs font-medium
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Order date
                    </p>

                    <p
                      className="
                        mt-2 flex items-center
                        gap-2 text-sm
                        font-semibold
                        text-slate-900
                      "
                    >
                      <CalendarDays
                        size={16}
                        className="
                          text-blue-600
                        "
                      />

                      {formatDate(
                        purchaseOrder
                          .order_date,
                      )}
                    </p>
                  </div>

                  <div
                    className="
                      rounded-xl border
                      border-slate-200 bg-white
                      p-4 shadow-sm
                    "
                  >
                    <p
                      className="
                        text-xs font-medium
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Expected delivery
                    </p>

                    <p
                      className="
                        mt-2 flex items-center
                        gap-2 text-sm
                        font-semibold
                        text-slate-900
                      "
                    >
                      <PackageCheck
                        size={16}
                        className="
                          text-blue-600
                        "
                      />

                      {formatDate(
                        purchaseOrder
                          .expected_delivery_date,
                      )}
                    </p>
                  </div>

                  <div
                    className="
                      rounded-xl border
                      border-slate-200 bg-white
                      p-4 shadow-sm
                    "
                  >
                    <p
                      className="
                        text-xs font-medium
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Items
                    </p>

                    <p
                      className="
                        mt-2 text-lg font-bold
                        text-slate-950
                      "
                    >
                      {
                        purchaseOrder
                          .item_count
                      }
                    </p>
                  </div>

                  <div
                    className="
                      rounded-xl border
                      border-slate-200 bg-white
                      p-4 shadow-sm
                    "
                  >
                    <p
                      className="
                        text-xs font-medium
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Created by
                    </p>

                    <p
                      className="
                        mt-2 text-sm font-semibold
                        text-slate-900
                      "
                    >
                      {purchaseOrder.created_by
                        ? (
                          `${
                            purchaseOrder
                              .created_by
                              .first_name
                          } ${
                            purchaseOrder
                              .created_by
                              .last_name
                          }`
                        ).trim()
                        ||
                        purchaseOrder
                          .created_by.email
                        : "—"}
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
                      px-4 py-4 sm:px-5
                    "
                  >
                    <h3
                      className="
                        font-bold text-slate-950
                      "
                    >
                      Order items
                    </h3>
                  </div>

                  <div
                    className="
                      divide-y
                      divide-slate-200
                      lg:hidden
                    "
                  >
                    {purchaseOrder.items.map(
                      (
                        item,
                        index,
                      ) => (
                        <article
                          key={`
                            ${
                              item.product.id
                            }-${index}
                          `}
                          className="p-4"
                        >
                          <div
                            className="
                              flex items-start
                              justify-between
                              gap-3
                            "
                          >
                            <div>
                              <p
                                className="
                                  font-semibold
                                  text-slate-950
                                "
                              >
                                {
                                  item
                                    .product
                                    .name
                                }
                              </p>

                              <p
                                className="
                                  mt-1 text-xs
                                  text-slate-500
                                "
                              >
                                {
                                  item
                                    .product
                                    .sku
                                }
                              </p>
                            </div>

                            <p
                              className="
                                font-bold
                                text-slate-950
                              "
                            >
                              {formatAmount(
                                item.total,
                              )}
                            </p>
                          </div>

                          <dl
                            className="
                              mt-4 grid
                              grid-cols-2 gap-3
                              text-sm
                            "
                          >
                            <div>
                              <dt
                                className="
                                  text-xs
                                  text-slate-500
                                "
                              >
                                Ordered
                              </dt>

                              <dd
                                className="
                                  mt-1 font-medium
                                  text-slate-900
                                "
                              >
                                {item.quantity}{" "}
                                {
                                  item
                                    .product
                                    .unit
                                }
                              </dd>
                            </div>

                            <div>
                              <dt
                                className="
                                  text-xs
                                  text-slate-500
                                "
                              >
                                Received
                              </dt>

                              <dd
                                className="
                                  mt-1 font-medium
                                  text-slate-900
                                "
                              >
                                {
                                  item
                                    .received_quantity
                                }{" "}
                                {
                                  item
                                    .product
                                    .unit
                                }
                              </dd>
                            </div>

                            <div>
                              <dt
                                className="
                                  text-xs
                                  text-slate-500
                                "
                              >
                                Remaining
                              </dt>

                              <dd
                                className="
                                  mt-1 font-medium
                                  text-slate-900
                                "
                              >
                                {
                                  item
                                    .remaining_quantity
                                }{" "}
                                {
                                  item
                                    .product
                                    .unit
                                }
                              </dd>
                            </div>

                            <div>
                              <dt
                                className="
                                  text-xs
                                  text-slate-500
                                "
                              >
                                Unit price
                              </dt>

                              <dd
                                className="
                                  mt-1 font-medium
                                  text-slate-900
                                "
                              >
                                {formatAmount(
                                  item.unit_price,
                                )}
                              </dd>
                            </div>

                            <div>
                              <dt
                                className="
                                  text-xs
                                  text-slate-500
                                "
                              >
                                Tax
                              </dt>

                              <dd
                                className="
                                  mt-1 font-medium
                                  text-slate-900
                                "
                              >
                                {
                                  item.tax_rate
                                }%
                              </dd>
                            </div>

                            <div>
                              <dt
                                className="
                                  text-xs
                                  text-slate-500
                                "
                              >
                                Discount
                              </dt>

                              <dd
                                className="
                                  mt-1 font-medium
                                  text-slate-900
                                "
                              >
                                {formatAmount(
                                  item.discount,
                                )}
                              </dd>
                            </div>
                          </dl>
                        </article>
                      ),
                    )}
                  </div>

                  <div
                    className="
                      hidden overflow-x-auto
                      lg:block
                    "
                  >
                    <table
                      className="
                        min-w-full
                        divide-y
                        divide-slate-200
                      "
                    >
                      <thead
                        className="
                          bg-slate-50
                        "
                      >
                        <tr>
                          {[
                            "Product",
                            "Ordered",
                            "Received",
                            "Remaining",
                            "Unit price",
                            "Tax",
                            "Discount",
                            "Total",
                          ].map(
                            (heading) => (
                              <th
                                key={heading}
                                className="
                                  px-4 py-3
                                  text-left text-xs
                                  font-semibold
                                  uppercase
                                  tracking-wide
                                  text-slate-600
                                "
                              >
                                {heading}
                              </th>
                            ),
                          )}
                        </tr>
                      </thead>

                      <tbody
                        className="
                          divide-y
                          divide-slate-200
                          bg-white
                        "
                      >
                        {purchaseOrder.items.map(
                          (
                            item,
                            index,
                          ) => (
                            <tr
                              key={`
                                ${
                                  item
                                    .product.id
                                }-${index}
                              `}
                            >
                              <td
                                className="
                                  px-4 py-3
                                "
                              >
                                <p
                                  className="
                                    font-medium
                                    text-slate-950
                                  "
                                >
                                  {
                                    item
                                      .product
                                      .name
                                  }
                                </p>

                                <p
                                  className="
                                    mt-1 text-xs
                                    text-slate-500
                                  "
                                >
                                  {
                                    item
                                      .product
                                      .sku
                                  }
                                </p>
                              </td>

                              <td
                                className="
                                  px-4 py-3
                                  text-sm
                                  text-slate-700
                                "
                              >
                                {
                                  item.quantity
                                }
                              </td>

                              <td
                                className="
                                  px-4 py-3
                                  text-sm
                                  text-slate-700
                                "
                              >
                                {
                                  item
                                    .received_quantity
                                }
                              </td>

                              <td
                                className="
                                  px-4 py-3
                                  text-sm
                                  text-slate-700
                                "
                              >
                                {
                                  item
                                    .remaining_quantity
                                }
                              </td>

                              <td
                                className="
                                  whitespace-nowrap
                                  px-4 py-3
                                  text-sm
                                  text-slate-700
                                "
                              >
                                {formatAmount(
                                  item.unit_price,
                                )}
                              </td>

                              <td
                                className="
                                  px-4 py-3
                                  text-sm
                                  text-slate-700
                                "
                              >
                                {
                                  item.tax_rate
                                }%
                              </td>

                              <td
                                className="
                                  whitespace-nowrap
                                  px-4 py-3
                                  text-sm
                                  text-slate-700
                                "
                              >
                                {formatAmount(
                                  item.discount,
                                )}
                              </td>

                              <td
                                className="
                                  whitespace-nowrap
                                  px-4 py-3
                                  text-sm
                                  font-semibold
                                  text-slate-950
                                "
                              >
                                {formatAmount(
                                  item.total,
                                )}
                              </td>
                            </tr>
                          ),
                        )}
                      </tbody>
                    </table>
                  </div>
                </section>

                <div
                  className="
                    grid gap-5
                    lg:grid-cols-[1fr_360px]
                  "
                >
                  <section
                    className="
                      rounded-xl border
                      border-slate-200 bg-white
                      p-4 shadow-sm sm:p-5
                    "
                  >
                    <h3
                      className="
                        font-bold text-slate-950
                      "
                    >
                      Notes
                    </h3>

                    <p
                      className="
                        mt-3 whitespace-pre-wrap
                        text-sm leading-6
                        text-slate-700
                      "
                    >
                      {
                        purchaseOrder.notes
                        ||
                        "No notes added."
                      }
                    </p>

                    <div
                      className="
                        mt-5 grid gap-3
                        border-t
                        border-slate-200 pt-4
                        text-sm sm:grid-cols-2
                      "
                    >
                      <div>
                        <p
                          className="
                            text-xs text-slate-500
                          "
                        >
                          Created
                        </p>

                        <p
                          className="
                            mt-1 font-medium
                            text-slate-900
                          "
                        >
                          {formatDateTime(
                            purchaseOrder
                              .created_at,
                          )}
                        </p>
                      </div>

                      <div>
                        <p
                          className="
                            text-xs text-slate-500
                          "
                        >
                          Updated
                        </p>

                        <p
                          className="
                            mt-1 font-medium
                            text-slate-900
                          "
                        >
                          {formatDateTime(
                            purchaseOrder
                              .updated_at,
                          )}
                        </p>
                      </div>

                      <div>
                        <p
                          className="
                            text-xs text-slate-500
                          "
                        >
                          Confirmed
                        </p>

                        <p
                          className="
                            mt-1 font-medium
                            text-slate-900
                          "
                        >
                          {formatDateTime(
                            purchaseOrder
                              .confirmed_at,
                          )}
                        </p>
                      </div>

                      <div>
                        <p
                          className="
                            text-xs text-slate-500
                          "
                        >
                          Cancelled
                        </p>

                        <p
                          className="
                            mt-1 font-medium
                            text-slate-900
                          "
                        >
                          {formatDateTime(
                            purchaseOrder
                              .cancelled_at,
                          )}
                        </p>
                      </div>
                    </div>
                  </section>

                  <section
                    className="
                      rounded-xl border
                      border-slate-200 bg-white
                      p-4 shadow-sm sm:p-5
                    "
                  >
                    <h3
                      className="
                        font-bold text-slate-950
                      "
                    >
                      Amount summary
                    </h3>

                    <dl
                      className="
                        mt-4 space-y-3
                        text-sm
                      "
                    >
                      <div
                        className="
                          flex justify-between
                          gap-4
                        "
                      >
                        <dt
                          className="
                            text-slate-600
                          "
                        >
                          Subtotal
                        </dt>

                        <dd
                          className="
                            font-medium
                            text-slate-900
                          "
                        >
                          {formatAmount(
                            purchaseOrder
                              .subtotal,
                          )}
                        </dd>
                      </div>

                      <div
                        className="
                          flex justify-between
                          gap-4
                        "
                      >
                        <dt
                          className="
                            text-slate-600
                          "
                        >
                          Tax
                        </dt>

                        <dd
                          className="
                            font-medium
                            text-slate-900
                          "
                        >
                          {formatAmount(
                            purchaseOrder
                              .tax_amount,
                          )}
                        </dd>
                      </div>

                      <div
                        className="
                          flex justify-between
                          gap-4
                        "
                      >
                        <dt
                          className="
                            text-slate-600
                          "
                        >
                          Discount
                        </dt>

                        <dd
                          className="
                            font-medium
                            text-slate-900
                          "
                        >
                          -{" "}
                          {formatAmount(
                            purchaseOrder
                              .discount_amount,
                          )}
                        </dd>
                      </div>

                      <div
                        className="
                          flex justify-between
                          gap-4 border-t
                          border-slate-200 pt-3
                        "
                      >
                        <dt
                          className="
                            font-bold
                            text-slate-950
                          "
                        >
                          Total
                        </dt>

                        <dd
                          className="
                            text-lg font-bold
                            text-slate-950
                          "
                        >
                          {formatAmount(
                            purchaseOrder
                              .total_amount,
                          )}
                        </dd>
                      </div>
                    </dl>
                  </section>
                </div>

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
            bg-white px-4 py-4 sm:px-6
          "
        >
          <button
            type="button"
            onClick={onClose}
            className="
              rounded-lg border
              border-slate-300 bg-white
              px-4 py-2 text-sm
              font-semibold text-slate-700
              hover:bg-slate-50
            "
          >
            Close
          </button>

          {purchaseOrder ? (
            <DocumentActions
              documentType="PURCHASE_ORDER"
              documentId={purchaseOrder.id}
              documentNumber={
                purchaseOrder.po_number
              }
              disabled={actionPending}
            />
          ) : null}

          {canEdit
            ? (
              <button
                type="button"
                disabled={actionPending}
                onClick={() => {
                  if (purchaseOrder) {
                    onEdit(
                      purchaseOrder,
                    );
                  }
                }}
                className="
                  inline-flex items-center
                  gap-2 rounded-lg border
                  border-blue-200 bg-blue-50
                  px-4 py-2 text-sm
                  font-semibold text-blue-700
                  hover:bg-blue-100
                  disabled:cursor-not-allowed
                  disabled:opacity-50
                "
              >
                <Edit3 size={16} />
                Edit
              </button>
            )
            : null}

          {canConfirm
            ? (
              <button
                type="button"
                disabled={actionPending}
                onClick={() => {
                  void handleConfirm();
                }}
                className="
                  inline-flex items-center
                  gap-2 rounded-lg
                  bg-emerald-600
                  px-4 py-2 text-sm
                  font-semibold text-white
                  hover:bg-emerald-700
                  disabled:cursor-not-allowed
                  disabled:opacity-50
                "
              >
                <CheckCircle2
                  size={16}
                />

                {confirmMutation
                  .isPending
                  ? "Confirming…"
                  : "Confirm order"}
              </button>
            )
            : null}

          {canCancelOrder
            ? (
              <button
                type="button"
                disabled={actionPending}
                onClick={() => {
                  void handleCancel();
                }}
                className="
                  inline-flex items-center
                  gap-2 rounded-lg
                  bg-red-600 px-4 py-2
                  text-sm font-semibold
                  text-white
                  hover:bg-red-700
                  disabled:cursor-not-allowed
                  disabled:opacity-50
                "
              >
                <XCircle size={16} />

                {cancelMutation
                  .isPending
                  ? "Cancelling…"
                  : "Cancel order"}
              </button>
            )
            : null}
        </footer>
      </div>
    </div>
  );
}
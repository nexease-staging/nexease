"use client";

import {
  Pencil,
  PackageCheck,
  X,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import DocumentActions from "@/features/documents/components/document-actions";

import {
  useCancelSalesOrder,
  useConfirmSalesOrder,
  useSalesOrder,
} from "@/features/sales-orders/hooks";

import type {
  SalesOrderStatus,
} from "@/features/sales-orders/types";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

interface SalesOrderDetailDialogProps {
  open: boolean;
  salesOrderId: string | null;
  onClose: () => void;
  onEdit: (salesOrderId: string) => void;
  onFulfill: (salesOrderId: string) => void;
}

function formatAmount(
  value: string,
): string {
  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
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
      date.getTime()
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      dateStyle: "medium",
    },
  ).format(date);
}

function statusClassName(
  status: SalesOrderStatus,
): string {
  if (status === "FULFILLED") {
    return (
      "border-emerald-200 "
      +
      "bg-emerald-50 "
      +
      "text-emerald-700"
    );
  }

  if (
    status
    ===
    "PARTIALLY_FULFILLED"
  ) {
    return (
      "border-blue-200 "
      +
      "bg-blue-50 "
      +
      "text-blue-700"
    );
  }

  if (status === "CONFIRMED") {
    return (
      "border-violet-200 "
      +
      "bg-violet-50 "
      +
      "text-violet-700"
    );
  }

  if (status === "CANCELLED") {
    return (
      "border-red-200 "
      +
      "bg-red-50 "
      +
      "text-red-700"
    );
  }

  return (
    "border-amber-200 "
    +
    "bg-amber-50 "
    +
    "text-amber-700"
  );
}

export default function SalesOrderDetailDialog({
  open,
  salesOrderId,
  onClose,
  onEdit,
  onFulfill,
}: SalesOrderDetailDialogProps) {
  const {
    authentication,
  } = useAuth();

  const salesOrderQuery =
    useSalesOrder(
      salesOrderId ?? "",
      open && Boolean(
        salesOrderId
      ),
    );

  const confirmMutation =
    useConfirmSalesOrder();

  const cancelMutation =
    useCancelSalesOrder();

  if (!open) {
    return null;
  }

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const canUpdate =
    hasPermission(
      permissions,
      "sales_orders.update",
    );

  const canCancel =
    hasPermission(
      permissions,
      "sales_orders.cancel",
    );

  const canFulfill =
    hasPermission(
      permissions,
      "sales_orders.fulfill",
    );

  const salesOrder =
    salesOrderQuery.data;

  const actionPending =
    confirmMutation.isPending
    ||
    cancelMutation.isPending;

  async function confirmOrder():
    Promise<void> {
    if (!salesOrder) {
      return;
    }

    const accepted =
      window.confirm(
        (
          `Confirm ${salesOrder.so_number}? `
          +
          "Required inventory will be reserved."
        ),
      );

    if (!accepted) {
      return;
    }

    try {
      await confirmMutation.mutateAsync(
        salesOrder.id
      );

    } catch {
      // The mutation error is rendered
      // inside the dialog.
    }
  }

  async function cancelOrder():
    Promise<void> {
    if (!salesOrder) {
      return;
    }

    const accepted =
      window.confirm(
        (
          `Cancel ${salesOrder.so_number}? `
          +
          "Existing reservations will be released."
        ),
      );

    if (!accepted) {
      return;
    }

    try {
      await cancelMutation.mutateAsync(
        salesOrder.id
      );

    } catch {
      // The mutation error is rendered
      // inside the dialog.
    }
  }

  return (
    <div
      role="presentation"
      className="
        fixed inset-0 z-50
        flex items-center justify-center
        bg-slate-950/50 p-3
        sm:p-4
      "
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="sales-order-detail-title"
        className="
          max-h-[94vh] w-full
          max-w-5xl overflow-y-auto
          rounded-2xl bg-white
          text-slate-900 shadow-2xl
        "
      >
        <div
          className="
            sticky top-0 z-10
            flex items-start justify-between
            border-b border-slate-200
            bg-white p-5
          "
        >
          <div>
            <h2
              id="sales-order-detail-title"
              className="text-xl font-bold"
            >
              {salesOrder
                ?.so_number
                ??
                "Sales order"}
            </h2>

            <p className="mt-1 text-sm text-slate-600">
              Sales Order details,
              lifecycle, and fulfilment.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close"
            disabled={actionPending}
            onClick={onClose}
            className="
              rounded-lg p-2 text-slate-500
              hover:bg-slate-100
              disabled:opacity-50
            "
          >
            <X size={20} />
          </button>
        </div>

        {salesOrderQuery.isPending ? (
          <div
            className="
              flex min-h-80 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading sales order…
          </div>
        ) : salesOrderQuery.isError ? (
          <div
            className="
              flex min-h-80 flex-col
              items-center justify-center
              gap-3 p-6
            "
          >
            <p className="text-sm text-red-700">
              {salesOrderQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void salesOrderQuery.refetch();
              }}
              className="
                rounded-lg bg-slate-900
                px-4 py-2 text-sm
                font-semibold text-white
              "
            >
              Try again
            </button>
          </div>
        ) : salesOrder ? (
          <div className="space-y-6 p-5">
            <div
              className="
                flex flex-wrap items-center
                justify-between gap-3
              "
            >
              <span
                className={`
                  rounded-full border
                  px-3 py-1 text-xs
                  font-bold
                  ${statusClassName(
                    salesOrder.status
                  )}
                `}
              >
                {
                  salesOrder.status.replaceAll(
                    "_",
                    " ",
                  )
                }
              </span>

                <div className="flex flex-wrap gap-2">
                  <DocumentActions
                    documentType="SALES_ORDER"
                    documentId={salesOrder.id}
                    documentNumber={
                      salesOrder.so_number
                    }
                    disabled={actionPending}
                  />

                  {canUpdate
                  && salesOrder.status
                    ===
                    "DRAFT" ? (
                    <>
                    <button
                      type="button"
                      disabled={actionPending}
                      onClick={() => {
                        onEdit(
                          salesOrder.id
                        );
                      }}
                      className="
                        inline-flex items-center
                        gap-2 rounded-lg border
                        border-slate-300 px-3
                        py-2 text-sm font-semibold
                        text-slate-700
                        hover:bg-slate-50
                      "
                    >
                      <Pencil size={16} />
                      Edit
                    </button>

                    <button
                      type="button"
                      disabled={actionPending}
                      onClick={() => {
                        void confirmOrder();
                      }}
                      className="
                        rounded-lg bg-blue-600
                        px-3 py-2 text-sm
                        font-semibold text-white
                        hover:bg-blue-700
                        disabled:opacity-50
                      "
                    >
                      {confirmMutation.isPending
                        ? "Confirming…"
                        : "Confirm order"}
                    </button>
                  </>
                ) : null}

                {canFulfill
                && (
                  salesOrder.status
                  ===
                  "CONFIRMED"
                  ||
                  salesOrder.status
                  ===
                  "PARTIALLY_FULFILLED"
                ) ? (
                  <button
                    type="button"
                    disabled={actionPending}
                    onClick={() => {
                      onFulfill(
                        salesOrder.id
                      );
                    }}
                    className="
                      inline-flex items-center
                      gap-2 rounded-lg
                      bg-emerald-600 px-3
                      py-2 text-sm font-semibold
                      text-white
                      hover:bg-emerald-700
                    "
                  >
                    <PackageCheck size={16} />
                    Fulfil
                  </button>
                ) : null}

                {canCancel
                && (
                  salesOrder.status
                  ===
                  "DRAFT"
                  ||
                  salesOrder.status
                  ===
                  "CONFIRMED"
                ) ? (
                  <button
                    type="button"
                    disabled={actionPending}
                    onClick={() => {
                      void cancelOrder();
                    }}
                    className="
                      rounded-lg border
                      border-red-200 px-3
                      py-2 text-sm font-semibold
                      text-red-700
                      hover:bg-red-50
                      disabled:opacity-50
                    "
                  >
                    {cancelMutation.isPending
                      ? "Cancelling…"
                      : "Cancel order"}
                  </button>
                ) : null}
              </div>
            </div>

            {(confirmMutation.error
            || cancelMutation.error) ? (
              <p
                className="
                  rounded-lg bg-red-50
                  px-4 py-3 text-sm
                  text-red-700
                "
              >
                {
                  (
                    confirmMutation.error
                    ??
                    cancelMutation.error
                  )?.message
                }
              </p>
            ) : null}

            <div
              className="
                grid gap-4 rounded-xl
                border border-slate-200
                p-4 sm:grid-cols-2
                lg:grid-cols-4
              "
            >
              <div>
                <p className="text-xs text-slate-500">
                  Customer
                </p>
                <p className="font-semibold">
                  {salesOrder.customer.name}
                </p>
                <p className="text-sm text-slate-500">
                  {salesOrder.customer.code}
                </p>
              </div>

              <div>
                <p className="text-xs text-slate-500">
                  Warehouse
                </p>
                <p className="font-semibold">
                  {salesOrder.warehouse.name}
                </p>
                <p className="text-sm text-slate-500">
                  {salesOrder.warehouse.code}
                </p>
              </div>

              <div>
                <p className="text-xs text-slate-500">
                  Order date
                </p>
                <p className="font-semibold">
                  {formatDate(
                    salesOrder.order_date
                  )}
                </p>
              </div>

              <div>
                <p className="text-xs text-slate-500">
                  Expected delivery
                </p>
                <p className="font-semibold">
                  {formatDate(
                    salesOrder
                      .expected_delivery_date
                  )}
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table
                className="
                  min-w-full divide-y
                  divide-slate-200
                  text-sm
                "
              >
                <thead className="bg-slate-50">
                  <tr>
                    {[
                      "Product",
                      "Ordered",
                      "Fulfilled",
                      "Price",
                      "Tax",
                      "Discount",
                      "Total",
                    ].map(
                      (heading) => (
                        <th
                          key={heading}
                          className="
                            whitespace-nowrap
                            px-3 py-3 text-left
                            text-xs font-bold
                            uppercase tracking-wide
                            text-slate-500
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
                    divide-y divide-slate-100
                  "
                >
                  {salesOrder.items.map(
                    (item) => (
                      <tr key={item.product.id}>
                        <td className="px-3 py-3">
                          <p className="font-semibold">
                            {item.product.name}
                          </p>
                          <p className="text-xs text-slate-500">
                            {item.product.sku}
                          </p>
                        </td>

                        <td className="whitespace-nowrap px-3 py-3">
                          {item.quantity}
                        </td>

                        <td className="whitespace-nowrap px-3 py-3">
                          {item.fulfilled_quantity}
                        </td>

                        <td className="whitespace-nowrap px-3 py-3">
                          {formatAmount(
                            item.unit_price
                          )}
                        </td>

                        <td className="whitespace-nowrap px-3 py-3">
                          {item.tax_rate}%
                        </td>

                        <td className="whitespace-nowrap px-3 py-3">
                          {formatAmount(
                            item.discount
                          )}
                        </td>

                        <td className="whitespace-nowrap px-3 py-3 font-semibold">
                          {formatAmount(
                            item.line_total
                          )}
                        </td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>

            <div
              className="
                ml-auto w-full space-y-2
                rounded-xl bg-slate-900
                p-4 text-sm text-white
                sm:max-w-sm
              "
            >
              {[
                [
                  "Subtotal",
                  salesOrder.subtotal,
                ],
                [
                  "Discount",
                  salesOrder.discount_amount,
                ],
                [
                  "Tax",
                  salesOrder.tax_amount,
                ],
                [
                  "Total",
                  salesOrder.total_amount,
                ],
              ].map(
                ([
                  label,
                  value,
                ]) => (
                  <div
                    key={label}
                    className={`
                      flex justify-between
                      ${
                        label === "Total"
                          ? (
                            "border-t "
                            +
                            "border-slate-700 "
                            +
                            "pt-2 text-base "
                            +
                            "font-bold"
                          )
                          : ""
                      }
                    `}
                  >
                    <span>{label}</span>
                    <span>
                      {formatAmount(value)}
                    </span>
                  </div>
                ),
              )}
            </div>

            {salesOrder.notes ? (
              <div
                className="
                  rounded-xl border
                  border-slate-200 p-4
                "
              >
                <p className="text-xs font-bold uppercase text-slate-500">
                  Notes
                </p>
                <p className="mt-2 whitespace-pre-wrap text-sm">
                  {salesOrder.notes}
                </p>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
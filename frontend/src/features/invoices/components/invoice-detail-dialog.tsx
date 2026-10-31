"use client";

import {InvoiceDetails} from "@/features/business/invoice-settings";
import InvoiceDescriptions from "@/features/business/invoice-descriptions";
import DocumentActions from "@/features/documents/components/document-actions";

import {
  Ban,
  CircleDollarSign,
  Send,
  X,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  useCancelInvoice,
  useInvoice,
  useIssueInvoice,
} from "@/features/invoices/hooks";

import type {
  InvoiceStatus,
  InvoiceSummary,
} from "@/features/invoices/types";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

interface InvoiceDetailDialogProps {
  open: boolean;
  invoiceId: string | null;
  onClose: () => void;
  onRecordPayment: (
    invoice: InvoiceSummary,
  ) => void;
}

function formatAmount(
  value: string,
): string {
  const amount =
    Number(
      value,
    );

  if (
    !Number.isFinite(
      amount,
    )
  ) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
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

  const date =
    new Date(
      value,
    );

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

function statusClassName(
  status: InvoiceStatus,
): string {
  if (status === "PAID") {
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
    "PARTIALLY_PAID"
  ) {
    return (
      "border-blue-200 "
      +
      "bg-blue-50 "
      +
      "text-blue-700"
    );
  }

  if (status === "ISSUED") {
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

function displayStatus(
  status: InvoiceStatus,
): string {
  return status
    .replaceAll(
      "_",
      " ",
    )
    .toLowerCase()
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase(),
    );
}

export default function InvoiceDetailDialog({
  open,
  invoiceId,
  onClose,
  onRecordPayment,
}: InvoiceDetailDialogProps) {
  const {
    authentication,
  } = useAuth();

  const invoiceQuery =
    useInvoice(
      invoiceId ?? "",
      open
      &&
      Boolean(
        invoiceId,
      ),
    );

  const issueMutation =
    useIssueInvoice();

  const cancelMutation =
    useCancelInvoice();

  if (!open) {
    return null;
  }

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const canIssue =
    hasPermission(
      permissions,
      "invoices.issue",
    );

  const canCancel =
    hasPermission(
      permissions,
      "invoices.cancel",
    );

  const canRecordPayment =
    hasPermission(
      permissions,
      "invoices.record_payment",
    );

  const invoice =
    invoiceQuery.data;

  const actionPending =
    issueMutation.isPending
    ||
    cancelMutation.isPending;

  async function issue():
    Promise<void> {
    if (!invoice) {
      return;
    }

    const accepted =
      window.confirm(
        (
          `Issue ${invoice.invoice_number}? `
          +
          "The invoice will become payable."
        ),
      );

    if (!accepted) {
      return;
    }

    try {
      await issueMutation
        .mutateAsync(
          invoice.id,
        );
    } catch {
      // Mutation error is displayed below.
    }
  }

  async function cancel():
    Promise<void> {
    if (!invoice) {
      return;
    }

    const accepted =
      window.confirm(
        (
          `Cancel ${invoice.invoice_number}? `
          +
          "This action cannot be reversed."
        ),
      );

    if (!accepted) {
      return;
    }

    try {
      await cancelMutation
        .mutateAsync(
          invoice.id,
        );
    } catch {
      // Mutation error is displayed below.
    }
  }

  const actionError =
    issueMutation.error
    ??
    cancelMutation.error;

  return (
    <div
      role="presentation"
      className="
        fixed inset-0 z-50 flex
        items-center justify-center
        bg-slate-950/50 p-4
      "
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="invoice-detail-title"
        className="
          max-h-[calc(100vh-2rem)]
          w-full max-w-5xl
          overflow-y-auto rounded-2xl
          border border-slate-200
          bg-white text-slate-900
          shadow-2xl
        "
      >
        <header
          className="
            sticky top-0 z-10
            flex items-start
            justify-between gap-4
            border-b border-slate-200
            bg-white px-5 py-4
            sm:px-6
          "
        >
          <div>
            <h2
              id="invoice-detail-title"
              className="
                text-lg font-semibold
                text-slate-950
              "
            >
              {invoice
                ?.invoice_number
                ??
                "Invoice Details"}
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-600
              "
            >
              Review billing, totals and
              invoice lifecycle information.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close"
            disabled={actionPending}
            onClick={onClose}
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

        {invoiceQuery.isPending ? (
          <div
            className="
              px-6 py-16 text-center
              text-sm text-slate-600
            "
          >
            Loading invoice…
          </div>
        ) : null}

        {invoiceQuery.isError ? (
          <div
            className="
              m-6 rounded-xl border
              border-red-200 bg-red-50
              px-4 py-3 text-sm
              text-red-700
            "
          >
            {invoiceQuery.error
              instanceof Error
              ? invoiceQuery.error.message
              : "Unable to load the invoice."}
          </div>
        ) : null}

        {invoice ? (
          <>
            <div
              className="
                flex flex-wrap items-center
                justify-between gap-3
                border-b border-slate-200
                px-5 py-4 sm:px-6
              "
            >
              <div
                className="
                  flex flex-wrap
                  items-center gap-3
                "
              >
                <span
                  className={`
                    rounded-full border
                    px-3 py-1 text-xs
                    font-semibold
                    ${statusClassName(
                      invoice.status,
                    )}
                  `}
                >
                  {displayStatus(
                    invoice.status,
                  )}
                </span>

                <span
                  className="
                    text-sm text-slate-600
                  "
                >
                  {invoice.sales_order
                    ?.so_number
                    ??
                    "No sales order"}
                </span>
              </div>

              <div
                className="
                  flex flex-wrap gap-2
                "
              >
                {canIssue && invoice.status === "DRAFT" && <><InvoiceDetails key={invoice.id+"details"} id={invoice.id}/><InvoiceDescriptions key={invoice.id} invoice={invoice}/></>}
                <DocumentActions
                  documentType="INVOICE"
                  documentId={invoice.id}
                  documentNumber={
                    invoice.invoice_number
                  }
                  defaultRecipient={
                    invoice.customer.email
                  }
                  disabled={actionPending}
                />
                {(
                  canIssue
                  &&
                  invoice.status === "DRAFT"
                ) ? (
                  <button
                    type="button"
                    disabled={actionPending}
                    onClick={() => {
                      void issue();
                    }}
                    className="
                      inline-flex items-center
                      gap-2 rounded-lg
                      bg-violet-600
                      px-3 py-2 text-sm
                      font-semibold text-white
                      hover:bg-violet-700
                      disabled:opacity-50
                    "
                  >
                    <Send size={16} />
                    Issue
                  </button>
                ) : null}

                {(
                  canRecordPayment
                  &&
                  (
                    invoice.status === "ISSUED"
                    ||
                    invoice.status
                    ===
                    "PARTIALLY_PAID"
                  )
                  &&
                  Number(
                    invoice.balance_due,
                  ) > 0
                ) ? (
                  <button
                    type="button"
                    disabled={actionPending}
                    onClick={() => {
                      onRecordPayment(
                        invoice,
                      );
                    }}
                    className="
                      inline-flex items-center
                      gap-2 rounded-lg
                      bg-emerald-600
                      px-3 py-2 text-sm
                      font-semibold text-white
                      hover:bg-emerald-700
                      disabled:opacity-50
                    "
                  >
                    <CircleDollarSign
                      size={16}
                    />
                    Record Payment
                  </button>
                ) : null}

                {(
                  canCancel
                  &&
                  (
                    invoice.status === "DRAFT"
                    ||
                    invoice.status === "ISSUED"
                  )
                ) ? (
                  <button
                    type="button"
                    disabled={actionPending}
                    onClick={() => {
                      void cancel();
                    }}
                    className="
                      inline-flex items-center
                      gap-2 rounded-lg
                      border border-red-200
                      bg-white px-3 py-2
                      text-sm font-semibold
                      text-red-700
                      hover:bg-red-50
                      disabled:opacity-50
                    "
                  >
                    <Ban size={16} />
                    Cancel
                  </button>
                ) : null}
              </div>
            </div>

            {actionError ? (
              <div
                className="
                  mx-5 mt-5 rounded-xl
                  border border-red-200
                  bg-red-50 px-4 py-3
                  text-sm text-red-700
                  sm:mx-6
                "
              >
                {actionError
                  instanceof Error
                  ? actionError.message
                  : "Unable to update the invoice."}
              </div>
            ) : null}

            <div
              className="
                grid gap-4 px-5 py-5
                sm:grid-cols-2
                lg:grid-cols-4 sm:px-6
              "
            >
              <div
                className="
                  rounded-xl bg-slate-50
                  p-4
                "
              >
                <p
                  className="
                    text-xs font-medium
                    uppercase tracking-wide
                    text-slate-500
                  "
                >
                  Customer
                </p>

                <p
                  className="
                    mt-1 font-semibold
                    text-slate-950
                  "
                >
                  {invoice.customer.name}
                </p>

                <p
                  className="
                    mt-1 text-sm
                    text-slate-600
                  "
                >
                  {invoice.customer.code}
                </p>
              </div>

              <div
                className="
                  rounded-xl bg-slate-50
                  p-4
                "
              >
                <p
                  className="
                    text-xs font-medium
                    uppercase tracking-wide
                    text-slate-500
                  "
                >
                  Invoice date
                </p>

                <p
                  className="
                    mt-1 font-semibold
                    text-slate-950
                  "
                >
                  {formatDate(
                    invoice.invoice_date,
                  )}
                </p>
              </div>

              <div
                className="
                  rounded-xl bg-slate-50
                  p-4
                "
              >
                <p
                  className="
                    text-xs font-medium
                    uppercase tracking-wide
                    text-slate-500
                  "
                >
                  Due date
                </p>

                <p
                  className="
                    mt-1 font-semibold
                    text-slate-950
                  "
                >
                  {formatDate(
                    invoice.due_date,
                  )}
                </p>
              </div>

              <div
                className="
                  rounded-xl bg-slate-50
                  p-4
                "
              >
                <p
                  className="
                    text-xs font-medium
                    uppercase tracking-wide
                    text-slate-500
                  "
                >
                  Balance due
                </p>

                <p
                  className="
                    mt-1 text-lg font-bold
                    text-red-700
                  "
                >
                  ₹
                  {formatAmount(
                    invoice.balance_due,
                  )}
                </p>
              </div>
            </div>

            <div
              className="
                px-5 pb-5 sm:px-6
              "
            >
              <h3
                className="
                  mb-3 font-semibold
                  text-slate-950
                "
              >
                Items
              </h3>

              <div
                className="
                  overflow-x-auto
                  rounded-xl border
                  border-slate-200
                "
              >
                <table
                  className="
                    min-w-full divide-y
                    divide-slate-200
                  "
                >
                  <thead className="bg-slate-50">
                    <tr>
                      <th
                        className="
                          px-4 py-3 text-left
                          text-xs font-semibold
                          uppercase text-slate-600
                        "
                      >
                        Product
                      </th>

                      <th
                        className="
                          px-4 py-3 text-right
                          text-xs font-semibold
                          uppercase text-slate-600
                        "
                      >
                        Quantity
                      </th>

                      <th
                        className="
                          px-4 py-3 text-right
                          text-xs font-semibold
                          uppercase text-slate-600
                        "
                      >
                        Rate
                      </th>

                      <th
                        className="
                          px-4 py-3 text-right
                          text-xs font-semibold
                          uppercase text-slate-600
                        "
                      >
                        Total
                      </th>
                    </tr>
                  </thead>

                  <tbody
                    className="
                      divide-y divide-slate-100
                      bg-white
                    "
                  >
                    {invoice.items.map(
                      (
                        item,
                        index,
                      ) => (
                        <tr
                          key={`
                            ${item.product.id}
                            -
                            ${index}
                          `}
                        >
                          <td
                            className="
                              px-4 py-3
                              text-sm
                            "
                          >
                            <p
                              className="
                                font-medium
                                text-slate-950
                              "
                            >
                              {item.product.name}
                            </p>

                            <p
                              className="
                                text-xs
                                text-slate-500
                              "
                            >
                              {item.product.sku} · {item.item_type??"goods"} · HSN/SAC: {item.hsn_code||"—"}
                            </p>
                          </td>

                          <td
                            className="
                              px-4 py-3
                              text-right text-sm
                              text-slate-700
                            "
                          >
                            {item.quantity}
                            {" "}
                            {item.product.unit}
                          </td>

                          <td
                            className="
                              px-4 py-3
                              text-right text-sm
                              text-slate-700
                            "
                          >
                            ₹
                            {formatAmount(
                              item.unit_price,
                            )}
                          </td>

                          <td
                            className="
                              px-4 py-3
                              text-right text-sm
                              font-semibold
                              text-slate-950
                            "
                          >
                            ₹
                            ₹
                            {formatAmount(
                              item.line_total,
                            )}
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div
              className="
                grid gap-5 border-t
                border-slate-200
                px-5 py-5
                lg:grid-cols-2 sm:px-6
              "
            >
              <div>
                <h3
                  className="
                    font-semibold
                    text-slate-950
                  "
                >
                  Billing information
                </h3>

                <div
                  className="
                    mt-3 text-sm
                    leading-6 text-slate-600
                  "
                >
                  <p
                    className="
                      font-medium
                      text-slate-900
                    "
                  >
                    {invoice.billing.name}
                  </p>

                  <p>
                    {[
                      invoice.billing.address,
                      invoice.billing.city,
                      invoice.billing.state,
                      invoice.billing.country,
                      invoice.billing.pincode,
                    ]
                      .filter(
                        Boolean,
                      )
                      .join(
                        ", ",
                      )
                      ||
                      "—"}
                  </p>

                  <p>
                    GSTIN:{" "}
                    {invoice.billing.gstin
                      ??
                      "—"}
                  </p>
                </div>

                {invoice.notes ? (
                  <div className="mt-4">
                    <p
                      className="
                        text-xs font-medium
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Notes
                    </p>

                    <p
                      className="
                        mt-1 whitespace-pre-wrap
                        text-sm text-slate-700
                      "
                    >
                      {invoice.notes}
                    </p>
                  </div>
                ) : null}
              </div>

              <div
                className="
                  rounded-xl bg-slate-50
                  p-4
                "
              >
                <div
                  className="
                    space-y-2 text-sm
                  "
                >
                  <div
                    className="
                      flex justify-between
                      gap-4
                    "
                  >
                    <span className="text-slate-600">
                      Subtotal
                    </span>

                    <span className="text-slate-900">
                      ₹
                      {formatAmount(
                        invoice.subtotal,
                      )}
                    </span>
                  </div>

                  <div
                    className="
                      flex justify-between
                      gap-4
                    "
                  >
                    <span className="text-slate-600">
                      Tax
                    </span>

                    <span className="text-slate-900">
                      ₹
                      {formatAmount(
                        invoice.tax_amount,
                      )}
                    </span>
                  </div>

                  <div
                    className="
                      flex justify-between
                      gap-4
                    "
                  >
                    <span className="text-slate-600">
                      Discount
                    </span>

                    <span className="text-slate-900">
                      ₹
                      {formatAmount(
                        invoice.discount_amount,
                      )}
                    </span>
                  </div>

                  <div
                    className="
                      flex justify-between
                      gap-4 border-t
                      border-slate-200 pt-2
                      font-semibold
                    "
                  >
                    <span>
                      Total
                    </span>

                    <span>
                      ₹
                      {formatAmount(
                        invoice.total_amount,
                      )}
                    </span>
                  </div>

                  <div
                    className="
                      flex justify-between
                      gap-4 text-emerald-700
                    "
                  >
                    <span>
                      Paid
                    </span>

                    <span>
                      ₹
                      {formatAmount(
                        invoice.amount_paid,
                      )}
                    </span>
                  </div>

                  <div
                    className="
                      flex justify-between
                      gap-4 font-bold
                      text-red-700
                    "
                  >
                    <span>
                      Balance
                    </span>

                    <span>
                      ₹
                      {formatAmount(
                        invoice.balance_due,
                      )}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <footer
              className="
                border-t border-slate-200
                bg-slate-50 px-5 py-4
                text-xs text-slate-500
                sm:px-6
              "
            >
              Issued:{" "}
              {formatDate(
                invoice.issued_at,
              )}
              {" · "}
              Paid:{" "}
              {formatDate(
                invoice.paid_at,
              )}
              {" · "}
              Cancelled:{" "}
              {formatDate(
                invoice.cancelled_at,
              )}
            </footer>
          </>
        ) : null}
      </section>
    </div>
  );
}
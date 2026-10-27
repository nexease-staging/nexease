"use client";

import {
  X,
} from "lucide-react";

import {
  useCustomerPayment,
} from "@/features/customer-payments/hooks";

import DocumentActions from "@/features/documents/components/document-actions";

interface CustomerPaymentDetailDialogProps {
  open: boolean;
  paymentId: string | null;
  onClose: () => void;
  onOpenInvoice?: (
    invoiceId: string,
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

function displayPaymentMethod(
  value: string,
): string {
  return value
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

export default function CustomerPaymentDetailDialog({
  open,
  paymentId,
  onClose,
  onOpenInvoice,
}: CustomerPaymentDetailDialogProps) {
  const paymentQuery =
    useCustomerPayment(
      paymentId ?? "",
      open
      &&
      Boolean(
        paymentId,
      ),
    );

  if (!open) {
    return null;
  }

  const payment =
    paymentQuery.data;

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
        aria-labelledby="payment-detail-title"
        className="
          max-h-[calc(100vh-2rem)]
          w-full max-w-3xl
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
              id="payment-detail-title"
              className="
                text-lg font-semibold
                text-slate-950
              "
            >
              {payment
                ?.payment_number
                ??
                "Payment Details"}
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-600
              "
            >
              Customer receipt and invoice
              allocation information.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close"
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

        {payment ? (
          <div
            className="
              flex flex-wrap justify-end
              gap-2 border-b
              border-slate-200
              bg-white px-5 py-3
              sm:px-6
            "
          >
            <DocumentActions
              documentType="CUSTOMER_PAYMENT"
              documentId={payment.id}
              documentNumber={
                payment.payment_number
              }
            />
          </div>
        ) : null}

        {paymentQuery.isPending ? (
          <div
            className="
              px-6 py-16 text-center
              text-sm text-slate-600
            "
          >
            Loading payment…
          </div>
        ) : null}

        {paymentQuery.isError ? (
          <div
            className="
              m-6 rounded-xl border
              border-red-200 bg-red-50
              px-4 py-3 text-sm
              text-red-700
            "
          >
            {paymentQuery.error
              instanceof Error
              ? paymentQuery.error.message
              : "Unable to load the payment."}
          </div>
        ) : null}

        {payment ? (
          <>
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
                    text-xs font-semibold
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
                  {payment.customer.name}
                </p>

                <p
                  className="
                    mt-1 text-xs
                    text-slate-500
                  "
                >
                  {payment.customer.code}
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
                    text-xs font-semibold
                    uppercase tracking-wide
                    text-slate-500
                  "
                >
                  Amount
                </p>

                <p
                  className="
                    mt-1 text-lg font-bold
                    text-emerald-700
                  "
                >
                  ₹
                  {formatAmount(
                    payment.amount,
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
                    text-xs font-semibold
                    uppercase tracking-wide
                    text-slate-500
                  "
                >
                  Payment date
                </p>

                <p
                  className="
                    mt-1 font-semibold
                    text-slate-950
                  "
                >
                  {formatDate(
                    payment.payment_date,
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
                    text-xs font-semibold
                    uppercase tracking-wide
                    text-slate-500
                  "
                >
                  Method
                </p>

                <p
                  className="
                    mt-1 font-semibold
                    text-slate-950
                  "
                >
                  {displayPaymentMethod(
                    payment.payment_method,
                  )}
                </p>
              </div>
            </div>

            <div
              className="
                grid gap-5 border-t
                border-slate-200
                px-5 py-5
                md:grid-cols-2 sm:px-6
              "
            >
              <div>
                <h3
                  className="
                    font-semibold
                    text-slate-950
                  "
                >
                  Receiving account
                </h3>

                <div
                  className="
                    mt-3 rounded-xl
                    border border-slate-200
                    p-4 text-sm
                  "
                >
                  {payment.bank_account ? (
                    <>
                      <p
                        className="
                          font-semibold
                          text-slate-900
                        "
                      >
                        {
                          payment
                            .bank_account
                            .account_name
                        }
                      </p>

                      <p
                        className="
                          mt-1 text-slate-600
                        "
                      >
                        {
                          payment
                            .bank_account
                            .bank_name
                          ??
                          payment
                            .bank_account
                            .account_type
                        }
                      </p>

                      <p
                        className="
                          mt-1 text-slate-600
                        "
                      >
                        {
                          payment
                            .bank_account
                            .masked_account_number
                          ??
                          "Account number unavailable"
                        }
                      </p>
                    </>
                  ) : (
                    <p className="text-slate-600">
                      No receiving account recorded.
                    </p>
                  )}
                </div>
              </div>

              <div>
                <h3
                  className="
                    font-semibold
                    text-slate-950
                  "
                >
                  Reference
                </h3>

                <dl
                  className="
                    mt-3 space-y-3
                    rounded-xl border
                    border-slate-200 p-4
                    text-sm
                  "
                >
                  <div>
                    <dt className="text-slate-500">
                      Reference number
                    </dt>

                    <dd
                      className="
                        mt-0.5 font-medium
                        text-slate-900
                      "
                    >
                      {payment.reference_number
                        ??
                        "—"}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-slate-500">
                      Recorded by
                    </dt>

                    <dd
                      className="
                        mt-0.5 font-medium
                        text-slate-900
                      "
                    >
                      {payment.created_by
                        ? (
                          payment.created_by
                            .first_name
                          +
                          " "
                          +
                          payment.created_by
                            .last_name
                        )
                        : "—"}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-slate-500">
                      Recorded on
                    </dt>

                    <dd
                      className="
                        mt-0.5 font-medium
                        text-slate-900
                      "
                    >
                      {formatDate(
                        payment.created_at,
                      )}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            <div
              className="
                border-t border-slate-200
                px-5 py-5 sm:px-6
              "
            >
              <h3
                className="
                  font-semibold
                  text-slate-950
                "
              >
                Invoice allocations
              </h3>

              <div
                className="
                  mt-3 overflow-x-auto
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
                      {[
                        "Invoice",
                        "Invoice Date",
                        "Invoice Total",
                        "Allocated",
                        "Balance",
                      ].map(
                        (heading) => (
                          <th
                            key={heading}
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-left
                              text-xs font-semibold
                              uppercase tracking-wide
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
                      divide-y divide-slate-100
                    "
                  >
                    {payment.allocations.map(
                      (allocation) => (
                        <tr
                          key={
                            allocation
                              .invoice
                              .id
                          }
                        >
                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3
                            "
                          >
                            <button
                              type="button"
                              disabled={
                                !onOpenInvoice
                              }
                              onClick={() => {
                                onOpenInvoice?.(
                                  allocation
                                    .invoice
                                    .id,
                                );
                              }}
                              className="
                                text-sm font-semibold
                                text-blue-700
                                hover:underline
                                disabled:cursor-default
                                disabled:text-slate-900
                                disabled:no-underline
                              "
                            >
                              {
                                allocation
                                  .invoice
                                  .invoice_number
                              }
                            </button>
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              text-slate-700
                            "
                          >
                            {formatDate(
                              allocation
                                .invoice
                                .invoice_date,
                            )}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              text-slate-700
                            "
                          >
                            ₹
                            {formatAmount(
                              allocation
                                .invoice
                                .total_amount,
                            )}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              font-semibold
                              text-emerald-700
                            "
                          >
                            ₹
                            {formatAmount(
                              allocation.amount,
                            )}
                          </td>

                          <td
                            className="
                              whitespace-nowrap
                              px-4 py-3 text-sm
                              text-red-700
                            "
                          >
                            ₹
                            {formatAmount(
                              allocation
                                .invoice
                                .balance_due,
                            )}
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>

              {payment.notes ? (
                <div
                  className="
                    mt-5 rounded-xl
                    bg-slate-50 p-4
                  "
                >
                  <p
                    className="
                      text-xs font-semibold
                      uppercase tracking-wide
                      text-slate-500
                    "
                  >
                    Notes
                  </p>

                  <p
                    className="
                      mt-2 whitespace-pre-wrap
                      text-sm text-slate-700
                    "
                  >
                    {payment.notes}
                  </p>
                </div>
              ) : null}
            </div>
          </>
        ) : null}
      </section>
    </div>
  );
}
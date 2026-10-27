"use client";

import DocumentActions from "@/features/documents/components/document-actions";

import {
  useState,
} from "react";

import {
  Ban,
  CheckCircle2,
  CreditCard,
  X,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import VendorBillPaymentDialog from "@/features/vendor-bills/components/vendor-bill-payment-dialog";

import {
  useCancelVendorBill,
  usePostVendorBill,
  useVendorBill,
} from "@/features/vendor-bills/hooks";

import type {
  VendorBillStatus,
} from "@/features/vendor-bills/types";

import {
  APIRequestError,
} from "@/lib/api/client";

interface VendorBillDetailDialogProps {
  open: boolean;
  billId: string;
  onClose: () => void;
}

const statusStyles:
  Record<
    VendorBillStatus,
    string
  > = {
    DRAFT:
      "bg-slate-100 text-slate-700",
    POSTED:
      "bg-blue-100 text-blue-700",
    PARTIALLY_PAID:
      "bg-amber-100 text-amber-700",
    PAID:
      "bg-emerald-100 text-emerald-700",
    CANCELLED:
      "bg-red-100 text-red-700",
  };

function formatStatus(
  status: VendorBillStatus,
): string {
  return status
    .toLowerCase()
    .split("_")
    .map(
      (word) =>
        (
          word.charAt(0)
          .toUpperCase()
          +
          word.slice(1)
        ),
    )
    .join(" ");
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

  return "Unable to complete the request.";
}

export default function VendorBillDetailDialog({
  open,
  billId,
  onClose,
}: VendorBillDetailDialogProps) {
  const {
    authentication,
  } = useAuth();

  const [
    paymentOpen,
    setPaymentOpen,
  ] = useState(false);

  const [
    actionError,
    setActionError,
  ] = useState<string | null>(
    null,
  );

  const vendorBillQuery =
    useVendorBill(
      billId,
      (
        open
        &&
        Boolean(billId)
      ),
    );

  const postMutation =
    usePostVendorBill();

  const cancelMutation =
    useCancelVendorBill();

  if (!open) {
    return null;
  }

  const vendorBill =
    vendorBillQuery.data;

  const permissions =
    authentication
      ?.role
      .permissions
      ??
      [];

  const canPost =
    Boolean(
      vendorBill
      &&
      vendorBill.status
      ===
      "DRAFT"
      &&
      permissions.includes(
        "bills.post",
      ),
    );

  const canCancel =
    Boolean(
      vendorBill
      &&
      (
        vendorBill.status
        ===
        "DRAFT"
        ||
        vendorBill.status
        ===
        "POSTED"
      )
      &&
      permissions.includes(
        "bills.cancel",
      ),
    );

  const canPay =
    Boolean(
      vendorBill
      &&
      (
        vendorBill.status
        ===
        "POSTED"
        ||
        vendorBill.status
        ===
        "PARTIALLY_PAID"
      )
      &&
      Number(
        vendorBill.balance_due,
      ) > 0
      &&
      permissions.includes(
        "bills.record_payment",
      ),
    );

  const actionPending =
    postMutation.isPending
    ||
    cancelMutation.isPending;

  async function handlePost():
    Promise<void> {
    if (!vendorBill) {
      return;
    }

    const accepted =
      window.confirm(
        (
          `Post vendor bill `
          +
          `${vendorBill.bill_number}? `
          +
          `This creates the accounting entry.`
        ),
      );

    if (!accepted) {
      return;
    }

    setActionError(null);

    try {
      await postMutation
        .mutateAsync(
          vendorBill.id,
        );
    } catch (error) {
      setActionError(
        getErrorMessage(error),
      );
    }
  }

  async function handleCancel():
    Promise<void> {
    if (!vendorBill) {
      return;
    }

    const accepted =
      window.confirm(
        (
          `Cancel vendor bill `
          +
          `${vendorBill.bill_number}?`
        ),
      );

    if (!accepted) {
      return;
    }

    setActionError(null);

    try {
      await cancelMutation
        .mutateAsync(
          vendorBill.id,
        );
    } catch (error) {
      setActionError(
        getErrorMessage(error),
      );
    }
  }

  return (
    <>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="
          vendor-bill-detail-title
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
            text-slate-950 shadow-2xl
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
            <div>
              <p
                className="
                  text-xs font-semibold
                  uppercase tracking-wide
                  text-blue-600
                "
              >
                Vendor bill
              </p>

              <h2
                id="
                  vendor-bill-detail-title
                "
                className="
                  mt-1 text-lg font-bold
                  text-slate-950 sm:text-xl
                "
              >
                {vendorBill
                  ?.bill_number
                  ??
                  "Bill details"}
              </h2>
            </div>

            <button
              type="button"
              aria-label="Close dialog"
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

          <div
            className="
              min-h-0 flex-1
              overflow-y-auto
              bg-slate-50 p-4 sm:p-6
            "
          >
            {vendorBillQuery.isLoading
              ? (
                <div
                  className="
                    rounded-xl border
                    border-slate-200 bg-white
                    px-5 py-12 text-center
                    text-sm text-slate-600
                  "
                >
                  Loading vendor bill…
                </div>
              )
              : null}

            {vendorBillQuery.isError
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
                    vendorBillQuery.error,
                  )}
                </div>
              )
              : null}

            {vendorBill
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
                              vendorBill
                                .bill_number
                            }
                          </h3>

                          <span
                            className={`
                              rounded-full
                              px-2.5 py-1
                              text-xs font-semibold
                              ${
                                statusStyles[
                                  vendorBill
                                    .status
                                ]
                              }
                            `}
                          >
                            {formatStatus(
                              vendorBill.status,
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
                            vendorBill
                              .supplier.name
                          }
                        </p>

                        <p
                          className="
                            mt-1 text-xs
                            text-slate-500
                          "
                        >
                          Supplier invoice:{" "}
                          {
                            vendorBill
                              .supplier_invoice_number
                            ??
                            "—"
                          }
                        </p>
                      </div>

                      <div
                        className="
                          text-left sm:text-right
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
                            mt-1 text-2xl
                            font-bold text-slate-950
                          "
                        >
                          {formatAmount(
                            vendorBill
                              .balance_due,
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
                    <InfoCard
                      label="Purchase order"
                      value={
                        vendorBill
                          .purchase_order
                          ?.po_number
                        ??
                        "—"
                      }
                    />

                    <InfoCard
                      label="Bill date"
                      value={formatDate(
                        vendorBill
                          .bill_date,
                      )}
                    />

                    <InfoCard
                      label="Due date"
                      value={formatDate(
                        vendorBill
                          .due_date,
                      )}
                    />

                    <InfoCard
                      label="Total amount"
                      value={formatAmount(
                        vendorBill
                          .total_amount,
                      )}
                    />
                  </section>

                  <section
                    className="
                      overflow-hidden
                      rounded-xl border
                      border-slate-200
                      bg-white shadow-sm
                    "
                  >
                    <div
                      className="
                        border-b
                        border-slate-200
                        px-4 py-4 sm:px-5
                      "
                    >
                      <h3
                        className="
                          font-bold
                          text-slate-950
                        "
                      >
                        Bill items
                      </h3>
                    </div>

                    <div
                      className="
                        divide-y
                        divide-slate-200
                        md:hidden
                      "
                    >
                      {vendorBill.items.map(
                        (item) => (
                          <article
                            key={
                              item.product.id
                            }
                            className="p-4"
                          >
                            <p
                              className="
                                font-semibold
                                text-slate-950
                              "
                            >
                              {
                                item
                                  .product.name
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
                                  .product.sku
                              }
                            </p>

                            <div
                              className="
                                mt-3 flex
                                justify-between
                                gap-3 text-sm
                              "
                            >
                              <span
                                className="
                                  text-slate-600
                                "
                              >
                                {item.quantity}
                                {" × "}
                                {formatAmount(
                                  item.unit_price,
                                )}
                              </span>

                              <span
                                className="
                                  font-bold
                                  text-slate-950
                                "
                              >
                                {formatAmount(
                                  item.line_total,
                                )}
                              </span>
                            </div>
                          </article>
                        ),
                      )}
                    </div>

                    <div
                      className="
                        hidden overflow-x-auto
                        md:block
                      "
                    >
                      <table
                        className="
                          min-w-full divide-y
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
                              "Quantity",
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
                          "
                        >
                          {vendorBill.items.map(
                            (item) => (
                              <tr
                                key={
                                  item
                                    .product.id
                                }
                              >
                                <td
                                  className="
                                    px-4 py-3
                                  "
                                >
                                  <p
                                    className="
                                      text-sm
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
                                  {item.quantity}
                                </td>

                                <td
                                  className="
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
                                  {item.tax_rate}%
                                </td>

                                <td
                                  className="
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
                                    px-4 py-3
                                    text-sm
                                    font-semibold
                                    text-slate-950
                                  "
                                >
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
                          font-bold
                          text-slate-950
                        "
                      >
                        Supplier and notes
                      </h3>

                      <p
                        className="
                          mt-3 text-sm
                          text-slate-700
                        "
                      >
                        {
                          vendorBill
                            .supplier_snapshot
                            .name
                        }
                      </p>

                      <p
                        className="
                          mt-1 text-sm
                          text-slate-600
                        "
                      >
                        {[
                          vendorBill
                            .supplier_snapshot
                            .address,
                          vendorBill
                            .supplier_snapshot
                            .city,
                          vendorBill
                            .supplier_snapshot
                            .state,
                          vendorBill
                            .supplier_snapshot
                            .pincode,
                        ]
                          .filter(Boolean)
                          .join(", ")
                          ||
                          "Address unavailable"}
                      </p>

                      <div
                        className="
                          mt-4 border-t
                          border-slate-200 pt-4
                        "
                      >
                        <p
                          className="
                            text-xs
                            text-slate-500
                          "
                        >
                          Notes
                        </p>

                        <p
                          className="
                            mt-2 whitespace-pre-wrap
                            text-sm leading-6
                            text-slate-700
                          "
                        >
                          {
                            vendorBill.notes
                            ||
                            "No notes added."
                          }
                        </p>
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
                          font-bold
                          text-slate-950
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
                        <AmountRow
                          label="Subtotal"
                          value={formatAmount(
                            vendorBill
                              .subtotal,
                          )}
                        />

                        <AmountRow
                          label="Tax"
                          value={formatAmount(
                            vendorBill
                              .tax_amount,
                          )}
                        />

                        <AmountRow
                          label="Discount"
                          value={
                            (
                              "- "
                              +
                              formatAmount(
                                vendorBill
                                  .discount_amount,
                              )
                            )
                          }
                        />

                        <AmountRow
                          label="Total"
                          value={formatAmount(
                            vendorBill
                              .total_amount,
                          )}
                          strong
                        />

                        <AmountRow
                          label="Paid"
                          value={formatAmount(
                            vendorBill
                              .amount_paid,
                          )}
                        />

                        <AmountRow
                          label="Balance"
                          value={formatAmount(
                            vendorBill
                              .balance_due,
                          )}
                          strong
                        />
                      </dl>
                    </section>
                  </div>

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
              flex flex-wrap justify-end
              gap-2 border-t
              border-slate-200 bg-white
              px-4 py-4 sm:px-6
            "
          >
            <button
              type="button"
              disabled={actionPending}
              onClick={onClose}
              className="
                rounded-lg border
                border-slate-300 px-4 py-2
                text-sm font-semibold
                text-slate-700
                hover:bg-slate-50
                disabled:opacity-50
              "
            >
              Close
            </button>
              {vendorBill ? (
                <DocumentActions
                  documentType="VENDOR_BILL"
                  documentId={vendorBill.id}
                  documentNumber={
                    vendorBill.bill_number
                  }
                  defaultRecipient={
                    vendorBill.supplier.email
                  }
                  disabled={actionPending}
                />
              ) : null}
            {canPost
              ? (
                <button
                  type="button"
                  disabled={actionPending}
                  onClick={() => {
                    void handlePost();
                  }}
                  className="
                    inline-flex items-center
                    gap-2 rounded-lg
                    bg-emerald-600
                    px-4 py-2 text-sm
                    font-semibold text-white
                    hover:bg-emerald-700
                    disabled:opacity-50
                  "
                >
                  <CheckCircle2
                    size={17}
                  />

                  {postMutation.isPending
                    ? "Posting…"
                    : "Post bill"}
                </button>
              )
              : null}

            {canPay
              ? (
                <button
                  type="button"
                  disabled={actionPending}
                  onClick={() => {
                    setPaymentOpen(true);
                  }}
                  className="
                    inline-flex items-center
                    gap-2 rounded-lg
                    bg-blue-600 px-4 py-2
                    text-sm font-semibold
                    text-white
                    hover:bg-blue-700
                  "
                >
                  <CreditCard size={17} />
                  Record payment
                </button>
              )
              : null}

            {canCancel
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
                    disabled:opacity-50
                  "
                >
                  <Ban size={17} />

                  {cancelMutation.isPending
                    ? "Cancelling…"
                    : "Cancel bill"}
                </button>
              )
              : null}
          </footer>
        </div>
      </div>

      <VendorBillPaymentDialog
        open={paymentOpen}
        vendorBill={
          vendorBill
          ??
          null
        }
        onClose={() => {
          setPaymentOpen(false);
        }}
        onRecorded={() => {
          setPaymentOpen(false);
        }}
      />
    </>
  );
}

interface InfoCardProps {
  label: string;
  value: string;
}

function InfoCard({
  label,
  value,
}: InfoCardProps) {
  return (
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
        {label}
      </p>

      <p
        className="
          mt-2 text-sm font-bold
          text-slate-950
        "
      >
        {value}
      </p>
    </div>
  );
}

interface AmountRowProps {
  label: string;
  value: string;
  strong?: boolean;
}

function AmountRow({
  label,
  value,
  strong = false,
}: AmountRowProps) {
  return (
    <div
      className={`
        flex justify-between gap-4
        ${
          strong
            ? (
              "border-t "
              +
              "border-slate-200 pt-3"
            )
            : ""
        }
      `}
    >
      <dt
        className={
          strong
            ? (
              "font-bold "
              +
              "text-slate-950"
            )
            : "text-slate-600"
        }
      >
        {label}
      </dt>

      <dd
        className={
          strong
            ? (
              "font-bold "
              +
              "text-slate-950"
            )
            : (
              "font-medium "
              +
              "text-slate-900"
            )
        }
      >
        {value}
      </dd>
    </div>
  );
}
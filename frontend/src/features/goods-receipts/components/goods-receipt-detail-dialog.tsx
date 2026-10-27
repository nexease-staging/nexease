"use client";

import {
  PackageCheck,
  X,
} from "lucide-react";

import DocumentActions from "@/features/documents/components/document-actions";

import {
  useGoodsReceipt,
} from "@/features/goods-receipts/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

interface GoodsReceiptDetailDialogProps {
  open: boolean;
  goodsReceiptId: string;
  onClose: () => void;
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
    "Unable to load the goods receipt."
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

function formatQuantity(
  value: string,
): string {
  const quantity =
    Number(value);

  if (
    Number.isNaN(quantity)
  ) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      minimumFractionDigits: 0,
      maximumFractionDigits: 4,
    },
  ).format(
    quantity,
  );
}

export default function GoodsReceiptDetailDialog({
  open,
  goodsReceiptId,
  onClose,
}: GoodsReceiptDetailDialogProps) {
  const goodsReceiptQuery =
    useGoodsReceipt(
      goodsReceiptId,
      (
        open
        &&
        Boolean(
          goodsReceiptId,
        )
      ),
    );

  if (!open) {
    return null;
  }

  const goodsReceipt =
    goodsReceiptQuery.data;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="
        goods-receipt-detail-title
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
          sm:max-w-4xl sm:rounded-2xl
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
              Goods receipt
            </p>

            <h2
              id="
                goods-receipt-detail-title
              "
              className="
                mt-1 text-lg font-bold
                text-slate-950 sm:text-xl
              "
            >
              {goodsReceipt
                ?.grn_number
                ??
                "Receipt details"}
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
          {goodsReceiptQuery.isLoading
            ? (
              <div
                className="
                  rounded-xl border
                  border-slate-200 bg-white
                  px-5 py-12 text-center
                  text-sm text-slate-600
                "
              >
                Loading receipt…
              </div>
            )
            : null}

          {goodsReceiptQuery.isError
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
                  goodsReceiptQuery.error,
                )}
              </div>
            )
            : null}

          {goodsReceipt
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
                          flex items-center gap-2
                        "
                      >
                        <PackageCheck
                          size={22}
                          className="
                            text-emerald-600
                          "
                        />

                        <h3
                          className="
                            text-xl font-bold
                            text-slate-950
                          "
                        >
                          {
                            goodsReceipt
                              .grn_number
                          }
                        </h3>
                      </div>

                      <p
                        className="
                          mt-2 text-sm
                          text-slate-600
                        "
                      >
                        Received against{" "}
                        <span
                          className="
                            font-semibold
                            text-slate-900
                          "
                        >
                          {
                            goodsReceipt
                              .purchase_order
                              .po_number
                          }
                        </span>
                      </p>
                    </div>

                    <span
                      className="
                        w-fit rounded-full
                        bg-emerald-100
                        px-2.5 py-1
                        text-xs font-semibold
                        text-emerald-700
                      "
                    >
                      Received
                    </span>
                  </div>
                </section>

                <section
                  className="
                    grid gap-4
                    sm:grid-cols-2
                    lg:grid-cols-4
                  "
                >
                  <DetailCard
                    label="Supplier"
                    value={
                      goodsReceipt
                        .supplier.name
                    }
                    helper={
                      goodsReceipt
                        .supplier.code
                    }
                  />

                  <DetailCard
                    label="Warehouse"
                    value={
                      goodsReceipt
                        .warehouse.name
                    }
                    helper={
                      goodsReceipt
                        .warehouse.code
                    }
                  />

                  <DetailCard
                    label="Items received"
                    value={String(
                      goodsReceipt
                        .item_count,
                    )}
                  />

                  <DetailCard
                    label="Received at"
                    value={formatDateTime(
                      goodsReceipt
                        .received_at,
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
                      Received items
                    </h3>
                  </div>

                  <div
                    className="
                      divide-y
                      divide-slate-200
                      md:hidden
                    "
                  >
                    {goodsReceipt.items.map(
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

                          <p
                            className="
                              mt-3 text-sm
                              text-slate-700
                            "
                          >
                            Quantity received:{" "}
                            <span
                              className="
                                font-bold
                                text-slate-950
                              "
                            >
                              {formatQuantity(
                                item
                                  .quantity_received,
                              )}{" "}
                              {
                                item
                                  .product.unit
                              }
                            </span>
                          </p>
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
                          <th
                            className="
                              px-4 py-3
                              text-left text-xs
                              font-semibold
                              uppercase
                              tracking-wide
                              text-slate-600
                            "
                          >
                            Product
                          </th>

                          <th
                            className="
                              px-4 py-3
                              text-left text-xs
                              font-semibold
                              uppercase
                              tracking-wide
                              text-slate-600
                            "
                          >
                            SKU
                          </th>

                          <th
                            className="
                              px-4 py-3
                              text-left text-xs
                              font-semibold
                              uppercase
                              tracking-wide
                              text-slate-600
                            "
                          >
                            Quantity received
                          </th>

                          <th
                            className="
                              px-4 py-3
                              text-left text-xs
                              font-semibold
                              uppercase
                              tracking-wide
                              text-slate-600
                            "
                          >
                            Unit
                          </th>
                        </tr>
                      </thead>

                      <tbody
                        className="
                          divide-y
                          divide-slate-200
                        "
                      >
                        {goodsReceipt
                          .items
                          .map(
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
                                </td>

                                <td
                                  className="
                                    px-4 py-3
                                    text-sm
                                    text-slate-600
                                  "
                                >
                                  {
                                    item
                                      .product
                                      .sku
                                  }
                                </td>

                                <td
                                  className="
                                    px-4 py-3
                                    text-sm
                                    font-semibold
                                    text-slate-950
                                  "
                                >
                                  {formatQuantity(
                                    item
                                      .quantity_received,
                                  )}
                                </td>

                                <td
                                  className="
                                    px-4 py-3
                                    text-sm
                                    text-slate-600
                                  "
                                >
                                  {
                                    item
                                      .product
                                      .unit
                                  }
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
                    Receipt information
                  </h3>

                  <div
                    className="
                      mt-4 grid gap-4
                      sm:grid-cols-2
                    "
                  >
                    <div>
                      <p
                        className="
                          text-xs
                          text-slate-500
                        "
                      >
                        Received by
                      </p>

                      <p
                        className="
                          mt-1 text-sm
                          font-medium
                          text-slate-900
                        "
                      >
                        {goodsReceipt
                          .received_by
                          ?.email
                          ??
                          "—"}
                      </p>
                    </div>

                    <div>
                      <p
                        className="
                          text-xs
                          text-slate-500
                        "
                      >
                        Created at
                      </p>

                      <p
                        className="
                          mt-1 text-sm
                          font-medium
                          text-slate-900
                        "
                      >
                        {formatDateTime(
                          goodsReceipt
                            .created_at,
                        )}
                      </p>
                    </div>
                  </div>

                  <div
                    className="
                      mt-4 border-t
                      border-slate-200 pt-4
                    "
                  >
                    <p
                      className="
                        text-xs text-slate-500
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
                        goodsReceipt.notes
                        ||
                        "No notes added."
                      }
                    </p>
                  </div>
                </section>
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
            onClick={onClose}
            className="
              rounded-lg border
              border-slate-300
              bg-white px-4 py-2
              text-sm font-semibold
              text-slate-700
              hover:bg-slate-50
            "
          >
            Close
          </button>
            {goodsReceipt ? (
              <DocumentActions
                documentType="GOODS_RECEIPT"
                documentId={goodsReceipt.id}
                documentNumber={
                  goodsReceipt.grn_number
                }
              />
            ) : null}
        </footer>
      </div>
    </div>
  );
}

interface DetailCardProps {
  label: string;
  value: string;
  helper?: string | null;
}

function DetailCard({
  label,
  value,
  helper,
}: DetailCardProps) {
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

      {helper
        ? (
          <p
            className="
              mt-1 text-xs
              text-slate-500
            "
          >
            {helper}
          </p>
        )
        : null}
    </div>
  );
}
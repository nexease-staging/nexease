"use client";
import { FormSheet } from "@/components/form/form-sheet";
import SearchSelect from "@/components/search-select";


import {
  useMemo,
  useState,
} from "react";

import {
  PackageCheck,
} from "lucide-react";

import {
  useCreateGoodsReceipt,
} from "@/features/goods-receipts/hooks";

import {
  usePurchaseOrder,
  usePurchaseOrderList,
} from "@/features/purchase-orders/hooks";

import type {
  PurchaseOrderItem,
  PurchaseOrderSummary,
} from "@/features/purchase-orders/types";

import {
  useWarehouseList,
} from "@/features/warehouses/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

interface GoodsReceiptDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (
    goodsReceiptId: string,
  ) => void;
}

interface ReceiptQuantity {
  product_id: string;
  quantity_received: string;
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
    "Unable to create the goods receipt."
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

export default function GoodsReceiptDialog({
  open,
  onClose,
  onCreated,
}: GoodsReceiptDialogProps) {
  const [
    purchaseOrderId,
    setPurchaseOrderId,
  ] = useState("");

  const [
    warehouseId,
    setWarehouseId,
  ] = useState("");

  const [
    quantities,
    setQuantities,
  ] = useState<
    ReceiptQuantity[]
  >([]);

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

  const confirmedQuery =
    usePurchaseOrderList({
      page: 1,
      page_size: 100,
      status: "CONFIRMED",
      sort: "-created_at",
    });

  const partiallyReceivedQuery =
    usePurchaseOrderList({
      page: 1,
      page_size: 100,
      status:
        "PARTIALLY_RECEIVED",
      sort: "-created_at",
    });

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

  const warehouseQuery =
    useWarehouseList({
      page: 1,
      page_size: 100,
      is_active: true,
      sort: "name",
    });

  const createMutation =
    useCreateGoodsReceipt();

  const eligiblePurchaseOrders =
    useMemo(() => {
      const purchaseOrders = [
        ...(
          confirmedQuery
            .data
            ?.purchase_orders
          ??
          []
        ),
        ...(
          partiallyReceivedQuery
            .data
            ?.purchase_orders
          ??
          []
        ),
      ];

      const uniquePurchaseOrders =
        new Map<
          string,
          PurchaseOrderSummary
        >();

      for (
        const purchaseOrder
        of purchaseOrders
      ) {
        uniquePurchaseOrders.set(
          purchaseOrder.id,
          purchaseOrder,
        );
      }

      return Array.from(
        uniquePurchaseOrders.values(),
      );
    }, [
      confirmedQuery.data,
      partiallyReceivedQuery.data,
    ]);

  const purchaseOrder =
    purchaseOrderQuery.data;

      function resetDialog():
    void {
    setPurchaseOrderId("");
    setWarehouseId("");
    setQuantities([]);
    setNotes("");
    setFormError(null);
  }

  function closeDialog():
    void {
    if (
      createMutation.isPending
    ) {
      return;
    }

    resetDialog();
    onClose();
  }

  if (!open) {
    return null;
  }

  const listLoading =
    confirmedQuery.isLoading
    ||
    partiallyReceivedQuery
      .isLoading;

  const listError =
    confirmedQuery.error
    ??
    partiallyReceivedQuery.error;

  function getQuantity(
    productId: string,
  ): string {
    return (
      quantities.find(
        (item) =>
          item.product_id
          ===
          productId,
      )
      ?.quantity_received
      ??
      ""
    );
  }

  function updateQuantity(
    productId: string,
    value: string,
  ): void {
    setQuantities(
      (current) => {
        const existing =
          current.some(
            (item) =>
              item.product_id
              ===
              productId,
          );

        if (!existing) {
          return [
            ...current,
            {
              product_id:
                productId,
              quantity_received:
                value,
            },
          ];
        }

        return current.map(
          (item) =>
            item.product_id
            ===
            productId
              ? {
                  ...item,
                  quantity_received:
                    value,
                }
              : item,
        );
      },
    );

    setFormError(null);
  }

  function receiveRemaining(
    item: PurchaseOrderItem,
  ): void {
    updateQuantity(
      item.product.id,
      item.remaining_quantity,
    );
  }

  async function submit():
    Promise<void> {
    setFormError(null);

    if (!purchaseOrderId) {
      setFormError(
        "Select a purchase order.",
      );
      return;
    }

    if (!warehouseId) {
      setFormError(
        "Select a receiving warehouse.",
      );
      return;
    }

    const receiptItems =
      quantities
        .filter((item) => {
          const quantity =
            Number(
              item.quantity_received,
            );

          return (
            Number.isFinite(
              quantity,
            )
            &&
            quantity > 0
          );
        })
        .map((item) => ({
          product_id:
            item.product_id,
          quantity_received:
            item.quantity_received,
        }));

    if (
      receiptItems.length === 0
    ) {
      setFormError(
        (
          "Enter a received quantity "
          +
          "for at least one item."
        ),
      );
      return;
    }

    if (purchaseOrder) {
      for (
        const receiptItem
        of receiptItems
      ) {
        const purchaseOrderItem =
          purchaseOrder.items.find(
            (item) =>
              item.product.id
              ===
              receiptItem.product_id,
          );

        if (!purchaseOrderItem) {
          continue;
        }

        const received =
          Number(
            receiptItem
              .quantity_received,
          );

        const remaining =
          Number(
            purchaseOrderItem
              .remaining_quantity,
          );

        if (
          !Number.isFinite(received)
          ||
          received <= 0
        ) {
          setFormError(
            (
              "Received quantities must "
              +
              "be greater than zero."
            ),
          );
          return;
        }

        if (
          Number.isFinite(remaining)
          &&
          received > remaining
        ) {
          setFormError(
            (
              `Received quantity for `
              +
              `${
                purchaseOrderItem
                  .product.name
              } cannot exceed `
              +
              `${purchaseOrderItem
                .remaining_quantity}.`
            ),
          );
          return;
        }
      }
    }

    try {
      const goodsReceipt =
        await createMutation
          .mutateAsync({
            purchase_order_id:
              purchaseOrderId,
            warehouse_id:
              warehouseId,
            items:
              receiptItems,
            notes:
              notes.trim()
              ||
              undefined,
          });

      resetDialog();

      if (onCreated) {
        onCreated(
          goodsReceipt.id,
        );
      } else {
        onClose();
      }
    } catch (error) {
      setFormError(
        getErrorMessage(error),
      );
    }
  }

  return (
    <FormSheet title={"Receive goods"} subtitle={"Record stock received against a confirmed purchase order."} onClose={closeDialog} busy={createMutation.isPending} size="xl" closeLabel="Close dialog">
      

        <div className="flex flex-col gap-4">
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
                  grid gap-4 sm:grid-cols-2
                "
              >
                <label
                  className="
                    block text-sm
                    font-semibold
                    text-slate-800
                  "
                >
                  Purchase order

                  <SearchSelect
                    value={
                      purchaseOrderId
                    }
                    disabled={
                      listLoading
                      ||
                      createMutation
                        .isPending
                    }
                    onChange={(event) => {
                    setPurchaseOrderId(
                        event.currentTarget
                        .value,
                    );

                    setQuantities([]);
                    setFormError(null);
                    }}
                    className="
                      mt-2 h-11 w-full
                      rounded-lg border
                      border-slate-300
                      bg-white px-3
                      text-sm text-slate-950
                      outline-none
                      focus:border-blue-500
                      focus:ring-2
                      focus:ring-blue-100
                      disabled:bg-slate-100
                    "
                  >
                    <option value="">
                      {listLoading
                        ? (
                          "Loading purchase "
                          +
                          "orders…"
                        )
                        : (
                          "Select purchase "
                          +
                          "order"
                        )}
                    </option>

                    {eligiblePurchaseOrders
                      .map(
                        (
                          purchaseOrderOption,
                        ) => (
                          <option
                            key={
                              purchaseOrderOption
                                .id
                            }
                            value={
                              purchaseOrderOption
                                .id
                            }
                          >
                            {
                              purchaseOrderOption
                                .po_number
                            }
                            {" — "}
                            {
                              purchaseOrderOption
                                .supplier.name
                            }
                            {" — "}
                            {
                              purchaseOrderOption
                                .status
                            }
                          </option>
                        ),
                      )}
                  </SearchSelect>
                </label>

                <label
                  className="
                    block text-sm
                    font-semibold
                    text-slate-800
                  "
                >
                  Receiving warehouse

                  <SearchSelect
                    value={warehouseId}
                    disabled={
                      warehouseQuery
                        .isLoading
                      ||
                      createMutation
                        .isPending
                    }
                    onChange={(event) => {
                      setWarehouseId(
                        event.currentTarget
                          .value,
                      );

                      setFormError(null);
                    }}
                    className="
                      mt-2 h-11 w-full
                      rounded-lg border
                      border-slate-300
                      bg-white px-3
                      text-sm text-slate-950
                      outline-none
                      focus:border-blue-500
                      focus:ring-2
                      focus:ring-blue-100
                      disabled:bg-slate-100
                    "
                  >
                    <option value="">
                      Select warehouse
                    </option>

                    {warehouseQuery
                      .data
                      ?.warehouses
                      .map(
                        (warehouse) => (
                          <option
                            key={
                              warehouse.id
                            }
                            value={
                              warehouse.id
                            }
                          >
                            {warehouse.code}
                            {" — "}
                            {warehouse.name}
                          </option>
                        ),
                      )}
                  </SearchSelect>
                </label>
              </div>

              {listError
                ? (
                  <p
                    className="
                      mt-3 text-sm
                      text-red-700
                    "
                  >
                    {getErrorMessage(
                      listError,
                    )}
                  </p>
                )
                : null}

              {warehouseQuery.isError
                ? (
                  <p
                    className="
                      mt-3 text-sm
                      text-red-700
                    "
                  >
                    {getErrorMessage(
                      warehouseQuery
                        .error,
                    )}
                  </p>
                )
                : null}
            </section>

            {purchaseOrderQuery
              .isLoading
              ? (
                <section
                  className="
                    rounded-xl border
                    border-slate-200
                    bg-white px-5 py-10
                    text-center text-sm
                    text-slate-600
                  "
                >
                  Loading purchase-order
                  items…
                </section>
              )
              : null}

            {purchaseOrderQuery.isError
              ? (
                <section
                  className="
                    rounded-xl border
                    border-red-200
                    bg-red-50 px-4 py-3
                    text-sm text-red-700
                  "
                >
                  {getErrorMessage(
                    purchaseOrderQuery
                      .error,
                  )}
                </section>
              )
              : null}

            {purchaseOrder
              ? (
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
                    <div
                      className="
                        flex flex-col gap-1
                        sm:flex-row
                        sm:items-center
                        sm:justify-between
                      "
                    >
                      <div>
                        <h3
                          className="
                            font-bold
                            text-slate-950
                          "
                        >
                          {
                            purchaseOrder
                              .po_number
                          }
                        </h3>

                        <p
                          className="
                            mt-1 text-sm
                            text-slate-600
                          "
                        >
                          {
                            purchaseOrder
                              .supplier.name
                          }
                        </p>
                      </div>

                      <span
                        className="
                          mt-2 w-fit
                          rounded-full
                          bg-blue-100
                          px-2.5 py-1
                          text-xs font-semibold
                          text-blue-700
                          sm:mt-0
                        "
                      >
                        {
                          purchaseOrder
                            .status
                        }
                      </span>
                    </div>
                  </div>

                  <div
                    className="
                      divide-y
                      divide-slate-200
                    "
                  >
                    {purchaseOrder.items.map(
                      (item) => (
                        <div
                          key={
                            item.product.id
                          }
                          className="
                            grid gap-4 p-4
                            sm:grid-cols-[minmax(0,1fr)_140px]
                            sm:items-end
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
                              {" · "}
                              Ordered:{" "}
                              {formatQuantity(
                                item.quantity,
                              )}
                              {" · "}
                              Received:{" "}
                              {formatQuantity(
                                item
                                  .received_quantity,
                              )}
                            </p>

                            <p
                              className="
                                mt-2 text-sm
                                font-medium
                                text-emerald-700
                              "
                            >
                              Remaining:{" "}
                              {formatQuantity(
                                item
                                  .remaining_quantity,
                              )}{" "}
                              {
                                item
                                  .product.unit
                              }
                            </p>
                          </div>

                          <div>
                            <label
                              className="
                                block text-xs
                                font-semibold
                                text-slate-700
                              "
                            >
                              Receive now

                              <input
                                type="number"
                                min="0"
                                step="0.01"
                                max={
                                  item
                                    .remaining_quantity
                                }
                                value={
                                  getQuantity(
                                    item
                                      .product.id,
                                  )
                                }
                                disabled={
                                  Number(
                                    item
                                      .remaining_quantity,
                                  )
                                  <=
                                  0
                                  ||
                                  createMutation
                                    .isPending
                                }
                                onChange={(
                                  event,
                                ) => {
                                  updateQuantity(
                                    item
                                      .product.id,
                                    event
                                      .currentTarget
                                      .value,
                                  );
                                }}
                                className="
                                  mt-2 h-10
                                  w-full rounded-lg
                                  border
                                  border-slate-300
                                  bg-white px-3
                                  text-sm
                                  text-slate-950
                                  outline-none
                                  focus:border-blue-500
                                  focus:ring-2
                                  focus:ring-blue-100
                                  disabled:bg-slate-100
                                "
                              />
                            </label>

                            <button
                              type="button"
                              disabled={
                                Number(
                                  item
                                    .remaining_quantity,
                                )
                                <=
                                0
                                ||
                                createMutation
                                  .isPending
                              }
                              onClick={() => {
                                receiveRemaining(
                                  item,
                                );
                              }}
                              className="
                                mt-2 text-xs
                                font-semibold
                                text-blue-700
                                hover:underline
                                disabled:text-slate-400
                                disabled:no-underline
                              "
                            >
                              Receive remaining
                            </button>
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                </section>
              )
              : null}

            <label
              className="
                block rounded-xl border
                border-slate-200 bg-white
                p-4 text-sm font-semibold
                text-slate-800 shadow-sm
                sm:p-5
              "
            >
              Notes

              <textarea
                rows={4}
                maxLength={1000}
                value={notes}
                disabled={
                  createMutation.isPending
                }
                placeholder="
                  Condition, delivery reference
                  or receiving notes
                "
                onChange={(event) => {
                  setNotes(
                    event.currentTarget
                      .value,
                  );
                }}
                className="
                  mt-2 w-full rounded-lg
                  border border-slate-300
                  bg-white px-3 py-2
                  text-sm text-slate-950
                  outline-none
                  placeholder:text-slate-400
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                  disabled:bg-slate-100
                "
              />
            </label>

            {formError
              ? (
                <div
                  className="
                    rounded-xl border
                    border-red-200 bg-red-50
                    px-4 py-3 text-sm
                    text-red-700
                  "
                >
                  {formError}
                </div>
              )
              : null}
          </div>
        </div>

        <footer className="nxf-actions"><span /><div className="nxf-buttons">
          <button
            type="button"
            disabled={
              createMutation.isPending
            }
            onClick={closeDialog}
            className="nx-button nx-secondary nxf-secondary-sm"
          >
            Cancel
          </button>

          <button
            type="button"
            disabled={
              createMutation.isPending
              ||
              !purchaseOrder
            }
            onClick={() => {
              void submit();
            }}
            className="nx-button"
          >
            <PackageCheck size={17} />

            {createMutation.isPending
              ? "Receiving…"
              : "Create receipt"}
          </button>
        </div></footer>
      </FormSheet>
  );
}

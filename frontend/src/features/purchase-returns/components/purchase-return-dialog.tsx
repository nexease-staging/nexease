"use client";
import SearchSelect from "@/components/search-select";


import {
  useMemo,
  useState,
} from "react";

import {
  RotateCcw,
  X,
} from "lucide-react";

import {
  usePurchaseOrder,
  usePurchaseOrderList,
} from "@/features/purchase-orders/hooks";

import type {
  PurchaseOrderItem,
  PurchaseOrderSummary,
} from "@/features/purchase-orders/types";

import {
  useCreatePurchaseReturn,
} from "@/features/purchase-returns/hooks";

import {
  useVendorBillList,
} from "@/features/vendor-bills/hooks";

import {
  useWarehouseList,
} from "@/features/warehouses/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

interface PurchaseReturnDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (
    purchaseReturnId: string,
  ) => void;
}

interface ReturnLineValue {
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

  return (
    "Unable to create the purchase return."
  );
}

function formatQuantity(
  value: string,
): string {
  const quantity = Number(value);

  if (
    Number.isNaN(quantity)
  ) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      maximumFractionDigits: 4,
    },
  ).format(
    quantity,
  );
}

export default function PurchaseReturnDialog({
  open,
  onClose,
  onCreated,
}: PurchaseReturnDialogProps) {
  const [
    purchaseOrderId,
    setPurchaseOrderId,
  ] = useState("");

  const [
    vendorBillId,
    setVendorBillId,
  ] = useState("");

  const [
    warehouseId,
    setWarehouseId,
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
  ] = useState<ReturnLineValue[]>(
    [],
  );

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

  const partiallyReceivedQuery =
    usePurchaseOrderList({
      page: 1,
      page_size: 100,
      status:
        "PARTIALLY_RECEIVED",
      sort: "-created_at",
    });

  const receivedQuery =
    usePurchaseOrderList({
      page: 1,
      page_size: 100,
      status: "RECEIVED",
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

  const vendorBillQuery =
    useVendorBillList({
      page: 1,
      page_size: 100,
      purchase_order_id:
        purchaseOrderId
        ||
        undefined,
      sort: "-created_at",
    });

  const warehouseQuery =
    useWarehouseList({
      page: 1,
      page_size: 100,
      is_active: true,
      sort: "name",
    });

  const createMutation =
    useCreatePurchaseReturn();

  const eligiblePurchaseOrders =
    useMemo(() => {
      const purchaseOrders = [
        ...(
          partiallyReceivedQuery
            .data
            ?.purchase_orders
          ??
          []
        ),
        ...(
          receivedQuery
            .data
            ?.purchase_orders
          ??
          []
        ),
      ];

      const unique =
        new Map<
          string,
          PurchaseOrderSummary
        >();

      for (
        const purchaseOrder
        of purchaseOrders
      ) {
        unique.set(
          purchaseOrder.id,
          purchaseOrder,
        );
      }

      return Array.from(
        unique.values(),
      );
    }, [
      partiallyReceivedQuery.data,
      receivedQuery.data,
    ]);

  const eligibleVendorBills =
    useMemo(
      () =>
        (
          vendorBillQuery
            .data
            ?.vendor_bills
          ??
          []
        ).filter(
          (bill) =>
            bill.purchase_order?.id
            ===
            purchaseOrderId
            &&
            bill.status
            !==
            "DRAFT"
            &&
            bill.status
            !==
            "CANCELLED",
        ),
      [
        purchaseOrderId,
        vendorBillQuery.data,
      ],
    );

  const purchaseOrder =
    purchaseOrderQuery.data;

  function resetDialog(): void {
    setPurchaseOrderId("");
    setVendorBillId("");
    setWarehouseId("");
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

  function selectPurchaseOrder(
    value: string,
  ): void {
    setPurchaseOrderId(
      value,
    );

    setVendorBillId("");
    setLines([]);
    setFormError(null);
  }

  function getLine(
    productId: string,
  ): ReturnLineValue {
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
    changes: Partial<
      ReturnLineValue
    >,
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

  function returnReceivedQuantity(
    item: PurchaseOrderItem,
  ): void {
    updateLine(
      item.product.id,
      {
        quantity:
          item.received_quantity,
      },
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

    if (!vendorBillId) {
      setFormError(
        "Select a vendor bill.",
      );
      return;
    }

    if (!warehouseId) {
      setFormError(
        "Select the warehouse holding the returned stock.",
      );
      return;
    }

    const selectedItems =
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
      const purchaseOrderItem =
        purchaseOrder
          ?.items
          .find(
            (item) =>
              item.product.id
              ===
              selectedItem.product_id,
          );

      if (!purchaseOrderItem) {
        setFormError(
          "A selected product is no longer available.",
        );
        return;
      }

      if (
        Number(
          selectedItem.quantity,
        )
        >
        Number(
          purchaseOrderItem
            .received_quantity,
        )
      ) {
        setFormError(
          (
            `Return quantity for ${
              purchaseOrderItem
                .product.name
            } exceeds its received quantity.`
          ),
        );
        return;
      }
    }

    try {
      const created =
        await createMutation
          .mutateAsync({
            purchase_order_id:
              purchaseOrderId,
            vendor_bill_id:
              vendorBillId,
            warehouse_id:
              warehouseId,
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

  const listLoading =
    partiallyReceivedQuery
      .isLoading
    ||
    receivedQuery.isLoading;

  const listError =
    partiallyReceivedQuery.error
    ??
    receivedQuery.error;

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
          "purchase-return-title"
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
              id="purchase-return-title"
              className="
                text-lg font-bold
                text-slate-950
              "
            >
              Create purchase return
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-500
              "
            >
              Return received inventory to a supplier.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close dialog"
            disabled={
              createMutation.isPending
            }
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
          <div
            className="
              space-y-5
            "
          >
            <section
              className="
                grid gap-4 rounded-xl
                border border-slate-200
                bg-white p-4 shadow-sm
                sm:grid-cols-2 sm:p-5
              "
            >
              <label
                className="
                  text-sm font-semibold
                  text-slate-800
                "
              >
                Purchase order

                <SearchSelect
                  value={purchaseOrderId}
                  disabled={
                    listLoading
                    ||
                    createMutation
                      .isPending
                  }
                  onChange={(event) => {
                    selectPurchaseOrder(
                      event.currentTarget
                        .value,
                    );
                  }}
                  className="
                    mt-2 h-11 w-full
                    rounded-lg border
                    border-slate-300
                    bg-white px-3 text-sm
                    text-slate-950
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                  "
                >
                  <option value="">
                    Select purchase order
                  </option>

                  {eligiblePurchaseOrders
                    .map(
                      (purchaseOrder) => (
                        <option
                          key={
                            purchaseOrder.id
                          }
                          value={
                            purchaseOrder.id
                          }
                        >
                          {
                            purchaseOrder
                              .po_number
                          }
                          {" - "}
                          {
                            purchaseOrder
                              .supplier.name
                          }
                        </option>
                      ),
                    )}
                </SearchSelect>
              </label>

              <label
                className="
                  text-sm font-semibold
                  text-slate-800
                "
              >
                Vendor bill

                <SearchSelect
                  value={vendorBillId}
                  disabled={
                    !purchaseOrderId
                    ||
                    vendorBillQuery
                      .isLoading
                    ||
                    createMutation
                      .isPending
                  }
                  onChange={(event) => {
                    setVendorBillId(
                      event.currentTarget
                        .value,
                    );
                    setFormError(null);
                  }}
                  className="
                    mt-2 h-11 w-full
                    rounded-lg border
                    border-slate-300
                    bg-white px-3 text-sm
                    text-slate-950
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                    disabled:bg-slate-100
                  "
                >
                  <option value="">
                    Select vendor bill
                  </option>

                  {eligibleVendorBills.map(
                    (bill) => (
                      <option
                        key={bill.id}
                        value={bill.id}
                      >
                        {bill.bill_number}
                        {" - "}
                        {bill.status}
                      </option>
                    ),
                  )}
                </SearchSelect>
              </label>

              <label
                className="
                  text-sm font-semibold
                  text-slate-800
                "
              >
                Warehouse

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
                    bg-white px-3 text-sm
                    text-slate-950
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                  "
                >
                  <option value="">
                    Select warehouse
                  </option>

                  {(
                    warehouseQuery
                      .data
                      ?.warehouses
                    ??
                    []
                  ).map(
                    (warehouse) => (
                      <option
                        key={warehouse.id}
                        value={warehouse.id}
                      >
                        {warehouse.code}
                        {" - "}
                        {warehouse.name}
                      </option>
                    ),
                  )}
                </SearchSelect>
              </label>

              <label
                className="
                  text-sm font-semibold
                  text-slate-800
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
                      event.currentTarget
                        .value,
                    );
                  }}
                  className="
                    mt-2 h-11 w-full
                    rounded-lg border
                    border-slate-300
                    bg-white px-3 text-sm
                    text-slate-950
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                  "
                />
              </label>
            </section>

            {listError
              ? (
                <div
                  className="
                    rounded-xl border
                    border-red-200
                    bg-red-50 px-4 py-3
                    text-sm text-red-700
                  "
                >
                  {getErrorMessage(
                    listError,
                  )}
                </div>
              )
              : null}

            {purchaseOrderQuery.error
              ? (
                <div
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
                </div>
              )
              : null}

            {purchaseOrder
              ? (
                <section
                  className="
                    rounded-xl border
                    border-slate-200
                    bg-white p-4 shadow-sm
                    sm:p-5
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
                        Items to return
                      </h3>

                      <p
                        className="
                          mt-1 text-sm
                          text-slate-500
                        "
                      >
                        Enter quantities from inventory currently held in the selected warehouse.
                      </p>
                    </div>
                  </div>

                  <div
                    className="
                      mt-4 space-y-3
                    "
                  >
                    {purchaseOrder.items.map(
                      (item) => {
                        const line =
                          getLine(
                            item.product.id,
                          );

                        return (
                          <div
                            key={
                              item.product.id
                            }
                            className="
                              grid gap-4
                              rounded-xl border
                              border-slate-200
                              bg-slate-50 p-4
                              md:grid-cols-[1fr_160px_1fr]
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
                                {item.product.sku}
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

                              <button
                                type="button"
                                disabled={
                                  Number(
                                    item
                                      .received_quantity,
                                  )
                                  <=
                                  0
                                  ||
                                  createMutation
                                    .isPending
                                }
                                onClick={() => {
                                  returnReceivedQuantity(
                                    item,
                                  );
                                }}
                                className="
                                  mt-2 text-xs
                                  font-semibold
                                  text-blue-700
                                  hover:underline
                                  disabled:text-slate-400
                                "
                              >
                                Use received quantity
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
                                max={
                                  item
                                    .received_quantity
                                }
                                value={
                                  line.quantity
                                }
                                disabled={
                                  Number(
                                    item
                                      .received_quantity,
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
                                  updateLine(
                                    item
                                      .product.id,
                                    {
                                      quantity:
                                        event
                                          .currentTarget
                                          .value,
                                    },
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
                                value={
                                  line.reason
                                }
                                disabled={
                                  createMutation
                                    .isPending
                                }
                                placeholder="Damaged, excess or incorrect item"
                                onChange={(
                                  event,
                                ) => {
                                  updateLine(
                                    item
                                      .product.id,
                                    {
                                      reason:
                                        event
                                          .currentTarget
                                          .value,
                                    },
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
                                "
                              />
                            </label>
                          </div>
                        );
                      },
                    )}
                  </div>
                </section>
              )
              : null}

            <section
              className="
                grid gap-4 rounded-xl
                border border-slate-200
                bg-white p-4 shadow-sm
                sm:grid-cols-2 sm:p-5
              "
            >
              <label
                className="
                  text-sm font-semibold
                  text-slate-800
                "
              >
                Overall reason

                <textarea
                  rows={4}
                  maxLength={500}
                  value={reason}
                  disabled={
                    createMutation.isPending
                  }
                  onChange={(event) => {
                    setReason(
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
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                  "
                />
              </label>

              <label
                className="
                  text-sm font-semibold
                  text-slate-800
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
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                  "
                />
              </label>
            </section>

            {formError
              ? (
                <div
                  className="
                    rounded-xl border
                    border-red-200
                    bg-red-50 px-4 py-3
                    text-sm text-red-700
                  "
                >
                  {formError}
                </div>
              )
              : null}
          </div>
        </div>

        <footer
          className="
            flex items-center
            justify-end gap-2
            border-t border-slate-200
            bg-white px-4 py-4
            sm:px-6
          "
        >
          <button
            type="button"
            disabled={
              createMutation.isPending
            }
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
            className="
              inline-flex items-center
              gap-2 rounded-lg
              bg-blue-600 px-4 py-2
              text-sm font-semibold
              text-white
              hover:bg-blue-700
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >
            <RotateCcw size={17} />

            {createMutation.isPending
              ? "Creating…"
              : "Create return"}
          </button>
        </footer>
      </div>
    </div>
  );
}
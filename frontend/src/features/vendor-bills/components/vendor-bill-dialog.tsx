"use client";
import { FormSheet } from "@/components/form/form-sheet";
import SearchSelect from "@/components/search-select";


import {
  useState,
} from "react";

import {
  FilePlus2,
} from "lucide-react";

import {
  usePurchaseOrderList,
} from "@/features/purchase-orders/hooks";

import {
  useCreateVendorBill,
} from "@/features/vendor-bills/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

interface VendorBillDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (
    billId: string,
  ) => void;
}

function todayValue(): string {
  const now = new Date();

  const offset =
    now.getTimezoneOffset()
    *
    60_000;

  return new Date(
    now.getTime() - offset,
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
    "Unable to create the vendor bill."
  );
}

export default function VendorBillDialog({
  open,
  onClose,
  onCreated,
}: VendorBillDialogProps) {
  const [
    purchaseOrderId,
    setPurchaseOrderId,
  ] = useState("");

  const [
    supplierInvoiceNumber,
    setSupplierInvoiceNumber,
  ] = useState("");

  const [
    billDate,
    setBillDate,
  ] = useState(
    todayValue(),
  );

  const [
    dueDate,
    setDueDate,
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

  const purchaseOrderQuery =
    usePurchaseOrderList({
      page: 1,
      page_size: 100,
      status: "RECEIVED",
      sort: "-created_at",
    });

  const createMutation =
    useCreateVendorBill();

  if (!open) {
    return null;
  }

  function resetDialog():
    void {
    setPurchaseOrderId("");
    setSupplierInvoiceNumber("");
    setBillDate(
      todayValue(),
    );
    setDueDate("");
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

  async function submit():
    Promise<void> {
    setFormError(null);

    if (!purchaseOrderId) {
      setFormError(
        "Select a received purchase order.",
      );
      return;
    }

    if (
      billDate
      &&
      dueDate
      &&
      dueDate < billDate
    ) {
      setFormError(
        (
          "Due date cannot be before "
          +
          "the bill date."
        ),
      );
      return;
    }

    try {
      const vendorBill =
        await createMutation
          .mutateAsync({
            purchase_order_id:
              purchaseOrderId,
            supplier_invoice_number:
              supplierInvoiceNumber
                .trim()
              ||
              undefined,
            bill_date:
              billDate
              ||
              undefined,
            due_date:
              dueDate
              ||
              undefined,
            notes:
              notes.trim()
              ||
              undefined,
          });

      resetDialog();

      if (onCreated) {
        onCreated(
          vendorBill.id,
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
    <FormSheet title={"New purchase bill"} subtitle={"Creates a draft bill from a fully received purchase order."} onClose={closeDialog} busy={createMutation.isPending} size="md" closeLabel="Close dialog">
      

        <div className="flex flex-col gap-4">
          <div
            className="
              space-y-5 rounded-xl
              border border-slate-200
              bg-white p-4 shadow-sm
              sm:p-5
            "
          >
            <label
              className="
                block text-sm
                font-semibold
                text-slate-800
              "
            >
              Received purchase order

              <SearchSelect
                value={purchaseOrderId}
                disabled={
                  purchaseOrderQuery
                    .isLoading
                  ||
                  createMutation
                    .isPending
                }
                onChange={(event) => {
                  setPurchaseOrderId(
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
                  {purchaseOrderQuery
                    .isLoading
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

                {purchaseOrderQuery
                  .data
                  ?.purchase_orders
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
                        {" — "}
                        {
                          purchaseOrder
                            .supplier.name
                        }
                        {" — ₹"}
                        {
                          purchaseOrder
                            .total_amount
                        }
                      </option>
                    ),
                  )}
              </SearchSelect>
            </label>

            {purchaseOrderQuery.isError
              ? (
                <p
                  className="
                    text-sm text-red-700
                  "
                >
                  {getErrorMessage(
                    purchaseOrderQuery
                      .error,
                  )}
                </p>
              )
              : null}

            <label
              className="
                block text-sm
                font-semibold
                text-slate-800
              "
            >
              Supplier invoice number

              <input
                type="text"
                maxLength={100}
                value={
                  supplierInvoiceNumber
                }
                disabled={
                  createMutation.isPending
                }
                placeholder="
                  Supplier invoice reference
                "
                onChange={(event) => {
                  setSupplierInvoiceNumber(
                    event.currentTarget
                      .value,
                  );
                }}
                className="
                  mt-2 h-11 w-full
                  rounded-lg border
                  border-slate-300
                  bg-white px-3
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
                Bill date

                <input
                  type="date"
                  value={billDate}
                  disabled={
                    createMutation
                      .isPending
                  }
                  onChange={(event) => {
                    setBillDate(
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
                />
              </label>

              <label
                className="
                  block text-sm
                  font-semibold
                  text-slate-800
                "
              >
                Due date

                <input
                  type="date"
                  value={dueDate}
                  min={
                    billDate
                    ||
                    undefined
                  }
                  disabled={
                    createMutation
                      .isPending
                  }
                  onChange={(event) => {
                    setDueDate(
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
                />
              </label>
            </div>

            <label
              className="
                block text-sm
                font-semibold
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
                placeholder="
                  Bill notes or internal reference
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
                    rounded-lg border
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
              !purchaseOrderId
            }
            onClick={() => {
              void submit();
            }}
            className="nx-button"
          >
            <FilePlus2 size={17} />

            {createMutation.isPending
              ? "Creating…"
              : "Create bill"}
          </button>
        </div></footer>
      </FormSheet>
  );
}

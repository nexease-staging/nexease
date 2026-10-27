"use client";
import SearchSelect from "@/components/search-select";


import {
  useEffect,
} from "react";

import {
  zodResolver,
} from "@hookform/resolvers/zod";

import {
  FilePlus2,
  X,
} from "lucide-react";

import {
  useForm,
} from "react-hook-form";

import {
  z,
} from "zod";

import {
  useCreateInvoice,
} from "@/features/invoices/hooks";

import {
  useSalesOrderList,
} from "@/features/sales-orders/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

const invoiceSchema = z.object({
  sales_order_id: z
    .string()
    .min(
      1,
      "Sales order is required.",
    ),

  invoice_date: z.string(),

  due_date: z.string(),

  notes: z
    .string()
    .trim()
    .max(
      1000,
      "Notes cannot exceed 1000 characters.",
    ),
});

type InvoiceFormValues =
  z.infer<typeof invoiceSchema>;

interface InvoiceDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (
    invoiceId: string,
  ) => void;
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

function emptyValues():
  InvoiceFormValues {
  return {
    sales_order_id: "",
    invoice_date:
      todayValue(),
    due_date: "",
    notes: "",
  };
}

function firstFieldMessage(
  value: unknown,
): string | null {
  if (
    Array.isArray(value)
    &&
    typeof value[0] === "string"
  ) {
    return value[0];
  }

  if (typeof value === "string") {
    return value;
  }

  return null;
}

export default function InvoiceDialog({
  open,
  onClose,
  onCreated,
}: InvoiceDialogProps) {
  const createMutation =
    useCreateInvoice();

  const salesOrderQuery =
    useSalesOrderList({
      page: 1,
      page_size: 100,
      status: "FULFILLED",
      sort: "-created_at",
    });

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<InvoiceFormValues>({
    resolver:
      zodResolver(
        invoiceSchema,
      ),

    defaultValues:
      emptyValues(),
  });

  useEffect(() => {
    if (open) {
      reset(
        emptyValues(),
      );
    }
  }, [
    open,
    reset,
  ]);

  if (!open) {
    return null;
  }

  const salesOrders =
    salesOrderQuery.data
      ?.sales_orders
    ??
    [];

  async function submit(
    values: InvoiceFormValues,
  ): Promise<void> {
    try {
      const invoice =
        await createMutation
          .mutateAsync({
            sales_order_id:
              values.sales_order_id,

            invoice_date:
              values.invoice_date
              ||
              undefined,

            due_date:
              values.due_date
              ||
              undefined,

            notes:
              values.notes.trim()
              ||
              undefined,
          });

      onClose();

      onCreated?.(
        invoice.id,
      );

    } catch (error) {
      if (
        error
        instanceof
        APIRequestError
      ) {
        const details =
          error.details
          ??
          {};

        const fields: Array<
          keyof InvoiceFormValues
        > = [
          "sales_order_id",
          "invoice_date",
          "due_date",
          "notes",
        ];

        let fieldErrorFound =
          false;

        for (const field of fields) {
          const message =
            firstFieldMessage(
              details[field],
            );

          if (message) {
            setError(
              field,
              {
                type: "server",
                message,
              },
            );

            fieldErrorFound =
              true;
          }
        }

        if (!fieldErrorFound) {
          setError(
            "root",
            {
              type: "server",
              message:
                error.message,
            },
          );
        }

        return;
      }

      setError(
        "root",
        {
          type: "server",
          message:
            "Unable to create the invoice.",
        },
      );
    }
  }

  const pending =
    createMutation.isPending;

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
        aria-labelledby="invoice-dialog-title"
        className="
          w-full max-w-2xl
          overflow-hidden rounded-2xl
          border border-slate-200
          bg-white text-slate-900
          shadow-2xl
        "
      >
        <header
          className="
            flex items-start
            justify-between gap-4
            border-b border-slate-200
            px-5 py-4 sm:px-6
          "
        >
          <div>
            <h2
              id="invoice-dialog-title"
              className="
                text-lg font-semibold
                text-slate-950
              "
            >
              Create Invoice
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-600
              "
            >
              Generate an invoice from a
              fulfilled sales order.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close"
            disabled={pending}
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

        <form
          onSubmit={(event) => {
            void handleSubmit(
              submit,
            )(
              event,
            );
          }}
        >
          <div
            className="
              grid gap-5 px-5 py-5
              sm:grid-cols-2 sm:px-6
            "
          >
            <div className="sm:col-span-2">
              <label
                htmlFor="invoice-sales-order"
                className="
                  text-sm font-medium
                  text-slate-800
                "
              >
                Fulfilled sales order
              </label>

              <SearchSelect
                id="invoice-sales-order"
                disabled={
                  pending
                  ||
                  salesOrderQuery.isPending
                }
                {...register(
                  "sales_order_id",
                )}
                className="
                  mt-1.5 w-full
                  rounded-lg border
                  border-slate-300
                  bg-white px-3 py-2.5
                  text-sm text-slate-950
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                  disabled:bg-slate-100
                "
              >
                <option value="">
                  Select a sales order
                </option>

                {salesOrders.map(
                  (salesOrder) => (
                    <option
                      key={
                        salesOrder.id
                      }
                      value={
                        salesOrder.id
                      }
                    >
                      {salesOrder.so_number}
                      {" — "}
                      {salesOrder.customer.name}
                      {" — ₹"}
                      {salesOrder.total_amount}
                    </option>
                  ),
                )}
              </SearchSelect>

              {errors.sales_order_id ? (
                <p
                  className="
                    mt-1 text-sm
                    text-red-600
                  "
                >
                  {
                    errors
                      .sales_order_id
                      .message
                  }
                </p>
              ) : null}

              {salesOrderQuery.isError ? (
                <p
                  className="
                    mt-1 text-sm
                    text-red-600
                  "
                >
                  Unable to load fulfilled
                  sales orders.
                </p>
              ) : null}

              {(
                !salesOrderQuery.isPending
                &&
                !salesOrderQuery.isError
                &&
                salesOrders.length === 0
              ) ? (
                <p
                  className="
                    mt-1 text-sm
                    text-amber-700
                  "
                >
                  No fulfilled sales order
                  is currently available.
                </p>
              ) : null}
            </div>

            <div>
              <label
                htmlFor="invoice-date"
                className="
                  text-sm font-medium
                  text-slate-800
                "
              >
                Invoice date
              </label>

              <input
                id="invoice-date"
                type="date"
                disabled={pending}
                {...register(
                  "invoice_date",
                )}
                className="
                  mt-1.5 w-full
                  rounded-lg border
                  border-slate-300
                  bg-white px-3 py-2.5
                  text-sm text-slate-950
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />

              {errors.invoice_date ? (
                <p
                  className="
                    mt-1 text-sm
                    text-red-600
                  "
                >
                  {
                    errors
                      .invoice_date
                      .message
                  }
                </p>
              ) : null}
            </div>

            <div>
              <label
                htmlFor="invoice-due-date"
                className="
                  text-sm font-medium
                  text-slate-800
                "
              >
                Due date
              </label>

              <input
                id="invoice-due-date"
                type="date"
                disabled={pending}
                {...register(
                  "due_date",
                )}
                className="
                  mt-1.5 w-full
                  rounded-lg border
                  border-slate-300
                  bg-white px-3 py-2.5
                  text-sm text-slate-950
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />

              {errors.due_date ? (
                <p
                  className="
                    mt-1 text-sm
                    text-red-600
                  "
                >
                  {
                    errors
                      .due_date
                      .message
                  }
                </p>
              ) : null}
            </div>

            <div className="sm:col-span-2">
              <label
                htmlFor="invoice-notes"
                className="
                  text-sm font-medium
                  text-slate-800
                "
              >
                Notes
              </label>

              <textarea
                id="invoice-notes"
                rows={4}
                disabled={pending}
                {...register(
                  "notes",
                )}
                className="
                  mt-1.5 w-full resize-y
                  rounded-lg border
                  border-slate-300
                  bg-white px-3 py-2.5
                  text-sm text-slate-950
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
                placeholder="Optional invoice notes"
              />

              {errors.notes ? (
                <p
                  className="
                    mt-1 text-sm
                    text-red-600
                  "
                >
                  {
                    errors.notes.message
                  }
                </p>
              ) : null}
            </div>

            {errors.root ? (
              <div
                className="
                  rounded-lg border
                  border-red-200
                  bg-red-50 px-4 py-3
                  text-sm text-red-700
                  sm:col-span-2
                "
              >
                {errors.root.message}
              </div>
            ) : null}
          </div>

          <footer
            className="
              flex flex-col-reverse
              gap-3 border-t
              border-slate-200
              bg-slate-50 px-5 py-4
              sm:flex-row
              sm:justify-end sm:px-6
            "
          >
            <button
              type="button"
              disabled={pending}
              onClick={onClose}
              className="
                rounded-lg border
                border-slate-300
                bg-white px-4 py-2.5
                text-sm font-semibold
                text-slate-700
                hover:bg-slate-100
                disabled:opacity-50
              "
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={
                pending
                ||
                salesOrderQuery.isPending
                ||
                salesOrders.length === 0
              }
              className="
                inline-flex items-center
                justify-center gap-2
                rounded-lg bg-blue-600
                px-4 py-2.5
                text-sm font-semibold
                text-white
                hover:bg-blue-700
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              <FilePlus2 size={17} />

              {pending
                ? "Creating…"
                : "Create Invoice"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}
"use client";

import {
  useEffect,
} from "react";

import {
  zodResolver,
} from "@hookform/resolvers/zod";

import {
  X,
} from "lucide-react";

import {
  useForm,
} from "react-hook-form";

import {
  z,
} from "zod";

import {
  useFulfillSalesOrder,
  useSalesOrder,
} from "@/features/sales-orders/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

const fulfillmentSchema = z.object({
  notes: z
    .string()
    .trim()
    .max(
      1000,
      "Notes cannot exceed 1000 characters.",
    ),

  quantities: z.record(
    z.string(),
    z.string(),
  ),
});

type FulfillmentFormValues =
  z.infer<typeof fulfillmentSchema>;

interface SalesOrderFulfillmentDialogProps {
  open: boolean;
  salesOrderId: string | null;
  onClose: () => void;
}

const inputClassName = `
  h-10 w-full rounded-lg
  border border-slate-300
  bg-white px-3 text-sm
  text-slate-900 outline-none
  focus:border-blue-500
  focus:ring-2 focus:ring-blue-100
  disabled:opacity-50
`;

export default function SalesOrderFulfillmentDialog({
  open,
  salesOrderId,
  onClose,
}: SalesOrderFulfillmentDialogProps) {
  const salesOrderQuery =
    useSalesOrder(
      salesOrderId ?? "",
      open && Boolean(
        salesOrderId
      ),
    );

  const fulfillmentMutation =
    useFulfillSalesOrder();

  const resetFulfillmentMutation =
    fulfillmentMutation.reset;

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<FulfillmentFormValues>({
    resolver:
      zodResolver(
        fulfillmentSchema,
      ),
    defaultValues: {
      notes: "",
      quantities: {},
    },
  });

  useEffect(() => {
    if (!open) {
      return;
    }

    resetFulfillmentMutation();

    if (!salesOrderQuery.data) {
      return;
    }

    const quantities =
      Object.fromEntries(
        salesOrderQuery.data.items
          .filter(
            (item) =>
              Number(
                item.remaining_quantity
              )
              >
              0,
          )
          .map(
            (item) => [
              item.product.id,
              "",
            ],
          ),
      );

    reset({
      notes: "",
      quantities,
    });
  }, [
    open,
    reset,
    resetFulfillmentMutation,
    salesOrderQuery.data,
  ]);

  async function submit(
    values: FulfillmentFormValues,
  ): Promise<void> {
    if (
      !salesOrderId
      ||
      !salesOrderQuery.data
    ) {
      return;
    }

    const items =
      salesOrderQuery.data.items
        .filter((item) => {
          const quantity =
            Number(
              values.quantities[
                item.product.id
              ]
              ??
              ""
            );

          return (
            Number.isFinite(quantity)
            &&
            quantity > 0
          );
        })
        .map((item) => ({
          product_id:
            item.product.id,
          quantity:
            values.quantities[
              item.product.id
            ],
        }));

    if (!items.length) {
      setError(
        "root",
        {
          type: "manual",
          message: (
            "Enter a fulfilment quantity "
            +
            "for at least one item."
          ),
        },
      );

      return;
    }

    for (const item of items) {
      const orderItem =
        salesOrderQuery.data.items.find(
          (candidate) =>
            candidate.product.id
            ===
            item.product_id,
        );

      if (
        orderItem
        &&
        Number(
          item.quantity
        )
        >
        Number(
          orderItem.remaining_quantity
        )
      ) {
        setError(
          `quantities.${item.product_id}`,
          {
            type: "manual",
            message: (
              "Quantity cannot exceed "
              +
              "the remaining quantity."
            ),
          },
        );

        return;
      }
    }

    try {
      await fulfillmentMutation.mutateAsync({
        salesOrderId,
        input: {
          items,
          notes:
            values.notes,
        },
      });

      onClose();

    } catch (error) {
      if (
        error instanceof APIRequestError
        &&
        error.details
      ) {
        const message =
          (
            Array.isArray(
              error.details.items
            )
            &&
            typeof error.details.items[0]
              ===
              "string"
          )
            ? error.details.items[0]
            : error.message;

        setError(
          "root",
          {
            type: "server",
            message,
          },
        );
      }
    }
  }

  if (!open) {
    return null;
  }

  const salesOrder =
    salesOrderQuery.data;

  const remainingItems =
    salesOrder?.items.filter(
      (item) =>
        Number(
          item.remaining_quantity
        )
        >
        0,
    )
    ??
    [];

  return (
    <div
      role="presentation"
      className="
        fixed inset-0 z-[60]
        flex items-center justify-center
        bg-slate-950/50 p-4
      "
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="fulfillment-dialog-title"
        className="
          max-h-[92vh] w-full
          max-w-3xl overflow-y-auto
          rounded-2xl bg-white
          text-slate-900 shadow-2xl
        "
      >
        <div
          className="
            flex items-start justify-between
            border-b border-slate-200 p-5
          "
        >
          <div>
            <h2
              id="fulfillment-dialog-title"
              className="text-xl font-bold"
            >
              Fulfil sales order
            </h2>

            <p className="mt-1 text-sm text-slate-600">
              {salesOrder
                ? `${salesOrder.so_number} — ${salesOrder.customer.name}`
                : "Load the remaining quantities."}
            </p>
          </div>

          <button
            type="button"
            aria-label="Close"
            disabled={
              fulfillmentMutation.isPending
            }
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
              flex min-h-64 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading sales order…
          </div>
        ) : salesOrderQuery.isError ? (
          <div
            className="
              flex min-h-64 flex-col
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
        ) : (
          <form
            onSubmit={(event) => {
              void handleSubmit(
                submit
              )(event);
            }}
            className="space-y-5 p-5"
          >
            <div className="space-y-3">
              {remainingItems.map(
                (item) => (
                  <div
                    key={item.product.id}
                    className="
                      grid gap-3 rounded-xl
                      border border-slate-200
                      bg-slate-50 p-4
                      sm:grid-cols-[1fr_170px]
                    "
                  >
                    <div>
                      <p className="font-semibold">
                        {item.product.name}
                      </p>

                      <p className="text-sm text-slate-500">
                        {item.product.sku}
                        {" · "}
                        Remaining:
                        {" "}
                        {item.remaining_quantity}
                        {" "}
                        {item.product.unit}
                      </p>
                    </div>

                    <label className="space-y-1">
                      <span className="text-xs font-semibold">
                        Fulfil quantity
                      </span>

                      <input
                        {...register(
                          `quantities.${item.product.id}`
                        )}
                        type="number"
                        min="0"
                        max={
                          item.remaining_quantity
                        }
                        step="0.01"
                        disabled={
                          fulfillmentMutation
                            .isPending
                        }
                        className={inputClassName}
                      />

                      {errors.quantities?.[
                        item.product.id
                      ] ? (
                        <p className="text-xs text-red-600">
                          {
                            errors.quantities[
                              item.product.id
                            ]?.message
                          }
                        </p>
                      ) : null}
                    </label>
                  </div>
                ),
              )}
            </div>

            <label className="block space-y-1.5">
              <span className="text-sm font-semibold">
                Dispatch notes
              </span>

              <textarea
                {...register("notes")}
                rows={4}
                placeholder="Optional fulfilment notes"
                disabled={
                  fulfillmentMutation.isPending
                }
                className="
                  w-full resize-y rounded-lg
                  border border-slate-300
                  bg-white px-3 py-2
                  text-sm text-slate-900
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />
            </label>

            {errors.root?.message ? (
              <p
                className="
                  rounded-lg bg-red-50
                  px-4 py-3 text-sm
                  text-red-700
                "
              >
                {errors.root.message}
              </p>
            ) : null}

            {fulfillmentMutation.error ? (
              <p
                className="
                  rounded-lg bg-red-50
                  px-4 py-3 text-sm
                  text-red-700
                "
              >
                {
                  fulfillmentMutation
                    .error.message
                }
              </p>
            ) : null}

            <div
              className="
                flex flex-col-reverse gap-3
                border-t border-slate-200
                pt-5 sm:flex-row
                sm:justify-end
              "
            >
              <button
                type="button"
                disabled={
                  fulfillmentMutation.isPending
                }
                onClick={onClose}
                className="
                  rounded-lg border
                  border-slate-300 px-4
                  py-2 text-sm font-semibold
                  text-slate-700
                "
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={
                  fulfillmentMutation.isPending
                  ||
                  !remainingItems.length
                }
                className="
                  rounded-lg bg-emerald-600
                  px-4 py-2 text-sm
                  font-semibold text-white
                  hover:bg-emerald-700
                  disabled:opacity-50
                "
              >
                {fulfillmentMutation.isPending
                  ? "Fulfilling…"
                  : "Confirm fulfilment"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
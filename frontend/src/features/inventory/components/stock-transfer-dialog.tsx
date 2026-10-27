"use client";
import SearchSelect from "@/components/search-select";


import {
  useEffect,
} from "react";

import {
  zodResolver,
} from "@hookform/resolvers/zod";

import {
  ArrowRight,
  X,
} from "lucide-react";

import {
  useForm,
  useWatch,
} from "react-hook-form";

import {
  z,
} from "zod";

import {
  useCreateStockTransfer,
  useProductLookup,
} from "@/features/inventory/hooks";

import {
  useWarehouseList,
} from "@/features/warehouses/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

const transferSchema = z
  .object({
    product_id: z
      .string()
      .trim()
      .min(
        1,
        "Select a product.",
      ),

    source_warehouse_id: z
      .string()
      .trim()
      .min(
        1,
        "Select the source warehouse.",
      ),

    destination_warehouse_id: z
      .string()
      .trim()
      .min(
        1,
        "Select the destination warehouse.",
      ),

    quantity: z
      .string()
      .trim()
      .min(
        1,
        "Enter the transfer quantity.",
      )
      .refine(
        (value) => {
          const quantity = Number(value);

          return (
            Number.isFinite(quantity)
            &&
            quantity > 0
          );
        },
        "Quantity must be greater than zero.",
      ),

    notes: z
      .string()
      .trim()
      .max(
        1000,
        "Notes cannot exceed 1000 characters.",
      ),
  })
  .refine(
    (values) =>
      values.source_warehouse_id
      !==
      values.destination_warehouse_id,
    {
      path: [
        "destination_warehouse_id",
      ],
      message:
        "Destination must be different from the source.",
    },
  );

type TransferFormValues =
  z.infer<typeof transferSchema>;

const emptyValues: TransferFormValues = {
  product_id: "",
  source_warehouse_id: "",
  destination_warehouse_id: "",
  quantity: "",
  notes: "",
};

interface StockTransferDialogProps {
  open: boolean;
  onClose: () => void;
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

export default function StockTransferDialog({
  open,
  onClose,
}: StockTransferDialogProps) {
  const createMutation =
    useCreateStockTransfer();

  const resetCreateMutation =
    createMutation.reset;

  const productQuery =
    useProductLookup({
      page: 1,
      page_size: 100,
      is_active: true,
      sort: "name",
    });

  const warehouseQuery =
    useWarehouseList({
      page: 1,
      page_size: 100,
      is_active: true,
      sort: "name",
    });

  const {
    control,
    register,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<TransferFormValues>({
    resolver:
      zodResolver(
        transferSchema,
      ),
    defaultValues:
      emptyValues,
  });

  useEffect(() => {
    if (!open) {
      return;
    }

    reset(
      emptyValues,
    );

    resetCreateMutation();
  }, [
    open,
    reset,
    resetCreateMutation,
  ]);

  const sourceWarehouseId =
    useWatch({
      control,
      name:
        "source_warehouse_id",
    });

  async function submit(
    values: TransferFormValues,
  ): Promise<void> {
    try {
      await createMutation.mutateAsync({
        product_id:
          values.product_id,

        source_warehouse_id:
          values.source_warehouse_id,

        destination_warehouse_id:
          values.destination_warehouse_id,

        quantity:
          values.quantity,

        notes:
          values.notes
          ||
          undefined,
      });

      onClose();
    } catch (error) {
      if (
        error instanceof APIRequestError
        &&
        error.details
      ) {
        const fields =
          error.details.fields;

        if (
          fields
          &&
          typeof fields === "object"
        ) {
          const fieldDetails =
            fields as Record<
              string,
              unknown
            >;

          const formFields: Array<
            keyof TransferFormValues
          > = [
            "product_id",
            "source_warehouse_id",
            "destination_warehouse_id",
            "quantity",
            "notes",
          ];

          for (const field of formFields) {
            const message =
              firstFieldMessage(
                fieldDetails[field],
              );

            if (message) {
              setError(
                field,
                {
                  type: "server",
                  message,
                },
              );
            }
          }
        }
      }
    }
  }

  if (!open) {
    return null;
  }

  const products =
    productQuery.data
      ?.products
    ??
    [];

  const warehouses =
    warehouseQuery.data
      ?.warehouses
    ??
    [];

  const generalError =
    createMutation.error
    instanceof Error
      ? createMutation.error.message
      : null;

  return (
    <div
      role="presentation"
      className="
        fixed inset-0 z-50
        flex items-center
        justify-center bg-slate-950/50
        p-4
      "
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="transfer-title"
        className="
          max-h-[90vh] w-full
          max-w-2xl overflow-y-auto
          rounded-2xl bg-white
          text-slate-900 shadow-2xl
        "
      >
        <div
          className="
            flex items-start
            justify-between border-b
            border-slate-200 p-5
          "
        >
          <div>
            <h2
              id="transfer-title"
              className="
                text-xl font-bold
                text-slate-900
              "
            >
              Create stock transfer
            </h2>

            <p
              className="
                mt-1 text-sm text-slate-600
              "
            >
              Move available product stock
              between two warehouses.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close"
            disabled={
              createMutation.isPending
            }
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
        </div>

        <form
          onSubmit={
            (event) => {
              void handleSubmit(
                submit,
              )(event);
            }
          }
          className="space-y-5 p-5"
        >
          <label className="block space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-900
              "
            >
              Product
            </span>

            <SearchSelect
              {...register(
                "product_id",
              )}
              disabled={
                productQuery.isPending
                ||
                createMutation.isPending
              }
              className="
                h-10 w-full rounded-lg
                border border-slate-300
                bg-white px-3 text-sm
                text-slate-900 outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
                disabled:opacity-50
              "
            >
              <option value="">
                Select product
              </option>

              {products.map(
                (product) => (
                  <option
                    key={product.id}
                    value={product.id}
                  >
                    {product.sku}
                    {" — "}
                    {product.name}
                  </option>
                ),
              )}
            </SearchSelect>

            {errors.product_id ? (
              <p className="text-sm text-red-600">
                {errors.product_id.message}
              </p>
            ) : null}
          </label>

          <div
            className="
              grid gap-4
              md:grid-cols-[1fr_auto_1fr]
              md:items-end
            "
          >
            <label className="block space-y-1.5">
              <span
                className="
                  text-sm font-semibold
                  text-slate-900
                "
              >
                Source warehouse
              </span>

              <SearchSelect
                {...register(
                  "source_warehouse_id",
                )}
                disabled={
                  warehouseQuery.isPending
                  ||
                  createMutation.isPending
                }
                className="
                  h-10 w-full rounded-lg
                  border border-slate-300
                  bg-white px-3 text-sm
                  text-slate-900 outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                  disabled:opacity-50
                "
              >
                <option value="">
                  Select source
                </option>

                {warehouses.map(
                  (warehouse) => (
                    <option
                      key={warehouse.id}
                      value={warehouse.id}
                    >
                      {warehouse.code}
                      {" — "}
                      {warehouse.name}
                    </option>
                  ),
                )}
              </SearchSelect>

              {errors.source_warehouse_id ? (
                <p
                  className="
                    text-sm text-red-600
                  "
                >
                  {
                    errors
                      .source_warehouse_id
                      .message
                  }
                </p>
              ) : null}
            </label>

            <div
              className="
                hidden h-10 items-center
                justify-center text-blue-600
                md:flex
              "
            >
              <ArrowRight size={22} />
            </div>

            <label className="block space-y-1.5">
              <span
                className="
                  text-sm font-semibold
                  text-slate-900
                "
              >
                Destination warehouse
              </span>

              <SearchSelect
                {...register(
                  "destination_warehouse_id",
                )}
                disabled={
                  warehouseQuery.isPending
                  ||
                  createMutation.isPending
                }
                className="
                  h-10 w-full rounded-lg
                  border border-slate-300
                  bg-white px-3 text-sm
                  text-slate-900 outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                  disabled:opacity-50
                "
              >
                <option value="">
                  Select destination
                </option>

                {warehouses
                  .filter(
                    (warehouse) =>
                      warehouse.id
                      !==
                      sourceWarehouseId,
                  )
                  .map(
                    (warehouse) => (
                      <option
                        key={warehouse.id}
                        value={warehouse.id}
                      >
                        {warehouse.code}
                        {" — "}
                        {warehouse.name}
                      </option>
                    ),
                  )}
              </SearchSelect>

              {
                errors
                  .destination_warehouse_id
                ? (
                  <p
                    className="
                      text-sm text-red-600
                    "
                  >
                    {
                      errors
                        .destination_warehouse_id
                        .message
                    }
                  </p>
                )
                : null
              }
            </label>
          </div>

          <label className="block space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-900
              "
            >
              Quantity
            </span>

            <input
              {...register(
                "quantity",
              )}
              type="number"
              min="0.01"
              step="0.01"
              inputMode="decimal"
              placeholder="0.00"
              disabled={
                createMutation.isPending
              }
              className="
                h-10 w-full rounded-lg
                border border-slate-300
                bg-white px-3 text-sm
                text-slate-900
                placeholder:text-slate-400
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
                disabled:opacity-50
              "
            />

            {errors.quantity ? (
              <p className="text-sm text-red-600">
                {errors.quantity.message}
              </p>
            ) : null}
          </label>

          <label className="block space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-900
              "
            >
              Notes
            </span>

            <textarea
              {...register(
                "notes",
              )}
              rows={4}
              placeholder="Optional transfer notes"
              disabled={
                createMutation.isPending
              }
              className="
                w-full resize-y rounded-lg
                border border-slate-300
                bg-white px-3 py-2
                text-sm text-slate-900
                placeholder:text-slate-400
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
                disabled:opacity-50
              "
            />

            {errors.notes ? (
              <p className="text-sm text-red-600">
                {errors.notes.message}
              </p>
            ) : null}
          </label>

          {generalError ? (
            <div
              className="
                rounded-lg border
                border-red-200 bg-red-50
                px-4 py-3 text-sm
                text-red-700
              "
            >
              {generalError}
            </div>
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
                createMutation.isPending
              }
              onClick={onClose}
              className="
                rounded-lg border
                border-slate-300 bg-white
                px-4 py-2 text-sm
                font-semibold text-slate-700
                hover:bg-slate-50
                disabled:opacity-50
              "
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={
                createMutation.isPending
              }
              className="
                rounded-lg bg-blue-600
                px-4 py-2 text-sm
                font-semibold text-white
                hover:bg-blue-700
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              {
                createMutation.isPending
                  ? "Transferring…"
                  : "Complete transfer"
              }
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
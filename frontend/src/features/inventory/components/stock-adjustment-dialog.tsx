"use client";
import { FormSheet } from "@/components/form/form-sheet";
import SearchSelect from "@/components/search-select";


import {
  useEffect,
} from "react";

import {
  LoaderCircle,
} from "lucide-react";

import {
  useForm,
} from "react-hook-form";

import {
  zodResolver,
} from "@hookform/resolvers/zod";

import {
  z,
} from "zod";

import {
  useAdjustInventory,
} from "@/features/inventory/hooks";

import type {
  InventorySummary,
} from "@/features/inventory/types";

import {
  APIRequestError,
} from "@/lib/api/client";

const adjustmentSchema = z.object({
  direction: z.enum([
    "increase",
    "decrease",
  ]),

  quantity: z
    .string()
    .trim()
    .min(
      1,
      "Quantity is required.",
    )
    .refine(
      (value) =>
        /^\d+(\.\d{1,2})?$/.test(
          value
        )
        &&
        Number(value) > 0,
      (
        "Use a number greater than zero "
        +
        "with up to two decimal places."
      ),
    ),

  reference_type: z
    .string()
    .trim()
    .max(
      100,
      "Use no more than 100 characters.",
    ),

  reference_id: z
    .string()
    .trim()
    .max(
      100,
      "Use no more than 100 characters.",
    ),

  notes: z
    .string()
    .trim()
    .max(
      1000,
      "Use no more than 1000 characters.",
    ),
});

type AdjustmentFormValues =
  z.infer<typeof adjustmentSchema>;

interface StockAdjustmentDialogProps {
  open: boolean;
  inventory: InventorySummary | null;
  onClose: () => void;
}

const emptyValues:
  AdjustmentFormValues = {
    direction: "increase",
    quantity: "",
    reference_type:
      "PHYSICAL_COUNT",
    reference_id: "",
    notes: "",
  };

function formatQuantity(
  value: string,
): string {
  const quantity = Number(
    value
  );

  return Number.isFinite(quantity)
    ? new Intl.NumberFormat(
        "en-IN",
        {
          maximumFractionDigits: 2,
        },
      ).format(
        quantity
      )
    : value;
}

export default function StockAdjustmentDialog({
  open,
  inventory,
  onClose,
}: StockAdjustmentDialogProps) {
  const adjustmentMutation =
    useAdjustInventory();

  const resetAdjustmentMutation =
    adjustmentMutation.reset;

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<
    AdjustmentFormValues
  >({
    resolver:
      zodResolver(
        adjustmentSchema,
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

    resetAdjustmentMutation();
  }, [
    open,
    reset,
    resetAdjustmentMutation,
  ]);

  async function submit(
    values: AdjustmentFormValues,
  ): Promise<void> {
    if (!inventory) {
      return;
    }

    const quantityChange =
      values.direction
      ===
      "decrease"
        ? `-${values.quantity}`
        : values.quantity;

    try {
      await adjustmentMutation.mutateAsync({
        inventoryId:
          inventory.id,
        input: {
          quantity_change:
            quantityChange,
          reference_type:
            values.reference_type,
          reference_id:
            values.reference_id,
          notes:
            values.notes,
        },
      });

      onClose();
    } catch (error) {
      if (
        error
        instanceof
        APIRequestError
      ) {
        const messages =
          error.details
            ?.quantity_change;

        if (
          Array.isArray(
            messages
          )
          &&
          typeof messages[0]
          ===
          "string"
        ) {
          setError(
            "quantity",
            {
              type: "server",
              message:
                messages[0],
            },
          );
        } else {
          setError(
            "root.server",
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
        "root.server",
        {
          type: "server",
          message: (
            "Unable to adjust "
            +
            "inventory."
          ),
        },
      );
    }
  }

  if (
    !open
    ||
    !inventory
  ) {
    return null;
  }

  return (
    <FormSheet title={"Adjust stock"} subtitle={"Correct stock after a count, damage or loss. Every change is logged."} onClose={onClose} busy={adjustmentMutation.isPending} size="md" closeLabel="Close dialog">
      

        <form
          onSubmit={(event) => {
            void handleSubmit(
              submit,
            )(event);
          }}
          className="space-y-5 p-6"
        >
          <div
            className="
              grid grid-cols-3 gap-3
              rounded-xl bg-slate-50 p-4
            "
          >
            <div>
              <p
                className="
                  text-xs text-slate-500
                "
              >
                Physical
              </p>

              <p
                className="
                  mt-1 font-semibold
                  text-blue-700
                "
              >
                {
                  formatQuantity(
                    inventory.quantity,
                  )
                }
              </p>
            </div>

            <div>
              <p
                className="
                  text-xs text-slate-500
                "
              >
                Reserved
              </p>

              <p
                className="
                  mt-1 font-semibold
                  text-amber-700
                "
              >
                {
                  formatQuantity(
                    inventory
                      .reserved_quantity,
                  )
                }
              </p>
            </div>

            <div>
              <p
                className="
                  text-xs text-slate-500
                "
              >
                Available
              </p>

              <p
                className="
                  mt-1 font-semibold
                  text-emerald-700
                "
              >
                {
                  formatQuantity(
                    inventory
                      .available_quantity,
                  )
                }
              </p>
            </div>
          </div>

          {errors.root?.server ? (
            <div
              role="alert"
              className="
                rounded-lg border
                border-red-200 bg-red-50
                px-4 py-3 text-sm
                text-red-700
              "
            >
              {
                errors.root
                  .server
                  .message
              }
            </div>
          ) : null}

          <div
            className="
              grid gap-4 sm:grid-cols-2
            "
          >
            <label className="space-y-1.5">
              <span
                className="
                  text-sm font-semibold
                  text-slate-700
                "
              >
                Direction
              </span>

              <SearchSelect
                {...register("direction")}
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
                "
              >
                <option value="increase">
                  Increase stock
                </option>

                <option value="decrease">
                  Decrease stock
                </option>
              </SearchSelect>
            </label>

            <label className="space-y-1.5">
              <span
                className="
                  text-sm font-semibold
                  text-slate-700
                "
              >
                Quantity
              </span>

              <input
                {...register("quantity")}
                inputMode="decimal"
                placeholder="0.00"
                className="
                  h-10 w-full rounded-lg
                  border border-slate-300
                  px-3 text-sm outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />

              {errors.quantity ? (
                <p className="text-xs text-red-600">
                  {errors.quantity.message}
                </p>
              ) : null}
            </label>
          </div>

          <div
            className="
              grid gap-4 sm:grid-cols-2
            "
          >
            <label className="space-y-1.5">
              <span
                className="
                  text-sm font-semibold
                  text-slate-700
                "
              >
                Reference type
              </span>

              <input
                {...register(
                  "reference_type"
                )}
                className="
                  h-10 w-full rounded-lg
                  border border-slate-300
                  px-3 text-sm outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />
            </label>

            <label className="space-y-1.5">
              <span
                className="
                  text-sm font-semibold
                  text-slate-700
                "
              >
                Reference ID
              </span>

              <input
                {...register(
                  "reference_id"
                )}
                placeholder="Optional"
                className="
                  h-10 w-full rounded-lg
                  border border-slate-300
                  px-3 text-sm outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />
            </label>
          </div>

          <label className="block space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Notes
            </span>

            <textarea
              {...register("notes")}
              rows={3}
              placeholder={
                "Reason for adjustment"
              }
              className="
                w-full resize-y rounded-lg
                border border-slate-300
                px-3 py-2 text-sm
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            />
          </label>

          <footer className="nxf-actions"><span /><div className="nxf-buttons">
            <button
              type="button"
              disabled={
                adjustmentMutation.isPending
              }
              onClick={onClose}
              className="nx-button nx-secondary nxf-secondary-sm"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={
                adjustmentMutation.isPending
              }
              className="nx-button"
            >
              {adjustmentMutation.isPending ? (
                <LoaderCircle
                  size={16}
                  className="animate-spin"
                />
              ) : null}

              Apply adjustment
            </button>
          </div></footer>
        </form>
      </FormSheet>
  );
}

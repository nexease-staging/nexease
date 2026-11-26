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
  useCreateInventory,
  useProductLookup,
} from "@/features/inventory/hooks";

import {
  useWarehouseList,
} from "@/features/warehouses/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

const openingInventorySchema =
  z.object({
    product_id: z
      .string()
      .min(
        1,
        "Select a product.",
      ),

    warehouse_id: z
      .string()
      .min(
        1,
        "Select a warehouse.",
      ),

    quantity: z
      .string()
      .trim()
      .min(
        1,
        "Opening quantity is required.",
      )
      .refine(
        (value) =>
          /^\d+(\.\d{1,2})?$/.test(
            value
          ),
        (
          "Use a non-negative number "
          +
          "with up to two decimal places."
        ),
      ),
  });

type OpeningInventoryFormValues =
  z.infer<
    typeof openingInventorySchema
  >;

interface OpeningInventoryDialogProps {
  open: boolean;
  onClose: () => void;
}

const emptyValues:
  OpeningInventoryFormValues = {
    product_id: "",
    warehouse_id: "",
    quantity: "0",
  };

export default function OpeningInventoryDialog({
  open,
  onClose,
}: OpeningInventoryDialogProps) {
  const createMutation =
    useCreateInventory();

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
    register,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<
    OpeningInventoryFormValues
  >({
    resolver:
      zodResolver(
        openingInventorySchema,
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

  async function submit(
    values: OpeningInventoryFormValues,
  ): Promise<void> {
    try {
      await createMutation.mutateAsync({
        product_id:
          values.product_id,
        warehouse_id:
          values.warehouse_id,
        quantity:
          values.quantity,
      });

      reset(
        emptyValues
      );

      onClose();
    } catch (error) {
      if (
        error
        instanceof
        APIRequestError
      ) {
        const fieldNames = [
          "product_id",
          "warehouse_id",
          "quantity",
        ] as const;

        let fieldErrorApplied = false;

        for (
          const field
          of fieldNames
        ) {
          const messages =
            error.details
              ?.[field];

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
              field,
              {
                type: "server",
                message:
                  messages[0],
              },
            );

            fieldErrorApplied = true;
          }
        }

        if (!fieldErrorApplied) {
          const inventoryMessages =
            error.details
              ?.inventory;

          setError(
            "root.server",
            {
              type: "server",
              message:
                (
                  Array.isArray(
                    inventoryMessages
                  )
                  &&
                  typeof inventoryMessages[0]
                  ===
                  "string"
                )
                  ? inventoryMessages[0]
                  : error.message,
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
            "Unable to create "
            +
            "opening inventory."
          ),
        },
      );
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

  const lookupError =
    productQuery.error
    ??
    warehouseQuery.error;

  const lookupPending =
    productQuery.isPending
    ||
    warehouseQuery.isPending;

  return (
    <FormSheet title={"Opening stock"} subtitle={"Record the stock you already have when you start using NexEase."} onClose={onClose} busy={createMutation.isPending} size="md" closeLabel="Close dialog">
      

        <form
          onSubmit={(event) => {
            void handleSubmit(
              submit,
            )(event);
          }}
          className="space-y-5 p-6"
        >
          {lookupError ? (
            <div
              role="alert"
              className="
                rounded-lg border
                border-red-200 bg-red-50
                px-4 py-3 text-sm
                text-red-700
              "
            >
              {lookupError.message}
            </div>
          ) : null}

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

          <label className="block space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Product
            </span>

            <SearchSelect
              {...register("product_id")}
              disabled={lookupPending}
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
              <p className="text-xs text-red-600">
                {errors.product_id.message}
              </p>
            ) : null}
          </label>

          <label className="block space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Warehouse
            </span>

            <SearchSelect
              {...register("warehouse_id")}
              disabled={lookupPending}
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
                Select warehouse
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

            {errors.warehouse_id ? (
              <p className="text-xs text-red-600">
                {errors.warehouse_id.message}
              </p>
            ) : null}
          </label>

          <label className="block space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Opening quantity
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

          <footer className="nxf-actions"><span /><div className="nxf-buttons">
            <button
              type="button"
              disabled={
                createMutation.isPending
              }
              onClick={onClose}
              className="nx-button nx-secondary nxf-secondary-sm"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={
                lookupPending
                ||
                Boolean(
                  lookupError
                )
                ||
                createMutation.isPending
              }
              className="nx-button"
            >
              {createMutation.isPending ? (
                <LoaderCircle
                  size={16}
                  className="animate-spin"
                />
              ) : null}

              Create inventory
            </button>
          </div></footer>
        </form>
      </FormSheet>
  );
}

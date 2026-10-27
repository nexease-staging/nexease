"use client";
import SearchSelect from "@/components/search-select";


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
  useCreateProduct,
  useProduct,
  useProductCategories,
  useUpdateProduct,
} from "@/features/products/hooks";

import type {
  ProductDetail,
} from "@/features/products/types";

import {
  APIRequestError,
} from "@/lib/api/client";

const optionalPriceSchema = z
  .string()
  .trim()
  .refine(
    (value) => {
      if (!value) {
        return true;
      }

      const price = Number(value);

      return (
        Number.isFinite(price)
        &&
        price >= 0
      );
    },
    "Price must be zero or greater.",
  );

const productSchema = z.object({
  sku: z
    .string()
    .trim()
    .min(
      1,
      "SKU is required.",
    )
    .max(
      50,
      "SKU cannot exceed 50 characters.",
    ),

  name: z
    .string()
    .trim()
    .min(
      1,
      "Product name is required.",
    )
    .max(
      200,
      "Name cannot exceed 200 characters.",
    ),

  category_id: z
    .string()
    .trim()
    .min(
      1,
      "Select a category.",
    ),

  unit: z
    .string()
    .trim()
    .min(
      1,
      "Unit is required.",
    )
    .max(
      30,
      "Unit cannot exceed 30 characters.",
    ),

  brand: z
    .string()
    .trim()
    .max(
      100,
      "Brand cannot exceed 100 characters.",
    ),

  barcode: z
    .string()
    .trim()
    .max(
      100,
      "Barcode cannot exceed 100 characters.",
    ),

  cost_price:
    optionalPriceSchema,

  selling_price:
    optionalPriceSchema,

  description: z
    .string()
    .trim()
    .max(
      1000,
      "Description cannot exceed 1000 characters.",
    ),
});

type ProductFormValues =
  z.infer<typeof productSchema>;

const emptyValues: ProductFormValues = {
  sku: "AUTO",
  name: "",
  category_id: "",
  unit: "piece",
  brand: "",
  barcode: "",
  cost_price: "0.00",
  selling_price: "0.00",
  description: "",
};

interface ProductDialogProps {
  open: boolean;
  productId: string | null;
  onClose: () => void;
  onCreated?: (
    product: ProductDetail,
  ) => void;
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

export default function ProductDialog({
  open,
  productId,
  onClose,
  onCreated,
}: ProductDialogProps) {
  const isEditing =
    Boolean(productId);

  const productQuery =
    useProduct(
      productId ?? "",
      open && isEditing,
    );

  const categoryQuery =
    useProductCategories();

  const createMutation =
    useCreateProduct();

  const updateMutation =
    useUpdateProduct();

  const resetCreateMutation =
    createMutation.reset;

  const resetUpdateMutation =
    updateMutation.reset;

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<ProductFormValues>({
    resolver:
      zodResolver(
        productSchema,
      ),
    defaultValues:
      emptyValues,
  });

  useEffect(() => {
    if (!open) {
      return;
    }

    resetCreateMutation();
    resetUpdateMutation();

    if (!productId) {
      reset(
        emptyValues,
      );
    }
  }, [
    open,
    productId,
    reset,
    resetCreateMutation,
    resetUpdateMutation,
  ]);

  useEffect(() => {
    if (
      !open
      ||
      !productId
      ||
      !productQuery.data
    ) {
      return;
    }

    const product =
      productQuery.data;

    reset({
      sku:
        product.sku,
      name:
        product.name,
      category_id:
        product.category.id,
      unit:
        product.unit,
      brand:
        product.brand
        ??
        "",
      barcode:
        product.barcode
        ??
        "",
      cost_price:
        product.cost_price,
      selling_price:
        product.selling_price,
      description:
        product.description
        ??
        "",
    });
  }, [
    open,
    productId,
    productQuery.data,
    reset,
  ]);

  function applyServerErrors(
    error: APIRequestError,
  ): void {
    if (!error.details) {
      return;
    }

    const nestedFields =
      error.details.fields;

    const fieldDetails =
      (
        nestedFields
        &&
        typeof nestedFields === "object"
      )
        ? nestedFields as Record<
            string,
            unknown
          >
        : error.details;

    const formFields: Array<
      keyof ProductFormValues
    > = [
      "sku",
      "name",
      "category_id",
      "unit",
      "brand",
      "barcode",
      "cost_price",
      "selling_price",
      "description",
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

  async function submit(
    values: ProductFormValues,
  ): Promise<void> {
    const input = {
      sku:
        values.sku,
      name:
        values.name,
      category_id:
        values.category_id,
      unit:
        values.unit,
      brand:
        values.brand,
      barcode:
        values.barcode,
      cost_price:
        values.cost_price
        ||
        "0.00",
      selling_price:
        values.selling_price
        ||
        "0.00",
      description:
        values.description,
    };

    try {
      if (productId) {
        await updateMutation.mutateAsync({
          productId,
          input,
        });
      } else {
        const createdProduct =
          await createMutation.mutateAsync(
            input,
          );

        onCreated?.(
          createdProduct,
        );
      }

      onClose();
    } catch (error) {
      if (
        error instanceof APIRequestError
      ) {
        applyServerErrors(error);
      }
    }
  }

  if (!open) {
    return null;
  }

  const categories =
    categoryQuery.data
      ?.categories
    ??
    [];

  const isPending =
    createMutation.isPending
    ||
    updateMutation.isPending;

  const mutationError =
    createMutation.error
    ??
    updateMutation.error;

  const generalError =
    mutationError instanceof Error
      ? mutationError.message
      : null;

  return (
    <div
      role="presentation"
      className="
        fixed inset-0 z-50
        flex items-center justify-center
        bg-slate-950/50 p-4
      "
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="product-dialog-title"
        className="
          max-h-[90vh] w-full
          max-w-3xl overflow-y-auto
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
              id="product-dialog-title"
              className="
                text-xl font-bold
                text-slate-900
              "
            >
              {
                isEditing
                  ? "Edit product"
                  : "Create product"
              }
            </h2>

            <p
              className="
                mt-1 text-sm text-slate-600
              "
            >
              {
                isEditing
                  ? "Update product catalog details."
                  : "Add a product to your catalog."
              }
            </p>
          </div>

          <button
            type="button"
            aria-label="Close"
            disabled={isPending}
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

        {isEditing
        && productQuery.isPending ? (
          <div
            className="
              flex min-h-72 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading product…
          </div>
        ) : isEditing
        && productQuery.isError ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              gap-3 p-6 text-center
            "
          >
            <p className="text-sm text-red-700">
              {productQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void productQuery.refetch();
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
                submit,
              )(event);
            }}
            className="space-y-5 p-5"
          >
            <div
              className="
                grid gap-4 md:grid-cols-2
              "
            >
              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  SKU
                </span>

                <input
                  {...register("sku")}
                  type="text"
                  placeholder="PRODUCT-001"
                  disabled={isPending}
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

                {errors.sku ? (
                  <p className="text-sm text-red-600">
                    {errors.sku.message}
                  </p>
                ) : null}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Product name
                </span>

                <input
                  {...register("name")}
                  type="text"
                  placeholder="Product name"
                  disabled={isPending}
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

                {errors.name ? (
                  <p className="text-sm text-red-600">
                    {errors.name.message}
                  </p>
                ) : null}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Category
                </span>

                <SearchSelect
                  {...register(
                    "category_id",
                  )}
                  disabled={
                    isPending
                    ||
                    categoryQuery.isPending
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
                    Select category
                  </option>

                  {categories.map(
                    (category) => (
                      <option
                        key={category.id}
                        value={category.id}
                      >
                        {category.name}
                      </option>
                    ),
                  )}
                </SearchSelect>

                {errors.category_id ? (
                  <p className="text-sm text-red-600">
                    {errors.category_id.message}
                  </p>
                ) : null}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Unit
                </span>

                <input
                  {...register("unit")}
                  type="text"
                  placeholder="piece"
                  disabled={isPending}
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

                {errors.unit ? (
                  <p className="text-sm text-red-600">
                    {errors.unit.message}
                  </p>
                ) : null}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Brand
                </span>

                <input
                  {...register("brand")}
                  type="text"
                  placeholder="Optional brand"
                  disabled={isPending}
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

                {errors.brand ? (
                  <p className="text-sm text-red-600">
                    {errors.brand.message}
                  </p>
                ) : null}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Barcode
                </span>

                <input
                  {...register("barcode")}
                  type="text"
                  placeholder="Optional barcode"
                  disabled={isPending}
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

                {errors.barcode ? (
                  <p className="text-sm text-red-600">
                    {errors.barcode.message}
                  </p>
                ) : null}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Cost price
                </span>

                <input
                  {...register("cost_price")}
                  type="number"
                  min="0"
                  step="0.01"
                  inputMode="decimal"
                  placeholder="0.00"
                  disabled={isPending}
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

                {errors.cost_price ? (
                  <p className="text-sm text-red-600">
                    {errors.cost_price.message}
                  </p>
                ) : null}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Selling price
                </span>

                <input
                  {...register(
                    "selling_price",
                  )}
                  type="number"
                  min="0"
                  step="0.01"
                  inputMode="decimal"
                  placeholder="0.00"
                  disabled={isPending}
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

                {errors.selling_price ? (
                  <p className="text-sm text-red-600">
                    {errors.selling_price.message}
                  </p>
                ) : null}
              </label>
            </div>

            <label className="block space-y-1.5">
              <span className="text-sm font-semibold">
                Description
              </span>

              <textarea
                {...register("description")}
                rows={4}
                placeholder="Optional product description"
                disabled={isPending}
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

              {errors.description ? (
                <p className="text-sm text-red-600">
                  {errors.description.message}
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
                disabled={isPending}
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
                disabled={isPending}
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
                  isPending
                    ? "Saving…"
                    : isEditing
                      ? "Save changes"
                      : "Create product"
                }
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
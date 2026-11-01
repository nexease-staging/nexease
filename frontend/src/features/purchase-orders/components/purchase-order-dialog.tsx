"use client";
import {getProduct} from "@/features/products/api";
import SearchSelect from "@/components/search-select";


import {
  useEffect,
} from "react";

import {
  zodResolver,
} from "@hookform/resolvers/zod";

import {
  Plus,
  Trash2,
  X,
} from "lucide-react";

import {
  useFieldArray,
  useForm,
  useWatch,
} from "react-hook-form";

import {
  z,
} from "zod";

import {
  useProductList,
} from "@/features/products/hooks";

import {
  useCreatePurchaseOrder,
  usePurchaseOrder,
  useUpdatePurchaseOrder,
} from "@/features/purchase-orders/hooks";

import {
  useSupplierList,
} from "@/features/suppliers/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

const nonNegativeNumber = z
  .string()
  .trim()
  .refine(
    (value) => {
      const number = Number(value);

      return (
        value !== ""
        &&
        Number.isFinite(number)
        &&
        number >= 0
      );
    },
    "Enter a valid non-negative number.",
  );

const positiveNumber = z
  .string()
  .trim()
  .refine(
    (value) => {
      const number = Number(value);

      return (
        value !== ""
        &&
        Number.isFinite(number)
        &&
        number > 0
      );
    },
    "Enter a number greater than zero.",
  );

const purchaseOrderSchema = z.object({
  supplier_id: z
    .string()
    .min(
      1,
      "Supplier is required.",
    ),

  order_date: z
    .string()
    .min(
      1,
      "Order date is required.",
    ),

  expected_delivery_date:
    z.string(),

  notes: z
    .string()
    .trim()
    .max(
      1000,
      "Notes cannot exceed 1000 characters.",
    ),

  items: z
    .array(
      z.object({
        product_id: z
          .string()
          .min(
            1,
            "Product is required.",
          ),

        quantity:
          positiveNumber,

        unit_price:
          nonNegativeNumber,

        tax_rate:
          nonNegativeNumber,

        discount:
          nonNegativeNumber,
      }),
    )
    .min(
      1,
      "At least one item is required.",
    ),
});

type PurchaseOrderFormValues =
  z.infer<
    typeof purchaseOrderSchema
  >;

interface PurchaseOrderDialogProps {
  open: boolean;
  purchaseOrderId: string | null;
  onClose: () => void;
  onSaved?: (
    purchaseOrderId: string,
  ) => void;
}

const emptyItem = {
  product_id: "",
  quantity: "1.00",
  unit_price: "0.00",
  tax_rate: "0.00",
  discount: "0.00",
};

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
  PurchaseOrderFormValues {
  return {
    supplier_id: "",
    order_date:
      todayValue(),
    expected_delivery_date: "",
    notes: "",
    items: [
      {
        ...emptyItem,
      },
    ],
  };
}

function calculateLineTotal(
  quantity: string,
  unitPrice: string,
  taxRate: string,
  discount: string,
): number {
  const quantityValue =
    Number(
      quantity,
    );

  const unitPriceValue =
    Number(
      unitPrice,
    );

  const taxRateValue =
    Number(
      taxRate,
    );

  const discountValue =
    Number(
      discount,
    );

  if (
    !Number.isFinite(
      quantityValue,
    )
    ||
    !Number.isFinite(
      unitPriceValue,
    )
    ||
    !Number.isFinite(
      taxRateValue,
    )
    ||
    !Number.isFinite(
      discountValue,
    )
  ) {
    return 0;
  }

  const subtotal =
    Math.max(
      0,
      (
        quantityValue
        *
        unitPriceValue
      )
      -
      discountValue,
    );

  return (
    subtotal
    +
    (
      subtotal
      *
      taxRateValue
      /
      100
    )
  );
}

function formatAmount(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-IN",
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(
    value,
  );
}

export default function PurchaseOrderDialog({
  open,
  purchaseOrderId,
  onClose,
  onSaved,
}: PurchaseOrderDialogProps) {
  const editing =
    Boolean(
      purchaseOrderId,
    );

  const purchaseOrderQuery =
    usePurchaseOrder(
      purchaseOrderId ?? "",
      open
      &&
      editing,
    );

  const createMutation =
    useCreatePurchaseOrder();

  const updateMutation =
    useUpdatePurchaseOrder();

  const supplierQuery =
    useSupplierList({
      page: 1,
      page_size: 100,
      is_active: true,
      sort: "name",
    });

  const productQuery =
    useProductList({
      page: 1,
      page_size: 100,
      is_active: true,
      sort: "name",
    });

  const {
    control,
    register,
    setValue,
    getValues,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<
    PurchaseOrderFormValues
  >({
    resolver:
      zodResolver(
        purchaseOrderSchema,
      ),

    defaultValues:
      emptyValues(),
  });

  const {
    fields,
    append,
    remove,
  } = useFieldArray({
    control,
    name: "items",
  });

  const watchedItems =
    useWatch({
      control,
      name: "items",
    });

  useEffect(() => {
    if (!open) {
      return;
    }

    if (
      editing
      &&
      purchaseOrderQuery.data
    ) {
      const purchaseOrder =
        purchaseOrderQuery.data;

      reset({
        supplier_id:
          purchaseOrder.supplier.id,
        order_date:
          purchaseOrder.order_date,
        expected_delivery_date:
          (
            purchaseOrder
              .expected_delivery_date
            ??
            ""
          ),
        notes:
          purchaseOrder.notes
          ??
          "",
        items:
          purchaseOrder.items.map(
            (item) => ({
              product_id:
                item.product.id,
              quantity:
                item.quantity,
              unit_price:
                item.unit_price,
              tax_rate:
                item.tax_rate,
              discount:
                item.discount,
            }),
          ),
      });

      return;
    }

    if (!editing) {
      reset(
        emptyValues(),
      );
    }
  }, [
    editing,
    open,
    purchaseOrderQuery.data,
    reset,
  ]);

  if (!open) {
    return null;
  }

  const suppliers =
    supplierQuery.data
      ?.suppliers
    ??
    [];

  const products =
    productQuery.data
      ?.products
    ??
    [];

  const estimatedTotal =
    (
      watchedItems
      ??
      []
    ).reduce(
      (
        total,
        item,
      ) => (
        total
        +
        calculateLineTotal(
          item.quantity,
          item.unit_price,
          item.tax_rate,
          item.discount,
        )
      ),
      0,
    );

  const pending =
    createMutation.isPending
    ||
    updateMutation.isPending;

  async function submit(
    values: PurchaseOrderFormValues,
  ): Promise<void> {
    const input = {
      supplier_id:
        values.supplier_id,
      order_date:
        values.order_date,
      expected_delivery_date:
        (
          values
            .expected_delivery_date
          ||
          undefined
        ),
      notes:
        values.notes.trim()
        ||
        undefined,
      items:
        values.items.map(
          (item) => ({
            product_id:
              item.product_id,
            quantity:
              item.quantity,
            unit_price:
              item.unit_price,
            tax_rate:
              item.tax_rate,
            discount:
              item.discount,
          }),
        ),
    };

    try {
      const savedPurchaseOrder =
        editing
        &&
        purchaseOrderId
          ? await updateMutation
              .mutateAsync({
                purchaseOrderId,
                input,
              })
          : await createMutation
              .mutateAsync(
                input,
              );

      onClose();

      onSaved?.(
        savedPurchaseOrder.id,
      );

    } catch (error) {
      setError(
        "root",
        {
          type: "server",
          message:
            error
            instanceof
            APIRequestError
              ? error.message
              : (
                "Unable to save the "
                +
                "purchase order."
              ),
        },
      );
    }
  }

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
        aria-labelledby="purchase-order-dialog-title"
        className="
          max-h-[calc(100vh-2rem)]
          w-full max-w-5xl
          overflow-y-auto rounded-2xl
          border border-slate-200
          bg-white text-slate-900
          shadow-2xl
        "
      >
        <header
          className="
            sticky top-0 z-20
            flex items-start
            justify-between gap-4
            border-b border-slate-200
            bg-white px-5 py-4
            sm:px-6
          "
        >
          <div>
            <h2
              id="purchase-order-dialog-title"
              className="
                text-lg font-semibold
                text-slate-950
              "
            >
              {editing
                ? "Edit Purchase Order"
                : "New Purchase Order"}
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-600
              "
            >
              Add the supplier, expected date
              and products to be purchased.
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

        {(
          editing
          &&
          purchaseOrderQuery.isPending
        ) ? (
          <div
            className="
              px-6 py-16 text-center
              text-sm text-slate-600
            "
          >
            Loading purchase order…
          </div>
        ) : (
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
                lg:grid-cols-3
              "
            >
              <div>
                <label
                  htmlFor="po-supplier"
                  className="
                    text-sm font-medium
                    text-slate-800
                  "
                >
                  Supplier
                </label>

                <SearchSelect
                  id="po-supplier"
                  disabled={pending}
                  {...register(
                    "supplier_id",
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
                >
                  <option value="">
                    Select supplier
                  </option>

                  {suppliers.map(
                    (supplier) => (
                      <option
                        key={supplier.id}
                        value={supplier.id}
                      >
                        {supplier.code}
                        {" — "}
                        {supplier.name}
                      </option>
                    ),
                  )}
                </SearchSelect>

                {errors.supplier_id ? (
                  <p
                    className="
                      mt-1 text-sm
                      text-red-600
                    "
                  >
                    {
                      errors
                        .supplier_id
                        .message
                    }
                  </p>
                ) : null}
              </div>

              <div>
                <label
                  htmlFor="po-order-date"
                  className="
                    text-sm font-medium
                    text-slate-800
                  "
                >
                  Order date
                </label>

                <input
                  id="po-order-date"
                  type="date"
                  disabled={pending}
                  {...register(
                    "order_date",
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

                {errors.order_date ? (
                  <p
                    className="
                      mt-1 text-sm
                      text-red-600
                    "
                  >
                    {
                      errors
                        .order_date
                        .message
                    }
                  </p>
                ) : null}
              </div>

              <div>
                <label
                  htmlFor="po-delivery-date"
                  className="
                    text-sm font-medium
                    text-slate-800
                  "
                >
                  Expected delivery
                </label>

                <input
                  id="po-delivery-date"
                  type="date"
                  disabled={pending}
                  {...register(
                    "expected_delivery_date",
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
              </div>
            </div>

            <div
              className="
                border-y border-slate-200
                bg-slate-50 px-5 py-5
                sm:px-6
              "
            >
              <div
                className="
                  flex items-center
                  justify-between gap-3
                "
              >
                <div>
                  <h3
                    className="
                      font-semibold
                      text-slate-950
                    "
                  >
                    Purchase Items
                  </h3>

                  <p
                    className="
                      mt-1 text-sm
                      text-slate-600
                    "
                  >
                    Estimated total: ₹
                    {formatAmount(
                      estimatedTotal,
                    )}
                  </p>
                </div>

                <button title="Add Item"
                  type="button"
                  disabled={pending}
                  onClick={() => {
                    append({
                      ...emptyItem,
                    });
                  }}
                  className="
                    inline-flex items-center
                    gap-2 rounded-lg
                    border border-blue-200
                    bg-blue-50 px-3 py-2
                    text-sm font-semibold
                    text-blue-700
                    hover:bg-blue-100
                  "
                >
                  <Plus size={16} /><span className="sr-only">Add Item</span></button>
              </div>

              <div className="mt-4 space-y-4">
                {fields.map(
                  (
                    field,
                    index,
                  ) => {
                    const watchedItem =
                      watchedItems?.[
                        index
                      ]
                      ??
                      emptyItem;

                    const lineTotal =
                      calculateLineTotal(
                        watchedItem.quantity,
                        watchedItem.unit_price,
                        watchedItem.tax_rate,
                        watchedItem.discount,
                      );

                    return (
                      <div
                        key={field.id}
                        className="
                          grid gap-3 rounded-xl
                          border border-slate-200
                          bg-white p-4
                          sm:grid-cols-2
                          xl:grid-cols-12
                        "
                      >
                        <div
                          className="
                            sm:col-span-2
                            xl:col-span-4
                          "
                        >
                          <label
                            className="
                              text-xs font-semibold
                              uppercase tracking-wide
                              text-slate-600
                            "
                          >
                            Product
                          </label>

                          <SearchSelect
                            disabled={pending}
                            {...register(
                              `items.${index}.product_id`,
                            )}
                            onChange={async e=>{const id=e.target.value;setValue(`items.${index}.product_id`,id,{shouldValidate:true});if(id){try{const product=await getProduct(id);if(getValues(`items.${index}.product_id`)!==id)return;setValue(`items.${index}.unit_price`,product.cost_price,{shouldValidate:true});}catch{setError('root',{message:'Could not load the product price. Review it before saving.'});}}}}
                            className="
                              mt-1.5 w-full
                              rounded-lg border
                              border-slate-300
                              bg-white px-3 py-2
                              text-sm text-slate-950
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

                          {errors.items?.[
                            index
                          ]?.product_id ? (
                            <p
                              className="
                                mt-1 text-xs
                                text-red-600
                              "
                            >
                              {
                                errors.items[
                                  index
                                ]?.product_id
                                  ?.message
                              }
                            </p>
                          ) : null}
                        </div>

                        {[
                          {
                            key:
                              "quantity",
                            label:
                              "Quantity",
                          },
                          {
                            key:
                              "unit_price",
                            label:
                              "Unit price",
                          },
                          {
                            key:
                              "tax_rate",
                            label:
                              "Tax %",
                          },
                          {
                            key:
                              "discount",
                            label:
                              "Discount",
                          },
                        ].map(
                          (input) => (
                            <div
                              key={input.key}
                              className="
                                xl:col-span-1
                              "
                            >
                              <label
                                className="
                                  text-xs font-semibold
                                  uppercase tracking-wide
                                  text-slate-600
                                "
                              >
                                {input.label}
                              </label>

                              <input
                                type="number"
                                min="0"
                                step="0.01"
                                disabled={pending}
                                {...register(
                                  (
                                    `items.${index}.`
                                    +
                                    input.key
                                  ) as (
                                    | `items.${number}.quantity`
                                    | `items.${number}.unit_price`
                                    | `items.${number}.tax_rate`
                                    | `items.${number}.discount`
                                  ),
                                )}
                                className="
                                  mt-1.5 w-full
                                  rounded-lg border
                                  border-slate-300
                                  bg-white px-2 py-2
                                  text-sm text-slate-950
                                "
                              />
                            </div>
                          ),
                        )}

                        <div
                          className="
                            flex items-end
                            xl:col-span-3
                          "
                        >
                          <div
                            className="
                              flex w-full
                              items-center
                              justify-between gap-3
                              rounded-lg
                              bg-slate-50
                              px-3 py-2
                            "
                          >
                            <div>
                              <p
                                className="
                                  text-xs
                                  text-slate-500
                                "
                              >
                                Line total
                              </p>

                              <p
                                className="
                                  font-semibold
                                  text-slate-950
                                "
                              >
                                ₹
                                {formatAmount(
                                  lineTotal,
                                )}
                              </p>
                            </div>

                            <button
                              type="button"
                              aria-label="Remove item"
                              disabled={
                                pending
                                ||
                                fields.length === 1
                              }
                              onClick={() => {
                                remove(
                                  index,
                                );
                              }}
                              className="
                                rounded-lg p-2
                                text-red-600
                                hover:bg-red-50
                                disabled:opacity-40
                              "
                            >
                              <Trash2
                                size={17}
                              />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  },
                )}
              </div>

              {errors.items?.message ? (
                <p
                  className="
                    mt-2 text-sm
                    text-red-600
                  "
                >
                  {errors.items.message}
                </p>
              ) : null}
            </div>

            <div
              className="
                px-5 py-5 sm:px-6
              "
            >
              <label
                htmlFor="po-notes"
                className="
                  text-sm font-medium
                  text-slate-800
                "
              >
                Notes
              </label>

              <textarea
                id="po-notes"
                rows={3}
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
                placeholder="Optional purchase notes"
              />

              {errors.root ? (
                <div
                  className="
                    mt-4 rounded-lg border
                    border-red-200 bg-red-50
                    px-4 py-3 text-sm
                    text-red-700
                  "
                >
                  {errors.root.message}
                </div>
              ) : null}
            </div>

            <footer
              className="
                sticky bottom-0 z-20
                flex flex-col-reverse
                gap-3 border-t
                border-slate-200
                bg-white px-5 py-4
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
                "
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={pending}
                className="
                  rounded-lg bg-blue-600
                  px-4 py-2.5
                  text-sm font-semibold
                  text-white
                  hover:bg-blue-700
                  disabled:opacity-50
                "
              >
                {pending
                  ? "Saving…"
                  : (
                    editing
                      ? "Update Order"
                      : "Create Order"
                  )}
              </button>
            </footer>
          </form>
        )}
      </section>
    </div>
  );
}
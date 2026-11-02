"use client";
import SearchSelect from "@/components/search-select";


import {
  useEffect,
  useState,
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
  SearchCombobox,
} from "@/components/ui/search-combobox";

import {
  useCustomerList,
} from "@/features/customers/hooks";

import CustomerDialog
  from "@/features/customers/components/customer-dialog";

import ProductDialog
  from "@/features/products/components/product-dialog";

import type {
  ProductDetail,
} from "@/features/products/types";

import {
  useCreateSalesOrder,
  useSalesOrder,
  useUpdateSalesOrder,
} from "@/features/sales-orders/hooks";

import SalesOrderProductSearch
  from "@/features/sales-orders/components/sales-order-product-search";

import {
  useWarehouseList,
} from "@/features/warehouses/hooks";

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

const salesOrderSchema = z.object({
  customer_id: z
    .string()
    .min(
      1,
      "Customer is required.",
    ),

  warehouse_id: z
    .string()
    .min(
      1,
      "Warehouse is required.",
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

type SalesOrderFormValues =
  z.infer<typeof salesOrderSchema>;

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
  SalesOrderFormValues {
  return {
    customer_id: "",
    warehouse_id: "",
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

function dateInputValue(
  value: string | null,
): string {
  if (!value) {
    return "";
  }

  return value.slice(
    0,
    10,
  );
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

const inputClassName = `
  h-10 w-full rounded-lg
  border border-slate-300
  bg-white px-3 text-sm
  text-slate-900 outline-none
  focus:border-blue-500
  focus:ring-2 focus:ring-blue-100
  disabled:opacity-50
`;

interface SalesOrderDialogProps {
  open: boolean;
  salesOrderId: string | null;
  canCreateCustomer: boolean;
  canCreateProduct: boolean;
  onClose: () => void;
}

export default function SalesOrderDialog({
  open,
  salesOrderId,
  canCreateCustomer,
  canCreateProduct,
  onClose,
}: SalesOrderDialogProps) {
  const isEditing =
    Boolean(
      salesOrderId
    );

  const [
    customerSearch,
    setCustomerSearch,
  ] = useState("");

  const [
    productSearches,
    setProductSearches,
  ] = useState<
    Record<string, string>
  >({});

  const [
    selectedProductLabels,
    setSelectedProductLabels,
  ] = useState<
    Record<string, string>
  >({});

  const [
    selectedCustomerLabel,
    setSelectedCustomerLabel,
  ] = useState("");

  const [
    customerDialogOpen,
    setCustomerDialogOpen,
  ] = useState(false);

  const [
    productDialogOpen,
    setProductDialogOpen,
  ] = useState(false);

  const [
    productCreateFieldId,
    setProductCreateFieldId,
  ] = useState<string | null>(
    null,
  );

  const salesOrderQuery =
    useSalesOrder(
      salesOrderId ?? "",
      open && isEditing,
    );

  const normalizedCustomerSearch =
    customerSearch.trim();

  const customerQuery =
    useCustomerList(
      {
        page: 1,
        page_size: 10,
        search:
          normalizedCustomerSearch.length >= 3
            ? normalizedCustomerSearch
            : undefined,
        is_active: true,
        sort: "name",
      },
      open
      &&
      normalizedCustomerSearch.length >= 3,
    );

  const warehouseQuery =
    useWarehouseList({
      page: 1,
      page_size: 100,
      is_active: true,
      sort: "name",
    });

  const createMutation =
    useCreateSalesOrder();

  const updateMutation =
    useUpdateSalesOrder();

  const resetCreateMutation =
    createMutation.reset;

  const resetUpdateMutation =
    updateMutation.reset;

  const {
    control,
    register,
    handleSubmit,
    reset,
    setError,
    setValue,
    formState: {
      errors,
    },
  } = useForm<SalesOrderFormValues>({
    resolver:
      zodResolver(
        salesOrderSchema,
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
    })
    ??
    [];

  useEffect(() => {
    if (!open) {
      return;
    }

    resetCreateMutation();
    resetUpdateMutation();

    if (!salesOrderId) {
      reset(
        emptyValues(),
      );
    }
  }, [
    open,
    reset,
    resetCreateMutation,
    resetUpdateMutation,
    salesOrderId,
  ]);

  useEffect(() => {
    if (
      !open
      ||
      !salesOrderId
      ||
      !salesOrderQuery.data
    ) {
      return;
    }

    const salesOrder =
      salesOrderQuery.data;

    const customerLabel =
      `${salesOrder.customer.code} — ${salesOrder.customer.name}`;

    queueMicrotask(() => {
      setCustomerSearch(
        customerLabel,
      );

      setSelectedCustomerLabel(
        customerLabel,
      );
    });

    reset({
      customer_id:
        salesOrder.customer.id,
      warehouse_id:
        salesOrder.warehouse.id,
      order_date:
        dateInputValue(
          salesOrder.order_date
        ),
      expected_delivery_date:
        dateInputValue(
          salesOrder
            .expected_delivery_date
        ),
      notes:
        salesOrder.notes
        ??
        "",
      items:
        salesOrder.items.map(
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
  }, [
    open,
    reset,
    salesOrderId,
    salesOrderQuery.data,
  ]);

  useEffect(() => {
    if (
      !open
      ||
      !salesOrderId
      ||
      !salesOrderQuery.data
      ||
      fields.length === 0
    ) {
      return;
    }

    const salesOrder =
      salesOrderQuery.data;

    if (
      fields.length
      !==
      salesOrder.items.length
    ) {
      return;
    }

    const searches:
      Record<string, string> = {};

    const labels:
      Record<string, string> = {};

    fields.forEach(
      (field, index) => {
        const product =
          salesOrder.items[index]
            ?.product;

        if (!product) {
          return;
        }

        const label =
          `${product.sku} — ${product.name}`;

        searches[field.id] =
          label;

        labels[field.id] =
          label;
      },
    );

    queueMicrotask(() => {
      setProductSearches(
        searches,
      );

      setSelectedProductLabels(
        labels,
      );
    });
  }, [
    open,
    salesOrderId,
    salesOrderQuery.data,
    fields,
  ]);

  const customers =
    customerQuery.data
      ?.customers
    ??
    [];

  const customerOptions =
    customers.map(
      (customer) => ({
        id: customer.id,

        label:
          `${customer.code} — ${customer.name}`,

        description:
          [
            customer.phone,
            customer.email,
          ]
            .filter(Boolean)
            .join(" · "),
      }),
    );

  const warehouses =
    warehouseQuery.data
      ?.warehouses
    ??
    [];

  const totals =
    watchedItems.reduce(
      (
        current,
        item,
      ) => {
        const quantity =
          Number(
            item.quantity
          )
          ||
          0;

        const unitPrice =
          Number(
            item.unit_price
          )
          ||
          0;

        const taxRate =
          Number(
            item.tax_rate
          )
          ||
          0;

        const discount =
          Number(
            item.discount
          )
          ||
          0;

        const subtotal =
          quantity
          *
          unitPrice;

        const taxable =
          Math.max(
            subtotal
            -
            discount,
            0,
          );

        const tax =
          taxable
          *
          taxRate
          /
          100;

        return {
          subtotal:
            current.subtotal
            +
            subtotal,
          discount:
            current.discount
            +
            discount,
          tax:
            current.tax
            +
            tax,
          total:
            current.total
            +
            taxable
            +
            tax,
        };
      },
      {
        subtotal: 0,
        discount: 0,
        tax: 0,
        total: 0,
      },
    );

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
      | "customer_id"
      | "warehouse_id"
      | "order_date"
      | "expected_delivery_date"
      | "items"
      | "notes"
    > = [
      "customer_id",
      "warehouse_id",
      "order_date",
      "expected_delivery_date",
      "items",
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

  async function submit(
    values: SalesOrderFormValues,
  ): Promise<void> {
    const input = {
      customer_id:
        values.customer_id,
      warehouse_id:
        values.warehouse_id,
      order_date:
        values.order_date,
      expected_delivery_date:
        values.expected_delivery_date
        ||
        undefined,
      items:
        values.items,
      notes:
        values.notes,
    };

    try {
      if (salesOrderId) {
        await updateMutation.mutateAsync({
          salesOrderId,
          input,
        });
      } else {
        await createMutation.mutateAsync(
          input
        );
      }

      onClose();

    } catch (error) {
      if (
        error instanceof APIRequestError
      ) {
        applyServerErrors(
          error
        );
      }
    }
  }

  if (!open) {
    return null;
  }

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

  const lookupPending =
    warehouseQuery.isPending;

  return (
    <>
      <div
        role="presentation"
      className="
        fixed inset-0 z-50
        flex items-center justify-center
        bg-slate-950/50 p-3
        sm:p-4
      "
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="sales-order-dialog-title"
        className="
          max-h-[94vh] w-full
          max-w-6xl overflow-y-auto
          rounded-2xl bg-white
          text-slate-900 shadow-2xl
        "
      >
        <div
          className="
            sticky top-0 z-10
            flex items-start justify-between
            border-b border-slate-200
            bg-white p-5
          "
        >
          <div>
            <h2
              id="sales-order-dialog-title"
              className="text-xl font-bold"
            >
              {isEditing
                ? "Edit sales order"
                : "Create sales order"}
            </h2>

            <p className="mt-1 text-sm text-slate-600">
              Add customer, warehouse,
              delivery, and product details.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close"
            disabled={isPending}
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

        {isEditing
        && salesOrderQuery.isPending ? (
          <div
            className="
              flex min-h-80 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading sales order…
          </div>
        ) : isEditing
        && salesOrderQuery.isError ? (
          <div
            className="
              flex min-h-80 flex-col
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
            className="space-y-6 p-5"
          >
            <div
              className="
                grid gap-4
                md:grid-cols-2
                xl:grid-cols-4
              "
            >
              <div className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Customer
                </span>

                <SearchCombobox
                  value={selectedCustomerLabel}
                  searchValue={customerSearch}
                  options={customerOptions}
                  placeholder="Search customer name, phone, email or code"
                  minimumSearchLength={3}
                  disabled={isPending}
                  isLoading={
                    normalizedCustomerSearch.length >= 3
                    &&
                    customerQuery.isFetching
                  }
                  emptyMessage="No matching customers found."
                  canCreate={
                    canCreateCustomer
                  }
                  createLabel={
                    `Create "${normalizedCustomerSearch}"`
                  }
                  onCreate={() => {
                    setCustomerDialogOpen(true);
                  }}
                  onSearchChange={(value) => {
                    setCustomerSearch(
                      value,
                    );

                    if (
                      value
                      !==
                      selectedCustomerLabel
                    ) {
                      setSelectedCustomerLabel("");

                      setValue(
                        "customer_id",
                        "",
                        {
                          shouldValidate: true,
                        },
                      );
                    }
                  }}
                  onSelect={(option) => {
                    setValue(
                      "customer_id",
                      option.id,
                      {
                        shouldValidate: true,
                        shouldDirty: true,
                      },
                    );

                    setCustomerSearch(
                      option.label,
                    );

                    setSelectedCustomerLabel(
                      option.label,
                    );
                  }}
                  onClear={() => {
                    setValue(
                      "customer_id",
                      "",
                      {
                        shouldValidate: true,
                        shouldDirty: true,
                      },
                    );

                    setCustomerSearch("");
                    setSelectedCustomerLabel("");
                    setProductSearches({});
                    setSelectedProductLabels({});
                  }}
                />

                {errors.customer_id ? (
                  <p className="text-sm text-red-600">
                    {errors.customer_id.message}
                  </p>
                ) : null}
              </div>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Warehouse
                </span>

                <SearchSelect
                  {...register("warehouse_id")}
                  disabled={
                    isPending
                    ||
                    lookupPending
                  }
                  className={inputClassName}
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
                  <p className="text-sm text-red-600">
                    {errors.warehouse_id.message}
                  </p>
                ) : null}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Order date
                </span>

                <input
                  {...register("order_date")}
                  type="date"
                  disabled={isPending}
                  className={inputClassName}
                />

                {errors.order_date ? (
                  <p className="text-sm text-red-600">
                    {errors.order_date.message}
                  </p>
                ) : null}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Expected delivery
                </span>

                <input
                  {...register(
                    "expected_delivery_date"
                  )}
                  type="date"
                  disabled={isPending}
                  className={inputClassName}
                />

                {errors.expected_delivery_date ? (
                  <p className="text-sm text-red-600">
                    {
                      errors
                        .expected_delivery_date
                        .message
                    }
                  </p>
                ) : null}
              </label>
            </div>

            <section className="space-y-3">
              <div
                className="
                  flex items-center justify-between
                "
              >
                <div>
                  <h3 className="font-bold">
                    Order items
                  </h3>

                  <p className="text-sm text-slate-500">
                    Totals are recalculated
                    by the backend.
                  </p>
                </div>

                <button title="Add item"
                  type="button"
                  disabled={isPending}
                  onClick={() => {
                    append({
                      ...emptyItem,
                    });
                  }}
                  className="
                    inline-flex items-center gap-2
                    rounded-lg bg-blue-50
                    px-3 py-2 text-sm
                    font-semibold text-blue-700
                    hover:bg-blue-100
                    disabled:opacity-50
                  "
                >
                  <Plus size={17} /><span className="sr-only">Add item</span></button>
              </div>

              <div className="space-y-3">
                {fields.map(
                  (
                    field,
                    index,
                  ) => {
                    const item =
                      watchedItems[index];

                    const quantity =
                      Number(
                        item?.quantity
                      )
                      ||
                      0;

                    const unitPrice =
                      Number(
                        item?.unit_price
                      )
                      ||
                      0;

                    const taxRate =
                      Number(
                        item?.tax_rate
                      )
                      ||
                      0;

                    const discount =
                      Number(
                        item?.discount
                      )
                      ||
                      0;

                    const subtotal =
                      quantity
                      *
                      unitPrice;

                    const taxable =
                      Math.max(
                        subtotal
                        -
                        discount,
                        0,
                      );

                    const lineTotal =
                      taxable
                      +
                      taxable
                      *
                      taxRate
                      /
                      100;

                    return (
                      <div
                        key={field.id}
                        className="
                          grid gap-3 rounded-xl
                          border border-slate-200
                          bg-slate-50 p-3
                          lg:grid-cols-12
                        "
                      >
                        <label
                          className="
                            space-y-1
                            lg:col-span-4
                          "
                        >
                          <span className="text-xs font-semibold">
                            Product
                          </span>

                          <SalesOrderProductSearch
                            value={
                              selectedProductLabels[
                                field.id
                              ]
                              ??
                              ""
                            }
                            searchValue={
                              productSearches[
                                field.id
                              ]
                              ??
                              ""
                            }
                            disabled={isPending}
                            canCreateProduct={
                              canCreateProduct
                            }
                            onCreate={() => {
                              setProductCreateFieldId(
                                field.id,
                              );
                              setProductDialogOpen(
                                true,
                              );
                            }}
                            onSearchChange={(value) => {
                              setProductSearches(
                                (current) => ({
                                  ...current,
                                  [field.id]: value,
                                }),
                              );

                              if (
                                value
                                !==
                                selectedProductLabels[
                                  field.id
                                ]
                              ) {
                                setSelectedProductLabels(
                                  (current) => ({
                                    ...current,
                                    [field.id]: "",
                                  }),
                                );

                                setValue(
                                  `items.${index}.product_id`,
                                  "",
                                  {
                                    shouldValidate: true,
                                    shouldDirty: true,
                                  },
                                );
                              }
                            }}
                            onSelect={(product) => {
                              const productLabel =
                                `${product.sku} — ${product.name}`;

                              setValue(
                                `items.${index}.product_id`,
                                product.id,
                                {
                                  shouldValidate: true,
                                  shouldDirty: true,
                                },
                              );

                              setValue(
                                `items.${index}.unit_price`,
                                product.selling_price,
                                {
                                  shouldValidate: true,
                                  shouldDirty: true,
                                },
                              );

                              setProductSearches(
                                (current) => ({
                                  ...current,
                                  [field.id]:
                                    productLabel,
                                }),
                              );

                              setSelectedProductLabels(
                                (current) => ({
                                  ...current,
                                  [field.id]:
                                    productLabel,
                                }),
                              );
                            }}
                            onClear={() => {
                              setValue(
                                `items.${index}.product_id`,
                                "",
                                {
                                  shouldValidate: true,
                                  shouldDirty: true,
                                },
                              );

                              setProductSearches(
                                (current) => ({
                                  ...current,
                                  [field.id]: "",
                                }),
                              );

                              setSelectedProductLabels(
                                (current) => ({
                                  ...current,
                                  [field.id]: "",
                                }),
                              );
                            }}
                          />

                          {errors.items?.[index]
                            ?.product_id ? (
                            <p className="text-xs text-red-600">
                              {
                                errors.items[index]
                                  ?.product_id
                                  ?.message
                              }
                            </p>
                          ) : null}
                        </label>

                        {[
                          [
                            "quantity",
                            "Quantity",
                          ],
                          [
                            "unit_price",
                            "Unit price",
                          ],
                          [
                            "tax_rate",
                            "Tax %",
                          ],
                          [
                            "discount",
                            "Discount",
                          ],
                        ].map(
                          ([
                            name,
                            label,
                          ]) => (
                            <label
                              key={name}
                              className="
                                space-y-1
                                lg:col-span-1
                              "
                            >
                              <span className="text-xs font-semibold">
                                {label}
                              </span>

                              <input
                                {...register(
                                  `items.${index}.${name as "quantity" | "unit_price" | "tax_rate" | "discount"}`
                                )}
                                type="number"
                                min="0"
                                step="0.01"
                                disabled={isPending}
                                className={inputClassName}
                              />
                            </label>
                          ),
                        )}

                        <div
                          className="
                            flex items-end
                            justify-between gap-3
                            lg:col-span-3
                          "
                        >
                          <div>
                            <p className="text-xs text-slate-500">
                              Line total
                            </p>

                            <p className="font-bold">
                              {lineTotal.toFixed(
                                2
                              )}
                            </p>
                          </div>

                          <button
                            type="button"
                            aria-label="Remove item"
                            disabled={
                              isPending
                              ||
                              fields.length === 1
                            }
                            onClick={() => {
                              remove(index);
                            }}
                            className="
                              rounded-lg p-2
                              text-red-600
                              hover:bg-red-50
                              disabled:opacity-30
                            "
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </div>
                    );
                  },
                )}
              </div>

              {errors.items
              && !Array.isArray(
                errors.items
              ) ? (
                <p className="text-sm text-red-600">
                  {errors.items.message}
                </p>
              ) : null}
            </section>

            <div
              className="
                grid gap-5
                lg:grid-cols-[1fr_320px]
              "
            >
              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Notes
                </span>

                <textarea
                  {...register("notes")}
                  rows={5}
                  disabled={isPending}
                  placeholder="Optional order notes"
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

                {errors.notes ? (
                  <p className="text-sm text-red-600">
                    {errors.notes.message}
                  </p>
                ) : null}
              </label>

              <div
                className="
                  space-y-2 rounded-xl
                  bg-slate-900 p-4
                  text-sm text-white
                "
              >
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span>
                    {totals.subtotal.toFixed(2)}
                  </span>
                </div>

                <div className="flex justify-between">
                  <span>Discount</span>
                  <span>
                    -{totals.discount.toFixed(2)}
                  </span>
                </div>

                <div className="flex justify-between">
                  <span>Tax</span>
                  <span>
                    {totals.tax.toFixed(2)}
                  </span>
                </div>

                <div
                  className="
                    flex justify-between
                    border-t border-slate-700
                    pt-2 text-base font-bold
                  "
                >
                  <span>Total</span>
                  <span>
                    {totals.total.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            {generalError ? (
              <p
                className="
                  rounded-lg bg-red-50
                  px-4 py-3 text-sm
                  text-red-700
                "
              >
                {generalError}
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
                disabled={isPending}
                onClick={onClose}
                className="
                  rounded-lg border
                  border-slate-300 px-4
                  py-2 text-sm font-semibold
                  text-slate-700
                  hover:bg-slate-50
                "
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={
                  isPending
                  ||
                  lookupPending
                }
                className="
                  rounded-lg bg-blue-600
                  px-4 py-2 text-sm
                  font-semibold text-white
                  hover:bg-blue-700
                  disabled:opacity-50
                "
              >
                {isPending
                  ? "Saving…"
                  : isEditing
                    ? "Save changes"
                    : "Create sales order"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
    <CustomerDialog
      open={customerDialogOpen}
      customerId={null}
      onClose={() => {
        setCustomerDialogOpen(false);
      }}
      onCreated={(customer) => {
        const customerLabel =
          `${customer.code} — ${customer.name}`;

        setValue(
          "customer_id",
          customer.id,
          {
            shouldValidate: true,
            shouldDirty: true,
          },
        );

        setCustomerSearch(
          customerLabel,
        );

        setSelectedCustomerLabel(
          customerLabel,
        );

        setCustomerDialogOpen(false);
      }}
    />
    <ProductDialog
      open={productDialogOpen}
      productId={null}
      onClose={() => {
        setProductDialogOpen(false);
        setProductCreateFieldId(null);
      }}
      onCreated={(product: ProductDetail) => {
        if (!productCreateFieldId) {
          setProductDialogOpen(false);
          return;
        }

        const productIndex =
          fields.findIndex(
            (field) =>
              field.id
              ===
              productCreateFieldId,
          );

        if (productIndex === -1) {
          setProductDialogOpen(false);
          setProductCreateFieldId(null);
          return;
        }

        const productLabel =
          `${product.sku} — ${product.name}`;

        setValue(
          `items.${productIndex}.product_id`,
          product.id,
          {
            shouldValidate: true,
            shouldDirty: true,
          },
        );

        setValue(
          `items.${productIndex}.unit_price`,
          product.selling_price,
          {
            shouldValidate: true,
            shouldDirty: true,
          },
        );

        setProductSearches(
          (current) => ({
            ...current,
            [productCreateFieldId]:
              productLabel,
          }),
        );

        setSelectedProductLabels(
          (current) => ({
            ...current,
            [productCreateFieldId]:
              productLabel,
          }),
        );

        setProductDialogOpen(false);
        setProductCreateFieldId(null);
      }}
    />
  </>
);
}
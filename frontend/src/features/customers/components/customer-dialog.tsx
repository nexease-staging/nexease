"use client";
import GstLookup from "@/features/business/gst-lookup";

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
  useCreateCustomer,
  useCustomer,
  useUpdateCustomer,
} from "@/features/customers/hooks";

import type {
  CustomerDetail,
} from "@/features/customers/types";

import {
  APIRequestError,
} from "@/lib/api/client";

const customerSchema = z.object({
  code: z
    .string()
    .trim()
    .min(
      1,
      "Customer code is required.",
    )
    .max(
      50,
      "Code cannot exceed 50 characters.",
    ),

  name: z
    .string()
    .trim()
    .min(
      1,
      "Customer name is required.",
    )
    .max(
      200,
      "Name cannot exceed 200 characters.",
    ),

  email: z.union([
    z.literal(""),
    z.email(
      "Enter a valid email address.",
    ),
  ]),

  phone: z
    .string()
    .trim()
    .max(
      30,
      "Phone cannot exceed 30 characters.",
    ),

  gstin: z
    .string()
    .trim()
    .max(
      20,
      "GSTIN cannot exceed 20 characters.",
    ),

  billing_address: z
    .string()
    .trim()
    .max(
      500,
      "Billing address cannot exceed 500 characters.",
    ),

  shipping_address: z
    .string()
    .trim()
    .max(
      500,
      "Shipping address cannot exceed 500 characters.",
    ),

  city: z
    .string()
    .trim()
    .max(
      100,
      "City cannot exceed 100 characters.",
    ),

  state: z
    .string()
    .trim()
    .max(
      100,
      "State cannot exceed 100 characters.",
    ),

  country: z
    .string()
    .trim()
    .max(
      100,
      "Country cannot exceed 100 characters.",
    ),

  pincode: z
    .string()
    .trim()
    .max(
      20,
      "Pincode cannot exceed 20 characters.",
    ),
});

type CustomerFormValues =
  z.infer<typeof customerSchema>;

const emptyValues: CustomerFormValues = {
  code: "AUTO",
  name: "",
  email: "",
  phone: "",
  gstin: "",
  billing_address: "",
  shipping_address: "",
  city: "",
  state: "",
  country: "India",
  pincode: "AUTO",
};

const inputClassName = `
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
`;

const textareaClassName = `
  w-full resize-y rounded-lg
  border border-slate-300
  bg-white px-3 py-2 text-sm
  text-slate-900
  placeholder:text-slate-400
  outline-none
  focus:border-blue-500
  focus:ring-2
  focus:ring-blue-100
  disabled:opacity-50
`;

interface CustomerDialogProps {
  open: boolean;
  customerId: string | null;
  onClose: () => void;
  onCreated?: (
    customer: CustomerDetail,
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

export default function CustomerDialog({
  open,
  customerId,
  onClose,
  onCreated,
}: CustomerDialogProps) {
  const isEditing =
    Boolean(customerId);

  const customerQuery =
    useCustomer(
      customerId ?? "",
      open && isEditing,
    );

  const createMutation =
    useCreateCustomer();

  const updateMutation =
    useUpdateCustomer();

  const resetCreateMutation =
    createMutation.reset;

  const resetUpdateMutation =
    updateMutation.reset;

  const {
    setValue,
    register,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<CustomerFormValues>({
    resolver:
      zodResolver(
        customerSchema,
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

    if (!customerId) {
      reset(
        emptyValues,
      );
    }
  }, [
    customerId,
    open,
    reset,
    resetCreateMutation,
    resetUpdateMutation,
  ]);

  useEffect(() => {
    if (
      !open
      ||
      !customerId
      ||
      !customerQuery.data
    ) {
      return;
    }

    const customer =
      customerQuery.data;

    reset({
      code:
        customer.code,
      name:
        customer.name,
      email:
        customer.email
        ??
        "",
      phone:
        customer.phone
        ??
        "",
      gstin:
        customer.gstin
        ??
        "",
      billing_address:
        customer.billing_address
        ??
        "",
      shipping_address:
        customer.shipping_address
        ??
        "",
      city:
        customer.city
        ??
        "",
      state:
        customer.state
        ??
        "",
      country:
        customer.country
        ??
        "India",
      pincode:
        customer.pincode
        ??
        "",
    });
  }, [
    customerId,
    customerQuery.data,
    open,
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
      keyof CustomerFormValues
    > = [
      "code",
      "name",
      "email",
      "phone",
      "gstin",
      "billing_address",
      "shipping_address",
      "city",
      "state",
      "country",
      "pincode",
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
    values: CustomerFormValues,
  ): Promise<void> {
    const editableInput = {
      name:
        values.name,
      email:
        values.email,
      phone:
        values.phone,
      gstin:
        values.gstin,
      billing_address:
        values.billing_address,
      shipping_address:
        values.shipping_address,
      city:
        values.city,
      state:
        values.state,
      country:
        values.country
        ||
        "India",
      pincode:
        values.pincode,
    };

    try {
      if (customerId) {
        await updateMutation.mutateAsync({
          customerId,
          input:
            editableInput,
        });
      } else {
        const createdCustomer =
          await createMutation.mutateAsync({
            code:
              values.code,
            ...editableInput,
          });

        onCreated?.(
          createdCustomer,
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

  const fieldError = (
    message: string | undefined,
  ) => (
    message
      ? (
        <p className="text-sm text-red-600">
          {message}
        </p>
      )
      : null
  );

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
        aria-labelledby="customer-dialog-title"
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
              id="customer-dialog-title"
              className="
                text-xl font-bold
                text-slate-900
              "
            >
              {
                isEditing
                  ? "Edit customer"
                  : "Create customer"
              }
            </h2>

            <p className="mt-1 text-sm text-slate-600">
              Manage customer identity,
              tax, contact, and address details.
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
              disabled:opacity-50
            "
          >
            <X size={20} />
          </button>
        </div>

        {isEditing
        && customerQuery.isPending ? (
          <div
            className="
              flex min-h-72 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading customer…
          </div>
        ) : isEditing
        && customerQuery.isError ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              gap-3 p-6
            "
          >
            <p className="text-sm text-red-700">
              {customerQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void customerQuery.refetch();
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
          ><div className="p-4"><GstLookup onSelect={r=>{for(const k of ['name','gstin','state','email','phone'] as const){if(r[k])setValue(k,r[k],{shouldValidate:true});}if(r.address)setValue('billing_address',r.address,{shouldValidate:true});}}/></div>
            <div
              className="
                grid gap-4 md:grid-cols-2
              "
            >
              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Customer code
                </span>

                <input
                  {...register("code")}
                  type="text"
                  placeholder="CUST-001"
                  disabled={
                    isPending
                    ||
                    isEditing
                  }
                  className={inputClassName}
                />

                {fieldError(
                  errors.code?.message,
                )}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Customer name
                </span>

                <input
                  {...register("name")}
                  type="text"
                  placeholder="Customer name"
                  disabled={isPending}
                  className={inputClassName}
                />

                {fieldError(
                  errors.name?.message,
                )}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Email
                </span>

                <input
                  {...register("email")}
                  type="email"
                  placeholder="customer@example.com"
                  disabled={isPending}
                  className={inputClassName}
                />

                {fieldError(
                  errors.email?.message,
                )}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Phone
                </span>

                <input
                  {...register("phone")}
                  type="text"
                  placeholder="Phone number"
                  disabled={isPending}
                  className={inputClassName}
                />

                {fieldError(
                  errors.phone?.message,
                )}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  GSTIN
                </span>

                <input
                  {...register("gstin")}
                  type="text"
                  placeholder="Optional GSTIN"
                  disabled={isPending}
                  className={inputClassName}
                />

                {fieldError(
                  errors.gstin?.message,
                )}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Pincode
                </span>

                <input
                  {...register("pincode")}
                  type="text"
                  placeholder="Pincode"
                  disabled={isPending}
                  className={inputClassName}
                />

                {fieldError(
                  errors.pincode?.message,
                )}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  City
                </span>

                <input
                  {...register("city")}
                  type="text"
                  placeholder="City"
                  disabled={isPending}
                  className={inputClassName}
                />

                {fieldError(
                  errors.city?.message,
                )}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  State
                </span>

                <input
                  {...register("state")}
                  type="text"
                  placeholder="State"
                  disabled={isPending}
                  className={inputClassName}
                />

                {fieldError(
                  errors.state?.message,
                )}
              </label>

              <label
                className="
                  space-y-1.5 md:col-span-2
                "
              >
                <span className="text-sm font-semibold">
                  Country
                </span>

                <input
                  {...register("country")}
                  type="text"
                  placeholder="India"
                  disabled={isPending}
                  className={inputClassName}
                />

                {fieldError(
                  errors.country?.message,
                )}
              </label>
            </div>

            <div
              className="
                grid gap-4 md:grid-cols-2
              "
            >
              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Billing address
                </span>

                <textarea
                  {...register(
                    "billing_address",
                  )}
                  rows={4}
                  placeholder="Billing address"
                  disabled={isPending}
                  className={
                    textareaClassName
                  }
                />

                {fieldError(
                  errors
                    .billing_address
                    ?.message,
                )}
              </label>

              <label className="space-y-1.5">
                <span className="text-sm font-semibold">
                  Shipping address
                </span>

                <textarea
                  {...register(
                    "shipping_address",
                  )}
                  rows={4}
                  placeholder="Shipping address"
                  disabled={isPending}
                  className={
                    textareaClassName
                  }
                />

                {fieldError(
                  errors
                    .shipping_address
                    ?.message,
                )}
              </label>
            </div>

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
                  disabled:opacity-50
                "
              >
                {
                  isPending
                    ? "Saving…"
                    : isEditing
                      ? "Save changes"
                      : "Create customer"
                }
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
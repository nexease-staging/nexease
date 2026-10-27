"use client";

import {
  useEffect,
} from "react";

import {
  LoaderCircle,
  X,
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
  APIRequestError,
} from "@/lib/api/client";

import {
  useCreateWarehouse,
  useUpdateWarehouse,
} from "@/features/warehouses/hooks";

import type {
  WarehouseDetail,
} from "@/features/warehouses/types";

const warehouseSchema = z.object({
  name: z
    .string()
    .trim()
    .min(
      1,
      "Warehouse name is required.",
    )
    .max(
      150,
      "Use no more than 150 characters.",
    ),

  code: z
    .string()
    .trim()
    .min(
      1,
      "Warehouse code is required.",
    )
    .max(
      50,
      "Use no more than 50 characters.",
    ),

  address: z
    .string()
    .trim()
    .max(
      500,
      "Use no more than 500 characters.",
    ),

  city: z
    .string()
    .trim()
    .max(
      100,
      "Use no more than 100 characters.",
    ),

  state: z
    .string()
    .trim()
    .max(
      100,
      "Use no more than 100 characters.",
    ),

  country: z
    .string()
    .trim()
    .max(
      100,
      "Use no more than 100 characters.",
    ),

  pincode: z
    .string()
    .trim()
    .max(
      20,
      "Use no more than 20 characters.",
    ),
});

type WarehouseFormValues =
  z.infer<typeof warehouseSchema>;

interface WarehouseFormDialogProps {
  open: boolean;
  warehouse?: WarehouseDetail | null;
  onClose: () => void;
}

const emptyValues: WarehouseFormValues = {
  name: "",
  code: "AUTO",
  address: "",
  city: "",
  state: "",
  country: "India",
  pincode: "AUTO",
};

export default function WarehouseFormDialog({
  open,
  warehouse,
  onClose,
}: WarehouseFormDialogProps) {
  const createMutation =
    useCreateWarehouse();

  const updateMutation =
    useUpdateWarehouse();

  const isEditing = Boolean(
    warehouse,
  );

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<WarehouseFormValues>({
    resolver:
      zodResolver(
        warehouseSchema,
      ),
    defaultValues:
      emptyValues,
  });

  useEffect(() => {
    if (!open) {
      return;
    }

    reset(
      warehouse
        ? {
            name:
              warehouse.name,
            code:
              warehouse.code,
            address:
              warehouse.address
              ??
              "",
            city:
              warehouse.city
              ??
              "",
            state:
              warehouse.state
              ??
              "",
            country:
              warehouse.country
              ??
              "India",
            pincode:
              warehouse.pincode
              ??
              "",
          }
        : emptyValues,
    );
  }, [
    open,
    reset,
    warehouse,
  ]);

  const isPending =
    createMutation.isPending
    ||
    updateMutation.isPending;

  const mutationError =
    createMutation.error
    ??
    updateMutation.error;

  async function submit(
    values: WarehouseFormValues,
  ): Promise<void> {
    try {
      if (warehouse) {
        await updateMutation.mutateAsync({
          warehouseId:
            warehouse.id,
          input:
            values,
        });
      } else {
        await createMutation.mutateAsync(
          values,
        );
      }

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
          "name",
          "code",
          "address",
          "city",
          "state",
          "country",
          "pincode",
        ] as const;

        let fieldErrorApplied = false;

        for (
          const field
          of fieldNames
        ) {
          const fieldMessages =
            error.details
              ?.[field];

          if (
            Array.isArray(
              fieldMessages
            )
            &&
            typeof fieldMessages[0]
            ===
            "string"
          ) {
            setError(
              field,
              {
                type: "server",
                message:
                  fieldMessages[0],
              },
            );

            fieldErrorApplied = true;
          }
        }

        if (!fieldErrorApplied) {
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
            "Unable to save the "
            +
            "warehouse."
          ),
        },
      );
    }
  }

  if (!open) {
    return null;
  }

  return (
    <div
      className="
        fixed inset-0 z-50
        flex items-center
        justify-center bg-slate-950/50
        p-4
      "
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target
          ===
          event.currentTarget
          &&
          !isPending
        ) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={
          "warehouse-dialog-title"
        }
        className="
          max-h-[90vh] w-full
          max-w-2xl overflow-y-auto
          rounded-2xl bg-white
          shadow-2xl
        "
      >
        <header
          className="
            flex items-center
            justify-between border-b
            border-slate-200 px-6 py-4
          "
        >
          <div>
            <h2
              id="warehouse-dialog-title"
              className="
                text-lg font-bold
                text-slate-900
              "
            >
              {isEditing
                ? "Edit warehouse"
                : "Create warehouse"}
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-500
              "
            >
              {isEditing
                ? (
                  "Update this storage "
                  +
                  "location."
                )
                : (
                  "Add a storage location "
                  +
                  "to your organization."
                )}
            </p>
          </div>

          <button
            type="button"
            aria-label="Close dialog"
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
        </header>

        <form
          onSubmit={(event) => {
            void handleSubmit(
              submit,
            )(event);
          }}
          className="space-y-5 p-6"
        >
          {errors.root?.server
          ||
          mutationError ? (
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
                  ?.server
                  ?.message
                ??
                mutationError
                  ?.message
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
                Name
              </span>

              <input
                {...register("name")}
                autoFocus
                className="
                  h-10 w-full rounded-lg
                  border border-slate-300
                  px-3 text-sm outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />

              {errors.name ? (
                <p className="text-xs text-red-600">
                  {errors.name.message}
                </p>
              ) : null}
            </label>

            <label className="space-y-1.5">
              <span
                className="
                  text-sm font-semibold
                  text-slate-700
                "
              >
                Code
              </span>

              <input
                {...register("code")}
                className="
                  h-10 w-full rounded-lg
                  border border-slate-300
                  px-3 text-sm uppercase
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />

              {errors.code ? (
                <p className="text-xs text-red-600">
                  {errors.code.message}
                </p>
              ) : null}
            </label>
          </div>

          <label className="block space-y-1.5">
            <span
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Address
            </span>

            <textarea
              {...register("address")}
              rows={3}
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

            {errors.address ? (
              <p className="text-xs text-red-600">
                {errors.address.message}
              </p>
            ) : null}
          </label>

          <div
            className="
              grid gap-4 sm:grid-cols-2
            "
          >
            {[
              {
                field:
                  "city" as const,
                label:
                  "City",
              },
              {
                field:
                  "state" as const,
                label:
                  "State",
              },
              {
                field:
                  "country" as const,
                label:
                  "Country",
              },
              {
                field:
                  "pincode" as const,
                label:
                  "Pincode",
              },
            ].map(
              ({
                field,
                label,
              }) => (
                <label
                  key={field}
                  className="space-y-1.5"
                >
                  <span
                    className="
                      text-sm font-semibold
                      text-slate-700
                    "
                  >
                    {label}
                  </span>

                  <input
                    {...register(field)}
                    className="
                      h-10 w-full rounded-lg
                      border border-slate-300
                      px-3 text-sm outline-none
                      focus:border-blue-500
                      focus:ring-2
                      focus:ring-blue-100
                    "
                  />

                  {errors[field] ? (
                    <p
                      className="
                        text-xs text-red-600
                      "
                    >
                      {
                        errors[field]
                          ?.message
                      }
                    </p>
                  ) : null}
                </label>
              ),
            )}
          </div>

          <footer
            className="
              flex justify-end gap-3
              border-t border-slate-200
              pt-5
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
                inline-flex items-center
                gap-2 rounded-lg
                bg-blue-600 px-4 py-2
                text-sm font-semibold
                text-white
                hover:bg-blue-700
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              {isPending ? (
                <LoaderCircle
                  size={16}
                  className="animate-spin"
                />
              ) : null}

              {isEditing
                ? "Save changes"
                : "Create warehouse"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}
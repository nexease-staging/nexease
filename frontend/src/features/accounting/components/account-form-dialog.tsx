"use client";
import SearchSelect from "@/components/search-select";


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
  useCreateChartOfAccount,
  useUpdateChartOfAccount,
} from "@/features/accounting/hooks";

import type {
  AccountType,
  ChartOfAccountDetail,
} from "@/features/accounting/types";

import {
  APIRequestError,
} from "@/lib/api/client";

const accountTypes:
  Array<{
    value: AccountType;
    label: string;
  }> = [
    {
      value: "ASSET",
      label: "Asset",
    },
    {
      value: "LIABILITY",
      label: "Liability",
    },
    {
      value: "EQUITY",
      label: "Equity",
    },
    {
      value: "REVENUE",
      label: "Revenue",
    },
    {
      value: "EXPENSE",
      label: "Expense",
    },
  ];

const accountSchema = z.object({
  account_code: z
    .string()
    .trim()
    .min(
      1,
      "Account code is required.",
    )
    .max(
      30,
      "Use no more than 30 characters.",
    ),

  account_name: z
    .string()
    .trim()
    .min(
      1,
      "Account name is required.",
    )
    .max(
      150,
      "Use no more than 150 characters.",
    ),

  account_type: z.enum([
    "ASSET",
    "LIABILITY",
    "EQUITY",
    "REVENUE",
    "EXPENSE",
  ]),

  account_subtype: z
    .string()
    .trim()
    .max(
      50,
      "Use no more than 50 characters.",
    ),

  description: z
    .string()
    .trim()
    .max(
      500,
      "Use no more than 500 characters.",
    ),

  allow_manual_posting:
    z.boolean(),
});

type AccountFormValues =
  z.infer<typeof accountSchema>;

interface AccountFormDialogProps {
  open: boolean;
  account?:
    ChartOfAccountDetail | null;
  onClose: () => void;
}

const emptyValues:
  AccountFormValues = {
    account_code: "",
    account_name: "",
    account_type: "ASSET",
    account_subtype: "",
    description: "",
    allow_manual_posting: true,
  };

export default function AccountFormDialog({
  open,
  account,
  onClose,
}: AccountFormDialogProps) {
  const createMutation =
    useCreateChartOfAccount();

  const updateMutation =
    useUpdateChartOfAccount();

  const isEditing = Boolean(
    account,
  );

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<AccountFormValues>({
    resolver:
      zodResolver(
        accountSchema,
      ),
    defaultValues:
      emptyValues,
  });

  useEffect(() => {
    if (!open) {
      return;
    }

    reset(
      account
        ? {
            account_code:
              account.account_code,
            account_name:
              account.account_name,
            account_type:
              account.account_type,
            account_subtype:
              account.account_subtype
              ??
              "",
            description:
              account.description
              ??
              "",
            allow_manual_posting:
              account
                .allow_manual_posting,
          }
        : emptyValues,
    );
  }, [
    account,
    open,
    reset,
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
    values: AccountFormValues,
  ): Promise<void> {
    try {
      if (account) {
        await updateMutation
          .mutateAsync({
            accountId:
              account.id,
            input: {
              account_name:
                values.account_name,
              account_subtype:
                values.account_subtype,
              description:
                values.description,
              allow_manual_posting:
                values
                  .allow_manual_posting,
            },
          });
      } else {
        await createMutation
          .mutateAsync(
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
          "account_code",
          "account_name",
          "account_type",
          "account_subtype",
          "description",
          "allow_manual_posting",
        ] as const;

        let fieldErrorApplied =
          false;

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

            fieldErrorApplied =
              true;
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
            "chart of account."
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
          "account-form-title"
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
              id="account-form-title"
              className="
                text-lg font-bold
                text-slate-900
              "
            >
              {isEditing
                ? "Edit account"
                : "Create account"}
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-500
              "
            >
              {isEditing
                ? (
                  "Update the editable "
                  +
                  "account settings."
                )
                : (
                  "Add an account to your "
                  +
                  "organization ledger."
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
          className="
            space-y-5 p-6
            text-slate-900
          "
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
              grid gap-5 sm:grid-cols-2
            "
          >
            <label
              className="
                block text-sm font-medium
                text-slate-700
              "
            >
              Account code

              <input
                {...register(
                  "account_code"
                )}
                disabled={
                  isEditing
                  ||
                  isPending
                }
                autoComplete="off"
                className="
                  mt-2 w-full rounded-lg
                  border border-slate-300
                  px-3 py-2 text-sm
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                  disabled:bg-slate-100
                  disabled:text-slate-500
                "
              />

              {errors.account_code ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors
                      .account_code
                      .message
                  }
                </span>
              ) : null}
            </label>

            <label
              className="
                block text-sm font-medium
                text-slate-700
              "
            >
              Account type

              <SearchSelect
                {...register(
                  "account_type"
                )}
                disabled={
                  isEditing
                  ||
                  isPending
                }
                className="
                  mt-2 w-full rounded-lg
                  border border-slate-300
                  bg-white px-3 py-2
                  text-sm outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                  disabled:bg-slate-100
                  disabled:text-slate-500
                "
              >
                {accountTypes.map(
                  (item) => (
                    <option
                      key={item.value}
                      value={item.value}
                    >
                      {item.label}
                    </option>
                  ),
                )}
              </SearchSelect>

              {errors.account_type ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors
                      .account_type
                      .message
                  }
                </span>
              ) : null}
            </label>
          </div>

          <label
            className="
              block text-sm font-medium
              text-slate-700
            "
          >
            Account name

            <input
              {...register(
                "account_name"
              )}
              disabled={isPending}
              autoComplete="off"
              className="
                mt-2 w-full rounded-lg
                border border-slate-300
                px-3 py-2 text-sm
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
                disabled:bg-slate-100
              "
            />

            {errors.account_name ? (
              <span
                className="
                  mt-1 block text-xs
                  text-red-600
                "
              >
                {
                  errors
                    .account_name
                    .message
                }
              </span>
            ) : null}
          </label>

          <label
            className="
              block text-sm font-medium
              text-slate-700
            "
          >
            Account subtype

            <input
              {...register(
                "account_subtype"
              )}
              disabled={isPending}
              autoComplete="off"
              placeholder={
                "For example: CURRENT_ASSET"
              }
              className="
                mt-2 w-full rounded-lg
                border border-slate-300
                px-3 py-2 text-sm
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
                disabled:bg-slate-100
              "
            />

            {errors.account_subtype ? (
              <span
                className="
                  mt-1 block text-xs
                  text-red-600
                "
              >
                {
                  errors
                    .account_subtype
                    .message
                }
              </span>
            ) : null}
          </label>

          <label
            className="
              block text-sm font-medium
              text-slate-700
            "
          >
            Description

            <textarea
              {...register(
                "description"
              )}
              disabled={isPending}
              rows={4}
              className="
                mt-2 w-full resize-y
                rounded-lg border
                border-slate-300 px-3
                py-2 text-sm outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
                disabled:bg-slate-100
              "
            />

            {errors.description ? (
              <span
                className="
                  mt-1 block text-xs
                  text-red-600
                "
              >
                {
                  errors
                    .description
                    .message
                }
              </span>
            ) : null}
          </label>

          <label
            className="
              flex items-start gap-3
              rounded-lg border
              border-slate-200 p-4
            "
          >
            <input
              type="checkbox"
              {...register(
                "allow_manual_posting"
              )}
              disabled={
                isPending
                ||
                Boolean(
                  account
                    ?.is_system_account
                )
              }
              className="
                mt-1 size-4 rounded
                border-slate-300
              "
            />

            <span>
              <span
                className="
                  block text-sm font-semibold
                  text-slate-800
                "
              >
                Allow manual posting
              </span>

              <span
                className="
                  mt-1 block text-xs
                  leading-5 text-slate-500
                "
              >
                Users can select this account
                when creating manual journal
                entries.
              </span>
            </span>
          </label>

          <div
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
                : "Create account"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
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
  useWatch,
} from "react-hook-form";

import {
  zodResolver,
} from "@hookform/resolvers/zod";

import {
  z,
} from "zod";

import {
  useCreateBankAccount,
  useUpdateBankAccount,
} from "@/features/banking/hooks";

import type {
  BankAccountSummary,
} from "@/features/banking/types";

import {
  APIRequestError,
} from "@/lib/api/client";

const accountSchema = z
  .object({
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
      "BANK",
      "CASH",
    ]),

    bank_name: z
      .string()
      .trim()
      .max(
        150,
        "Use no more than 150 characters.",
      ),

    account_number: z
      .string()
      .trim()
      .max(
        100,
        "Use no more than 100 characters.",
      ),

    ifsc_code: z
      .string()
      .trim()
      .max(
        20,
        "Use no more than 20 characters.",
      ),

    currency: z
      .string()
      .trim()
      .min(
        1,
        "Currency is required.",
      )
      .max(
        10,
        "Use no more than 10 characters.",
      ),

    opening_balance: z
      .string()
      .trim()
      .min(
        1,
        "Opening balance is required.",
      )
      .refine(
        (value) => {
          const amount =
            Number(value);

          return (
            Number.isFinite(
              amount,
            )
            &&
            /^\-?\d+(\.\d{1,2})?$/
              .test(
                value,
              )
          );
        },
        (
          "Enter a valid amount with "
          +
          "up to 2 decimal places."
        ),
      ),
  })
  .superRefine(
    (
      values,
      context,
    ) => {
      if (
        values.account_type
        ===
        "BANK"
      ) {
        if (!values.bank_name) {
          context.addIssue({
            code:
              "custom",
            path: [
              "bank_name",
            ],
            message: (
              "Bank name is required "
              +
              "for bank accounts."
            ),
          });
        }

        if (!values.account_number) {
          context.addIssue({
            code:
              "custom",
            path: [
              "account_number",
            ],
            message: (
              "Account number is required "
              +
              "for bank accounts."
            ),
          });
        }
      }

      if (
        values.account_type
        ===
        "CASH"
        &&
        (
          values.bank_name
          ||
          values.account_number
          ||
          values.ifsc_code
        )
      ) {
        context.addIssue({
          code:
            "custom",
          path: [
            "account_type",
          ],
          message: (
            "Cash accounts cannot contain "
            +
            "bank details."
          ),
        });
      }
    },
  );

type BankAccountFormValues =
  z.infer<typeof accountSchema>;

interface BankAccountFormDialogProps {
  open: boolean;
  account?:
    BankAccountSummary | null;
  onClose: () => void;
}

const emptyValues:
  BankAccountFormValues = {
    account_name: "",
    account_type: "BANK",
    bank_name: "",
    account_number: "",
    ifsc_code: "",
    currency: "INR",
    opening_balance: "0.00",
  };

export default function BankAccountFormDialog({
  open,
  account,
  onClose,
}: BankAccountFormDialogProps) {
  const createMutation =
    useCreateBankAccount();

  const updateMutation =
    useUpdateBankAccount();

  const isEditing = Boolean(
    account,
  );

  const {
    register,
    handleSubmit,
    control,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<BankAccountFormValues>({
    resolver:
      zodResolver(
        accountSchema,
      ),
    defaultValues:
      emptyValues,
  });

  const accountType =
    useWatch({
      control,
      name: "account_type",
    });

  useEffect(() => {
    if (!open) {
      return;
    }

    reset(
      account
        ? {
            account_name:
              account.account_name,
            account_type:
              account.account_type,
            bank_name:
              account.bank_name
              ??
              "",
            account_number:
              account.account_number
              ??
              "",
            ifsc_code:
              account.ifsc_code
              ??
              "",
            currency:
              account.currency,
            opening_balance:
              account.opening_balance,
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
    values: BankAccountFormValues,
  ): Promise<void> {
    try {
      if (account) {
        await updateMutation
          .mutateAsync({
            bankAccountId:
              account.id,
            input: {
              account_name:
                values.account_name,
              bank_name:
                values.bank_name,
              account_number:
                values.account_number,
              ifsc_code:
                values.ifsc_code,
            },
          });
      } else {
        await createMutation
          .mutateAsync({
            account_name:
              values.account_name,
            account_type:
              values.account_type,
            bank_name:
              values.bank_name,
            account_number:
              values.account_number,
            ifsc_code:
              values.ifsc_code,
            currency:
              values.currency,
            opening_balance:
              values.opening_balance,
          });
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
          "account_name",
          "account_type",
          "bank_name",
          "account_number",
          "ifsc_code",
          "currency",
          "opening_balance",
        ] as const;

        let applied = false;

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

            applied = true;
          }
        }

        if (!applied) {
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
            "bank account."
          ),
        },
      );
    }
  }

  if (!open) {
    return null;
  }

  const inputClass = `
    mt-1 w-full rounded-lg border
    border-slate-300 bg-white
    px-3 py-2 text-sm
    text-slate-900 outline-none
    placeholder:text-slate-400
    focus:border-blue-500
    focus:ring-2 focus:ring-blue-100
    disabled:bg-slate-100
    disabled:text-slate-500
  `;

  return (
    <div
      className="
        fixed inset-0 z-50
        flex items-center justify-center
        bg-slate-950/50 p-4
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
          "bank-account-form-title"
        }
        className="
          max-h-[92vh] w-full
          max-w-2xl overflow-y-auto
          rounded-2xl bg-white
          text-slate-900 shadow-2xl
        "
      >
        <header
          className="
            flex items-start justify-between
            gap-4 border-b
            border-slate-200 px-6 py-4
          "
        >
          <div>
            <h2
              id="bank-account-form-title"
              className="
                text-lg font-bold
                text-slate-900
              "
            >
              {isEditing
                ? "Edit bank account"
                : "Create bank account"}
            </h2>

            <p
              className="
                mt-1 text-sm text-slate-500
              "
            >
              {isEditing
                ? (
                  "Update the editable "
                  +
                  "account details."
                )
                : (
                  "Add a bank or cash account "
                  +
                  "with its opening balance."
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
            )(
              event,
            );
          }}
          className="space-y-5 p-6"
        >
          <div
            className="
              grid gap-5 sm:grid-cols-2
            "
          >
            <label
              className="
                text-sm font-semibold
                text-slate-700
                sm:col-span-2
              "
            >
              Account name
              <input
                {...register(
                  "account_name"
                )}
                className={inputClass}
                placeholder={
                  "Operating Bank"
                }
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
                text-sm font-semibold
                text-slate-700
              "
            >
              Account type
              <SearchSelect
                {...register(
                  "account_type"
                )}
                disabled={isEditing}
                className={inputClass}
              >
                <option value="BANK">
                  Bank
                </option>
                <option value="CASH">
                  Cash
                </option>
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

            <label
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Currency
              <input
                {...register(
                  "currency"
                )}
                disabled={isEditing}
                className={inputClass}
                placeholder="INR"
              />
              {errors.currency ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors
                      .currency
                      .message
                  }
                </span>
              ) : null}
            </label>

            {accountType === "BANK" ? (
              <>
                <label
                  className="
                    text-sm font-semibold
                    text-slate-700
                  "
                >
                  Bank name
                  <input
                    {...register(
                      "bank_name"
                    )}
                    className={inputClass}
                    placeholder={
                      "Bank name"
                    }
                  />
                  {errors.bank_name ? (
                    <span
                      className="
                        mt-1 block text-xs
                        text-red-600
                      "
                    >
                      {
                        errors
                          .bank_name
                          .message
                      }
                    </span>
                  ) : null}
                </label>

                <label
                  className="
                    text-sm font-semibold
                    text-slate-700
                  "
                >
                  Account number
                  <input
                    {...register(
                      "account_number"
                    )}
                    className={inputClass}
                    placeholder={
                      "Account number"
                    }
                  />
                  {errors.account_number ? (
                    <span
                      className="
                        mt-1 block text-xs
                        text-red-600
                      "
                    >
                      {
                        errors
                          .account_number
                          .message
                      }
                    </span>
                  ) : null}
                </label>

                <label
                  className="
                    text-sm font-semibold
                    text-slate-700
                    sm:col-span-2
                  "
                >
                  IFSC code
                  <input
                    {...register(
                      "ifsc_code"
                    )}
                    className={inputClass}
                    placeholder={
                      "ABCD0001234"
                    }
                  />
                  {errors.ifsc_code ? (
                    <span
                      className="
                        mt-1 block text-xs
                        text-red-600
                      "
                    >
                      {
                        errors
                          .ifsc_code
                          .message
                      }
                    </span>
                  ) : null}
                </label>
              </>
            ) : null}

            <label
              className="
                text-sm font-semibold
                text-slate-700
                sm:col-span-2
              "
            >
              Opening balance
              <input
                {...register(
                  "opening_balance"
                )}
                type="number"
                step="0.01"
                disabled={isEditing}
                className={inputClass}
              />
              {errors.opening_balance ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors
                      .opening_balance
                      .message
                  }
                </span>
              ) : null}
            </label>
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
                  .server.message
              }
            </div>
          ) : mutationError ? (
            <div
              role="alert"
              className="
                rounded-lg border
                border-red-200 bg-red-50
                px-4 py-3 text-sm
                text-red-700
              "
            >
              {mutationError.message}
            </div>
          ) : null}

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
                text-white hover:bg-blue-700
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
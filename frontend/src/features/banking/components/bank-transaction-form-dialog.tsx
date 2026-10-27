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
  useBankAccountList,
  useCreateBankTransaction,
} from "@/features/banking/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

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

const transactionSchema = z
  .object({
    bank_account_id: z
      .string()
      .min(
        1,
        "Bank account is required.",
      ),

    transaction_type: z.enum([
      "MONEY_IN",
      "MONEY_OUT",
      "BANK_CHARGE",
      "INTEREST",
      "OTHER_IN",
      "OTHER_OUT",
    ]),

    transaction_date: z
      .string()
      .min(
        1,
        "Transaction date is required.",
      ),

    amount: z
      .string()
      .trim()
      .refine(
        (value) => {
          const amount =
            Number(value);

          return (
            Number.isFinite(
              amount,
            )
            &&
            amount > 0
            &&
            /^\d+(\.\d{1,2})?$/
              .test(
                value,
              )
          );
        },
        (
          "Enter an amount greater than "
          +
          "zero with up to 2 decimals."
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

    external_reference: z
      .string()
      .trim()
      .max(
        150,
        "Use no more than 150 characters.",
      ),

    description: z
      .string()
      .trim()
      .max(
        1000,
        "Use no more than 1000 characters.",
      ),
  })
  .superRefine(
    (
      values,
      context,
    ) => {
      if (
        Boolean(
          values.reference_type
        )
        !==
        Boolean(
          values.reference_id
        )
      ) {
        context.addIssue({
          code: "custom",
          path: [
            "reference_id",
          ],
          message: (
            "Reference type and ID must "
            +
            "be provided together."
          ),
        });
      }
    },
  );

type TransactionFormValues =
  z.infer<typeof transactionSchema>;

interface BankTransactionFormDialogProps {
  open: boolean;
  onClose: () => void;
}

const emptyValues:
  TransactionFormValues = {
    bank_account_id: "",
    transaction_type: "MONEY_IN",
    transaction_date: "",
    amount: "",
    reference_type: "",
    reference_id: "",
    external_reference: "",
    description: "",
  };

const transactionTypes = [
  {
    value: "MONEY_IN",
    label: "Money in",
  },
  {
    value: "MONEY_OUT",
    label: "Money out",
  },
  {
    value: "BANK_CHARGE",
    label: "Bank charge",
  },
  {
    value: "INTEREST",
    label: "Interest received",
  },
  {
    value: "OTHER_IN",
    label: "Other money in",
  },
  {
    value: "OTHER_OUT",
    label: "Other money out",
  },
] as const;

export default function BankTransactionFormDialog({
  open,
  onClose,
}: BankTransactionFormDialogProps) {
  const createMutation =
    useCreateBankTransaction();

  const accountQuery =
    useBankAccountList({
      page_size: 100,
      is_active: true,
      sort: "account_name",
    });

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<TransactionFormValues>({
    resolver:
      zodResolver(
        transactionSchema,
      ),
    defaultValues:
      emptyValues,
  });

  useEffect(() => {
    if (!open) {
      return;
    }

    reset({
      ...emptyValues,
      transaction_date:
        todayValue(),
    });
  }, [
    open,
    reset,
  ]);

  async function submit(
    values: TransactionFormValues,
  ): Promise<void> {
    try {
      await createMutation
        .mutateAsync({
          bank_account_id:
            values.bank_account_id,
          transaction_type:
            values.transaction_type,
          transaction_date:
            values.transaction_date,
          amount:
            values.amount,
          reference_type:
            values.reference_type
            ||
            undefined,
          reference_id:
            values.reference_id
            ||
            undefined,
          external_reference:
            values.external_reference
            ||
            undefined,
          description:
            values.description
            ||
            undefined,
        });

      onClose();
    } catch (error) {
      if (
        error
        instanceof
        APIRequestError
      ) {
        const fields = [
          "bank_account_id",
          "transaction_type",
          "transaction_date",
          "amount",
          "reference_type",
          "reference_id",
          "external_reference",
          "description",
        ] as const;

        let applied = false;

        for (const field of fields) {
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
            "Unable to create the "
            +
            "bank transaction."
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
    px-3 py-2 text-sm text-slate-900
    outline-none
    placeholder:text-slate-400
    focus:border-blue-500
    focus:ring-2 focus:ring-blue-100
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
          !createMutation.isPending
        ) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={
          "bank-transaction-form-title"
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
              id={
                "bank-transaction-form-title"
              }
              className="
                text-lg font-bold
                text-slate-900
              "
            >
              Create bank transaction
            </h2>

            <p
              className="
                mt-1 text-sm text-slate-500
              "
            >
              Record a manual money-in or
              money-out transaction.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close dialog"
            disabled={
              createMutation.isPending
            }
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
              Bank account
              <SearchSelect
                {...register(
                  "bank_account_id"
                )}
                className={inputClass}
              >
                <option value="">
                  Select an account
                </option>
                {
                  accountQuery.data
                    ?.bank_accounts
                    .map(
                      (account) => (
                        <option
                          key={account.id}
                          value={account.id}
                        >
                          {
                            account
                              .account_name
                          }
                          {" — "}
                          {
                            account
                              .currency
                          }
                          {" "}
                          {
                            account
                              .current_balance
                          }
                        </option>
                      ),
                    )
                }
              </SearchSelect>
              {errors.bank_account_id ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors
                      .bank_account_id
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
              Transaction type
              <SearchSelect
                {...register(
                  "transaction_type"
                )}
                className={inputClass}
              >
                {transactionTypes.map(
                  (type) => (
                    <option
                      key={type.value}
                      value={type.value}
                    >
                      {type.label}
                    </option>
                  ),
                )}
              </SearchSelect>
            </label>

            <label
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Transaction date
              <input
                {...register(
                  "transaction_date"
                )}
                type="date"
                className={inputClass}
              />
              {errors.transaction_date ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors
                      .transaction_date
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
              Amount
              <input
                {...register(
                  "amount"
                )}
                type="number"
                min="0.01"
                step="0.01"
                className={inputClass}
                placeholder="0.00"
              />
              {errors.amount ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors.amount.message
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
              Reference type
              <input
                {...register(
                  "reference_type"
                )}
                className={inputClass}
                placeholder={
                  "Optional reference type"
                }
              />
            </label>

            <label
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Reference ID
              <input
                {...register(
                  "reference_id"
                )}
                className={inputClass}
                placeholder={
                  "Optional reference ID"
                }
              />
              {errors.reference_id ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors
                      .reference_id
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
              External reference
              <input
                {...register(
                  "external_reference"
                )}
                className={inputClass}
                placeholder={
                  "UTR, cheque number, etc."
                }
              />
            </label>

            <label
              className="
                text-sm font-semibold
                text-slate-700
                sm:col-span-2
              "
            >
              Description
              <textarea
                {...register(
                  "description"
                )}
                rows={3}
                className={inputClass}
                placeholder={
                  "Transaction description"
                }
              />
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
          ) : createMutation.error ? (
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
                createMutation
                  .error.message
              }
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
                inline-flex items-center
                gap-2 rounded-lg
                bg-blue-600 px-4 py-2
                text-sm font-semibold
                text-white hover:bg-blue-700
                disabled:opacity-50
              "
            >
              {createMutation.isPending ? (
                <LoaderCircle
                  size={16}
                  className="animate-spin"
                />
              ) : null}

              Create transaction
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
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
  useCreateBankTransfer,
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

const transferSchema = z
  .object({
    source_account_id: z
      .string()
      .min(
        1,
        "Source account is required.",
      ),

    destination_account_id: z
      .string()
      .min(
        1,
        "Destination account is required.",
      ),

    transfer_date: z
      .string()
      .min(
        1,
        "Transfer date is required.",
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

    reference: z
      .string()
      .trim()
      .max(
        150,
        "Use no more than 150 characters.",
      ),

    notes: z
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
        values.source_account_id
        &&
        values.source_account_id
        ===
        values.destination_account_id
      ) {
        context.addIssue({
          code: "custom",
          path: [
            "destination_account_id",
          ],
          message: (
            "Destination must be different "
            +
            "from source account."
          ),
        });
      }
    },
  );

type TransferFormValues =
  z.infer<typeof transferSchema>;

interface BankTransferFormDialogProps {
  open: boolean;
  onClose: () => void;
}

const emptyValues:
  TransferFormValues = {
    source_account_id: "",
    destination_account_id: "",
    transfer_date: "",
    amount: "",
    reference: "",
    notes: "",
  };

export default function BankTransferFormDialog({
  open,
  onClose,
}: BankTransferFormDialogProps) {
  const createMutation =
    useCreateBankTransfer();

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
  } = useForm<TransferFormValues>({
    resolver:
      zodResolver(
        transferSchema,
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
      transfer_date:
        todayValue(),
    });
  }, [
    open,
    reset,
  ]);

  async function submit(
    values: TransferFormValues,
  ): Promise<void> {
    try {
      await createMutation
        .mutateAsync({
          source_account_id:
            values.source_account_id,
          destination_account_id:
            values
              .destination_account_id,
          transfer_date:
            values.transfer_date,
          amount:
            values.amount,
          reference:
            values.reference
            ||
            undefined,
          notes:
            values.notes
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
          "source_account_id",
          "destination_account_id",
          "transfer_date",
          "amount",
          "reference",
          "notes",
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
            "bank transfer."
          ),
        },
      );
    }
  }

  if (!open) {
    return null;
  }

  const accounts =
    accountQuery.data
      ?.bank_accounts
    ??
    [];

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
          "bank-transfer-form-title"
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
                "bank-transfer-form-title"
              }
              className="
                text-lg font-bold
                text-slate-900
              "
            >
              Create bank transfer
            </h2>

            <p
              className="
                mt-1 text-sm text-slate-500
              "
            >
              Move money between two active
              accounts with matching currency.
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
              "
            >
              Source account
              <SearchSelect
                {...register(
                  "source_account_id"
                )}
                className={inputClass}
              >
                <option value="">
                  Select source
                </option>
                {accounts.map(
                  (account) => (
                    <option
                      key={account.id}
                      value={account.id}
                    >
                      {
                        account.account_name
                      }
                      {" — "}
                      {
                        account.currency
                      }
                      {" "}
                      {
                        account
                          .current_balance
                      }
                    </option>
                  ),
                )}
              </SearchSelect>
              {errors.source_account_id ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors
                      .source_account_id
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
              Destination account
              <SearchSelect
                {...register(
                  "destination_account_id"
                )}
                className={inputClass}
              >
                <option value="">
                  Select destination
                </option>
                {accounts.map(
                  (account) => (
                    <option
                      key={account.id}
                      value={account.id}
                    >
                      {
                        account.account_name
                      }
                      {" — "}
                      {
                        account.currency
                      }
                      {" "}
                      {
                        account
                          .current_balance
                      }
                    </option>
                  ),
                )}
              </SearchSelect>
              {
                errors
                  .destination_account_id
                ? (
                  <span
                    className="
                      mt-1 block text-xs
                      text-red-600
                    "
                  >
                    {
                      errors
                        .destination_account_id
                        .message
                    }
                  </span>
                )
                : null
              }
            </label>

            <label
              className="
                text-sm font-semibold
                text-slate-700
              "
            >
              Transfer date
              <input
                {...register(
                  "transfer_date"
                )}
                type="date"
                className={inputClass}
              />
              {errors.transfer_date ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors
                      .transfer_date
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
                sm:col-span-2
              "
            >
              Reference
              <input
                {...register(
                  "reference"
                )}
                className={inputClass}
                placeholder={
                  "Optional bank reference"
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
              Notes
              <textarea
                {...register(
                  "notes"
                )}
                rows={4}
                className={inputClass}
                placeholder={
                  "Optional transfer notes"
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
                ||
                accounts.length < 2
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

              Create transfer
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
"use client";
import SearchSelect from "@/components/search-select";


import {
  useEffect,
} from "react";

import {
  zodResolver,
} from "@hookform/resolvers/zod";

import {
  IndianRupee,
  X,
} from "lucide-react";

import {
  useForm,
} from "react-hook-form";

import {
  z,
} from "zod";

import {
  useInvoiceBankAccounts,
  useRecordInvoicePayment,
} from "@/features/invoices/hooks";

import type {
  InvoicePaymentMethod,
  InvoiceSummary,
} from "@/features/invoices/types";

import {
  APIRequestError,
} from "@/lib/api/client";

const positiveAmount = z
  .string()
  .trim()
  .refine(
    (value) => {
      const amount =
        Number(
          value,
        );

      return (
        value !== ""
        &&
        Number.isFinite(
          amount,
        )
        &&
        amount > 0
      );
    },
    "Enter an amount greater than zero.",
  );

const paymentSchema = z.object({
  amount:
    positiveAmount,

  payment_method: z.enum([
    "CASH",
    "BANK_TRANSFER",
    "UPI",
    "CHEQUE",
    "CARD",
    "OTHER",
  ]),

  bank_account_id: z
    .string()
    .min(
      1,
      "Bank account is required.",
    ),

  payment_date:
    z.string(),

  reference_number: z
    .string()
    .trim()
    .max(
      100,
      "Reference cannot exceed 100 characters.",
    ),

  notes: z
    .string()
    .trim()
    .max(
      1000,
      "Notes cannot exceed 1000 characters.",
    ),
});

type PaymentFormValues =
  z.infer<typeof paymentSchema>;

interface InvoicePaymentDialogProps {
  open: boolean;
  invoice: InvoiceSummary | null;
  onClose: () => void;
  onRecorded?: () => void;
}

const paymentMethods: Array<{
  value: InvoicePaymentMethod;
  label: string;
}> = [
  {
    value: "BANK_TRANSFER",
    label: "Bank transfer",
  },
  {
    value: "UPI",
    label: "UPI",
  },
  {
    value: "CHEQUE",
    label: "Cheque",
  },
  {
    value: "CARD",
    label: "Card",
  },
  {
    value: "CASH",
    label: "Cash",
  },
  {
    value: "OTHER",
    label: "Other",
  },
];

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

function emptyValues(
  balanceDue = "",
): PaymentFormValues {
  return {
    amount:
      balanceDue,
    payment_method:
      "BANK_TRANSFER",
    bank_account_id: "",
    payment_date:
      todayValue(),
    reference_number: "",
    notes: "",
  };
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

function formatAmount(
  value: string,
): string {
  const amount =
    Number(
      value,
    );

  if (
    !Number.isFinite(
      amount,
    )
  ) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(
    amount,
  );
}

export default function InvoicePaymentDialog({
  open,
  invoice,
  onClose,
  onRecorded,
}: InvoicePaymentDialogProps) {
  const bankAccountQuery =
    useInvoiceBankAccounts(
      open,
    );

  const paymentMutation =
    useRecordInvoicePayment();

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<PaymentFormValues>({
    resolver:
      zodResolver(
        paymentSchema,
      ),

    defaultValues:
      emptyValues(),
  });

  useEffect(() => {
    if (
      open
      &&
      invoice
    ) {
      reset(
        emptyValues(
          invoice.balance_due,
        ),
      );
    }
  }, [
    invoice,
    open,
    reset,
  ]);

  if (
    !open
    ||
    !invoice
  ) {
    return null;
  }

  const bankAccounts =
    bankAccountQuery.data
      ?.bank_accounts
    ??
    [];

  async function submit(
    values: PaymentFormValues,
  ): Promise<void> {
    if (!invoice) {
      return;
    }

    const amount =
      Number(
        values.amount,
      );

    const balanceDue =
      Number(
        invoice.balance_due,
      );

    if (
      Number.isFinite(
        balanceDue,
      )
      &&
      amount > balanceDue
    ) {
      setError(
        "amount",
        {
          type: "validate",
          message:
            "Payment cannot exceed the balance due.",
        },
      );

      return;
    }

    try {
      await paymentMutation
        .mutateAsync({
          invoiceId:
            invoice.id,

          input: {
            amount:
              values.amount,

            payment_method:
              values.payment_method,

            bank_account_id:
              values.bank_account_id,

            payment_date:
              values.payment_date
              ||
              undefined,

            reference_number:
              values
                .reference_number
                .trim()
              ||
              undefined,

            notes:
              values.notes.trim()
              ||
              undefined,
          },
        });

      onClose();
      onRecorded?.();

    } catch (error) {
      if (
        error
        instanceof
        APIRequestError
      ) {
        const details =
          error.details
          ??
          {};

        const fields: Array<
          keyof PaymentFormValues
        > = [
          "amount",
          "payment_method",
          "bank_account_id",
          "payment_date",
          "reference_number",
          "notes",
        ];

        let fieldErrorFound =
          false;

        for (const field of fields) {
          const message =
            firstFieldMessage(
              details[field],
            );

          if (message) {
            setError(
              field,
              {
                type: "server",
                message,
              },
            );

            fieldErrorFound =
              true;
          }
        }

        if (!fieldErrorFound) {
          setError(
            "root",
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
        "root",
        {
          type: "server",
          message:
            "Unable to record the payment.",
        },
      );
    }
  }

  const pending =
    paymentMutation.isPending;

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
        aria-labelledby="invoice-payment-title"
        className="
          max-h-[calc(100vh-2rem)]
          w-full max-w-2xl
          overflow-y-auto rounded-2xl
          border border-slate-200
          bg-white text-slate-900
          shadow-2xl
        "
      >
        <header
          className="
            flex items-start
            justify-between gap-4
            border-b border-slate-200
            px-5 py-4 sm:px-6
          "
        >
          <div>
            <h2
              id="invoice-payment-title"
              className="
                text-lg font-semibold
                text-slate-950
              "
            >
              Record Payment
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-600
              "
            >
              {invoice.invoice_number}
              {" · "}
              Balance ₹
              {formatAmount(
                invoice.balance_due,
              )}
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
            "
          >
            <div>
              <label
                htmlFor="payment-amount"
                className="
                  text-sm font-medium
                  text-slate-800
                "
              >
                Amount
              </label>

              <input
                id="payment-amount"
                type="number"
                min="0.01"
                step="0.01"
                disabled={pending}
                {...register(
                  "amount",
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

              {errors.amount ? (
                <p
                  className="
                    mt-1 text-sm
                    text-red-600
                  "
                >
                  {errors.amount.message}
                </p>
              ) : null}
            </div>

            <div>
              <label
                htmlFor="payment-date"
                className="
                  text-sm font-medium
                  text-slate-800
                "
              >
                Payment date
              </label>

              <input
                id="payment-date"
                type="date"
                disabled={pending}
                {...register(
                  "payment_date",
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

              {errors.payment_date ? (
                <p
                  className="
                    mt-1 text-sm
                    text-red-600
                  "
                >
                  {
                    errors
                      .payment_date
                      .message
                  }
                </p>
              ) : null}
            </div>

            <div>
              <label
                htmlFor="payment-method"
                className="
                  text-sm font-medium
                  text-slate-800
                "
              >
                Payment method
              </label>

              <SearchSelect
                id="payment-method"
                disabled={pending}
                {...register(
                  "payment_method",
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
                {paymentMethods.map(
                  (method) => (
                    <option
                      key={method.value}
                      value={method.value}
                    >
                      {method.label}
                    </option>
                  ),
                )}
              </SearchSelect>

              {errors.payment_method ? (
                <p
                  className="
                    mt-1 text-sm
                    text-red-600
                  "
                >
                  {
                    errors
                      .payment_method
                      .message
                  }
                </p>
              ) : null}
            </div>

            <div>
              <label
                htmlFor="payment-account"
                className="
                  text-sm font-medium
                  text-slate-800
                "
              >
                Receiving account
              </label>

              <SearchSelect
                id="payment-account"
                disabled={
                  pending
                  ||
                  bankAccountQuery.isPending
                }
                {...register(
                  "bank_account_id",
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
                  Select an account
                </option>

                {bankAccounts.map(
                  (account) => (
                    <option
                      key={account.id}
                      value={account.id}
                    >
                      {account.account_name}
                      {" — "}
                      {account.bank_name
                        ??
                        account.account_type}
                      {account
                        .masked_account_number
                        ? ` ${account.masked_account_number}`
                        : ""}
                    </option>
                  ),
                )}
              </SearchSelect>

              {errors.bank_account_id ? (
                <p
                  className="
                    mt-1 text-sm
                    text-red-600
                  "
                >
                  {
                    errors
                      .bank_account_id
                      .message
                  }
                </p>
              ) : null}

              {bankAccountQuery.isError ? (
                <p
                  className="
                    mt-1 text-sm
                    text-red-600
                  "
                >
                  Unable to load payment
                  accounts.
                </p>
              ) : null}
            </div>

            <div className="sm:col-span-2">
              <label
                htmlFor="payment-reference"
                className="
                  text-sm font-medium
                  text-slate-800
                "
              >
                Reference number
              </label>

              <input
                id="payment-reference"
                type="text"
                disabled={pending}
                {...register(
                  "reference_number",
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
                placeholder="Transaction, UPI or cheque reference"
              />

              {errors.reference_number ? (
                <p
                  className="
                    mt-1 text-sm
                    text-red-600
                  "
                >
                  {
                    errors
                      .reference_number
                      .message
                  }
                </p>
              ) : null}
            </div>

            <div className="sm:col-span-2">
              <label
                htmlFor="payment-notes"
                className="
                  text-sm font-medium
                  text-slate-800
                "
              >
                Notes
              </label>

              <textarea
                id="payment-notes"
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
                placeholder="Optional payment notes"
              />

              {errors.notes ? (
                <p
                  className="
                    mt-1 text-sm
                    text-red-600
                  "
                >
                  {errors.notes.message}
                </p>
              ) : null}
            </div>

            {errors.root ? (
              <div
                className="
                  rounded-lg border
                  border-red-200
                  bg-red-50 px-4 py-3
                  text-sm text-red-700
                  sm:col-span-2
                "
              >
                {errors.root.message}
              </div>
            ) : null}
          </div>

          <footer
            className="
              flex flex-col-reverse
              gap-3 border-t
              border-slate-200
              bg-slate-50 px-5 py-4
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
                disabled:opacity-50
              "
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={
                pending
                ||
                bankAccountQuery.isPending
                ||
                bankAccounts.length === 0
              }
              className="
                inline-flex items-center
                justify-center gap-2
                rounded-lg bg-emerald-600
                px-4 py-2.5
                text-sm font-semibold
                text-white
                hover:bg-emerald-700
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              <IndianRupee size={17} />

              {pending
                ? "Recording…"
                : "Record Payment"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}
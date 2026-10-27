"use client";
import SearchSelect from "@/components/search-select";


import {
  useEffect,
  useState,
} from "react";

import {
  FileSpreadsheet,
  LoaderCircle,
  Upload,
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
  useImportBankStatement,
} from "@/features/banking/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

const MAX_FILE_SIZE =
  5 * 1024 * 1024;

function localDateValue(
  date: Date,
): string {
  const offset =
    date.getTimezoneOffset()
    *
    60_000;

  return new Date(
    date.getTime()
    -
    offset,
  )
    .toISOString()
    .slice(0, 10);
}

function defaultDates(): {
  start: string;
  end: string;
} {
  const now = new Date();
  const start = new Date(
    now.getFullYear(),
    now.getMonth(),
    1,
  );

  return {
    start: localDateValue(start),
    end: localDateValue(now),
  };
}

const amountSchema = z
  .string()
  .trim()
  .min(
    1,
    "Amount is required.",
  )
  .refine(
    (value) => (
      /^-?\d+(\.\d{1,2})?$/
        .test(value)
      &&
      Number.isFinite(Number(value))
    ),
    "Enter a valid amount with up to 2 decimals.",
  );

const statementSchema = z
  .object({
    bank_account_id: z
      .string()
      .min(
        1,
        "Bank account is required.",
      ),

    statement_start_date: z
      .string()
      .min(
        1,
        "Start date is required.",
      ),

    statement_end_date: z
      .string()
      .min(
        1,
        "End date is required.",
      ),

    opening_balance:
      amountSchema,

    closing_balance:
      amountSchema,
  })
  .superRefine(
    (
      values,
      context,
    ) => {
      if (
        values.statement_start_date
        >
        values.statement_end_date
      ) {
        context.addIssue({
          code: "custom",
          path: [
            "statement_end_date",
          ],
          message: (
            "End date must be on or "
            +
            "after the start date."
          ),
        });
      }
    },
  );

type StatementFormValues =
  z.infer<typeof statementSchema>;

interface BankStatementImportDialogProps {
  open: boolean;
  onClose: () => void;
  onImported?: (
    statementId: string,
  ) => void;
}

export default function BankStatementImportDialog({
  open,
  onClose,
  onImported,
}: BankStatementImportDialogProps) {
  const [file, setFile] =
    useState<File | null>(null);
  const [fileError, setFileError] =
    useState("");

  const importMutation =
    useImportBankStatement();

  const accountQuery =
    useBankAccountList({
      page_size: 100,
      account_type: "BANK",
      is_active: true,
      sort: "account_name",
    });

  const {
    register,
    handleSubmit,
    reset,
    setError,
    clearErrors,
    formState: {
      errors,
    },
  } = useForm<StatementFormValues>({
    resolver:
      zodResolver(
        statementSchema,
      ),
    defaultValues: {
      bank_account_id: "",
      statement_start_date: "",
      statement_end_date: "",
      opening_balance: "",
      closing_balance: "",
    },
  });

  useEffect(() => {
    if (!open) {
      return;
    }

    const dates =
      defaultDates();

    reset({
      bank_account_id: "",
      statement_start_date:
        dates.start,
      statement_end_date:
        dates.end,
      opening_balance: "",
      closing_balance: "",
    });


  }, [
    open,
    reset,
  ]);
  function closeDialog(): void {
    setFile(null);
    setFileError("");
    onClose();
  }
  function selectFile(
    selected: File | null,
  ): void {
    setFileError("");
    clearErrors("root.server");

    if (!selected) {
      setFile(null);
      return;
    }

    const extension =
      selected.name
        .split(".")
        .pop()
        ?.toLowerCase();

    if (
      extension !== "csv"
      &&
      extension !== "xlsx"
    ) {
      setFile(null);
      setFileError(
        "Choose a CSV or XLSX file.",
      );
      return;
    }

    if (
      selected.size
      >
      MAX_FILE_SIZE
    ) {
      setFile(null);
      setFileError(
        "The file must not exceed 5 MB.",
      );
      return;
    }

    setFile(selected);
  }

  async function submit(
    values: StatementFormValues,
  ): Promise<void> {
    if (!file) {
      setFileError(
        "Statement file is required.",
      );
      return;
    }

    try {
      const statement =
        await importMutation
          .mutateAsync({
            file,
            bank_account_id:
              values.bank_account_id,
            statement_start_date:
              values.statement_start_date,
            statement_end_date:
              values.statement_end_date,
            opening_balance:
              values.opening_balance,
            closing_balance:
              values.closing_balance,
          });

      closeDialog();
      onImported?.(
        statement.id,
      );
    } catch (error) {
      if (
        error
        instanceof APIRequestError
      ) {
        const fields = [
          "bank_account_id",
          "statement_start_date",
          "statement_end_date",
          "opening_balance",
          "closing_balance",
        ] as const;

        let applied = false;

        for (const field of fields) {
          const messages =
            error.details
              ?.[field];

          if (
            Array.isArray(messages)
            &&
            typeof messages[0]
            === "string"
          ) {
            setError(
              field,
              {
                type: "server",
                message: messages[0],
              },
            );
            applied = true;
          }
        }

        const fileMessages =
          error.details?.file;

        if (
          Array.isArray(fileMessages)
          &&
          typeof fileMessages[0]
          === "string"
        ) {
          setFileError(
            fileMessages[0],
          );
          applied = true;
        }

        if (!applied) {
          setError(
            "root.server",
            {
              type: "server",
              message: error.message,
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
            "Unable to import the bank "
            +
            "statement."
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
          !importMutation.isPending
        ) {
          closeDialog();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={
          "bank-statement-import-title"
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
              id="bank-statement-import-title"
              className="
                text-lg font-bold
                text-slate-900
              "
            >
              Import bank statement
            </h2>

            <p
              className="
                mt-1 text-sm text-slate-500
              "
            >
              Upload a CSV or XLSX statement
              for transaction reconciliation.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close dialog"
            disabled={
              importMutation.isPending
            }
            onClick={closeDialog}
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
          <label
            className="
              block text-sm font-semibold
              text-slate-700
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
                Select bank account
              </option>
              {accounts.map(
                (account) => (
                  <option
                    key={account.id}
                    value={account.id}
                  >
                    {account.account_name}
                    {" — "}
                    {account.currency}
                    {" "}
                    {account.current_balance}
                  </option>
                ),
              )}
            </SearchSelect>
            {errors.bank_account_id ? (
              <span
                className="
                  mt-1 block text-xs
                  text-red-600
                "
              >
                {
                  errors.bank_account_id
                    .message
                }
              </span>
            ) : null}
          </label>

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
              Statement start date
              <input
                {...register(
                  "statement_start_date"
                )}
                type="date"
                className={inputClass}
              />
              {errors.statement_start_date ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors.statement_start_date
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
              Statement end date
              <input
                {...register(
                  "statement_end_date"
                )}
                type="date"
                className={inputClass}
              />
              {errors.statement_end_date ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors.statement_end_date
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
              Opening balance
              <input
                {...register(
                  "opening_balance"
                )}
                type="number"
                step="0.01"
                className={inputClass}
                placeholder="0.00"
              />
              {errors.opening_balance ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors.opening_balance
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
              Closing balance
              <input
                {...register(
                  "closing_balance"
                )}
                type="number"
                step="0.01"
                className={inputClass}
                placeholder="0.00"
              />
              {errors.closing_balance ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors.closing_balance
                      .message
                  }
                </span>
              ) : null}
            </label>
          </div>

          <div>
            <label
              className="
                block text-sm font-semibold
                text-slate-700
              "
            >
              Statement file
              <span
                className="
                  mt-1 flex cursor-pointer
                  items-center justify-center
                  gap-3 rounded-xl border-2
                  border-dashed border-slate-300
                  bg-slate-50 px-5 py-8
                  text-center hover:border-blue-400
                  hover:bg-blue-50
                "
              >
                <FileSpreadsheet
                  size={28}
                  className="text-blue-600"
                />
                <span>
                  <span
                    className="
                      block text-sm font-semibold
                      text-slate-800
                    "
                  >
                    {file
                      ? file.name
                      : "Choose CSV or XLSX"}
                  </span>
                  <span
                    className="
                      mt-1 block text-xs
                      text-slate-500
                    "
                  >
                    Maximum file size: 5 MB
                  </span>
                </span>
                <input
                  type="file"
                  accept=".csv,.xlsx"
                  className="sr-only"
                  onChange={(event) => {
                    selectFile(
                      event.target.files
                        ?.[0]
                      ??
                      null,
                    );
                  }}
                />
              </span>
            </label>

            {fileError ? (
              <p
                className="
                  mt-2 text-xs text-red-600
                "
              >
                {fileError}
              </p>
            ) : null}
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
              {errors.root.server.message}
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
                importMutation.isPending
              }
              onClick={closeDialog}
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
                importMutation.isPending
                ||
                accounts.length === 0
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
              {importMutation.isPending ? (
                <LoaderCircle
                  size={16}
                  className="animate-spin"
                />
              ) : (
                <Upload size={16} />
              )}
              Import statement
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

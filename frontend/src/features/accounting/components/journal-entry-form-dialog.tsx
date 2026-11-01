"use client";
import SearchSelect from "@/components/search-select";


import {
  useEffect,
} from "react";

import {
  LoaderCircle,
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
  zodResolver,
} from "@hookform/resolvers/zod";

import {
  z,
} from "zod";

import {
  useChartOfAccountList,
  useCreateJournalEntry,
  useUpdateJournalEntry,
} from "@/features/accounting/hooks";

import type {
  JournalEntryDetail,
} from "@/features/accounting/types";

import {
  APIRequestError,
} from "@/lib/api/client";

const amountSchema = z
  .string()
  .trim()
  .refine(
    (value) => {
      const amount =
        Number(value);

      return (
        value !== ""
        &&
        Number.isFinite(
          amount
        )
        &&
        amount >= 0
      );
    },
    "Enter a valid non-negative amount.",
  );

const lineSchema = z
  .object({
    account_id: z
      .string()
      .min(
        1,
        "Account is required.",
      ),

    description: z
      .string()
      .trim()
      .max(
        500,
        "Use no more than 500 characters.",
      ),

    debit:
      amountSchema,

    credit:
      amountSchema,
  })
  .superRefine(
    (
      line,
      context,
    ) => {
      const debit =
        Number(
          line.debit
        );

      const credit =
        Number(
          line.credit
        );

      if (
        debit > 0
        &&
        credit > 0
      ) {
        context.addIssue({
          code:
            "custom",
          path: [
            "debit",
          ],
          message: (
            "Use either debit or credit, "
            +
            "not both."
          ),
        });
      }

      if (
        debit === 0
        &&
        credit === 0
      ) {
        context.addIssue({
          code:
            "custom",
          path: [
            "debit",
          ],
          message: (
            "Enter a debit or credit amount."
          ),
        });
      }
    },
  );

const journalSchema = z
  .object({
    journal_date: z
      .string()
      .min(
        1,
        "Journal date is required.",
      ),

    description: z
      .string()
      .trim()
      .max(
        1000,
        "Use no more than 1000 characters.",
      ),

    lines: z
      .array(
        lineSchema
      )
      .min(
        2,
        (
          "At least two journal "
          +
          "lines are required."
        ),
      ),
  })
  .superRefine(
    (
      values,
      context,
    ) => {
      const totalDebit =
        values.lines.reduce(
          (
            total,
            line,
          ) =>
            total
            +
            (
              Number(
                line.debit
              )
              ||
              0
            ),
          0,
        );

      const totalCredit =
        values.lines.reduce(
          (
            total,
            line,
          ) =>
            total
            +
            (
              Number(
                line.credit
              )
              ||
              0
            ),
          0,
        );

      if (
        Math.abs(
          totalDebit
          -
          totalCredit
        )
        >
        0.005
      ) {
        context.addIssue({
          code:
            "custom",
          path: [
            "lines",
          ],
          message: (
            "Journal debit and credit "
            +
            "totals must be equal."
          ),
        });
      }
    },
  );

type JournalFormValues =
  z.infer<typeof journalSchema>;

interface JournalEntryFormDialogProps {
  open: boolean;
  journal?:
    JournalEntryDetail | null;
  onClose: () => void;
  onSaved?: (
    journalId: string,
  ) => void;
}

const emptyLine = {
  account_id: "",
  description: "",
  debit: "0.00",
  credit: "0.00",
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

function dateInputValue(
  value: string | null,
): string {
  if (!value) {
    return todayValue();
  }

  return value.slice(
    0,
    10,
  );
}

function emptyValues():
  JournalFormValues {
  return {
    journal_date:
      todayValue(),
    description: "",
    lines: [
      {
        ...emptyLine,
      },
      {
        ...emptyLine,
      },
    ],
  };
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

export default function JournalEntryFormDialog({
  open,
  journal,
  onClose,
  onSaved,
}: JournalEntryFormDialogProps) {
  const accountQuery =
    useChartOfAccountList({
      page: 1,
      page_size: 100,
      is_active: true,
      allow_manual_posting: true,
      sort: "account_code",
    });

  const createMutation =
    useCreateJournalEntry();

  const updateMutation =
    useUpdateJournalEntry();

  const editing = Boolean(
    journal,
  );

  const {
    register,
    control,
    handleSubmit,
    reset,
    setError,
    formState: {
      errors,
    },
  } = useForm<JournalFormValues>({
    resolver:
      zodResolver(
        journalSchema,
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
    name: "lines",
  });

  const watchedLines =
    useWatch({
      control,
      name: "lines",
    });

  useEffect(() => {
    if (!open) {
      return;
    }

    reset(
      journal
        ? {
            journal_date:
              dateInputValue(
                journal.journal_date
              ),
            description:
              journal.description
              ??
              "",
            lines:
              journal.lines.map(
                (line) => ({
                  account_id:
                    line.account.id,
                  description:
                    line.description
                    ??
                    "",
                  debit:
                    line.debit,
                  credit:
                    line.credit,
                }),
              ),
          }
        : emptyValues(),
    );
  }, [
    journal,
    open,
    reset,
  ]);

  const accounts =
    accountQuery
      .data
      ?.accounts
      ??
      [];

  const totalDebit =
    watchedLines?.reduce(
      (
        total,
        line,
      ) =>
        total
        +
        (
          Number(
            line?.debit
          )
          ||
          0
        ),
      0,
    )
    ??
    0;

  const totalCredit =
    watchedLines?.reduce(
      (
        total,
        line,
      ) =>
        total
        +
        (
          Number(
            line?.credit
          )
          ||
          0
        ),
      0,
    )
    ??
    0;

  const difference =
    totalDebit
    -
    totalCredit;

  const balanced =
    totalDebit > 0
    &&
    totalCredit > 0
    &&
    Math.abs(
      difference
    ) <= 0.005;

  const pending =
    createMutation.isPending
    ||
    updateMutation.isPending;

  const mutationError =
    createMutation.error
    ??
    updateMutation.error;

  async function submit(
    values: JournalFormValues,
  ): Promise<void> {
    try {
      const input = {
        journal_date:
          values.journal_date,
        description:
          values.description,
        lines:
          values.lines.map(
            (line) => ({
              account_id:
                line.account_id,
              description:
                line.description,
              debit:
                line.debit,
              credit:
                line.credit,
            }),
          ),
      };

      const savedJournal =
        journal
          ? await updateMutation
              .mutateAsync({
                journalId:
                  journal.id,
                input,
              })
          : await createMutation
              .mutateAsync(
                input
              );

      reset(
        emptyValues()
      );

      onSaved?.(
        savedJournal.id
      );

      onClose();
    } catch (error) {
      if (
        error
        instanceof
        APIRequestError
      ) {
        const journalDateMessages =
          error.details
            ?.journal_date;

        const descriptionMessages =
          error.details
            ?.description;

        if (
          Array.isArray(
            journalDateMessages
          )
          &&
          typeof journalDateMessages[0]
          ===
          "string"
        ) {
          setError(
            "journal_date",
            {
              type: "server",
              message:
                journalDateMessages[0],
            },
          );
        }

        if (
          Array.isArray(
            descriptionMessages
          )
          &&
          typeof descriptionMessages[0]
          ===
          "string"
        ) {
          setError(
            "description",
            {
              type: "server",
              message:
                descriptionMessages[0],
            },
          );
        }

        if (
          !Array.isArray(
            journalDateMessages
          )
          &&
          !Array.isArray(
            descriptionMessages
          )
        ) {
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
            "journal entry."
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
          !pending
        ) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={
          "journal-form-title"
        }
        className="
          max-h-[94vh] w-full
          max-w-5xl overflow-y-auto
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
              id="journal-form-title"
              className="
                text-lg font-bold
                text-slate-900
              "
            >
              {editing
                ? "Edit draft journal"
                : "Create manual journal"}
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-500
              "
            >
              Every journal must contain
              equal debit and credit totals.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close dialog"
            disabled={pending}
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
          className="
            text-slate-900
          "
          onSubmit={(event) => {
            void handleSubmit(
              submit,
            )(event);
          }}
        >
          <div
            className="
              grid gap-5 border-b
              border-slate-200 px-6
              py-5 sm:grid-cols-3
            "
          >
            <label
              className="
                block text-sm font-medium
                text-slate-700
              "
            >
              Journal date

              <input
                type="date"
                {...register(
                  "journal_date"
                )}
                disabled={pending}
                className="
                  mt-2 w-full rounded-lg
                  border border-slate-300
                  px-3 py-2 text-sm
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />

              {errors.journal_date ? (
                <span
                  className="
                    mt-1 block text-xs
                    text-red-600
                  "
                >
                  {
                    errors
                      .journal_date
                      .message
                  }
                </span>
              ) : null}
            </label>

            <label
              className="
                block text-sm font-medium
                text-slate-700
                sm:col-span-2
              "
            >
              Description

              <input
                {...register(
                  "description"
                )}
                disabled={pending}
                placeholder={
                  "Purpose of this journal"
                }
                className="
                  mt-2 w-full rounded-lg
                  border border-slate-300
                  px-3 py-2 text-sm
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
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
          </div>

          <div className="px-6 py-5">
            <div
              className="
                flex flex-col gap-3
                sm:flex-row sm:items-center
                sm:justify-between
              "
            >
              <div>
                <h3
                  className="
                    font-semibold
                    text-slate-900
                  "
                >
                  Journal lines
                </h3>

                <p
                  className="
                    mt-1 text-sm
                    text-slate-500
                  "
                >
                  Use one side only on each
                  journal line.
                </p>
              </div>

              <button title="Add line"
                type="button"
                disabled={pending}
                onClick={() => {
                  append({
                    ...emptyLine,
                  });
                }}
                className="
                  inline-flex items-center
                  justify-center gap-2
                  rounded-lg border
                  border-blue-200 bg-blue-50
                  px-3 py-2 text-sm
                  font-semibold text-blue-700
                  hover:bg-blue-100
                  disabled:opacity-50
                "
              >
                <Plus size={16} /><span className="sr-only">Add line</span></button>
            </div>

            {accountQuery.isError ? (
              <div
                role="alert"
                className="
                  mt-4 rounded-lg border
                  border-red-200 bg-red-50
                  px-4 py-3 text-sm
                  text-red-700
                "
              >
                Unable to load posting accounts.
              </div>
            ) : null}

            <div className="mt-4 space-y-4">
              {fields.map(
                (
                  field,
                  index,
                ) => (
                  <div
                    key={field.id}
                    className="
                      grid gap-3 rounded-xl
                      border border-slate-200
                      bg-slate-50/50 p-4
                      lg:grid-cols-12
                    "
                  >
                    <label
                      className="
                        block text-xs
                        font-semibold uppercase
                        tracking-wide
                        text-slate-600
                        lg:col-span-4
                      "
                    >
                      Account

                      <SearchSelect
                        {...register(
                          `lines.${index}.account_id`
                        )}
                        disabled={
                          pending
                          ||
                          accountQuery
                            .isLoading
                        }
                        className="
                          mt-2 w-full
                          rounded-lg border
                          border-slate-300
                          bg-white px-3 py-2
                          text-sm outline-none
                          focus:border-blue-500
                          focus:ring-2
                          focus:ring-blue-100
                        "
                      >
                        <option value="">
                          Select account
                        </option>

                        {accounts.map(
                          (account) => (
                            <option
                              key={
                                account.id
                              }
                              value={
                                account.id
                              }
                            >
                              {
                                account.account_code
                              }
                              {" — "}
                              {
                                account.account_name
                              }
                            </option>
                          ),
                        )}
                      </SearchSelect>

                      {
                        errors.lines?.[
                          index
                        ]?.account_id
                        ? (
                          <span
                            className="
                              mt-1 block
                              text-xs
                              text-red-600
                            "
                          >
                            {
                              errors
                                .lines[
                                  index
                                ]
                                ?.account_id
                                ?.message
                            }
                          </span>
                        )
                        : null
                      }
                    </label>

                    <label
                      className="
                        block text-xs
                        font-semibold uppercase
                        tracking-wide
                        text-slate-600
                        lg:col-span-3
                      "
                    >
                      Description

                      <input
                        {...register(
                          `lines.${index}.description`
                        )}
                        disabled={pending}
                        className="
                          mt-2 w-full
                          rounded-lg border
                          border-slate-300
                          bg-white px-3 py-2
                          text-sm outline-none
                          focus:border-blue-500
                          focus:ring-2
                          focus:ring-blue-100
                        "
                      />
                    </label>

                    <label
                      className="
                        block text-xs
                        font-semibold uppercase
                        tracking-wide
                        text-slate-600
                        lg:col-span-2
                      "
                    >
                      Debit

                      <input
                        inputMode="decimal"
                        {...register(
                          `lines.${index}.debit`
                        )}
                        disabled={pending}
                        className="
                          mt-2 w-full
                          rounded-lg border
                          border-slate-300
                          bg-white px-3 py-2
                          text-right text-sm
                          outline-none
                          focus:border-blue-500
                          focus:ring-2
                          focus:ring-blue-100
                        "
                      />

                      {
                        errors.lines?.[
                          index
                        ]?.debit
                        ? (
                          <span
                            className="
                              mt-1 block
                              text-xs normal-case
                              tracking-normal
                              text-red-600
                            "
                          >
                            {
                              errors
                                .lines[
                                  index
                                ]
                                ?.debit
                                ?.message
                            }
                          </span>
                        )
                        : null
                      }
                    </label>

                    <label
                      className="
                        block text-xs
                        font-semibold uppercase
                        tracking-wide
                        text-slate-600
                        lg:col-span-2
                      "
                    >
                      Credit

                      <input
                        inputMode="decimal"
                        {...register(
                          `lines.${index}.credit`
                        )}
                        disabled={pending}
                        className="
                          mt-2 w-full
                          rounded-lg border
                          border-slate-300
                          bg-white px-3 py-2
                          text-right text-sm
                          outline-none
                          focus:border-blue-500
                          focus:ring-2
                          focus:ring-blue-100
                        "
                      />

                      {
                        errors.lines?.[
                          index
                        ]?.credit
                        ? (
                          <span
                            className="
                              mt-1 block
                              text-xs normal-case
                              tracking-normal
                              text-red-600
                            "
                          >
                            {
                              errors
                                .lines[
                                  index
                                ]
                                ?.credit
                                ?.message
                            }
                          </span>
                        )
                        : null
                      }
                    </label>

                    <div
                      className="
                        flex items-end
                        lg:col-span-1
                      "
                    >
                      <button
                        type="button"
                        aria-label={
                          "Remove journal line"
                        }
                        disabled={
                          pending
                          ||
                          fields.length <= 2
                        }
                        onClick={() => {
                          remove(
                            index
                          );
                        }}
                        className="
                          rounded-lg p-2
                          text-red-600
                          hover:bg-red-50
                          disabled:opacity-40
                        "
                      >
                        <Trash2 size={17} />
                      </button>
                    </div>
                  </div>
                ),
              )}
            </div>

            {errors.lines?.message ? (
              <p
                className="
                  mt-3 text-sm
                  text-red-600
                "
              >
                {errors.lines.message}
              </p>
            ) : null}

            <div
              className="
                mt-5 grid gap-3
                rounded-xl bg-slate-900
                p-4 text-white
                sm:grid-cols-3
              "
            >
              <div>
                <p
                  className="
                    text-xs uppercase
                    tracking-wide
                    text-slate-400
                  "
                >
                  Total debit
                </p>

                <p
                  className="
                    mt-1 text-lg font-bold
                  "
                >
                  ₹{formatAmount(
                    totalDebit
                  )}
                </p>
              </div>

              <div>
                <p
                  className="
                    text-xs uppercase
                    tracking-wide
                    text-slate-400
                  "
                >
                  Total credit
                </p>

                <p
                  className="
                    mt-1 text-lg font-bold
                  "
                >
                  ₹{formatAmount(
                    totalCredit
                  )}
                </p>
              </div>

              <div>
                <p
                  className="
                    text-xs uppercase
                    tracking-wide
                    text-slate-400
                  "
                >
                  Difference
                </p>

                <p
                  className={`
                    mt-1 text-lg font-bold
                    ${
                      balanced
                        ? "text-emerald-400"
                        : "text-amber-400"
                    }
                  `}
                >
                  ₹{formatAmount(
                    Math.abs(
                      difference
                    )
                  )}
                </p>
              </div>
            </div>

            {errors.root?.server
            ||
            mutationError ? (
              <div
                role="alert"
                className="
                  mt-4 rounded-lg border
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
          </div>

          <footer
            className="
              flex justify-end gap-3
              border-t border-slate-200
              px-6 py-4
            "
          >
            <button
              type="button"
              disabled={pending}
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
                pending
                ||
                !balanced
                ||
                accountQuery.isLoading
              }
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
              {pending ? (
                <LoaderCircle
                  size={16}
                  className="animate-spin"
                />
              ) : null}

              {editing
                ? "Save draft"
                : "Create journal"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}
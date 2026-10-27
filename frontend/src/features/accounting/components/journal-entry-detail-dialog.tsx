"use client";

import {
  useState,
} from "react";

import {
  LoaderCircle,
  Pencil,
  RotateCcw,
  Send,
  X,
} from "lucide-react";

import {
  useJournalEntry,
  usePostJournalEntry,
  useReverseJournalEntry,
} from "@/features/accounting/hooks";

import type {
  JournalEntryDetail,
} from "@/features/accounting/types";

import {
  APIRequestError,
} from "@/lib/api/client";

interface JournalEntryDetailDialogProps {
  open: boolean;
  journalId: string;
  canEdit: boolean;
  canPost: boolean;
  canReverse: boolean;
  onClose: () => void;
  onEdit: (
    journal: JournalEntryDetail,
  ) => void;
}

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

function formatAmount(
  value: string,
): string {
  const amount =
    Number(value);

  if (
    Number.isNaN(
      amount
    )
  ) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
    },
  ).format(
    amount,
  );
}

function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  const parsedDate =
    new Date(value);

  if (
    Number.isNaN(
      parsedDate.getTime()
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  ).format(
    parsedDate,
  );
}

function getErrorMessage(
  error: unknown,
): string {
  if (
    error
    instanceof
    APIRequestError
  ) {
    return error.message;
  }

  if (
    error
    instanceof
    Error
  ) {
    return error.message;
  }

  return (
    "Unable to load the journal entry."
  );
}

const statusStyles = {
  DRAFT:
    "bg-slate-100 text-slate-700",
  POSTED:
    "bg-blue-100 text-blue-700",
  REVERSED:
    "bg-amber-100 text-amber-700",
};

export default function JournalEntryDetailDialog({
  open,
  journalId,
  canEdit,
  canPost,
  canReverse,
  onClose,
  onEdit,
}: JournalEntryDetailDialogProps) {
  const [
    reverseMode,
    setReverseMode,
  ] = useState(false);

  const [
    reversalDate,
    setReversalDate,
  ] = useState(
    todayValue()
  );

  const [
    reversalDescription,
    setReversalDescription,
  ] = useState("");

  const journalQuery =
    useJournalEntry(
      journalId,
      open,
    );

  const postMutation =
    usePostJournalEntry();

  const reverseMutation =
    useReverseJournalEntry();

  if (!open) {
    return null;
  }

  const journal =
    journalQuery.data;

  const pending =
    postMutation.isPending
    ||
    reverseMutation.isPending;

  async function postJournal():
    Promise<void> {
    if (!journal) {
      return;
    }

    await postMutation.mutateAsync(
      journal.id,
    );
  }

  async function reverseJournal():
    Promise<void> {
    if (!journal) {
      return;
    }

    await reverseMutation
      .mutateAsync({
        journalId:
          journal.id,
        input: {
          reversal_date:
            reversalDate
            ||
            undefined,
          description:
            reversalDescription
            ||
            undefined,
        },
      });

    setReverseMode(false);
    setReversalDescription("");
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
          "journal-detail-title"
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
            flex items-start
            justify-between gap-4
            border-b border-slate-200
            px-6 py-4
          "
        >
          <div>
            <p
              className="
                text-xs font-semibold
                uppercase tracking-wide
                text-blue-600
              "
            >
              Journal Entry
            </p>

            <h2
              id="journal-detail-title"
              className="
                mt-1 text-xl font-bold
                text-slate-900
              "
            >
              {
                journal
                  ?.journal_number
                ??
                "Journal details"
              }
            </h2>
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

        {journalQuery.isLoading ? (
          <div
            className="
              flex items-center
              justify-center gap-2
              px-6 py-20 text-sm
              text-slate-500
            "
          >
            <LoaderCircle
              size={18}
              className="animate-spin"
            />
            Loading journal entry...
          </div>
        ) : journalQuery.isError ? (
          <div
            className="
              px-6 py-16 text-center
            "
          >
            <p
              className="
                text-sm font-semibold
                text-red-700
              "
            >
              {
                getErrorMessage(
                  journalQuery.error
                )
              }
            </p>

            <button
              type="button"
              onClick={() => {
                void journalQuery
                  .refetch();
              }}
              className="
                mt-4 rounded-lg border
                border-slate-300 px-4
                py-2 text-sm font-semibold
                text-slate-700
              "
            >
              Try again
            </button>
          </div>
        ) : journal ? (
          <>
            <div
              className="
                grid gap-4 border-b
                border-slate-200 px-6
                py-5 sm:grid-cols-2
                lg:grid-cols-4
              "
            >
              <div>
                <p
                  className="
                    text-xs font-semibold
                    uppercase tracking-wide
                    text-slate-500
                  "
                >
                  Status
                </p>

                <span
                  className={`
                    mt-2 inline-flex
                    rounded-full px-2.5
                    py-1 text-xs
                    font-semibold
                    ${
                      statusStyles[
                        journal.status
                      ]
                    }
                  `}
                >
                  {journal.status}
                </span>
              </div>

              <div>
                <p
                  className="
                    text-xs font-semibold
                    uppercase tracking-wide
                    text-slate-500
                  "
                >
                  Journal date
                </p>

                <p
                  className="
                    mt-2 text-sm font-semibold
                    text-slate-900
                  "
                >
                  {
                    formatDate(
                      journal.journal_date
                    )
                  }
                </p>
              </div>

              <div>
                <p
                  className="
                    text-xs font-semibold
                    uppercase tracking-wide
                    text-slate-500
                  "
                >
                  Source
                </p>

                <p
                  className="
                    mt-2 text-sm font-semibold
                    text-slate-900
                  "
                >
                  {journal.source_type}
                </p>
              </div>

              <div>
                <p
                  className="
                    text-xs font-semibold
                    uppercase tracking-wide
                    text-slate-500
                  "
                >
                  Lines
                </p>

                <p
                  className="
                    mt-2 text-sm font-semibold
                    text-slate-900
                  "
                >
                  {journal.line_count}
                </p>
              </div>
            </div>

            <div className="px-6 py-5">
              <p
                className="
                  text-sm text-slate-600
                "
              >
                {
                  journal.description
                  ??
                  "No journal description."
                }
              </p>

              <div
                className="
                  mt-5 overflow-hidden
                  rounded-xl border
                  border-slate-200
                "
              >
                <div className="overflow-x-auto">
                  <table
                    className="
                      min-w-full divide-y
                      divide-slate-200
                    "
                  >
                    <thead
                      className="bg-slate-50"
                    >
                      <tr>
                        {[
                          "Account",
                          "Description",
                          "Debit",
                          "Credit",
                        ].map(
                          (heading) => (
                            <th
                              key={heading}
                              className="
                                px-4 py-3
                                text-left text-xs
                                font-semibold
                                uppercase
                                tracking-wide
                                text-slate-500
                              "
                            >
                              {heading}
                            </th>
                          ),
                        )}
                      </tr>
                    </thead>

                    <tbody
                      className="
                        divide-y
                        divide-slate-100
                      "
                    >
                      {journal.lines.map(
                        (
                          line,
                          index,
                        ) => (
                          <tr
                            key={
                              `${line.account.id}-${index}`
                            }
                          >
                            <td
                              className="
                                px-4 py-3
                                text-sm font-semibold
                                text-slate-900
                              "
                            >
                              {
                                line.account
                                  .account_code
                              }
                              {" — "}
                              {
                                line.account
                                  .account_name
                              }
                            </td>

                            <td
                              className="
                                px-4 py-3
                                text-sm
                                text-slate-600
                              "
                            >
                              {
                                line.description
                                ??
                                "—"
                              }
                            </td>

                            <td
                              className="
                                px-4 py-3
                                text-right text-sm
                                font-semibold
                                text-slate-900
                              "
                            >
                              {
                                formatAmount(
                                  line.debit
                                )
                              }
                            </td>

                            <td
                              className="
                                px-4 py-3
                                text-right text-sm
                                font-semibold
                                text-slate-900
                              "
                            >
                              {
                                formatAmount(
                                  line.credit
                                )
                              }
                            </td>
                          </tr>
                        ),
                      )}
                    </tbody>

                    <tfoot
                      className="
                        border-t-2
                        border-slate-300
                        bg-slate-50
                      "
                    >
                      <tr>
                        <td
                          colSpan={2}
                          className="
                            px-4 py-3
                            text-sm font-bold
                            text-slate-900
                          "
                        >
                          Total
                        </td>

                        <td
                          className="
                            px-4 py-3
                            text-right text-sm
                            font-bold
                            text-slate-900
                          "
                        >
                          {
                            formatAmount(
                              journal.total_debit
                            )
                          }
                        </td>

                        <td
                          className="
                            px-4 py-3
                            text-right text-sm
                            font-bold
                            text-slate-900
                          "
                        >
                          {
                            formatAmount(
                              journal.total_credit
                            )
                          }
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              {journal.reversal_of_id ? (
                <p
                  className="
                    mt-4 text-sm
                    text-amber-700
                  "
                >
                  This journal reverses entry{" "}
                  {journal.reversal_of_id}.
                </p>
              ) : null}

              {journal.reversed_by_id ? (
                <p
                  className="
                    mt-4 text-sm
                    text-amber-700
                  "
                >
                  Reversed by entry{" "}
                  {journal.reversed_by_id}.
                </p>
              ) : null}

              {reverseMode ? (
                <div
                  className="
                    mt-5 rounded-xl border
                    border-amber-200
                    bg-amber-50 p-4
                  "
                >
                  <h3
                    className="
                      font-semibold
                      text-amber-900
                    "
                  >
                    Reverse this journal
                  </h3>

                  <p
                    className="
                      mt-1 text-sm
                      text-amber-800
                    "
                  >
                    A posted reversal entry
                    will be created automatically.
                  </p>

                  <div
                    className="
                      mt-4 grid gap-4
                      sm:grid-cols-3
                    "
                  >
                    <label
                      className="
                        text-sm font-medium
                        text-slate-700
                      "
                    >
                      Reversal date

                      <input
                        type="date"
                        value={reversalDate}
                        disabled={pending}
                        onChange={(event) => {
                          setReversalDate(
                            event.target.value
                          );
                        }}
                        className="
                          mt-2 w-full
                          rounded-lg border
                          border-slate-300
                          bg-white px-3 py-2
                          text-sm
                        "
                      />
                    </label>

                    <label
                      className="
                        text-sm font-medium
                        text-slate-700
                        sm:col-span-2
                      "
                    >
                      Description

                      <input
                        value={
                          reversalDescription
                        }
                        disabled={pending}
                        onChange={(event) => {
                          setReversalDescription(
                            event.target.value
                          );
                        }}
                        placeholder={
                          "Reason for reversal"
                        }
                        className="
                          mt-2 w-full
                          rounded-lg border
                          border-slate-300
                          bg-white px-3 py-2
                          text-sm
                        "
                      />
                    </label>
                  </div>

                  <div
                    className="
                      mt-4 flex justify-end
                      gap-3
                    "
                  >
                    <button
                      type="button"
                      disabled={pending}
                      onClick={() => {
                        setReverseMode(
                          false
                        );
                      }}
                      className="
                        rounded-lg border
                        border-slate-300
                        bg-white px-3 py-2
                        text-sm font-semibold
                        text-slate-700
                      "
                    >
                      Cancel
                    </button>

                    <button
                      type="button"
                      disabled={
                        pending
                        ||
                        !reversalDate
                      }
                      onClick={() => {
                        void reverseJournal();
                      }}
                      className="
                        inline-flex items-center
                        gap-2 rounded-lg
                        bg-amber-600 px-3
                        py-2 text-sm
                        font-semibold text-white
                        hover:bg-amber-700
                        disabled:opacity-50
                      "
                    >
                      {reverseMutation
                        .isPending ? (
                        <LoaderCircle
                          size={16}
                          className="
                            animate-spin
                          "
                        />
                      ) : null}

                      Confirm reversal
                    </button>
                  </div>
                </div>
              ) : null}

              {postMutation.error
              ||
              reverseMutation.error ? (
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
                    postMutation.error
                      ?.message
                    ??
                    reverseMutation.error
                      ?.message
                  }
                </div>
              ) : null}
            </div>

            <footer
              className="
                flex flex-wrap
                justify-end gap-3
                border-t border-slate-200
                px-6 py-4
              "
            >
              {journal.status === "DRAFT"
              &&
              canEdit ? (
                <button
                  type="button"
                  disabled={pending}
                  onClick={() => {
                    onEdit(
                      journal
                    );
                  }}
                  className="
                    inline-flex items-center
                    gap-2 rounded-lg
                    border border-slate-300
                    px-4 py-2 text-sm
                    font-semibold text-slate-700
                    hover:bg-slate-50
                  "
                >
                  <Pencil size={16} />
                  Edit draft
                </button>
              ) : null}

              {journal.status === "DRAFT"
              &&
              canPost ? (
                <button
                  type="button"
                  disabled={pending}
                  onClick={() => {
                    void postJournal();
                  }}
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
                  {postMutation.isPending ? (
                    <LoaderCircle
                      size={16}
                      className="animate-spin"
                    />
                  ) : (
                    <Send size={16} />
                  )}

                  Post journal
                </button>
              ) : null}

              {journal.status === "POSTED"
              &&
              journal.source_type
                !==
                "REVERSAL"
              &&
              canReverse
              &&
              !reverseMode ? (
                <button
                  type="button"
                  disabled={pending}
                  onClick={() => {
                    setReversalDate(
                      todayValue()
                    );
                    setReversalDescription(
                      ""
                    );
                    setReverseMode(
                      true
                    );
                  }}
                  className="
                    inline-flex items-center
                    gap-2 rounded-lg
                    bg-amber-600 px-4
                    py-2 text-sm
                    font-semibold text-white
                    hover:bg-amber-700
                    disabled:opacity-50
                  "
                >
                  <RotateCcw size={16} />
                  Reverse journal
                </button>
              ) : null}
            </footer>
          </>
        ) : null}
      </section>
    </div>
  );
}
"use client";
import SearchSelect from "@/components/search-select";


import {
  useDeferredValue,
  useState,
} from "react";

import {
  ChevronLeft,
  ChevronRight,
  Eye,
  Plus,
  Search,
} from "lucide-react";

import JournalEntryDetailDialog from "@/features/accounting/components/journal-entry-detail-dialog";
import JournalEntryFormDialog from "@/features/accounting/components/journal-entry-form-dialog";

import {
  useJournalEntryList,
} from "@/features/accounting/hooks";

import type {
  JournalEntryDetail,
  JournalEntryStatus,
  JournalSourceType,
} from "@/features/accounting/types";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  APIRequestError,
} from "@/lib/api/client";

const PAGE_SIZE = 25;

const statuses:
  Array<{
    value: JournalEntryStatus;
    label: string;
  }> = [
    {
      value: "DRAFT",
      label: "Draft",
    },
    {
      value: "POSTED",
      label: "Posted",
    },
    {
      value: "REVERSED",
      label: "Reversed",
    },
  ];

const sourceTypes:
  Array<{
    value: JournalSourceType;
    label: string;
  }> = [
    {
      value: "MANUAL",
      label: "Manual",
    },
    {value: "PAYROLL", label: "Payroll"},
    {value: "SALARY_PAYMENT", label: "Salary payment"},
    {value: "EMPLOYEE_ADVANCE", label: "Employee advance"},
    {value: "DAILY_EXPENSE", label: "Daily expense"},
    {
      value: "SALES_INVOICE",
      label: "Sales invoice",
    },
    {
      value: "CUSTOMER_PAYMENT",
      label: "Customer payment",
    },
    {
      value: "SALES_CREDIT_NOTE",
      label: "Sales credit note",
    },
    {
      value: "VENDOR_BILL",
      label: "Vendor bill",
    },
    {
      value: "SUPPLIER_PAYMENT",
      label: "Supplier payment",
    },
    {
      value: "VENDOR_DEBIT_NOTE",
      label: "Vendor debit note",
    },
    {
      value: "BANK_TRANSACTION",
      label: "Bank transaction",
    },
    {
      value: "OPENING_BALANCE",
      label: "Opening balance",
    },
    {
      value: "REVERSAL",
      label: "Reversal",
    },
  ];

const statusStyles:
  Record<
    JournalEntryStatus,
    string
  > = {
    DRAFT:
      "bg-slate-100 text-slate-700",
    POSTED:
      "bg-blue-100 text-blue-700",
    REVERSED:
      "bg-amber-100 text-amber-700",
  };

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

function formatSource(
  value: JournalSourceType,
): string {
  return (
    sourceTypes.find(
      (item) =>
        item.value === value,
    )
    ?.label
    ??
    value
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
    "Unable to load journal entries."
  );
}

export default function JournalEntriesPage() {
  const {
    authentication,
  } = useAuth();

  const [
    page,
    setPage,
  ] = useState(1);

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    status,
    setStatus,
  ] = useState<
    JournalEntryStatus | ""
  >("");

  const [
    sourceType,
    setSourceType,
  ] = useState<
    JournalSourceType | ""
  >("");

  const [
    sort,
    setSort,
  ] = useState(
    "-journal_date,-created_at",
  );

  const [
    formOpen,
    setFormOpen,
  ] = useState(false);

  const [
    editingJournal,
    setEditingJournal,
  ] = useState<
    JournalEntryDetail | null
  >(null);

  const [
    detailOpen,
    setDetailOpen,
  ] = useState(false);

  const [
    selectedJournalId,
    setSelectedJournalId,
  ] = useState("");

  const deferredSearch =
    useDeferredValue(
      search.trim(),
    );

  const permissions =
    authentication
      ?.role
      .permissions
      ??
      [];

  const canCreate =
    permissions.includes(
      "journal_entries.create",
    );

  const canPost =
    permissions.includes(
      "journal_entries.post",
    );

  const canReverse =
    permissions.includes(
      "journal_entries.reverse",
    );

  const journalQuery =
    useJournalEntryList({
      page,
      page_size: PAGE_SIZE,
      status:
        status
        ||
        undefined,
      source_type:
        sourceType
        ||
        undefined,
      search:
        deferredSearch
        ||
        undefined,
      sort,
    });

  const journals =
    journalQuery
      .data
      ?.journal_entries
      ??
      [];

  const pagination =
    journalQuery
      .data
      ?.pagination;

  function openCreate(): void {
    setEditingJournal(
      null
    );

    setDetailOpen(false);
    setFormOpen(true);
  }

  function openDetail(
    journalId: string,
  ): void {
    setSelectedJournalId(
      journalId
    );

    setFormOpen(false);
    setDetailOpen(true);
  }

  function editJournal(
    journal:
      JournalEntryDetail,
  ): void {
    setEditingJournal(
      journal
    );

    setDetailOpen(false);
    setFormOpen(true);
  }

  function handleSaved(
    journalId: string,
  ): void {
    setSelectedJournalId(
      journalId
    );

    setFormOpen(false);
    setDetailOpen(true);
  }

  return (
    <>
      <div
        className="
          space-y-6 text-slate-900
        "
      >
        <header
          className="
            flex flex-col gap-4
            sm:flex-row
            sm:items-start
            sm:justify-between
          "
        >
          <div>
            <p
              className="
                text-sm font-semibold
                text-blue-600
              "
            >
              Finance
            </p>

            <h1
              className="
                mt-1 text-2xl font-bold
                tracking-tight text-slate-950
                sm:text-3xl
              "
            >
              Journal Entries
            </h1>

            <p
              className="
                mt-2 max-w-2xl text-sm
                leading-6 text-slate-600
              "
            >
              Create balanced manual journals,
              review system-generated entries,
              post drafts, and create controlled
              reversals.
            </p>
          </div>

          {canCreate ? (
            <button title="Create journal"
              type="button"
              onClick={openCreate}
              className="
                inline-flex items-center
                justify-center gap-2
                rounded-lg bg-blue-600
                px-4 py-2.5 text-sm
                font-semibold text-white
                hover:bg-blue-700
              "
            >
              <Plus size={18} /><span className="sr-only">Create journal</span></button>
          ) : null}
        </header>

        <section
          className="
            rounded-2xl border
            border-slate-200 bg-white
            p-4 shadow-sm
          "
        >
          <div
            className="nx-list-filters
              grid gap-3
              md:grid-cols-2
              xl:grid-cols-4
            "
          >
            <label
              className="
                relative block
                md:col-span-2
              "
            >
              <span className="sr-only">
                Search journal entries
              </span>

              <Search
                size={18}
                className="
                  pointer-events-none
                  absolute left-3 top-1/2
                  -translate-y-1/2
                  text-slate-400
                "
              />

              <input
                value={search}
                onChange={(event) => {
                  setSearch(
                    event.target.value
                  );
                  setPage(1);
                }}
                placeholder={
                  "Search number, description, source..."
                }
                className="
                  w-full rounded-lg border
                  border-slate-300 py-2
                  pl-10 pr-3 text-sm
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                "
              />
            </label>

            <SearchSelect
              value={status}
              onChange={(event) => {
                setStatus(
                  event.target.value as
                    JournalEntryStatus | "",
                );
                setPage(1);
              }}
              className="
                rounded-lg border
                border-slate-300 bg-white
                px-3 py-2 text-sm
                outline-none
              "
            >
              <option value="">
                All statuses
              </option>

              {statuses.map(
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

            <SearchSelect
              value={sourceType}
              onChange={(event) => {
                setSourceType(
                  event.target.value as
                    JournalSourceType | "",
                );
                setPage(1);
              }}
              className="
                rounded-lg border
                border-slate-300 bg-white
                px-3 py-2 text-sm
                outline-none
              "
            >
              <option value="">
                All sources
              </option>

              {sourceTypes.map(
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
          </div>

          <div className="mt-3 flex justify-end">
            <SearchSelect
              value={sort}
              onChange={(event) => {
                setSort(
                  event.target.value
                );
                setPage(1);
              }}
              aria-label="Sort journal entries"
              className="
                rounded-lg border
                border-slate-300 bg-white
                px-3 py-2 text-sm
                outline-none
              "
            >
              <option
                value={
                  "-journal_date,-created_at"
                }
              >
                Newest journal date
              </option>

              <option
                value={
                  "journal_date,created_at"
                }
              >
                Oldest journal date
              </option>

              <option value="journal_number">
                Journal number
              </option>

              <option value="status">
                Status
              </option>

              <option value="-total_debit">
                Highest amount
              </option>
            </SearchSelect>
          </div>
        </section>

        <section
          className="
            overflow-hidden rounded-2xl
            border border-slate-200
            bg-white shadow-sm
          "
        >
          {journalQuery.isLoading ? (
            <div
              className="
                px-6 py-16 text-center
                text-sm text-slate-500
              "
            >
              Loading journal entries...
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
                  void journalQuery.refetch();
                }}
                className="
                  mt-4 rounded-lg border
                  border-slate-300 px-4
                  py-2 text-sm font-semibold
                  text-slate-700
                  hover:bg-slate-50
                "
              >
                Try again
              </button>
            </div>
          ) : journals.length === 0 ? (
            <div
              className="
                px-6 py-16 text-center
              "
            >
              <p
                className="
                  font-semibold text-slate-800
                "
              >
                No journal entries found
              </p>

              <p
                className="
                  mt-2 text-sm text-slate-500
                "
              >
                Adjust the filters or create
                a balanced manual journal.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table
                className="
                  min-w-full divide-y
                  divide-slate-200
                "
              >
                <thead className="bg-slate-50">
                  <tr>
                    {[
                      "Journal",
                      "Date",
                      "Source",
                      "Status",
                      "Debit",
                      "Credit",
                      "Actions",
                    ].map(
                      (heading) => (
                        <th
                          key={heading}
                          className="
                            px-5 py-3 text-left
                            text-xs font-semibold
                            uppercase tracking-wide
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
                    divide-y divide-slate-100
                  "
                >
                  {journals.map(
                    (journal) => (
                      <tr
                        key={journal.id}
                        className="
                          hover:bg-slate-50/70
                        "
                      >
                        <td className="px-5 py-4">
                          <p
                            className="
                              text-sm font-semibold
                              text-slate-900
                            "
                          >
                            {
                              journal
                                .journal_number
                            }
                          </p>

                          <p
                            className="
                              mt-1 max-w-xs
                              truncate text-xs
                              text-slate-500
                            "
                          >
                            {
                              journal.description
                              ??
                              "No description"
                            }
                          </p>
                        </td>

                        <td
                          className="
                            whitespace-nowrap
                            px-5 py-4 text-sm
                            text-slate-700
                          "
                        >
                          {
                            formatDate(
                              journal
                                .journal_date
                            )
                          }
                        </td>

                        <td
                          className="
                            px-5 py-4 text-sm
                            text-slate-700
                          "
                        >
                          {
                            formatSource(
                              journal
                                .source_type
                            )
                          }

                          <p
                            className="
                              mt-1 text-xs
                              text-slate-500
                            "
                          >
                            {
                              journal.line_count
                            }
                            {" lines"}
                          </p>
                        </td>

                        <td className="px-5 py-4">
                          <span
                            className={`
                              inline-flex rounded-full
                              px-2.5 py-1 text-xs
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
                        </td>

                        <td
                          className="
                            whitespace-nowrap
                            px-5 py-4 text-right
                            text-sm font-semibold
                            text-slate-900
                          "
                        >
                          {
                            formatAmount(
                              journal
                                .total_debit
                            )
                          }
                        </td>

                        <td
                          className="
                            whitespace-nowrap
                            px-5 py-4 text-right
                            text-sm font-semibold
                            text-slate-900
                          "
                        >
                          {
                            formatAmount(
                              journal
                                .total_credit
                            )
                          }
                        </td>

                        <td className="px-5 py-4">
                          <button
                            type="button"
                            onClick={() => {
                              openDetail(
                                journal.id
                              );
                            }}
                            aria-label={
                              `View ${journal.journal_number}`
                            }
                            className="
                              rounded-lg border
                              border-slate-300 p-2
                              text-slate-600
                              hover:bg-slate-50
                            "
                          >
                            <Eye size={16} />
                          </button>
                        </td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          )}

          {pagination ? (
            <footer
              className="
                flex flex-col gap-3
                border-t border-slate-200
                px-5 py-4
                sm:flex-row sm:items-center
                sm:justify-between
              "
            >
              <p
                className="
                  text-sm text-slate-500
                "
              >
                Page {pagination.page} of{" "}
                {Math.max(
                  pagination.total_pages,
                  1,
                )}
                {" • "}
                {pagination.total_items} journals
              </p>

              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={
                    !pagination.has_previous
                  }
                  onClick={() => {
                    setPage(
                      (current) =>
                        Math.max(
                          current - 1,
                          1,
                        ),
                    );
                  }}
                  className="
                    inline-flex items-center
                    gap-1 rounded-lg border
                    border-slate-300 px-3
                    py-2 text-sm font-semibold
                    text-slate-700
                    hover:bg-slate-50
                    disabled:opacity-40
                  "
                >
                  <ChevronLeft size={16} />
                  Previous
                </button>

                <button
                  type="button"
                  disabled={
                    !pagination.has_next
                  }
                  onClick={() => {
                    setPage(
                      (current) =>
                        current + 1,
                    );
                  }}
                  className="
                    inline-flex items-center
                    gap-1 rounded-lg border
                    border-slate-300 px-3
                    py-2 text-sm font-semibold
                    text-slate-700
                    hover:bg-slate-50
                    disabled:opacity-40
                  "
                >
                  Next
                  <ChevronRight size={16} />
                </button>
              </div>
            </footer>
          ) : null}
        </section>
      </div>

      <JournalEntryFormDialog
        open={formOpen}
        journal={editingJournal}
        onSaved={handleSaved}
        onClose={() => {
          setFormOpen(false);
          setEditingJournal(null);
        }}
      />

      <JournalEntryDetailDialog
        open={detailOpen}
        journalId={selectedJournalId}
        canEdit={canCreate}
        canPost={canPost}
        canReverse={canReverse}
        onEdit={editJournal}
        onClose={() => {
          setDetailOpen(false);
          setSelectedJournalId("");
        }}
      />
    </>
  );
}
"use client";
import SearchSelect from "@/components/search-select";


import {
  useDeferredValue,
  useState,
} from "react";

import {
  Ban,
  ChevronLeft,
  ChevronRight,
  Pencil,
  Plus,
  Search,
} from "lucide-react";

import {
  getChartOfAccount,
} from "@/features/accounting/api";

import AccountDeactivateDialog from "@/features/accounting/components/account-deactivate-dialog";
import AccountFormDialog from "@/features/accounting/components/account-form-dialog";

import {
  useChartOfAccountList,
} from "@/features/accounting/hooks";

import type {
  AccountType,
  ChartOfAccountDetail,
  ChartOfAccountSummary,
} from "@/features/accounting/types";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  APIRequestError,
} from "@/lib/api/client";

const PAGE_SIZE = 25;

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

const typeStyles:
  Record<AccountType, string> = {
    ASSET:
      "bg-blue-100 text-blue-700",
    LIABILITY:
      "bg-amber-100 text-amber-700",
    EQUITY:
      "bg-violet-100 text-violet-700",
    REVENUE:
      "bg-emerald-100 text-emerald-700",
    EXPENSE:
      "bg-rose-100 text-rose-700",
  };

function formatAccountType(
  value: AccountType,
): string {
  return (
    accountTypes.find(
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
    "Unable to load chart of accounts."
  );
}

export default function ChartOfAccountsPage() {
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
    accountType,
    setAccountType,
  ] = useState<AccountType | "">(
    "",
  );

  const [
    activeFilter,
    setActiveFilter,
  ] = useState<
    "all" | "active" | "inactive"
  >("active");

  const [
    sort,
    setSort,
  ] = useState("account_code");

  const [
    formOpen,
    setFormOpen,
  ] = useState(false);

  const [
    editingAccount,
    setEditingAccount,
  ] = useState<
    ChartOfAccountDetail | null
  >(null);

  const [
    editLoadingId,
    setEditLoadingId,
  ] = useState("");

  const [
    editError,
    setEditError,
  ] = useState("");

  const [
    deactivateOpen,
    setDeactivateOpen,
  ] = useState(false);

  const [
    selectedAccount,
    setSelectedAccount,
  ] = useState<
    ChartOfAccountSummary | null
  >(null);

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
      "chart_of_accounts.create",
    );

  const canUpdate =
    permissions.includes(
      "chart_of_accounts.update",
    );

  const canDeactivate =
    permissions.includes(
      "chart_of_accounts.deactivate",
    );

  const accountQuery =
    useChartOfAccountList({
      page,
      page_size: PAGE_SIZE,
      account_type:
        accountType
        ||
        undefined,
      is_active:
        activeFilter === "all"
          ? undefined
          : activeFilter === "active",
      search:
        deferredSearch
        ||
        undefined,
      sort,
    });

  const accounts =
    accountQuery
      .data
      ?.accounts
      ??
      [];

  const pagination =
    accountQuery
      .data
      ?.pagination;

  function openCreate(): void {
    setEditingAccount(
      null
    );

    setEditError("");
    setFormOpen(true);
  }

  async function openEdit(
    account:
      ChartOfAccountSummary,
  ): Promise<void> {
    setEditError("");
    setEditLoadingId(
      account.id
    );

    try {
      const detail =
        await getChartOfAccount(
          account.id,
        );

      setEditingAccount(
        detail
      );

      setFormOpen(true);
    } catch (error) {
      setEditError(
        getErrorMessage(
          error
        )
      );
    } finally {
      setEditLoadingId("");
    }
  }

  function openDeactivate(
    account:
      ChartOfAccountSummary,
  ): void {
    setSelectedAccount(
      account
    );

    setDeactivateOpen(true);
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
              Chart of Accounts
            </h1>

            <p
              className="
                mt-2 max-w-2xl text-sm
                leading-6 text-slate-600
              "
            >
              Maintain the accounts used for
              journal posting, ledgers, and
              financial reporting.
            </p>
          </div>

          {canCreate ? (
            <button title="Create account"
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
              <Plus size={18} /><span className="sr-only">Create account</span></button>
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
                Search accounts
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
                  "Search code, name, subtype..."
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
              value={accountType}
              onChange={(event) => {
                setAccountType(
                  event.target.value as AccountType | "",);
                setPage(1);
              }}
              className="
                rounded-lg border
                border-slate-300 bg-white
                px-3 py-2 text-sm
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            >
              <option value="">
                All account types
              </option>

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

            <SearchSelect
              value={activeFilter}
              onChange={(event) => {
                setActiveFilter(
                  event.target.value as (| "all"| "active"| "inactive"),
                );
                setPage(1);
              }}
              className="
                rounded-lg border
                border-slate-300 bg-white
                px-3 py-2 text-sm
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            >
              <option value="active">
                Active accounts
              </option>
              <option value="inactive">
                Inactive accounts
              </option>
              <option value="all">
                All accounts
              </option>
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
              aria-label="Sort accounts"
              className="
                rounded-lg border
                border-slate-300 bg-white
                px-3 py-2 text-sm
                outline-none
              "
            >
              <option value="account_code">
                Code: ascending
              </option>
              <option value="-account_code">
                Code: descending
              </option>
              <option value="account_name">
                Name: ascending
              </option>
              <option value="-account_name">
                Name: descending
              </option>
              <option value="account_type">
                Type
              </option>
              <option value="-updated_at">
                Recently updated
              </option>
            </SearchSelect>
          </div>
        </section>

        {editError ? (
          <div
            role="alert"
            className="
              rounded-xl border
              border-red-200 bg-red-50
              px-4 py-3 text-sm
              text-red-700
            "
          >
            {editError}
          </div>
        ) : null}

        <section
          className="
            overflow-hidden rounded-2xl
            border border-slate-200
            bg-white shadow-sm
          "
        >
          {accountQuery.isLoading ? (
            <div
              className="
                px-6 py-16 text-center
                text-sm text-slate-500
              "
            >
              Loading chart of accounts...
            </div>
          ) : accountQuery.isError ? (
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
                    accountQuery.error
                  )
                }
              </p>

              <button
                type="button"
                onClick={() => {
                  void accountQuery.refetch();
                }}
                className="
                  mt-4 rounded-lg
                  border border-slate-300
                  px-4 py-2 text-sm
                  font-semibold text-slate-700
                  hover:bg-slate-50
                "
              >
                Try again
              </button>
            </div>
          ) : accounts.length === 0 ? (
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
                No accounts found
              </p>

              <p
                className="
                  mt-2 text-sm text-slate-500
                "
              >
                Adjust the filters or create
                a new ledger account.
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
                      "Account",
                      "Type",
                      "Normal balance",
                      "Manual posting",
                      "Status",
                      "Actions",
                    ].map(
                      (heading) => (
                        <th
                          key={heading}
                          className="
                            px-5 py-3
                            text-left text-xs
                            font-semibold uppercase
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
                    divide-y divide-slate-100
                  "
                >
                  {accounts.map(
                    (account) => (
                      <tr
                        key={account.id}
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
                            {account.account_code}
                            {" — "}
                            {account.account_name}
                          </p>

                          <p
                            className="
                              mt-1 text-xs
                              text-slate-500
                            "
                          >
                            {
                              account.account_subtype
                              ??
                              "No subtype"
                            }

                            {account.system_key
                              ? (
                                <>
                                  {" • "}
                                  {account.system_key}
                                </>
                              )
                              : null}
                          </p>
                        </td>

                        <td className="px-5 py-4">
                          <span
                            className={`
                              inline-flex rounded-full
                              px-2.5 py-1 text-xs
                              font-semibold
                              ${
                                typeStyles[
                                  account
                                    .account_type
                                ]
                              }
                            `}
                          >
                            {
                              formatAccountType(
                                account.account_type
                              )
                            }
                          </span>
                        </td>

                        <td
                          className="
                            px-5 py-4 text-sm
                            text-slate-700
                          "
                        >
                          {
                            account.normal_balance
                          }
                        </td>

                        <td
                          className="
                            px-5 py-4 text-sm
                            text-slate-700
                          "
                        >
                          {
                            account
                              .allow_manual_posting
                            ? "Allowed"
                            : "Blocked"
                          }
                        </td>

                        <td className="px-5 py-4">
                          <span
                            className={`
                              inline-flex rounded-full
                              px-2.5 py-1 text-xs
                              font-semibold
                              ${
                                account.is_active
                                  ? (
                                    "bg-emerald-100 "
                                    +
                                    "text-emerald-700"
                                  )
                                  : (
                                    "bg-slate-100 "
                                    +
                                    "text-slate-600"
                                  )
                              }
                            `}
                          >
                            {
                              account.is_active
                              ? "Active"
                              : "Inactive"
                            }
                          </span>
                        </td>

                        <td className="px-5 py-4">
                          <div
                            className="
                              flex items-center
                              gap-2
                            "
                          >
                            {canUpdate ? (
                              <button
                                type="button"
                                disabled={
                                  editLoadingId
                                  ===
                                  account.id
                                }
                                onClick={() => {
                                  void openEdit(
                                    account
                                  );
                                }}
                                className="
                                  rounded-lg border
                                  border-slate-300
                                  p-2 text-slate-600
                                  hover:bg-slate-50
                                  disabled:opacity-50
                                "
                                aria-label={
                                  `Edit ${account.account_name}`
                                }
                              >
                                <Pencil
                                  size={16}
                                />
                              </button>
                            ) : null}

                            {canDeactivate
                            &&
                            account.is_active
                            &&
                            !account
                              .is_system_account ? (
                              <button
                                type="button"
                                onClick={() => {
                                  openDeactivate(
                                    account
                                  );
                                }}
                                className="
                                  rounded-lg border
                                  border-red-200 p-2
                                  text-red-600
                                  hover:bg-red-50
                                "
                                aria-label={
                                  `Deactivate ${account.account_name}`
                                }
                              >
                                <Ban size={16} />
                              </button>
                            ) : null}
                          </div>
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
                {pagination.total_items} accounts
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

      <AccountFormDialog
        open={formOpen}
        account={editingAccount}
        onClose={() => {
          setFormOpen(false);
          setEditingAccount(null);
        }}
      />

      <AccountDeactivateDialog
        open={deactivateOpen}
        account={selectedAccount}
        onClose={() => {
          setDeactivateOpen(false);
          setSelectedAccount(null);
        }}
      />
    </>
  );
}
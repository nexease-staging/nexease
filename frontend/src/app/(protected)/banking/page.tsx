"use client";
import SearchSelect from "@/components/search-select";


import {
  useDeferredValue,
  useState,
} from "react";

import {
  ArrowRightLeft,
  Ban,
  Banknote,
  ChevronLeft,
  ChevronRight,
  Eye,
  FileSpreadsheet,
  Pencil,
  Plus,
  ReceiptText,
  Search,
  Upload,
} from "lucide-react";

import {
  getBankAccount,
} from "@/features/banking/api";

import BankAccountDeactivateDialog from "@/features/banking/components/bank-account-deactivate-dialog";
import BankAccountFormDialog from "@/features/banking/components/bank-account-form-dialog";
import BankStatementDetailDialog from "@/features/banking/components/bank-statement-detail-dialog";
import BankStatementImportDialog from "@/features/banking/components/bank-statement-import-dialog";
import BankTransactionDetailDialog from "@/features/banking/components/bank-transaction-detail-dialog";
import BankTransactionFormDialog from "@/features/banking/components/bank-transaction-form-dialog";
import BankTransferDetailDialog from "@/features/banking/components/bank-transfer-detail-dialog";
import BankTransferFormDialog from "@/features/banking/components/bank-transfer-form-dialog";

import {
  useBankAccountList,
  useBankStatementList,
  useBankTransactionList,
  useBankTransferList,
} from "@/features/banking/hooks";

import type {
  BankAccountDetail,
  BankAccountSummary,
  BankAccountType,
  BankStatementSourceType,
  BankStatementStatus,
  BankTransactionType,
  BankTransferStatus,
  ReconciliationStatus,
} from "@/features/banking/types";

import {
  useAuth,
} from "@/features/auth/auth-context";

import type {
  APIPagination,
} from "@/lib/api/types";

const PAGE_SIZE = 25;

type BankingTab =
  | "accounts"
  | "transactions"
  | "transfers"
  | "statements";

function formatAmount(
  value: string,
  currency = "INR",
): string {
  const amount = Number(value);

  if (Number.isNaN(amount)) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
    },
  ).format(amount);
}

function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "â€”";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  ).format(parsed);
}

function Pagination({
  pagination,
  noun,
  onPage,
}: {
  pagination?: APIPagination;
  noun: string;
  onPage: (page: number) => void;
}) {
  if (!pagination) {
    return null;
  }

  return (
    <footer
      className="
        flex flex-col gap-3 border-t
        border-slate-200 px-5 py-4
        sm:flex-row sm:items-center
        sm:justify-between
      "
    >
      <p className="text-sm text-slate-500">
        Page {pagination.page} of{" "}
        {Math.max(pagination.total_pages, 1)}
        {" â€¢ "}
        {pagination.total_items} {noun}
      </p>

      <div className="flex gap-2">
        <button
          type="button"
          disabled={!pagination.has_previous}
          onClick={() => {
            onPage(Math.max(pagination.page - 1, 1));
          }}
          className="
            inline-flex items-center gap-1
            rounded-lg border border-slate-300
            px-3 py-2 text-sm font-semibold
            text-slate-700 hover:bg-slate-50
            disabled:opacity-40
          "
        >
          <ChevronLeft size={16} />
          Previous
        </button>

        <button
          type="button"
          disabled={!pagination.has_next}
          onClick={() => {
            onPage(pagination.page + 1);
          }}
          className="
            inline-flex items-center gap-1
            rounded-lg border border-slate-300
            px-3 py-2 text-sm font-semibold
            text-slate-700 hover:bg-slate-50
            disabled:opacity-40
          "
        >
          Next
          <ChevronRight size={16} />
        </button>
      </div>
    </footer>
  );
}

export default function BankingPage() {
  const { authentication } = useAuth();
  const permissions =
    authentication?.role.permissions ?? [];

  const [tab, setTab] =
    useState<BankingTab>("accounts");
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search.trim());

  const [accountPage, setAccountPage] = useState(1);
  const [accountType, setAccountType] =
    useState<BankAccountType | "">("");
  const [accountActive, setAccountActive] =
    useState<"all" | "active" | "inactive">("active");

  const [transactionPage, setTransactionPage] = useState(1);
  const [transactionType, setTransactionType] =
    useState<BankTransactionType | "">("");
  const [reconciliationStatus, setReconciliationStatus] =
    useState<ReconciliationStatus | "">("");

  const [transferPage, setTransferPage] = useState(1);
  const [transferStatus, setTransferStatus] =
    useState<BankTransferStatus | "">("");

  const [statementPage, setStatementPage] = useState(1);
  const [statementStatus, setStatementStatus] =
    useState<BankStatementStatus | "">("");
  const [statementSourceType, setStatementSourceType] =
    useState<BankStatementSourceType | "">("");

  const [accountFormOpen, setAccountFormOpen] = useState(false);
  const [editingAccount, setEditingAccount] =
    useState<BankAccountDetail | null>(null);
  const [accountDeactivateOpen, setAccountDeactivateOpen] =
    useState(false);
  const [selectedAccount, setSelectedAccount] =
    useState<BankAccountSummary | null>(null);
  const [editError, setEditError] = useState("");

  const [transactionFormOpen, setTransactionFormOpen] =
    useState(false);
  const [transactionDetailId, setTransactionDetailId] =
    useState("");

  const [transferFormOpen, setTransferFormOpen] =
    useState(false);
  const [transferDetailId, setTransferDetailId] =
    useState("");

  const [statementImportOpen, setStatementImportOpen] =
    useState(false);
  const [statementDetailId, setStatementDetailId] =
    useState("");

  const accountQuery = useBankAccountList({
    page: accountPage,
    page_size: PAGE_SIZE,
    account_type: accountType || undefined,
    is_active:
      accountActive === "all"
        ? undefined
        : accountActive === "active",
    search: tab === "accounts" ? deferredSearch || undefined : undefined,
    sort: "account_name",
  });

  const transactionQuery = useBankTransactionList({
    page: transactionPage,
    page_size: PAGE_SIZE,
    transaction_type: transactionType || undefined,
    reconciliation_status: reconciliationStatus || undefined,
    search: tab === "transactions" ? deferredSearch || undefined : undefined,
    sort: "-transaction_date,-created_at",
  });

  const transferQuery = useBankTransferList({
    page: transferPage,
    page_size: PAGE_SIZE,
    status: transferStatus || undefined,
    search: tab === "transfers" ? deferredSearch || undefined : undefined,
    sort: "-transfer_date,-created_at",
  });

  const statementQuery = useBankStatementList({
    page: statementPage,
    page_size: PAGE_SIZE,
    status: statementStatus || undefined,
    source_type: statementSourceType || undefined,
    search: tab === "statements" ? deferredSearch || undefined : undefined,
    sort: "-statement_end_date,-created_at",
  });

  const canCreateAccount = permissions.includes("bank_accounts.create");
  const canUpdateAccount = permissions.includes("bank_accounts.update");
  const canDeactivateAccount = permissions.includes("bank_accounts.deactivate");
  const canCreateTransaction = permissions.includes("bank_transactions.create");
  const canReconcile = permissions.includes("bank_transactions.reconcile");
  const canCreateTransfer = permissions.includes("bank_transfers.create");
  const canPostTransfer = permissions.includes("bank_transfers.post");
  const canCancelTransfer = permissions.includes("bank_transfers.cancel");
  const canCreateStatement = permissions.includes("bank_statements.create");
  const canReconcileStatement = permissions.includes("bank_statements.reconcile");
  const canCancelStatement = permissions.includes("bank_statements.cancel");

  async function openEditAccount(
    account: BankAccountSummary,
  ): Promise<void> {
    setEditError("");

    try {
      const detail = await getBankAccount(account.id);
      setEditingAccount(detail);
      setAccountFormOpen(true);
    } catch (error) {
      setEditError(
        error instanceof Error
          ? error.message
          : "Unable to load bank account.",
      );
    }
  }

  const inputClass = `
    rounded-lg border border-slate-300
    bg-white px-3 py-2 text-sm
    text-slate-900 outline-none
    placeholder:text-slate-400
    focus:border-blue-500
    focus:ring-2 focus:ring-blue-100
  `;

  const tabs: Array<{
    value: BankingTab;
    label: string;
    icon: typeof Banknote;
  }> = [
    { value: "accounts", label: "Accounts", icon: Banknote },
    { value: "transactions", label: "Transactions", icon: ReceiptText },
    { value: "transfers", label: "Transfers", icon: ArrowRightLeft },
    { value: "statements", label: "Statements", icon: FileSpreadsheet },
  ];

  return (
    <>
      <div className="space-y-6 text-slate-900">
        <header
          className="
            flex flex-col gap-4
            lg:flex-row lg:items-end
            lg:justify-between
          "
        >
          <div>
            <p className="text-sm font-semibold text-blue-600">
              Finance
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Banking
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-500">
              Manage cash and bank accounts, record transactions,
              reconcile activity, and transfer funds.
            </p>
          </div>

          {tab === "accounts" && canCreateAccount ? (
            <button title="New account"
              type="button"
              onClick={() => {
                setEditingAccount(null);
                setAccountFormOpen(true);
              }}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
            >
              <Plus size={17} /><span className="sr-only">New account</span></button>
          ) : tab === "transactions" && canCreateTransaction ? (
            <button title="New transaction"
              type="button"
              onClick={() => setTransactionFormOpen(true)}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
            >
              <Plus size={17} /><span className="sr-only">New transaction</span></button>
          ) : tab === "transfers" && canCreateTransfer ? (
            <button title="New transfer"
              type="button"
              onClick={() => setTransferFormOpen(true)}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
            >
              <Plus size={17} /><span className="sr-only">New transfer</span></button>
          ) : tab === "statements" && canCreateStatement ? (
            <button
              type="button"
              onClick={() => setStatementImportOpen(true)}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
            >
              <Upload size={17} />
              Import statement
            </button>
          ) : null}
        </header>

        <nav
          className="flex overflow-x-auto rounded-xl border border-slate-200 bg-white p-1"
          aria-label="Banking sections"
        >
          {tabs.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.value}
                type="button"
                onClick={() => {
                  setTab(item.value);
                  setSearch("");
                }}
                className={`
                  inline-flex min-w-max flex-1 items-center
                  justify-center gap-2 rounded-lg px-4 py-2.5
                  text-sm font-semibold
                  ${
                    tab === item.value
                      ? "bg-blue-600 text-white"
                      : "text-slate-600 hover:bg-slate-50"
                  }
                `}
              >
                <Icon size={17} />
                {item.label}
              </button>
            );
          })}
        </nav>

        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="nx-list-filters flex flex-col gap-3 border-b border-slate-200 p-5 lg:flex-row lg:items-center">
            <label className="relative flex-1">
              <Search
                size={17}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setAccountPage(1);
                  setTransactionPage(1);
                  setTransferPage(1);
                  setStatementPage(1);
                }}
                className={`${inputClass} w-full pl-9`}
                placeholder={`Search ${tab}...`}
              />
            </label>

            {tab === "accounts" ? (
              <>
                <SearchSelect
                  value={accountType}
                  onChange={(event) => {
                    setAccountType(event.target.value as BankAccountType | "");
                    setAccountPage(1);
                  }}
                  className={inputClass}
                >
                  <option value="">All types</option>
                  <option value="BANK">Bank</option>
                  <option value="CASH">Cash</option>
                </SearchSelect>
                <SearchSelect
                  value={accountActive}
                  onChange={(event) => {
                    setAccountActive(event.target.value as "all" | "active" | "inactive");
                    setAccountPage(1);
                  }}
                  className={inputClass}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="all">All statuses</option>
                </SearchSelect>
              </>
            ) : tab === "transactions" ? (
              <>
                <SearchSelect
                  value={transactionType}
                  onChange={(event) => {
                    setTransactionType(event.target.value as BankTransactionType | "");
                    setTransactionPage(1);
                  }}
                  className={inputClass}
                >
                  <option value="">All types</option>
                  <option value="MONEY_IN">Money in</option>
                  <option value="MONEY_OUT">Money out</option>
                  <option value="BANK_CHARGE">Bank charge</option>
                  <option value="INTEREST">Interest</option>
                  <option value="OTHER_IN">Other in</option>
                  <option value="OTHER_OUT">Other out</option>
                  <option value="OPENING_BALANCE">Opening balance</option>
                  <option value="TRANSFER_IN">Transfer in</option>
                  <option value="TRANSFER_OUT">Transfer out</option>
                </SearchSelect>
                <SearchSelect
                  value={reconciliationStatus}
                  onChange={(event) => {
                    setReconciliationStatus(event.target.value as ReconciliationStatus | "");
                    setTransactionPage(1);
                  }}
                  className={inputClass}
                >
                  <option value="">All reconciliation</option>
                  <option value="UNRECONCILED">Unreconciled</option>
                  <option value="RECONCILED">Reconciled</option>
                </SearchSelect>
              </>
            ) : tab === "transfers" ? (
              <SearchSelect
                value={transferStatus}
                onChange={(event) => {
                  setTransferStatus(event.target.value as BankTransferStatus | "");
                  setTransferPage(1);
                }}
                className={inputClass}
              >
                <option value="">All statuses</option>
                <option value="DRAFT">Draft</option>
                <option value="POSTED">Posted</option>
                <option value="CANCELLED">Cancelled</option>
              </SearchSelect>
            ) : (
              <>
                <SearchSelect
                  value={statementStatus}
                  onChange={(event) => {
                    setStatementStatus(event.target.value as BankStatementStatus | "");
                    setStatementPage(1);
                  }}
                  className={inputClass}
                >
                  <option value="">All statuses</option>
                  <option value="IMPORTED">Imported</option>
                  <option value="PARTIALLY_RECONCILED">Partially reconciled</option>
                  <option value="RECONCILED">Reconciled</option>
                  <option value="CANCELLED">Cancelled</option>
                </SearchSelect>
                <SearchSelect
                  value={statementSourceType}
                  onChange={(event) => {
                    setStatementSourceType(event.target.value as BankStatementSourceType | "");
                    setStatementPage(1);
                  }}
                  className={inputClass}
                >
                  <option value="">All sources</option>
                  <option value="CSV">CSV</option>
                  <option value="XLSX">XLSX</option>
                  <option value="MANUAL">Manual</option>
                </SearchSelect>
              </>
            )}
          </div>

          {editError ? (
            <div role="alert" className="m-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {editError}
            </div>
          ) : null}

          {tab === "accounts" ? (
            accountQuery.isLoading ? (
              <p className="p-12 text-center text-sm text-slate-500">Loading bank accounts...</p>
            ) : accountQuery.isError ? (
              <p className="p-12 text-center text-sm text-red-700">{accountQuery.error.message}</p>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="bg-slate-50">
                      <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                        <th className="px-5 py-3">Account</th>
                        <th className="px-5 py-3">Type</th>
                        <th className="px-5 py-3">Currency</th>
                        <th className="px-5 py-3">Balance</th>
                        <th className="px-5 py-3">Status</th>
                        <th className="px-5 py-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {(accountQuery.data?.bank_accounts ?? []).map((account) => (
                        <tr key={account.id} className="hover:bg-slate-50/70">
                          <td className="px-5 py-4">
                            <p className="text-sm font-semibold text-slate-900">{account.account_name}</p>
                            <p className="mt-1 text-xs text-slate-500">
                              {account.bank_name ?? "Cash account"}
                              {account.account_number ? ` â€¢ ${account.account_number}` : ""}
                            </p>
                          </td>
                          <td className="px-5 py-4 text-sm text-slate-700">{account.account_type}</td>
                          <td className="px-5 py-4 text-sm text-slate-700">{account.currency}</td>
                          <td className="px-5 py-4 text-sm font-semibold text-slate-900">
                            {formatAmount(account.current_balance, account.currency)}
                          </td>
                          <td className="px-5 py-4">
                            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${account.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
                              {account.is_active ? "Active" : "Inactive"}
                            </span>
                          </td>
                          <td className="px-5 py-4">
                            <div className="flex gap-2">
                              {canUpdateAccount ? (
                                <button
                                  type="button"
                                  onClick={() => void openEditAccount(account)}
                                  className="rounded-lg border border-slate-300 p-2 text-slate-600 hover:bg-slate-50"
                                  aria-label={`Edit ${account.account_name}`}
                                >
                                  <Pencil size={16} />
                                </button>
                              ) : null}
                              {canDeactivateAccount && account.is_active ? (
                                <button
                                  type="button"
                                  onClick={() => {
                                    setSelectedAccount(account);
                                    setAccountDeactivateOpen(true);
                                  }}
                                  className="rounded-lg border border-red-200 p-2 text-red-600 hover:bg-red-50"
                                  aria-label={`Deactivate ${account.account_name}`}
                                >
                                  <Ban size={16} />
                                </button>
                              ) : null}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <Pagination pagination={accountQuery.data?.pagination} noun="accounts" onPage={setAccountPage} />
              </>
            )
          ) : tab === "transactions" ? (
            transactionQuery.isLoading ? (
              <p className="p-12 text-center text-sm text-slate-500">Loading transactions...</p>
            ) : transactionQuery.isError ? (
              <p className="p-12 text-center text-sm text-red-700">{transactionQuery.error.message}</p>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="bg-slate-50">
                      <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                        <th className="px-5 py-3">Transaction</th>
                        <th className="px-5 py-3">Account</th>
                        <th className="px-5 py-3">Date</th>
                        <th className="px-5 py-3">Amount</th>
                        <th className="px-5 py-3">Reconciliation</th>
                        <th className="px-5 py-3">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {(transactionQuery.data?.bank_transactions ?? []).map((transaction) => (
                        <tr key={transaction.id} className="hover:bg-slate-50/70">
                          <td className="px-5 py-4">
                            <p className="text-sm font-semibold text-slate-900">{transaction.transaction_number}</p>
                            <p className="mt-1 text-xs text-slate-500">{transaction.transaction_type}</p>
                          </td>
                          <td className="px-5 py-4 text-sm text-slate-700">{transaction.bank_account.account_name}</td>
                          <td className="px-5 py-4 text-sm text-slate-700">{formatDate(transaction.transaction_date)}</td>
                          <td className="px-5 py-4 text-sm font-semibold text-slate-900">
                            {formatAmount(transaction.amount, transaction.bank_account.currency)}
                          </td>
                          <td className="px-5 py-4">
                            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${transaction.reconciliation_status === "RECONCILED" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                              {transaction.reconciliation_status}
                            </span>
                          </td>
                          <td className="px-5 py-4">
                            <button
                              type="button"
                              onClick={() => setTransactionDetailId(transaction.id)}
                              className="rounded-lg border border-slate-300 p-2 text-slate-600 hover:bg-slate-50"
                              aria-label={`View ${transaction.transaction_number}`}
                            >
                              <Eye size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <Pagination pagination={transactionQuery.data?.pagination} noun="transactions" onPage={setTransactionPage} />
              </>
            )
          ) : tab === "transfers" ? (
            transferQuery.isLoading ? (
            <p className="p-12 text-center text-sm text-slate-500">Loading transfers...</p>
          ) : transferQuery.isError ? (
            <p className="p-12 text-center text-sm text-red-700">{transferQuery.error.message}</p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <th className="px-5 py-3">Transfer</th>
                      <th className="px-5 py-3">From</th>
                      <th className="px-5 py-3">To</th>
                      <th className="px-5 py-3">Date</th>
                      <th className="px-5 py-3">Amount</th>
                      <th className="px-5 py-3">Status</th>
                      <th className="px-5 py-3">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(transferQuery.data?.bank_transfers ?? []).map((transfer) => (
                      <tr key={transfer.id} className="hover:bg-slate-50/70">
                        <td className="px-5 py-4 text-sm font-semibold text-slate-900">{transfer.transfer_number}</td>
                        <td className="px-5 py-4 text-sm text-slate-700">{transfer.source_account.account_name}</td>
                        <td className="px-5 py-4 text-sm text-slate-700">{transfer.destination_account.account_name}</td>
                        <td className="px-5 py-4 text-sm text-slate-700">{formatDate(transfer.transfer_date)}</td>
                        <td className="px-5 py-4 text-sm font-semibold text-slate-900">
                          {formatAmount(transfer.amount, transfer.source_account.currency)}
                        </td>
                        <td className="px-5 py-4">
                          <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${transfer.status === "POSTED" ? "bg-emerald-100 text-emerald-700" : transfer.status === "CANCELLED" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-700"}`}>
                            {transfer.status}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <button
                            type="button"
                            onClick={() => setTransferDetailId(transfer.id)}
                            className="rounded-lg border border-slate-300 p-2 text-slate-600 hover:bg-slate-50"
                            aria-label={`View ${transfer.transfer_number}`}
                          >
                            <Eye size={16} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination pagination={transferQuery.data?.pagination} noun="transfers" onPage={setTransferPage} />
            </>
            )
          ) : statementQuery.isLoading ? (
            <p className="p-12 text-center text-sm text-slate-500">Loading bank statements...</p>
          ) : statementQuery.isError ? (
            <p className="p-12 text-center text-sm text-red-700">{statementQuery.error.message}</p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <th className="px-5 py-3">Statement</th>
                      <th className="px-5 py-3">Bank account</th>
                      <th className="px-5 py-3">Period</th>
                      <th className="px-5 py-3">Closing balance</th>
                      <th className="px-5 py-3">Progress</th>
                      <th className="px-5 py-3">Status</th>
                      <th className="px-5 py-3">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(statementQuery.data?.bank_statements ?? []).map((statement) => {
                      const completed = statement.matched_count + statement.ignored_count;
                      const progress = statement.line_count > 0
                        ? Math.round((completed / statement.line_count) * 100)
                        : 0;

                      return (
                        <tr key={statement.id} className="hover:bg-slate-50/70">
                          <td className="px-5 py-4">
                            <p className="text-sm font-semibold text-slate-900">{statement.statement_number}</p>
                            <p className="mt-1 text-xs text-slate-500">
                              {statement.source_type}
                              {statement.source_filename ? ` · ${statement.source_filename}` : ""}
                            </p>
                          </td>
                          <td className="px-5 py-4 text-sm text-slate-700">
                            {statement.bank_account.account_name}
                          </td>
                          <td className="px-5 py-4 text-sm text-slate-700 whitespace-nowrap">
                            {formatDate(statement.statement_start_date)}
                            {" — "}
                            {formatDate(statement.statement_end_date)}
                          </td>
                          <td className="px-5 py-4 text-sm font-semibold text-slate-900 whitespace-nowrap">
                            {formatAmount(statement.closing_balance, statement.bank_account.currency)}
                          </td>
                          <td className="px-5 py-4">
                            <div className="min-w-32">
                              <div className="flex justify-between text-xs text-slate-500">
                                <span>{completed}/{statement.line_count}</span>
                                <span>{progress}%</span>
                              </div>
                              <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-200">
                                <div
                                  className="h-full rounded-full bg-emerald-500"
                                  style={{ width: `${progress}%` }}
                                />
                              </div>
                            </div>
                          </td>
                          <td className="px-5 py-4">
                            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                              statement.status === "RECONCILED"
                                ? "bg-emerald-100 text-emerald-700"
                                : statement.status === "CANCELLED"
                                  ? "bg-slate-200 text-slate-700"
                                  : statement.status === "PARTIALLY_RECONCILED"
                                    ? "bg-blue-100 text-blue-700"
                                    : "bg-amber-100 text-amber-700"
                            }`}>
                              {statement.status}
                            </span>
                          </td>
                          <td className="px-5 py-4">
                            <button
                              type="button"
                              onClick={() => setStatementDetailId(statement.id)}
                              className="rounded-lg border border-slate-300 p-2 text-slate-600 hover:bg-slate-50"
                              aria-label={`View ${statement.statement_number}`}
                            >
                              <Eye size={16} />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <Pagination pagination={statementQuery.data?.pagination} noun="statements" onPage={setStatementPage} />
            </>
          )}
        </section>
      </div>

      <BankAccountFormDialog
        open={accountFormOpen}
        account={editingAccount}
        onClose={() => {
          setAccountFormOpen(false);
          setEditingAccount(null);
        }}
      />
      <BankAccountDeactivateDialog
        open={accountDeactivateOpen}
        account={selectedAccount}
        onClose={() => {
          setAccountDeactivateOpen(false);
          setSelectedAccount(null);
        }}
      />
      <BankTransactionFormDialog
        open={transactionFormOpen}
        onClose={() => setTransactionFormOpen(false)}
      />
      <BankTransactionDetailDialog
        open={Boolean(transactionDetailId)}
        transactionId={transactionDetailId}
        canReconcile={canReconcile}
        onClose={() => setTransactionDetailId("")}
      />
      <BankTransferFormDialog
        open={transferFormOpen}
        onClose={() => setTransferFormOpen(false)}
      />
      <BankTransferDetailDialog
        open={Boolean(transferDetailId)}
        transferId={transferDetailId}
        canPost={canPostTransfer}
        canCancel={canCancelTransfer}
        onClose={() => setTransferDetailId("")}
      />
      <BankStatementImportDialog
        open={statementImportOpen}
        onClose={() => setStatementImportOpen(false)}
        onImported={(statementId) => {
          setStatementDetailId(statementId);
        }}
      />
      <BankStatementDetailDialog
        open={Boolean(statementDetailId)}
        statementId={statementDetailId}
        canReconcile={canReconcileStatement}
        canCancel={canCancelStatement}
        onClose={() => setStatementDetailId("")}
      />
    </>
  );
}

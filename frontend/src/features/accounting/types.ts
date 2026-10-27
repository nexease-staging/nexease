import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

export type AccountType =
  | "ASSET"
  | "LIABILITY"
  | "EQUITY"
  | "REVENUE"
  | "EXPENSE";

export type NormalBalance =
  | "DEBIT"
  | "CREDIT";

export type JournalEntryStatus =
  | "DRAFT"
  | "POSTED"
  | "REVERSED";

export type JournalSourceType =
  | "MANUAL"
  | "PAYROLL"
  | "SALARY_PAYMENT"
  | "EMPLOYEE_ADVANCE"
  | "DAILY_EXPENSE"
  | "SALES_INVOICE"
  | "CUSTOMER_PAYMENT"
  | "SALES_CREDIT_NOTE"
  | "VENDOR_BILL"
  | "SUPPLIER_PAYMENT"
  | "VENDOR_DEBIT_NOTE"
  | "BANK_TRANSACTION"
  | "OPENING_BALANCE"
  | "REVERSAL";

export interface AccountingCreator {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface ChartOfAccountSummary {
  id: string;
  account_code: string;
  account_name: string;
  account_type: AccountType;
  account_subtype: string | null;
  normal_balance: NormalBalance;
  system_key: string | null;
  is_system_account: boolean;
  is_active: boolean;
  allow_manual_posting: boolean;
}

export interface ChartOfAccountDetail
  extends ChartOfAccountSummary {
  description: string | null;
  created_by: AccountingCreator | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ChartOfAccountListData {
  accounts: ChartOfAccountSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface ChartOfAccountData {
  account: ChartOfAccountDetail;
}

export interface ChartOfAccountListParameters {
  page?: number;
  page_size?: number;
  account_type?: AccountType;
  account_subtype?: string;
  normal_balance?: NormalBalance;
  is_system_account?: boolean;
  is_active?: boolean;
  allow_manual_posting?: boolean;
  search?: string;
  sort?: string;
}

export interface CreateChartOfAccountInput {
  account_code: string;
  account_name: string;
  account_type: AccountType;
  account_subtype?: string;
  description?: string;
  allow_manual_posting?: boolean;
}

export interface UpdateChartOfAccountInput {
  account_name?: string;
  account_subtype?: string;
  description?: string;
  allow_manual_posting?: boolean;
}

export interface JournalEntryLine {
  account: ChartOfAccountSummary;
  description: string | null;
  debit: string;
  credit: string;
}

export interface JournalEntrySummary {
  id: string;
  journal_number: string;
  journal_date: string | null;
  description: string | null;
  source_type: JournalSourceType;
  source_id: string | null;
  status: JournalEntryStatus;
  total_debit: string;
  total_credit: string;
  line_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface JournalEntryDetail
  extends JournalEntrySummary {
  lines: JournalEntryLine[];
  posted_at: string | null;
  reversed_at: string | null;
  reversal_of_id: string | null;
  reversed_by_id: string | null;
  created_by: AccountingCreator | null;
}

export interface JournalEntryListData {
  journal_entries:
    JournalEntrySummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface JournalEntryData {
  journal_entry: JournalEntryDetail;
}

export interface JournalEntryListParameters {
  page?: number;
  page_size?: number;
  status?: JournalEntryStatus;
  source_type?: JournalSourceType;
  source_id?: string;
  search?: string;
  sort?: string;
}

export interface JournalEntryLineInput {
  account_id: string;
  description?: string;
  debit?: string;
  credit?: string;
}

export interface CreateJournalEntryInput {
  journal_date: string;
  description?: string;
  lines: JournalEntryLineInput[];
}

export interface UpdateJournalEntryInput {
  journal_date?: string;
  description?: string;
  lines?: JournalEntryLineInput[];
}

export interface ReverseJournalEntryInput {
  reversal_date?: string;
  description?: string;
}

export interface ReverseJournalEntryData {
  original: JournalEntryDetail;
  reversal: JournalEntryDetail;
}

export interface GeneralLedgerEntry {
  journal_number: string;
  journal_date: string | null;
  description: string | null;
  source_type: JournalSourceType;
  source_id: string | null;
  debit: string;
  credit: string;
  running_balance: string;
}

export interface GeneralLedger {
  account: ChartOfAccountDetail;
  start_date: string | null;
  end_date: string | null;
  opening_balance: string;
  entries: GeneralLedgerEntry[];
  total_debit: string;
  total_credit: string;
  closing_balance: string;
}

export interface GeneralLedgerData {
  general_ledger: GeneralLedger;
}

export interface GeneralLedgerParameters {
  account_id: string;
  start_date?: string;
  end_date?: string;
}

export interface TrialBalanceRow {
  account: ChartOfAccountSummary;
  total_debit: string;
  total_credit: string;
  debit_balance: string;
  credit_balance: string;
}

export interface TrialBalance {
  as_of_date: string | null;
  rows: TrialBalanceRow[];
  total_debit_balance: string;
  total_credit_balance: string;
  difference: string;
  is_balanced: boolean;
}

export interface TrialBalanceData {
  trial_balance: TrialBalance;
}

export interface TrialBalanceParameters {
  as_of_date?: string;
  include_zero_balances?: boolean;
}

export interface FinanceDashboardBankAccount {
  id: string;
  [key: string]: unknown;
  current_balance: string;
}

export interface FinanceDashboardBankAccounts {
  account_count: number;
  total_balance: string;
  accounts: FinanceDashboardBankAccount[];
}

export interface FinanceDashboardTransactions {
  total_in: string;
  total_out: string;
  net_cash_flow: string;
  [key: string]: unknown;
}

export interface FinanceDashboardStatements {
  [key: string]: unknown;
}

export interface FinanceDashboardPaymentSuggestions {
  [key: string]: unknown;
}

export interface FinanceDashboardReceivables {
  total_receivable: string;
  [key: string]: unknown;
}

export interface FinanceDashboardPayables {
  total_payable: string;
  [key: string]: unknown;
}

export interface FinanceDashboard {
  bank_accounts: FinanceDashboardBankAccounts;
  transactions: FinanceDashboardTransactions;
  statements: FinanceDashboardStatements;
  payment_suggestions:
    FinanceDashboardPaymentSuggestions;
  receivables: FinanceDashboardReceivables;
  payables: FinanceDashboardPayables;
}

export interface FinanceDashboardData {
  finance_dashboard: FinanceDashboard;
}

export interface AccountingDashboardSection {
  [key: string]:
    | string
    | number
    | boolean
    | null;
}

export interface AccountingDashboard {
  as_of_date: string | null;
  liquidity: AccountingDashboardSection;
  working_capital: AccountingDashboardSection;
  profitability: AccountingDashboardSection;
  balance_sheet: AccountingDashboardSection;
  trial_balance: AccountingDashboardSection;
  accounting_health:
    Record<string, unknown>;
}

export interface AccountingDashboardData {
  accounting_dashboard: AccountingDashboard;
}

export interface AccountingDashboardParameters {
  as_of_date?: string;
}

export interface CashFlowBankAccount {
  id?: string;
  [key: string]: unknown;
}

export interface CashFlowDailySummary {
  money_in: string;
  money_out: string;
  net_cash_flow: string;
  [key: string]: unknown;
}

export interface CashFlowTransaction {
  transaction_date: string | null;
  amount: string;
  signed_amount: string;
  [key: string]: unknown;
}

export interface CashFlowReport {
  start_date: string;
  end_date: string;
  bank_account:
    CashFlowBankAccount | null;
  opening_balance: string;
  total_in: string;
  total_out: string;
  net_cash_flow: string;
  closing_balance: string;
  transaction_count: number;
  reconciled_count: number;
  unreconciled_count: number;
  daily_summary: CashFlowDailySummary[];
  transactions: CashFlowTransaction[];
}

export interface CashFlowReportData {
  cash_flow: CashFlowReport;
}

export interface CashFlowReportParameters {
  start_date: string;
  end_date: string;
  bank_account_id?: string;
}

export interface FinanceAuditStatementExceptions {
  unmatched_lines:
    Record<string, unknown>[];

  invalid_matched_lines:
    Record<string, unknown>[];

  stale_unresolved_links:
    Record<string, unknown>[];
}

export interface FinanceAuditTransactionExceptions {
  unreconciled_transactions:
    Record<string, unknown>[];

  duplicate_matches:
    Record<string, unknown>[];
}

export interface FinanceAuditSuggestionExceptions {
  pending:
    Record<string, unknown>[];

  confirmed_unexecuted:
    Record<string, unknown>[];

  rejected:
    Record<string, unknown>[];

  invalid_execution_state:
    Record<string, unknown>[];
}

export interface FinanceAuditReport {
  healthy: boolean;

  critical_exception_count:
    number;

  attention_count:
    number;

  statement_exceptions:
    FinanceAuditStatementExceptions;

  transaction_exceptions:
    FinanceAuditTransactionExceptions;

  suggestion_exceptions:
    FinanceAuditSuggestionExceptions;

  invoice_exceptions:
    Record<string, unknown>[];

  vendor_bill_exceptions:
    Record<string, unknown>[];
}

export interface FinanceAuditData {
  finance_audit: FinanceAuditReport;
}
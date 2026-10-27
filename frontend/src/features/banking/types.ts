import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

import type {
  CustomerPaymentDetail,
  InvoiceSummary,
} from "@/features/invoices/types";

import type {
  SupplierPaymentDetail,
  VendorBillSummary,
} from "@/features/vendor-bills/types";

export type BankAccountType =
  | "BANK"
  | "CASH";

export type BankTransactionType =
  | "OPENING_BALANCE"
  | "MONEY_IN"
  | "MONEY_OUT"
  | "TRANSFER_IN"
  | "TRANSFER_OUT"
  | "BANK_CHARGE"
  | "INTEREST"
  | "OTHER_IN"
  | "OTHER_OUT";

export type ManualBankTransactionType =
  | "MONEY_IN"
  | "MONEY_OUT"
  | "BANK_CHARGE"
  | "INTEREST"
  | "OTHER_IN"
  | "OTHER_OUT";

export type ReconciliationStatus =
  | "UNRECONCILED"
  | "RECONCILED";

export type BankTransferStatus =
  | "DRAFT"
  | "POSTED"
  | "CANCELLED";

export interface BankingCreator {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface BankAccountSummary {
  id: string;
  account_name: string;
  account_type: BankAccountType;
  bank_name: string | null;
  account_number: string | null;
  ifsc_code: string | null;
  currency: string;
  opening_balance: string;
  current_balance: string;
  is_active: boolean;
}

export interface BankAccountDetail
  extends BankAccountSummary {
  created_by: BankingCreator | null;
  created_at: string;
  updated_at: string;
}

export interface BankAccountListParameters {
  page?: number;
  page_size?: number;
  account_type?: BankAccountType | "";
  currency?: string;
  is_active?: boolean;
  search?: string;
  sort?: string;
}

export interface BankAccountListData {
  bank_accounts: BankAccountSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface BankAccountData {
  bank_account: BankAccountDetail;
}

export interface CreateBankAccountInput {
  account_name: string;
  account_type: BankAccountType;
  bank_name?: string;
  account_number?: string;
  ifsc_code?: string;
  currency?: string;
  opening_balance?: string;
}

export interface UpdateBankAccountInput {
  account_name?: string;
  bank_name?: string;
  account_number?: string;
  ifsc_code?: string;
}

export interface BankTransactionSummary {
  id: string;
  bank_account: BankAccountSummary;
  transaction_number: string;
  transaction_type: BankTransactionType;
  transaction_date: string;
  amount: string;
  balance_before: string;
  balance_after: string;
  external_reference: string | null;
  description: string | null;
  reconciliation_status:
    ReconciliationStatus;
  reconciled_at: string | null;
}

export interface BankTransactionDetail
  extends BankTransactionSummary {
  reference_type: string | null;
  reference_id: string | null;
  created_by: BankingCreator | null;
  created_at: string;
}

export interface BankTransactionListParameters {
  page?: number;
  page_size?: number;
  bank_account_id?: string;
  transaction_type?:
    BankTransactionType | "";
  reconciliation_status?:
    ReconciliationStatus | "";
  search?: string;
  sort?: string;
}

export interface BankTransactionListData {
  bank_transactions:
    BankTransactionSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface BankTransactionData {
  bank_transaction:
    BankTransactionDetail;
}

export interface CreateBankTransactionInput {
  bank_account_id: string;
  transaction_type:
    ManualBankTransactionType;
  transaction_date: string;
  amount: string;
  reference_type?: string;
  reference_id?: string;
  external_reference?: string;
  description?: string;
}

export interface BankTransferSummary {
  id: string;
  transfer_number: string;
  source_account: BankAccountSummary;
  destination_account:
    BankAccountSummary;
  transfer_date: string;
  amount: string;
  status: BankTransferStatus;
  reference: string | null;
  created_at: string;
  updated_at: string;
}

export interface BankTransferDetail
  extends BankTransferSummary {
  notes: string | null;
  posted_at: string | null;
  cancelled_at: string | null;
  created_by: BankingCreator | null;
}

export interface BankTransferListParameters {
  page?: number;
  page_size?: number;
  source_account_id?: string;
  destination_account_id?: string;
  status?: BankTransferStatus | "";
  search?: string;
  sort?: string;
}

export interface BankTransferListData {
  bank_transfers: BankTransferSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface BankTransferData {
  bank_transfer: BankTransferDetail;
}

export interface CreateBankTransferInput {
  source_account_id: string;
  destination_account_id: string;
  transfer_date: string;
  amount: string;
  reference?: string;
  notes?: string;
}
export type BankStatementSourceType =
  | "MANUAL"
  | "CSV"
  | "XLSX";

export type BankStatementStatus =
  | "IMPORTED"
  | "PARTIALLY_RECONCILED"
  | "RECONCILED"
  | "CANCELLED";

export type BankStatementLineMatchStatus =
  | "UNMATCHED"
  | "MATCHED"
  | "IGNORED";

export interface BankStatementLine {
  line_number: number;
  transaction_date: string;
  value_date: string | null;
  description: string | null;
  external_reference: string | null;
  debit_amount: string;
  credit_amount: string;
  running_balance: string | null;
  match_status:
    BankStatementLineMatchStatus;
  matched_transaction:
    BankTransactionSummary | null;
  matched_at: string | null;
}

export interface BankStatementSummary {
  id: string;
  statement_number: string;
  bank_account: BankAccountSummary;
  statement_start_date: string;
  statement_end_date: string;
  opening_balance: string;
  closing_balance: string;
  source_filename: string | null;
  source_type:
    BankStatementSourceType;
  status: BankStatementStatus;
  line_count: number;
  matched_count: number;
  ignored_count: number;
  unmatched_count: number;
  created_at: string;
  updated_at: string;
}

export interface BankStatementDetail
  extends BankStatementSummary {
  lines: BankStatementLine[];
  reconciled_at: string | null;
  cancelled_at: string | null;
  created_by: BankingCreator | null;
}

export interface BankStatementListParameters {
  page?: number;
  page_size?: number;
  bank_account_id?: string;
  status?: BankStatementStatus | "";
  source_type?:
    BankStatementSourceType | "";
  search?: string;
  sort?: string;
}

export interface BankStatementListData {
  bank_statements:
    BankStatementSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface BankStatementData {
  bank_statement:
    BankStatementDetail;
}

export interface ImportBankStatementInput {
  file: File;
  bank_account_id: string;
  statement_start_date: string;
  statement_end_date: string;
  opening_balance: string;
  closing_balance: string;
}

export interface BankStatementLineActionData {
  statement: BankStatementSummary;
  line: BankStatementLine;
  transaction?:
    BankTransactionDetail | null;
}

export interface BankStatementAutoMatchData
  extends BankStatementLineActionData {
  matched: boolean;
  match_type: string | null;
  candidate_count: number | null;
}

export interface AutoMatchStatementLineInput {
  statementId: string;
  lineNumber: number;
  dateToleranceDays?: number;
}

export interface MatchStatementLineInput {
  statementId: string;
  lineNumber: number;
  transactionId: string;
}

export interface IgnoreStatementLineInput {
  statementId: string;
  lineNumber: number;
}

export type BankPaymentSuggestionType =
  | "CUSTOMER_RECEIPT"
  | "SUPPLIER_PAYMENT";

export type BankPaymentSuggestionStatus =
  | "PENDING"
  | "CONFIRMED"
  | "REJECTED";

export interface BankPaymentSuggestionSummary {
  id: string;
  statement: BankStatementSummary;
  line_number: string;
  suggestion_type:
    BankPaymentSuggestionType;
  invoice: InvoiceSummary | null;
  vendor_bill:
    VendorBillSummary | null;
  amount: string;
  confidence: string;
  match_reason: string | null;
  status:
    BankPaymentSuggestionStatus;
  is_executed: boolean;
  payment_reference: string | null;
  created_at: string;
  updated_at: string;
}

export interface BankPaymentSuggestionDetail
  extends BankPaymentSuggestionSummary {
  confirmed_at: string | null;
  rejected_at: string | null;
  executed_at: string | null;
  created_by: BankingCreator | null;
}

export interface BankPaymentSuggestionListParameters {
  page?: number;
  page_size?: number;
  statement_id?: string;
  invoice_id?: string;
  vendor_bill_id?: string;
  suggestion_type?:
    BankPaymentSuggestionType | "";
  status?:
    BankPaymentSuggestionStatus | "";
  search?: string;
  sort?: string;
}

export interface BankPaymentSuggestionListData {
  bank_payment_suggestions:
    BankPaymentSuggestionSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface BankPaymentSuggestionData {
  bank_payment_suggestion:
    BankPaymentSuggestionDetail;
}

export interface GeneratePaymentSuggestionInput {
  statementId: string;
  lineNumber: number;
}

export interface BankPaymentSuggestionExecution {
  suggestion:
    BankPaymentSuggestionDetail;
  payment:
    | CustomerPaymentDetail
    | SupplierPaymentDetail;
  bank_transaction:
    BankTransactionDetail;
}

export interface BankPaymentSuggestionExecutionData {
  execution:
    BankPaymentSuggestionExecution;
}
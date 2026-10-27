import {
  apiRequest,
} from "@/lib/api/client";

import type {
  AutoMatchStatementLineInput,
  BankAccountData,
  BankAccountDetail,
  BankAccountListData,
  BankAccountListParameters,
  BankPaymentSuggestionData,
  BankPaymentSuggestionDetail,
  BankPaymentSuggestionExecution,
  BankPaymentSuggestionExecutionData,
  BankPaymentSuggestionListData,
  BankPaymentSuggestionListParameters,
  BankStatementAutoMatchData,
  BankStatementData,
  BankStatementDetail,
  BankStatementLineActionData,
  BankStatementListData,
  BankStatementListParameters,
  BankTransactionData,
  BankTransactionDetail,
  BankTransactionListData,
  BankTransactionListParameters,
  BankTransferData,
  BankTransferDetail,
  BankTransferListData,
  BankTransferListParameters,
  CreateBankAccountInput,
  CreateBankTransactionInput,
  CreateBankTransferInput,
  GeneratePaymentSuggestionInput,
  IgnoreStatementLineInput,
  ImportBankStatementInput,
  MatchStatementLineInput,
  UpdateBankAccountInput,
} from "@/features/banking/types";

type QueryValue =
  | string
  | number
  | boolean
  | undefined;

function buildQuery(
  parameters: Record<
    string,
    QueryValue
  >,
): string {
  const searchParameters =
    new URLSearchParams();

  for (
    const [
      key,
      value,
    ]
    of Object.entries(
      parameters,
    )
  ) {
    if (
      value === undefined
      ||
      value === ""
    ) {
      continue;
    }

    searchParameters.set(
      key,
      String(
        value,
      ),
    );
  }

  const query =
    searchParameters.toString();

  return query
    ? `?${query}`
    : "";
}

export async function listBankAccounts(
  parameters:
    BankAccountListParameters = {},
): Promise<BankAccountListData> {
  const response =
    await apiRequest<
      BankAccountListData
    >(
      (
        "/bank-accounts/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          account_type:
            parameters.account_type,
          currency:
            parameters.currency,
          is_active:
            parameters.is_active,
          search:
            parameters.search,
          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}

export async function getBankAccount(
  bankAccountId: string,
): Promise<BankAccountDetail> {
  const response =
    await apiRequest<
      BankAccountData
    >(
      (
        "/bank-accounts/"
        +
        `${bankAccountId}/`
      ),
    );

  return response
    .data
    .bank_account;
}

export async function createBankAccount(
  input: CreateBankAccountInput,
): Promise<BankAccountDetail> {
  const response =
    await apiRequest<
      BankAccountData
    >(
      "/bank-accounts/",
      {
        method: "POST",
        body: input,
      },
    );

  return response
    .data
    .bank_account;
}

export async function updateBankAccount(
  bankAccountId: string,
  input: UpdateBankAccountInput,
): Promise<BankAccountDetail> {
  const response =
    await apiRequest<
      BankAccountData
    >(
      (
        "/bank-accounts/"
        +
        `${bankAccountId}/`
      ),
      {
        method: "PATCH",
        body: input,
      },
    );

  return response
    .data
    .bank_account;
}

export async function deactivateBankAccount(
  bankAccountId: string,
): Promise<BankAccountDetail> {
  const response =
    await apiRequest<
      BankAccountData
    >(
      (
        "/bank-accounts/"
        +
        `${bankAccountId}/deactivate/`
      ),
      {
        method: "POST",
      },
    );

  return response
    .data
    .bank_account;
}

export async function listBankTransactions(
  parameters:
    BankTransactionListParameters = {},
): Promise<BankTransactionListData> {
  const response =
    await apiRequest<
      BankTransactionListData
    >(
      (
        "/bank-transactions/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          bank_account_id:
            parameters.bank_account_id,
          transaction_type:
            parameters.transaction_type,
          reconciliation_status:
            parameters
              .reconciliation_status,
          search:
            parameters.search,
          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}

export async function getBankTransaction(
  transactionId: string,
): Promise<BankTransactionDetail> {
  const response =
    await apiRequest<
      BankTransactionData
    >(
      (
        "/bank-transactions/"
        +
        `${transactionId}/`
      ),
    );

  return response
    .data
    .bank_transaction;
}

export async function createBankTransaction(
  input: CreateBankTransactionInput,
): Promise<BankTransactionDetail> {
  const response =
    await apiRequest<
      BankTransactionData
    >(
      "/bank-transactions/",
      {
        method: "POST",
        body: input,
      },
    );

  return response
    .data
    .bank_transaction;
}

export async function reconcileBankTransaction(
  transactionId: string,
): Promise<BankTransactionDetail> {
  const response =
    await apiRequest<
      BankTransactionData
    >(
      (
        "/bank-transactions/"
        +
        `${transactionId}/reconcile/`
      ),
      {
        method: "POST",
      },
    );

  return response
    .data
    .bank_transaction;
}

export async function listBankTransfers(
  parameters:
    BankTransferListParameters = {},
): Promise<BankTransferListData> {
  const response =
    await apiRequest<
      BankTransferListData
    >(
      (
        "/bank-transfers/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          source_account_id:
            parameters
              .source_account_id,
          destination_account_id:
            parameters
              .destination_account_id,
          status:
            parameters.status,
          search:
            parameters.search,
          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}

export async function getBankTransfer(
  transferId: string,
): Promise<BankTransferDetail> {
  const response =
    await apiRequest<
      BankTransferData
    >(
      (
        "/bank-transfers/"
        +
        `${transferId}/`
      ),
    );

  return response
    .data
    .bank_transfer;
}

export async function createBankTransfer(
  input: CreateBankTransferInput,
): Promise<BankTransferDetail> {
  const response =
    await apiRequest<
      BankTransferData
    >(
      "/bank-transfers/",
      {
        method: "POST",
        body: input,
      },
    );

  return response
    .data
    .bank_transfer;
}

export async function postBankTransfer(
  transferId: string,
): Promise<BankTransferDetail> {
  const response =
    await apiRequest<
      BankTransferData
    >(
      (
        "/bank-transfers/"
        +
        `${transferId}/post/`
      ),
      {
        method: "POST",
      },
    );

  return response
    .data
    .bank_transfer;
}

export async function cancelBankTransfer(
  transferId: string,
): Promise<BankTransferDetail> {
  const response =
    await apiRequest<
      BankTransferData
    >(
      (
        "/bank-transfers/"
        +
        `${transferId}/cancel/`
      ),
      {
        method: "POST",
      },
    );

  return response
    .data
    .bank_transfer;
}
export async function listBankStatements(
  parameters:
    BankStatementListParameters = {},
): Promise<BankStatementListData> {
  const response =
    await apiRequest<
      BankStatementListData
    >(
      (
        "/bank-statements/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          bank_account_id:
            parameters.bank_account_id,
          status:
            parameters.status,
          source_type:
            parameters.source_type,
          search:
            parameters.search,
          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}

export async function getBankStatement(
  statementId: string,
): Promise<BankStatementDetail> {
  const response =
    await apiRequest<
      BankStatementData
    >(
      (
        "/bank-statements/"
        +
        `${statementId}/`
      ),
    );

  return response
    .data
    .bank_statement;
}

export async function importBankStatement(
  input: ImportBankStatementInput,
): Promise<BankStatementDetail> {
  const formData =
    new FormData();

  formData.append(
    "file",
    input.file,
  );

  formData.append(
    "bank_account_id",
    input.bank_account_id,
  );

  formData.append(
    "statement_start_date",
    input.statement_start_date,
  );

  formData.append(
    "statement_end_date",
    input.statement_end_date,
  );

  formData.append(
    "opening_balance",
    input.opening_balance,
  );

  formData.append(
    "closing_balance",
    input.closing_balance,
  );

  const response =
    await apiRequest<
      BankStatementData
    >(
      "/bank-statements/",
      {
        method: "POST",
        body: formData,
      },
    );

  return response
    .data
    .bank_statement;
}

export async function cancelBankStatement(
  statementId: string,
): Promise<BankStatementDetail> {
  const response =
    await apiRequest<
      BankStatementData
    >(
      (
        "/bank-statements/"
        +
        `${statementId}/cancel/`
      ),
      {
        method: "POST",
      },
    );

  return response
    .data
    .bank_statement;
}

export async function autoMatchStatementLine(
  input: AutoMatchStatementLineInput,
): Promise<BankStatementAutoMatchData> {
  const response =
    await apiRequest<
      BankStatementAutoMatchData
    >(
      (
        "/bank-statements/"
        +
        `${input.statementId}/lines/`
        +
        `${input.lineNumber}/auto-match/`
      ),
      {
        method: "POST",
        body: {
          date_tolerance_days:
            input.dateToleranceDays
            ??
            2,
        },
      },
    );

  return response.data;
}

export async function matchStatementLine(
  input: MatchStatementLineInput,
): Promise<BankStatementLineActionData> {
  const response =
    await apiRequest<
      BankStatementLineActionData
    >(
      (
        "/bank-statements/"
        +
        `${input.statementId}/lines/`
        +
        `${input.lineNumber}/match/`
      ),
      {
        method: "POST",
        body: {
          transaction_id:
            input.transactionId,
        },
      },
    );

  return response.data;
}

export async function ignoreStatementLine(
  input: IgnoreStatementLineInput,
): Promise<BankStatementLineActionData> {
  const response =
    await apiRequest<
      BankStatementLineActionData
    >(
      (
        "/bank-statements/"
        +
        `${input.statementId}/lines/`
        +
        `${input.lineNumber}/ignore/`
      ),
      {
        method: "POST",
      },
    );

  return response.data;
}

export async function listBankPaymentSuggestions(
  parameters:
    BankPaymentSuggestionListParameters = {},
): Promise<BankPaymentSuggestionListData> {
  const response =
    await apiRequest<
      BankPaymentSuggestionListData
    >(
      (
        "/bank-payment-suggestions/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          statement_id:
            parameters.statement_id,
          invoice_id:
            parameters.invoice_id,
          vendor_bill_id:
            parameters.vendor_bill_id,
          suggestion_type:
            parameters.suggestion_type,
          status:
            parameters.status,
          search:
            parameters.search,
          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}

export async function getBankPaymentSuggestion(
  suggestionId: string,
): Promise<BankPaymentSuggestionDetail> {
  const response =
    await apiRequest<
      BankPaymentSuggestionData
    >(
      (
        "/bank-payment-suggestions/"
        +
        `${suggestionId}/`
      ),
    );

  return response
    .data
    .bank_payment_suggestion;
}

export async function generateBankPaymentSuggestion(
  input: GeneratePaymentSuggestionInput,
): Promise<BankPaymentSuggestionDetail> {
  const response =
    await apiRequest<
      BankPaymentSuggestionData
    >(
      (
        "/bank-statements/"
        +
        `${input.statementId}/lines/`
        +
        `${input.lineNumber}/`
        +
        "payment-suggestion/"
      ),
      {
        method: "POST",
      },
    );

  return response
    .data
    .bank_payment_suggestion;
}

export async function confirmBankPaymentSuggestion(
  suggestionId: string,
): Promise<BankPaymentSuggestionDetail> {
  const response =
    await apiRequest<
      BankPaymentSuggestionData
    >(
      (
        "/bank-payment-suggestions/"
        +
        `${suggestionId}/confirm/`
      ),
      {
        method: "POST",
      },
    );

  return response
    .data
    .bank_payment_suggestion;
}

export async function rejectBankPaymentSuggestion(
  suggestionId: string,
): Promise<BankPaymentSuggestionDetail> {
  const response =
    await apiRequest<
      BankPaymentSuggestionData
    >(
      (
        "/bank-payment-suggestions/"
        +
        `${suggestionId}/reject/`
      ),
      {
        method: "POST",
      },
    );

  return response
    .data
    .bank_payment_suggestion;
}

export async function executeBankPaymentSuggestion(
  suggestionId: string,
): Promise<BankPaymentSuggestionExecution> {
  const response =
    await apiRequest<
      BankPaymentSuggestionExecutionData
    >(
      (
        "/bank-payment-suggestions/"
        +
        `${suggestionId}/execute/`
      ),
      {
        method: "POST",
      },
    );

  return response
    .data
    .execution;
}
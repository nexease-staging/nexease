import {
  apiRequest,
} from "@/lib/api/client";

import type {
  AccountsReceivableData,
  AccountsReceivableSummary,
  ReceivableAgingData,
  ReceivableAgingSummary,
} from "@/features/receivables/types";

export async function getAccountsReceivable():
  Promise<AccountsReceivableSummary> {
  const response =
    await apiRequest<
      AccountsReceivableData
    >(
      "/accounts-receivable/",
    );

  return response
    .data
    .accounts_receivable;
}

export async function getReceivableAging():
  Promise<ReceivableAgingSummary> {
  const response =
    await apiRequest<
      ReceivableAgingData
    >(
      (
        "/accounts-receivable/"
        +
        "aging/"
      ),
    );

  return response.data.aging;
}
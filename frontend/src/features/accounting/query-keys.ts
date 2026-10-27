import type {
  AccountingDashboardParameters,
  CashFlowReportParameters,
  ChartOfAccountListParameters,
  GeneralLedgerParameters,
  JournalEntryListParameters,
  TrialBalanceParameters,
} from "@/features/accounting/types";

export const accountingQueryKeys = {
  all: [
    "accounting",
  ] as const,

  accounts: () => [
    ...accountingQueryKeys.all,
    "accounts",
  ] as const,

  accountLists: () => [
    ...accountingQueryKeys.accounts(),
    "list",
  ] as const,

  accountList: (
    parameters:
      ChartOfAccountListParameters,
  ) => [
    ...accountingQueryKeys
      .accountLists(),
    parameters,
  ] as const,

  accountDetails: () => [
    ...accountingQueryKeys.accounts(),
    "detail",
  ] as const,

  accountDetail: (
    accountId: string,
  ) => [
    ...accountingQueryKeys
      .accountDetails(),
    accountId,
  ] as const,

  journals: () => [
    ...accountingQueryKeys.all,
    "journals",
  ] as const,

  journalLists: () => [
    ...accountingQueryKeys.journals(),
    "list",
  ] as const,

  journalList: (
    parameters:
      JournalEntryListParameters,
  ) => [
    ...accountingQueryKeys
      .journalLists(),
    parameters,
  ] as const,

  journalDetails: () => [
    ...accountingQueryKeys.journals(),
    "detail",
  ] as const,

  journalDetail: (
    journalId: string,
  ) => [
    ...accountingQueryKeys
      .journalDetails(),
    journalId,
  ] as const,

  ledgers: () => [
    ...accountingQueryKeys.all,
    "general-ledger",
  ] as const,

  ledger: (
    parameters:
      GeneralLedgerParameters,
  ) => [
    ...accountingQueryKeys.ledgers(),
    parameters,
  ] as const,

  trialBalances: () => [
    ...accountingQueryKeys.all,
    "trial-balance",
  ] as const,

  trialBalance: (
    parameters:
      TrialBalanceParameters,
  ) => [
    ...accountingQueryKeys
      .trialBalances(),
    parameters,
  ] as const,
  reports: () => [
    ...accountingQueryKeys.all,
    "reports",
  ] as const,

  financeDashboards: () => [
    ...accountingQueryKeys.reports(),
    "finance-dashboard",
  ] as const,

  financeDashboard: () => [
    ...accountingQueryKeys
      .financeDashboards(),
  ] as const,

  accountingDashboards: () => [
    ...accountingQueryKeys.reports(),
    "accounting-dashboard",
  ] as const,

  accountingDashboard: (
    parameters:
      AccountingDashboardParameters,
  ) => [
    ...accountingQueryKeys
      .accountingDashboards(),
    parameters,
  ] as const,

  cashFlows: () => [
    ...accountingQueryKeys.reports(),
    "cash-flow",
  ] as const,

  cashFlow: (
    parameters:
      CashFlowReportParameters,
  ) => [
    ...accountingQueryKeys.cashFlows(),
    parameters,
  ] as const,

  financeAudits: () => [
    ...accountingQueryKeys.reports(),
    "finance-audit",
  ] as const,

  financeAudit: () => [
    ...accountingQueryKeys
      .financeAudits(),
  ] as const,
};
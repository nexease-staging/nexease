import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createChartOfAccount,
  createJournalEntry,
  deactivateChartOfAccount,
  getChartOfAccount,
  getGeneralLedger,
  getJournalEntry,
  getTrialBalance,
  listChartOfAccounts,
  listJournalEntries,
  postJournalEntry,
  reverseJournalEntry,
  updateChartOfAccount,
  updateJournalEntry,
  getAccountingDashboard,
  getCashFlowReport,
  getFinanceAudit,
  getFinanceDashboard,
} from "@/features/accounting/api";

import {
  accountingQueryKeys,
} from "@/features/accounting/query-keys";

import type {
  ChartOfAccountListParameters,
  CreateChartOfAccountInput,
  CreateJournalEntryInput,
  GeneralLedgerParameters,
  JournalEntryListParameters,
  ReverseJournalEntryInput,
  TrialBalanceParameters,
  UpdateChartOfAccountInput,
  UpdateJournalEntryInput,
  AccountingDashboardParameters,
  CashFlowReportParameters,
} from "@/features/accounting/types";

export function useChartOfAccountList(
  parameters:
    ChartOfAccountListParameters,
) {
  return useQuery({
    queryKey:
      accountingQueryKeys
      .accountList(
        parameters,
      ),

    queryFn: () =>
      listChartOfAccounts(
        parameters,
      ),

    staleTime: 30_000,
  });
}

export function useChartOfAccount(
  accountId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      accountingQueryKeys
      .accountDetail(
        accountId,
      ),

    queryFn: () =>
      getChartOfAccount(
        accountId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        accountId,
      ),

    staleTime: 30_000,
  });
}

export function useCreateChartOfAccount() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input:
        CreateChartOfAccountInput,
    ) =>
      createChartOfAccount(
        input,
      ),

    onSuccess: async (
      account,
    ) => {
      queryClient.setQueryData(
        accountingQueryKeys
          .accountDetail(
            account.id,
          ),
        account,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            accountingQueryKeys
            .accountLists(),
        });
    },
  });
}

interface UpdateAccountVariables {
  accountId: string;
  input:
    UpdateChartOfAccountInput;
}

export function useUpdateChartOfAccount() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      accountId,
      input,
    }: UpdateAccountVariables) =>
      updateChartOfAccount(
        accountId,
        input,
      ),

    onSuccess: async (
      account,
    ) => {
      queryClient.setQueryData(
        accountingQueryKeys
          .accountDetail(
            account.id,
          ),
        account,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            accountingQueryKeys
            .accountLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            accountingQueryKeys
            .ledgers(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            accountingQueryKeys
            .trialBalances(),
        }),
      ]);
    },
  });
}

export function useDeactivateChartOfAccount() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      accountId: string,
    ) =>
      deactivateChartOfAccount(
        accountId,
      ),

    onSuccess: async (
      account,
    ) => {
      queryClient.setQueryData(
        accountingQueryKeys
          .accountDetail(
            account.id,
          ),
        account,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            accountingQueryKeys
            .accountLists(),
        });
    },
  });
}

export function useJournalEntryList(
  parameters:
    JournalEntryListParameters,
) {
  return useQuery({
    queryKey:
      accountingQueryKeys
      .journalList(
        parameters,
      ),

    queryFn: () =>
      listJournalEntries(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useJournalEntry(
  journalId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      accountingQueryKeys
      .journalDetail(
        journalId,
      ),

    queryFn: () =>
      getJournalEntry(
        journalId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        journalId,
      ),

    staleTime: 30_000,
  });
}

export function useCreateJournalEntry() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input:
        CreateJournalEntryInput,
    ) =>
      createJournalEntry(
        input,
      ),

    onSuccess: async (
      journal,
    ) => {
      queryClient.setQueryData(
        accountingQueryKeys
          .journalDetail(
            journal.id,
          ),
        journal,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            accountingQueryKeys
            .journalLists(),
        });
    },
  });
}

interface UpdateJournalVariables {
  journalId: string;
  input:
    UpdateJournalEntryInput;
}

export function useUpdateJournalEntry() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      journalId,
      input,
    }: UpdateJournalVariables) =>
      updateJournalEntry(
        journalId,
        input,
      ),

    onSuccess: async (
      journal,
    ) => {
      queryClient.setQueryData(
        accountingQueryKeys
          .journalDetail(
            journal.id,
          ),
        journal,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            accountingQueryKeys
            .journalLists(),
        });
    },
  });
}

export function usePostJournalEntry() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      journalId: string,
    ) =>
      postJournalEntry(
        journalId,
      ),

    onSuccess: async (
      journal,
    ) => {
      queryClient.setQueryData(
        accountingQueryKeys
          .journalDetail(
            journal.id,
          ),
        journal,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            accountingQueryKeys
            .journalLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            accountingQueryKeys
            .ledgers(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            accountingQueryKeys
            .trialBalances(),
        }),
      ]);
    },
  });
}

interface ReverseJournalVariables {
  journalId: string;
  input:
    ReverseJournalEntryInput;
}

export function useReverseJournalEntry() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      journalId,
      input,
    }: ReverseJournalVariables) =>
      reverseJournalEntry(
        journalId,
        input,
      ),

    onSuccess: async (
      result,
    ) => {
      queryClient.setQueryData(
        accountingQueryKeys
          .journalDetail(
            result.original.id,
          ),
        result.original,
      );

      queryClient.setQueryData(
        accountingQueryKeys
          .journalDetail(
            result.reversal.id,
          ),
        result.reversal,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            accountingQueryKeys
            .journalLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            accountingQueryKeys
            .ledgers(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            accountingQueryKeys
            .trialBalances(),
        }),
      ]);
    },
  });
}

export function useGeneralLedger(
  parameters:
    GeneralLedgerParameters,
  enabled = true,
) {
  return useQuery({
    queryKey:
      accountingQueryKeys
      .ledger(
        parameters,
      ),

    queryFn: () =>
      getGeneralLedger(
        parameters,
      ),

    enabled:
      enabled
      &&
      Boolean(
        parameters.account_id,
      ),

    staleTime: 30_000,
  });
}

export function useTrialBalance(
  parameters:
    TrialBalanceParameters,
  enabled = true,
) {
  return useQuery({
    queryKey:
      accountingQueryKeys
      .trialBalance(
        parameters,
      ),

    queryFn: () =>
      getTrialBalance(
        parameters,
      ),

    enabled,
    staleTime: 30_000,
  });
}
export function useFinanceDashboard(
  enabled = true,
) {
  return useQuery({
    queryKey:
      accountingQueryKeys
        .financeDashboard(),

    queryFn:
      getFinanceDashboard,

    enabled,
    staleTime: 30_000,
  });
}

export function useAccountingDashboard(
  parameters:
    AccountingDashboardParameters = {},
  enabled = true,
) {
  return useQuery({
    queryKey:
      accountingQueryKeys
        .accountingDashboard(
          parameters,
        ),

    queryFn: () =>
      getAccountingDashboard(
        parameters,
      ),

    enabled,
    staleTime: 30_000,
  });
}

export function useCashFlowReport(
  parameters:
    CashFlowReportParameters,
  enabled = true,
) {
  return useQuery({
    queryKey:
      accountingQueryKeys
        .cashFlow(
          parameters,
        ),

    queryFn: () =>
      getCashFlowReport(
        parameters,
      ),

    enabled:
      enabled
      &&
      Boolean(
        parameters.start_date
      )
      &&
      Boolean(
        parameters.end_date
      ),

    staleTime: 30_000,
  });
}

export function useFinanceAudit(
  enabled = true,
) {
  return useQuery({
    queryKey:
      accountingQueryKeys
        .financeAudit(),

    queryFn:
      getFinanceAudit,

    enabled,
    staleTime: 30_000,
  });
}
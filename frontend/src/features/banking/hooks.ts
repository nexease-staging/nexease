import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  autoMatchStatementLine,
  cancelBankStatement,
  cancelBankTransfer,
  confirmBankPaymentSuggestion,
  createBankAccount,
  createBankTransaction,
  createBankTransfer,
  deactivateBankAccount,
  executeBankPaymentSuggestion,
  generateBankPaymentSuggestion,
  getBankAccount,
  getBankPaymentSuggestion,
  getBankStatement,
  getBankTransaction,
  getBankTransfer,
  ignoreStatementLine,
  importBankStatement,
  listBankAccounts,
  listBankPaymentSuggestions,
  listBankStatements,
  listBankTransactions,
  listBankTransfers,
  matchStatementLine,
  postBankTransfer,
  reconcileBankTransaction,
  rejectBankPaymentSuggestion,
  updateBankAccount,
} from "@/features/banking/api";

import {
  bankingQueryKeys,
} from "@/features/banking/query-keys";

import type {
  AutoMatchStatementLineInput,
  BankAccountListParameters,
  BankPaymentSuggestionListParameters,
  BankStatementListParameters,
  BankTransactionListParameters,
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

export function useBankAccountList(
  parameters:
    BankAccountListParameters,
) {
  return useQuery({
    queryKey:
      bankingQueryKeys
      .accountList(
        parameters,
      ),

    queryFn: () =>
      listBankAccounts(
        parameters,
      ),

    staleTime: 30_000,
  });
}

export function useBankAccount(
  bankAccountId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      bankingQueryKeys
      .accountDetail(
        bankAccountId,
      ),

    queryFn: () =>
      getBankAccount(
        bankAccountId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        bankAccountId,
      ),

    staleTime: 30_000,
  });
}

export function useCreateBankAccount() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input:
        CreateBankAccountInput,
    ) =>
      createBankAccount(
        input,
      ),

    onSuccess: async (
      bankAccount,
    ) => {
      queryClient.setQueryData(
        bankingQueryKeys
          .accountDetail(
            bankAccount.id,
          ),
        bankAccount,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .accountLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .transactionLists(),
        }),
      ]);
    },
  });
}

interface UpdateBankAccountVariables {
  bankAccountId: string;
  input: UpdateBankAccountInput;
}

export function useUpdateBankAccount() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      bankAccountId,
      input,
    }: UpdateBankAccountVariables) =>
      updateBankAccount(
        bankAccountId,
        input,
      ),

    onSuccess: async (
      bankAccount,
    ) => {
      queryClient.setQueryData(
        bankingQueryKeys
          .accountDetail(
            bankAccount.id,
          ),
        bankAccount,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            bankingQueryKeys
            .accountLists(),
        });
    },
  });
}

export function useDeactivateBankAccount() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      bankAccountId: string,
    ) =>
      deactivateBankAccount(
        bankAccountId,
      ),

    onSuccess: async (
      bankAccount,
    ) => {
      queryClient.setQueryData(
        bankingQueryKeys
          .accountDetail(
            bankAccount.id,
          ),
        bankAccount,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .accountLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .transactionLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .transferLists(),
        }),
      ]);
    },
  });
}

export function useBankTransactionList(
  parameters:
    BankTransactionListParameters,
) {
  return useQuery({
    queryKey:
      bankingQueryKeys
      .transactionList(
        parameters,
      ),

    queryFn: () =>
      listBankTransactions(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useBankTransaction(
  transactionId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      bankingQueryKeys
      .transactionDetail(
        transactionId,
      ),

    queryFn: () =>
      getBankTransaction(
        transactionId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        transactionId,
      ),

    staleTime: 30_000,
  });
}

export function useCreateBankTransaction() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input:
        CreateBankTransactionInput,
    ) =>
      createBankTransaction(
        input,
      ),

    onSuccess: async (
      transaction,
    ) => {
      queryClient.setQueryData(
        bankingQueryKeys
          .transactionDetail(
            transaction.id,
          ),
        transaction,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .transactionLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .accounts(),
        }),
      ]);
    },
  });
}

export function useReconcileBankTransaction() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      transactionId: string,
    ) =>
      reconcileBankTransaction(
        transactionId,
      ),

    onSuccess: async (
      transaction,
    ) => {
      queryClient.setQueryData(
        bankingQueryKeys
          .transactionDetail(
            transaction.id,
          ),
        transaction,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            bankingQueryKeys
            .transactionLists(),
        });
    },
  });
}

export function useBankTransferList(
  parameters:
    BankTransferListParameters,
) {
  return useQuery({
    queryKey:
      bankingQueryKeys
      .transferList(
        parameters,
      ),

    queryFn: () =>
      listBankTransfers(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useBankTransfer(
  transferId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      bankingQueryKeys
      .transferDetail(
        transferId,
      ),

    queryFn: () =>
      getBankTransfer(
        transferId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        transferId,
      ),

    staleTime: 30_000,
  });
}

export function useCreateBankTransfer() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input:
        CreateBankTransferInput,
    ) =>
      createBankTransfer(
        input,
      ),

    onSuccess: async (
      transfer,
    ) => {
      queryClient.setQueryData(
        bankingQueryKeys
          .transferDetail(
            transfer.id,
          ),
        transfer,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            bankingQueryKeys
            .transferLists(),
        });
    },
  });
}

export function usePostBankTransfer() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      transferId: string,
    ) =>
      postBankTransfer(
        transferId,
      ),

    onSuccess: async (
      transfer,
    ) => {
      queryClient.setQueryData(
        bankingQueryKeys
          .transferDetail(
            transfer.id,
          ),
        transfer,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .transferLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .accounts(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .transactionLists(),
        }),
      ]);
    },
  });
}

export function useCancelBankTransfer() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      transferId: string,
    ) =>
      cancelBankTransfer(
        transferId,
      ),

    onSuccess: async (
      transfer,
    ) => {
      queryClient.setQueryData(
        bankingQueryKeys
          .transferDetail(
            transfer.id,
          ),
        transfer,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            bankingQueryKeys
            .transferLists(),
        });
    },
  });
}
export function useBankStatementList(
  parameters:
    BankStatementListParameters,
) {
  return useQuery({
    queryKey:
      bankingQueryKeys
      .statementList(
        parameters,
      ),

    queryFn: () =>
      listBankStatements(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useBankStatement(
  statementId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      bankingQueryKeys
      .statementDetail(
        statementId,
      ),

    queryFn: () =>
      getBankStatement(
        statementId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        statementId,
      ),

    staleTime: 15_000,
  });
}

export function useImportBankStatement() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input:
        ImportBankStatementInput,
    ) =>
      importBankStatement(
        input,
      ),

    onSuccess: async (
      statement,
    ) => {
      queryClient.setQueryData(
        bankingQueryKeys
          .statementDetail(
            statement.id,
          ),
        statement,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            bankingQueryKeys
            .statementLists(),
        });
    },
  });
}

export function useCancelBankStatement() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      statementId: string,
    ) =>
      cancelBankStatement(
        statementId,
      ),

    onSuccess: async (
      statement,
    ) => {
      queryClient.setQueryData(
        bankingQueryKeys
          .statementDetail(
            statement.id,
          ),
        statement,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            bankingQueryKeys
            .statementLists(),
        });
    },
  });
}

export function useAutoMatchStatementLine() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input:
        AutoMatchStatementLineInput,
    ) =>
      autoMatchStatementLine(
        input,
      ),

    onSuccess: async (
      result,
    ) => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .statementDetail(
              result.statement.id,
            ),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .statementLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .transactionLists(),
        }),
      ]);
    },
  });
}

export function useMatchStatementLine() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input:
        MatchStatementLineInput,
    ) =>
      matchStatementLine(
        input,
      ),

    onSuccess: async (
      result,
    ) => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .statementDetail(
              result.statement.id,
            ),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .statementLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .transactionLists(),
        }),
      ]);
    },
  });
}

export function useIgnoreStatementLine() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input:
        IgnoreStatementLineInput,
    ) =>
      ignoreStatementLine(
        input,
      ),

    onSuccess: async (
      result,
    ) => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .statementDetail(
              result.statement.id,
            ),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .statementLists(),
        }),
      ]);
    },
  });
}

export function useBankPaymentSuggestionList(
  parameters:
    BankPaymentSuggestionListParameters,
) {
  return useQuery({
    queryKey:
      bankingQueryKeys
      .paymentSuggestionList(
        parameters,
      ),

    queryFn: () =>
      listBankPaymentSuggestions(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useBankPaymentSuggestion(
  suggestionId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      bankingQueryKeys
      .paymentSuggestionDetail(
        suggestionId,
      ),

    queryFn: () =>
      getBankPaymentSuggestion(
        suggestionId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        suggestionId,
      ),

    staleTime: 15_000,
  });
}

export function useGenerateBankPaymentSuggestion() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input:
        GeneratePaymentSuggestionInput,
    ) =>
      generateBankPaymentSuggestion(
        input,
      ),

    onSuccess: async (
      suggestion,
    ) => {
      queryClient.setQueryData(
        bankingQueryKeys
          .paymentSuggestionDetail(
            suggestion.id,
          ),
        suggestion,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .paymentSuggestionLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .statementDetail(
              suggestion.statement.id,
            ),
        }),
      ]);
    },
  });
}

export function useConfirmBankPaymentSuggestion() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      suggestionId: string,
    ) =>
      confirmBankPaymentSuggestion(
        suggestionId,
      ),

    onSuccess: async (
      suggestion,
    ) => {
      queryClient.setQueryData(
        bankingQueryKeys
          .paymentSuggestionDetail(
            suggestion.id,
          ),
        suggestion,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            bankingQueryKeys
            .paymentSuggestionLists(),
        });
    },
  });
}

export function useRejectBankPaymentSuggestion() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      suggestionId: string,
    ) =>
      rejectBankPaymentSuggestion(
        suggestionId,
      ),

    onSuccess: async (
      suggestion,
    ) => {
      queryClient.setQueryData(
        bankingQueryKeys
          .paymentSuggestionDetail(
            suggestion.id,
          ),
        suggestion,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            bankingQueryKeys
            .paymentSuggestionLists(),
        });
    },
  });
}

export function useExecuteBankPaymentSuggestion() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      suggestionId: string,
    ) =>
      executeBankPaymentSuggestion(
        suggestionId,
      ),

    onSuccess: async (
      execution,
    ) => {
      const suggestion =
        execution.suggestion;

      queryClient.setQueryData(
        bankingQueryKeys
          .paymentSuggestionDetail(
            suggestion.id,
          ),
        suggestion,
      );

      queryClient.setQueryData(
        bankingQueryKeys
          .transactionDetail(
            execution
              .bank_transaction
              .id,
          ),
        execution.bank_transaction,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .paymentSuggestionLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .statementDetail(
              suggestion.statement.id,
            ),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .statementLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .transactionLists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            bankingQueryKeys
            .accountLists(),
        }),
      ]);
    },
  });
}
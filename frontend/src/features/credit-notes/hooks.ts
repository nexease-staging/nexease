import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  cancelCreditNote,
  createCreditNote,
  getCreditNote,
  issueCreditNote,
  listCreditNotes,
} from "@/features/credit-notes/api";

import {
  creditNoteQueryKeys,
} from "@/features/credit-notes/query-keys";

import type {
  CreateCreditNoteInput,
  CreditNoteListParameters,
} from "@/features/credit-notes/types";

export function useCreditNoteList(
  parameters:
    CreditNoteListParameters,
) {
  return useQuery({
    queryKey:
      creditNoteQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listCreditNotes(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useCreditNote(
  creditNoteId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      creditNoteQueryKeys.detail(
        creditNoteId,
      ),

    queryFn: () =>
      getCreditNote(
        creditNoteId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        creditNoteId,
      ),

    staleTime: 30_000,
  });
}

export function useCreateCreditNote() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateCreditNoteInput,
    ) =>
      createCreditNote(
        input,
      ),

    onSuccess: async (
      creditNote,
    ) => {
      queryClient.setQueryData(
        creditNoteQueryKeys.detail(
          creditNote.id,
        ),
        creditNote,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            creditNoteQueryKeys
            .lists(),
        });
    },
  });
}

export function useIssueCreditNote() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      creditNoteId: string,
    ) =>
      issueCreditNote(
        creditNoteId,
      ),

    onSuccess: async (
      creditNote,
    ) => {
      queryClient.setQueryData(
        creditNoteQueryKeys.detail(
          creditNote.id,
        ),
        creditNote,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            creditNoteQueryKeys
            .lists(),
        });
    },
  });
}

export function useCancelCreditNote() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      creditNoteId: string,
    ) =>
      cancelCreditNote(
        creditNoteId,
      ),

    onSuccess: async (
      creditNote,
    ) => {
      queryClient.setQueryData(
        creditNoteQueryKeys.detail(
          creditNote.id,
        ),
        creditNote,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            creditNoteQueryKeys
            .lists(),
        });
    },
  });
}
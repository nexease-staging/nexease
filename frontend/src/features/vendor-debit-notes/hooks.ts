import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  cancelVendorDebitNote,
  createVendorDebitNote,
  getVendorDebitNote,
  issueVendorDebitNote,
  listVendorDebitNotes,
} from "@/features/vendor-debit-notes/api";

import {
  vendorDebitNoteQueryKeys,
} from "@/features/vendor-debit-notes/query-keys";

import type {
  CreateVendorDebitNoteInput,
  VendorDebitNoteListParameters,
} from "@/features/vendor-debit-notes/types";

export function useVendorDebitNoteList(
  parameters:
    VendorDebitNoteListParameters,
) {
  return useQuery({
    queryKey:
      vendorDebitNoteQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listVendorDebitNotes(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useVendorDebitNote(
  debitNoteId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      vendorDebitNoteQueryKeys.detail(
        debitNoteId,
      ),

    queryFn: () =>
      getVendorDebitNote(
        debitNoteId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        debitNoteId,
      ),

    staleTime: 30_000,
  });
}

export function useCreateVendorDebitNote() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateVendorDebitNoteInput,
    ) =>
      createVendorDebitNote(
        input,
      ),

    onSuccess: async (
      debitNote,
    ) => {
      queryClient.setQueryData(
        vendorDebitNoteQueryKeys.detail(
          debitNote.id,
        ),
        debitNote,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            vendorDebitNoteQueryKeys
            .lists(),
        }),

        queryClient.invalidateQueries({
          queryKey: [
            "purchase-returns",
          ],
        }),

        queryClient.invalidateQueries({
          queryKey: [
            "vendor-bills",
          ],
        }),
      ]);
    },
  });
}

export function useIssueVendorDebitNote() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      debitNoteId: string,
    ) =>
      issueVendorDebitNote(
        debitNoteId,
      ),

    onSuccess: async (
      debitNote,
    ) => {
      queryClient.setQueryData(
        vendorDebitNoteQueryKeys.detail(
          debitNote.id,
        ),
        debitNote,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            vendorDebitNoteQueryKeys
            .lists(),
        }),

        queryClient.invalidateQueries({
          queryKey: [
            "vendor-bills",
          ],
        }),

        queryClient.invalidateQueries({
          queryKey: [
            "accounts-payable",
          ],
        }),
      ]);
    },
  });
}

export function useCancelVendorDebitNote() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      debitNoteId: string,
    ) =>
      cancelVendorDebitNote(
        debitNoteId,
      ),

    onSuccess: async (
      debitNote,
    ) => {
      queryClient.setQueryData(
        vendorDebitNoteQueryKeys.detail(
          debitNote.id,
        ),
        debitNote,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            vendorDebitNoteQueryKeys
            .lists(),
        });
    },
  });
}
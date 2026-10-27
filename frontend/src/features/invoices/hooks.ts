import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  cancelInvoice,
  createInvoice,
  getInvoice,
  issueInvoice,
  listInvoiceBankAccounts,
  listInvoices,
  recordInvoicePayment,
} from "@/features/invoices/api";

import {
  invoiceQueryKeys,
} from "@/features/invoices/query-keys";

import type {
  CreateInvoiceInput,
  InvoiceListParameters,
  RecordInvoicePaymentInput,
} from "@/features/invoices/types";

export function useInvoiceList(
  parameters:
    InvoiceListParameters,
) {
  return useQuery({
    queryKey:
      invoiceQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listInvoices(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useInvoice(
  invoiceId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      invoiceQueryKeys.detail(
        invoiceId,
      ),

    queryFn: () =>
      getInvoice(
        invoiceId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        invoiceId,
      ),

    staleTime: 30_000,
  });
}

export function useInvoiceBankAccounts(
  enabled = true,
) {
  return useQuery({
    queryKey:
      invoiceQueryKeys
      .bankAccounts(),

    queryFn:
      listInvoiceBankAccounts,

    enabled,

    staleTime: 60_000,
  });
}

export function useCreateInvoice() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateInvoiceInput,
    ) =>
      createInvoice(
        input,
      ),

    onSuccess: async (
      invoice,
    ) => {
      queryClient.setQueryData(
        invoiceQueryKeys.detail(
          invoice.id,
        ),
        invoice,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            invoiceQueryKeys.lists(),
        });
    },
  });
}

export function useIssueInvoice() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      invoiceId: string,
    ) =>
      issueInvoice(
        invoiceId,
      ),

    onSuccess: async (
      invoice,
    ) => {
      queryClient.setQueryData(
        invoiceQueryKeys.detail(
          invoice.id,
        ),
        invoice,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            invoiceQueryKeys.lists(),
        });
    },
  });
}

export function useCancelInvoice() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      invoiceId: string,
    ) =>
      cancelInvoice(
        invoiceId,
      ),

    onSuccess: async (
      invoice,
    ) => {
      queryClient.setQueryData(
        invoiceQueryKeys.detail(
          invoice.id,
        ),
        invoice,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            invoiceQueryKeys.lists(),
        });
    },
  });
}

interface RecordPaymentVariables {
  invoiceId: string;

  input:
    RecordInvoicePaymentInput;
}

export function useRecordInvoicePayment() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      invoiceId,
      input,
    }: RecordPaymentVariables) =>
      recordInvoicePayment(
        invoiceId,
        input,
      ),

    onSuccess: async (
      result,
    ) => {
      queryClient.setQueryData(
        invoiceQueryKeys.detail(
          result.invoice.id,
        ),
        result.invoice,
      );

      await queryClient
        .invalidateQueries({
          queryKey:
            invoiceQueryKeys.lists(),
        });
    },
  });
}
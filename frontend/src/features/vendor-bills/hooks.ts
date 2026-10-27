import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  cancelVendorBill,
  createVendorBill,
  getAccountsPayable,
  getVendorBill,
  listVendorBillBankAccounts,
  listVendorBills,
  postVendorBill,
  recordVendorBillPayment,
} from "@/features/vendor-bills/api";

import {
  vendorBillQueryKeys,
} from "@/features/vendor-bills/query-keys";

import type {
  CreateVendorBillInput,
  RecordVendorBillPaymentInput,
  VendorBillListParameters,
} from "@/features/vendor-bills/types";

export function useVendorBillList(
  parameters:
    VendorBillListParameters,
) {
  return useQuery({
    queryKey:
      vendorBillQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listVendorBills(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useVendorBill(
  billId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      vendorBillQueryKeys.detail(
        billId,
      ),

    queryFn: () =>
      getVendorBill(
        billId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        billId,
      ),

    staleTime: 30_000,
  });
}

export function useCreateVendorBill() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateVendorBillInput,
    ) =>
      createVendorBill(
        input,
      ),

    onSuccess: async (
      vendorBill,
    ) => {
      queryClient.setQueryData(
        vendorBillQueryKeys.detail(
          vendorBill.id,
        ),
        vendorBill,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            vendorBillQueryKeys
            .lists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            vendorBillQueryKeys
            .accountsPayable(),
        }),
      ]);
    },
  });
}

export function usePostVendorBill() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      billId: string,
    ) =>
      postVendorBill(
        billId,
      ),

    onSuccess: async (
      vendorBill,
    ) => {
      queryClient.setQueryData(
        vendorBillQueryKeys.detail(
          vendorBill.id,
        ),
        vendorBill,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            vendorBillQueryKeys
            .lists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            vendorBillQueryKeys
            .accountsPayable(),
        }),
      ]);
    },
  });
}

export function useCancelVendorBill() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      billId: string,
    ) =>
      cancelVendorBill(
        billId,
      ),

    onSuccess: async (
      vendorBill,
    ) => {
      queryClient.setQueryData(
        vendorBillQueryKeys.detail(
          vendorBill.id,
        ),
        vendorBill,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            vendorBillQueryKeys
            .lists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            vendorBillQueryKeys
            .accountsPayable(),
        }),
      ]);
    },
  });
}

interface RecordPaymentVariables {
  billId: string;
  input:
    RecordVendorBillPaymentInput;
}

export function useRecordVendorBillPayment() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      billId,
      input,
    }: RecordPaymentVariables) =>
      recordVendorBillPayment(
        billId,
        input,
      ),

    onSuccess: async (
      result,
    ) => {
      queryClient.setQueryData(
        vendorBillQueryKeys.detail(
          result.vendor_bill.id,
        ),
        result.vendor_bill,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            vendorBillQueryKeys
            .lists(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            vendorBillQueryKeys
            .accountsPayable(),
        }),
      ]);
    },
  });
}

export function useVendorBillBankAccounts(
  enabled = true,
) {
  return useQuery({
    queryKey:
      vendorBillQueryKeys
      .bankAccounts(),

    queryFn:
      listVendorBillBankAccounts,

    enabled,
    staleTime: 60_000,
  });
}

export function useAccountsPayable() {
  return useQuery({
    queryKey:
      vendorBillQueryKeys
      .accountsPayable(),

    queryFn:
      getAccountsPayable,

    staleTime: 30_000,
  });
}
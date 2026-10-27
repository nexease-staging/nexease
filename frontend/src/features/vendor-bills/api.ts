import {
  apiRequest,
} from "@/lib/api/client";

import type {
  AccountsPayableData,
  AccountsPayableSummary,
  CreateVendorBillInput,
  RecordVendorBillPaymentInput,
  VendorBillBankAccount,
  VendorBillBankAccountListData,
  VendorBillData,
  VendorBillDetail,
  VendorBillListData,
  VendorBillListParameters,
  VendorBillPaymentData,
} from "@/features/vendor-bills/types";

type QueryValue =
  | string
  | number
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
      String(value),
    );
  }

  const query =
    searchParameters.toString();

  return query
    ? `?${query}`
    : "";
}

export async function listVendorBills(
  parameters:
    VendorBillListParameters = {},
): Promise<VendorBillListData> {
  const response =
    await apiRequest<VendorBillListData>(
      (
        "/vendor-bills/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          supplier_id:
            parameters.supplier_id,
          purchase_order_id:
            parameters
              .purchase_order_id,
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

export async function getVendorBill(
  billId: string,
): Promise<VendorBillDetail> {
  const response =
    await apiRequest<VendorBillData>(
      `/vendor-bills/${billId}/`,
    );

  return response.data.vendor_bill;
}

export async function createVendorBill(
  input: CreateVendorBillInput,
): Promise<VendorBillDetail> {
  const response =
    await apiRequest<VendorBillData>(
      "/vendor-bills/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.vendor_bill;
}

export async function postVendorBill(
  billId: string,
): Promise<VendorBillDetail> {
  const response =
    await apiRequest<VendorBillData>(
      `/vendor-bills/${billId}/post/`,
      {
        method: "POST",
      },
    );

  return response.data.vendor_bill;
}

export async function cancelVendorBill(
  billId: string,
): Promise<VendorBillDetail> {
  const response =
    await apiRequest<VendorBillData>(
      `/vendor-bills/${billId}/cancel/`,
      {
        method: "POST",
      },
    );

  return response.data.vendor_bill;
}

export async function recordVendorBillPayment(
  billId: string,
  input: RecordVendorBillPaymentInput,
): Promise<VendorBillPaymentData> {
  const response =
    await apiRequest<VendorBillPaymentData>(
      `/vendor-bills/${billId}/payments/`,
      {
        method: "POST",
        body: input,
      },
    );

  return response.data;
}

export async function listVendorBillBankAccounts():
  Promise<VendorBillBankAccount[]> {
  const response =
    await apiRequest<
      VendorBillBankAccountListData
    >(
      "/vendor-bills/bank-accounts/",
    );

  return response.data.bank_accounts;
}

export async function getAccountsPayable():
  Promise<AccountsPayableSummary> {
  const response =
    await apiRequest<AccountsPayableData>(
      "/accounts-payable/",
    );

  return response
    .data
    .accounts_payable;
}
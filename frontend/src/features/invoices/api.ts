import {
  apiRequest,
} from "@/lib/api/client";

import type {
  BankAccountLookupListData,
  CreateInvoiceInput,
  InvoiceData,
  InvoiceDetail,
  InvoiceListData,
  InvoiceListParameters,
  InvoicePaymentData,
  RecordInvoicePaymentInput,
} from "@/features/invoices/types";

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

export async function listInvoices(
  parameters:
    InvoiceListParameters = {},
): Promise<InvoiceListData> {
  const response =
    await apiRequest<InvoiceListData>(
      (
        "/invoices/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          customer_id:
            parameters.customer_id,
          sales_order_id:
            parameters.sales_order_id,
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

export async function getInvoice(
  invoiceId: string,
): Promise<InvoiceDetail> {
  const response =
    await apiRequest<InvoiceData>(
      `/invoices/${invoiceId}/`,
    );

  return response.data.invoice;
}

export async function createInvoice(
  input: CreateInvoiceInput,
): Promise<InvoiceDetail> {
  const response =
    await apiRequest<InvoiceData>(
      "/invoices/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.invoice;
}

export async function issueInvoice(
  invoiceId: string,
): Promise<InvoiceDetail> {
  const response =
    await apiRequest<InvoiceData>(
      `/invoices/${invoiceId}/issue/`,
      {
        method: "POST",
        body: {},
      },
    );

  return response.data.invoice;
}

export async function cancelInvoice(
  invoiceId: string,
): Promise<InvoiceDetail> {
  const response =
    await apiRequest<InvoiceData>(
      `/invoices/${invoiceId}/cancel/`,
      {
        method: "POST",
        body: {},
      },
    );

  return response.data.invoice;
}

export async function listInvoiceBankAccounts():
  Promise<BankAccountLookupListData> {
  const response =
    await apiRequest<
      BankAccountLookupListData
    >(
      "/invoice-bank-accounts/",
    );

  return response.data;
}

export async function recordInvoicePayment(
  invoiceId: string,
  input: RecordInvoicePaymentInput,
): Promise<InvoicePaymentData> {
  const response =
    await apiRequest<InvoicePaymentData>(
      (
        `/invoices/${invoiceId}`
        +
        "/record-payment/"
      ),
      {
        method: "POST",
        body: input,
      },
    );

  return response.data;
}
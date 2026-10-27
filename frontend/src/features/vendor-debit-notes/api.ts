import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CreateVendorDebitNoteInput,
  VendorDebitNoteData,
  VendorDebitNoteDetail,
  VendorDebitNoteListData,
  VendorDebitNoteListParameters,
} from "@/features/vendor-debit-notes/types";

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

export async function listVendorDebitNotes(
  parameters:
    VendorDebitNoteListParameters = {},
): Promise<VendorDebitNoteListData> {
  const response =
    await apiRequest<VendorDebitNoteListData>(
      (
        "/vendor-debit-notes/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          supplier_id:
            parameters.supplier_id,
          purchase_order_id:
            parameters.purchase_order_id,
          purchase_return_id:
            parameters.purchase_return_id,
          vendor_bill_id:
            parameters.vendor_bill_id,
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

export async function getVendorDebitNote(
  debitNoteId: string,
): Promise<VendorDebitNoteDetail> {
  const response =
    await apiRequest<VendorDebitNoteData>(
      (
        "/vendor-debit-notes/"
        +
        `${debitNoteId}/`
      ),
    );

  return response.data.vendor_debit_note;
}

export async function createVendorDebitNote(
  input: CreateVendorDebitNoteInput,
): Promise<VendorDebitNoteDetail> {
  const response =
    await apiRequest<VendorDebitNoteData>(
      "/vendor-debit-notes/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.vendor_debit_note;
}

export async function issueVendorDebitNote(
  debitNoteId: string,
): Promise<VendorDebitNoteDetail> {
  const response =
    await apiRequest<VendorDebitNoteData>(
      (
        "/vendor-debit-notes/"
        +
        `${debitNoteId}/issue/`
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response.data.vendor_debit_note;
}

export async function cancelVendorDebitNote(
  debitNoteId: string,
): Promise<VendorDebitNoteDetail> {
  const response =
    await apiRequest<VendorDebitNoteData>(
      (
        "/vendor-debit-notes/"
        +
        `${debitNoteId}/cancel/`
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response.data.vendor_debit_note;
}
import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CreateCreditNoteInput,
  CreditNoteData,
  CreditNoteDetail,
  CreditNoteListData,
  CreditNoteListParameters,
} from "@/features/credit-notes/types";

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

export async function listCreditNotes(
  parameters:
    CreditNoteListParameters = {},
): Promise<CreditNoteListData> {
  const response =
    await apiRequest<CreditNoteListData>(
      (
        "/credit-notes/"
        +
        buildQuery({
          page:
            parameters.page,
          page_size:
            parameters.page_size,
          customer_id:
            parameters.customer_id,
          invoice_id:
            parameters.invoice_id,
          sales_return_id:
            parameters.sales_return_id,
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

export async function getCreditNote(
  creditNoteId: string,
): Promise<CreditNoteDetail> {
  const response =
    await apiRequest<CreditNoteData>(
      (
        "/credit-notes/"
        +
        `${creditNoteId}/`
      ),
    );

  return response.data.credit_note;
}

export async function createCreditNote(
  input: CreateCreditNoteInput,
): Promise<CreditNoteDetail> {
  const response =
    await apiRequest<CreditNoteData>(
      "/credit-notes/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.credit_note;
}

export async function issueCreditNote(
  creditNoteId: string,
): Promise<CreditNoteDetail> {
  const response =
    await apiRequest<CreditNoteData>(
      (
        "/credit-notes/"
        +
        `${creditNoteId}/issue/`
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response.data.credit_note;
}

export async function cancelCreditNote(
  creditNoteId: string,
): Promise<CreditNoteDetail> {
  const response =
    await apiRequest<CreditNoteData>(
      (
        "/credit-notes/"
        +
        `${creditNoteId}/cancel/`
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response.data.credit_note;
}
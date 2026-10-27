import {
  apiBinaryRequest,
  apiRequest,
} from "@/lib/api/client";

import type {
  APIBinaryResponse,
} from "@/lib/api/client";

import type {
  DocumentAccessLogData,
  DocumentAccessLogParameters,
  DocumentDeliveryLogData,
  DocumentDeliveryLogParameters,
  DocumentEmailData,
  DocumentEmailInput,
  DocumentEmailResult,
  DocumentLogSummary,
  DocumentLogSummaryData,
  DocumentType,
  ExportFormat,
  ExportParameters,
  ExportResourceType,
} from "@/features/documents/types";

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
      String(value),
    );
  }

  const query =
    searchParameters.toString();

  return query
    ? `?${query}`
    : "";
}

function documentPath(
  documentType: DocumentType,
  documentId: string,
): string {
  return (
    "/documents/"
    +
    `${documentType}/`
    +
    `${documentId}/`
  );
}

export async function getDocumentPDF(
  documentType: DocumentType,
  documentId: string,
): Promise<APIBinaryResponse> {
  return apiBinaryRequest(
    (
      documentPath(
        documentType,
        documentId,
      )
      +
      "pdf/"
    ),
  );
}

export async function sendDocumentEmail(
  documentType: DocumentType,
  documentId: string,
  input: DocumentEmailInput = {},
): Promise<DocumentEmailResult> {
  const response =
    await apiRequest<
      DocumentEmailData
    >(
      (
        documentPath(
          documentType,
          documentId,
        )
        +
        "email/"
      ),
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.document;
}

export async function listDocumentAccessLogs(
  parameters:
    DocumentAccessLogParameters = {},
): Promise<DocumentAccessLogData> {
  const response =
    await apiRequest<
      DocumentAccessLogData
    >(
      (
        "/document-access-logs/"
        +
        buildQuery({
          document_type:
            parameters.document_type,

          action:
            parameters.action,

          document_number:
            parameters.document_number,

          user_id:
            parameters.user_id,

          limit:
            parameters.limit,
        })
      ),
    );

  return response.data;
}

export async function getDocumentAccessLogSummary():
  Promise<DocumentLogSummary> {
  const response =
    await apiRequest<
      DocumentLogSummaryData
    >(
      "/document-access-logs/summary/",
    );

  return response.data.summary;
}

export async function listDocumentDeliveryLogs(
  parameters:
    DocumentDeliveryLogParameters = {},
): Promise<DocumentDeliveryLogData> {
  const response =
    await apiRequest<
      DocumentDeliveryLogData
    >(
      (
        "/document-delivery-logs/"
        +
        buildQuery({
          document_type:
            parameters.document_type,

          channel:
            parameters.channel,

          status:
            parameters.status,

          recipient:
            parameters.recipient,

          document_number:
            parameters.document_number,

          subject:
            parameters.subject,

          recipient_overridden:
            parameters
              .recipient_overridden,

          custom_subject:
            parameters.custom_subject,

          custom_message:
            parameters.custom_message,

          limit:
            parameters.limit,
        })
      ),
    );

  return response.data;
}

export async function getDocumentDeliveryLogSummary():
  Promise<DocumentLogSummary> {
  const response =
    await apiRequest<
      DocumentLogSummaryData
    >(
      "/document-delivery-logs/summary/",
    );

  return response.data.summary;
}

export async function exportResource(
  resourceType: ExportResourceType,
  format: ExportFormat,
  parameters: ExportParameters = {},
): Promise<APIBinaryResponse> {
  return apiBinaryRequest(
    (
      "/exports/"
      +
      `${resourceType}/`
      +
      buildQuery({
        format,
        ...parameters,
      })
    ),
  );
}
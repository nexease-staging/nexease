import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  exportResource,
  getDocumentAccessLogSummary,
  getDocumentDeliveryLogSummary,
  getDocumentPDF,
  listDocumentAccessLogs,
  listDocumentDeliveryLogs,
  sendDocumentEmail,
} from "@/features/documents/api";

import {
  documentQueryKeys,
} from "@/features/documents/query-keys";

import {
  downloadBlob,
} from "@/lib/browser/download";

import type {
  DocumentAccessLogParameters,
  DocumentDeliveryLogParameters,
  DocumentEmailInput,
  DocumentType,
  ExportFormat,
  ExportParameters,
  ExportResourceType,
} from "@/features/documents/types";

interface DownloadDocumentVariables {
  documentType: DocumentType;
  documentId: string;
  fallbackFilename?: string;
}

export function useDownloadDocumentPDF() {
  return useMutation({
    mutationFn: async ({
      documentType,
      documentId,
      fallbackFilename,
    }: DownloadDocumentVariables) => {
      const response =
        await getDocumentPDF(
          documentType,
          documentId,
        );

      const filename =
        response.filename
        ??
        fallbackFilename
        ??
        `${documentType.toLowerCase()}-${documentId}.pdf`;

      downloadBlob(
        response.blob,
        filename,
      );

      return {
        filename,
        contentType:
          response.contentType,
      };
    },
  });
}

interface SendDocumentEmailVariables {
  documentType: DocumentType;
  documentId: string;
  input?: DocumentEmailInput;
}

export function useSendDocumentEmail() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      documentType,
      documentId,
      input = {},
    }: SendDocumentEmailVariables) =>
      sendDocumentEmail(
        documentType,
        documentId,
        input,
      ),

    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            documentQueryKeys
              .deliveryLogs(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            documentQueryKeys
              .accessLogs(),
        }),
      ]);
    },
  });
}

interface ExportResourceVariables {
  resourceType:
    ExportResourceType;

  format:
    ExportFormat;

  parameters?:
    ExportParameters;

  fallbackFilename?:
    string;
}

export function useExportResource() {
  return useMutation({
    mutationFn: async ({
      resourceType,
      format,
      parameters = {},
      fallbackFilename,
    }: ExportResourceVariables) => {
      const response =
        await exportResource(
          resourceType,
          format,
          parameters,
        );

      const extension =
        format === "xlsx"
          ? "xlsx"
          : "csv";

      const filename =
        response.filename
        ??
        fallbackFilename
        ??
        `${resourceType.toLowerCase()}.${extension}`;

      downloadBlob(
        response.blob,
        filename,
      );

      return {
        filename,
        contentType:
          response.contentType,
      };
    },
  });
}

export function useDocumentAccessLogs(
  parameters:
    DocumentAccessLogParameters = {},
  enabled = true,
) {
  return useQuery({
    queryKey:
      documentQueryKeys
        .accessLogList(
          parameters,
        ),

    queryFn: () =>
      listDocumentAccessLogs(
        parameters,
      ),

    enabled,

    staleTime: 30_000,
  });
}

export function useDocumentAccessLogSummary(
  enabled = true,
) {
  return useQuery({
    queryKey:
      documentQueryKeys
        .accessLogSummary(),

    queryFn:
      getDocumentAccessLogSummary,

    enabled,

    staleTime: 30_000,
  });
}

export function useDocumentDeliveryLogs(
  parameters:
    DocumentDeliveryLogParameters = {},
  enabled = true,
) {
  return useQuery({
    queryKey:
      documentQueryKeys
        .deliveryLogList(
          parameters,
        ),

    queryFn: () =>
      listDocumentDeliveryLogs(
        parameters,
      ),

    enabled,

    staleTime: 30_000,
  });
}

export function useDocumentDeliveryLogSummary(
  enabled = true,
) {
  return useQuery({
    queryKey:
      documentQueryKeys
        .deliveryLogSummary(),

    queryFn:
      getDocumentDeliveryLogSummary,

    enabled,

    staleTime: 30_000,
  });
}
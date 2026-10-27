"use client";

import {
  useState,
} from "react";

import {
  Download,
  Mail,
} from "lucide-react";

import DocumentEmailDialog from "@/features/documents/components/document-email-dialog";

import {
  useDownloadDocumentPDF,
} from "@/features/documents/hooks";

import type {
  DocumentType,
} from "@/features/documents/types";

import {
  APIRequestError,
} from "@/lib/api/client";

interface DocumentActionsProps {
  documentType: DocumentType;
  documentId: string;
  documentNumber: string;
  defaultRecipient?: string | null;
  disabled?: boolean;
}

function getErrorMessage(
  error: unknown,
): string {
  if (
    error
    instanceof
    APIRequestError
  ) {
    return error.message;
  }

  if (
    error
    instanceof
    Error
  ) {
    return error.message;
  }

  return "Unable to download the document.";
}

export default function DocumentActions({
  documentType,
  documentId,
  documentNumber,
  defaultRecipient = null,
  disabled = false,
}: DocumentActionsProps) {
  const [
    emailOpen,
    setEmailOpen,
  ] = useState(false);

  const [
    downloadError,
    setDownloadError,
  ] = useState<string | null>(
    null,
  );

  const downloadMutation =
    useDownloadDocumentPDF();

  const actionDisabled =
    disabled
    ||
    downloadMutation.isPending;

  async function handleDownload():
    Promise<void> {
    setDownloadError(null);

    try {
      await downloadMutation.mutateAsync({
        documentType,
        documentId,
        fallbackFilename:
          `${documentNumber}.pdf`,
      });
    } catch (error) {
      setDownloadError(
        getErrorMessage(error),
      );
    }
  }

  function handleOpenEmail(): void {
    setDownloadError(null);
    setEmailOpen(true);
  }

  function handleCloseEmail(): void {
    setEmailOpen(false);
  }

  return (
    <>
      <div>
        <div
          className="
            flex flex-wrap gap-2
          "
        >
          <button
            type="button"
            disabled={actionDisabled}
            onClick={() => {
              void handleDownload();
            }}
            className="
              inline-flex items-center
              gap-2 rounded-lg
              border border-slate-300
              bg-white px-3 py-2
              text-sm font-semibold
              text-slate-700
              hover:bg-slate-50
              hover:text-slate-950
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >
            <Download size={16} />

            {downloadMutation.isPending
              ? "Downloading..."
              : "PDF"}
          </button>

          <button
            type="button"
            disabled={disabled}
            onClick={
              handleOpenEmail
            }
            className="
              inline-flex items-center
              gap-2 rounded-lg
              border border-blue-200
              bg-white px-3 py-2
              text-sm font-semibold
              text-blue-700
              hover:bg-blue-50
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >
            <Mail size={16} />
            Email
          </button>
        </div>

        {downloadError ? (
          <p
            role="alert"
            className="
              mt-2 text-xs
              text-red-700
            "
          >
            {downloadError}
          </p>
        ) : null}
      </div>

      <DocumentEmailDialog
        open={emailOpen}
        documentType={documentType}
        documentId={documentId}
        documentNumber={
          documentNumber
        }
        defaultRecipient={
          defaultRecipient
        }
        onClose={
          handleCloseEmail
        }
      />
    </>
  );
}
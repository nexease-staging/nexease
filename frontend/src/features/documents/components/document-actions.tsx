"use client";

import {
  useState,
} from "react";

import {
  Download,
  Mail,
  MessageCircle,
  Share2, Send } from "lucide-react";

import { Capacitor } from "@capacitor/core";

import DocumentPDFPreview from "./document-pdf-preview";
import { DOC_KIND, openShare } from "@/features/share/api";

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
  whatsappMessage?: string;
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
  whatsappMessage,
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

  const native = Capacitor.isNativePlatform();
  const pdfLabel = native ? "Share PDF" : "Download PDF";

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
        <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label={`${documentNumber} actions`}>
          <button type="button" className="nx-button nx-secondary nxsh-trigger" disabled={disabled} onClick={() => openShare({ kind: DOC_KIND[documentType], id: documentId, title: documentNumber })}>
            <Send size={16} aria-hidden="true" />Share
          </button>
          <DocumentPDFPreview documentType={documentType} documentId={documentId} documentNumber={documentNumber} disabled={disabled}/>
          <button type="button" className="nxl-icon" aria-label={pdfLabel} title={pdfLabel} disabled={actionDisabled} aria-busy={downloadMutation.isPending || undefined} onClick={() => { void handleDownload(); }}>
            {native ? <Share2 size={18} strokeWidth={1.8} aria-hidden="true" /> : <Download size={18} strokeWidth={1.8} aria-hidden="true" className={downloadMutation.isPending ? "animate-pulse" : undefined} />}
          </button>
          <button type="button" className="nxl-icon" aria-label="Email" title="Email" disabled={disabled} onClick={handleOpenEmail}>
            <Mail size={18} strokeWidth={1.8} aria-hidden="true" />
          </button>
          {whatsappMessage && !native && !disabled && (
            <a className="nxl-icon" aria-label="WhatsApp message" title="WhatsApp message"
              href={`https://wa.me/?text=${encodeURIComponent(whatsappMessage)}`}
              target="_blank" rel="noopener noreferrer">
              <MessageCircle size={18} strokeWidth={1.8} aria-hidden="true" />
            </a>
          )}
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
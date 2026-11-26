"use client";

import { useState } from "react";
import { Capacitor } from "@capacitor/core";
import { Download, Mail, MessageCircle, Share2 } from "lucide-react";
import type { ListAction } from "@/components/list/list-kit";
import { notify } from "@/components/nex-feedback";
import DocumentEmailDialog from "@/features/documents/components/document-email-dialog";
import { useDownloadDocumentPDF } from "@/features/documents/hooks";
import type { DocumentType } from "@/features/documents/types";

interface Target {
  documentType: DocumentType;
  documentId: string;
  documentNumber: string;
  recipient?: string | null;
}

/**
 * Icon actions for document rows: PDF (download on web, share sheet on the app), email, WhatsApp.
 * Render `dialog` once in the page.
 */
export function useDocumentRowActions() {
  const download = useDownloadDocumentPDF();
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [emailTarget, setEmailTarget] = useState<Target | null>(null);
  const native = Capacitor.isNativePlatform();

  function actionsFor(target: Target, options: { whatsapp?: string; email?: boolean } = {}): ListAction[] {
    const pdfLabel = `${native ? "Share" : "Download"} PDF ${target.documentNumber}`;
    const actions: ListAction[] = [
      {
        icon: native ? Share2 : Download,
        label: pdfLabel,
        busy: pendingId === target.documentId,
        onClick: () => {
          setPendingId(target.documentId);
          download
            .mutateAsync({ documentType: target.documentType, documentId: target.documentId, fallbackFilename: `${target.documentNumber}.pdf` })
            .catch((error: unknown) => notify(error instanceof Error ? error.message : "Unable to prepare the PDF.", "error"))
            .finally(() => setPendingId(null));
        },
      },
    ];
    if (options.email !== false) {
      actions.push({ icon: Mail, label: `Email ${target.documentNumber}`, onClick: () => setEmailTarget(target) });
    }
    if (options.whatsapp && !native) {
      const text = options.whatsapp;
      actions.push({
        icon: MessageCircle,
        label: `WhatsApp ${target.documentNumber}`,
        onClick: () => window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank", "noopener,noreferrer"),
      });
    }
    return actions;
  }

  const dialog = emailTarget ? (
    <DocumentEmailDialog
      open
      documentType={emailTarget.documentType}
      documentId={emailTarget.documentId}
      documentNumber={emailTarget.documentNumber}
      defaultRecipient={emailTarget.recipient ?? null}
      onClose={() => setEmailTarget(null)}
    />
  ) : null;

  return { actionsFor, dialog };
}

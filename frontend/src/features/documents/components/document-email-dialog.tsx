"use client";

import {
  useState,
} from "react";

import {
  Mail,
  Send,
  X,
} from "lucide-react";

import {
  useSendDocumentEmail,
} from "@/features/documents/hooks";

import type {
  DocumentType,
} from "@/features/documents/types";

import {
  APIRequestError,
} from "@/lib/api/client";

interface DocumentEmailDialogProps {
  open: boolean;
  documentType: DocumentType;
  documentId: string;
  documentNumber: string;
  defaultRecipient?: string | null;
  onClose: () => void;
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

  return "Unable to email the document.";
}

export default function DocumentEmailDialog({
  open,
  documentType,
  documentId,
  documentNumber,
  defaultRecipient = null,
  onClose,
}: DocumentEmailDialogProps) {
  const [
    recipientEmail,
    setRecipientEmail,
  ] = useState(
    defaultRecipient ?? "",
  );

  const [
    successMessage,
    setSuccessMessage,
  ] = useState<string | null>(
    null,
  );

  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string | null>(
    null,
  );

  const emailMutation =
    useSendDocumentEmail();

  if (!open) {
    return null;
  }

  const canSubmit =
    recipientEmail.trim().length > 0
    &&
    !emailMutation.isPending;

  async function handleSubmit(
    event:
      React.FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await emailMutation.mutateAsync({
        documentType,
        documentId,

        input: {
          recipient_email:
            recipientEmail.trim(),
        },
      });

      setSuccessMessage(
        `${documentNumber} was emailed successfully.`,
      );
    } catch (error) {
      setErrorMessage(
        getErrorMessage(error),
      );
    }
  }

  function handleClose(): void {
    if (emailMutation.isPending) {
      return;
    }

    setRecipientEmail(
      defaultRecipient ?? "",
    );

    setSuccessMessage(null);
    setErrorMessage(null);

    onClose();
  }

  return (
    <div
      role="presentation"
      className="
        fixed inset-0 z-[70] flex
        items-center justify-center
        bg-slate-950/50 p-4
      "
      onMouseDown={(event) => {
        if (
          event.target
          ===
          event.currentTarget
        ) {
          handleClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="
          document-email-dialog-title
        "
        className="
          w-full max-w-lg
          overflow-hidden rounded-2xl
          border border-slate-200
          bg-white text-slate-950
          shadow-2xl
        "
      >
        <header
          className="
            flex items-start
            justify-between gap-4
            border-b border-slate-200
            px-5 py-4
          "
        >
          <div>
            <div
              className="
                flex items-center gap-2
              "
            >
              <Mail
                size={18}
                className="text-blue-600"
              />

              <h2
                id="
                  document-email-dialog-title
                "
                className="
                  text-lg font-bold
                  text-slate-950
                "
              >
                Email document
              </h2>
            </div>

            <p
              className="
                mt-1 text-sm
                text-slate-600
              "
            >
              Send {documentNumber} as a PDF
              attachment.
            </p>
          </div>

          <button
            type="button"
            aria-label="Close dialog"
            disabled={
              emailMutation.isPending
            }
            onClick={handleClose}
            className="
              rounded-lg p-2
              text-slate-500
              hover:bg-slate-100
              hover:text-slate-900
              disabled:opacity-50
            "
          >
            <X size={20} />
          </button>
        </header>

        <form
          onSubmit={(event) => {
            void handleSubmit(event);
          }}
        >
          <div
            className="
              space-y-5 px-5 py-5
            "
          >
            <div>
              <label
                htmlFor="
                  document-recipient-email
                "
                className="
                  block text-sm font-semibold
                  text-slate-700
                "
              >
                Recipient email
              </label>

              <input
                id="
                  document-recipient-email
                "
                type="email"
                required
                autoFocus
                value={recipientEmail}
                disabled={
                  emailMutation.isPending
                }
                onChange={(event) => {
                  setRecipientEmail(
                    event.target.value,
                  );

                  setErrorMessage(null);
                  setSuccessMessage(null);
                }}
                placeholder="
                  customer@example.com
                "
                className="
                  mt-2 w-full rounded-lg
                  border border-slate-300
                  bg-white px-3 py-2.5
                  text-sm text-slate-950
                  outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-100
                  disabled:bg-slate-100
                "
              />
            </div>

            <div
              className="
                rounded-xl border
                border-slate-200
                bg-slate-50 p-4
              "
            >
              <p
                className="
                  text-xs font-medium
                  uppercase tracking-wide
                  text-slate-500
                "
              >
                Document
              </p>

              <p
                className="
                  mt-1 text-sm font-bold
                  text-slate-950
                "
              >
                {documentNumber}
              </p>

              <p
                className="
                  mt-1 text-xs
                  text-slate-500
                "
              >
                A PDF copy will be attached
                automatically.
              </p>
            </div>

            {errorMessage ? (
              <div
                role="alert"
                className="
                  rounded-xl border
                  border-red-200 bg-red-50
                  px-4 py-3 text-sm
                  text-red-700
                "
              >
                {errorMessage}
              </div>
            ) : null}

            {successMessage ? (
              <div
                role="status"
                className="
                  rounded-xl border
                  border-emerald-200
                  bg-emerald-50
                  px-4 py-3 text-sm
                  text-emerald-700
                "
              >
                {successMessage}
              </div>
            ) : null}
          </div>

          <footer
            className="
              flex flex-wrap
              justify-end gap-2
              border-t border-slate-200
              bg-slate-50 px-5 py-4
            "
          >
            <button
              type="button"
              disabled={
                emailMutation.isPending
              }
              onClick={handleClose}
              className="
                rounded-lg border
                border-slate-300
                bg-white px-4 py-2
                text-sm font-semibold
                text-slate-700
                hover:bg-slate-50
                disabled:opacity-50
              "
            >
              {successMessage
                ? "Close"
                : "Cancel"}
            </button>

            {!successMessage ? (
              <button
                type="submit"
                disabled={!canSubmit}
                className="
                  inline-flex items-center
                  gap-2 rounded-lg
                  bg-blue-600 px-4 py-2
                  text-sm font-semibold
                  text-white
                  hover:bg-blue-700
                  disabled:cursor-not-allowed
                  disabled:opacity-50
                "
              >
                <Send size={16} />

                {emailMutation.isPending
                  ? "Sending..."
                  : "Send email"}
              </button>
            ) : null}
          </footer>
        </form>
      </section>
    </div>
  );
}
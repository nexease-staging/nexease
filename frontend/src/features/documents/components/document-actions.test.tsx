import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";

import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import DocumentActions
  from "@/features/documents/components/document-actions";

const mockDownloadMutateAsync =
  vi.fn();

vi.mock(
  "@/lib/api/client",
  () => ({
    APIRequestError:
      class APIRequestError
        extends Error {},
  }),
);

vi.mock(
  "@/features/documents/hooks",
  () => ({
    useDownloadDocumentPDF: () => ({
      mutateAsync:
        mockDownloadMutateAsync,

      isPending: false,
    }),
  }),
);

vi.mock(
  "@/features/documents/components/document-email-dialog",
  () => ({
    default: ({
      open,
      documentType,
      documentId,
      documentNumber,
      defaultRecipient,
    }: {
      open: boolean;
      documentType: string;
      documentId: string;
      documentNumber: string;
      defaultRecipient:
        | string
        | null;
    }) => (
      open ? (
        <div
          data-testid="email-dialog"
        >
          <span>
            {documentType}
          </span>

          <span>
            {documentId}
          </span>

          <span>
            {documentNumber}
          </span>

          <span>
            {
              defaultRecipient
              ??
              "No recipient"
            }
          </span>
        </div>
      ) : null
    ),
  }),
);

describe(
  "DocumentActions",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      mockDownloadMutateAsync
        .mockResolvedValue({
          filename:
            "INV-TEST-001.pdf",

          contentType:
            "application/pdf",
        });
    });

    it(
      "renders PDF and Email actions",
      () => {
        render(
          <DocumentActions
            documentType="INVOICE"
            documentId="invoice-1"
            documentNumber={
              "INV-TEST-001"
            }
            defaultRecipient={
              "customer@example.com"
            }
          />,
        );

        expect(
          screen.getByRole(
            "button",
            {
              name: "PDF",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name: "Email",
            },
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "downloads the selected document",
      async () => {
        render(
          <DocumentActions
            documentType="INVOICE"
            documentId="invoice-1"
            documentNumber={
              "INV-TEST-001"
            }
          />,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "PDF",
            },
          ),
        );

        await waitFor(() => {
          expect(
            mockDownloadMutateAsync,
          ).toHaveBeenCalledTimes(
            1,
          );
        });

        expect(
          mockDownloadMutateAsync,
        ).toHaveBeenCalledWith({
          documentType:
            "INVOICE",

          documentId:
            "invoice-1",

          fallbackFilename:
            "INV-TEST-001.pdf",
        });
      },
    );

    it(
      "opens the email dialog with document data",
      () => {
        render(
          <DocumentActions
            documentType="VENDOR_BILL"
            documentId="bill-1"
            documentNumber={
              "BILL-TEST-001"
            }
            defaultRecipient={
              "supplier@example.com"
            }
          />,
        );

        expect(
          screen.queryByTestId(
            "email-dialog",
          ),
        ).not.toBeInTheDocument();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "Email",
            },
          ),
        );

        const dialog =
          screen.getByTestId(
            "email-dialog",
          );

        expect(
          dialog,
        ).toHaveTextContent(
          "VENDOR_BILL",
        );

        expect(
          dialog,
        ).toHaveTextContent(
          "bill-1",
        );

        expect(
          dialog,
        ).toHaveTextContent(
          "BILL-TEST-001",
        );

        expect(
          dialog,
        ).toHaveTextContent(
          "supplier@example.com",
        );
      },
    );

    it(
      "shows a download error",
      async () => {
        mockDownloadMutateAsync
          .mockRejectedValue(
            new Error(
              "PDF download failed",
            ),
          );

        render(
          <DocumentActions
            documentType="CREDIT_NOTE"
            documentId="credit-note-1"
            documentNumber={
              "CN-TEST-001"
            }
          />,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "PDF",
            },
          ),
        );

        expect(
          await screen.findByRole(
            "alert",
          ),
        ).toHaveTextContent(
          "PDF download failed",
        );
      },
    );
  },
);
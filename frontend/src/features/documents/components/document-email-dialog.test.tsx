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

import DocumentEmailDialog
  from "@/features/documents/components/document-email-dialog";

const mockEmailMutateAsync =
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
    useSendDocumentEmail: () => ({
      mutateAsync:
        mockEmailMutateAsync,

      isPending: false,
    }),
  }),
);

function renderDialog({
  defaultRecipient =
    "customer@example.com",
  onClose = vi.fn(),
}: {
  defaultRecipient?:
    | string
    | null;

  onClose?: () => void;
} = {}) {
  return render(
    <DocumentEmailDialog
      open
      documentType="INVOICE"
      documentId="invoice-1"
      documentNumber="INV-TEST-001"
      defaultRecipient={
        defaultRecipient
      }
      onClose={onClose}
    />,
  );
}

describe(
  "DocumentEmailDialog",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      mockEmailMutateAsync
        .mockResolvedValue({
          document_type:
            "INVOICE",

          document_id:
            "invoice-1",

          recipient:
            "customer@example.com",

          sent_count: 1,

          delivery: {
            id: "delivery-1",
            status: "SENT",
            channel: "EMAIL",
            recipient:
              "customer@example.com",
          },
        });
    });

    it(
      "does not render when closed",
      () => {
        render(
          <DocumentEmailDialog
            open={false}
            documentType="INVOICE"
            documentId="invoice-1"
            documentNumber={
              "INV-TEST-001"
            }
            defaultRecipient={
              "customer@example.com"
            }
            onClose={vi.fn()}
          />,
        );

        expect(
          screen.queryByText(
            "INV-TEST-001",
          ),
        ).not.toBeInTheDocument();
      },
    );

    it(
      "shows the default recipient",
      () => {
        renderDialog();

        expect(
          screen.getByDisplayValue(
            "customer@example.com",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "sends the document to the entered recipient",
      async () => {
        renderDialog();

        const emailInput =
          screen.getByDisplayValue(
            "customer@example.com",
          );

        fireEvent.change(
          emailInput,
          {
            target: {
              value:
                "billing@example.com",
            },
          },
        );

        const sendButton =
          screen.getByRole(
            "button",
            {
              name: /send/i,
            },
          );

        fireEvent.click(
          sendButton,
        );

        await waitFor(() => {
          expect(
            mockEmailMutateAsync,
          ).toHaveBeenCalledTimes(
            1,
          );
        });

        expect(
          mockEmailMutateAsync,
        ).toHaveBeenCalledWith({
          documentType:
            "INVOICE",

          documentId:
            "invoice-1",

          input: {
            recipient_email:
              "billing@example.com",
          },
        });
      },
    );

    it(
      "shows a success message after sending",
      async () => {
        renderDialog();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: /send/i,
            },
          ),
        );

        await waitFor(() => {
          expect(
            mockEmailMutateAsync,
          ).toHaveBeenCalled();
        });

        expect(
        await screen.findByRole(
            "status",
        ),
        ).toHaveTextContent(
        "INV-TEST-001 was emailed successfully.",
        );
      },
    );

    it(
      "shows an email delivery error",
      async () => {
        mockEmailMutateAsync
          .mockRejectedValue(
            new Error(
              "Email delivery failed",
            ),
          );

        renderDialog();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: /send/i,
            },
          ),
        );

        expect(
          await screen.findByRole(
            "alert",
          ),
        ).toHaveTextContent(
          "Email delivery failed",
        );
      },
    );

    it(
      "closes and resets the dialog",
      () => {
        const onClose =
          vi.fn();

        renderDialog({
          onClose,
        });

        const emailInput =
          screen.getByDisplayValue(
            "customer@example.com",
          );

        fireEvent.change(
          emailInput,
          {
            target: {
              value:
                "changed@example.com",
            },
          },
        );

        const closeButton =
        screen.getByRole(
            "button",
            {
            name: "Cancel",
            },
        );

        fireEvent.click(
          closeButton,
        );

        expect(
          onClose,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );
  },
);
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

import DocumentLogsPage
  from "@/app/(protected)/document-logs/page";

const mockUseDocumentAccessLogs =
  vi.fn();

const mockUseDocumentAccessLogSummary =
  vi.fn();

const mockUseDocumentDeliveryLogs =
  vi.fn();

const mockUseDocumentDeliveryLogSummary =
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
    useDocumentAccessLogs: (
      ...args: unknown[]
    ) =>
      mockUseDocumentAccessLogs(
        ...args,
      ),

    useDocumentAccessLogSummary: (
      ...args: unknown[]
    ) =>
      mockUseDocumentAccessLogSummary(
        ...args,
      ),

    useDocumentDeliveryLogs: (
      ...args: unknown[]
    ) =>
      mockUseDocumentDeliveryLogs(
        ...args,
      ),

    useDocumentDeliveryLogSummary: (
      ...args: unknown[]
    ) =>
      mockUseDocumentDeliveryLogSummary(
        ...args,
      ),
  }),
);

const accessLog = {
  id: "access-1",

  user: {
    id: "user-1",
    email: "admin@example.com",
  },

  document_type: "INVOICE",
  document_id: "invoice-1",
  document_number: "INV-TEST-001",
  action: "PDF",
  created_at:
    "2026-09-01T10:30:00Z",
};

const deliveryLog = {
  id: "delivery-1",

  document_type: "INVOICE",
  document_id: "invoice-1",
  document_number: "INV-TEST-001",

  channel: "EMAIL",
  recipient:
    "customer@example.com",

  subject: "Invoice",
  status: "SENT",

  recipient_overridden: false,
  custom_subject: false,
  custom_message: false,

  error_message: null,

  sent_at:
    "2026-09-01T10:35:00Z",

  created_at:
    "2026-09-01T10:34:00Z",

  updated_at:
    "2026-09-01T10:35:00Z",
};

function setDefaultMocks() {
  mockUseDocumentAccessLogs
    .mockReturnValue({
      data: {
        logs: [
          accessLog,
        ],
      },

      isLoading: false,
      isFetching: false,
      error: null,
    });

  mockUseDocumentAccessLogSummary
    .mockReturnValue({
      data: {
        total_logs: 1,
        pdf_count: 1,
      },

      isLoading: false,
      error: null,
    });

  mockUseDocumentDeliveryLogs
    .mockReturnValue({
      data: {
        logs: [
          deliveryLog,
        ],
      },

      isLoading: false,
      isFetching: false,
      error: null,
    });

  mockUseDocumentDeliveryLogSummary
    .mockReturnValue({
      data: {
        total_logs: 1,
        sent_count: 1,
      },

      isLoading: false,
      error: null,
    });
}

describe(
  "DocumentLogsPage",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      setDefaultMocks();
    });

    it(
      "shows access activity by default",
      () => {
        render(
          <DocumentLogsPage />,
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Document Activity",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Access Summary",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Access history",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "INV-TEST-001",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "admin@example.com",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Total Logs",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Pdf Count",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "enables only access queries on the access tab",
      () => {
        render(
          <DocumentLogsPage />,
        );

        expect(
          mockUseDocumentAccessLogs,
        ).toHaveBeenCalledWith(
          {
            limit: 100,
          },
          true,
        );

        expect(
          mockUseDocumentAccessLogSummary,
        ).toHaveBeenCalledWith(
          true,
        );

        expect(
          mockUseDocumentDeliveryLogs,
        ).toHaveBeenCalledWith(
          {
            limit: 100,
          },
          false,
        );

        expect(
          mockUseDocumentDeliveryLogSummary,
        ).toHaveBeenCalledWith(
          false,
        );
      },
    );

    it(
      "applies access log filters",
      async () => {
        render(
          <DocumentLogsPage />,
        );

        changeControl(
          screen.getByRole(
            "combobox",
          ),
          {
            target: {
              value: "INVOICE",
            },
          },
        );

        changeControl(
          screen.getByPlaceholderText(
            "e.g. PDF",
          ),
          {
            target: {
              value: " PDF ",
            },
          },
        );

        const inputs =
          screen.getAllByRole(
            "textbox",
          );

        const documentNumberInput =
          inputs.find(
            (input) =>
              input
                .getAttribute(
                  "placeholder",
                )
              ===
              null,
          );

        expect(
          documentNumberInput,
        ).toBeDefined();

        changeControl(
          documentNumberInput!,
          {
            target: {
              value:
                " INV-TEST-001 ",
            },
          },
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Apply filters",
            },
          ),
        );

        await waitFor(() => {
          expect(
            mockUseDocumentAccessLogs,
          ).toHaveBeenLastCalledWith(
            {
              document_type:
                "INVOICE",

              action:
                "PDF",

              document_number:
                "INV-TEST-001",

              limit: 100,
            },
            true,
          );
        });
      },
    );

    it(
      "clears access log filters",
      async () => {
        render(
          <DocumentLogsPage />,
        );

        changeControl(
          screen.getByRole(
            "combobox",
          ),
          {
            target: {
              value:
                "VENDOR_BILL",
            },
          },
        );

        changeControl(
          screen.getByPlaceholderText(
            "e.g. PDF",
          ),
          {
            target: {
              value: "PDF",
            },
          },
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "Clear",
            },
          ),
        );

        await waitFor(() => {
          expect(
            mockUseDocumentAccessLogs,
          ).toHaveBeenLastCalledWith(
            {
              limit: 100,
            },
            true,
          );
        });

        expect(
          screen.getByRole(
            "combobox",
          ),
        ).toHaveValue("All document types");

        expect(
          screen.getByPlaceholderText(
            "e.g. PDF",
          ),
        ).toHaveValue("");
      },
    );

    it(
      "switches to delivery activity",
      () => {
        render(
          <DocumentLogsPage />,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Delivery Logs",
            },
          ),
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Delivery Summary",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Delivery history",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "customer@example.com",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "SENT",
          ),
        ).toBeInTheDocument();

        expect(
          mockUseDocumentDeliveryLogs,
        ).toHaveBeenLastCalledWith(
          {
            limit: 100,
          },
          true,
        );

        expect(
          mockUseDocumentDeliveryLogSummary,
        ).toHaveBeenLastCalledWith(
          true,
        );
      },
    );

    it(
      "applies delivery log filters",
      async () => {
        render(
          <DocumentLogsPage />,
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Delivery Logs",
            },
          ),
        );

        changeControl(
          screen.getByRole(
            "combobox",
          ),
          {
            target: {
              value: "INVOICE",
            },
          },
        );

        changeControl(
          screen.getByPlaceholderText(
            "Delivery status",
          ),
          {
            target: {
              value: " SENT ",
            },
          },
        );

        changeControl(
          screen.getByPlaceholderText(
            "Email recipient",
          ),
          {
            target: {
              value:
                " customer@example.com ",
            },
          },
        );

        const textboxes =
          screen.getAllByRole(
            "textbox",
          );

        const documentNumberInput =
          textboxes.find(
            (input) =>
              !input.getAttribute(
                "placeholder",
              ),
          );

        expect(
          documentNumberInput,
        ).toBeDefined();

        changeControl(
          documentNumberInput!,
          {
            target: {
              value:
                " INV-TEST-001 ",
            },
          },
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Apply filters",
            },
          ),
        );

        await waitFor(() => {
          expect(
            mockUseDocumentDeliveryLogs,
          ).toHaveBeenLastCalledWith(
            {
              document_type:
                "INVOICE",

              status:
                "SENT",

              recipient:
                "customer@example.com",

              document_number:
                "INV-TEST-001",

              limit: 100,
            },
            true,
          );
        });
      },
    );

    it(
      "shows access loading state",
      () => {
        mockUseDocumentAccessLogs
          .mockReturnValue({
            data: undefined,
            isLoading: true,
            isFetching: false,
            error: null,
          });

        render(
          <DocumentLogsPage />,
        );

        expect(
          screen.getByText(
            "Loading access logs...",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "shows access error state",
      () => {
        mockUseDocumentAccessLogs
          .mockReturnValue({
            data: undefined,
            isLoading: false,
            isFetching: false,
            error:
              new Error(
                "Access logs failed",
              ),
          });

        render(
          <DocumentLogsPage />,
        );

        expect(
          screen.getByRole(
            "alert",
          ),
        ).toHaveTextContent(
          "Access logs failed",
        );
      },
    );

    it(
      "shows empty access state",
      () => {
        mockUseDocumentAccessLogs
          .mockReturnValue({
            data: {
              logs: [],
            },
            isLoading: false,
            isFetching: false,
            error: null,
          });

        render(
          <DocumentLogsPage />,
        );

        expect(
          screen.getByText(
            "No document access logs found.",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "shows an empty summary state",
      () => {
        mockUseDocumentAccessLogSummary
          .mockReturnValue({
            data: {},
            isLoading: false,
            error: null,
          });

        render(
          <DocumentLogsPage />,
        );

        expect(
          screen.getByText(
            "No summary data available.",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
function changeControl(element:HTMLElement, event:{target:{value:string}}){
 if(element.getAttribute('role')==='combobox' && element.tagName==='INPUT'){
  const select=element.parentElement?.querySelector('select');
  const option=Array.from(select?.options??[]).find(o=>o.value===event.target.value);
  fireEvent.focus(element);fireEvent.change(element,{target:{value:option?.text??event.target.value}});
  const button=Array.from(document.querySelectorAll('[role="option"]')??[]).find(b=>b.textContent===option?.text);
  if(!button)throw new Error('Matching option not rendered');fireEvent.click(button);
 }else fireEvent.change(element,event);
}

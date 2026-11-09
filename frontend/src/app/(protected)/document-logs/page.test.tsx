import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import Page from "./page";
const state = vi.hoisted(() => ({
  access: vi.fn(),
  delivery: vi.fn(),
  refresh: vi.fn(),
}));
vi.mock("@/features/documents/hooks", () => ({
  useDocumentAccessLogs: (...args: unknown[]) => state.access(...args),
  useDocumentDeliveryLogs: (...args: unknown[]) => state.delivery(...args),
  useDocumentAccessLogSummary: () => ({
    data: { total: 1 },
    refetch: state.refresh,
  }),
  useDocumentDeliveryLogSummary: () => ({ data: {}, refetch: state.refresh }),
}));
vi.mock("@/components/nex-dialog", () => ({
  default: ({
    title,
    children,
    onClose,
  }: {
    title: string;
    children: React.ReactNode;
    onClose: () => void;
  }) => (
    <section role="dialog" aria-label={title}>
      <button onClick={onClose}>Close</button>
      {children}
    </section>
  ),
}));
beforeEach(() => {
  state.access.mockReturnValue({
    data: {
      logs: [
        {
          id: "1",
          document_number: "INV-1",
          document_type: "INVOICE",
          action: "PDF",
          created_at: null,
          user: null,
        },
      ],
    },
    refetch: state.refresh,
  });
  state.delivery.mockReturnValue({
    data: { logs: [] },
    refetch: state.refresh,
  });
  state.refresh.mockClear();
});
it("renders missing/deleted user safely and opens detail popup", () => {
  render(<Page />);
  expect(screen.getByText("Deleted user")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "View details" }));
  expect(
    screen.getByRole("dialog", { name: "Document access" }),
  ).toBeInTheDocument();
});
it("applies filters and switches to email delivery", () => {
  render(<Page />);
  fireEvent.change(screen.getByLabelText("Document number"), {
    target: { value: "INV-1" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Apply filters" }));
  expect(state.access).toHaveBeenLastCalledWith(
    expect.objectContaining({ document_number: "INV-1" }),
    true,
  );
  fireEvent.click(screen.getByRole("tab", { name: "Delivery logs" }));
  expect(state.delivery).toHaveBeenLastCalledWith(
    expect.objectContaining({ limit: 100 }),
    true,
  );
  expect(
    screen.getByText("No document activity matches these filters."),
  ).toBeInTheDocument();
});
it("refreshes logs and summary", () => {
  render(<Page />);
  fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
  expect(state.refresh).toHaveBeenCalledTimes(2);
});

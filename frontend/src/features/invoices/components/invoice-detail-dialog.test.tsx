import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import InvoiceDetailDialog from "./invoice-detail-dialog";

vi.mock("@/features/auth/auth-context", () => ({
  useAuth: () => ({ authentication: { role: { permissions: [] } } }),
}));
vi.mock("@/features/invoices/hooks", () => ({
  useInvoice: () => ({ isLoading: true }),
  useIssueInvoice: () => ({ isPending: false }),
  useCancelInvoice: () => ({ isPending: false }),
}));
vi.mock("@/features/business/workspace", () => ({
  getConfig: async () => ({ modules: {} }),
}));

it("can open and close an already mounted invoice dialog", () => {
  const client = new QueryClient();
  const view = (open: boolean) => (
    <QueryClientProvider client={client}>
      <InvoiceDetailDialog open={open} invoiceId={open ? "invoice-1" : null}
        onClose={() => {}} onRecordPayment={() => {}} />
    </QueryClientProvider>
  );
  const { rerender } = render(view(false));
  rerender(view(true));
  expect(screen.getByRole("heading", { name: "Invoice Details" })).toBeInTheDocument();
  rerender(view(false));
  expect(screen.queryByRole("heading", { name: "Invoice Details" })).not.toBeInTheDocument();
});

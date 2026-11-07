import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import FastInvoice, { whatsappLink } from "./fast-invoice";
import { apiRequest } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn() }));
vi.mock("@/features/auth/auth-context", () => ({
  useAuth: () => ({ authentication: { role: { permissions: ["invoices.create", "invoices.issue"] } } }),
}));
vi.mock("@/features/business/gst-lookup", () => ({ default: () => null }));
vi.mock("@/features/business/barcode-scan", () => ({
  default: ({ renderInput }: { renderInput?: (...a: unknown[]) => unknown }) =>
    renderInput?.(() => {}, { current: null }, false) ?? null,
}));
vi.mock("@/features/documents/components/document-actions", () => ({
  default: () => <button type="button">PDF</button>,
}));
vi.mock("@/features/invoices/hooks", () => ({
  useInvoice: () => ({
    data: {
      id: "inv1",
      invoice_number: "INV-001",
      invoice_date: "2026-11-06",
      status: "ISSUED",
      total_amount: "118.00",
      balance_due: "118.00",
      customer: { name: "New customer", phone: "9876543210", email: null },
    },
    isError: false,
  }),
  useIssueInvoice: () => ({ mutate: vi.fn(), isPending: false, isError: false }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(apiRequest).mockImplementation(
    async (path: string) =>
      ({ data: path.includes("/lookup/") ? { records: [] } : { id: "inv1" } }) as never,
  );
});

function mount() {
  const onClose = vi.fn();
  const onCreated = vi.fn();
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <FastInvoice onClose={onClose} onCreated={onCreated} />
    </QueryClientProvider>,
  );
  return { onClose, onCreated };
}

function fillMinimal() {
  fireEvent.change(screen.getByLabelText("Customer name *"), { target: { value: "New customer" } });
  fireEvent.change(screen.getByLabelText("name line 1"), { target: { value: "Service" } });
  fireEvent.change(screen.getByLabelText("unit_price line 1"), { target: { value: "100" } });
  fireEvent.change(screen.getByLabelText("tax_rate line 1"), { target: { value: "18" } });
}

describe("Fast invoice", () => {
  it("shows a live estimated total including GST", () => {
    mount();
    fillMinimal();
    fireEvent.change(screen.getByLabelText("quantity line 1"), { target: { value: "2" } });
    expect(screen.getAllByText(/236\.00/).length).toBeGreaterThan(0);
  });

  it("blocks saving without customer, items and place of supply", async () => {
    mount();
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Choose a customer");
    fillMinimal();
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("place of supply");
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it("saves and issues via the direct-invoice endpoint, then offers sharing", async () => {
    mount();
    fillMinimal();
    fireEvent.change(screen.getByPlaceholderText("State code, e.g. 27"), { target: { value: "27" } });
    fireEvent.click(screen.getByRole("button", { name: "Save & issue" }));
    await waitFor(() => expect(screen.getByText("Invoice issued")).toBeInTheDocument());
    expect(apiRequest).toHaveBeenCalledWith(
      "/business/direct-invoices/",
      expect.objectContaining({
        method: "POST",
        body: expect.objectContaining({
          customer: expect.objectContaining({ name: "New customer" }),
          billing_details: { supply_type: "taxable", place_of_supply: "27" },
          items: [expect.objectContaining({ name: "Service", unit_price: "100", tax_rate: "18" })],
        }),
      }),
    );
    expect(apiRequest).toHaveBeenCalledWith("/invoices/inv1/issue/", expect.objectContaining({ method: "POST" }));
    expect(screen.getByRole("link", { name: /WhatsApp/ })).toHaveAttribute(
      "href",
      expect.stringContaining("https://wa.me/919876543210"),
    );
  });

  it("keeps a manually changed or cleared WhatsApp number", async () => {
    mount();
    fillMinimal();
    fireEvent.change(screen.getByPlaceholderText("State code, e.g. 27"), { target: { value: "27" } });
    fireEvent.click(screen.getByRole("button", { name: "Save & issue" }));
    const input = await screen.findByLabelText("Customer WhatsApp number");
    expect(input).toHaveValue("9876543210");
    fireEvent.change(input, { target: { value: "9123456780" } });
    expect(screen.getByRole("link", { name: /WhatsApp/ })).toHaveAttribute(
      "href", expect.stringContaining("https://wa.me/919123456780"),
    );
    fireEvent.change(input, { target: { value: "" } });
    expect(input).toHaveValue("");
    expect(screen.queryByRole("link", { name: /WhatsApp/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "WhatsApp" })).toBeDisabled();
  });

  it("builds WhatsApp links for 10-digit and country-coded numbers", () => {
    expect(whatsappLink("98765 43210", "hi")).toBe("https://wa.me/919876543210?text=hi");
    expect(whatsappLink("+91 98765-43210", "a b")).toBe("https://wa.me/919876543210?text=a%20b");
  });
});

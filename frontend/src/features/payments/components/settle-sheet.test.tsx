import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SettleSheet from "./settle-sheet";
import { apiRequest } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn() }));
vi.mock("@/components/search-select", () => ({ default: ({ "aria-label": label, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) => <select aria-label={label} {...props} /> }));
const accounts = [
  { id: "cash", account_name: "Cash box", account_type: "CASH", bank_name: null, masked_account_number: null, currency: "INR", is_active: true },
  { id: "hdfc", account_name: "HDFC current", account_type: "BANK", bank_name: "HDFC", masked_account_number: "••4417", currency: "INR", is_active: true },
];
vi.mock("@/features/invoices/hooks", () => ({ useInvoiceBankAccounts: () => ({ data: { bank_accounts: accounts, count: 2 } }) }));
vi.mock("@/features/vendor-bills/hooks", () => ({ useVendorBillBankAccounts: () => ({ data: accounts }) }));

const party = { id: "c1", name: "Sharma Traders", code: "C1", phone: "9876543210", email: "", open_count: 2, outstanding: "1500.00", overdue: "1000.00", buckets: { current: "500.00", d1_30: "0.00", d31_60: "1000.00", d61_90: "0.00", d90_plus: "0.00" }, oldest_due: "2026-10-12", max_days_overdue: 45 };
const documents = [
  { id: "i1", party_id: "c1", number: "INV-1", date: "2026-09-27", due_date: "2026-10-12", days_overdue: 45, bucket: "d31_60", total: "1000.00", outstanding: "1000.00", status: "ISSUED" },
  { id: "i2", party_id: "c1", number: "INV-2", date: "2026-11-20", due_date: "2026-12-06", days_overdue: 0, bucket: "current", total: "500.00", outstanding: "500.00", status: "ISSUED" },
];

function serve(settle: () => Promise<unknown>) {
  vi.mocked(apiRequest).mockImplementation(((path: string) => {
    if (path.includes("party_id=")) return Promise.resolve({ data: { side: "receivable", party, documents, total: "1500.00" } });
    if (path.startsWith("/business/payments/outstanding/")) return Promise.resolve({ data: { side: "receivable", parties: [party], totals: {}, as_of: "", party_count: 1, document_count: 2, truncated: false } });
    return settle();
  }) as never);
}

function mount(onClose = vi.fn()) {
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><SettleSheet side="receivable" partyId="c1" onClose={onClose} /></QueryClientProvider>);
  return onClose;
}

beforeEach(() => vi.clearAllMocks());

describe("SettleSheet", () => {
  it("splits the amount oldest first and sends explicit allocations with a request key", async () => {
    serve(() => Promise.resolve({ data: { payments: [] }, message: "ok" }));
    const onClose = mount();
    await screen.findByText("INV-1");
    fireEvent.change(screen.getByLabelText("Amount"), { target: { value: "1200" } });
    expect(screen.getByLabelText("Amount for INV-1")).toHaveValue(1000);
    expect(screen.getByLabelText("Amount for INV-2")).toHaveValue(200);
    expect(screen.getByLabelText("Received into")).toHaveValue("hdfc"); // UPI goes to a bank account
    fireEvent.click(screen.getByRole("button", { name: "Cash" }));
    expect(screen.getByLabelText("Received into")).toHaveValue("cash");
    fireEvent.change(screen.getByLabelText("Reference"), { target: { value: "R-9" } });
    fireEvent.click(screen.getByRole("button", { name: "Save receipt" }));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(apiRequest).toHaveBeenCalledWith("/business/payments/receive/", expect.objectContaining({
      method: "POST",
      body: expect.objectContaining({
        party_id: "c1", amount: "1200.00", payment_method: "CASH", bank_account_id: "cash", reference_number: "R-9",
        allocations: [{ document_id: "i1", amount: "1000.00" }, { document_id: "i2", amount: "200.00" }],
        request_key: expect.stringMatching(/^pay-[A-Za-z0-9_-]{16,}$/),
      }),
    }));
  });

  it("explains a split that does not add up, without calling the server", async () => {
    serve(() => Promise.resolve({ data: {} }));
    mount();
    await screen.findByText("INV-1");
    fireEvent.change(screen.getByLabelText("Amount"), { target: { value: "1200" } });
    fireEvent.change(screen.getByLabelText("Amount for INV-2"), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: "Save receipt" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Split ₹1,000.00 of ₹1,200.00");
    fireEvent.click(screen.getByRole("button", { name: /Use ₹1,000.00 as the amount/ }));
    expect(screen.getByLabelText("Amount")).toHaveValue(1000);
    expect(vi.mocked(apiRequest).mock.calls.some(([path]) => String(path).includes("/receive/"))).toBe(false);
  });

  it("blocks more than the outstanding total", async () => {
    serve(() => Promise.resolve({ data: {} }));
    mount();
    await screen.findByText("INV-1");
    fireEvent.change(screen.getByLabelText("Amount"), { target: { value: "2000" } });
    fireEvent.click(screen.getByRole("button", { name: "Save receipt" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Advance payments are not supported yet");
  });

  it("locks the form after a partial save and resends the identical request", async () => {
    const partial = Object.assign(new Error("Recorded 1 of 2 parts. INV-2: Bank is offline."), { status: 422 });
    let calls = 0;
    serve(() => (++calls === 1 ? Promise.reject(partial) : Promise.resolve({ data: { payments: [] } })));
    const onClose = mount();
    await screen.findByText("INV-1");
    fireEvent.click(screen.getByRole("button", { name: "Settle in full" }));
    fireEvent.click(screen.getByRole("button", { name: "Save receipt" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Recorded 1 of 2");
    expect(screen.getByLabelText("Amount")).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Finish recording" }));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const bodies = vi.mocked(apiRequest).mock.calls.filter(([path]) => String(path).includes("/receive/")).map(([, options]) => (options as { body: unknown }).body);
    expect(bodies).toHaveLength(2);
    expect(bodies[1]).toEqual(bodies[0]);
  });
});

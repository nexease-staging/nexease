import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import RegisterScreen from "./register-screen";
import { apiRequest } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn() }));
let permissions = ["invoices.read", "bills.read", "invoices.record_payment", "bills.record_payment"];
vi.mock("@/features/auth/auth-context", () => ({ useAuth: () => ({ authentication: { organization: { name: "Demo Traders" }, role: { permissions } } }) }));
vi.mock("@/features/customer-payments/components/customer-payment-detail-dialog", () => ({ default: ({ open, paymentId }: { open: boolean; paymentId: string | null }) => (open ? <div role="dialog">Receipt {paymentId}</div> : null) }));
vi.mock("./settle-sheet", () => ({ default: ({ side }: { side: string }) => <div role="dialog">Settle {side}</div> }));

const payments = [
  { id: "p1", direction: "in", number: "PAY-1", date: "2026-11-25", party: { id: "c1", name: "Sharma Traders", code: "C1", phone: "9876543210", email: "" }, amount: "1200.00", method: "UPI", account: { id: "b", name: "HDFC current" }, reference: "UTR1", notes: "", documents: [{ id: "i1", number: "INV-1", amount: "1000.00" }, { id: "i2", number: "INV-2", amount: "200.00" }] },
  { id: "s1", direction: "out", number: "SP-1", date: "2026-11-24", party: { id: "s1", name: "Om Cement Depot", code: "S1", phone: "", email: "" }, amount: "300.00", method: "CASH", account: { id: "c", name: "Cash box" }, reference: "", notes: "", documents: [{ id: "b1", number: "B-1", amount: "300.00" }] },
];

beforeEach(() => {
  vi.clearAllMocks();
  HTMLDialogElement.prototype.showModal ??= function (this: HTMLDialogElement) { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close ??= function (this: HTMLDialogElement) { this.removeAttribute("open"); };
  permissions = ["invoices.read", "bills.read", "invoices.record_payment", "bills.record_payment"];
  vi.mocked(apiRequest).mockImplementation(((path: string) => path.startsWith("/business/payments/outstanding/")
    ? Promise.resolve({ data: { totals: { outstanding: "1800.00", overdue: "1300.00", buckets: {} }, parties: [] } })
    : Promise.resolve({ data: { summary: { money_in: "1200.00", money_out: "300.00", net: "900.00", count: 2, by_method: {} }, payments, pagination: { page: 1, page_size: 25, total: 2, pages: 1 } } })) as never);
});

const mount = (props: Partial<React.ComponentProps<typeof RegisterScreen>> = {}) =>
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><RegisterScreen title="Payments" subtitle="x" {...props} /></QueryClientProvider>);

const registerCalls = () => vi.mocked(apiRequest).mock.calls.map(([p]) => String(p)).filter((p) => p.startsWith("/business/payments/register/"));

describe("RegisterScreen", () => {
  it("shows money in and out with signs, totals and details", async () => {
    mount();
    const list = await screen.findByRole("list", { name: "Payments" });
    expect(within(list).getByText("+ ₹1,200.00")).toBeInTheDocument();
    expect(within(list).getByText("− ₹300.00")).toBeInTheDocument();
    expect(screen.getByTitle("₹900.00")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Show details of PAY-1" }));
    expect(within(screen.getByRole("list", { name: "PAY-1 details" })).getByText("Invoice INV-2")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open receipt PAY-1" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("Receipt p1");
  });

  it("switches direction and applies period filters", async () => {
    mount();
    await screen.findByText("Sharma Traders");
    fireEvent.click(screen.getByRole("button", { name: "Money out" }));
    await waitFor(() => expect(registerCalls().some((p) => p.includes("direction=out"))).toBe(true));
    fireEvent.click(screen.getByRole("button", { name: "More filters" }));
    fireEvent.change(screen.getByLabelText("From date"), { target: { value: "2026-04-01" } });
    fireEvent.change(screen.getByLabelText("Payment method filter"), { target: { value: "UPI" } });
    await waitFor(() => expect(registerCalls().some((p) => p.includes("from=2026-04-01") && p.includes("method=UPI"))).toBe(true));
  });

  it("customer payments view is locked to money in and receives payments", async () => {
    mount({ initialDirection: "in", lockDirection: true, title: "Customer payments" });
    await screen.findByText("Sharma Traders");
    expect(screen.queryByRole("group", { name: "Payment direction" })).not.toBeInTheDocument();
    expect(registerCalls()[0]).toContain("direction=in");
    fireEvent.click(screen.getAllByRole("button", { name: "Receive payment" })[0]);
    expect(screen.getByRole("dialog")).toHaveTextContent("Settle receivable");
  });

  it("hides money out without bills.read", async () => {
    permissions = ["customer_payments.read"];
    mount();
    await screen.findByText("Sharma Traders");
    expect(screen.queryByRole("button", { name: "Money out" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Receive payment|Pay supplier/ })).not.toBeInTheDocument();
  });
});

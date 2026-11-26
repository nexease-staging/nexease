import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import OutstandingScreen from "./outstanding-screen";
import { apiRequest } from "@/lib/api/client";
import { reminderText } from "../reminder";

vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn() }));
vi.mock("@/features/auth/auth-context", () => ({
  useAuth: () => ({ authentication: { organization: { name: "Demo Traders" }, role: { permissions: ["invoices.read", "invoices.record_payment"] } } }),
}));
vi.mock("./settle-sheet", () => ({ default: ({ partyId }: { partyId?: string }) => <div role="dialog">Settle {partyId ?? "new"}</div> }));

const zero = { current: "0.00", d1_30: "0.00", d31_60: "0.00", d61_90: "0.00", d90_plus: "0.00" };
const sharma = { id: "c1", name: "Sharma Traders", code: "C1", phone: "9876543210", email: "a@sharma.in", open_count: 2, outstanding: "1500.00", overdue: "1000.00", buckets: { ...zero, current: "500.00", d31_60: "1000.00" }, oldest_due: "2026-10-12", max_days_overdue: 45 };
const patil = { id: "c2", name: "Patil Hardware", code: "C2", phone: "", email: "", open_count: 1, outstanding: "300.00", overdue: "300.00", buckets: { ...zero, d90_plus: "300.00" }, oldest_due: "2026-08-18", max_days_overdue: 100 };
const fresh = { id: "c3", name: "New Buyer", code: "C3", phone: "", email: "", open_count: 1, outstanding: "200.00", overdue: "0.00", buckets: { ...zero, current: "200.00" }, oldest_due: "2026-12-20", max_days_overdue: 0 };

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(apiRequest).mockImplementation(((path: string) => path.includes("party_id=")
    ? Promise.resolve({ data: { documents: [{ id: "i1", number: "INV-1", outstanding: "1000.00", days_overdue: 45, due_date: "2026-10-12", date: "2026-09-27" }] } })
    : Promise.resolve({ data: { side: "receivable", as_of: "2026-11-26", totals: { outstanding: "2000.00", overdue: "1300.00", buckets: { current: "700.00", d1_30: "0.00", d31_60: "1000.00", d61_90: "0.00", d90_plus: "300.00" } }, party_count: 3, document_count: 4, truncated: false, parties: [sharma, patil, fresh] } })) as never);
});

const mount = () => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><OutstandingScreen side="receivable" /></QueryClientProvider>);

describe("OutstandingScreen", () => {
  it("lists customers with totals, filters overdue and 90+ days", async () => {
    mount();
    const list = await screen.findByRole("list", { name: "Receivables" });
    expect(within(list).getAllByRole("listitem")).toHaveLength(3);
    expect(screen.getByTitle("₹2,000.00")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Overdue" }));
    expect(within(list).queryByText("New Buyer")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "90+ days" }));
    expect(within(list).getAllByRole("listitem")).toHaveLength(1);
    expect(within(list).getByText("Patil Hardware")).toBeInTheDocument();
  });

  it("expands a customer to show open invoices and opens the receive sheet for them", async () => {
    mount();
    fireEvent.click(await screen.findByRole("button", { name: "Show open invoices for Sharma Traders" }));
    expect(await screen.findByText("INV-1")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Receive from Sharma Traders" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("Settle c1");
  });

  it("offers WhatsApp and email reminders only where contact details exist", async () => {
    mount();
    await screen.findByText("Sharma Traders");
    expect(screen.getByRole("button", { name: "WhatsApp reminder to Sharma Traders" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Email reminder to Sharma Traders" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "WhatsApp reminder to Patil Hardware" })).not.toBeInTheDocument();
    const open = vi.spyOn(window, "open").mockReturnValue(null);
    fireEvent.click(screen.getByRole("button", { name: "WhatsApp reminder to Sharma Traders" }));
    await vi.waitFor(() => expect(open).toHaveBeenCalled());
    const url = String(open.mock.calls[0][0]);
    expect(url.startsWith("https://wa.me/919876543210?text=")).toBe(true);
    expect(decodeURIComponent(url)).toContain("INV-1: ₹1,000.00 (45 days overdue)");
  });
});

describe("reminderText", () => {
  it("is polite, names the business and caps the invoice list", () => {
    const docs = Array.from({ length: 7 }, (_, i) => ({ id: String(i), party_id: "c1", number: `INV-${i}`, date: null, due_date: "2026-12-01", days_overdue: 0, bucket: "current" as const, total: "10.00", outstanding: "10.00", status: "ISSUED" }));
    const text = reminderText({ name: "Sharma Traders", outstanding: "70.00", overdue: "0.00" }, "Demo Traders", docs);
    expect(text).toContain("Namaste Sharma Traders");
    expect(text).toContain("friendly reminder from Demo Traders");
    expect(text).toContain("₹70.00 is outstanding.");
    expect(text).toContain("and 2 more");
  });
});

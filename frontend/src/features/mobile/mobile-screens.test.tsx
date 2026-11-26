import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import MobileHome from "./mobile-home";
import PartiesScreen, { reminderText, whatsappLink } from "./parties-screen";
import type { MobileHome as Home, PartyList } from "./api";

const { api, perms } = vi.hoisted(() => ({ api: vi.fn(), perms: { list: ["invoices.read", "invoices.create", "invoices.record_payment", "customers.read", "customers.create", "suppliers.read"] } }));
vi.mock("@/lib/api/client", () => ({ apiRequest: api }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }), usePathname: () => "/home" }));
vi.mock("@/features/auth/auth-context", () => ({ useAuth: () => ({ authentication: { organization: { name: "Demo Traders" }, role: { permissions: perms.list } } }) }));
vi.mock("@/lib/authorization/permissions", () => ({ hasPermission: (list: string[], p: string) => list.includes(p) }));

const home: Home = { as_of: "2026-11-26", receivable: "84560.00", payable: "12000.00", sales_today: "4484.00", sales_month: "126500.00", purchases_month: "40000.00", money_in_month: "50000.00", money_out_month: "0.00",
  transactions: [
    { type: "sale", id: "i1", number: "INV/0148", party: "Sharma Traders", date: "2026-11-26", amount: "4484.00", balance: "4484.00", status: "ISSUED", href: "/invoices?view=i1" },
    { type: "payment_in", id: "p1", number: "RCPT-9", party: "Patil Hardware", date: "2026-11-25", amount: "5000.00", balance: null, status: "UPI", href: "/payments" },
    { type: "expense", id: "e1", number: "R1", party: "HP pump", date: "2026-11-25", amount: "500.00", balance: null, status: "Petrol / fuel", href: "/expenses" },
  ] };
const parties: PartyList = { side: "customers", count: 2, total_balance: "84560.00", with_balance: 1, parties: [
  { id: "c1", name: "Sharma Traders", code: "C1", phone: "9876543210", email: "", gstin: "", city: "Pune", balance: "84560.00", overdue: "35000.00" },
  { id: "c2", name: "Gupta Stores", code: "C2", phone: "", email: "", gstin: "", city: "", balance: "0.00", overdue: "0.00" },
] };

const wrap = (ui: React.ReactNode) => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{ui}</QueryClientProvider>);
beforeEach(() => { vi.clearAllMocks(); localStorage.clear(); });

describe("Phone home", () => {
  it("shows what you will get and pay, quick actions allowed by role, and a filterable feed", async () => {
    api.mockResolvedValue({ data: home });
    wrap(<MobileHome />);
    expect(await screen.findByText("₹84,560")).toBeInTheDocument();
    expect(screen.getByText("₹12,000")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add sale" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Purchase" })).not.toBeInTheDocument();
    expect(screen.getByText("Unpaid · ₹4,484")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Payments" }));
    expect(screen.queryByText("Sharma Traders")).not.toBeInTheDocument();
    expect(screen.getByText("Patil Hardware")).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Hide amounts"));
    expect(screen.queryByText("₹84,560")).not.toBeInTheDocument();
  });

  it("falls back to the saved copy when offline", async () => {
    localStorage.setItem("nexease:mobile-cache:home", JSON.stringify({ at: Date.now(), data: home }));
    api.mockRejectedValue(new Error("Network error"));
    wrap(<MobileHome />);
    expect(await screen.findByText(/Offline — showing saved figures/)).toBeInTheDocument();
    expect(screen.getByText("₹84,560")).toBeInTheDocument();
  });

  it("saves the latest summary for offline use", async () => {
    api.mockResolvedValue({ data: home });
    wrap(<MobileHome />);
    await screen.findByText("₹84,560");
    expect(JSON.parse(localStorage.getItem("nexease:mobile-cache:home")!).data.receivable).toBe("84560.00");
  });
});

describe("Parties", () => {
  it("lists balances with call, WhatsApp reminder and receive for parties who owe", async () => {
    api.mockImplementation(async (path: string) => (path.includes("outstanding") ? { data: { documents: [{ id: "i1", number: "INV/0131", days_overdue: 45, due_date: "2026-10-12", outstanding: "35000.00" }] } } : { data: parties }));
    wrap(<PartiesScreen />);
    expect(await screen.findByText("Sharma Traders")).toBeInTheDocument();
    expect(screen.getByText("1 of 2 customers with a balance")).toBeInTheDocument();
    expect(screen.getByLabelText("Call Sharma Traders")).toHaveAttribute("href", "tel:9876543210");
    expect(screen.getByLabelText("WhatsApp Sharma Traders").getAttribute("href")).toMatch(/^https:\/\/wa\.me\/919876543210\?text=/);
    expect(screen.getAllByRole("button", { name: "Receive" })).toHaveLength(1);
    expect(screen.queryByLabelText("Call Gupta Stores")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Sharma Traders/ }));
    expect(await screen.findByText("45 days overdue")).toBeInTheDocument();
  });

  it("switches to suppliers", async () => {
    api.mockResolvedValue({ data: { ...parties, side: "suppliers", parties: [] } });
    wrap(<PartiesScreen />);
    fireEvent.click(await screen.findByRole("tab", { name: "Suppliers" }));
    expect(api.mock.calls.some(([p]) => String(p).includes("side=suppliers"))).toBe(true);
  });

  it("writes a polite reminder and handles numbers without a country code", () => {
    expect(reminderText(parties.parties[0], "Demo Traders", true)).toContain("₹84,560 is due");
    expect(whatsappLink("098765 43210", "hi")).toBe("https://wa.me/919876543210?text=hi");
    expect(whatsappLink("123", "hi")).toBeNull();
  });
});

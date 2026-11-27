import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import PhoneHome from "./home";
import PhoneDashboard from "./dashboard";
import PhoneMenu from "./menu";
import { CreateSheet, PhoneTabBar, screenTitle } from "./shell";

const { api, perms, push, quick, share } = vi.hoisted(() => ({
  api: vi.fn(), push: vi.fn(), quick: vi.fn(), share: vi.fn(),
  perms: { list: ["invoices.read", "invoices.create", "invoices.record_payment", "customers.read", "customers.create", "suppliers.read", "bills.read"] },
}));
vi.mock("@/lib/api/client", () => ({ apiRequest: api, apiBinaryRequest: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, replace: vi.fn(), back: vi.fn() }), usePathname: () => "/home" }));
vi.mock("@/features/auth/auth-context", () => ({ useAuth: () => ({ authentication: { user: { first_name: "Ravi", last_name: "S", email: "r@x.in" }, organization: { name: "Demo Traders" }, role: { name: "Owner", permissions: perms.list } }, signOut: vi.fn() }) }));
vi.mock("@/lib/authorization/permissions", () => ({ hasPermission: (list: string[], p: string) => list.includes(p) }));
vi.mock("@/features/mobile/quick-actions", () => ({ runQuick: quick }));
vi.mock("@/features/share/api", () => ({ openShare: share, fetchPdf: vi.fn(), waLink: (p: string, t: string) => `https://wa.me/91${p}?text=${t}` }));
vi.mock("@/features/notifications/components/notification-menu", () => ({ default: () => null }));
vi.mock("@/components/mobile/easy-workspace", () => ({ useEasyFeatures: () => [
  { label: "Administration", items: [{ label: "Users", href: "/settings/users", icon: () => null }] },
  { label: "Sales", items: [{ label: "Invoices", href: "/invoices", icon: () => null }, { label: "Quotations", href: "/quotations", icon: () => null }] },
] }));
vi.mock("@/components/mobile/device-notification-settings", () => ({ default: () => null }));
vi.mock("@/components/mobile/mobile-connection", () => ({ default: () => null }));

const sale = (i: number, over = {}) => ({ type: "sale", id: "i" + i, number: "INV-" + i, party: i === 1 ? "Krishna Hardware" : "Patil Builders", party_id: "c1", date: `2026-11-${10 + i}`, due_date: null, amount: String(1000 * i), balance: i === 1 ? "1000" : "0", status: i === 1 ? "ISSUED" : "PAID", ...over });
const doc = { type: "sale", id: "i1", number: "INV-1", status: "ISSUED", date: "2026-11-11", due_date: null, party: { id: "c1", name: "Krishna Hardware", phone: "9820000000", email: "" },
  subtotal: "847.46", tax: "152.54", discount: "0", total: "1000", paid: "0", balance: "1000", lines: [{ name: "Cement", qty: "2", unit: "Bag", rate: "423.73", tax_rate: "18", amount: "1000" }], can_pay: true, href: "/invoices?view=i1" };

function setup() {
  api.mockImplementation(async (path: string) => {
    if (path.startsWith("/business/mobile/transactions/")) return { data: { type: "sale", rows: path.includes("search=patil") ? [sale(2)] : [sale(1), sale(2)], page: 0, more: false } };
    if (path.startsWith("/business/mobile/document/")) return { data: doc };
    if (path.startsWith("/business/mobile/parties/")) return { data: { side: path.includes("suppliers") ? "suppliers" : "customers", parties: [{ id: "c1", name: path.includes("suppliers") ? "Om Steel" : "Krishna Hardware", code: "C1", phone: "9820000000", email: "", gstin: "", city: "Pune", balance: "1000", overdue: "0" }], count: 1, total_balance: "1000", with_balance: 1 } };
    if (path.startsWith("/business/mobile/dashboard/")) return { data: { as_of: "2026-11-27", receivable: "1000", payable: "500", overdue_receivable: "0", sales_month: "3000", sales_prev: "2000", purchases_month: "500",
      trend: [{ month: "2026-10", sales: "2000", purchases: "400" }, { month: "2026-11", sales: "3000", purchases: "500" }], top_dues: [{ id: "c1", name: "Krishna Hardware", phone: "", balance: "1000", overdue: "0" }], banks: [], tally: { company: "Sharma Traders", last_seen: null } } };
    return { data: {} };
  });
}
const wrap = (ui: React.ReactNode) => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{ui}</QueryClientProvider>);
beforeEach(() => { vi.clearAllMocks(); setup(); });

describe("phone home", () => {
  it("shows the segments and quick actions the role allows, lists sales and opens a document", async () => {
    wrap(<PhoneHome />);
    expect(screen.getByRole("tab", { name: "Sales" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Purchases" })).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Expenses" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Purchase" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Money in" }));
    expect(quick).toHaveBeenCalledWith("payment_in");
    expect(await screen.findByText("Krishna Hardware")).toBeInTheDocument();
    expect(screen.getByText("Due ₹1,000")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Krishna Hardware"));
    expect(await screen.findByText("Invoice INV-1")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "WhatsApp" }));
    expect(share).toHaveBeenCalledWith(expect.objectContaining({ kind: "invoice", id: "i1", channel: "whatsapp" }));
    fireEvent.click(screen.getByRole("button", { name: "Receive payment" }));
    expect(quick).toHaveBeenCalledWith("payment_in", "c1");
  });

  it("searches on the server and shows parties with what you will get", async () => {
    wrap(<PhoneHome />);
    fireEvent.change(await screen.findByLabelText("Search this list"), { target: { value: "patil" } });
    await waitFor(() => expect(screen.queryByText("Krishna Hardware")).not.toBeInTheDocument());
    fireEvent.click(screen.getByRole("tab", { name: "Parties" }));
    expect(await screen.findByText("Om Steel")).toBeInTheDocument();
    expect(screen.getAllByText("You’ll get")[0]).toBeInTheDocument();
    fireEvent.click(screen.getByText("Krishna Hardware"));
    fireEvent.click(await screen.findByRole("button", { name: "Share statement" }));
    expect(share).toHaveBeenCalledWith(expect.objectContaining({ kind: "statement", id: "c1", side: "customer" }));
  });
});

describe("phone shell", () => {
  it("offers only permitted create actions and opens forms", () => {
    const close = vi.fn();
    render(<CreateSheet onClose={close} />);
    expect(screen.getByRole("button", { name: "Sale invoice" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Purchase bill" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Quotation" }));
    expect(push).toHaveBeenCalledWith("/quotations?new=1");
    fireEvent.click(screen.getByRole("button", { name: "Customer" }));
    expect(quick).toHaveBeenCalledWith("customer");
  });

  it("has the five-place tab bar with the + in the middle", () => {
    render(<PhoneTabBar />);
    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    expect([...nav.children].map((c) => c.textContent || c.getAttribute("aria-label"))).toEqual(["Home", "Dashboard", "Create new", "Items", "Menu"]);
    expect(screen.getByRole("link", { name: "Home" })).toHaveAttribute("aria-current", "page");
    fireEvent.click(screen.getByRole("button", { name: "Create new" }));
    expect(screen.getByRole("dialog", { name: "Create new" })).toBeInTheDocument();
  });

  it("names screens from the navigation", () => {
    expect(screenTitle("/invoices")).toBe("Invoices");
    expect(screenTitle("/parties/")).toBe("Parties");
  });
});

describe("phone dashboard and menu", () => {
  it("shows balances, growth and the Tally link", async () => {
    wrap(<PhoneDashboard />);
    expect(await screen.findByText("₹3,000")).toBeInTheDocument();
    expect(screen.getByText(/50% vs last month/)).toBeInTheDocument();
    expect(screen.getByText("Tally · Sharma Traders")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Send statement to Krishna Hardware" }));
    expect(share).toHaveBeenCalledWith(expect.objectContaining({ kind: "statement", id: "c1" }));
  });

  it("orders groups, expands them, searches every feature and opens settings", async () => {
    wrap(<PhoneMenu />);
    const groups = screen.getAllByRole("button", { expanded: false }).map((b) => b.textContent);
    expect(groups[0]).toContain("Sales");
    fireEvent.click(screen.getByRole("button", { name: /Sales/ }));
    expect(screen.getByRole("link", { name: "Quotations" })).toHaveAttribute("href", "/quotations");
    fireEvent.change(screen.getByLabelText("Search all features"), { target: { value: "user" } });
    expect(screen.getByRole("link", { name: /Users/ })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Search all features"), { target: { value: "" } });
    act(() => { fireEvent.click(screen.getByRole("button", { name: "Settings" })); });
    expect(screen.getByRole("radiogroup", { name: "Appearance" })).toBeInTheDocument();
    expect(screen.getByText("Demo Traders · Owner")).toBeInTheDocument();
  });
});

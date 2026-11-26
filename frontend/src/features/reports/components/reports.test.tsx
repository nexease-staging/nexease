import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ReportsHub from "./reports-hub";
import ReportViewer from "./report-viewer";
import { apiRequest } from "@/lib/api/client";
import { change, formatValue, periodPresets } from "../api";

vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn() }));
vi.mock("next/link", () => ({ default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => <a href={href} {...rest}>{children}</a> }));
let permissions: string[] = [];
vi.mock("@/features/auth/auth-context", () => ({ useAuth: () => ({ authentication: { organization: { name: "Demo Traders" }, role: { permissions } } }) }));

const itemReport = {
  id: "sales/item", title: "Sales by item", dated: true, period: { from: "2026-11-01", to: "2026-11-26" },
  columns: [
    { key: "item", label: "Item", type: "text" }, { key: "sku", label: "SKU", type: "text" }, { key: "qty", label: "Quantity", type: "qty" },
    { key: "net", label: "Taxable value", type: "money" }, { key: "tax", label: "GST", type: "money" }, { key: "total", label: "Total", type: "money" }, { key: "share", label: "Share", type: "percent" },
  ],
  rows: [
    { item: "Enamel paint", sku: "PNT", qty: "4.00", net: "2240.00", tax: "627.20", total: "2867.20", share: "5.24" },
    { item: "OPC cement", sku: "CEM", qty: "100.00", net: "41000.00", tax: "7380.00", total: "48380.00", share: "88.4" },
  ],
  totals: { qty: "104.00", net: "43240.00", tax: "8007.20", total: "51247.20", share: "100.00" },
  previous: { period: { from: "2026-10-06", to: "2026-10-31" }, totals: { qty: "10.00", net: "4000.00", tax: "720.00", total: "4720.00", share: "100.00" } },
  chart: { type: "bar", x: "item", y: ["total"], limit: 8 },
  notes: ["Only issued invoices are counted."],
};

beforeEach(() => {
  vi.clearAllMocks();
  window.localStorage.clear();
  permissions = ["invoices.read", "inventory.read"];
  vi.mocked(apiRequest).mockResolvedValue({ data: itemReport } as never);
});

const wrap = (node: React.ReactNode) => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{node}</QueryClientProvider>);

describe("ReportsHub", () => {
  it("shows only reports the role can read, and searches across groups", () => {
    wrap(<ReportsHub />);
    expect(screen.getByRole("link", { name: /Item sales/ })).toHaveAttribute("href", "/reports/view?id=sales%2Fitem");
    expect(screen.getByRole("link", { name: /Low stock summary/ })).toBeInTheDocument();
    expect(screen.queryByText("Purchase transactions")).not.toBeInTheDocument();
    expect(screen.queryByText("Gross profit by item")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Customer outstanding/ })).toHaveAttribute("href", "/accounts-receivable");
    fireEvent.change(screen.getByLabelText("Search reports"), { target: { value: "low stock" } });
    expect(screen.getAllByRole("listitem")).toHaveLength(1);
  });

  it("pins favourites to the top and keeps them", () => {
    const { unmount } = wrap(<ReportsHub />);
    fireEvent.click(screen.getByRole("button", { name: "Add Item sales to favourites" }));
    expect(within(screen.getByRole("heading", { name: "Favourites" }).closest("section")!).getByText("Item sales")).toBeInTheDocument();
    unmount();
    wrap(<ReportsHub />);
    expect(screen.getByRole("heading", { name: "Favourites" })).toBeInTheDocument();
  });
});

describe("ReportViewer", () => {
  it("shows KPIs with change, chart, table with totals, and notes", async () => {
    wrap(<ReportViewer id="sales/item" />);
    const table = await screen.findByRole("table", { name: "Item sales" });
    expect(apiRequest).toHaveBeenCalledWith(expect.stringMatching(/^\/business\/reports\/run\/\?report=sales%2Fitem&from=\d{4}-\d{2}-01&to=.*&compare=1$/));
    expect(screen.getByText("₹51,247.20", { selector: ".nxr-kpi strong" })).toBeInTheDocument();
    expect(screen.getAllByText("+985.7% vs previous")[0]).toBeInTheDocument();
    expect(screen.getByRole("figure", { name: /top 2 by total/ })).toBeInTheDocument();
    expect(within(table).getByText("Total · 2 rows")).toBeInTheDocument();
    expect(within(screen.getByRole("list", { name: "Item sales rows" })).getByText("₹48,380.00")).toBeInTheDocument();
    expect(screen.getByText("Only issued invoices are counted.")).toBeInTheDocument();
  });

  it("sorts by a column and changes the period", async () => {
    wrap(<ReportViewer id="sales/item" />);
    const table = await screen.findByRole("table", { name: "Item sales" });
    fireEvent.click(within(table).getByRole("button", { name: "Total" }));
    expect(within(table).getAllByRole("row")[1]).toHaveTextContent("OPC cement");
    fireEvent.click(within(table).getByRole("button", { name: /Total/ }));
    expect(within(table).getAllByRole("row")[1]).toHaveTextContent("Enamel paint");
    fireEvent.click(screen.getByRole("button", { name: periodPresets()[3].label }));
    await waitFor(() => expect(vi.mocked(apiRequest).mock.calls.some(([p]) => String(p).includes(`from=${periodPresets()[3].from}`))).toBe(true));
    fireEvent.click(screen.getByLabelText("Compare with previous period"));
    await waitFor(() => expect(vi.mocked(apiRequest).mock.calls.some(([p]) => !String(p).includes("compare="))).toBe(true));
  });

  it("reports an unknown id and server errors plainly", async () => {
    const { unmount } = wrap(<ReportViewer id="nope/bad" />);
    expect(screen.getByText("Report not found")).toBeInTheDocument();
    unmount();
    vi.mocked(apiRequest).mockRejectedValue(new Error("GST reports need the taxation.read permission."));
    wrap(<ReportViewer id="sales/hsn" />);
    expect(await screen.findByRole("alert")).toHaveTextContent("taxation.read");
  });
});

describe("report helpers", () => {
  it("builds Indian financial year presets", () => {
    const presets = periodPresets(new Date("2026-02-10T00:00:00Z"));
    expect(presets.find((p) => p.key === "this-fy")).toMatchObject({ label: "FY 2025-26", from: "2025-04-01" });
    expect(presets.find((p) => p.key === "this-quarter")?.from).toBe("2026-01-01");
    expect(presets.find((p) => p.key === "last-fy")).toMatchObject({ from: "2024-04-01", to: "2025-03-31" });
  });
  it("formats values and change", () => {
    expect(formatValue("1234567.5", "money")).toBe("₹12,34,567.50");
    expect(formatValue("12.345", "percent")).toBe("12.3%");
    expect(change("150", "100")).toBe(50);
    expect(change("150", "0")).toBeNull();
  });
});

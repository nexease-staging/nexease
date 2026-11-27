import type { ReactNode } from "react";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { MainDashboard } from "@/features/dashboard/types";
import { compact, periodLabel, presetRange, rupees } from "@/features/dashboard/format";

const state = vi.hoisted(() => ({
  result: {} as Record<string, unknown>,
  calls: [] as Array<{ start_date?: string; end_date?: string }>,
  permissions: ["invoices.create", "invoices.read"] as string[],
}));

vi.mock("recharts", () => {
  const Box = ({ children }: { children?: ReactNode }) => <div>{children}</div>;
  const Nil = () => null;
  return { ResponsiveContainer: Box, BarChart: Box, Bar: Box, Cell: Nil, CartesianGrid: Nil, ReferenceLine: Nil, Tooltip: Nil, XAxis: Nil, YAxis: Nil };
});
vi.mock("./business-setup-card", () => ({ default: () => null }));
vi.mock("@/features/auth/auth-context", () => ({
  useAuth: () => ({ authentication: { organization: { name: "Ramesh Steel" }, user: { first_name: "Ramesh" }, role: { permissions: state.permissions } } }),
}));
vi.mock("@/features/dashboard/hooks", () => ({
  useMainDashboard: (p: { start_date?: string; end_date?: string }) => {
    state.calls.push(p);
    return state.result;
  },
}));

import DashboardShell from "./dashboard-shell";

const data: MainDashboard = {
  period: { start_date: "2026-04-01", end_date: "2026-11-27" },
  kpis: { total_sales: "1000000", total_purchases: "600000", receivables: "300000", payables: "500000", bank_balance: "1248730.50", inventory_value: "2154300", out_of_stock_items: 2 },
  sales_trend: [{ period: "2026-10", amount: "400000" }, { period: "2026-11", amount: "600000" }],
  purchase_trend: [{ period: "2026-10", amount: "250000" }, { period: "2026-11", amount: "350000" }],
  cash_flow: [{ period: "2026-10", inflow: "300000", outflow: "350000", net: "-50000" }, { period: "2026-11", inflow: "500000", outflow: "200000", net: "300000" }],
  receivable_aging: { current: "150000", "1_30": "60000", "31_60": "30000", "61_90": "40000", "90_plus": "20000" },
  invoice_status: { issued: 4, partially_paid: 2, paid: 30, overdue: 3 },
  bill_status: { posted: 2, partially_paid: 1, paid: 20, overdue: 0 },
  inventory_status: { in_stock: 50, out_of_stock: 2 },
  top_customers: [{ customer_id: "c1", customer_name: "Patil Builders", amount: "250000" }],
  top_suppliers: [],
  alerts: { overdue_invoices: 3, overdue_bills: 0, out_of_stock_items: 2 },
  recent_activity: [
    { activity_type: "INVOICE", reference_id: "i1", reference_number: "INV-0009", description: "Invoice to Patil Builders", activity_date: "2026-11-27T10:00:00Z", amount: "15340" },
    { activity_type: "STOCK_MOVEMENT", reference_id: "m1", reference_number: "SM-1", description: "Sheets issued", activity_date: "2026-11-20T10:00:00Z", amount: null, quantity: "7" },
  ],
};

const ok = (d: MainDashboard | undefined = data) => ({ data: d, isLoading: false, isFetching: false, isError: false, error: null, refetch: vi.fn(), dataUpdatedAt: 0 });

describe("dashboard format helpers", () => {
  it("formats rupees in lakh and crore", () => {
    expect(rupees("1248730.5")).toBe("₹12,48,731");
    expect(compact(684250)).toBe("₹6.84 L");
    expect(compact(43530000)).toBe("₹4.35 Cr");
    expect(compact(96400)).toBe("₹96.4K");
    expect(compact(-45000)).toBe("-₹45K");
    expect(compact("not a number")).toBe("₹0");
  });
  it("labels months and days", () => {
    expect(periodLabel("2026-03")).toBe("Mar");
    expect(periodLabel("2026-03-14")).toBe("14 Mar");
    expect(periodLabel("W12")).toBe("W12");
  });
  it("uses the April to March financial year", () => {
    const nov = new Date(2026, 10, 27);
    expect(presetRange("fy", nov)).toEqual({ start_date: "2026-04-01", end_date: "2026-11-27" });
    expect(presetRange("quarter", nov)).toEqual({ start_date: "2026-10-01", end_date: "2026-11-27" });
    expect(presetRange("last_fy", nov)).toEqual({ start_date: "2025-04-01", end_date: "2026-03-31" });
    const feb = new Date(2027, 1, 10);
    expect(presetRange("fy", feb).start_date).toBe("2026-04-01");
    expect(presetRange("quarter", feb).start_date).toBe("2027-01-01");
    expect(presetRange("month", feb).start_date).toBe("2027-02-01");
  });
});

describe("DashboardShell", () => {
  beforeEach(() => {
    state.calls = [];
    state.permissions = ["invoices.create", "invoices.read"];
    state.result = ok();
  });

  it("greets the user and shows the money position in plain words", () => {
    render(<DashboardShell />);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toMatch(/Ramesh$/);
    expect(screen.getByText(/from 1 Apr 2026 to 27 Nov 2026/)).toBeInTheDocument();
    const band = screen.getByRole("region", { name: "Money position" });
    expect(within(band).getByText("₹12,48,731")).toBeInTheDocument();
    expect(within(band).getByRole("link", { name: /Customers owe you/ })).toHaveAttribute("href", "/accounts-receivable");
    expect(band.querySelector(".nxd-band-net")?.textContent).toContain("₹2 L more than customers owe you");
  });

  it("lists only the alerts that need action, each linked to where it is fixed", () => {
    render(<DashboardShell />);
    const strip = screen.getByRole("region", { name: "Needs attention" });
    expect(within(strip).getByRole("link", { name: /3 invoices are past due/ })).toHaveAttribute("href", "/accounts-receivable");
    expect(within(strip).getByRole("link", { name: /2 items are out of stock/ })).toHaveAttribute("href", "/inventory");
    expect(within(strip).queryByText(/bills? (is|are) past due/)).not.toBeInTheDocument();
  });

  it("says when nothing needs attention", () => {
    state.result = ok({ ...data, alerts: { overdue_invoices: 0, overdue_bills: 0, out_of_stock_items: 0 } });
    render(<DashboardShell />);
    expect(screen.getByText(/Nothing needs your attention right now/)).toBeInTheDocument();
  });

  it("summarises trends, aging, status, rankings and activity", () => {
    render(<DashboardShell />);
    expect(screen.getByRole("heading", { name: "Sales and purchases" })).toBeInTheDocument();
    expect(screen.getByText("+₹4 L")).toBeInTheDocument();
    expect(screen.getByText("+₹2.5 L")).toBeInTheDocument();
    expect(screen.getByText(/₹60K/, { selector: "strong" }).closest("p")?.textContent).toContain("(20%) is more than 60 days late");
    expect(screen.getByRole("link", { name: "Sales invoices" })).toHaveAttribute("href", "/invoices");
    expect(screen.getByText("Patil Builders")).toBeInTheDocument();
    expect(screen.getByText("25%")).toBeInTheDocument();
    expect(screen.getByText("No purchases in this period yet.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Invoice to Patil Builders/ })).toHaveAttribute("href", "/invoices?view=i1");
    expect(screen.getByText("7 units")).toBeInTheDocument();
  });

  it("switches period presets and opens custom dates", () => {
    render(<DashboardShell />);
    expect(screen.getByRole("button", { name: "This FY" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "Last FY" }));
    const last = state.calls.at(-1)!;
    expect(last.start_date?.endsWith("-04-01")).toBe(true);
    expect(last.end_date?.endsWith("-03-31")).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Custom" }));
    fireEvent.change(screen.getByLabelText("From"), { target: { value: "2025-06-01" } });
    expect(state.calls.at(-1)).toEqual({ start_date: "2025-06-01", end_date: last.end_date });
  });

  it("filters quick actions by permission", () => {
    state.permissions = ["invoices.read"];
    render(<DashboardShell />);
    const nav = screen.getByRole("navigation", { name: "Quick actions" });
    expect(within(nav).queryByRole("link", { name: "New invoice" })).not.toBeInTheDocument();
    expect(within(nav).getByRole("link", { name: "Record payment" })).toBeInTheDocument();
  });

  it("shows loading and a retryable error", () => {
    state.result = { ...ok(undefined), isLoading: true };
    const view = render(<DashboardShell />);
    expect(screen.getByRole("status", { name: "Loading dashboard" })).toBeInTheDocument();
    const refetch = vi.fn();
    state.result = { ...ok(undefined), isError: true, error: new Error("Server unavailable."), refetch };
    view.rerender(<DashboardShell />);
    expect(screen.getByRole("alert").textContent).toContain("Server unavailable.");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(refetch).toHaveBeenCalled();
  });
});

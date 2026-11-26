import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import FinanceHub from "./finance-hub";
import StatementView from "./statement-view";
import { change, presets } from "./api";

const { api } = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock("@/lib/api/client", () => ({ apiRequest: api, apiBinaryRequest: vi.fn() }));
vi.mock("@/features/business/workspace", () => ({ exportWorkbook: vi.fn() }));
vi.mock("@/features/reports/components/report-chart", () => ({ default: ({ title }: { title: string }) => <div data-testid="chart">{title}</div> }));

const overview = {
  from: "2026-04-01", to: "2026-11-26", previous: { from: "2025-04-01", to: "2025-11-26" },
  cash_bank: "420500.00", receivable: "177000.00", payable: "45000.00", gst_position: "27000.00",
  income: "101000.00", expenses: "80500.00", net_profit: "20500.00", gross_profit: "40000.00",
  previous_income: "80000.00", previous_expenses: "90000.00", previous_net_profit: "-10000.00",
  ratios: { gross_margin: "40.0", net_margin: "20.3", current_ratio: "2.1", receivable_days: "45.2", payable_days: "30.0" },
  trend: [{ period: "2026-05", income: "100000.00", expense: "60000.00", net: "40000.00" }],
  top_expenses: [{ account_id: "a1", name: "Cost of goods sold", amount: "60000.00", share: "74.5" }],
  bank_accounts: [{ id: "b1", name: "HDFC current", type: "BANK", bank: "HDFC", number: "5678", balance: "440500.00" }],
  unreconciled: 3, draft_journals: 1, alerts: [{ tone: "warn", text: "1 journal entries are still drafts and not in your reports.", href: "/journal-entries" }],
};
const pl = {
  statement: "pl", from: "2026-04-01", to: "2026-06-30", previous_period: { from: "2026-01-01", to: "2026-03-31" },
  sections: [
    { key: "revenue", label: "Revenue from operations", rows: [{ account_id: "s", code: "4000", name: "Sales", amount: "100000.00", previous: "50000.00", percent: "100.0" }], total: "100000.00", previous: "50000.00", percent: "100.0" },
    { key: "cost_of_sales", label: "Cost of sales", rows: [{ account_id: "c", code: "5000", name: "Cost of goods sold", amount: "60000.00", previous: "0.00", percent: "60.0" }], total: "60000.00", previous: "0.00", percent: "60.0" },
    { key: "operating_expenses", label: "Operating expenses", rows: [], total: "20000.00", previous: "0.00", percent: "20.0" },
    { key: "other_income", label: "Other income", rows: [], total: "1000.00", previous: "0.00", percent: "1.0" },
    { key: "other_expenses", label: "Finance and other expenses", rows: [], total: "500.00", previous: "0.00", percent: "0.5" },
  ],
  subtotals: [
    { key: "gross_profit", label: "Gross profit", amount: "40000.00", previous: "50000.00", percent: "40.0" },
    { key: "operating_profit", label: "Operating profit", amount: "20000.00", previous: "50000.00", percent: "20.0" },
    { key: "net_profit", label: "Net profit", amount: "20500.00", previous: "50000.00", percent: "20.5" },
  ],
  totals: {},
};

const wrap = (ui: React.ReactNode) => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{ui}</QueryClientProvider>);
beforeEach(() => vi.clearAllMocks());

describe("Finance hub", () => {
  it("shows balances, profit with change, alerts, banks and every finance tool", async () => {
    api.mockResolvedValue({ data: overview });
    wrap(<FinanceHub />);
    expect(await screen.findByText("₹4,20,500")).toBeInTheDocument();
    expect(screen.getByText("GST payable (net)")).toBeInTheDocument();
    expect(screen.getByText("Net profit")).toBeInTheDocument();
    expect(screen.getByText(/1 journal entries are still drafts/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Cost of goods sold/ })).toHaveAttribute("href", "/general-ledger?account=a1");
    expect(screen.getByText("3 to reconcile")).toBeInTheDocument();
    for (const name of ["Profit & loss", "Balance sheet", "Trial balance", "Banking"]) expect(screen.getAllByText(name).length).toBeGreaterThan(0);
  });

  it("changes the period", async () => {
    api.mockResolvedValue({ data: overview });
    wrap(<FinanceHub />);
    await screen.findByText("₹4,20,500");
    fireEvent.change(screen.getByLabelText("Period"), { target: { value: "last_fy" } });
    const lastFy = presets().find((p) => p.key === "last_fy")!;
    await waitFor(() => expect(api).toHaveBeenLastCalledWith(`/business/finance/overview/?from=${lastFy.from}&to=${lastFy.to}`));
  });
});

describe("Profit & loss", () => {
  it("lists sections with accounts linked to the ledger, subtotals and comparison", async () => {
    api.mockResolvedValue({ data: pl });
    wrap(<StatementView kind="profit-and-loss" />);
    expect(await screen.findByRole("link", { name: /4000\s*Sales/ })).toHaveAttribute("href", "/general-ledger?account=s");
    expect(screen.getAllByText("Gross profit").length).toBeGreaterThan(0);
    expect(screen.getByText(/01 Jan 2026|1 Jan 2026/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Revenue from operations" }));
    expect(screen.queryByRole("link", { name: /4000\s*Sales/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Compare"));
    await waitFor(() => expect(String(api.mock.calls.at(-1)?.[0])).toContain("compare=0"));
  });
});

it("percentage change needs an earlier figure", () => {
  expect(change("150", "100")).toBe(50);
  expect(change("50", "0")).toBeNull();
  expect(change("20", "-10")).toBe(300);
});

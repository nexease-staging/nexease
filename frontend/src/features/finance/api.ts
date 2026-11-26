import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api/client";

export type FinanceOverview = {
  from: string; to: string; previous: { from: string; to: string };
  cash_bank: string; receivable: string; payable: string; gst_position: string;
  income: string; expenses: string; net_profit: string; gross_profit: string;
  previous_income: string; previous_expenses: string; previous_net_profit: string;
  ratios: { gross_margin: string | null; net_margin: string | null; current_ratio: string | null; receivable_days: string | null; payable_days: string | null };
  trend: { period: string; income: string; expense: string; net: string }[];
  top_expenses: { account_id: string; name: string; amount: string; share: string }[];
  bank_accounts: { id: string; name: string; type: string; bank: string; number: string; balance: string }[];
  unreconciled: number; draft_journals: number;
  alerts: { tone: "danger" | "warn" | "info"; text: string; href: string }[];
};

export type StatementRow = { account_id: string; code: string; name: string; amount: string; previous: string | null; percent?: string | null };
export type StatementSection = { key: string; label: string; group?: string; rows: StatementRow[]; total: string; previous: string | null; percent?: string | null };

export type ProfitAndLoss = {
  statement: "pl"; from: string; to: string; previous_period: { from: string; to: string } | null;
  sections: StatementSection[];
  subtotals: { key: string; label: string; amount: string; previous: string | null; percent: string | null }[];
  totals: Record<string, string>;
};

export type BalanceSheet = {
  statement: "bs"; as_of: string; previous_date: string | null; sections: StatementSection[];
  totals: Record<string, string>; previous_totals: Record<string, string> | null; balanced: boolean;
};

const qs = (p: Record<string, string | undefined>) => new URLSearchParams(Object.entries(p).filter(([, v]) => v) as [string, string][]).toString();

export const useFinanceOverview = (from: string, to: string) =>
  useQuery({ queryKey: ["finance", "overview", from, to], queryFn: async () => (await apiRequest<FinanceOverview>(`/business/finance/overview/?${qs({ from, to })}`)).data });

export function useStatement<T extends ProfitAndLoss | BalanceSheet>(kind: "profit-and-loss" | "balance-sheet", params: { from?: string; to?: string; compare: boolean }) {
  const query = qs({ from: params.from, to: params.to, compare: params.compare ? "1" : "0" });
  return useQuery({ queryKey: ["finance", "statement", kind, query], queryFn: async () => (await apiRequest<T>(`/business/finance/statements/${kind}/?${query}`)).data });
}

export const statementExport = (kind: string, p: { from?: string; to?: string; compare: boolean }) => `/business/finance/statements/${kind}/?${qs({ from: p.from, to: p.to, compare: p.compare ? "1" : "0", format: "xlsx" })}`;

export const inr = (v: string | number | null | undefined, digits = 0) =>
  v === null || v === undefined || v === "" ? "—" : new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: digits, minimumFractionDigits: digits }).format(Number(v));

export function change(current: string, previous: string) {
  const c = Number(current), p = Number(previous);
  if (!p) return null;
  return ((c - p) / Math.abs(p)) * 100;
}

const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

/** Indian financial year and other common reporting periods. */
export function presets(now = new Date()) {
  const fy = now.getMonth() >= 3 ? now.getFullYear() : now.getFullYear() - 1;
  const q = Math.floor(((now.getMonth() + 9) % 12) / 3); // FY quarter 0..3 (Apr–Jun = 0)
  const qStartMonth = (3 + q * 3) % 12;
  const qStartYear = qStartMonth < 3 ? fy + 1 : fy;
  return [
    { key: "fy", label: "This financial year", from: `${fy}-04-01`, to: iso(now) },
    { key: "quarter", label: "This quarter", from: iso(new Date(qStartYear, qStartMonth, 1)), to: iso(now) },
    { key: "month", label: "This month", from: iso(new Date(now.getFullYear(), now.getMonth(), 1)), to: iso(now) },
    { key: "last_month", label: "Last month", from: iso(new Date(now.getFullYear(), now.getMonth() - 1, 1)), to: iso(new Date(now.getFullYear(), now.getMonth(), 0)) },
    { key: "last_fy", label: "Last financial year", from: `${fy - 1}-04-01`, to: `${fy}-03-31` },
  ];
}

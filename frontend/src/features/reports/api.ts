import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api/client";

export type ColumnType = "text" | "date" | "int" | "qty" | "money" | "percent";
export interface ReportColumn { key: string; label: string; type: ColumnType }
export type ReportRow = Record<string, string | number>;
export interface ReportChart { type: "bar" | "line"; x: string; y: string[]; limit?: number }

export interface ReportData {
  id: string;
  title: string;
  dated: boolean;
  period: { from: string; to: string };
  columns: ReportColumn[];
  rows: ReportRow[];
  totals: Record<string, string | number>;
  previous: { period: { from: string; to: string }; totals: Record<string, string | number> } | null;
  chart: ReportChart | null;
  notes: string[];
}

export function useReport(id: string, from: string, to: string, compare: boolean) {
  return useQuery({
    queryKey: ["report", id, from, to, compare],
    queryFn: async () => {
      const query = new URLSearchParams({ report: id, from, to, ...(compare ? { compare: "1" } : {}) });
      return (await apiRequest<ReportData>(`/business/reports/run/?${query}`)).data;
    },
    enabled: Boolean(id && from && to),
    placeholderData: keepPreviousData,
    staleTime: 60_000,
  });
}

/** Periods people actually ask for. The Indian financial year runs April to March. */
export function periodPresets(today = new Date(Date.now() + 330 * 60_000)) {
  const iso = (d: Date) => d.toISOString().slice(0, 10);
  const y = today.getUTCFullYear(), m = today.getUTCMonth();
  const q = Math.floor(((m + 9) % 12) / 3); // FY quarter: Apr–Jun = 0
  const fy = m >= 3 ? y : y - 1;
  const qStartMonth = 3 + q * 3;
  return [
    { key: "this-month", label: "This month", from: iso(new Date(Date.UTC(y, m, 1))), to: iso(today) },
    { key: "last-month", label: "Last month", from: iso(new Date(Date.UTC(y, m - 1, 1))), to: iso(new Date(Date.UTC(y, m, 0))) },
    { key: "this-quarter", label: "This quarter", from: iso(new Date(Date.UTC(fy, qStartMonth, 1))), to: iso(today) },
    { key: "this-fy", label: `FY ${fy}-${String(fy + 1).slice(2)}`, from: `${fy}-04-01`, to: iso(today) },
    { key: "last-fy", label: `FY ${fy - 1}-${String(fy).slice(2)}`, from: `${fy - 1}-04-01`, to: `${fy}-03-31` },
  ];
}

export function formatValue(value: string | number | undefined, type: ColumnType): string {
  if (value === undefined || value === "") return type === "text" || type === "date" ? "—" : "0";
  if (type === "money") return Number(value).toLocaleString("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 });
  if (type === "qty") return Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 });
  if (type === "int") return Number(value).toLocaleString("en-IN");
  if (type === "percent") return `${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 1 })}%`;
  if (type === "date") {
    const d = new Date(String(value) + "T00:00:00");
    return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  }
  return String(value);
}

/** "2026-11" → "Nov 26", "2026-11-03" → "3 Nov"; anything else unchanged. */
export function periodLabel(value: string) {
  if (/^\d{4}-\d{2}$/.test(value)) return new Date(value + "-01T00:00:00").toLocaleDateString("en-IN", { month: "short", year: "2-digit" });
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return new Date(value + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short" });
  return value;
}

/** Percentage change, or null when there is no meaningful base. */
export function change(current: string | number | undefined, previous: string | number | undefined): number | null {
  const a = Number(current ?? 0), b = Number(previous ?? 0);
  if (!b) return null;
  return ((a - b) / Math.abs(b)) * 100;
}

import { useSyncExternalStore } from "react";
import { keepPreviousData, useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api/client";

export type TxType = "sale" | "purchase" | "expense" | "payment_in" | "payment_out";
export type TxRow = {
  type: TxType; id: string; number: string; party: string; party_id: string; date: string | null; due_date: string | null;
  amount: string; balance: string | null; status: string; note?: string; mode?: string;
};
export type Dashboard = {
  as_of: string; receivable: string | null; payable: string | null; overdue_receivable: string | null; sales_month: string | null; sales_prev: string | null;
  purchases_month: string | null; trend: { month: string; sales: string | null; purchases: string | null }[];
  top_dues: { id: string; name: string; phone: string; balance: string; overdue: string }[];
  banks: { id: string; name: string; type: string; balance: string }[]; tally: { company: string; last_seen: string | null } | null;
};
export type Item = { id: string; name: string; sku: string; unit: string; hsn: string; price: string; type: "goods" | "service"; stock: string | null };
export type Doc = {
  type: "sale" | "purchase"; id: string; number: string; status: string; date: string | null; due_date: string | null;
  party: { id: string; name: string; phone: string; email: string };
  subtotal: string; tax: string; discount: string; total: string; paid: string; balance: string;
  lines: { name: string; qty: string; unit: string; rate: string; tax_rate: string; amount: string }[]; can_pay: boolean; href: string;
};

type Page<T> = { rows: T[]; page: number; more: boolean };

export function useTransactions(type: TxType, search: string, status: string) {
  return useInfiniteQuery({
    queryKey: ["phone-tx", type, search, status],
    queryFn: async ({ pageParam }) => {
      const q = new URLSearchParams({ type, page: String(pageParam) });
      if (search) q.set("search", search);
      if (status) q.set("status", status);
      return (await apiRequest<Page<TxRow>>(`/business/mobile/transactions/?${q}`)).data;
    },
    initialPageParam: 0,
    getNextPageParam: (last) => (last.more ? last.page + 1 : undefined),
    placeholderData: keepPreviousData,
    staleTime: 15_000,
  });
}

export function useItems(search: string, type: string) {
  return useInfiniteQuery({
    queryKey: ["phone-items", search, type],
    queryFn: async ({ pageParam }) => {
      const q = new URLSearchParams({ page: String(pageParam) });
      if (search) q.set("search", search);
      if (type) q.set("type", type);
      return (await apiRequest<Page<Item>>(`/business/mobile/items/?${q}`)).data;
    },
    initialPageParam: 0,
    getNextPageParam: (last) => (last.more ? last.page + 1 : undefined),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export const useDashboard = () => useQuery({ queryKey: ["phone-dashboard"], queryFn: async () => (await apiRequest<Dashboard>("/business/mobile/dashboard/")).data, staleTime: 30_000 });
export const useDocument = (type: string, id: string | null) =>
  useQuery({ queryKey: ["phone-doc", type, id], queryFn: async () => (await apiRequest<Doc>(`/business/mobile/document/?type=${type}&id=${id}`)).data, enabled: !!id });

export const inr = (v: string | number | null | undefined) =>
  v === null || v === undefined || v === "" ? "—" : new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: Number(v) % 1 ? 2 : 0 }).format(Number(v));

export const day = (s: string | null | undefined) => (s ? new Date(s.length === 10 ? s + "T00:00:00" : s).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : "");

const PHONE = "(max-width: 767px)";
const media = () => (typeof window !== "undefined" && typeof window.matchMedia === "function" ? window.matchMedia(PHONE) : null);
const subscribe = (cb: () => void) => {
  const m = media();
  if (!m) return () => {};
  m.addEventListener("change", cb);
  return () => m.removeEventListener("change", cb);
};
/** True on phone-sized screens (and in the Android app). False during server rendering. */
export function usePhone() {
  return useSyncExternalStore(subscribe, () => media()?.matches ?? false, () => false);
}

export const STATUS_LABEL: Record<string, string> = {
  ISSUED: "Unpaid", PARTIALLY_PAID: "Partly paid", PAID: "Paid", DRAFT: "Draft", CANCELLED: "Cancelled", POSTED: "Unpaid",
};

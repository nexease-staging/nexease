import { useMemo, useSyncExternalStore } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api/client";

export type FeedRow = {
  type: "sale" | "purchase" | "payment_in" | "payment_out" | "expense";
  id: string;
  number: string;
  party: string;
  date: string | null;
  amount: string;
  balance: string | null;
  status: string;
  href: string;
};

export type MobileHome = {
  as_of: string;
  receivable: string | null;
  payable: string | null;
  sales_today: string | null;
  sales_month: string | null;
  purchases_month: string | null;
  money_in_month: string | null;
  money_out_month: string | null;
  transactions: FeedRow[];
};

export type Party = { id: string; name: string; code: string; phone: string; email: string; gstin: string; city: string; balance: string | null; overdue: string | null };
export type PartyList = { side: "customers" | "suppliers"; parties: Party[]; count: number; total_balance: string | null; with_balance: number };

/**
 * Offline support: the last good copy of each phone screen is kept on the device, so the app
 * still shows balances and recent activity without a connection (marked as saved data).
 */
const CACHE = "nexease:mobile-cache:";
type Saved<T> = { at: number; data: T };

export function readSaved<T>(key: string): Saved<T> | null {
  try {
    const raw = localStorage.getItem(CACHE + key);
    return raw ? (JSON.parse(raw) as Saved<T>) : null;
  } catch {
    return null;
  }
}

function save<T>(key: string, data: T) {
  try {
    localStorage.setItem(CACHE + key, JSON.stringify({ at: Date.now(), data }));
  } catch {
    /* storage full or unavailable; the live data still shows */
  }
}

async function cached<T>(key: string, path: string) {
  const data = (await apiRequest<T>(path)).data;
  save(key, data);
  return data;
}

export function useMobileHome() {
  return useQuery({ queryKey: ["mobile-home"], queryFn: () => cached<MobileHome>("home", "/business/mobile/home/"), staleTime: 15_000 });
}

export function useParties(side: "customers" | "suppliers", search: string) {
  const key = `parties:${side}`;
  return useQuery({
    queryKey: ["mobile-parties", side, search],
    queryFn: () => (search ? apiRequest<PartyList>(`/business/mobile/parties/?side=${side}&search=${encodeURIComponent(search)}`).then((r) => r.data) : cached<PartyList>(key, `/business/mobile/parties/?side=${side}`)),
    staleTime: 15_000,
  });
}

export const rupees = (value: string | number | null | undefined, hidden = false) => {
  if (hidden) return "₹ ••••";
  if (value === null || value === undefined || value === "") return "—";
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: Number(value) % 1 ? 2 : 0 }).format(Number(value));
};

export const savedAt = (at: number) => new Date(at).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });

const noop = () => () => {};
/** Saved copy for a screen; null during server rendering so hydration stays consistent. */
export function useSaved<T>(key: string): Saved<T> | null {
  const raw = useSyncExternalStore(noop, () => { try { return localStorage.getItem(CACHE + key); } catch { return null; } }, () => null);
  return useMemo(() => { try { return raw ? (JSON.parse(raw) as Saved<T>) : null; } catch { return null; } }, [raw]);
}

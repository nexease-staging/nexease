import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api/client";

export type Side = "receivable" | "payable";
export type Direction = "all" | "in" | "out";
export type Bucket = "current" | "d1_30" | "d31_60" | "d61_90" | "d90_plus";
export const BUCKETS: Array<{ key: Bucket; label: string }> = [
  { key: "current", label: "Not due" },
  { key: "d1_30", label: "1–30 days" },
  { key: "d31_60", label: "31–60 days" },
  { key: "d61_90", label: "61–90 days" },
  { key: "d90_plus", label: "90+ days" },
];
export const METHODS = [
  { value: "UPI", label: "UPI" },
  { value: "CASH", label: "Cash" },
  { value: "BANK_TRANSFER", label: "Bank transfer" },
  { value: "CHEQUE", label: "Cheque" },
  { value: "CARD", label: "Card" },
  { value: "OTHER", label: "Other" },
] as const;
export const methodLabel = (value: string) => METHODS.find((m) => m.value === value)?.label ?? value;

export interface PartySummary {
  id: string;
  name: string;
  code: string;
  phone: string;
  email: string;
  open_count: number;
  outstanding: string;
  overdue: string;
  buckets: Record<Bucket, string>;
  oldest_due: string | null;
  max_days_overdue: number;
}

export interface OutstandingSummary {
  side: Side;
  as_of: string;
  totals: { outstanding: string; overdue: string; buckets: Record<Bucket, string> };
  party_count: number;
  document_count: number;
  truncated: boolean;
  parties: PartySummary[];
}

export interface OpenDocument {
  id: string;
  party_id: string;
  number: string;
  date: string | null;
  due_date: string | null;
  days_overdue: number;
  bucket: Bucket;
  total: string;
  outstanding: string;
  status: string;
}

export interface PartyOutstanding {
  side: Side;
  party: { id: string; name: string; code: string; phone: string; email: string };
  documents: OpenDocument[];
  total: string;
}

export interface RegisterPayment {
  id: string;
  direction: "in" | "out";
  number: string;
  date: string | null;
  party: { id: string; name: string; code: string; phone: string; email: string };
  amount: string;
  method: string;
  account: { id: string; name: string };
  reference: string;
  notes: string;
  documents: Array<{ id: string; number: string; amount: string }>;
}

export interface RegisterData {
  summary: { money_in: string; money_out: string; net: string; count: number; by_method: Record<string, { in: string; out: string }> };
  payments: RegisterPayment[];
  pagination: { page: number; page_size: number; total: number; pages: number };
}

export interface RegisterParams {
  direction: Direction;
  page: number;
  page_size?: number;
  search?: string;
  method?: string;
  from?: string;
  to?: string;
  party_id?: string;
}

export interface SettleInput {
  side: Side;
  party_id: string;
  amount: string;
  payment_method: string;
  bank_account_id: string;
  payment_date?: string;
  reference_number?: string;
  notes?: string;
  allocations: Array<{ document_id: string; amount: string }>;
  request_key: string;
}

export interface SettleResult {
  party: { id: string; name: string };
  amount: string;
  payments: Array<{ document_id: string; number: string; amount: string; payment_id: string; payment_number: string }>;
}

function query(params: object) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) if (value !== undefined && value !== "" && value !== null) search.set(key, String(value));
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const paymentKeys = {
  all: ["payments-hub"] as const,
  outstanding: (side: Side) => ["payments-hub", "outstanding", side] as const,
  party: (side: Side, id: string) => ["payments-hub", "party", side, id] as const,
  register: (params: RegisterParams) => ["payments-hub", "register", params] as const,
};

export function useOutstanding(side: Side, enabled = true) {
  return useQuery({
    queryKey: paymentKeys.outstanding(side),
    queryFn: async () => (await apiRequest<OutstandingSummary>(`/business/payments/outstanding/${query({ side })}`)).data,
    enabled,
    staleTime: 30_000,
  });
}

export function usePartyOutstanding(side: Side, partyId: string | null | undefined) {
  return useQuery({
    queryKey: paymentKeys.party(side, partyId ?? ""),
    queryFn: async () => (await apiRequest<PartyOutstanding>(`/business/payments/outstanding/${query({ side, party_id: partyId })}`)).data,
    enabled: Boolean(partyId),
    staleTime: 10_000,
  });
}

export function usePaymentRegister(params: RegisterParams, enabled = true) {
  return useQuery({
    queryKey: paymentKeys.register(params),
    queryFn: async () => (await apiRequest<RegisterData>(`/business/payments/register/${query({ page_size: 25, ...params })}`)).data,
    enabled,
    placeholderData: keepPreviousData,
    staleTime: 15_000,
  });
}

export function useSettle() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async ({ side, ...body }: SettleInput) => {
      const response = await apiRequest<SettleResult>(`/business/payments/${side === "receivable" ? "receive" : "pay"}/`, { method: "POST", body });
      return { ...response.data, message: response.message };
    },
    // Partial failures still recorded money, so refresh after every attempt.
    onSettled: () => client.invalidateQueries(),
  });
}

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api/client";

export type Device = { id: string; name: string; last_seen: string | null; online: boolean; info: Record<string, string> };
export type Company = {
  id: string; name: string; enabled: boolean; open: boolean; gstin: string; state: string; books_from: string; progress: number;
  masters_synced: boolean; counts: Partial<Record<"ledger" | "stockitem" | "voucher", number>>; seen_at: string | null;
};
export type Status = {
  connected: boolean; online: boolean; tally_ok: boolean; devices: Device[]; companies: Company[]; pending: number; failed: number; issues: number;
  pushed: number; paused: boolean; last_sync: string | null; tally_error: string; download_url: string; can_manage: boolean; interval: number;
};
export type Voucher = { guid: string; date: string; type: string; base: string; number: string; party: string; amount: number; narration: string; reference: string; from_nexease: boolean; cancelled: boolean };
export type Kpi = { value: number; previous: number };
export type Overview = {
  connected: boolean; company: string; kpis: Record<"sales" | "purchase" | "receipts" | "payments", Kpi>; receivable: number; payable: number; cash: number; bank: number;
  stock_value: number; cash_bank: { name: string; balance: number; group: string }[]; trend: { month: string; sales: number; purchase: number; receipts: number; payments: number }[];
  top_debtors: PartyLite[]; top_creditors: PartyLite[]; recent: Voucher[];
};
export type PartyLite = { guid: string; name: string; balance: number; phone: string };
export type Party = PartyLite & { group: string; parent: string; gstin: string; email: string; state: string; credit_days: string; nexease_id: string | null; nexease_model: string | null };
export type Statement = {
  guid: string; name: string; group: string; parent: string; gstin: string; phone: string; email: string; address: string; state: string; credit_days: string;
  closing: number; opening: number; from: string; to: string; rows: (Voucher & { debit: number; credit: number; balance: number; particulars: string })[];
  bills: { name: string; date: string; due: string; overdue_days: number; amount: number }[];
};
export type StockItem = { guid: string; name: string; group: string; unit: string; hsn: string; gst_rate: string; qty: number; rate: number; value: number; price: number };
export type VoucherDetail = Voucher & { party_gstin: string; place_of_supply: string; entries: { ledger: string; debit: number; credit: number }[];
  inventory: { item: string; qty: string; unit: string; rate: string; amount: string }[]; bills: { ledger: string; name: string; type: string; amount: string }[]; deleted: boolean };
export type Register = { type: string; from: string; to: string; vouchers: Voucher[]; count: number; total: number; months: { month: string; amount: number }[]; ledgers: { ledger: string; amount: number }[] };
export type TrialBalance = { groups: { code: string; label: string; debit: number; credit: number; ledgers: { guid: string; name: string; debit: number; credit: number }[] }[]; debit: number; credit: number; difference: number };
export type SyncSettings = {
  write_back: Record<string, boolean>; mapping: Record<string, string>; bank_ledgers: Record<string, string>; expense_ledgers: Record<string, string>;
  journal_accounts?: Record<string, string>; voucher_types: Record<string, string>; import_masters: boolean; invoice_mode: "auto" | "item" | "accounting";
  debtors_group: string; creditors_group: string; paused?: boolean; interval?: number; push_from: string;
};
export type SettingsData = {
  settings: SyncSettings; write_kinds: string[]; mapping_keys: string[];
  options: { ledgers: string[]; by_group: Record<string, string[]>; bank_accounts: { id: string; name: string; type: string }[]; accounts: { id: string; name: string; code: string }[];
    expense_categories: string[]; voucher_types: string[]; suggested: Record<string, string> };
};
export type Job = { id: string; type: string; kind: string; label: string; status: string; attempts: number; error: string; created_at: string; done_at: string | null; result: Record<string, string | number> };
export type Issue = { model: string; id: string; label: string; state: string; error: string; updated_at: string };

const qs = (p: Record<string, string | undefined>) => new URLSearchParams(Object.entries(p).filter(([, v]) => v) as [string, string][]).toString();
const get = async <T,>(path: string) => (await apiRequest<T>(`/business/tally/${path}`)).data;
export const tallyKeys = { all: ["tally"] as const };

export const useStatus = () => useQuery({ queryKey: ["tally", "status"], queryFn: () => get<Status>("status/"), refetchInterval: 15_000 });
export const useOverview = (enabled: boolean) => useQuery({ queryKey: ["tally", "overview"], queryFn: () => get<Overview>("overview/"), enabled, refetchInterval: 60_000 });
export const useParties = (side: string, q: string) =>
  useQuery({ queryKey: ["tally", "parties", side, q], queryFn: () => get<{ parties: Party[]; total: number; count: number }>(`parties/?${qs({ side, q })}`), placeholderData: keepPreviousData });
export const useStatement = (guid: string | null, from: string, to: string) =>
  useQuery({ queryKey: ["tally", "statement", guid, from, to], queryFn: () => get<Statement>(`parties/${guid}/?${qs({ from, to })}`), enabled: !!guid });
export const useStock = (q: string) => useQuery({ queryKey: ["tally", "stock", q], queryFn: () => get<{ items: StockItem[]; count: number; value: number; negative: number }>(`stock/?${qs({ q })}`), placeholderData: keepPreviousData });
export const useDaybook = (from: string, to: string, type: string, q: string) =>
  useQuery({ queryKey: ["tally", "daybook", from, to, type, q], queryFn: () => get<{ vouchers: Voucher[]; by_type: Record<string, number>; types: string[] }>(`daybook/?${qs({ from, to, type, q })}`), placeholderData: keepPreviousData });
export const useVoucher = (guid: string | null) => useQuery({ queryKey: ["tally", "voucher", guid], queryFn: () => get<VoucherDetail>(`vouchers/${guid}/`), enabled: !!guid });
export const useRegister = (type: string, from: string, to: string) =>
  useQuery({ queryKey: ["tally", "register", type, from, to], queryFn: () => get<Register>(`registers/?${qs({ type, from, to })}`), placeholderData: keepPreviousData });
export const useTrialBalance = () => useQuery({ queryKey: ["tally", "tb"], queryFn: () => get<TrialBalance>("trial-balance/") });
export const useSettings = () => useQuery({ queryKey: ["tally", "settings"], queryFn: () => get<SettingsData>("settings/") });
export const useJobs = (status: string) => useQuery({ queryKey: ["tally", "jobs", status], queryFn: () => get<{ jobs: Job[] }>(`jobs/?${qs({ status })}`), refetchInterval: 15_000 });
export const useIssues = () => useQuery({ queryKey: ["tally", "issues"], queryFn: () => get<{ issues: Issue[] }>("issues/") });

function useAction<B>(path: (b: B) => string, body: (b: B) => unknown = (b) => b) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (b: B) => (await apiRequest<Record<string, unknown>>(`/business/tally/${path(b)}`, { method: "POST", body: body(b) })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: tallyKeys.all }),
  });
}

export const usePair = () => useAction<void>(() => "pair/", () => ({}));
export const useRevoke = () => useAction<string>((id) => `devices/${id}/revoke/`, () => ({}));
export const useCompany = () => useAction<{ id: string; enabled: boolean }>((b) => `companies/${encodeURIComponent(b.id)}/`, (b) => ({ enabled: b.enabled }));
export const useSaveSettings = () => useAction<Partial<SyncSettings>>(() => "settings/");
export const useResync = () => useAction<"all" | "masters" | "vouchers">(() => "resync/", (scope) => ({ scope }));
export const useRetryJob = () => useAction<string>((id) => `jobs/${id}/retry/`, () => ({}));
export const useRetryIssues = () => useAction<string | undefined>(() => "issues/retry/", (id) => (id ? { id } : {}));

export const exportPath = (path: string, params: Record<string, string | undefined> = {}) => `/business/tally/${path}?${qs({ ...params, export: "xlsx" })}`;

export const inr = (v: number | string | null | undefined, digits = 0) =>
  v === null || v === undefined || v === "" ? "—" : new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: digits, minimumFractionDigits: digits }).format(Number(v));

export const WRITE_LABELS: Record<string, string> = {
  customers: "Customers → ledgers", suppliers: "Suppliers → ledgers", products: "Products → stock items", invoices: "Sales invoices → Sales", bills: "Purchase bills → Purchase",
  receipts: "Customer payments → Receipt", payments: "Supplier payments → Payment", credit_notes: "Credit notes", debit_notes: "Debit notes", sales_orders: "Sales orders",
  purchase_orders: "Purchase orders", expenses: "Expenses → Payment", journals: "Manual journals → Journal",
};
export const MAPPING_LABELS: Record<string, { label: string; groups: string[] }> = {
  sales: { label: "Sales", groups: ["sales"] }, purchase: { label: "Purchase", groups: ["purchase"] },
  service_income: { label: "Service income (optional)", groups: ["sales", "direct_income", "indirect_income"] },
  cgst_out: { label: "CGST output", groups: ["tax"] }, sgst_out: { label: "SGST output", groups: ["tax"] }, igst_out: { label: "IGST output", groups: ["tax"] },
  cgst_in: { label: "CGST input", groups: ["tax"] }, sgst_in: { label: "SGST input", groups: ["tax"] }, igst_in: { label: "IGST input", groups: ["tax"] },
  round_off: { label: "Round off", groups: ["indirect_expense", "indirect_income"] }, cash: { label: "Cash", groups: ["cash"] }, bank: { label: "Bank (default)", groups: ["bank"] },
  expense_default: { label: "Expenses (default)", groups: ["indirect_expense", "direct_expense"] },
};

export function ago(iso: string | null) {
  if (!iso) return "never";
  const s = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.round(s / 60)} min ago`;
  if (s < 86400) return `${Math.round(s / 3600)} h ago`;
  return `${Math.round(s / 86400)} d ago`;
}

export const today = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
export const fyStart = () => { const d = new Date(); return `${d.getMonth() >= 3 ? d.getFullYear() : d.getFullYear() - 1}-04-01`; };
export const monthStart = () => today().slice(0, 8) + "01";

export function whatsappLink(phone: string, name: string, amount: number, company: string) {
  const digits = phone.replace(/\D/g, "");
  const number = digits.length === 10 ? "91" + digits : digits;
  const text = `Dear ${name}, a balance of ${inr(amount)} is due to ${company}. Please arrange the payment at the earliest. Thank you.`;
  return `https://wa.me/${number}?text=${encodeURIComponent(text)}`;
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api/client";

export type ImsAction = "accept" | "reject" | "pending" | "none";
export type MatchStatus = "matched" | "date_mismatch" | "mismatch" | "only_in_2b" | "note";
type Heads = { taxable: string; igst: string; cgst: string; sgst: string; cess: string };
type Tax4 = { igst: string; cgst: string; sgst: string; cess: string };

export type InwardRecord = Heads & {
  id: string;
  period: string;
  source: string;
  supplier_gstin: string;
  supplier_name: string;
  doc_type: "INV" | "CN" | "DN";
  doc_number: string;
  doc_date: string;
  pos: string;
  rcm: boolean;
  total_tax: string;
  value: string;
  itc_available: boolean;
  portal_action: string;
  action: ImsAction;
  reason: string;
  itc_reduce: string;
  match: { status: MatchStatus; differences: { field: string; portal: string; books: string; difference: string }[]; bill: { id: string; number: string; supplier_invoice: string; date: string; taxable: string; total_tax: string } | null };
  suggested: ImsAction;
  suggestion: string;
};

export type MissingBill = { id: string; number: string; bill_number: string; supplier_gstin: string; supplier_name: string; date: string; taxable: string; total_tax: string };
export type ImsList = { period: string; records: InwardRecord[]; count: number; missing_in_2b: MissingBill[] };
export type Deadline = { key: string; label: string; date: string; note: string };
export type Registration = { gstin: string; state_code: string; legal_name: string; registration: string; frequency: string; configured: boolean };
export type ReturnRow = Heads & { table?: string; row?: string; label: string; count?: number };

export type Overview = {
  period: string;
  registration: Registration;
  deadlines: Deadline[];
  ims: Record<ImsAction, number>;
  reconciliation: Partial<Record<MatchStatus, number>>;
  missing_in_2b: number;
  gstr1: { tables: ReturnRow[]; documents: { from: string; to: string; issued: number; cancelled: number } };
  gstr3b: { liability: Tax4; itc: Tax4; cash: Tax4 };
  alerts: { tone: "danger" | "warn" | "info"; text: string; href: string }[];
};

export type Gstr1 = {
  period: string; from: string; to: string; tables: ReturnRow[];
  b2cs: (Heads & { pos: string; state: string; rate: string; count: number })[];
  hsn: { section: string; hsn: string; rate: string; quantity: string; taxable: string; tax: string }[];
  documents: { from: string; to: string; issued: number; cancelled: number };
  review: { id: string; number: string; reason: string }[];
  review_count: number;
};

export type Gstr3b = {
  period: string; periods: string[]; from: string; to: string;
  table_3_1: ReturnRow[];
  table_3_2: { pos: string; state: string; taxable: string; igst: string }[];
  table_4: { a5_all_other_itc: Tax4; a3_reverse_charge: Tax4; b2_rule37_reversal: Tax4; net: Tax4; books: Omit<Tax4, "cess"> };
  rule37_bills: { id: string; number: string; supplier: string; date: string; balance: string; itc: string }[];
  ims_counts: Record<ImsAction, number>;
  payment: { cash: Tax4; carry_forward: Tax4; utilised: { credit: string; against: string; amount: string }[] };
  liability: Tax4;
  review_count: number;
  notes: string[];
};

export const gstKeys = {
  overview: (p: string) => ["gst", "overview", p] as const,
  ims: (p: string) => ["gst", "ims", p] as const,
  ret: (form: string, p: string) => ["gst", "return", form, p] as const,
};

export const useOverview = (period: string) => useQuery({ queryKey: gstKeys.overview(period), queryFn: async () => (await apiRequest<Overview>(`/business/gst/overview/?period=${period}`)).data });
export const useIms = (period: string) => useQuery({ queryKey: gstKeys.ims(period), queryFn: async () => (await apiRequest<ImsList>(`/business/gst/ims/?period=${period}`)).data });
export const useGstr1 = (period: string) => useQuery({ queryKey: gstKeys.ret("gstr1", period), queryFn: async () => (await apiRequest<Gstr1>(`/business/gst/returns/gstr1/?period=${period}`)).data });
export const useGstr3b = (period: string) => useQuery({ queryKey: gstKeys.ret("gstr3b", period), queryFn: async () => (await apiRequest<Gstr3b>(`/business/gst/returns/gstr3b/?period=${period}`)).data });

export function useImsAction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { ids: string[]; action: ImsAction; reason?: string; itc_reduce?: string }) => (await apiRequest<{ updated: number; skipped: string[] }>("/business/gst/ims/action/", { method: "POST", body })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["gst"] }),
  });
}

export function useImport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, period }: { file: File; period: string }) => {
      const form = new FormData();
      form.append("file", file);
      form.append("period", period);
      return (await apiRequest<{ period: string; added: number; updated: number }>("/business/gst/ims/", { method: "POST", body: form })).data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["gst"] }),
  });
}

export function useLinkBill() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { record_id: string; bill_id: string }) => (await apiRequest("/business/gst/ims/link/", { method: "POST", body })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["gst"] }),
  });
}

export const inr = (v: string | number | undefined | null) => (v === undefined || v === null || v === "" ? "—" : new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(v)));
export const taxOf = (h: { igst: string; cgst: string; sgst: string; cess?: string }) => Number(h.igst) + Number(h.cgst) + Number(h.sgst) + Number(h.cess ?? 0);

/** The default period is last month: that is the return you are usually preparing. */
export function lastMonth(now = new Date()) {
  const d = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export const periodLabel = (p: string) => new Date(Number(p.slice(0, 4)), Number(p.slice(5, 7)) - 1, 1).toLocaleDateString("en-IN", { month: "long", year: "numeric" });

export const ACTION_LABEL: Record<ImsAction, string> = { accept: "Accepted", reject: "Rejected", pending: "Pending", none: "No action" };
export const MATCH_LABEL: Record<MatchStatus, string> = { matched: "Matches books", date_mismatch: "Date differs", mismatch: "Amount differs", only_in_2b: "Not in books", note: "Credit / debit note" };

/** A CSV the user can follow on the GST portal to mirror the decisions taken here. */
export function portalChecklist(rows: InwardRecord[]) {
  const head = ["Supplier GSTIN", "Supplier", "Type", "Number", "Date", "Taxable", "Total tax", "Action to take on portal", "Reason", "ITC to reduce"];
  const esc = (v: string) => (/[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v);
  const body = rows.filter((r) => r.action !== "none" && !r.rcm).map((r) => [r.supplier_gstin, r.supplier_name, r.doc_type, r.doc_number, r.doc_date, r.taxable, r.total_tax, ACTION_LABEL[r.action], r.reason, r.itc_reduce].map((v) => esc(String(v ?? ""))).join(","));
  return [head.join(","), ...body].join("\n");
}

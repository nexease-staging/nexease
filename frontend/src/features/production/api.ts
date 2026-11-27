import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api/client";

export type Stage = { key: string; label: string };
export type Party = { id: string; name: string; phone?: string } | null;
export type JobRow = {
  id: string; number: string; title: string; customer: Party; product: { id: string; name: string; sku: string; unit: string } | null;
  quantity: string; unit: string; made_to_order: boolean; status: JobStatus; stage: string; stage_label: string; stage_index: number; progress: number;
  priority: Priority; assignees: string[]; due: string | null; days_left: number | null; overdue: boolean; quoted: string; cost: string; margin: string;
  margin_pct: string | null; invoice: { id: string; number: string; total: string } | null; sales_order: { id: string; number: string } | null; revision: number;
  updated_at: string | null;
};
export type JobStatus = "open" | "on_hold" | "completed" | "delivered" | "cancelled";
export type Priority = "low" | "normal" | "high" | "urgent";
export type JobMaterial = { product: string; name: string; unit: string; planned: string; issued: string; pending: string; value: string; rate: string; available: string };
export type Labour = { id: string; date: string; worker: string; hours: string; rate: string; amount: string; note: string };
export type Expense = { id: string; date: string; kind: string; label: string; amount: string; note: string };
export type JobEvent = { at: string; kind: string; text: string; by: string };
export type Costs = { material: string; labour: string; expenses: string; total: string; planned_material: string; quoted: string; margin: string; margin_pct: string | null; unit_cost: string | null };
export type Job = JobRow & {
  stages: Stage[]; warehouse: { id: string; name: string }; specification: string; materials: JobMaterial[]; labour: Labour[]; expenses: Expense[];
  costs: Costs; completed_quantity: string; finished_to_stock: boolean; events: JobEvent[]; created_at: string | null; completed_at: string | null;
  expense_kinds: Record<string, string>;
};
export type Summary = {
  active: number; on_hold: number; overdue: number; due_week: number; wip_value: string; completed_30d: number; margin_30d: string; margin_pct_30d: string | null;
  to_invoice: number; by_stage: (Stage & { count: number })[];
};
export type Board = { rows: JobRow[]; count: number; summary: Summary; stages: Stage[]; priorities: Priority[] };
export type RecipeMaterial = { product: string; name: string; unit: string; per_unit: string; rate: string; on_hand: string; active: boolean };
export type Recipe = {
  product: string; name: string; sku: string; unit: string; selling_price: string; made_to_order: boolean; materials: RecipeMaterial[];
  labour_per_unit: string; material_cost: string; unit_cost: string; can_make: number | null; notes: string; updated_at: string | null;
};
export type Filters = { status: string; stage: string; search: string; priority: string; overdue: boolean };

const qs = (p: Record<string, string | undefined>) => new URLSearchParams(Object.entries(p).filter(([, v]) => v) as [string, string][]).toString();
const root = "/business/jobs/";

export const useBoard = (f: Filters) =>
  useQuery({
    queryKey: ["production", "board", f],
    queryFn: async () => (await apiRequest<Board>(`${root}?${qs({ status: f.status, stage: f.stage, search: f.search, priority: f.priority, overdue: f.overdue ? "1" : "" })}`)).data,
    placeholderData: keepPreviousData,
    refetchInterval: 30_000,
  });

export const useJob = (id: string | null) =>
  useQuery({ queryKey: ["production", "job", id], enabled: !!id, queryFn: async () => (await apiRequest<Job>(`${root}${id}/`)).data });

export function useJobAction(id: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: Record<string, unknown>) => (await apiRequest<Job>(`${root}${id}/`, { method: "POST", body })).data,
    onSuccess: (job) => {
      qc.setQueryData(["production", "job", job.id], job);
      void qc.invalidateQueries({ queryKey: ["production", "board"] });
    },
    onError: () => void qc.invalidateQueries({ queryKey: ["production", "job", id] }),
  });
}

export function useCreateJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: Record<string, unknown>) => (await apiRequest<Job>(root, { method: "POST", body })).data,
    onSuccess: (job) => {
      qc.setQueryData(["production", "job", job.id], job);
      void qc.invalidateQueries({ queryKey: ["production", "board"] });
    },
  });
}

export function useInvoiceJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ job, unit_price, tax_rate, invoice_date }: { job: Job; unit_price: string; tax_rate: string; invoice_date: string }) =>
      (await apiRequest<{ id: string; invoice_number: string }>("/business/direct-invoices/", {
        method: "POST",
        body: {
          job_id: job.id, invoice_date, warehouse_id: job.warehouse.id,
          customer: { id: job.customer?.id, name: job.customer?.name },
          items: [{ sku: job.product?.sku, name: job.product?.name ?? job.title, unit: job.unit || "PCS", quantity: job.quantity, unit_price, tax_rate }],
        },
      })).data,
    onSuccess: (_, v) => {
      void qc.invalidateQueries({ queryKey: ["production", "job", v.job.id] });
      void qc.invalidateQueries({ queryKey: ["production", "board"] });
    },
  });
}

export const useStageSettings = () =>
  useQuery({ queryKey: ["production", "settings"], queryFn: async () => (await apiRequest<{ stages: Stage[] }>(`${root}settings/`)).data });

export function useSaveStages() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (stages: Stage[]) => (await apiRequest<{ stages: Stage[] }>(`${root}settings/`, { method: "POST", body: { stages } })).data,
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["production"] }),
  });
}

export const useRecipes = (search: string) =>
  useQuery({ queryKey: ["production", "recipes", search], placeholderData: keepPreviousData,
    queryFn: async () => (await apiRequest<{ rows: Recipe[]; count: number }>(`/business/recipes/?${qs({ search })}`)).data });

export const useRecipe = (product: string | null) =>
  useQuery({ queryKey: ["production", "recipe", product], enabled: !!product, queryFn: async () => (await apiRequest<Recipe>(`/business/recipes/${product}/`)).data });

export function useSaveRecipe() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ product, ...body }: { product: string; made_to_order: boolean; materials: { product: string; per_unit: string }[]; labour_per_unit: string; notes: string }) =>
      (await apiRequest<Recipe>(`/business/recipes/${product}/`, { method: "POST", body })).data,
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["production"] }),
  });
}

export function useDeleteRecipe() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (product: string) => (await apiRequest<{ deleted: boolean }>(`/business/recipes/${product}/`, { method: "DELETE" })).data,
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["production"] }),
  });
}

export const useWarehouses = (enabled: boolean) =>
  useQuery({ queryKey: ["production", "warehouses"], enabled, staleTime: 300_000,
    queryFn: async () => (await apiRequest<{ warehouses: { id: string; name: string; code?: string }[] }>("/warehouses/?page_size=100")).data.warehouses ?? [] });

export const inr = (v: string | number | null | undefined, digits = 0) =>
  Number(v ?? 0).toLocaleString("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: digits, minimumFractionDigits: digits });
export const qty = (v: string | number) => Number(v).toLocaleString("en-IN", { maximumFractionDigits: 3 });
export const today = () => new Date().toISOString().slice(0, 10);

export function dueText(row: Pick<JobRow, "due" | "days_left" | "status">) {
  if (!row.due || row.days_left === null) return "No due date";
  if (row.status === "completed" || row.status === "delivered") return `Due ${new Date(row.due).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}`;
  const d = row.days_left;
  if (d < 0) return `${-d} day${d === -1 ? "" : "s"} late`;
  if (d === 0) return "Due today";
  if (d === 1) return "Due tomorrow";
  return `Due in ${d} days`;
}

export const STATUS_LABEL: Record<JobStatus, string> = { open: "In progress", on_hold: "On hold", completed: "Completed", delivered: "Delivered", cancelled: "Cancelled" };
export const PRIORITY_LABEL: Record<Priority, string> = { low: "Low", normal: "Normal", high: "High", urgent: "Urgent" };

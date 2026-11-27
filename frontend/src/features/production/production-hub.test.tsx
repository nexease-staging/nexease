import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import ProductionHub from "./production-hub";
import { dueText, type Board, type Job, type JobRow } from "./api";

const { api, params, replace, perms } = vi.hoisted(() => ({
  api: vi.fn(), params: { value: "" }, replace: vi.fn(),
  perms: { value: ["manufacturing.read", "manufacturing.manage", "inventory.adjust", "invoices.create"] },
}));
vi.mock("@/lib/api/client", () => ({ apiRequest: api }));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: (url: string) => { replace(url); params.value = url.split("?")[1] ?? ""; }, push: vi.fn() }),
  usePathname: () => "/manufacturing",
  useSearchParams: () => new URLSearchParams(params.value),
}));
vi.mock("@/features/auth/auth-context", () => ({ useAuth: () => ({ authentication: { role: { permissions: perms.value } } }) }));
vi.mock("@/features/business/barcode-scan", () => ({ default: () => null }));

const stages = [{ key: "design", label: "Design & measurement" }, { key: "cutting", label: "Cutting" }, { key: "ready", label: "Ready for delivery" }];
const row: JobRow = {
  id: "j1", number: "JOB-0007", title: "Steel almirah", customer: { id: "c1", name: "Patil Builders", phone: "9876543210" },
  product: { id: "p1", name: "Steel almirah", sku: "ALM", unit: "PCS" }, quantity: "2", unit: "PCS", made_to_order: true, status: "open", stage: "cutting",
  stage_label: "Cutting", stage_index: 1, progress: 33, priority: "urgent", assignees: ["Raju", "Imran"], due: "2026-11-25", days_left: -2, overdue: true,
  quoted: "50000.00", cost: "15540.00", margin: "34460.00", margin_pct: "68.9", invoice: null, sales_order: null, revision: 4, updated_at: null,
};
const board: Board = {
  rows: [row, { ...row, id: "j2", number: "JOB-0008", title: "Shop counter", stage: "design", stage_index: 0, overdue: false, days_left: 6, due: "2026-12-03", priority: "normal" }],
  count: 2, stages, priorities: ["low", "normal", "high", "urgent"],
  summary: { active: 2, on_hold: 0, overdue: 1, due_week: 1, wip_value: "15540.00", completed_30d: 3, margin_30d: "41000.00", margin_pct_30d: "32.5", to_invoice: 1,
    by_stage: [{ ...stages[0], count: 1 }, { ...stages[1], count: 1 }, { ...stages[2], count: 0 }] },
};
const job: Job = {
  ...row, stages, warehouse: { id: "w1", name: "Main godown" }, specification: "6 ft, mirror door",
  materials: [{ product: "m1", name: "Plywood 18mm", unit: "SHEET", planned: "8", issued: "7", pending: "1", value: "8400.00", rate: "1200.00", available: "0" }],
  labour: [{ id: "l1", date: "2026-11-26", worker: "Raju", hours: "8", rate: "400.00", amount: "3200.00", note: "" }],
  expenses: [{ id: "e1", date: "2026-11-26", kind: "transport", label: "Transport", amount: "800.00", note: "Tempo" }],
  costs: { material: "9040.00", labour: "3200.00", expenses: "800.00", total: "13040.00", planned_material: "10240.00", quoted: "50000.00", margin: "36960.00", margin_pct: "73.9", unit_cost: "6520.00" },
  completed_quantity: "0", finished_to_stock: false, events: [{ at: "2026-11-26T10:00:00Z", kind: "stage", text: "Moved to Cutting", by: "Ramesh S" }],
  created_at: null, completed_at: null, expense_kinds: { machine: "Machine / power", transport: "Transport", other: "Other" },
};

function setup() {
  api.mockImplementation(async (path: string, opts?: { method?: string; body?: Record<string, unknown> }) => {
    if (path.startsWith("/business/jobs/j1/")) {
      if (opts?.method === "POST") return { data: { ...job, revision: 5, stage: String(opts.body?.stage ?? job.stage), events: [{ at: "2026-11-27T10:00:00Z", kind: "note", text: "posted", by: "" }, ...job.events] } };
      return { data: job };
    }
    if (path.startsWith("/business/jobs/")) return { data: board };
    if (path.startsWith("/business/recipes/")) return { data: { rows: [{ product: "p1", name: "Steel almirah", sku: "ALM", unit: "PCS", selling_price: "25000.00", made_to_order: true, materials: [{ product: "m1", name: "Plywood 18mm", unit: "SHEET", per_unit: "4", rate: "1200.00", on_hand: "20", active: true }], labour_per_unit: "1500.00", material_cost: "4800.00", unit_cost: "6300.00", can_make: 5, notes: "", updated_at: null }], count: 1 } };
    if (path.startsWith("/business/direct-invoices/")) return { data: { id: "i1", invoice_number: "INV-0042" } };
    if (path.startsWith("/warehouses/")) return { data: { warehouses: [] } };
    return { data: {} };
  });
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><ProductionHub /></QueryClientProvider>);
}

beforeEach(() => {
  vi.clearAllMocks();
  params.value = "";
  perms.value = ["manufacturing.read", "manufacturing.manage", "inventory.adjust", "invoices.create"];
});

describe("Production hub", () => {
  it("shows the board with stage columns, KPIs and late jobs", async () => {
    setup();
    expect(await screen.findByRole("region", { name: "Cutting" })).toHaveTextContent("Steel almirah");
    expect(screen.getByRole("region", { name: "Design & measurement" })).toHaveTextContent("Shop counter");
    expect(screen.getByText("Ready to invoice")).toBeInTheDocument();
    expect(screen.getByText("2 days late")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Cutting\s*1/ }));
    await waitFor(() => expect(api).toHaveBeenCalledWith(expect.stringContaining("stage=cutting")));
  });

  it("opens a job card, moves its stage and issues material", async () => {
    params.value = "job=j1";
    setup();
    const dialog = await screen.findByRole("dialog");
    expect(await within(dialog).findByText("Plywood 18mm")).toBeInTheDocument();
    expect(within(dialog).getByText("Made to order")).toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole("button", { name: /Ready for delivery/ }));
    await waitFor(() => expect(api).toHaveBeenCalledWith("/business/jobs/j1/", expect.objectContaining({ method: "POST", body: { action: "stage", stage: "ready", revision: 4 } })));
    fireEvent.change(within(dialog).getByLabelText("Quantity of Plywood 18mm"), { target: { value: "1" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Issue Plywood 18mm" }));
    await waitFor(() => expect(api).toHaveBeenCalledWith("/business/jobs/j1/", expect.objectContaining({ body: expect.objectContaining({ action: "issue", product: "m1", quantity: "1" }) })));
  });

  it("raises an invoice for a made-to-order job", async () => {
    params.value = "job=j1";
    setup();
    const dialog = await screen.findByRole("dialog");
    fireEvent.click(await within(dialog).findByRole("button", { name: "Create invoice" }));
    fireEvent.click(await screen.findByRole("button", { name: "Create draft invoice" }));
    expect(await screen.findByText("INV-0042")).toBeInTheDocument();
    expect(api).toHaveBeenCalledWith("/business/direct-invoices/", expect.objectContaining({
      body: expect.objectContaining({ job_id: "j1", items: [expect.objectContaining({ sku: "ALM", quantity: "2", unit_price: "25000.00" })] }),
    }));
  });

  it("hides changes for read-only users and lists recipes", async () => {
    perms.value = ["manufacturing.read"];
    params.value = "tab=recipes";
    setup();
    expect(await screen.findByText("Steel almirah")).toBeInTheDocument();
    expect(screen.getByText("Can make now")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /New recipe/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /New job/ })).toBeNull();
  });

  it("describes due dates in plain words", () => {
    expect(dueText({ due: "x", days_left: 0, status: "open" })).toBe("Due today");
    expect(dueText({ due: "x", days_left: -1, status: "open" })).toBe("1 day late");
    expect(dueText({ due: null, days_left: null, status: "open" })).toBe("No due date");
  });
});

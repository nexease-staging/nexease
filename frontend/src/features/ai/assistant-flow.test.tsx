import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import Assistant from "@/features/saas/assistant";
import type { Assist, Proposal } from "./forms";

const { api, push } = vi.hoisted(() => ({ api: vi.fn(), push: vi.fn() }));
vi.mock("@/lib/api/client", () => ({ apiRequest: api, apiBinaryRequest: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }), usePathname: () => "/dashboard", useSearchParams: () => new URLSearchParams() }));
vi.mock("./ai-form-host", () => ({ default: ({ proposal }: { proposal: Proposal }) => <div data-testid="ai-form">{proposal.assist?.form?.type}:{JSON.stringify(proposal.data.items)}</div> }));

const base: Assist = { kind: "invoice", label: "Sales invoice", form: { type: "invoice", route: "/invoices" }, missing: [], ready: true, summary: [], reply: "", refs: {}, quick_save: true };
const items = [{ name: "Cement", quantity: "10", unit_price: "", tax_rate: "18" }];
const asking: Proposal = { id: "p1", kind: "invoice", state: "review", warnings: [], result: {}, data: { kind: "invoice", fields: { party_name: "Sharma" }, items, questions: [], warnings: [] },
  assist: { ...base, ready: false, reply: "Sales invoice for Sharma — almost there. What is the rate for Cement?", missing: [{ field: "items.0.unit_price", label: "Rate", question: "What is the rate for Cement?", required: true, choices: [], input: "number" }] } };

function setup(post: (path: string, body: unknown) => unknown) {
  api.mockImplementation(async (path: string, options?: { method?: string; body?: unknown }) => {
    if (path.includes("subscription")) return { data: { membership: { features: ["ai"], status: "active", end: "2099-01-01T00:00:00", suspended: false } } };
    if (options?.method === "POST") return { data: post(path, options.body) };
    return { data: { enabled: true, history: [], usage: { requests: 0, pages: 0 }, accounts: [], employees: [] } };
  });
  localStorage.setItem("nexease-ai-consent", "yes");
  render(<QueryClientProvider client={new QueryClient()}><Assistant /></QueryClientProvider>);
  fireEvent.click(screen.getByLabelText("Open NexEase AI"));
}

beforeEach(() => { vi.clearAllMocks(); localStorage.clear(); sessionStorage.clear(); });

describe("NexEase AI conversation", () => {
  it("asks for a missing rate, takes the answer without another AI call, then opens the prefilled invoice", async () => {
    setup((path, body) => {
      if (path === "/saas/ai/") return asking;
      const data = (body as { data: Proposal["data"] }).data;
      return { ...asking, data, assist: { ...base, reply: "Sales invoice for Sharma is ready." } };
    });
    fireEvent.change(await screen.findByLabelText("AI instruction"), { target: { value: "Invoice Sharma 10 cement 18% GST" } });
    fireEvent.click(screen.getByLabelText("Prepare entry"));
    expect(await screen.findByText(/almost there/)).toBeInTheDocument();
    expect(screen.getByText("1 detail needed")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Rate"), { target: { value: "380" } });
    fireEvent.click(screen.getByLabelText("Answer Rate"));
    expect(await screen.findByText("Sales invoice for Sharma is ready.")).toBeInTheDocument();
    const review = api.mock.calls.find(([p]) => String(p).includes("/review/"));
    expect(review?.[1].body.data.items[0].unit_price).toBe("380");
    expect(api.mock.calls.filter(([p, o]) => p === "/saas/ai/" && o?.method === "POST")).toHaveLength(1);
    expect(await screen.findByTestId("ai-form", {}, { timeout: 2000 })).toHaveTextContent('invoice:[{"name":"Cement","quantity":"10","unit_price":"380"');
    expect(api.mock.calls.some(([p]) => String(p).includes("/confirm/"))).toBe(false);
  });

  it("hands a ready expense to the expenses screen", async () => {
    setup(() => ({ id: "p2", kind: "expense", state: "review", warnings: [], result: {}, data: { kind: "expense", fields: { party_name: "HP pump", amount: "500", payment_mode: "UPI", category: "Petrol / fuel", description: "Site visit" }, items: [], questions: [], warnings: [] },
      assist: { ...base, kind: "expense", label: "Expense", form: { type: "record", record_kind: "expenses", route: "/expenses" }, reply: "Expense is ready." } }));
    fireEvent.change(await screen.findByLabelText("AI instruction"), { target: { value: "paid 500 petrol upi" } });
    fireEvent.keyDown(screen.getByLabelText("AI instruction"), { key: "Enter" });
    await waitFor(() => expect(push).toHaveBeenCalledWith("/expenses"), { timeout: 2000 });
    const stored = JSON.parse(sessionStorage.getItem("nexease:ai-prefill") ?? "{}");
    expect(stored.kind).toBe("expenses");
    expect(stored.data).toMatchObject({ payee: "HP pump", amount: "500", payment_mode: "UPI" });
  });

  it("offers choices as one-tap answers and remembers consent", async () => {
    setup((path, body) => (path === "/saas/ai/" ? { ...asking, assist: { ...asking.assist!, missing: [{ field: "payment_mode", label: "Payment mode", question: "How was it paid?", required: true, choices: ["Cash", "UPI"], input: "choice" }] } } : { ...asking, data: (body as { data: Proposal["data"] }).data }));
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
    fireEvent.change(await screen.findByLabelText("AI instruction"), { target: { value: "Received 500 from Ravi" } });
    fireEvent.click(screen.getByLabelText("Prepare entry"));
    fireEvent.click(await screen.findByRole("button", { name: "UPI" }));
    await waitFor(() => expect(api.mock.calls.find(([p]) => String(p).includes("/review/"))?.[1].body.data.fields.payment_mode).toBe("UPI"));
  });
});

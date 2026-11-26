import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import GstHub from "./gst-hub";
import { portalChecklist, type InwardRecord } from "./api";

const { api, params, replace } = vi.hoisted(() => ({ api: vi.fn(), params: { value: "tab=ims&period=2026-10" }, replace: vi.fn() }));
vi.mock("@/lib/api/client", () => ({ apiRequest: api, apiBinaryRequest: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace, push: vi.fn() }), usePathname: () => "/taxation", useSearchParams: () => new URLSearchParams(params.value) }));
vi.mock("@/features/auth/auth-context", () => ({ useAuth: () => ({ authentication: { role: { permissions: ["taxation.read", "taxation.manage"] } } }) }));
vi.mock("@/lib/authorization/permissions", () => ({ hasPermission: (l: string[], p: string) => l.includes(p) }));
vi.mock("@/features/business/workspace", () => ({ default: () => <div>workspace</div>, exportWorkbook: vi.fn() }));
vi.mock("@/features/business/gst-source-review", () => ({ default: () => null }));

const rec = (over: Partial<InwardRecord>): InwardRecord => ({
  id: "r1", period: "2026-10", source: "gstr2b", supplier_gstin: "27AAPFU0939F1ZV", supplier_name: "Om Steel", doc_type: "INV", doc_number: "OMS/0221", doc_date: "2026-10-05",
  pos: "27", rcm: false, taxable: "13000.00", igst: "0.00", cgst: "1170.00", sgst: "1170.00", cess: "0.00", total_tax: "2340.00", value: "15340.00", itc_available: true,
  portal_action: "", action: "none", reason: "", itc_reduce: "", match: { status: "matched", differences: [], bill: { id: "b1", number: "B-1", supplier_invoice: "OMS-221", date: "2026-10-05", taxable: "13000.00", total_tax: "2340.00" } },
  suggested: "accept", suggestion: "Matches your purchase bill.", ...over,
});
const records = [
  rec({}),
  rec({ id: "r2", doc_number: "SE-9", supplier_name: "Sharma Exports", match: { status: "only_in_2b", differences: [], bill: null }, suggested: "pending", suggestion: "Not in your books." }),
  rec({ id: "r3", doc_number: "RC-1", rcm: true, suggested: "none" }),
];
const overview = { period: "2026-10", registration: { gstin: "27AAACN1234F1Z5", state_code: "27", legal_name: "Demo Traders", registration: "regular", frequency: "monthly", configured: true },
  deadlines: [], ims: { accept: 0, reject: 0, pending: 0, none: 2 }, reconciliation: {}, missing_in_2b: 0, gstr1: { tables: [], documents: { from: "", to: "", issued: 0, cancelled: 0 } },
  gstr3b: { liability: { igst: "0", cgst: "0", sgst: "0", cess: "0" }, itc: { igst: "0", cgst: "0", sgst: "0", cess: "0" }, cash: { igst: "0", cgst: "0", sgst: "0", cess: "0" } }, alerts: [] };

function setup() {
  api.mockImplementation(async (path: string, options?: { method?: string }) => {
    if (path.startsWith("/business/gst/overview/")) return { data: overview };
    if (path.startsWith("/business/gst/ims/action/")) return { data: { updated: 1, skipped: [] } };
    if (path.startsWith("/business/gst/ims/") && options?.method === "POST") return { data: { period: "2026-10", added: 3, updated: 0 } };
    if (path.startsWith("/business/gst/ims/")) return { data: { period: "2026-10", records, count: 3, missing_in_2b: [] } };
    return { data: {} };
  });
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><GstHub /></QueryClientProvider>);
}

beforeEach(() => { vi.clearAllMocks(); params.value = "tab=ims&period=2026-10"; });

describe("IMS inbox", () => {
  it("bulk-accepts selected documents and never offers reverse-charge rows for selection", async () => {
    setup();
    expect(await screen.findByLabelText("Select OMS/0221")).toBeInTheDocument();
    expect(screen.queryByLabelText("Select RC-1")).not.toBeInTheDocument();
    expect(screen.getByText("Not in IMS")).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Select OMS/0221"));
    fireEvent.click(screen.getByRole("button", { name: /^Accept$/ }));
    await waitFor(() => expect(api).toHaveBeenCalledWith("/business/gst/ims/action/", { method: "POST", body: { ids: ["r1"], action: "accept" } }));
  });

  it("asks for a reason before rejecting", async () => {
    setup();
    fireEvent.click(await screen.findByLabelText("Select SE-9"));
    fireEvent.click(screen.getByRole("button", { name: /^Reject$/ }));
    const submit = screen.getByRole("button", { name: "Reject 1" });
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Reason for rejecting"), { target: { value: "Not our purchase" } });
    fireEvent.click(submit);
    await waitFor(() => expect(api).toHaveBeenCalledWith("/business/gst/ims/action/", { method: "POST", body: { ids: ["r2"], action: "reject", reason: "Not our purchase" } }));
  });

  it("applies suggestions to documents without an action", async () => {
    setup();
    fireEvent.click(await screen.findByRole("button", { name: /Apply suggestions/ }));
    await waitFor(() => expect(api.mock.calls.filter(([p]) => p === "/business/gst/ims/action/")).toHaveLength(2));
    const bodies = api.mock.calls.filter(([p]) => p === "/business/gst/ims/action/").map(([, o]) => o.body);
    expect(bodies).toContainEqual({ ids: ["r1"], action: "accept" });
    expect(bodies.find((b) => b.action === "pending").ids).toEqual(["r2"]);
  });

  it("filters by action and shows the match details", async () => {
    setup();
    const tabs = await screen.findByRole("tablist", { name: "Filter by IMS action" });
    await waitFor(() => expect(within(tabs).getByRole("tab", { name: /No action/ })).toHaveTextContent("3"));
    fireEvent.click(screen.getByRole("button", { name: /Sharma Exports/ }));
    expect(screen.getByText("Not in your books.")).toBeInTheDocument();
  });
});

describe("Hub navigation", () => {
  it("switches tabs through the URL", async () => {
    params.value = "period=2026-10";
    setup();
    fireEvent.click(await screen.findByRole("tab", { name: /GSTR-3B/ }));
    expect(replace).toHaveBeenCalledWith("/taxation?period=2026-10&tab=gstr3b", { scroll: false });
  });
});

it("portal checklist lists only decided, non-reverse-charge documents", () => {
  const csv = portalChecklist([rec({ action: "accept" }), rec({ id: "x", doc_number: "A,B", action: "reject", reason: "Wrong \"GSTIN\"" }), rec({ id: "y", action: "none" }), rec({ id: "z", rcm: true, action: "accept" })]);
  const lines = csv.split("\n");
  expect(lines).toHaveLength(3);
  expect(lines[1]).toContain("Accepted");
  expect(lines[2]).toContain('"A,B"');
  expect(lines[2]).toContain('"Wrong ""GSTIN"""');
});

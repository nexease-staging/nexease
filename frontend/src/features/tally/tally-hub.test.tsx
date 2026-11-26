import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import TallyHub from "./tally-hub";
import { whatsappLink, type Status } from "./api";

const { api, params, replace } = vi.hoisted(() => ({ api: vi.fn(), params: { value: "" }, replace: vi.fn() }));
vi.mock("@/lib/api/client", () => ({ apiRequest: api, apiBinaryRequest: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace, push: vi.fn() }), usePathname: () => "/tally", useSearchParams: () => new URLSearchParams(params.value) }));
vi.mock("@/features/business/workspace", () => ({ exportWorkbook: vi.fn() }));
vi.mock("@/features/reports/components/report-chart", () => ({ default: ({ title }: { title: string }) => <div>chart {title}</div> }));

const company = { id: "c1", name: "Sharma Traders", enabled: true, open: true, gstin: "27AAACS1111A1Z5", state: "Maharashtra", books_from: "2026-04-01", progress: 100,
  masters_synced: true, counts: { ledger: 15, stockitem: 1, voucher: 2 }, seen_at: null };
const base: Status = { connected: true, online: true, tally_ok: true, devices: [{ id: "d1", name: "Accounts PC", last_seen: new Date().toISOString(), online: true, info: { version: "1.0.0" } }],
  companies: [company], pending: 0, failed: 0, issues: 1, pushed: 4, paused: false, last_sync: new Date().toISOString(), tally_error: "", download_url: "https://example.com/c.exe", can_manage: true, interval: 30 };
const voucher = { guid: "v1", date: "2026-11-02", type: "GST Sales", base: "Sales", number: "T-1", party: "Acme Retail", amount: 1180, narration: "", reference: "", from_nexease: false, cancelled: false };
const overview = { connected: true, company: "Sharma Traders", kpis: { sales: { value: 1180, previous: 0 }, purchase: { value: 0, previous: 0 }, receipts: { value: 500, previous: 0 }, payments: { value: 0, previous: 0 } },
  receivable: 680, payable: 0, cash: 0, bank: 500, stock_value: 24000, cash_bank: [{ name: "HDFC Bank", balance: 500, group: "bank" }], trend: [{ month: "2026-11", sales: 1180, purchase: 0, receipts: 500, payments: 0 }],
  top_debtors: [{ guid: "l1", name: "Acme Retail", balance: 680, phone: "9876500001" }], top_creditors: [], recent: [voucher] };
const settings = { settings: { write_back: {}, mapping: {}, bank_ledgers: {}, expense_ledgers: {}, voucher_types: {}, import_masters: true, invoice_mode: "auto", debtors_group: "Sundry Debtors", creditors_group: "Sundry Creditors", push_from: "2026-11-27" },
  write_kinds: ["customers", "invoices"], mapping_keys: ["sales", "cgst_out"],
  options: { ledgers: ["Sales GST", "Output CGST"], by_group: { sales: ["Sales GST"], tax: ["Output CGST"] }, bank_accounts: [], accounts: [], expense_categories: [], voucher_types: [], suggested: { sales: "Sales GST", cgst_out: "Output CGST" } } };

function setup(status: Status = base) {
  api.mockImplementation(async (path: string) => {
    if (path.startsWith("/business/tally/status/")) return { data: status };
    if (path.startsWith("/business/tally/overview/")) return { data: overview };
    if (path.startsWith("/business/tally/pair/")) return { data: { code: "ABCD-2345" } };
    if (path.startsWith("/business/tally/settings/")) return { data: settings };
    if (path.startsWith("/business/tally/issues/")) return { data: { issues: [{ model: "invoice", id: "i1", label: "Invoice INV-11", state: "blocked", error: "Choose the Tally ledger for “sales”.", updated_at: "" }] } };
    if (path.startsWith("/business/tally/jobs/")) return { data: { jobs: [{ id: "j1", type: "push", kind: "invoice", label: "Invoice INV-9", status: "done", attempts: 1, error: "", created_at: new Date().toISOString(), done_at: null, result: {} }] } };
    if (path.startsWith("/business/tally/vouchers/")) return { data: { ...voucher, party_gstin: "", place_of_supply: "", entries: [{ ledger: "Acme Retail", debit: 1180, credit: 0 }, { ledger: "Sales GST", debit: 0, credit: 1000 }], inventory: [], bills: [], deleted: false } };
    return { data: {} };
  });
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><TallyHub /></QueryClientProvider>);
}

beforeEach(() => { vi.clearAllMocks(); params.value = ""; });

describe("Tally hub", () => {
  it("guides setup and creates a pairing code when Tally is not connected", async () => {
    setup({ ...base, connected: false, online: false, tally_ok: false, devices: [], companies: [], issues: 0 });
    expect(await screen.findByText("Connect Tally to NexEase")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Download for Windows/ })).toHaveAttribute("href", "https://example.com/c.exe");
    fireEvent.click(screen.getByRole("button", { name: /Create pairing code/ }));
    expect(await screen.findByLabelText("Pairing code")).toHaveTextContent("ABCD-2345");
    expect(api).toHaveBeenCalledWith("/business/tally/pair/", expect.objectContaining({ method: "POST" }));
  });

  it("shows live Tally figures and opens a voucher", async () => {
    setup();
    expect(await screen.findByText("Sales this month")).toBeInTheDocument();
    expect(screen.getByText("In sync")).toBeInTheDocument();
    const shared = vi.fn();
    window.addEventListener("nexease:share", (e) => shared((e as CustomEvent).detail));
    fireEvent.click(screen.getByRole("button", { name: "Remind Acme Retail on WhatsApp" }));
    expect(shared).toHaveBeenCalledWith(expect.objectContaining({ kind: "tally_ledger", id: "l1" }));
    fireEvent.click(screen.getByText("T-1"));
    await waitFor(() => expect(screen.getByRole("dialog")).toHaveTextContent("Sales GST"));
  });

  it("lists items held back and saves the suggested ledger mapping", async () => {
    params.value = "tab=sync";
    setup();
    expect(await screen.findByText("Invoice INV-11")).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "Fill suggestions" }));
    fireEvent.click(screen.getByRole("button", { name: "Save settings" }));
    await waitFor(() => expect(api).toHaveBeenCalledWith("/business/tally/settings/", expect.objectContaining({ method: "POST", body: expect.objectContaining({ mapping: { sales: "Sales GST", cgst_out: "Output CGST" } }) })));
  });
});

describe("whatsappLink", () => {
  it("adds the country code to ten-digit numbers", () => {
    expect(whatsappLink("98765 00001", "A", 100, "Co")).toMatch(/^https:\/\/wa\.me\/919876500001\?text=/);
  });
});

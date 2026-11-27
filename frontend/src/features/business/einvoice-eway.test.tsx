import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import EInvoices, { deadline, type Listing, type Row } from "./einvoices";
import EWayBills, { type Bill } from "./eway-bills";

const { api, params } = vi.hoisted(() => ({ api: vi.fn(), params: { value: "" } }));
vi.mock("@/lib/api/client", () => ({ apiRequest: api, apiBinaryRequest: vi.fn() }));
vi.mock("@/lib/browser/download", () => ({ downloadBlob: vi.fn() }));
vi.mock("@/components/nex-feedback", () => ({ confirmAction: vi.fn().mockResolvedValue(true), notify: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), replace: vi.fn() }), useSearchParams: () => new URLSearchParams(params.value) }));

const row = (over: Partial<Row>): Row => ({ id: "i1", kind: "invoice", number: "INV-0101", date: "2026-11-25", customer: "Patil Builders", invoice_status: "ISSUED",
  total: "11800.00", category: "", days_left: 28, late: false, ...over });
const listing = (over: Partial<Listing> = {}): Listing => ({
  records: [row({}), row({ id: "i2", number: "INV-0090", days_left: -10, late: true }), row({ id: "i3", number: "EXP-0001", export: true }),
    row({ id: "i4", number: "INV-0080", status: "registered", irn: "a".repeat(64), ack_no: "1123", days_left: null })],
  summary: { to_register: 3, due_soon: 0, late: 1, pending: 0 }, configured: true, gstin: "27AAACN1234F1Z5", environment: "test",
  preferences: { turnover_10cr: true, auto_generate: false },
  categories: { B2B: "Business to business", SEZWP: "SEZ with payment of IGST", SEZWOP: "SEZ without payment (LUT/bond)", EXPWP: "Export with payment of IGST", EXPWOP: "Export without payment (LUT/bond)" },
  reporting_days: 30, bulk_limit: 25, can_configure: true, can_issue: true, can_cancel: true, ...over,
});
const wrap = (ui: React.ReactNode) => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{ui}</QueryClientProvider>);

beforeEach(() => { vi.clearAllMocks(); params.value = ""; });

describe("E-invoices", () => {
  it("shows deadlines, blocks late documents and registers ready ones in bulk", async () => {
    api.mockImplementation(async (path: string, opts?: { body?: Record<string, unknown> }) => {
      if (opts?.body?.action === "generate-bulk") return { data: { results: [{ id: "i1", number: "INV-0101", ok: true }], registered: 1 } };
      return { data: listing() };
    });
    wrap(<EInvoices />);
    expect(await screen.findByRole("button", { name: "INV-0090 is past the 30-day limit" })).toBeDisabled();
    expect(screen.getAllByText("Past 30 days").length).toBeGreaterThanOrEqual(2);
    fireEvent.click(screen.getByRole("button", { name: /Register 1 ready/ }));
    await waitFor(() => expect(api).toHaveBeenCalledWith("/business/e-invoices/", expect.objectContaining({ body: expect.objectContaining({ action: "generate-bulk", ids: ["i1"], kind: "invoice", confirm: true }) })));
    expect(await screen.findByText("Bulk registration")).toBeInTheDocument();
  });

  it("asks for the export details for an export invoice", async () => {
    api.mockResolvedValue({ data: listing() });
    wrap(<EInvoices />);
    fireEvent.click(await screen.findByRole("button", { name: "Register EXP-0001" }));
    const sheet = await screen.findByRole("dialog");
    expect(within(sheet).getByDisplayValue("Export without payment (LUT/bond)")).toBeInTheDocument();
    fireEvent.change(within(sheet).getByLabelText("Destination country code"), { target: { value: "AE" } });
    fireEvent.click(within(sheet).getByRole("button", { name: "Submit to IRP" }));
    await waitFor(() => expect(api).toHaveBeenCalledWith("/business/e-invoices/", expect.objectContaining({
      body: expect.objectContaining({ action: "generate", id: "i3", category: "EXPWOP", export: expect.objectContaining({ country: "AE" }) }) })));
  });

  it("switches to credit notes", async () => {
    api.mockResolvedValue({ data: listing({ records: [] }) });
    wrap(<EInvoices />);
    fireEvent.click(await screen.findByRole("button", { name: "Credit notes" }));
    await waitFor(() => expect(api).toHaveBeenCalledWith(expect.stringContaining("kind=credit_note")));
  });

  it("describes the reporting window", () => {
    expect(deadline({ days_left: 3, invoice_status: "ISSUED" }, false)).toEqual({ label: "3 days left", tone: "warning" });
    expect(deadline({ days_left: -2, invoice_status: "ISSUED" }, false)?.tone).toBe("warning");
    expect(deadline({ days_left: -2, invoice_status: "ISSUED" }, true)).toEqual({ label: "Past 30 days", tone: "danger" });
    expect(deadline({ days_left: 3, status: "registered", invoice_status: "ISSUED" }, true)).toBeNull();
  });
});

const bill = (over: Partial<Bill>): Bill => ({ source_id: "c1", kind: "challan", document: "DC-0001", status: "generated", number: "321000000001",
  valid_until: "28/11/2026 11:59:00 PM", vehicle: "MH12AB1234", cancellable: true, extendable: false, extend_opens: "2026-11-28T10:29:00+05:30", history: [], ...over });

describe("E-way bills", () => {
  const data = {
    sources: [{ id: "c9", kind: "challan", document: "DC-0009", customer: "Coat Works" }],
    records: [bill({}), bill({ source_id: "c2", document: "DC-0002", number: "321000000002", cancellable: false, extendable: true })],
    consolidated: [], configured: true, environment: "test", state_code: "27", can_issue: true, can_cancel: true,
    reasons: { cancel: { "2": "Order cancelled" }, vehicle: { "1": "Due to break down" }, extend: { "5": "Accident" } },
  };

  it("cancels, changes vehicle and only extends inside the window", async () => {
    api.mockImplementation(async (_p: string, opts?: { body?: Record<string, unknown> }) => (opts?.body ? { data: { number: "321000000001", status: "cancelled" } } : { data }));
    wrap(<EWayBills />);
    expect(await screen.findByRole("button", { name: /Extension opens/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Extend 321000000002" })).toBeEnabled();
    expect(screen.queryByRole("button", { name: "Cancel 321000000002" })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Cancel 321000000001" }));
    const sheet = await screen.findByRole("dialog");
    fireEvent.change(within(sheet).getByLabelText("Remarks"), { target: { value: "Order cancelled" } });
    fireEvent.click(within(sheet).getByRole("button", { name: "Cancel e-way bill" }));
    await waitFor(() => expect(api).toHaveBeenCalledWith("/business/e-way-bills/", expect.objectContaining({ body: expect.objectContaining({ action: "cancel", id: "c1", reason: "2", remarks: "Order cancelled" }) })));

    fireEvent.click(screen.getByRole("button", { name: "Change vehicle for 321000000002" }));
    const v = await screen.findByRole("dialog");
    fireEvent.change(within(v).getByLabelText("Vehicle number"), { target: { value: "MH14XY9876" } });
    fireEvent.change(within(v).getByLabelText("Current place"), { target: { value: "Talegaon" } });
    fireEvent.click(within(v).getByRole("button", { name: "Update vehicle" }));
    await waitFor(() => expect(api).toHaveBeenCalledWith("/business/e-way-bills/", expect.objectContaining({ body: expect.objectContaining({ action: "vehicle", vehicle: "MH14XY9876", from_place: "Talegaon" }) })));
  });

  it("generates with the distance left to the portal and consolidates trips", async () => {
    api.mockImplementation(async (_p: string, opts?: { body?: Record<string, unknown> }) => (opts?.body ? { data: { number: "4100000001" } } : { data }));
    wrap(<EWayBills />);
    fireEvent.click((await screen.findAllByRole("button", { name: /New e-way bill/ }))[0]);
    const sheet = await screen.findByRole("dialog");
    fireEvent.change(within(sheet).getByLabelText("Invoice or delivery challan"), { target: { value: "challan:c9" } });
    fireEvent.change(within(sheet).getByLabelText("Vehicle number"), { target: { value: "MH12AB1234" } });
    fireEvent.change(within(sheet).getByLabelText("Delivery city"), { target: { value: "Chakan" } });
    fireEvent.change(within(sheet).getByLabelText("Delivery PIN"), { target: { value: "410501" } });
    expect(within(sheet).queryByLabelText("Distance (km)")).toBeNull();
    fireEvent.click(within(sheet).getByRole("button", { name: "Generate e-way bill" }));
    await waitFor(() => expect(api).toHaveBeenCalledWith("/business/e-way-bills/", expect.objectContaining({ body: expect.objectContaining({ action: "generate", kind: "challan", id: "c9", auto_distance: true }) })));

    fireEvent.click(screen.getAllByRole("button", { name: "Consolidate e-way bills" })[0]);
    const c = await screen.findByRole("dialog");
    within(c).getAllByRole("checkbox").forEach((box) => fireEvent.click(box));
    fireEvent.change(within(c).getByLabelText("Vehicle number"), { target: { value: "MH12AB1234" } });
    fireEvent.change(within(c).getByLabelText("Dispatch place"), { target: { value: "Pune" } });
    fireEvent.click(within(c).getByRole("button", { name: "Generate consolidated e-way bill" }));
    await waitFor(() => expect(api).toHaveBeenCalledWith("/business/e-way-bills/", expect.objectContaining({ body: expect.objectContaining({ action: "consolidate", numbers: ["321000000001", "321000000002"] }) })));
  });
});

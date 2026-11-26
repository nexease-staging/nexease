import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import ShareHost from "./share-dialog";
import { openShare, waNumber, type Prepared } from "./api";

const { api, binary, nativeShare } = vi.hoisted(() => ({ api: vi.fn(), binary: vi.fn(), nativeShare: vi.fn() }));
vi.mock("@/lib/api/client", () => ({ apiRequest: api, apiBinaryRequest: binary }));
vi.mock("@capacitor/core", () => ({ Capacitor: { isNativePlatform: () => false } }));
vi.mock("@capacitor/filesystem", () => ({ Filesystem: {}, Directory: {} }));
vi.mock("@capacitor/share", () => ({ Share: { share: nativeShare } }));
vi.mock("@/lib/browser/download", () => ({ downloadBlob: vi.fn() }));
vi.mock("@/components/nex-feedback", () => ({ notify: vi.fn() }));

const prepared = (over: Partial<Prepared> = {}): Prepared => ({
  kind: "invoice", id: "i1", label: "Invoice", number: "INV-7", filename: "Invoice-INV-7.pdf", recipient: { name: "Acme Retail", phone: "98765 00001", email: "acme@example.com" },
  amount: 1180, whatsapp: "Dear Acme Retail,\nPlease find invoice INV-7 for ₹1,180.00 from Sharma Traders.", subject: "Invoice INV-7 from Sharma Traders", body: "Dear Acme Retail,\n\nPlease find attached invoice INV-7.",
  link: { token: "tok", url: "https://api.example.com/api/v1/business/share/l/tok/", expires: "2026-12-27", views: 0 }, extra: {}, history: [], ...over,
});

function setup(data = prepared()) {
  api.mockImplementation(async (path: string) => {
    if (path.startsWith("/business/share/prepare/")) return { data };
    if (path === "/business/share/email/") return { data: { sent_to: ["acme@example.com"] } };
    return { data: {} };
  });
  binary.mockResolvedValue({ blob: new Blob(["%PDF-1.4"], { type: "application/pdf" }), filename: "x.pdf", contentType: "application/pdf" });
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><ShareHost /></QueryClientProvider>);
}

beforeEach(() => { vi.clearAllMocks(); });

describe("share sheet", () => {
  it("opens the chat with the number, the message and the live link", async () => {
    const open = vi.spyOn(window, "open").mockReturnValue(null);
    setup();
    act(() => openShare({ kind: "invoice", id: "i1" }));
    expect(await screen.findByDisplayValue("98765 00001")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Open chat with 98765 00001/ }));
    const url = open.mock.calls[0][0] as string;
    expect(url.startsWith("https://wa.me/919876500001?text=")).toBe(true);
    expect(decodeURIComponent(url)).toContain("View / download: https://api.example.com/api/v1/business/share/l/tok/");
    expect(api).toHaveBeenCalledWith("/business/share/log/", expect.objectContaining({ body: expect.objectContaining({ channel: "whatsapp", recipient: "98765 00001" }) }));
  });

  it("attaches the PDF through the device share sheet when supported", async () => {
    const share = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { share, canShare: () => true });
    setup();
    act(() => openShare({ kind: "invoice", id: "i1" }));
    fireEvent.click(await screen.findByRole("button", { name: /Send PDF on WhatsApp/ }));
    await waitFor(() => expect(share).toHaveBeenCalled());
    const payload = share.mock.calls[0][0] as { files: File[]; text: string };
    expect(payload.files[0].name).toBe("Invoice-INV-7.pdf");
    expect(payload.text).toContain("invoice INV-7");
  });

  it("emails with attachment and edited subject", async () => {
    setup();
    act(() => openShare({ kind: "invoice", id: "i1", channel: "email" }));
    const subject = await screen.findByDisplayValue("Invoice INV-7 from Sharma Traders");
    fireEvent.change(subject, { target: { value: "Your invoice" } });
    fireEvent.click(screen.getByRole("button", { name: /Send email/ }));
    await waitFor(() => expect(api).toHaveBeenCalledWith("/business/share/email/", expect.objectContaining({
      body: expect.objectContaining({ kind: "invoice", id: "i1", recipients: "acme@example.com", subject: "Your invoice", attach: true }) })));
    expect(await screen.findByText(/Shared · Email · acme@example.com/)).toBeInTheDocument();
  });

  it("lets a statement change period", async () => {
    setup(prepared({ kind: "statement", label: "Statement", extra: { from: "2026-04-01", to: "2026-11-27", side: "customer", balance: 680 } }));
    act(() => openShare({ kind: "statement", id: "c1", side: "customer" }));
    fireEvent.click(await screen.findByRole("radio", { name: "Last month" }));
    await waitFor(() => expect(api.mock.calls.some(([p]) => String(p).includes("kind=statement") && String(p).includes("side=customer") && String(p).includes("from="))).toBe(true));
    expect(await screen.findByText(/due from them/)).toBeInTheDocument();
  });
});

describe("waNumber", () => {
  it("adds India's code to 10-digit numbers and rejects junk", () => {
    expect(waNumber("098765 00001")).toBe("919876500001");
    expect(waNumber("+44 7700 900123")).toBe("447700900123");
    expect(waNumber("123")).toBe("");
  });
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import InvoiceFormats from "./invoice-formats";

const { api, binary } = vi.hoisted(() => ({ api: vi.fn(), binary: vi.fn() }));
vi.mock("@/lib/api/client", () => ({ apiRequest: api, apiBinaryRequest: binary }));

const templates = [
  { id: "gst_classic", name: "GST Classic", color: "#1f2937", layout: "gst_classic", description: "Boxed GST format" },
  { id: "modern", name: "Modern band", color: "#0f766e", layout: "modern", description: "Coloured band" },
  { id: "thermal", name: "Thermal receipt (80 mm)", color: "#111827", layout: "thermal", description: "Narrow roll" },
];

beforeEach(() => {
  vi.clearAllMocks();
  api.mockImplementation(async (_path: string, options?: { method?: string; body?: unknown }) => ({ data: { settings: options?.body ?? { template: "gst_classic" }, templates } }));
  binary.mockResolvedValue({ blob: new Blob(["%PDF"], { type: "application/pdf" }), contentType: "application/pdf" });
  URL.createObjectURL = vi.fn(() => "blob:preview");
  URL.revokeObjectURL = vi.fn();
});

const wrap = () => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><InvoiceFormats /></QueryClientProvider>);

it("chooses a template for every document and saves it", async () => {
  wrap();
  fireEvent.click(await screen.findByRole("button", { name: "Use Modern band" }));
  expect(screen.getByRole("button", { name: "Use Modern band" })).toHaveAttribute("aria-pressed", "true");
  fireEvent.click(screen.getByRole("button", { name: "Save changes" }));
  await waitFor(() => expect(api).toHaveBeenCalledWith("/business/invoice-settings/", { method: "POST", body: { template: "modern" } }));
});

it("blocks saving an invalid UPI ID", async () => {
  wrap();
  fireEvent.change(await screen.findByPlaceholderText("business@okhdfcbank"), { target: { value: "wrong" } });
  expect(screen.getByText(/Enter a UPI ID/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
});

it("previews any document type in a template and can apply it", async () => {
  wrap();
  fireEvent.click((await screen.findAllByRole("button", { name: "Preview" }))[2]);
  expect(await screen.findByTitle("Thermal receipt (80 mm) sample")).toHaveAttribute("src", "blob:preview");
  fireEvent.click(screen.getByRole("tab", { name: "Estimate / quotation" }));
  await waitFor(() => expect(binary).toHaveBeenLastCalledWith(expect.stringContaining("kind=quotation")));
  expect(binary.mock.calls.at(-1)?.[0]).toContain("template=thermal");
  fireEvent.click(screen.getByRole("button", { name: "Use this format" }));
  expect(screen.getByRole("button", { name: "Use Thermal receipt (80 mm)" })).toHaveAttribute("aria-pressed", "true");
});

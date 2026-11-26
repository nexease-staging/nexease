import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ReorderSheet from "./reorder-sheet";
import { apiRequest } from "@/lib/api/client";
import type { LowStockItem } from "../insights";

vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn() }));
vi.mock("@/features/suppliers/hooks", () => ({ useSupplierList: () => ({ data: { suppliers: [{ id: "OMC", code: "OMC", name: "Om Cement Depot" }, { id: "SST", code: "SST", name: "Shree Steel" }] } }) }));
vi.mock("@/components/search-select", () => ({ default: (props: React.SelectHTMLAttributes<HTMLSelectElement>) => <select aria-label="Supplier" {...props} /> }));

const cement: LowStockItem = { product_id: "p1", sku: "CEM", name: "OPC cement", unit: "BAG", cost_price: "380.00", on_hand: "12.00", reserved: "2.00", available: "10.00", reorder_level: "20.00", suggested_quantity: "30.00", supplier: { id: "OMC", code: "OMC", name: "Om Cement Depot", last_rate: "375.00", last_po: "PO-1" } };

beforeEach(() => { vi.clearAllMocks(); vi.mocked(apiRequest).mockResolvedValue({ data: { number: "PO-0043" } } as never); });

function mount() {
  const onClose = vi.fn(), onCreated = vi.fn();
  render(<QueryClientProvider client={new QueryClient()}><ReorderSheet items={[cement]} onClose={onClose} onCreated={onCreated} /></QueryClientProvider>);
  return { onClose, onCreated };
}

describe("ReorderSheet", () => {
  it("pre-fills the last supplier, suggested quantity and last rate", () => {
    mount();
    expect(screen.getByLabelText("Supplier")).toHaveValue("OMC");
    expect(screen.getByLabelText("quantity CEM")).toHaveValue("30.00");
    expect(screen.getByLabelText("rate CEM")).toHaveValue("375.00");
  });
  it("creates a draft purchase order through quick purchases", async () => {
    const { onClose, onCreated } = mount();
    fireEvent.change(screen.getByLabelText("gst CEM"), { target: { value: "28" } });
    fireEvent.click(screen.getByRole("button", { name: "Create draft PO" }));
    await waitFor(() => expect(onCreated).toHaveBeenCalledWith("PO-0043"));
    expect(apiRequest).toHaveBeenCalledWith("/business/quick-purchases/", expect.objectContaining({
      method: "POST",
      body: expect.objectContaining({ kind: "purchase_order", supplier: { code: "OMC", name: "Om Cement Depot" }, items: [expect.objectContaining({ sku: "CEM", quantity: "30.00", unit_price: "375.00", tax_rate: "28" })] }),
    }));
    expect(onClose).toHaveBeenCalled();
  });
  it("blocks an invalid quantity without calling the server", async () => {
    mount();
    fireEvent.change(screen.getByLabelText("quantity CEM"), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: "Create draft PO" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("quantity above 0");
    expect(apiRequest).not.toHaveBeenCalled();
  });
});

import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import InventoryPage from "./page";
import { useInventoryList } from "@/features/inventory/hooks";
import { useInventoryInsights } from "@/features/inventory/insights";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock("@/features/auth/auth-context", () => ({ useAuth: () => ({ authentication: { role: { permissions: ["inventory.read", "inventory.adjust", "purchase_orders.create"] } } }) }));
vi.mock("@/features/warehouses/hooks", () => ({ useWarehouseList: () => ({ data: { warehouses: [] } }) }));
vi.mock("@/features/inventory/components/opening-inventory-dialog", () => ({ default: () => null }));
vi.mock("@/features/inventory/components/stock-adjustment-dialog", () => ({ default: ({ open }: { open: boolean }) => (open ? <div role="dialog">Adjusting</div> : null) }));
vi.mock("@/features/inventory/components/reorder-sheet", () => ({ default: ({ items }: { items: { sku: string }[] }) => <div role="dialog">Reorder {items.map((i) => i.sku).join(",")}</div> }));
vi.mock("@/features/inventory/hooks", () => ({ useInventoryList: vi.fn() }));
vi.mock("@/features/inventory/insights", async (orig) => ({ ...(await orig<typeof import("@/features/inventory/insights")>()), useInventoryInsights: vi.fn() }));

const low = (sku: string, available: string) => ({ product_id: sku, sku, name: `Item ${sku}`, unit: "BAG", cost_price: "100.00", on_hand: available, reserved: "0.00", available, reorder_level: "10.00", suggested_quantity: "18.00", supplier: null });
const ok = { isPending: false, isLoading: false, isFetching: false, error: null, refetch: vi.fn() };

beforeEach(() => {
  vi.mocked(useInventoryList).mockReturnValue({ ...ok, data: { inventory: [{ id: "i1", product: { id: "CEM", sku: "CEM", name: "OPC cement", unit: "BAG" }, warehouse: { id: "w1", code: "MAIN", name: "Main godown" }, quantity: "12", reserved_quantity: "2", available_quantity: "10" }], pagination: { page: 1, total_pages: 1, total_items: 1, has_next: false, has_previous: false } } } as never);
  vi.mocked(useInventoryInsights).mockReturnValue({ ...ok, data: { as_of: "", warehouse_id: null, dead_days: 90, summary: { stock_value: "656000", products: 4, in_stock: 3, out_of_stock: 1, low_stock: 2, dead_stock: 1, dead_stock_value: "2000", unvalued_products: 0 }, by_warehouse: [], low_stock: [low("CEM", "8.00"), low("SND", "0.00")], dead_stock: [] } } as never);
});

describe("Stock screen", () => {
  it("shows KPI cards and marks low items in the stock list", () => {
    render(<InventoryPage />);
    expect(screen.getByText("₹6.6L")).toBeInTheDocument();
    expect(screen.getByText("OPC cement")).toBeInTheDocument();
    expect(screen.getByText("Low")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Adjust OPC cement in Main godown" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("Adjusting");
  });
  it("selects low-stock items and opens the reorder sheet for them", () => {
    render(<InventoryPage />);
    fireEvent.click(screen.getByRole("button", { name: "Show low stock" }));
    expect(screen.getByText("Out")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create draft PO" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Select Item SND" }));
    expect(screen.getByText("1 selected")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Create draft PO" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("Reorder SND");
  });
});

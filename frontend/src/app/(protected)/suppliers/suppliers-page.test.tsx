import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, fireEvent, render, screen } from "@testing-library/react";
import SuppliersPage from "./page";
import { useSupplierList } from "@/features/suppliers/hooks";

vi.mock("@/features/auth/auth-context", () => ({ useAuth: () => ({ authentication: { role: { permissions: ["suppliers.read", "suppliers.update"] } } }) }));
vi.mock("@/features/suppliers/components/supplier-dialog", () => ({ default: ({ open, supplierId }: { open: boolean; supplierId: string | null }) => (open ? <div role="dialog">Editing {supplierId}</div> : null) }));
vi.mock("@/features/suppliers/hooks", () => ({
  useSupplierList: vi.fn(),
  useActivateSupplier: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeactivateSupplier: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

const customer = { id: "c1", code: "CUS-1", name: "Sharma Traders", email: null, phone: "98765 43210", gstin: "27ABCDE1234F1Z5", city: "Pune", state: "Maharashtra", country: "India", is_active: true };

beforeEach(() => {
  vi.mocked(useSupplierList).mockReturnValue({ data: { suppliers: [customer], pagination: { page: 1, total_pages: 1, total_items: 1, has_next: false, has_previous: false } }, isPending: false, isFetching: false, error: null, refetch: vi.fn() } as never);
});

describe("Suppliers list", () => {
  it("shows a compact row and hides create for roles without suppliers.create", () => {
    render(<SuppliersPage />);
    expect(screen.getByText("Sharma Traders")).toBeInTheDocument();
    expect(screen.getByText("CUS-1 · 98765 43210 · 27ABCDE1234F1Z5")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "New supplier" })).not.toBeInTheDocument();
  });

  it("opens WhatsApp with the country code and edits on row tap", () => {
    const open = vi.spyOn(window, "open").mockReturnValue(null);
    render(<SuppliersPage />);
    fireEvent.click(screen.getByRole("button", { name: "WhatsApp Sharma Traders" }));
    expect(open).toHaveBeenCalledWith("https://wa.me/919876543210", "_blank", "noopener,noreferrer");
    fireEvent.click(screen.getByRole("button", { name: "Open Sharma Traders" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("Editing c1");
  });

  it("debounces search before querying", () => {
    vi.useFakeTimers();
    render(<SuppliersPage />);
    fireEvent.change(screen.getByLabelText("Search suppliers"), { target: { value: "shar" } });
    const lastSearch = () => vi.mocked(useSupplierList).mock.calls.at(-1)?.[0]?.search;
    expect(lastSearch()).toBeUndefined();
    act(() => { vi.advanceTimersByTime(350); });
    expect(lastSearch()).toBe("shar");
    vi.useRealTimers();
  });
});

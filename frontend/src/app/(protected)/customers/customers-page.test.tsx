import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, fireEvent, render, screen } from "@testing-library/react";
import CustomersPage from "./page";
import { useCustomerList } from "@/features/customers/hooks";

vi.mock("@/features/auth/auth-context", () => ({ useAuth: () => ({ authentication: { role: { permissions: ["customers.read", "customers.update"] } } }) }));
vi.mock("@/features/customers/components/customer-dialog", () => ({ default: ({ open, customerId }: { open: boolean; customerId: string | null }) => (open ? <div role="dialog">Editing {customerId}</div> : null) }));
vi.mock("@/features/customers/hooks", () => ({
  useCustomerList: vi.fn(),
  useActivateCustomer: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeactivateCustomer: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

const customer = { id: "c1", code: "CUS-1", name: "Sharma Traders", email: null, phone: "98765 43210", gstin: "27ABCDE1234F1Z5", city: "Pune", state: "Maharashtra", country: "India", is_active: true };

beforeEach(() => {
  vi.mocked(useCustomerList).mockReturnValue({ data: { customers: [customer], pagination: { page: 1, total_pages: 1, total_items: 1, has_next: false, has_previous: false } }, isPending: false, isFetching: false, error: null, refetch: vi.fn() } as never);
});

describe("Customers list", () => {
  it("shows a compact row and hides create for roles without customers.create", () => {
    render(<CustomersPage />);
    expect(screen.getByText("Sharma Traders")).toBeInTheDocument();
    expect(screen.getByText("CUS-1 · 98765 43210 · 27ABCDE1234F1Z5")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "New customer" })).not.toBeInTheDocument();
  });

  it("opens WhatsApp with the country code and edits on row tap", () => {
    const open = vi.spyOn(window, "open").mockReturnValue(null);
    render(<CustomersPage />);
    fireEvent.click(screen.getByRole("button", { name: "WhatsApp Sharma Traders" }));
    expect(open).toHaveBeenCalledWith("https://wa.me/919876543210", "_blank", "noopener,noreferrer");
    fireEvent.click(screen.getByRole("button", { name: "Open Sharma Traders" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("Editing c1");
  });

  it("debounces search before querying", () => {
    vi.useFakeTimers();
    render(<CustomersPage />);
    fireEvent.change(screen.getByLabelText("Search customers"), { target: { value: "shar" } });
    const lastSearch = () => vi.mocked(useCustomerList).mock.calls.at(-1)?.[0]?.search;
    expect(lastSearch()).toBeUndefined();
    act(() => { vi.advanceTimersByTime(350); });
    expect(lastSearch()).toBe("shar");
    vi.useRealTimers();
  });
});

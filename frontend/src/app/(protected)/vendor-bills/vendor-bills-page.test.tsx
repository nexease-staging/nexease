import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import VendorBillsPage from "./page";
import { useVendorBill, useVendorBillList } from "@/features/vendor-bills/hooks";

vi.mock("@/features/auth/auth-context", () => ({ useAuth: () => ({ authentication: { role: { permissions: ["bills.read", "bills.record_payment"] } } }) }));
vi.mock("@/features/suppliers/hooks", () => ({ useSupplierList: () => ({ data: { suppliers: [] } }) }));
vi.mock("@/features/business/quick-purchase", () => ({ default: () => null }));
vi.mock("@/features/documents/components/document-row-actions", () => ({ useDocumentRowActions: () => ({ actionsFor: () => [], dialog: null }) }));
vi.mock("@/features/vendor-bills/components/vendor-bill-detail-dialog", () => ({ default: () => null }));
vi.mock("@/features/vendor-bills/components/vendor-bill-dialog", () => ({ default: () => null }));
vi.mock("@/features/vendor-bills/components/vendor-bill-payment-dialog", () => ({ default: ({ open, vendorBill }: { open: boolean; vendorBill: { bill_number: string } | null }) => (open ? <div role="dialog">Paying {vendorBill?.bill_number}</div> : null) }));
vi.mock("@/features/vendor-bills/hooks", () => ({ useVendorBillList: vi.fn(), useVendorBill: vi.fn() }));

const supplier = { id: "s1", code: "SUP-1", name: "Om Cement Depot", email: null, phone: null, gstin: null, city: null, state: null, country: null, is_active: true };
const bill = (id: string, status: string, due: string | null, balance: string) => ({ id, bill_number: `BILL-${id}`, supplier_invoice_number: "OC/77", purchase_order: null, supplier, status, bill_date: "2026-11-01", due_date: due, subtotal: "0", tax_amount: "0", discount_amount: "0", total_amount: "1000.00", amount_paid: "0", balance_due: balance, item_count: 1, created_at: null, updated_at: null });

beforeEach(() => {
  vi.mocked(useVendorBillList).mockReturnValue({ data: { vendor_bills: [bill("1", "POSTED", "2026-11-02", "1000.00"), bill("2", "PAID", "2026-11-02", "0.00")], pagination: { page: 1, total_pages: 1, total_items: 2, has_next: false, has_previous: false } }, isPending: false, isFetching: false, error: null, refetch: vi.fn() } as never);
  vi.mocked(useVendorBill).mockImplementation((id: string) => ({ data: { ...bill(id, "POSTED", null, "1000.00") }, error: null }) as never);
});

describe("Purchase bills list", () => {
  it("offers Pay only on unpaid posted bills and marks overdue ones", () => {
    render(<VendorBillsPage />);
    expect(screen.getByRole("button", { name: "Pay bill BILL-1" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Pay bill BILL-2" })).not.toBeInTheDocument();
    expect(screen.getByText("Overdue")).toBeInTheDocument();
    expect(screen.getByText("BILL-1 · Inv OC/77 · 1 Nov 2026")).toBeInTheDocument();
  });
  it("loads the bill and opens the payment dialog from the row", () => {
    render(<VendorBillsPage />);
    fireEvent.click(screen.getByRole("button", { name: "Pay bill BILL-1" }));
    expect(useVendorBill).toHaveBeenCalledWith("1", true);
    expect(screen.getByRole("dialog")).toHaveTextContent("Paying BILL-1");
  });
});

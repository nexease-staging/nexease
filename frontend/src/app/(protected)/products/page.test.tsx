import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import Page from "./page";
vi.mock("@/features/auth/auth-context", () => ({
  useAuth: () => ({
    authentication: {
      role: {
        permissions: ["products.read", "products.update", "inventory.read"],
      },
    },
  }),
}));
vi.mock("@/features/products/hooks", () => ({
  useActivateProduct: () => ({ isPending: false }),
  useDeactivateProduct: () => ({ isPending: false }),
  useProductList: () => ({
    data: {
      products: [
        {
          id: "p1",
          name: "Quick item",
          sku: "Q1",
          category: { name: "Goods" },
          unit: "PCS",
          cost_price: "0",
          selling_price: "10",
          is_active: true,
          item_type: "goods",
        },
      ],
      pagination: {
        page: 1,
        page_size: 25,
        total_items: 1,
        total_pages: 1,
        has_next: false,
        has_previous: false,
      },
    },
    isLoading: false,
    refetch: vi.fn(),
  }),
}));
vi.mock("@tanstack/react-query", () => ({
  useQuery: () => ({ data: { quantities: { p1: "-5" } } }),
}));
vi.mock("@/features/products/components/product-dialog", () => ({
  default: () => null,
}));
vi.mock("@/features/products/components/reorder-level", () => ({
  default: () => <div role="dialog" aria-label="Reorder alert" />,
}));
it("shows negative product stock and exposes the reorder control in the table", () => {
  render(<Page />);
  expect(screen.getByText("-5")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Reorder" }));
  expect(
    screen.getByRole("dialog", { name: "Reorder alert" }),
  ).toBeInTheDocument();
});

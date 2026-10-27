import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";

import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import SalesOrderProductSearch
  from "@/features/sales-orders/components/sales-order-product-search";

const mockUseProductList =
  vi.fn();

vi.mock(
  "@/features/products/hooks",
  () => ({
    useProductList: (
      ...args: unknown[]
    ) =>
      mockUseProductList(
        ...args,
      ),
  }),
);

const product = {
  id: "product-1",
  sku: "SKU-001",
  name: "Test Product",
  category: {
    id: "category-1",
    code: "CAT-001",
    name: "Test Category",
  },
  brand: "Test Brand",
  unit: "piece",
  cost_price: "80.00",
  selling_price: "125.00",
  barcode: "1234567890",
  is_active: true,
};

interface RenderSearchOptions {
  value?: string;
  searchValue?: string;
  canCreateProduct?: boolean;
}

function renderSearch({
  value = "",
  searchValue = "",
  canCreateProduct = true,
}: RenderSearchOptions = {}) {
  const onSearchChange =
    vi.fn();

  const onSelect =
    vi.fn();

  const onClear =
    vi.fn();

  const onCreate =
    vi.fn();

  render(
    <SalesOrderProductSearch
      value={value}
      searchValue={searchValue}
      canCreateProduct={
        canCreateProduct
      }
      onSearchChange={
        onSearchChange
      }
      onSelect={onSelect}
      onClear={onClear}
      onCreate={onCreate}
    />,
  );

  return {
    onSearchChange,
    onSelect,
    onClear,
    onCreate,
  };
}

describe(
  "SalesOrderProductSearch",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      mockUseProductList
        .mockReturnValue({
          data: {
            products: [],
          },
          isFetching: false,
        });
    });

    it(
      "does not enable product search below three characters",
      () => {
        renderSearch({
          searchValue: "AB",
        });

        expect(
          mockUseProductList,
        ).toHaveBeenCalledWith(
          {
            page: 1,
            page_size: 10,
            search: undefined,
            is_active: true,
            sort: "name",
          },
          false,
        );

        fireEvent.focus(
          screen.getByPlaceholderText(
            "Search product name, SKU, brand or barcode",
          ),
        );

        expect(
          screen.getByText(
            "Type at least 3 characters to search.",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "enables product search at three characters",
      () => {
        renderSearch({
          searchValue: "SKU",
        });

        expect(
          mockUseProductList,
        ).toHaveBeenCalledWith(
          {
            page: 1,
            page_size: 10,
            search: "SKU",
            is_active: true,
            sort: "name",
          },
          true,
        );
      },
    );

    it(
      "trims product search before querying",
      () => {
        renderSearch({
          searchValue:
            "  SKU-001  ",
        });

        expect(
          mockUseProductList,
        ).toHaveBeenCalledWith(
          {
            page: 1,
            page_size: 10,
            search: "SKU-001",
            is_active: true,
            sort: "name",
          },
          true,
        );
      },
    );

    it(
      "shows searching state",
      () => {
        mockUseProductList
          .mockReturnValue({
            data: undefined,
            isFetching: true,
          });

        renderSearch({
          searchValue: "SKU",
        });

        fireEvent.focus(
          screen.getByPlaceholderText(
            "Search product name, SKU, brand or barcode",
          ),
        );

        expect(
          screen.getByText(
            "Searching...",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "renders matching products",
      () => {
        mockUseProductList
          .mockReturnValue({
            data: {
              products: [
                product,
              ],
            },
            isFetching: false,
          });

        renderSearch({
          searchValue: "Test",
        });

        fireEvent.focus(
          screen.getByPlaceholderText(
            "Search product name, SKU, brand or barcode",
          ),
        );

        expect(
          screen.getByText(
            "SKU-001 — Test Product",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Test Brand · 1234567890 · piece",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "returns the selected product",
      () => {
        mockUseProductList
          .mockReturnValue({
            data: {
              products: [
                product,
              ],
            },
            isFetching: false,
          });

        const {
          onSelect,
        } = renderSearch({
          searchValue: "Test",
        });

        fireEvent.focus(
          screen.getByPlaceholderText(
            "Search product name, SKU, brand or barcode",
          ),
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                /SKU-001 — Test Product/i,
            },
          ),
        );

        expect(
          onSelect,
        ).toHaveBeenCalledTimes(
          1,
        );

        expect(
          onSelect,
        ).toHaveBeenCalledWith(
          product,
        );
      },
    );

    it(
      "shows empty state when no products match",
      () => {
        renderSearch({
          searchValue:
            "ZZZNOTFOUND999",
          canCreateProduct: false,
        });

        fireEvent.focus(
          screen.getByPlaceholderText(
            "Search product name, SKU, brand or barcode",
          ),
        );

        expect(
          screen.getByText(
            "No matching products found.",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "shows create action when product creation is permitted",
      () => {
        const {
          onCreate,
        } = renderSearch({
          searchValue:
            "New Product",
          canCreateProduct: true,
        });

        fireEvent.focus(
          screen.getByPlaceholderText(
            "Search product name, SKU, brand or barcode",
          ),
        );

        const createButton =
          screen.getByRole(
            "button",
            {
              name:
                'Create "New Product"',
            },
          );

        expect(
          createButton,
        ).toBeInTheDocument();

        fireEvent.click(
          createButton,
        );

        expect(
          onCreate,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );

    it(
      "hides create action without products.create permission",
      () => {
        renderSearch({
          searchValue:
            "New Product",
          canCreateProduct: false,
        });

        fireEvent.focus(
          screen.getByPlaceholderText(
            "Search product name, SKU, brand or barcode",
          ),
        );

        expect(
          screen.queryByRole(
            "button",
            {
              name:
                'Create "New Product"',
            },
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByText(
            "No matching products found.",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "forwards search input changes",
      () => {
        const {
          onSearchChange,
        } = renderSearch();

        fireEvent.change(
          screen.getByPlaceholderText(
            "Search product name, SKU, brand or barcode",
          ),
          {
            target: {
              value: "ABC",
            },
          },
        );

        expect(
          onSearchChange,
        ).toHaveBeenCalledWith(
          "ABC",
        );
      },
    );

    it(
      "clears the selected product",
      () => {
        const {
          onClear,
        } = renderSearch({
          value:
            "SKU-001 — Test Product",
          searchValue:
            "SKU-001 — Test Product",
        });

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Clear selection",
            },
          ),
        );

        expect(
          onClear,
        ).toHaveBeenCalledTimes(
          1,
        );
      },
    );
  },
);
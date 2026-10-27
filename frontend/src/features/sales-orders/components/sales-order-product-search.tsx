"use client";

import {
  SearchCombobox,
} from "@/components/ui/search-combobox";

import {
  useProductList,
} from "@/features/products/hooks";

import type {
  ProductSummary,
} from "@/features/products/types";

interface SalesOrderProductSearchProps {
  value: string;
  searchValue: string;
  disabled?: boolean;
  canCreateProduct: boolean;
  onSearchChange: (
    value: string,
  ) => void;
  onSelect: (
    product: ProductSummary,
  ) => void;
  onClear: () => void;
  onCreate: () => void;
}

export default function SalesOrderProductSearch({
  value,
  searchValue,
  disabled = false,
  canCreateProduct,
  onSearchChange,
  onSelect,
  onClear,
  onCreate,
}: SalesOrderProductSearchProps) {
  const normalizedSearch =
    searchValue.trim();

  const productQuery =
    useProductList(
      {
        page: 1,
        page_size: 10,
        search:
          normalizedSearch.length >= 3
            ? normalizedSearch
            : undefined,
        is_active: true,
        sort: "name",
      },
      normalizedSearch.length >= 3,
    );

  const products =
    productQuery.data
      ?.products
    ??
    [];

  const options =
    products.map(
      (product) => ({
        id: product.id,
        label:
          `${product.sku} — ${product.name}`,
        description:
          [
            product.brand,
            product.barcode,
            product.unit,
          ]
            .filter(Boolean)
            .join(" · "),
      }),
    );

  return (
    <SearchCombobox
      value={value}
      searchValue={searchValue}
      options={options}
      placeholder="Search product name, SKU, brand or barcode"
      minimumSearchLength={3}
      disabled={disabled}
      isLoading={
        normalizedSearch.length >= 3
        &&
        productQuery.isFetching
      }
      emptyMessage="No matching products found."
      canCreate={
        canCreateProduct
        &&
        normalizedSearch.length >= 3
      }
      createLabel={
        `Create "${normalizedSearch}"`
      }
      onCreate={onCreate}
      onSearchChange={
        onSearchChange
      }
      onSelect={(option) => {
        const product =
          products.find(
            (candidate) =>
              candidate.id
              ===
              option.id,
          );

        if (product) {
          onSelect(product);
        }
      }}
      onClear={onClear}
    />
  );
}
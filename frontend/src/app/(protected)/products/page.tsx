"use client";
import {confirmAction} from "@/components/nex-feedback";
import SearchSelect from "@/components/search-select";


import {
  useMemo,
  useState,
} from "react";

import {
  Package,
  Pencil,
  Plus,
  Power,
  PowerOff,
  RefreshCw,
  Search,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import ProductDialog from "@/features/products/components/product-dialog";

import {
  useActivateProduct,
  useDeactivateProduct,
  useProductList,
} from "@/features/products/hooks";

import type {
  ProductSummary,
} from "@/features/products/types";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

function formatCurrency(
  value: string,
): string {
  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return value;
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(amount);
}

export default function ProductsPage() {
  const {
    authentication,
  } = useAuth();

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    activeFilter,
    setActiveFilter,
  ] = useState<
    "all" | "active" | "inactive"
  >("all");

  const [
    page,
    setPage,
  ] = useState(1);

  const [
    productDialogOpen,
    setProductDialogOpen,
  ] = useState(false);

  const [
    editingProductId,
    setEditingProductId,
  ] = useState<string | null>(
    null,
  );

  const [
    actionError,
    setActionError,
  ] = useState<string | null>(
    null,
  );

  const activateMutation =
    useActivateProduct();

  const deactivateMutation =
    useDeactivateProduct();

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const canRead = hasPermission(
    permissions,
    "products.read",
  );

  const canCreate = hasPermission(
    permissions,
    "products.create",
  );

  const canUpdate = hasPermission(
    permissions,
    "products.update",
  );

  const canDelete = hasPermission(
    permissions,
    "products.delete",
  );

  const listParameters = useMemo(
    () => ({
      page,
      page_size: 25,
      search:
        search.trim()
        ||
        undefined,
      is_active:
        activeFilter === "all"
          ? undefined
          : activeFilter === "active",
      sort: "name",
    }),
    [
      activeFilter,
      page,
      search,
    ],
  );

  const productQuery =
    useProductList(
      listParameters,
    );

  if (!authentication) {
    return null;
  }

  if (!canRead) {
    return (
      <section
        className="
          rounded-2xl border
          border-amber-200 bg-amber-50
          p-6
        "
      >
        <h1
          className="
            text-lg font-semibold
            text-amber-900
          "
        >
          Product access restricted
        </h1>

        <p
          className="
            mt-2 text-sm text-amber-800
          "
        >
          Your role does not include the
          products.read permission.
        </p>
      </section>
    );
  }

  const products =
    productQuery.data
      ?.products
    ??
    [];

  const pagination =
    productQuery.data
      ?.pagination;

  const actionPending =
    activateMutation.isPending
    ||
    deactivateMutation.isPending;

  function openCreateDialog(): void {
    setEditingProductId(
      null,
    );

    setProductDialogOpen(
      true,
    );
  }

  function openEditDialog(
    productId: string,
  ): void {
    setEditingProductId(
      productId,
    );

    setProductDialogOpen(
      true,
    );
  }

  async function activate(
    product: ProductSummary,
  ): Promise<void> {
    const confirmed =
      await confirmAction(
        (
          `Activate ${product.name}?`
          +
          "\n\nThe product will become "
          +
          "available for inventory operations."
        ),
      );

    if (!confirmed) {
      return;
    }

    setActionError(
      null,
    );

    try {
      await activateMutation.mutateAsync(
        product.id,
      );
    } catch (error) {
      setActionError(
        error instanceof Error
          ? error.message
          : "Unable to activate product.",
      );
    }
  }

  async function deactivate(
    product: ProductSummary,
  ): Promise<void> {
    const confirmed =
      await confirmAction(
        (
          `Deactivate ${product.name}?`
          +
          "\n\nThe product will remain in "
          +
          "historical records."
        ),
      );

    if (!confirmed) {
      return;
    }

    setActionError(
      null,
    );

    try {
      await deactivateMutation.mutateAsync(
        product.id,
      );
    } catch (error) {
      setActionError(
        error instanceof Error
          ? error.message
          : "Unable to deactivate product.",
      );
    }
  }

  return (
    <section className="space-y-6">
      <div
        className="
          flex flex-col gap-4
          sm:flex-row sm:items-center
          sm:justify-between
        "
      >
        <div>
          <div
            className="
              flex items-center gap-2
            "
          >
            <Package
              size={25}
              className="text-blue-600"
            />

            <h1
              className="
                text-2xl font-bold
                text-slate-900
              "
            >
              Products
            </h1>
          </div>

          <p
            className="
              mt-1 text-sm text-slate-600
            "
          >
            Manage product catalog, pricing,
            categories, and availability.
          </p>
        </div>

        <div
          className="
            flex flex-col gap-2
            sm:flex-row
          "
        >
          <button
            type="button"
            disabled={
              productQuery.isFetching
            }
            onClick={() => {
              void productQuery.refetch();
            }}
            className="
              inline-flex items-center
              justify-center gap-2
              rounded-lg border
              border-slate-300 bg-white
              px-4 py-2 text-sm
              font-semibold text-slate-700
              hover:bg-slate-50
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >
            <RefreshCw
              size={16}
              className={
                productQuery.isFetching
                  ? "animate-spin"
                  : undefined
              }
            />

            Refresh
          </button>

          {canCreate ? (
            <button title="New product"
              type="button"
              onClick={
                openCreateDialog
              }
              className="
                inline-flex items-center
                justify-center gap-2
                rounded-lg bg-blue-600
                px-4 py-2 text-sm
                font-semibold text-white
                hover:bg-blue-700
              "
            >
              <Plus size={17} /><span className="sr-only">New product</span></button>
          ) : null}
        </div>
      </div>

      <div
        className="nx-list-filters
          grid gap-4 rounded-2xl
          border border-slate-200
          bg-white p-4 shadow-sm
          md:grid-cols-[minmax(0,1fr)_240px]
        "
      >
        <label className="space-y-1.5">
          <span
            className="
              text-sm font-semibold
              text-slate-700
            "
          >
            Search
          </span>

          <div className="relative">
            <Search
              size={17}
              className="
                pointer-events-none
                absolute left-3 top-1/2
                -translate-y-1/2
                text-slate-400
              "
            />

            <input
              type="search"
              value={search}
              placeholder="Search SKU, name, brand or barcode"
              onChange={(event) => {
                setSearch(
                  event.target.value,
                );

                setPage(1);
              }}
              className="
                h-10 w-full rounded-lg
                border border-slate-300
                bg-white pl-9 pr-3
                text-sm text-slate-900
                placeholder:text-slate-400
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            />
          </div>
        </label>

        <label className="space-y-1.5">
          <span
            className="
              text-sm font-semibold
              text-slate-700
            "
          >
            Status
          </span>

          <SearchSelect
            value={activeFilter}
            onChange={(event) => {
              setActiveFilter(
                event.target.value as (
                  "all"
                  |
                  "active"
                  |
                  "inactive"
                ),
              );

              setPage(1);
            }}
            className="
              h-10 w-full rounded-lg
              border border-slate-300
              bg-white px-3 text-sm
              text-slate-900 outline-none
              focus:border-blue-500
              focus:ring-2
              focus:ring-blue-100
            "
          >
            <option value="all">
              All products
            </option>

            <option value="active">
              Active products
            </option>

            <option value="inactive">
              Inactive products
            </option>
          </SearchSelect>
        </label>
      </div>

      {actionError ? (
        <div
          className="
            rounded-xl border
            border-red-200 bg-red-50
            px-4 py-3 text-sm
            text-red-700
          "
        >
          {actionError}
        </div>
      ) : null}

      <div
        className="
          overflow-hidden rounded-2xl
          border border-slate-200
          bg-white shadow-sm
        "
      >
        {productQuery.isPending ? (
          <div
            className="
              flex min-h-72 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading products…
          </div>
        ) : productQuery.isError ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              gap-3 p-6 text-center
            "
          >
            <p
              className="
                text-sm font-medium
                text-red-700
              "
            >
              {productQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void productQuery.refetch();
              }}
              className="
                rounded-lg bg-slate-900
                px-4 py-2 text-sm
                font-semibold text-white
                hover:bg-slate-700
              "
            >
              Try again
            </button>
          </div>
        ) : products.length === 0 ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              p-6 text-center
            "
          >
            <Package
              size={36}
              className="text-slate-300"
            />

            <h2
              className="
                mt-3 font-semibold
                text-slate-900
              "
            >
              No products found
            </h2>

            <p
              className="
                mt-1 max-w-md text-sm
                text-slate-500
              "
            >
              Change the filters or create
              your first catalog product.
            </p>

            {canCreate ? (
              <button title="Create product"
                type="button"
                onClick={
                  openCreateDialog
                }
                className="
                  mt-4 inline-flex
                  items-center gap-2
                  rounded-lg bg-blue-600
                  px-4 py-2 text-sm
                  font-semibold text-white
                  hover:bg-blue-700
                "
              >
                <Plus size={16} /><span className="sr-only">Create product</span></button>
            ) : null}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table
              className="
                min-w-full divide-y
                divide-slate-200
              "
            >
              <thead className="bg-slate-50">
                <tr>
                  {[
                    "SKU",
                    "Product",
                    "Category",
                    "Unit",
                    "Cost price",
                    "Selling price",
                    "Status",
                    "Actions",
                  ].map(
                    (heading) => (
                      <th
                        key={heading}
                        scope="col"
                        className="
                          whitespace-nowrap
                          px-4 py-3 text-left
                          text-xs font-semibold
                          uppercase tracking-wide
                          text-slate-500
                        "
                      >
                        {heading}
                      </th>
                    ),
                  )}
                </tr>
              </thead>

              <tbody
                className="
                  divide-y divide-slate-100
                "
              >
                {products.map(
                  (product) => (
                    <tr
                      key={product.id}
                      className="
                        hover:bg-slate-50
                      "
                    >
                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          font-bold text-slate-900
                        "
                      >
                        {product.sku}
                      </td>

                      <td
                        className="
                          px-4 py-4 text-sm
                          text-slate-700
                        "
                      >
                        <p
                          className="
                            font-semibold
                            text-slate-900
                          "
                        >
                          {product.name}<span className="block text-xs font-normal text-slate-500">{product.item_type==="service"?"Service":"Goods"} · HSN/SAC: {product.hsn_code||"Not set"}</span>
                        </p>

                        <p
                          className="
                            mt-0.5 text-xs
                            text-slate-500
                          "
                        >
                          {product.brand
                            ??
                            "No brand"}
                        </p>
                      </td>

                      <td
                        className="
                          px-4 py-4 text-sm
                          text-slate-700
                        "
                      >
                        {product.category.name}
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          text-slate-600
                        "
                      >
                        {product.unit}
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          text-slate-700
                        "
                      >
                        {
                          product.cost_price == null ? "Restricted" : formatCurrency(product.cost_price)
                        }
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          font-semibold
                          text-slate-900
                        "
                      >
                        {
                          formatCurrency(
                            product
                              .selling_price,
                          )
                        }
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                        "
                      >
                        <span
                          className={`
                            inline-flex rounded-full
                            border px-2.5 py-1
                            text-xs font-semibold
                            ${
                              product.is_active
                                ? (
                                  "border-emerald-200 "
                                  +
                                  "bg-emerald-50 "
                                  +
                                  "text-emerald-700"
                                )
                                : (
                                  "border-slate-200 "
                                  +
                                  "bg-slate-100 "
                                  +
                                  "text-slate-600"
                                )
                            }
                          `}
                        >
                          {
                            product.is_active
                              ? "Active"
                              : "Inactive"
                          }
                        </span>
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                        "
                      >
                        <div
                          className="
                            flex items-center gap-2
                          "
                        >
                          {canUpdate
                          && product.is_active ? (
                            <button
                              type="button"
                              title="Edit product"
                              aria-label={
                                `Edit ${product.name}`
                              }
                              disabled={
                                actionPending
                              }
                              onClick={() => {
                                openEditDialog(
                                  product.id,
                                );
                              }}
                              className="
                                rounded-lg border
                                border-slate-300
                                bg-white p-2
                                text-slate-600
                                hover:bg-slate-50
                                hover:text-blue-700
                                disabled:opacity-40
                              "
                            >
                              <Pencil size={16} />
                            </button>
                          ) : null}

                          {canUpdate
                          && !product.is_active ? (
                            <button
                              type="button"
                              title="Activate product"
                              aria-label={
                                `Activate ${product.name}`
                              }
                              disabled={
                                actionPending
                              }
                              onClick={() => {
                                void activate(
                                  product,
                                );
                              }}
                              className="
                                rounded-lg border
                                border-emerald-200
                                bg-emerald-50 p-2
                                text-emerald-700
                                hover:bg-emerald-100
                                disabled:opacity-40
                              "
                            >
                              <Power size={16} />
                            </button>
                          ) : null}

                          {canDelete
                          && product.is_active ? (
                            <button
                              type="button"
                              title="Deactivate product"
                              aria-label={
                                `Deactivate ${product.name}`
                              }
                              disabled={
                                actionPending
                              }
                              onClick={() => {
                                void deactivate(
                                  product,
                                );
                              }}
                              className="
                                rounded-lg border
                                border-red-200
                                bg-red-50 p-2
                                text-red-700
                                hover:bg-red-100
                                disabled:opacity-40
                              "
                            >
                              <PowerOff size={16} />
                            </button>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}

        {pagination ? (
          <div
            className="
              flex flex-col gap-3
              border-t border-slate-200
              px-4 py-3
              sm:flex-row sm:items-center
              sm:justify-between
            "
          >
            <p className="text-sm text-slate-600">
              Page {pagination.page} of{" "}
              {pagination.total_pages || 1}
              {" · "}
              {pagination.total_items} products
            </p>

            <div className="flex gap-2">
              <button
                type="button"
                disabled={
                  !pagination.has_previous
                  ||
                  productQuery.isFetching
                }
                onClick={() => {
                  setPage(
                    (current) =>
                      Math.max(
                        1,
                        current - 1,
                      ),
                  );
                }}
                className="
                  rounded-lg border
                  border-slate-300 bg-white
                  px-3 py-1.5 text-sm
                  font-semibold text-slate-700
                  hover:bg-slate-50
                  disabled:opacity-40
                "
              >
                Previous
              </button>

              <button
                type="button"
                disabled={
                  !pagination.has_next
                  ||
                  productQuery.isFetching
                }
                onClick={() => {
                  setPage(
                    (current) =>
                      current + 1,
                  );
                }}
                className="
                  rounded-lg border
                  border-slate-300 bg-white
                  px-3 py-1.5 text-sm
                  font-semibold text-slate-700
                  hover:bg-slate-50
                  disabled:opacity-40
                "
              >
                Next
              </button>
            </div>
          </div>
        ) : null}
      </div>

      <ProductDialog
        open={
          productDialogOpen
        }
        productId={
          editingProductId
        }
        onClose={() => {
          setProductDialogOpen(
            false,
          );

          setEditingProductId(
            null,
          );
        }}
      />
    </section>
  );
}
"use client";
import SearchSelect from "@/components/search-select";


import {
  useMemo,
  useState,
} from "react";

import {
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Tags,
} from "lucide-react";

import CategoryDialog from "@/features/categories/components/category-dialog";

import {
  useActivateCategory,
  useCategories,
  useDeactivateCategory,
} from "@/features/categories/hooks";

import type {
  CategorySummary,
} from "@/features/categories/types";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  hasPermission,
} from "@/lib/authorization/permissions";


export default function CategoriesPage() {
  const {
    authentication,
  } = useAuth();

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const canRead =
    hasPermission(
      permissions,
      "products.read",
    );

  const canCreate =
    hasPermission(
      permissions,
      "products.create",
    );

  const canUpdate =
    hasPermission(
      permissions,
      "products.update",
    );

  const canDeactivate =
    hasPermission(
      permissions,
      "products.delete",
    );

  const categoryQuery =
    useCategories();

  const activateMutation =
    useActivateCategory();

  const deactivateMutation =
    useDeactivateCategory();

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    activeFilter,
    setActiveFilter,
  ] = useState<
    "all"
    |
    "active"
    |
    "inactive"
  >("all");

  const [
    dialogOpen,
    setDialogOpen,
  ] = useState(false);

  const [
    selectedCategoryId,
    setSelectedCategoryId,
  ] = useState<
    string | null
  >(null);

  const [
    actionError,
    setActionError,
  ] = useState<
    string | null
  >(null);


  const categories =
    useMemo(
      () => {
        const source =
          categoryQuery.data
            ?.categories
          ??
          [];

        const normalizedSearch =
          search
            .trim()
            .toLowerCase();

        return source.filter(
          (category) => {
            if (
              activeFilter
              ===
              "active"
              &&
              !category.is_active
            ) {
              return false;
            }

            if (
              activeFilter
              ===
              "inactive"
              &&
              category.is_active
            ) {
              return false;
            }

            if (!normalizedSearch) {
              return true;
            }

            return (
              category.name
                .toLowerCase()
                .includes(
                  normalizedSearch,
                )
              ||
              (
                category.description
                ??
                ""
              )
                .toLowerCase()
                .includes(
                  normalizedSearch,
                )
            );
          },
        );
      },
      [
        activeFilter,
        categoryQuery.data,
        search,
      ],
    );


  function openCreateDialog(): void {
    setSelectedCategoryId(
      null,
    );

    setDialogOpen(
      true,
    );
  }


  function openEditDialog(
    category: CategorySummary,
  ): void {
    setSelectedCategoryId(
      category.id,
    );

    setDialogOpen(
      true,
    );
  }


  function closeDialog(): void {
    setDialogOpen(
      false,
    );

    setSelectedCategoryId(
      null,
    );
  }


  async function activate(
    category: CategorySummary,
  ): Promise<void> {
    const confirmed =
      window.confirm(
        (
          `Activate ${category.name}?`
          +
          "\n\nThe category will become "
          +
          "available for product use again."
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
        category.id,
      );
    } catch (error) {
      setActionError(
        error instanceof Error
          ? error.message
          : "Unable to activate category.",
      );
    }
  }


  async function deactivate(
    category: CategorySummary,
  ): Promise<void> {
    const confirmed =
      window.confirm(
        (
          `Deactivate ${category.name}?`
          +
          "\n\nThe category will no longer "
          +
          "be available for new product use."
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
        category.id,
      );
    } catch (error) {
      setActionError(
        error instanceof Error
          ? error.message
          : "Unable to deactivate category.",
      );
    }
  }


  if (!canRead) {
    return (
      <section
        className="
          rounded-2xl border
          border-slate-200 bg-white
          p-6 shadow-sm
        "
      >
        <h1
          className="
            text-xl font-bold
            text-slate-900
          "
        >
          Categories
        </h1>

        <p
          className="
            mt-2 text-sm
            text-slate-600
          "
        >
          You do not have permission
          to view product categories.
        </p>
      </section>
    );
  }


  const actionPending =
    activateMutation.isPending
    ||
    deactivateMutation.isPending;


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
            <Tags
              size={25}
              className="text-blue-600"
            />

            <h1
              className="
                text-2xl font-bold
                text-slate-900
              "
            >
              Categories
            </h1>
          </div>

          <p
            className="
              mt-1 text-sm text-slate-600
            "
          >
            Manage categories used to
            organize products and inventory.
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
              categoryQuery.isFetching
            }
            onClick={() => {
              void categoryQuery.refetch();
            }}
            className="
              inline-flex items-center
              justify-center gap-2
              rounded-lg border
              border-slate-300 bg-white
              px-4 py-2 text-sm
              font-semibold text-slate-700
              hover:bg-slate-50
              disabled:opacity-50
            "
          >
            <RefreshCw
              size={16}
              className={
                categoryQuery.isFetching
                  ? "animate-spin"
                  : undefined
              }
            />

            Refresh
          </button>

          {canCreate ? (
            <button
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
              <Plus size={17} />

              New category
            </button>
          ) : null}
        </div>
      </div>

      <div
        className="
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
              placeholder={
                "Search name or description"
              }
              onChange={(event) => {
                setSearch(
                  event.target.value,
                );
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
              All categories
            </option>

            <option value="active">
              Active categories
            </option>

            <option value="inactive">
              Inactive categories
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
        {categoryQuery.isPending ? (
          <div
            className="
              flex min-h-72 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading categories...
          </div>
        ) : categoryQuery.isError ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              gap-3 p-6 text-center
            "
          >
            <p className="text-sm text-red-700">
              {categoryQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void categoryQuery.refetch();
              }}
              className="
                rounded-lg bg-slate-900
                px-4 py-2 text-sm
                font-semibold text-white
              "
            >
              Try again
            </button>
          </div>
        ) : categories.length === 0 ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              p-6 text-center
            "
          >
            <Tags
              size={36}
              className="text-slate-300"
            />

            <h2
              className="
                mt-3 font-semibold
                text-slate-900
              "
            >
              No categories found
            </h2>

            <p
              className="
                mt-1 max-w-md text-sm
                text-slate-500
              "
            >
              {search
              || activeFilter !== "all"
                ? (
                    "Change the search or "
                    +
                    "status filter."
                  )
                : (
                    "Create your first category "
                    +
                    "before adding products."
                  )}
            </p>

            {canCreate
            && !search
            && activeFilter === "all" ? (
              <button
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
                <Plus size={16} />

                Create category
              </button>
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
                    "Category",
                    "Description",
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
                  bg-white
                "
              >
                {categories.map(
                  (category) => (
                    <tr
                      key={category.id}
                      className="
                        hover:bg-slate-50/70
                      "
                    >
                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                        "
                      >
                        <div
                          className="
                            font-semibold
                            text-slate-900
                          "
                        >
                          {category.name}
                        </div>
                      </td>

                      <td
                        className="
                          max-w-md px-4 py-4
                          text-sm text-slate-600
                        "
                      >
                        {category.description
                          ||
                          (
                            <span
                              className="
                                text-slate-400
                              "
                            >
                              No description
                            </span>
                          )}
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                        "
                      >
                        <span
                          className={
                            category.is_active
                              ? (
                                  "inline-flex rounded-full "
                                  +
                                  "bg-emerald-50 px-2.5 "
                                  +
                                  "py-1 text-xs font-semibold "
                                  +
                                  "text-emerald-700"
                                )
                              : (
                                  "inline-flex rounded-full "
                                  +
                                  "bg-slate-100 px-2.5 "
                                  +
                                  "py-1 text-xs font-semibold "
                                  +
                                  "text-slate-600"
                                )
                          }
                        >
                          {category.is_active
                            ? "Active"
                            : "Inactive"}
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
                          {canUpdate ? (
                            <button
                              type="button"
                              onClick={() => {
                                openEditDialog(
                                  category,
                                );
                              }}
                              className="
                                inline-flex items-center
                                gap-1.5 rounded-lg
                                border border-slate-300
                                bg-white px-3 py-1.5
                                text-xs font-semibold
                                text-slate-700
                                hover:bg-slate-50
                              "
                            >
                              <Pencil size={14} />

                              Edit
                            </button>
                          ) : null}

                          {category.is_active
                          && canDeactivate ? (
                            <button
                              type="button"
                              disabled={
                                actionPending
                              }
                              onClick={() => {
                                void deactivate(
                                  category,
                                );
                              }}
                              className="
                                rounded-lg border
                                border-red-200 bg-white
                                px-3 py-1.5 text-xs
                                font-semibold text-red-700
                                hover:bg-red-50
                                disabled:opacity-50
                              "
                            >
                              Deactivate
                            </button>
                          ) : null}

                          {!category.is_active
                          && canUpdate ? (
                            <button
                              type="button"
                              disabled={
                                actionPending
                              }
                              onClick={() => {
                                void activate(
                                  category,
                                );
                              }}
                              className="
                                rounded-lg border
                                border-emerald-200
                                bg-white px-3 py-1.5
                                text-xs font-semibold
                                text-emerald-700
                                hover:bg-emerald-50
                                disabled:opacity-50
                              "
                            >
                              Activate
                            </button>
                          ) : null}

                          {!canUpdate
                          && !canDeactivate ? (
                            <span
                              className="
                                text-xs text-slate-400
                              "
                            >
                              View only
                            </span>
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
      </div>

      <CategoryDialog
        open={dialogOpen}
        categoryId={
          selectedCategoryId
        }
        onClose={
          closeDialog
        }
      />
    </section>
  );
}
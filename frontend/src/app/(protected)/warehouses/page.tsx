"use client";
import SearchSelect from "@/components/search-select";


import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Pencil,
  Plus,
  Power,
  PowerOff,
  RefreshCw,
  Search,
  Warehouse,
} from "lucide-react";

import WarehouseLifecycleDialog from "@/features/warehouses/components/warehouse-lifecycle-dialog";


import {
  useAuth,
} from "@/features/auth/auth-context";

import WarehouseFormDialog from "@/features/warehouses/components/warehouse-form-dialog";

import {
  useWarehouse,
  useWarehouseList,
} from "@/features/warehouses/hooks";

import type {
    WarehouseSummary,
} from "@/features/warehouses/types";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

type StatusFilter =
  | "all"
  | "active"
  | "inactive";

export default function WarehousesPage() {
  const {
    authentication,
  } = useAuth();

  const [
    searchInput,
    setSearchInput,
  ] = useState("");

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    statusFilter,
    setStatusFilter,
  ] = useState<StatusFilter>(
    "all",
  );

  const [
    page,
    setPage,
  ] = useState(1);

  const [
    formOpen,
    setFormOpen,
  ] = useState(false);

  const [
    selectedWarehouseId,
    setSelectedWarehouseId,
  ] = useState<string | null>(
    null,
  );

  const [
    lifecycleWarehouse,
    setLifecycleWarehouse,
  ] = useState<WarehouseSummary | null>(
    null,
  );

  useEffect(() => {
    const timeout = window.setTimeout(
      () => {
        setSearch(
          searchInput.trim(),
        );

        setPage(1);
      },
      300,
    );

    return () => {
      window.clearTimeout(
        timeout,
      );
    };
  }, [
    searchInput,
  ]);

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const canRead = hasPermission(
    permissions,
    "warehouses.read",
  );

  const canCreate = hasPermission(
    permissions,
    "warehouses.create",
  );

  const canUpdate = hasPermission(
    permissions,
    "warehouses.update",
  );

  const listParameters = useMemo(
    () => ({
      page,
      page_size: 10,
      search:
        search
        ||
        undefined,
      is_active:
        statusFilter === "all"
          ? undefined
          : statusFilter === "active",
      sort: "name",
    }),
    [
      page,
      search,
      statusFilter,
    ],
  );

  const warehouseQuery =
    useWarehouseList(
      listParameters,
    );

  const selectedWarehouseQuery =
    useWarehouse(
      selectedWarehouseId
      ??
      "",
      formOpen
      &&
      Boolean(
        selectedWarehouseId
      ),
    );

  function openCreateDialog(): void {
    setSelectedWarehouseId(
      null
    );

    setFormOpen(
      true
    );
  }

  function openEditDialog(
    warehouseId: string,
  ): void {
    setSelectedWarehouseId(
      warehouseId
    );

    setFormOpen(
      true
    );
  }

  function closeFormDialog(): void {
    setFormOpen(
      false
    );

    setSelectedWarehouseId(
      null
    );
  }

  function openLifecycleDialog(
    warehouse: WarehouseSummary,
  ): void {
    setLifecycleWarehouse(
      warehouse
    );
  }

  function closeLifecycleDialog(): void {
    setLifecycleWarehouse(
      null
    );
  }

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
          Warehouse access restricted
        </h1>

        <p
          className="
            mt-2 text-sm text-amber-800
          "
        >
          Your role does not include the
          warehouses.read permission.
        </p>
      </section>
    );
  }

  const warehouses =
    warehouseQuery.data
      ?.warehouses
    ??
    [];

  const pagination =
    warehouseQuery.data
      ?.pagination;

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
            <Warehouse
              className="text-blue-600"
              size={24}
            />

            <h1
              className="
                text-2xl font-bold
                text-slate-900
              "
            >
              Warehouses
            </h1>
          </div>

          <p
            className="
              mt-1 text-sm text-slate-600
            "
          >
            Manage storage locations for{" "}
            {
              authentication
                .organization
                .name
            }.
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
            onClick={() => {
              void warehouseQuery.refetch();
            }}
            disabled={
              warehouseQuery.isFetching
            }
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
                warehouseQuery.isFetching
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

              New warehouse
            </button>
          ) : null}
        </div>
      </div>

      <div
        className="
          grid gap-3 rounded-2xl
          border border-slate-200
          bg-white p-4 shadow-sm
          md:grid-cols-[1fr_200px]
        "
      >
        <label className="relative block">
          <span className="sr-only">
            Search warehouses
          </span>

          <Search
            size={18}
            className="
              pointer-events-none
              absolute left-3 top-1/2
              -translate-y-1/2
              text-slate-400
            "
          />

          <input
            type="search"
            value={searchInput}
            onChange={(event) => {
              setSearchInput(
                event.target.value,
              );
            }}
            placeholder={
              "Search name, code, city, state…"
            }
            className="
              h-10 w-full rounded-lg
              border border-slate-300
              bg-white pl-10 pr-3
              text-sm text-slate-900
              outline-none
              placeholder:text-slate-400
              focus:border-blue-500
              focus:ring-2
              focus:ring-blue-100
            "
          />
        </label>

        <label>
          <span className="sr-only">
            Filter by status
          </span>

          <SearchSelect
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(
                event.target
                  .value as StatusFilter,
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
              All statuses
            </option>

            <option value="active">
              Active
            </option>

            <option value="inactive">
              Inactive
            </option>
          </SearchSelect>
        </label>
      </div>

      <div
        className="
          overflow-hidden rounded-2xl
          border border-slate-200
          bg-white shadow-sm
        "
      >
        {warehouseQuery.isPending ? (
          <div
            className="
              flex min-h-64 items-center
              justify-center
              text-sm text-slate-500
            "
          >
            Loading warehouses…
          </div>
        ) : warehouseQuery.isError ? (
          <div
            className="
              flex min-h-64 flex-col
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
              {
                warehouseQuery
                  .error
                  .message
              }
            </p>

            <button
              type="button"
              onClick={() => {
                void warehouseQuery.refetch();
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
        ) : warehouses.length === 0 ? (
          <div
            className="
              flex min-h-64 flex-col
              items-center justify-center
              p-6 text-center
            "
          >
            <Warehouse
              size={34}
              className="text-slate-300"
            />

            <h2
              className="
                mt-3 font-semibold
                text-slate-900
              "
            >
              No warehouses found
            </h2>

            <p
              className="
                mt-1 text-sm text-slate-500
              "
            >
              Adjust the search or status
              filter to see more results.
            </p>

            {canCreate ? (
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

                Create warehouse
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
                    "Code",
                    "Warehouse",
                    "Location",
                    "Country",
                    "Status",
                    ...(
                      canUpdate
                        ? [
                            "Actions",
                          ]
                        : []
                    ),
                  ].map(
                    (heading) => (
                      <th
                        key={heading}
                        scope="col"
                        className="
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
                {warehouses.map(
                  (warehouse) => (
                    <tr
                      key={warehouse.id}
                      className="
                        hover:bg-slate-50
                      "
                    >
                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          font-semibold
                          text-slate-900
                        "
                      >
                        {warehouse.code}
                      </td>

                      <td
                        className="
                          px-4 py-4 text-sm
                          text-slate-700
                        "
                      >
                        {warehouse.name}
                      </td>

                      <td
                        className="
                          px-4 py-4 text-sm
                          text-slate-600
                        "
                      >
                        {[
                          warehouse.city,
                          warehouse.state,
                        ]
                          .filter(Boolean)
                          .join(", ")
                          ||
                          "—"}
                      </td>

                      <td
                        className="
                          px-4 py-4 text-sm
                          text-slate-600
                        "
                      >
                        {
                          warehouse.country
                          ||
                          "—"
                        }
                      </td>

                      <td className="px-4 py-4">
                        <span
                          className={
                            warehouse.is_active
                              ? (
                                "inline-flex rounded-full "
                                +
                                "bg-emerald-100 px-2.5 "
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
                          {
                            warehouse.is_active
                              ? "Active"
                              : "Inactive"
                          }
                        </span>
                      </td>

                      {canUpdate ? (
                        <td className="px-4 py-4">
                          <div
                            className="
                              flex items-center gap-2
                            "
                          >
                            <button
                              type="button"
                              onClick={() => {
                                openEditDialog(
                                  warehouse.id,
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

                            <button
                              type="button"
                              onClick={() => {
                                openLifecycleDialog(
                                  warehouse,
                                );
                              }}
                              className={
                                warehouse.is_active
                                  ? (
                                    "inline-flex items-center "
                                    +
                                    "gap-1.5 rounded-lg border "
                                    +
                                    "border-red-200 bg-white "
                                    +
                                    "px-3 py-1.5 text-xs "
                                    +
                                    "font-semibold text-red-700 "
                                    +
                                    "hover:bg-red-50"
                                  )
                                  : (
                                    "inline-flex items-center "
                                    +
                                    "gap-1.5 rounded-lg border "
                                    +
                                    "border-emerald-200 bg-white "
                                    +
                                    "px-3 py-1.5 text-xs "
                                    +
                                    "font-semibold "
                                    +
                                    "text-emerald-700 "
                                    +
                                    "hover:bg-emerald-50"
                                  )
                              }
                            >
                              {warehouse.is_active ? (
                                <PowerOff size={14} />
                              ) : (
                                <Power size={14} />
                              )}

                              {warehouse.is_active
                                ? "Deactivate"
                                : "Activate"}
                            </button>
                          </div>
                        </td>
                      ) : null}
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
            <p
              className="
                text-sm text-slate-600
              "
            >
              Page {pagination.page} of{" "}
              {pagination.total_pages || 1}
              {" · "}
              {pagination.total_items} warehouses
            </p>

            <div className="flex gap-2">
              <button
                type="button"
                disabled={
                  !pagination.has_previous
                  ||
                  warehouseQuery.isFetching
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
                  disabled:cursor-not-allowed
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
                  warehouseQuery.isFetching
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
                  disabled:cursor-not-allowed
                  disabled:opacity-40
                "
              >
                Next
              </button>
            </div>
          </div>
        ) : null}
      </div>

      {formOpen
      &&
      selectedWarehouseId
      &&
      selectedWarehouseQuery.isPending ? (
        <div
          className="
            fixed inset-0 z-50
            flex items-center
            justify-center
            bg-slate-950/50 p-4
          "
        >
          <div
            className="
              rounded-xl bg-white
              px-6 py-4 text-sm
              font-medium text-slate-700
              shadow-xl
            "
          >
            Loading warehouse…
          </div>
        </div>
      ) : null}

      {formOpen
      &&
      selectedWarehouseId
      &&
      selectedWarehouseQuery.isError ? (
        <div
          className="
            fixed inset-0 z-50
            flex items-center
            justify-center
            bg-slate-950/50 p-4
          "
        >
          <div
            className="
              w-full max-w-sm
              rounded-xl bg-white p-6
              text-center shadow-xl
            "
          >
            <p
              className="
                text-sm font-medium
                text-red-700
              "
            >
              {
                selectedWarehouseQuery
                  .error
                  .message
              }
            </p>

            <button
              type="button"
              onClick={
                closeFormDialog
              }
              className="
                mt-4 rounded-lg
                bg-slate-900 px-4 py-2
                text-sm font-semibold
                text-white
                hover:bg-slate-700
              "
            >
              Close
            </button>
          </div>
        </div>
      ) : null}

      <WarehouseFormDialog
        open={
          formOpen
          &&
          (
            !selectedWarehouseId
            ||
            Boolean(
              selectedWarehouseQuery
                .data
            )
          )
        }
        warehouse={
          selectedWarehouseId
            ? (
              selectedWarehouseQuery
                .data
              ??
              null
            )
            : null
        }
        onClose={
          closeFormDialog
        }
      />
      <WarehouseLifecycleDialog
        open={
          Boolean(
            lifecycleWarehouse
          )
        }
        warehouse={
          lifecycleWarehouse
        }
        onClose={
          closeLifecycleDialog
        }
      />
    </section>
  );
}
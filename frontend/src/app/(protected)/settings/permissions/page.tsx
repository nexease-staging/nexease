"use client";
import SearchSelect from "@/components/search-select";


import {
  useMemo,
  useState,
} from "react";

import {
  KeyRound,
  RefreshCw,
  Search,
} from "lucide-react";

import {
  usePermissionList,
} from "@/features/roles";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  hasPermission,
} from "@/lib/authorization/permissions";


export default function PermissionsPage() {
  const {
    authentication,
  } = useAuth();

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    moduleFilter,
    setModuleFilter,
  ] = useState("");

  const [
    statusFilter,
    setStatusFilter,
  ] = useState<
    "all" | "active" | "inactive"
  >("all");

  const [
    page,
    setPage,
  ] = useState(1);

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const canRead =
    hasPermission(
      permissions,
      "permissions.read",
    );

  const parameters = useMemo(
    () => ({
      page,
      page_size: 50,

      search:
        search.trim()
        ||
        undefined,

      module:
        moduleFilter
        ||
        undefined,

      is_active:
        statusFilter === "all"
          ? undefined
          : statusFilter === "active",

      sort: "module,code",
    }),
    [
      moduleFilter,
      page,
      search,
      statusFilter,
    ],
  );

  const permissionQuery =
    usePermissionList(
      parameters,
      canRead,
    );

  if (!authentication) {
    return null;
  }

  if (!canRead) {
    return (
      <section
        className="
          rounded-2xl border
          border-amber-200
          bg-amber-50 p-6
        "
      >
        <h1
          className="
            text-lg font-semibold
            text-amber-900
          "
        >
          Permission access restricted
        </h1>

        <p
          className="
            mt-2 text-sm text-amber-800
          "
        >
          Your role does not include the
          permissions.read permission.
        </p>
      </section>
    );
  }

  const permissionItems =
    permissionQuery.data
      ?.permissions
    ??
    [];

  const modules =
    permissionQuery.data
      ?.modules
    ??
    [];

  const pagination =
    permissionQuery.data
      ?.pagination;

  return (
    <section className="space-y-6">
      <div
        className="
          flex flex-col gap-4
          sm:flex-row
          sm:items-center
          sm:justify-between
        "
      >
        <div>
          <div
            className="
              flex items-center gap-2
            "
          >
            <KeyRound
              size={25}
              className="text-blue-600"
            />

            <h1
              className="
                text-2xl font-bold
                text-slate-900
              "
            >
              Permissions
            </h1>
          </div>

          <p
            className="
              mt-1 text-sm
              text-slate-600
            "
          >
            Review application permissions
            available for role assignment.
          </p>
        </div>

        <button
          type="button"
          disabled={
            permissionQuery.isFetching
          }
          onClick={() => {
            void permissionQuery.refetch();
          }}
          className="
            inline-flex items-center
            justify-center gap-2
            rounded-lg border
            border-slate-300
            bg-white px-4 py-2
            text-sm font-semibold
            text-slate-700
            hover:bg-slate-50
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          <RefreshCw
            size={16}
            className={
              permissionQuery.isFetching
                ? "animate-spin"
                : undefined
            }
          />

          Refresh
        </button>
      </div>

      <div
        className="
          grid gap-4 rounded-2xl
          border border-slate-200
          bg-white p-4 shadow-sm
          md:grid-cols-3
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
              placeholder="Search code or name"
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
            Module
          </span>

          <SearchSelect
            value={moduleFilter}
            onChange={(event) => {
              setModuleFilter(
                event.target.value,
              );

              setPage(1);
            }}
            className="
              h-10 w-full rounded-lg
              border border-slate-300
              bg-white px-3
              text-sm text-slate-900
              outline-none
              focus:border-blue-500
              focus:ring-2
              focus:ring-blue-100
            "
          >
            <option value="">
              All modules
            </option>

            {modules.map(
              (module) => (
                <option
                  key={module}
                  value={module}
                >
                  {module}
                </option>
              ),
            )}
          </SearchSelect>
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
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(
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
              bg-white px-3
              text-sm text-slate-900
              outline-none
              focus:border-blue-500
              focus:ring-2
              focus:ring-blue-100
            "
          >
            <option value="all">
              All permissions
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
        {permissionQuery.isPending ? (
          <div
            className="
              flex min-h-72
              items-center justify-center
              text-sm text-slate-500
            "
          >
            Loading permissions…
          </div>
        ) : permissionQuery.isError ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              gap-3 p-6 text-center
            "
          >
            <p
              className="
                text-sm text-red-700
              "
            >
              {permissionQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void permissionQuery.refetch();
              }}
              className="
                rounded-lg bg-slate-900
                px-4 py-2
                text-sm font-semibold
                text-white
              "
            >
              Try again
            </button>
          </div>
        ) : permissionItems.length === 0 ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              p-6 text-center
            "
          >
            <KeyRound
              size={36}
              className="text-slate-300"
            />

            <h2
              className="
                mt-3 font-semibold
                text-slate-900
              "
            >
              No permissions found
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-500
              "
            >
              Change the search or filters
              to view other permissions.
            </p>
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
                    "Permission",
                    "Code",
                    "Module",
                    "Description",
                    "Status",
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
                {permissionItems.map(
                  (permission) => (
                    <tr
                      key={permission.id}
                      className="
                        hover:bg-slate-50
                      "
                    >
                      <td
                        className="
                          px-4 py-4
                          text-sm font-semibold
                          text-slate-900
                        "
                      >
                        {permission.name}
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                        "
                      >
                        <code
                          className="
                            rounded-md
                            bg-slate-100
                            px-2 py-1
                            text-xs
                            text-slate-700
                          "
                        >
                          {permission.code}
                        </code>
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                        "
                      >
                        <span
                          className="
                            inline-flex
                            rounded-full
                            border
                            border-blue-200
                            bg-blue-50
                            px-2.5 py-1
                            text-xs font-semibold
                            text-blue-700
                          "
                        >
                          {permission.module}
                        </span>
                      </td>

                      <td
                        className="
                          max-w-lg px-4 py-4
                          text-sm text-slate-600
                        "
                      >
                        {
                          permission.description
                          ??
                          "No description"
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
                            inline-flex
                            rounded-full border
                            px-2.5 py-1
                            text-xs font-semibold
                            ${
                              permission.is_active
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
                            permission.is_active
                              ? "Active"
                              : "Inactive"
                          }
                        </span>
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
            <p
              className="
                text-sm text-slate-600
              "
            >
              Page {pagination.page} of{" "}
              {pagination.total_pages || 1}
              {" · "}
              {pagination.total_items} permissions
            </p>

            <div className="flex gap-2">
              <button
                type="button"
                disabled={
                  !pagination.has_previous
                  ||
                  permissionQuery.isFetching
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
                  border-slate-300
                  bg-white px-3 py-1.5
                  text-sm font-semibold
                  text-slate-700
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
                  permissionQuery.isFetching
                }
                onClick={() => {
                  setPage(
                    (current) =>
                      current + 1,
                  );
                }}
                className="
                  rounded-lg border
                  border-slate-300
                  bg-white px-3 py-1.5
                  text-sm font-semibold
                  text-slate-700
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
    </section>
  );
}
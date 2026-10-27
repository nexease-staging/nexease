"use client";
import SearchSelect from "@/components/search-select";


import {
  useMemo,
  useState,
} from "react";

import {
  KeyRound,
  Pencil,
  Plus,
  Power,
  PowerOff,
  RefreshCw,
  Search,
  ShieldCheck,
} from "lucide-react";

import {
  RoleDialog,
} from "@/features/roles/components/role-dialog";

import {
  RolePermissionsDialog,
} from "@/features/roles/components/role-permissions-dialog";

import {
  RoleStatusDialog,
} from "@/features/roles/components/role-status-dialog";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  RoleSummary,
  useRoleList,
} from "@/features/roles";

import {
  hasPermission,
} from "@/lib/authorization/permissions";


export default function RolesPage() {
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
    typeFilter,
    setTypeFilter,
  ] = useState<
    "all" | "system" | "custom"
  >("all");

  const [
    page,
    setPage,
  ] = useState(1);

  const [
    createDialogOpen,
    setCreateDialogOpen,
  ] = useState(false);

  const [
    editingRole,
    setEditingRole,
  ] = useState<RoleSummary | null>(
    null,
  );

  const [
    permissionRole,
    setPermissionRole,
  ] = useState<RoleSummary | null>(
    null,
  );

  const [
    statusRole,
    setStatusRole,
  ] = useState<RoleSummary | null>(
    null,
  );

  const [
    statusAction,
    setStatusAction,
  ] = useState<
    "activate" | "deactivate"
  >("deactivate");

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const canRead = hasPermission(
    permissions,
    "roles.read",
  );

  const canCreate = hasPermission(
    permissions,
    "roles.create",
  );

  const canUpdate = hasPermission(
    permissions,
    "roles.update",
  );

  const canAssignPermissions =
    hasPermission(
      permissions,
      "roles.assign_permissions",
    );

  const canActivate =
    hasPermission(
      permissions,
      "roles.activate",
    );

  const canDeactivate =
    hasPermission(
      permissions,
      "roles.deactivate",
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

      is_system:
        typeFilter === "all"
          ? undefined
          : typeFilter === "system",

      sort: "name",
    }),
    [
      activeFilter,
      page,
      search,
      typeFilter,
    ],
  );

  const roleQuery =
    useRoleList(
      listParameters,
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
          Role access restricted
        </h1>

        <p
          className="
            mt-2 text-sm text-amber-800
          "
        >
          Your role does not include the
          roles.read permission.
        </p>
      </section>
    );
  }

  const roles =
    roleQuery.data
      ?.roles
    ??
    [];

  const pagination =
    roleQuery.data
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
            <ShieldCheck
              size={25}
              className="text-blue-600"
            />

            <h1
              className="
                text-2xl font-bold
                text-slate-900
              "
            >
              Roles
            </h1>
          </div>

          <p
            className="
              mt-1 text-sm text-slate-600
            "
          >
            Review organization roles and
            their assigned permission counts.
          </p>
        </div>

        <div
          className="
            flex flex-wrap items-center gap-2
          "
        >
          <button
            type="button"
            disabled={roleQuery.isFetching}
            onClick={() => {
              void roleQuery.refetch();
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
                roleQuery.isFetching
                  ? "animate-spin"
                  : undefined
              }
            />

            Refresh
          </button>

          {canCreate ? (
            <button
              type="button"
              onClick={() => {
                setCreateDialogOpen(true);
              }}
              className="
                inline-flex items-center
                justify-center gap-2
                rounded-lg bg-blue-600
                px-4 py-2 text-sm
                font-semibold text-white
                hover:bg-blue-700
              "
            >
              <Plus size={16} />

              Create Role
            </button>
          ) : null}
        </div>
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
              placeholder="Search name or description"
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
              All roles
            </option>

            <option value="active">
              Active roles
            </option>

            <option value="inactive">
              Inactive roles
            </option>
          </SearchSelect>
        </label>

        <label className="space-y-1.5">
          <span
            className="
              text-sm font-semibold
              text-slate-700
            "
          >
            Role type
          </span>

          <SearchSelect
            value={typeFilter}
            onChange={(event) => {
              setTypeFilter(
                event.target.value as (
                  "all"
                  |
                  "system"
                  |
                  "custom"
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
              All role types
            </option>

            <option value="system">
              System roles
            </option>

            <option value="custom">
              Custom roles
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
        {roleQuery.isPending ? (
          <div
            className="
              flex min-h-72 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading roles…
          </div>
        ) : roleQuery.isError ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              gap-3 p-6 text-center
            "
          >
            <p className="text-sm text-red-700">
              {roleQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void roleQuery.refetch();
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
        ) : roles.length === 0 ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              p-6 text-center
            "
          >
            <ShieldCheck
              size={36}
              className="text-slate-300"
            />

            <h2
              className="
                mt-3 font-semibold
                text-slate-900
              "
            >
              No roles found
            </h2>

            <p
              className="
                mt-1 max-w-md text-sm
                text-slate-500
              "
            >
              Change the search or filters
              to view other roles.
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
                    "Role",
                    "Description",
                    "Type",
                    "Permissions",
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
                {roles.map(
                  (role) => (
                    <tr
                      key={role.id}
                      className="
                        hover:bg-slate-50
                      "
                    >
                      <td
                        className="
                          px-4 py-4 text-sm
                          font-semibold
                          text-slate-900
                        "
                      >
                        {role.name}
                      </td>

                      <td
                        className="
                          max-w-md px-4 py-4
                          text-sm text-slate-600
                        "
                      >
                        {
                          role.description
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
                            inline-flex rounded-full
                            border px-2.5 py-1
                            text-xs font-semibold
                            ${
                              role.is_system
                                ? (
                                  "border-blue-200 "
                                  +
                                  "bg-blue-50 "
                                  +
                                  "text-blue-700"
                                )
                                : (
                                  "border-violet-200 "
                                  +
                                  "bg-violet-50 "
                                  +
                                  "text-violet-700"
                                )
                            }
                          `}
                        >
                          {
                            role.is_system
                              ? "System"
                              : "Custom"
                          }
                        </span>
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4 text-sm
                          font-semibold
                          text-slate-900
                        "
                      >
                        {role.permission_count}
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
                              role.is_active
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
                            role.is_active
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
                          {canUpdate && !role.is_system ? (
                            <button
                              type="button"
                              onClick={() => {
                                setEditingRole(role);
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

                          {canAssignPermissions
                            &&
                            !role.is_system ? (
                              <button
                                type="button"
                                onClick={() => {
                                  setPermissionRole(
                                    role,
                                  );
                                }}
                                className="
                                  inline-flex items-center
                                  gap-1.5 rounded-lg
                                  border border-blue-200
                                  bg-blue-50 px-3 py-1.5
                                  text-xs font-semibold
                                  text-blue-700
                                  hover:bg-blue-100
                                "
                              >
                                <KeyRound size={14} />

                                Permissions
                              </button>
                            ) : null}

                          {role.is_active
                            ? (
                                canDeactivate
                                &&
                                !role.is_system ? (
                                  <button
                                    type="button"
                                    onClick={() => {
                                      setStatusAction(
                                        "deactivate",
                                      );

                                      setStatusRole(role);
                                    }}
                                    className="
                                      inline-flex
                                      items-center gap-1.5
                                      rounded-lg border
                                      border-red-200
                                      bg-red-50
                                      px-3 py-1.5
                                      text-xs font-semibold
                                      text-red-700
                                      hover:bg-red-100
                                      disabled:cursor-not-allowed
                                      disabled:opacity-50
                                    "
                                  >
                                    <PowerOff size={14} />

                                    Deactivate
                                  </button>
                                ) : null
                              )
                            : (
                                canActivate
                                &&
                                !role.is_system ? (
                                  <button
                                    type="button"
                                    onClick={() => {
                                      setStatusAction(
                                        "activate",
                                      );

                                      setStatusRole(role);
                                    }}
                                    className="
                                      inline-flex
                                      items-center gap-1.5
                                      rounded-lg border
                                      border-emerald-200
                                      bg-emerald-50
                                      px-3 py-1.5
                                      text-xs font-semibold
                                      text-emerald-700
                                      hover:bg-emerald-100
                                      disabled:cursor-not-allowed
                                      disabled:opacity-50
                                    "
                                  >
                                    <Power size={14} />

                                    Activate
                                  </button>
                                ) : null
                              )}

                          {!canUpdate
                            &&
                            !canAssignPermissions
                            &&
                            !canActivate
                            &&
                            !canDeactivate ? (
                              <span
                                className="
                                  text-xs text-slate-400
                                "
                              >
                                —
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
              {pagination.total_items} roles
            </p>

            <div className="flex gap-2">
              <button
                type="button"
                disabled={
                  !pagination.has_previous
                  ||
                  roleQuery.isFetching
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
                  roleQuery.isFetching
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

      <RoleDialog
        key={
          createDialogOpen
            ? "create-open"
            : "create-closed"
        }
        open={createDialogOpen}
        onClose={() => {
          setCreateDialogOpen(false);
        }}
      />

      <RoleDialog
        key={
          editingRole
            ? `edit-${editingRole.id}`
            : "edit-closed"
        }
        open={editingRole !== null}
        role={editingRole}
        onClose={() => {
          setEditingRole(null);
        }}
      />

      <RolePermissionsDialog
        key={
          permissionRole
            ? `permissions-${permissionRole.id}`
            : "permissions-closed"
        }
        open={permissionRole !== null}
        role={permissionRole}
        onClose={() => {
          setPermissionRole(null);
        }}
      />

      <RoleStatusDialog
        key={
          statusRole
            ? `status-${statusAction}-${statusRole.id}`
            : "status-closed"
        }
        open={statusRole !== null}
        role={statusRole}
        action={statusAction}
        onClose={() => {
          setStatusRole(null);
        }}
      />
    </section>
  );
}
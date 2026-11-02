"use client";
import {confirmAction} from "@/components/nex-feedback";
import SearchSelect from "@/components/search-select";


import {
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
  UserRoundCog,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import UserDialog from "@/features/users/components/user-dialog";

import {
  useActivateUser,
  useDeactivateUser,
  useUserList,
} from "@/features/users/hooks";

import type {
  UserSummary,
} from "@/features/users/types";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

export default function UsersPage() {
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
    userDialogOpen,
    setUserDialogOpen,
  ] = useState(false);

  const [
    editingUserId,
    setEditingUserId,
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
    useActivateUser();

  const deactivateMutation =
    useDeactivateUser();

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const currentUserId =
    authentication
      ?.user
      .id
    ??
    "";

  const canRead = hasPermission(
    permissions,
    "users.read",
  );

  const canCreate = hasPermission(
    permissions,
    "users.create",
  );

  const canUpdate = hasPermission(
    permissions,
    "users.update",
  );

  const canActivate = hasPermission(
    permissions,
    "users.activate",
  );

  const canDeactivate = hasPermission(
    permissions,
    "users.deactivate",
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
      sort: "email",
    }),
    [
      activeFilter,
      page,
      search,
    ],
  );

  const userQuery =
    useUserList(
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
          User access restricted
        </h1>

        <p
          className="
            mt-2 text-sm text-amber-800
          "
        >
          Your role does not include the
          users.read permission.
        </p>
      </section>
    );
  }

  const users =
    userQuery.data
      ?.users
    ??
    [];

  const pagination =
    userQuery.data
      ?.pagination;

  const actionPending =
    activateMutation.isPending
    ||
    deactivateMutation.isPending;

  function openCreateDialog(): void {
    setEditingUserId(
      null,
    );

    setUserDialogOpen(
      true,
    );
  }

  function openEditDialog(
    userId: string,
  ): void {
    setEditingUserId(
      userId,
    );

    setUserDialogOpen(
      true,
    );
  }

  async function activate(
    user: UserSummary,
  ): Promise<void> {
    const confirmed =
      await confirmAction(
        (
          `Activate ${user.full_name || user.email}?`
          +
          "\n\nThe user will be able "
          +
          "to sign in again."
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
        user.id,
      );
    } catch (error) {
      setActionError(
        error instanceof Error
          ? error.message
          : "Unable to activate user.",
      );
    }
  }

  async function deactivate(
    user: UserSummary,
  ): Promise<void> {
    const confirmed =
      await confirmAction(
        (
          `Deactivate ${user.full_name || user.email}?`
          +
          "\n\nThe user will lose "
          +
          "access to the application."
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
        user.id,
      );
    } catch (error) {
      setActionError(
        error instanceof Error
          ? error.message
          : "Unable to deactivate user.",
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
            <UserRoundCog
              size={25}
              className="text-blue-600"
            />

            <h1
              className="
                text-2xl font-bold
                text-slate-900
              "
            >
              Users
            </h1>
          </div>

          <p
            className="
              mt-1 text-sm text-slate-600
            "
          >
            Manage organization users,
            assigned roles, and access status.
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
              userQuery.isFetching
            }
            onClick={() => {
              void userQuery.refetch();
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
                userQuery.isFetching
                  ? "animate-spin"
                  : undefined
              }
            />

            Refresh
          </button>

          {canCreate ? (
            <button title="New user"
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
              <Plus size={17} /><span className="sr-only">New user</span></button>
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
              placeholder="Search name or email"
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
              All users
            </option>

            <option value="active">
              Active users
            </option>

            <option value="inactive">
              Inactive users
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
        {userQuery.isPending ? (
          <div
            className="
              flex min-h-72 items-center
              justify-center text-sm
              text-slate-500
            "
          >
            Loading users…
          </div>
        ) : userQuery.isError ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              gap-3 p-6 text-center
            "
          >
            <p className="text-sm text-red-700">
              {userQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void userQuery.refetch();
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
        ) : users.length === 0 ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              p-6 text-center
            "
          >
            <UserRoundCog
              size={36}
              className="text-slate-300"
            />

            <h2
              className="
                mt-3 font-semibold
                text-slate-900
              "
            >
              No users found
            </h2>

            <p
              className="
                mt-1 max-w-md text-sm
                text-slate-500
              "
            >
              Change the filters or create
              another organization user.
            </p>

            {canCreate ? (
              <button title="Create user"
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
                <Plus size={16} /><span className="sr-only">Create user</span></button>
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
                    "User",
                    "Email",
                    "Role",
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
                {users.map(
                  (user) => {
                    const isCurrentUser =
                      user.id
                      ===
                      currentUserId;

                    const initials = (
                      `${user.first_name[0] ?? ""}`
                      +
                      `${user.last_name[0] ?? ""}`
                    ).toUpperCase();

                    return (
                      <tr
                        key={user.id}
                        className="
                          hover:bg-slate-50
                        "
                      >
                        <td
                          className="
                            px-4 py-4 text-sm
                          "
                        >
                          <div
                            className="
                              flex items-center gap-3
                            "
                          >
                            <div
                              className="
                                flex size-9 shrink-0
                                items-center
                                justify-center
                                rounded-full
                                bg-blue-100
                                font-bold
                                text-blue-700
                              "
                            >
                              {initials || "U"}
                            </div>

                            <div>
                              <p
                                className="
                                  font-semibold
                                  text-slate-900
                                "
                              >
                                {
                                  user.full_name
                                  ||
                                  user.email
                                }
                              </p>

                              {isCurrentUser ? (
                                <p
                                  className="
                                    mt-0.5 text-xs
                                    font-medium
                                    text-blue-600
                                  "
                                >
                                  Current user
                                </p>
                              ) : null}
                            </div>
                          </div>
                        </td>

                        <td
                          className="
                            px-4 py-4 text-sm
                            text-slate-700
                          "
                        >
                          {user.email}
                        </td>

                        <td
                          className="
                            px-4 py-4 text-sm
                            text-slate-700
                          "
                        >
                          {
                            user.role?.name
                            ??
                            "No role"
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
                                user.is_active
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
                              user.is_active
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
                            && user.is_active ? (
                              <button
                                type="button"
                                title="Edit user"
                                aria-label={
                                  `Edit ${user.email}`
                                }
                                disabled={
                                  actionPending
                                }
                                onClick={() => {
                                  openEditDialog(
                                    user.id,
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

                            {canActivate
                            && !user.is_active
                            && !isCurrentUser ? (
                              <button
                                type="button"
                                title="Activate user"
                                aria-label={
                                  `Activate ${user.email}`
                                }
                                disabled={
                                  actionPending
                                }
                                onClick={() => {
                                  void activate(
                                    user,
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

                            {canDeactivate
                            && user.is_active
                            && !isCurrentUser ? (
                              <button
                                type="button"
                                title="Deactivate user"
                                aria-label={
                                  `Deactivate ${user.email}`
                                }
                                disabled={
                                  actionPending
                                }
                                onClick={() => {
                                  void deactivate(
                                    user,
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
                    );
                  },
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
              {pagination.total_items} users
            </p>

            <div className="flex gap-2">
              <button
                type="button"
                disabled={
                  !pagination.has_previous
                  ||
                  userQuery.isFetching
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
                  userQuery.isFetching
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

      <UserDialog
        open={
          userDialogOpen
        }
        userId={
          editingUserId
        }
        onClose={() => {
          setUserDialogOpen(
            false,
          );

          setEditingUserId(
            null,
          );
        }}
      />
    </section>
  );
}
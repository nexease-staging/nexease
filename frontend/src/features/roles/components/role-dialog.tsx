"use client";

import {
  FormEvent,
  useMemo,
  useState,
} from "react";

import {
  Loader2,
  ShieldCheck,
  X,
} from "lucide-react";

import {
  RoleSummary,
  useCreateRole,
  usePermissionList,
  useUpdateRole,
} from "@/features/roles";

interface RoleDialogProps {
  open: boolean;
  onClose: () => void;
  role?: RoleSummary | null;
}

export function RoleDialog({
  open,
  onClose,
  role = null,
}: RoleDialogProps) {

  const isEditing =
    role !== null;

  const updateMutation =
    useUpdateRole(
      role?.id ?? "",
    );

  const [
    name,
    setName,
  ] = useState(
    () => role?.name ?? "",
  );

  const [
    description,
    setDescription,
  ] = useState(
    () => role?.description ?? "",
  );

  const [
    selectedPermissionCodes,
    setSelectedPermissionCodes,
  ] = useState<string[]>([]);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string | null>(
    null,
  );

  const permissionQuery =
    usePermissionList(
      {
        page_size: 100,
        is_active: true,
        sort: "module,code",
      },
      open && !isEditing,
    );

  const createMutation =
    useCreateRole();

  const permissions =
    useMemo(
      () =>
        permissionQuery.data
          ?.permissions
        ??
        [],
      [
        permissionQuery.data
          ?.permissions,
      ],
    );

  const permissionsByModule =
    useMemo(
      () => {
        const grouped =
          new Map<
            string,
            typeof permissions
          >();

        for (
          const permission
          of permissions
        ) {
          const existing =
            grouped.get(
              permission.module,
            )
            ??
            [];

          grouped.set(
            permission.module,
            [
              ...existing,
              permission,
            ],
          );
        }

        return Array.from(
          grouped.entries(),
        );
      },
      [
        permissions,
      ],
    );

  if (!open) {
    return null;
  }

  const togglePermission = (
    code: string,
  ) => {
    setSelectedPermissionCodes(
      (current) =>
        current.includes(code)
          ? current.filter(
              (item) =>
                item !== code,
            )
          : [
              ...current,
              code,
            ],
    );
  };

  const toggleModule = (
    modulePermissions:
      typeof permissions,
  ) => {
    const moduleCodes =
      modulePermissions.map(
        (permission) =>
          permission.code,
      );

    const allSelected =
      moduleCodes.every(
        (code) =>
          selectedPermissionCodes
            .includes(code),
      );

    if (allSelected) {
      setSelectedPermissionCodes(
        (current) =>
          current.filter(
            (code) =>
              !moduleCodes.includes(
                code,
              ),
          ),
      );

      return;
    }

    setSelectedPermissionCodes(
      (current) =>
        Array.from(
          new Set([
            ...current,
            ...moduleCodes,
          ]),
        ),
    );
  };

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    const normalizedName =
      name.trim();

    if (!normalizedName) {
      setErrorMessage(
        "Role name is required.",
      );

      return;
    }

    setErrorMessage(null);

    try {
      if (isEditing) {
        await updateMutation.mutateAsync({
          name:
            normalizedName,

          description:
            description.trim(),
        });
      } else {
        await createMutation.mutateAsync({
          name:
            normalizedName,

          description:
            description.trim(),

          permission_codes:
            selectedPermissionCodes,
        });
      }

      onClose();
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : (
              isEditing
                ? "Unable to update role."
                : "Unable to create role."
            ),
      );
    }
  };

  const isSubmitting =
    createMutation.isPending
    ||
    updateMutation.isPending;

  return (
    <div
      className="
        fixed inset-0 z-50
        flex items-center justify-center
        bg-slate-950/40 p-4
      "
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target
          ===
          event.currentTarget
          &&
          !isSubmitting
        ) {
          onClose();
        }
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="role-dialog-title"
        className="
          flex max-h-[90vh]
          w-full max-w-3xl
          flex-col overflow-hidden
          rounded-2xl bg-white
          shadow-2xl
        "
      >
        <div
          className="
            flex items-start
            justify-between gap-4
            border-b border-slate-200
            px-6 py-5
          "
        >
          <div
            className="
              flex items-start gap-3
            "
          >
            <div
              className="
                rounded-xl bg-blue-50
                p-2.5 text-blue-600
              "
            >
              <ShieldCheck
                size={22}
              />
            </div>

            <div>
              <h2
                id="role-dialog-title"
                className="
                  text-lg font-bold
                  text-slate-900
                "
              >
                {isEditing
                  ? "Edit role"
                  : "Create role"}
              </h2>

              <p
                className="
                  mt-1 text-sm
                  text-slate-500
                "
              >
                {isEditing
                  ? (
                      "Update the custom role name and description."
                    )
                  : (
                      <>
                        Create a custom role and
                        choose its permissions.
                      </>
                    )}
              </p>
            </div>
          </div>

          <button
            type="button"
            disabled={isSubmitting}
            onClick={onClose}
            aria-label="Close role dialog"
            className="
              rounded-lg p-2
              text-slate-500
              hover:bg-slate-100
              disabled:opacity-50
            "
          >
            <X size={19} />
          </button>
        </div>

        <form
          onSubmit={handleSubmit}
          className="
            flex min-h-0 flex-1
            flex-col
          "
        >
          <div
            className="
              space-y-6 overflow-y-auto
              px-6 py-5
            "
          >
            {errorMessage ? (
              <div
                className="
                  rounded-xl border
                  border-red-200
                  bg-red-50 px-4 py-3
                  text-sm text-red-700
                "
              >
                {errorMessage}
              </div>
            ) : null}

            <div
              className="
                grid gap-4 md:grid-cols-2
              "
            >
              <label
                className="
                  space-y-1.5
                  md:col-span-1
                "
              >
                <span
                  className="
                    text-sm font-semibold
                    text-slate-700
                  "
                >
                  Role name
                </span>

                <input
                  value={name}
                  disabled={isSubmitting}
                  onChange={(event) => {
                    setName(
                      event.target.value,
                    );
                  }}
                  placeholder="Example: Sales Manager"
                  className="
                    h-10 w-full rounded-lg
                    border border-slate-300
                    px-3 text-sm
                    text-slate-900
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                    disabled:bg-slate-100
                  "
                />
              </label>

              <label
                className="
                  space-y-1.5
                  md:col-span-2
                "
              >
                <span
                  className="
                    text-sm font-semibold
                    text-slate-700
                  "
                >
                  Description
                </span>

                <textarea
                  value={description}
                  disabled={isSubmitting}
                  onChange={(event) => {
                    setDescription(
                      event.target.value,
                    );
                  }}
                  rows={3}
                  placeholder="Describe what this role is responsible for."
                  className="
                    w-full resize-y
                    rounded-lg border
                    border-slate-300
                    px-3 py-2 text-sm
                    text-slate-900
                    outline-none
                    focus:border-blue-500
                    focus:ring-2
                    focus:ring-blue-100
                    disabled:bg-slate-100
                  "
                />
              </label>
            </div>

          {!isEditing ? (
            <div>
              <div
                className="
                  flex flex-col gap-1
                  sm:flex-row
                  sm:items-center
                  sm:justify-between
                "
              >
                <div>
                  <h3
                    className="
                      text-sm font-bold
                      text-slate-900
                    "
                  >
                    Permissions
                  </h3>

                  <p
                    className="
                      mt-1 text-sm
                      text-slate-500
                    "
                  >
                    {
                      selectedPermissionCodes
                        .length
                    }{" "}
                    selected
                  </p>
                </div>
              </div>

              {permissionQuery.isPending ? (
                <div
                  className="
                    mt-4 flex min-h-32
                    items-center
                    justify-center
                    rounded-xl border
                    border-slate-200
                    text-sm text-slate-500
                  "
                >
                  <Loader2
                    size={18}
                    className="
                      mr-2 animate-spin
                    "
                  />

                  Loading permissions...
                </div>
              ) : permissionQuery.isError ? (
                <div
                  className="
                    mt-4 rounded-xl border
                    border-red-200
                    bg-red-50 p-4
                    text-sm text-red-700
                  "
                >
                  {
                    permissionQuery
                      .error.message
                  }
                </div>
              ) : (
                <div
                  className="
                    mt-4 space-y-4
                  "
                >
                  {permissionsByModule.map(
                    ([
                      module,
                      modulePermissions,
                    ]) => {
                      const moduleCodes =
                        modulePermissions.map(
                          (permission) =>
                            permission.code,
                        );

                      const allSelected =
                        moduleCodes.length > 0
                        &&
                        moduleCodes.every(
                          (code) =>
                            selectedPermissionCodes
                              .includes(code),
                        );

                      return (
                        <section
                          key={module}
                          className="
                            overflow-hidden
                            rounded-xl border
                            border-slate-200
                          "
                        >
                          <div
                            className="
                              flex items-center
                              justify-between
                              gap-3 bg-slate-50
                              px-4 py-3
                            "
                          >
                            <div>
                              <h4
                                className="
                                  text-sm
                                  font-bold
                                  capitalize
                                  text-slate-800
                                "
                              >
                                {module}
                              </h4>

                              <p
                                className="
                                  text-xs
                                  text-slate-500
                                "
                              >
                                {
                                  modulePermissions
                                    .length
                                }{" "}
                                permissions
                              </p>
                            </div>

                            <button
                              type="button"
                              disabled={
                                isSubmitting
                              }
                              onClick={() => {
                                toggleModule(
                                  modulePermissions,
                                );
                              }}
                              className="
                                text-xs
                                font-semibold
                                text-blue-700
                                hover:text-blue-900
                                disabled:opacity-50
                              "
                            >
                              {
                                allSelected
                                  ? "Clear module"
                                  : "Select module"
                              }
                            </button>
                          </div>

                          <div
                            className="
                              grid gap-0
                              sm:grid-cols-2
                            "
                          >
                            {
                              modulePermissions
                                .map(
                                  (
                                    permission,
                                  ) => (
                                    <label
                                      key={
                                        permission.id
                                      }
                                      className="
                                        flex cursor-pointer
                                        items-start gap-3
                                        border-t
                                        border-slate-100
                                        px-4 py-3
                                        hover:bg-slate-50
                                      "
                                    >
                                      <input
                                        type="checkbox"
                                        checked={
                                          selectedPermissionCodes
                                            .includes(
                                              permission.code,
                                            )
                                        }
                                        disabled={
                                          isSubmitting
                                        }
                                        onChange={() => {
                                          togglePermission(
                                            permission.code,
                                          );
                                        }}
                                        className="
                                          mt-0.5 h-4 w-4
                                          rounded
                                          border-slate-300
                                        "
                                      />

                                      <span>
                                        <span
                                          className="
                                            block text-sm
                                            font-semibold
                                            text-slate-800
                                          "
                                        >
                                          {
                                            permission.name
                                          }
                                        </span>

                                        <span
                                          className="
                                            mt-0.5 block
                                            font-mono
                                            text-xs
                                            text-slate-500
                                          "
                                        >
                                          {
                                            permission.code
                                          }
                                        </span>
                                      </span>
                                    </label>
                                  ),
                                )
                            }
                          </div>
                        </section>
                      );
                    },
                  )}
                </div>
              )}
            </div>
          ) : null}
        </div>

        <div
          className="
            flex justify-end gap-3
            border-t border-slate-200
            bg-slate-50 px-6 py-4
          "
        >
            <button
              type="button"
              disabled={isSubmitting}
              onClick={onClose}
              className="
                rounded-lg border
                border-slate-300
                bg-white px-4 py-2
                text-sm font-semibold
                text-slate-700
                hover:bg-slate-50
                disabled:opacity-50
              "
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={
                isSubmitting
                ||
                (
                  !isEditing
                  &&
                  permissionQuery.isPending
                )
              }
              className="
                inline-flex items-center
                gap-2 rounded-lg
                bg-blue-600 px-4 py-2
                text-sm font-semibold
                text-white
                hover:bg-blue-700
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              {isSubmitting ? (
                <Loader2
                  size={16}
                  className="animate-spin"
                />
              ) : null}

            {isEditing
              ? "Save changes"
              : "Create role"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
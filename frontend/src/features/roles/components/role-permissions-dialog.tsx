"use client";

import {
  useMemo,
  useState,
} from "react";

import {
  KeyRound,
  Loader2,
  X,
} from "lucide-react";

import {
  RoleSummary,
  useAssignRolePermissions,
  usePermissionList,
  useRole,
} from "@/features/roles";

interface RolePermissionsDialogProps {
  open: boolean;
  role: RoleSummary | null;
  onClose: () => void;
}

export function RolePermissionsDialog({
  open,
  role,
  onClose,
}: RolePermissionsDialogProps) {
  const roleId = role?.id ?? "";

  const roleQuery =
    useRole(
      roleId,
      open && Boolean(roleId),
    );

  const permissionQuery =
    usePermissionList(
      {
        page_size: 100,
        is_active: true,
        sort: "module,code",
      },
      open,
    );

  const assignMutation =
    useAssignRolePermissions(
      roleId,
    );

  const [
    permissionOverride,
    setPermissionOverride,
  ] = useState<string[] | null>(
    null,
  );

  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string | null>(
    null,
  );

  const roleDetail =
    roleQuery.data;

  const selectedPermissionCodes =
    permissionOverride
    ??
    roleDetail?.permission_codes
    ??
    [];
    
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

  if (
    !open
    ||
    !role
  ) {
    return null;
  }

  const isSubmitting =
    assignMutation.isPending;

  const isLoading =
    roleQuery.isPending
    ||
    permissionQuery.isPending;

  const togglePermission = (
    code: string,
  ) => {
    setPermissionOverride(
      (current) => {
        const effective =
          current
          ??
          roleDetail?.permission_codes
          ??
          [];

        return effective.includes(code)
          ? effective.filter(
              (item) =>
                item !== code,
            )
          : [
              ...effective,
              code,
            ];
      },
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

    setPermissionOverride(
      (current) => {
        const effective =
          current
          ??
          roleDetail?.permission_codes
          ??
          [];

        if (allSelected) {
          return effective.filter(
            (code) =>
              !moduleCodes.includes(
                code,
              ),
          );
        }

        return Array.from(
          new Set([
            ...effective,
            ...moduleCodes,
          ]),
        );
      },
    );
  };

  const handleSave =
    async () => {
      setErrorMessage(null);

      try {
        await assignMutation.mutateAsync({
          permission_codes:
            selectedPermissionCodes,
        });

        onClose();
      } catch (error) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to update role permissions.",
        );
      }
    };

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
        aria-labelledby="role-permissions-dialog-title"
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
              <KeyRound size={22} />
            </div>

            <div>
              <h2
                id="role-permissions-dialog-title"
                className="
                  text-lg font-bold
                  text-slate-900
                "
              >
                Manage permissions
              </h2>

              <p
                className="
                  mt-1 text-sm
                  text-slate-500
                "
              >
                {role.name}
              </p>
            </div>
          </div>

          <button
            type="button"
            disabled={isSubmitting}
            onClick={onClose}
            aria-label="Close permissions dialog"
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

        <div
          className="
            min-h-0 flex-1
            overflow-y-auto
            px-6 py-5
          "
        >
          {errorMessage ? (
            <div
              className="
                mb-4 rounded-xl border
                border-red-200 bg-red-50
                px-4 py-3
                text-sm text-red-700
              "
            >
              {errorMessage}
            </div>
          ) : null}

          {isLoading ? (
            <div
              className="
                flex min-h-48
                items-center justify-center
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

              Loading role permissions...
            </div>
          ) : roleQuery.isError ? (
            <div
              className="
                rounded-xl border
                border-red-200 bg-red-50
                p-4 text-sm text-red-700
              "
            >
              {roleQuery.error.message}
            </div>
          ) : permissionQuery.isError ? (
            <div
              className="
                rounded-xl border
                border-red-200 bg-red-50
                p-4 text-sm text-red-700
              "
            >
              {permissionQuery.error.message}
            </div>
          ) : (
            <>
              <div
                className="
                  mb-4 flex items-center
                  justify-between gap-3
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

              <div
                className="
                  space-y-4
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
                            justify-between gap-3
                            bg-slate-50
                            px-4 py-3
                          "
                        >
                          <div>
                            <h4
                              className="
                                text-sm font-bold
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
                            disabled={isSubmitting}
                            onClick={() => {
                              toggleModule(
                                modulePermissions,
                              );
                            }}
                            className="
                              text-xs font-semibold
                              text-blue-700
                              hover:text-blue-900
                              disabled:opacity-50
                            "
                          >
                            {allSelected
                              ? "Clear module"
                              : "Select module"}
                          </button>
                        </div>

                        <div
                          className="
                            grid gap-0
                            sm:grid-cols-2
                          "
                        >
                          {modulePermissions.map(
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
                                      font-mono text-xs
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
                          )}
                        </div>
                      </section>
                    );
                  },
                )}
              </div>
            </>
          )}
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
              border-slate-300 bg-white
              px-4 py-2
              text-sm font-semibold
              text-slate-700
              hover:bg-slate-50
              disabled:opacity-50
            "
          >
            Cancel
          </button>

          <button
            type="button"
            disabled={
              isSubmitting
              ||
              isLoading
              ||
              roleQuery.isError
              ||
              permissionQuery.isError
            }
            onClick={handleSave}
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

            Save permissions
          </button>
        </div>
      </div>
    </div>
  );
}
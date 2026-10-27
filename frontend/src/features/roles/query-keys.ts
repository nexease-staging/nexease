import type {
  PermissionListParameters,
  RoleListParameters,
} from "@/features/roles/types";


export const roleQueryKeys = {
  all: [
    "roles",
  ] as const,

  lists: () =>
    [
      ...roleQueryKeys.all,
      "list",
    ] as const,

  list: (
    parameters: RoleListParameters,
  ) =>
    [
      ...roleQueryKeys.lists(),
      parameters,
    ] as const,

  details: () =>
    [
      ...roleQueryKeys.all,
      "detail",
    ] as const,

  detail: (
    roleId: string,
  ) =>
    [
      ...roleQueryKeys.details(),
      roleId,
    ] as const,
};


export const permissionQueryKeys = {
  all: [
    "permissions",
  ] as const,

  lists: () =>
    [
      ...permissionQueryKeys.all,
      "list",
    ] as const,

  list: (
    parameters:
      PermissionListParameters,
  ) =>
    [
      ...permissionQueryKeys.lists(),
      parameters,
    ] as const,
};
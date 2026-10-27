export {
  activateRole,
  assignRolePermissions,
  createRole,
  deactivateRole,
  getRole,
  listPermissions,
  listRoles,
  updateRole,
} from "@/features/roles/api";

export {
  useActivateRole,
  useAssignRolePermissions,
  useCreateRole,
  useDeactivateRole,
  usePermissionList,
  useRole,
  useRoleList,
  useUpdateRole,
} from "@/features/roles/hooks";

export {
  permissionQueryKeys,
  roleQueryKeys,
} from "@/features/roles/query-keys";

export type {
  AssignRolePermissionsInput,
  CreateRoleInput,
  PaginationData,
  PermissionDetail,
  PermissionListData,
  PermissionListParameters,
  PermissionSummary,
  RoleActivationData,
  RoleData,
  RoleDeactivationData,
  RoleDetail,
  RoleListData,
  RoleListParameters,
  RoleOrganizationReference,
  RoleSummary,
  UpdateRoleInput,
} from "@/features/roles/types";
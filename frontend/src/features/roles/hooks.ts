import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  activateRole,
  assignRolePermissions,
  createRole,
  deactivateRole,
  getRole,
  listPermissions,
  listRoles,
  updateRole,
} from "@/features/roles/api";

import {
  permissionQueryKeys,
  roleQueryKeys,
} from "@/features/roles/query-keys";

import type {
  AssignRolePermissionsInput,
  CreateRoleInput,
  PermissionListParameters,
  RoleListParameters,
  UpdateRoleInput,
} from "@/features/roles/types";


export function useRoleList(
  parameters:
    RoleListParameters = {},
  enabled = true,
) {
  return useQuery({
    queryKey:
      roleQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listRoles(
        parameters,
      ),

    enabled,

    staleTime: 30_000,
  });
}


export function useRole(
  roleId: string | null,
  enabled = true,
) {
  return useQuery({
    queryKey:
      roleQueryKeys.detail(
        roleId ?? "",
      ),

    queryFn: () =>
      getRole(
        roleId as string,
      ),

    enabled:
      enabled
      &&
      Boolean(roleId),

    staleTime: 30_000,
  });
}


export function usePermissionList(
  parameters:
    PermissionListParameters = {},
  enabled = true,
) {
  return useQuery({
    queryKey:
      permissionQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listPermissions(
        parameters,
      ),

    enabled,

    staleTime: 60_000,
  });
}


export function useCreateRole() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateRoleInput,
    ) =>
      createRole(
        input,
      ),

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey:
          roleQueryKeys.lists(),
      });
    },
  });
}


export function useUpdateRole(
  roleId: string,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: UpdateRoleInput,
    ) =>
      updateRole(
        roleId,
        input,
      ),

    onSuccess: async (
      role,
    ) => {
      queryClient.setQueryData(
        roleQueryKeys.detail(
          roleId,
        ),
        role,
      );

      await queryClient.invalidateQueries({
        queryKey:
          roleQueryKeys.lists(),
      });
    },
  });
}


export function useAssignRolePermissions(
  roleId: string,
) {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input:
        AssignRolePermissionsInput,
    ) =>
      assignRolePermissions(
        roleId,
        input,
      ),

    onSuccess: async (
      role,
    ) => {
      queryClient.setQueryData(
        roleQueryKeys.detail(
          roleId,
        ),
        role,
      );

      await queryClient.invalidateQueries({
        queryKey:
          roleQueryKeys.lists(),
      });
    },
  });
}


export function useActivateRole() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      roleId: string,
    ) =>
      activateRole(
        roleId,
      ),

    onSuccess: async (
      result,
    ) => {
      queryClient.setQueryData(
        roleQueryKeys.detail(
          result.role.id,
        ),
        result.role,
      );

      await queryClient.invalidateQueries({
        queryKey:
          roleQueryKeys.lists(),
      });
    },
  });
}


export function useDeactivateRole() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      roleId: string,
    ) =>
      deactivateRole(
        roleId,
      ),

    onSuccess: async (
      result,
    ) => {
      queryClient.setQueryData(
        roleQueryKeys.detail(
          result.role.id,
        ),
        result.role,
      );

      await queryClient.invalidateQueries({
        queryKey:
          roleQueryKeys.lists(),
      });
    },
  });
}
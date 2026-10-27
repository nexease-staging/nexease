import {
  apiRequest,
} from "@/lib/api/client";

import type {
  AssignRolePermissionsInput,
  CreateRoleInput,
  PermissionListData,
  PermissionListParameters,
  RoleActivationData,
  RoleData,
  RoleDeactivationData,
  RoleDetail,
  RoleListData,
  RoleListParameters,
  UpdateRoleInput,
} from "@/features/roles/types";


type QueryValue =
  | string
  | number
  | boolean
  | undefined;


function buildQuery(
  parameters: Record<
    string,
    QueryValue
  >,
): string {
  const searchParameters =
    new URLSearchParams();

  for (
    const [
      key,
      value,
    ]
    of Object.entries(
      parameters,
    )
  ) {
    if (
      value === undefined
      ||
      value === ""
    ) {
      continue;
    }

    searchParameters.set(
      key,
      String(value),
    );
  }

  const query =
    searchParameters.toString();

  return query
    ? `?${query}`
    : "";
}


export async function listRoles(
  parameters:
    RoleListParameters = {},
): Promise<RoleListData> {
  const response =
    await apiRequest<RoleListData>(
      (
        "/roles/"
        +
        buildQuery({
          page:
            parameters.page,

          page_size:
            parameters.page_size,

          search:
            parameters.search,

          is_active:
            parameters.is_active,

          is_system:
            parameters.is_system,

          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}


export async function getRole(
  roleId: string,
): Promise<RoleDetail> {
  const response =
    await apiRequest<RoleData>(
      `/roles/${roleId}/`,
    );

  return response.data.role;
}


export async function createRole(
  input: CreateRoleInput,
): Promise<RoleDetail> {
  const response =
    await apiRequest<RoleData>(
      "/roles/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.role;
}


export async function updateRole(
  roleId: string,
  input: UpdateRoleInput,
): Promise<RoleDetail> {
  const response =
    await apiRequest<RoleData>(
      `/roles/${roleId}/`,
      {
        method: "PATCH",
        body: input,
      },
    );

  return response.data.role;
}


export async function assignRolePermissions(
  roleId: string,
  input: AssignRolePermissionsInput,
): Promise<RoleDetail> {
  const response =
    await apiRequest<RoleData>(
      `/roles/${roleId}/permissions/`,
      {
        method: "PATCH",
        body: input,
      },
    );

  return response.data.role;
}


export async function activateRole(
  roleId: string,
): Promise<RoleActivationData> {
  const response =
    await apiRequest<RoleActivationData>(
      `/roles/${roleId}/activate/`,
      {
        method: "POST",
      },
    );

  return response.data;
}


export async function deactivateRole(
  roleId: string,
): Promise<RoleDeactivationData> {
  const response =
    await apiRequest<RoleDeactivationData>(
      `/roles/${roleId}/deactivate/`,
      {
        method: "POST",
      },
    );

  return response.data;
}


export async function listPermissions(
  parameters:
    PermissionListParameters = {},
): Promise<PermissionListData> {
  const response =
    await apiRequest<PermissionListData>(
      (
        "/permissions/"
        +
        buildQuery({
          page:
            parameters.page,

          page_size:
            parameters.page_size,

          search:
            parameters.search,

          module:
            parameters.module,

          is_active:
            parameters.is_active,

          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}
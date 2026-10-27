import {
  apiRequest,
} from "@/lib/api/client";

import type {
  CreateUserInput,
  RoleListData,
  RoleListParameters,
  UpdateUserInput,
  UserData,
  UserDetail,
  UserListData,
  UserListParameters,
} from "@/features/users/types";

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

export async function listUsers(
  parameters:
    UserListParameters = {},
): Promise<UserListData> {
  const response =
    await apiRequest<UserListData>(
      (
        "/users/"
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
          sort:
            parameters.sort,
        })
      ),
    );

  return response.data;
}

export async function getUser(
  userId: string,
): Promise<UserDetail> {
  const response =
    await apiRequest<UserData>(
      `/users/${userId}/`,
    );

  return response.data.user;
}

export async function createUser(
  input: CreateUserInput,
): Promise<UserDetail> {
  const response =
    await apiRequest<UserData>(
      "/users/",
      {
        method: "POST",
        body: input,
      },
    );

  return response.data.user;
}

export async function updateUser(
  userId: string,
  input: UpdateUserInput,
): Promise<UserDetail> {
  const response =
    await apiRequest<UserData>(
      `/users/${userId}/`,
      {
        method: "PATCH",
        body: input,
      },
    );

  return response.data.user;
}

export async function activateUser(
  userId: string,
): Promise<UserDetail> {
  const response =
    await apiRequest<UserData>(
      `/users/${userId}/activate/`,
      {
        method: "POST",
      },
    );

  return response.data.user;
}

export async function deactivateUser(
  userId: string,
): Promise<UserDetail> {
  const response =
    await apiRequest<UserData>(
      `/users/${userId}/deactivate/`,
      {
        method: "POST",
      },
    );

  return response.data.user;
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
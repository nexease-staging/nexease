import type {
  RoleListParameters,
  UserListParameters,
} from "@/features/users/types";

export const userQueryKeys = {
  all: [
    "users",
  ] as const,

  lists: () => [
    ...userQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      UserListParameters,
  ) => [
    ...userQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...userQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    userId: string,
  ) => [
    ...userQueryKeys.details(),
    userId,
  ] as const,
};

export const roleLookupQueryKeys = {
  all: [
    "user-management",
    "roles",
  ] as const,

  lists: () => [
    ...roleLookupQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      RoleListParameters,
  ) => [
    ...roleLookupQueryKeys.lists(),
    parameters,
  ] as const,
};
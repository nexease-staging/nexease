import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  activateUser,
  createUser,
  deactivateUser,
  getUser,
  listRoles,
  listUsers,
  updateUser,
} from "@/features/users/api";

import {
  roleLookupQueryKeys,
  userQueryKeys,
} from "@/features/users/query-keys";

import type {
  CreateUserInput,
  RoleListParameters,
  UpdateUserInput,
  UserListParameters,
} from "@/features/users/types";

export function useUserList(
  parameters:
    UserListParameters,
) {
  return useQuery({
    queryKey:
      userQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listUsers(
        parameters,
      ),

    staleTime: 15_000,
  });
}

export function useUser(
  userId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      userQueryKeys.detail(
        userId,
      ),

    queryFn: () =>
      getUser(
        userId,
      ),

    enabled:
      enabled
      &&
      Boolean(
        userId,
      ),

    staleTime: 30_000,
  });
}

export function useRoleLookup(
  parameters:
    RoleListParameters,
) {
  return useQuery({
    queryKey:
      roleLookupQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listRoles(
        parameters,
      ),

    staleTime: 60_000,
  });
}

export function useCreateUser() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      input: CreateUserInput,
    ) =>
      createUser(
        input,
      ),

    onSuccess: async (
      user,
    ) => {
      queryClient.setQueryData(
        userQueryKeys.detail(
          user.id,
        ),
        user,
      );

      await queryClient.invalidateQueries({
        queryKey:
          userQueryKeys.lists(),
      });
    },
  });
}

export function useUpdateUser() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      userId,
      input,
    }: {
      userId: string;
      input: UpdateUserInput;
    }) =>
      updateUser(
        userId,
        input,
      ),

    onSuccess: async (
      user,
    ) => {
      queryClient.setQueryData(
        userQueryKeys.detail(
          user.id,
        ),
        user,
      );

      await queryClient.invalidateQueries({
        queryKey:
          userQueryKeys.lists(),
      });
    },
  });
}

export function useActivateUser() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      userId: string,
    ) =>
      activateUser(
        userId,
      ),

    onSuccess: async (
      user,
    ) => {
      queryClient.setQueryData(
        userQueryKeys.detail(
          user.id,
        ),
        user,
      );

      await queryClient.invalidateQueries({
        queryKey:
          userQueryKeys.lists(),
      });
    },
  });
}

export function useDeactivateUser() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      userId: string,
    ) =>
      deactivateUser(
        userId,
      ),

    onSuccess: async (
      user,
    ) => {
      queryClient.setQueryData(
        userQueryKeys.detail(
          user.id,
        ),
        user,
      );

      await queryClient.invalidateQueries({
        queryKey:
          userQueryKeys.lists(),
      });
    },
  });
}
"use client";

import {
  createContext,
  useContext,
  type ReactNode,
} from "react";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  APIRequestError,
} from "@/lib/api/client";

import {
  getCurrentUser,
  login,
  logout,
  logoutAll,
} from "@/features/auth/api";

import type {
  AuthenticationContext,
  LoginCredentials,
} from "@/features/auth/types";

const AUTH_QUERY_KEY = [
  "authentication",
  "current-user",
] as const;

type AuthenticationStatus =
  | "loading"
  | "authenticated"
  | "unauthenticated";

interface AuthContextValue {
  authentication:
    AuthenticationContext | null;

  status:
    AuthenticationStatus;

  isLoading:
    boolean;

  isAuthenticated:
    boolean;

  error:
    Error | null;

  signIn: (
    credentials: LoginCredentials,
  ) => Promise<AuthenticationContext>;

  signOut: () => Promise<void>;

  signOutAll: () => Promise<void>;

  refreshAuthentication:
    () => Promise<void>;
}

const AuthContext =
  createContext<AuthContextValue | null>(
    null,
  );

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const queryClient = useQueryClient();

  const authenticationQuery =
    useQuery({
      queryKey: AUTH_QUERY_KEY,
      queryFn: getCurrentUser,
      retry: false,
      staleTime: 60_000,
    });

  const loginMutation =
    useMutation({
      mutationFn: login,

      onSuccess: (
        authentication,
      ) => {
        queryClient.setQueryData(
          AUTH_QUERY_KEY,
          authentication,
        );
      },
    });

  const logoutMutation =
    useMutation({
      mutationFn: logout,
    });

  const logoutAllMutation =
    useMutation({
      mutationFn: logoutAll,
    });

  const authentication =
    authenticationQuery.data ?? null;

  const isLoading =
    authenticationQuery.isPending;

  const isAuthenticated =
    Boolean(
      authentication
        ?.authentication
        .authenticated,
    );

  const status:
    AuthenticationStatus =
      isLoading
        ? "loading"
        : isAuthenticated
          ? "authenticated"
          : "unauthenticated";

  const errorCandidate =
    authenticationQuery.error ??
    loginMutation.error ??
    logoutMutation.error ??
    logoutAllMutation.error;

  const error =
    errorCandidate instanceof Error
      ? errorCandidate
      : null;

  async function signIn(
    credentials: LoginCredentials,
  ): Promise<AuthenticationContext> {
    return loginMutation.mutateAsync(
      credentials,
    );
  }

  async function clearAuthentication():
    Promise<void> {
    await queryClient.cancelQueries({
      queryKey: AUTH_QUERY_KEY,
    });

    queryClient.setQueryData(
      AUTH_QUERY_KEY,
      null,
    );
  }

  async function signOut():
    Promise<void> {
    try {
      await logoutMutation.mutateAsync();

    } catch (error) {
      const sessionAlreadyEnded =
        error instanceof APIRequestError
        &&
        error.status === 401;

      if (!sessionAlreadyEnded) {
        throw error;
      }

    } finally {
      await clearAuthentication();
    }
  }

  async function signOutAll():
    Promise<void> {
    try {
      await logoutAllMutation.mutateAsync();

    } catch (error) {
      const sessionAlreadyEnded =
        error instanceof APIRequestError
        &&
        error.status === 401;

      if (!sessionAlreadyEnded) {
        throw error;
      }

    } finally {
      await clearAuthentication();
    }
  }

  async function refreshAuthentication():
    Promise<void> {
    await authenticationQuery.refetch();
  }

  const value: AuthContextValue = {
    authentication,
    status,
    isLoading,
    isAuthenticated,
    error,
    signIn,
    signOut,
    signOutAll,
    refreshAuthentication,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth():
  AuthContextValue {
  const context = useContext(
    AuthContext,
  );

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider.",
    );
  }

  return context;
}
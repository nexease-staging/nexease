import {
  useQuery,
} from "@tanstack/react-query";

import {
  listAuthenticationAuditLogs,
} from "@/features/audit/api";

import {
  authenticationAuditQueryKeys,
} from "@/features/audit/query-keys";

import type {
  AuthenticationAuditListParameters,
} from "@/features/audit/types";


export function useAuthenticationAuditList(
  parameters:
    AuthenticationAuditListParameters = {},
  enabled = true,
) {
  return useQuery({
    queryKey:
      authenticationAuditQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listAuthenticationAuditLogs(
        parameters,
      ),

    enabled,

    staleTime: 30_000,
  });
}
import type {
  AuthenticationAuditListParameters,
} from "@/features/audit/types";


export const authenticationAuditQueryKeys = {
  all: [
    "authentication-audit",
  ] as const,

  lists: () => [
    ...authenticationAuditQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      AuthenticationAuditListParameters,
  ) => [
    ...authenticationAuditQueryKeys.lists(),
    parameters,
  ] as const,
};
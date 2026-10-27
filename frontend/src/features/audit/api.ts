import {
  apiRequest,
} from "@/lib/api/client";

import type {
  AuthenticationAuditListData,
  AuthenticationAuditListParameters,
} from "@/features/audit/types";


type QueryValue =
  | string
  | number
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


export async function listAuthenticationAuditLogs(
  parameters:
    AuthenticationAuditListParameters = {},
): Promise<AuthenticationAuditListData> {
  const response =
    await apiRequest<
      AuthenticationAuditListData
    >(
      (
        "/auth/authentication-audit-logs/"
        +
        buildQuery({
          event_type:
            parameters.event_type,

          identifier:
            parameters.identifier,

          ip_address:
            parameters.ip_address,

          limit:
            parameters.limit,
        })
      ),
    );

  return response.data;
}
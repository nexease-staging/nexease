import {
  apiRequest,
} from "@/lib/api/client";

import type {
  DashboardParameters,
  MainDashboard,
  MainDashboardData,
} from "@/features/dashboard/types";


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
      String(
        value,
      ),
    );
  }

  const query =
    searchParameters.toString();

  return query
    ? `?${query}`
    : "";
}


export async function getMainDashboard(
  parameters:
    DashboardParameters = {},
): Promise<MainDashboard> {
  const response =
    await apiRequest<
      MainDashboardData
    >(
      (
        "/dashboard/"
        +
        buildQuery({
          start_date:
            parameters.start_date,
          end_date:
            parameters.end_date,
        })
      ),
    );

  return response
    .data
    .dashboard;
}
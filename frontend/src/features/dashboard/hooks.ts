import {
  useQuery,
} from "@tanstack/react-query";

import {
  getMainDashboard,
} from "@/features/dashboard/api";

import {
  dashboardQueryKeys,
} from "@/features/dashboard/query-keys";

import type {
  DashboardParameters,
} from "@/features/dashboard/types";


export function useMainDashboard(
  parameters:
    DashboardParameters = {},
  enabled = true,
) {
  return useQuery({
    queryKey:
      dashboardQueryKeys
        .dashboard(
          parameters,
        ),

    queryFn: () =>
      getMainDashboard(
        parameters,
      ),

    enabled,

    staleTime: 30_000,
  });
}
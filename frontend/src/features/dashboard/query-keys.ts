import type {
  DashboardParameters,
} from "@/features/dashboard/types";


export const dashboardQueryKeys = {
  all: [
    "dashboard",
  ] as const,

  dashboards: () => [
    ...dashboardQueryKeys.all,
    "main",
  ] as const,

  dashboard: (
    parameters:
      DashboardParameters,
  ) => [
    ...dashboardQueryKeys
      .dashboards(),
    parameters,
  ] as const,
};
import type {
  BackgroundJobListParameters,
} from "@/features/background-jobs/types";

export const backgroundJobQueryKeys = {
  all: [
    "background-jobs",
  ] as const,

  lists: () => [
    ...backgroundJobQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      BackgroundJobListParameters,
  ) => [
    ...backgroundJobQueryKeys.lists(),
    parameters,
  ] as const,

  details: () => [
    ...backgroundJobQueryKeys.all,
    "detail",
  ] as const,

  detail: (
    jobId: string,
  ) => [
    ...backgroundJobQueryKeys.details(),
    jobId,
  ] as const,
};
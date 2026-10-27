"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getBackgroundJob,
  listBackgroundJobs,
  retryBackgroundJob,
} from "@/features/background-jobs/api";

import {
  backgroundJobQueryKeys,
} from "@/features/background-jobs/query-keys";

import type {
  BackgroundJobListParameters,
} from "@/features/background-jobs/types";

export function useBackgroundJobList(
  parameters:
    BackgroundJobListParameters = {},
  enabled = true,
) {
  return useQuery({
    queryKey:
      backgroundJobQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listBackgroundJobs(
        parameters,
      ),

    enabled,
  });
}

export function useBackgroundJob(
  jobId: string,
  enabled = true,
) {
  return useQuery({
    queryKey:
      backgroundJobQueryKeys.detail(
        jobId,
      ),

    queryFn: () =>
      getBackgroundJob(
        jobId,
      ),

    enabled:
      enabled
      && Boolean(jobId),
  });
}

export function useRetryBackgroundJob() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn:
      retryBackgroundJob,

    onSuccess: (
      job,
    ) => {
      queryClient.setQueryData(
        backgroundJobQueryKeys.detail(
          job.id,
        ),
        job,
      );

      void queryClient.invalidateQueries({
        queryKey:
          backgroundJobQueryKeys.lists(),
      });
    },
  });
}
import {
  apiRequest,
} from "@/lib/api/client";

import type {
  BackgroundJob,
  BackgroundJobListParameters,
  BackgroundJobListResponse,
} from "@/features/background-jobs/types";

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
      String(value),
    );
  }

  const query =
    searchParameters.toString();

  return query
    ? `?${query}`
    : "";
}

export async function listBackgroundJobs(
  parameters:
    BackgroundJobListParameters = {},
): Promise<BackgroundJobListResponse> {
  const response =
    await apiRequest<
      BackgroundJobListResponse
    >(
      (
        "/background-jobs/"
        +
        buildQuery({
          status:
            parameters.status,

          job_type:
            parameters.job_type,

          limit:
            parameters.limit,
        })
      ),
    );

  return response.data;
}

export async function getBackgroundJob(
  jobId: string,
): Promise<BackgroundJob> {
  const response =
    await apiRequest<
      BackgroundJob
    >(
      (
        "/background-jobs/"
        +
        `${jobId}/`
      ),
    );

  return response.data;
}

export async function retryBackgroundJob(
  jobId: string,
): Promise<BackgroundJob> {
  const response =
    await apiRequest<
      BackgroundJob
    >(
      (
        "/background-jobs/"
        +
        `${jobId}/retry/`
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response.data;
}
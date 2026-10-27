"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Loader2,
  RefreshCw,
  RotateCcw,
} from "lucide-react";

import {
  useBackgroundJobList,
  useRetryBackgroundJob,
} from "@/features/background-jobs/hooks";

import type {
  BackgroundJob,
  BackgroundJobStatus,
} from "@/features/background-jobs/types";


function statusClass(
  status: BackgroundJobStatus,
): string {
  switch (status) {
    case "SUCCEEDED":
      return (
        "bg-emerald-100 "
        +
        "text-emerald-700"
      );

    case "FAILED":
      return (
        "bg-red-100 "
        +
        "text-red-700"
      );

    case "RUNNING":
      return (
        "bg-blue-100 "
        +
        "text-blue-700"
      );

    case "RETRYING":
      return (
        "bg-amber-100 "
        +
        "text-amber-700"
      );

    default:
      return (
        "bg-slate-100 "
        +
        "text-slate-700"
      );
  }
}


function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}


function jobTypeLabel(
  jobType: string,
): string {
  return jobType
    .toLowerCase()
    .split("_")
    .map(
      (part) =>
        part.charAt(0).toUpperCase()
        +
        part.slice(1),
    )
    .join(" ");
}


interface JobRowProps {
  job: BackgroundJob;
  retrying: boolean;

  onRetry: (
    job: BackgroundJob,
  ) => void;
}


function JobRow({
  job,
  retrying,
  onRetry,
}: JobRowProps) {
  return (
    <tr
      className="
        border-b border-slate-100
        last:border-b-0
      "
    >
      <td
        className="
          px-4 py-3
          align-top
        "
      >
        <p
          className="
            text-sm font-medium
            text-slate-900
          "
        >
          {jobTypeLabel(
            job.job_type,
          )}
        </p>

        <p
          className="
            mt-1 max-w-72
            truncate text-xs
            text-slate-400
          "
          title={job.id}
        >
          {job.id}
        </p>
      </td>

      <td
        className="
          px-4 py-3
          align-top
        "
      >
        <span
          className={`
            inline-flex rounded-full
            px-2.5 py-1 text-xs
            font-semibold
            ${statusClass(
              job.status,
            )}
          `}
        >
          {job.status}
        </span>
      </td>

      <td
        className="
          px-4 py-3
          align-top text-sm
          text-slate-600
        "
      >
        {job.attempts}
        {" / "}
        {job.max_attempts}
      </td>

      <td
        className="
          px-4 py-3
          align-top text-sm
          text-slate-600
        "
      >
        {formatDate(
          job.created_at,
        )}
      </td>

      <td
        className="
          px-4 py-3
          align-top text-sm
          text-slate-600
        "
      >
        {formatDate(
          job.completed_at,
        )}
      </td>

      <td
        className="
          max-w-80 px-4 py-3
          align-top
        "
      >
        {job.last_error ? (
          <p
            className="
              text-sm leading-5
              text-red-600
            "
          >
            {job.last_error}
          </p>
        ) : (
          <span
            className="
              text-sm text-slate-400
            "
          >
            —
          </span>
        )}
      </td>

      <td
        className="
          px-4 py-3
          text-right align-top
        "
      >
        {job.status === "FAILED" && (
          <button
            type="button"
            disabled={retrying}
            onClick={() => {
              onRetry(job);
            }}
            className="
              inline-flex items-center
              gap-1.5 rounded-lg
              border border-slate-200
              bg-white px-3 py-1.5
              text-sm font-medium
              text-slate-700
              hover:bg-slate-50
              disabled:opacity-50
            "
          >
            {retrying ? (
              <Loader2
                size={15}
                className="animate-spin"
              />
            ) : (
              <RotateCcw size={15} />
            )}

            Retry
          </button>
        )}
      </td>
    </tr>
  );
}


export default function BackgroundJobsPage() {
  const jobsQuery =
    useBackgroundJobList(
      {
        limit: 100,
      },
    );

  const retryMutation =
    useRetryBackgroundJob();

  const jobs =
    jobsQuery.data?.results
    ??
    [];

  const pendingCount =
    jobs.filter(
      (job) =>
        job.status === "PENDING"
        ||
        job.status === "RETRYING",
    ).length;

  const runningCount =
    jobs.filter(
      (job) =>
        job.status === "RUNNING",
    ).length;

  const successCount =
    jobs.filter(
      (job) =>
        job.status === "SUCCEEDED",
    ).length;

  const failedCount =
    jobs.filter(
      (job) =>
        job.status === "FAILED",
    ).length;

  function handleRetry(
    job: BackgroundJob,
  ) {
    if (
      retryMutation.isPending
      ||
      job.status !== "FAILED"
    ) {
      return;
    }

    retryMutation.mutate(
      job.id,
    );
  }

  return (
    <div
      className="
        space-y-6
      "
    >
      <div
        className="
          flex flex-col gap-3
          sm:flex-row
          sm:items-center
          sm:justify-between
        "
      >
        <div>
          <h1
            className="
              text-2xl font-bold
              text-slate-900
            "
          >
            Background Jobs
          </h1>

          <p
            className="
              mt-1 text-sm
              text-slate-500
            "
          >
            Monitor asynchronous system jobs
            and retry failed work.
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            void jobsQuery.refetch();
          }}
          disabled={jobsQuery.isFetching}
          className="
            inline-flex items-center
            justify-center gap-2
            rounded-lg border
            border-slate-200
            bg-white px-3 py-2
            text-sm font-medium
            text-slate-700
            hover:bg-slate-50
            disabled:opacity-50
          "
        >
          <RefreshCw
            size={16}
            className={
              jobsQuery.isFetching
                ? "animate-spin"
                : ""
            }
          />

          Refresh
        </button>
      </div>

      <div
        className="
          grid gap-4
          sm:grid-cols-2
          xl:grid-cols-4
        "
      >
        <div
          className="
            rounded-xl border
            border-slate-200
            bg-white p-4
          "
        >
          <div
            className="
              flex items-center gap-2
              text-sm font-medium
              text-slate-500
            "
          >
            <Clock3 size={17} />
            Pending
          </div>

          <p
            className="
              mt-2 text-2xl font-bold
              text-slate-900
            "
          >
            {pendingCount}
          </p>
        </div>

        <div
          className="
            rounded-xl border
            border-slate-200
            bg-white p-4
          "
        >
          <div
            className="
              flex items-center gap-2
              text-sm font-medium
              text-blue-600
            "
          >
            <Loader2 size={17} />
            Running
          </div>

          <p
            className="
              mt-2 text-2xl font-bold
              text-slate-900
            "
          >
            {runningCount}
          </p>
        </div>

        <div
          className="
            rounded-xl border
            border-slate-200
            bg-white p-4
          "
        >
          <div
            className="
              flex items-center gap-2
              text-sm font-medium
              text-emerald-600
            "
          >
            <CheckCircle2 size={17} />
            Succeeded
          </div>

          <p
            className="
              mt-2 text-2xl font-bold
              text-slate-900
            "
          >
            {successCount}
          </p>
        </div>

        <div
          className="
            rounded-xl border
            border-slate-200
            bg-white p-4
          "
        >
          <div
            className="
              flex items-center gap-2
              text-sm font-medium
              text-red-600
            "
          >
            <AlertTriangle size={17} />
            Failed
          </div>

          <p
            className="
              mt-2 text-2xl font-bold
              text-slate-900
            "
          >
            {failedCount}
          </p>
        </div>
      </div>

      <div
        className="
          overflow-hidden rounded-xl
          border border-slate-200
          bg-white
        "
      >
        {jobsQuery.isLoading && (
          <div
            className="
              flex items-center
              justify-center gap-2
              px-6 py-16
              text-sm text-slate-500
            "
          >
            <Loader2
              size={18}
              className="animate-spin"
            />

            Loading background jobs...
          </div>
        )}

        {jobsQuery.isError && (
          <div
            className="
              px-6 py-16 text-center
              text-sm text-red-600
            "
          >
            Unable to load background jobs.
          </div>
        )}

        {jobsQuery.isSuccess
          &&
          jobs.length === 0 && (
            <div
              className="
                px-6 py-16 text-center
                text-sm text-slate-500
              "
            >
              No background jobs found.
            </div>
          )}

        {jobsQuery.isSuccess
          &&
          jobs.length > 0 && (
            <div
              className="
                overflow-x-auto
              "
            >
              <table
                className="
                  min-w-full
                  text-left
                "
              >
                <thead
                  className="
                    border-b
                    border-slate-200
                    bg-slate-50
                  "
                >
                  <tr>
                    <th
                      className="
                        px-4 py-3
                        text-xs font-semibold
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Job
                    </th>

                    <th
                      className="
                        px-4 py-3
                        text-xs font-semibold
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Status
                    </th>

                    <th
                      className="
                        px-4 py-3
                        text-xs font-semibold
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Attempts
                    </th>

                    <th
                      className="
                        px-4 py-3
                        text-xs font-semibold
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Created
                    </th>

                    <th
                      className="
                        px-4 py-3
                        text-xs font-semibold
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Completed
                    </th>

                    <th
                      className="
                        px-4 py-3
                        text-xs font-semibold
                        uppercase tracking-wide
                        text-slate-500
                      "
                    >
                      Error
                    </th>

                    <th
                      className="
                        px-4 py-3
                        text-right text-xs
                        font-semibold uppercase
                        tracking-wide
                        text-slate-500
                      "
                    >
                      Actions
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {jobs.map(
                    (job) => (
                      <JobRow
                        key={job.id}
                        job={job}
                        retrying={
                          retryMutation.isPending
                          &&
                          retryMutation.variables
                            === job.id
                        }
                        onRetry={
                          handleRetry
                        }
                      />
                    ),
                  )}
                </tbody>
              </table>
            </div>
          )}
      </div>
    </div>
  );
}
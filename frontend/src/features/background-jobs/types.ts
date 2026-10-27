export type BackgroundJobType =
  | "BANK_STATEMENT_IMPORT"
  | "DOCUMENT_EMAIL"
  | "NOTIFICATION";

export type BackgroundJobStatus =
  | "PENDING"
  | "RUNNING"
  | "RETRYING"
  | "SUCCEEDED"
  | "FAILED";

export interface BackgroundJob {
  id: string;
  job_type: BackgroundJobType;
  status: BackgroundJobStatus;

  attempts: number;
  max_attempts: number;

  available_at: string | null;
  started_at: string | null;
  completed_at: string | null;

  last_error: string | null;
  result: Record<string, unknown>;

  created_at: string;
  updated_at: string;
}

export interface BackgroundJobListResponse {
  results: BackgroundJob[];
  count: number;
}

export interface BackgroundJobListParameters {
  status?: BackgroundJobStatus;
  job_type?: BackgroundJobType;
  limit?: number;
}
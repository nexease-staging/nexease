export type NotificationType =
  | "SYSTEM"
  | "JOB_SUCCEEDED"
  | "JOB_FAILED"
  | "IMPORT_COMPLETED"
  | "DOCUMENT_SENT";

export type NotificationSeverity =
  | "INFO"
  | "SUCCESS"
  | "WARNING"
  | "ERROR";

export interface Notification {
  id: string;
  notification_type: NotificationType;

  title: string;
  message: string;

  severity: NotificationSeverity;

  resource_type: string | null;
  resource_id: string | null;
  action_url: string | null;

  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  results: Notification[];
  count: number;
  unread_count: number;
}

export interface NotificationListParameters {
  is_read?: boolean;
  limit?: number;
}
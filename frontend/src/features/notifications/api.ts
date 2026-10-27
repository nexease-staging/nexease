import {
  apiRequest,
} from "@/lib/api/client";

import type {
  Notification,
  NotificationListParameters,
  NotificationListResponse,
} from "@/features/notifications/types";

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

export async function listNotifications(
  parameters:
    NotificationListParameters = {},
): Promise<NotificationListResponse> {
  const response =
    await apiRequest<
      NotificationListResponse
    >(
      (
        "/notifications/"
        +
        buildQuery({
          is_read:
            parameters.is_read,

          limit:
            parameters.limit,
        })
      ),
    );

  return response.data;
}

export async function markNotificationRead(
  notificationId: string,
): Promise<Notification> {
  const response =
    await apiRequest<
      Notification
    >(
      (
        "/notifications/"
        +
        `${notificationId}/read/`
      ),
      {
        method: "POST",
        body: {},
      },
    );

  return response.data;
}
import type {
  NotificationListParameters,
} from "@/features/notifications/types";

export const notificationQueryKeys = {
  all: [
    "notifications",
  ] as const,

  lists: () => [
    ...notificationQueryKeys.all,
    "list",
  ] as const,

  list: (
    parameters:
      NotificationListParameters,
  ) => [
    ...notificationQueryKeys.lists(),
    parameters,
  ] as const,
};
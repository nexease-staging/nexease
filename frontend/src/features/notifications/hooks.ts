"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  listNotifications,
  markNotificationRead,
} from "@/features/notifications/api";

import {
  notificationQueryKeys,
} from "@/features/notifications/query-keys";

import type {
  NotificationListParameters,
} from "@/features/notifications/types";

export function useNotificationList(
  parameters:
    NotificationListParameters = {},
  enabled = true,
) {
  return useQuery({
    queryKey:
      notificationQueryKeys.list(
        parameters,
      ),

    queryFn: () =>
      listNotifications(
        parameters,
      ),

    enabled,
  });
}

export function useMarkNotificationRead() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn:
      markNotificationRead,

    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey:
          notificationQueryKeys.lists(),
      });
    },
  });
}
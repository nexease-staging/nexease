"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  Bell,
  Check,
  Loader2,
} from "lucide-react";

import {
  useMarkNotificationRead,
  useNotificationList,
} from "@/features/notifications/hooks";

import type {
  Notification,
  NotificationSeverity,
} from "@/features/notifications/types";


function severityClass(
  severity: NotificationSeverity,
): string {
  switch (severity) {
    case "SUCCESS":
      return (
        "bg-emerald-100 "
        +
        "text-emerald-700"
      );

    case "WARNING":
      return (
        "bg-amber-100 "
        +
        "text-amber-700"
      );

    case "ERROR":
      return (
        "bg-red-100 "
        +
        "text-red-700"
      );

    default:
      return (
        "bg-blue-100 "
        +
        "text-blue-700"
      );
  }
}


function formatNotificationDate(
  value: string,
): string {
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


interface NotificationItemProps {
  notification: Notification;
  markingRead: boolean;

  onMarkRead: (
    notification: Notification,
  ) => void;
}


function NotificationItem({
  notification,
  markingRead,
  onMarkRead,
}: NotificationItemProps) {
  return (
    <div
      className={`
        border-b border-slate-100
        px-4 py-3
        last:border-b-0
        ${
          notification.is_read
            ? "bg-white"
            : "bg-blue-50/50"
        }
      `}
    >
      <div
        className="
          flex items-start gap-3
        "
      >
        <div
          className={`
            mt-0.5 flex size-8
            shrink-0 items-center
            justify-center rounded-full
            text-xs font-bold
            ${severityClass(
              notification.severity,
            )}
          `}
        >
          {notification.severity[0]}
        </div>

        <div
          className="
            min-w-0 flex-1
          "
        >
          <div
            className="
              flex items-start
              justify-between gap-2
            "
          >
            <p
              className="
                text-sm font-semibold
                text-slate-900
              "
            >
              {notification.title}
            </p>

            {!notification.is_read && (
              <span
                className="
                  mt-1 size-2 shrink-0
                  rounded-full bg-blue-600
                "
                aria-label="Unread"
              />
            )}
          </div>

          <p
            className="
              mt-1 text-sm
              leading-5 text-slate-600
            "
          >
            {notification.message}
          </p>

          <div
            className="
              mt-2 flex items-center
              justify-between gap-2
            "
          >
            <span
              className="
                text-xs text-slate-400
              "
            >
              {formatNotificationDate(
                notification.created_at,
              )}
            </span>

            {!notification.is_read && (
              <button
                type="button"
                disabled={markingRead}
                onClick={() => {
                  onMarkRead(
                    notification,
                  );
                }}
                className="
                  inline-flex items-center
                  gap-1 rounded-md px-2
                  py-1 text-xs font-medium
                  text-blue-700
                  hover:bg-blue-100
                  disabled:opacity-50
                "
              >
                {markingRead ? (
                  <Loader2
                    size={13}
                    className="animate-spin"
                  />
                ) : (
                  <Check size={13} />
                )}

                Mark read
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


export default function NotificationMenu() {
  const [
    open,
    setOpen,
  ] = useState(false);

  const containerRef =
    useRef<HTMLDivElement>(
      null,
    );

  const notificationsQuery =
    useNotificationList(
      {
        limit: 20,
      },
      open,
    );

  const markReadMutation =
    useMarkNotificationRead();

  useEffect(() => {
    function handlePointerDown(
      event: MouseEvent,
    ) {
      if (
        containerRef.current
        &&
        !containerRef.current.contains(
          event.target as Node,
        )
      ) {
        setOpen(false);
      }
    }

    document.addEventListener(
      "mousedown",
      handlePointerDown,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handlePointerDown,
      );
    };
  }, []);

  const data =
    notificationsQuery.data;

  const unreadCount =
    data?.unread_count ?? 0;

  function handleMarkRead(
    notification: Notification,
  ) {
    if (
      notification.is_read
      ||
      markReadMutation.isPending
    ) {
      return;
    }

    markReadMutation.mutate(
      notification.id,
    );
  }

  return (
    <div
      ref={containerRef}
      className="relative"
    >
      <button
        type="button"
        aria-label="Notifications"
        aria-expanded={open}
        onClick={() => {
          setOpen(
            (current) => !current,
          );
        }}
        className="
          relative rounded-lg p-2
          text-slate-500
          hover:bg-slate-100
          hover:text-slate-700
        "
      >
        <Bell size={20} />

        {unreadCount > 0 && (
          <span
            className="
              absolute -right-0.5
              -top-0.5 flex min-w-4
              items-center justify-center
              rounded-full bg-red-600
              px-1 text-[10px]
              font-bold leading-4
              text-white
            "
          >
            {unreadCount > 99
              ? "99+"
              : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div
          className="
            absolute right-0 top-11
            z-50 w-[min(24rem,calc(100vw-2rem))]
            overflow-hidden rounded-xl
            border border-slate-200
            bg-white shadow-xl
          "
        >
          <div
            className="
              flex items-center
              justify-between border-b
              border-slate-200 px-4
              py-3
            "
          >
            <div>
              <p
                className="
                  text-sm font-semibold
                  text-slate-900
                "
              >
                Notifications
              </p>

              <p
                className="
                  text-xs text-slate-500
                "
              >
                {unreadCount === 1
                  ? "1 unread notification"
                  : `${unreadCount} unread notifications`}
              </p>
            </div>
          </div>

          <div
            className="
              max-h-[28rem]
              overflow-y-auto
            "
          >
            {notificationsQuery.isLoading && (
              <div
                className="
                  flex items-center
                  justify-center gap-2
                  px-4 py-10
                  text-sm text-slate-500
                "
              >
                <Loader2
                  size={18}
                  className="animate-spin"
                />

                Loading notifications...
              </div>
            )}

            {notificationsQuery.isError && (
              <div
                className="
                  px-4 py-8 text-center
                  text-sm text-red-600
                "
              >
                Unable to load notifications.
              </div>
            )}

            {notificationsQuery.isSuccess
              &&
              notificationsQuery.data.results.length === 0 && (
                <div
                  className="
                    px-4 py-10 text-center
                    text-sm text-slate-500
                  "
                >
                  No notifications yet.
                </div>
              )}

            {notificationsQuery.isSuccess
              &&
              notificationsQuery.data.results.map(
                (notification) => (
                  <NotificationItem
                    key={
                      notification.id
                    }
                    notification={
                      notification
                    }
                    markingRead={
                      markReadMutation.isPending
                      &&
                      markReadMutation.variables
                        === notification.id
                    }
                    onMarkRead={
                      handleMarkRead
                    }
                  />
                ),
              )}
          </div>
        </div>
      )}
    </div>
  );
}
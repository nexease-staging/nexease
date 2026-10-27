"use client";
import SearchSelect from "@/components/search-select";


import {
  useMemo,
  useState,
} from "react";

import {
  RefreshCw,
  Search,
  ShieldCheck,
} from "lucide-react";

import {
  useAuthenticationAuditList,
} from "@/features/audit";

import type {
  AuthenticationAuditEventType,
} from "@/features/audit";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  hasPermission,
} from "@/lib/authorization/permissions";


const EVENT_OPTIONS: Array<{
  value: AuthenticationAuditEventType;
  label: string;
}> = [
  {
    value: "LOGIN_SUCCESS",
    label: "Login success",
  },
  {
    value: "LOGIN_FAILED",
    label: "Login failed",
  },
  {
    value: "LOGIN_BLOCKED",
    label: "Login blocked",
  },
  {
    value: "LOGOUT",
    label: "Logout",
  },
  {
    value: "LOGOUT_ALL",
    label: "Logout all",
  },
];


function eventLabel(
  eventType: AuthenticationAuditEventType,
) {
  return (
    EVENT_OPTIONS.find(
      (option) =>
        option.value === eventType,
    )?.label
    ??
    eventType
  );
}


function formatDateTime(
  value: string | null,
) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return date.toLocaleString();
}


export default function AuditPage() {
  const {
    authentication,
  } = useAuth();

  const [
    eventType,
    setEventType,
  ] = useState<
    AuthenticationAuditEventType
    | ""
  >("");

  const [
    identifier,
    setIdentifier,
  ] = useState("");

  const [
    ipAddress,
    setIpAddress,
  ] = useState("");

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const canRead =
    hasPermission(
      permissions,
      "accounting_audit.read",
    );

  const parameters = useMemo(
    () => ({
      event_type:
        eventType
        ||
        undefined,

      identifier:
        identifier.trim()
        ||
        undefined,

      ip_address:
        ipAddress.trim()
        ||
        undefined,

      limit: 100,
    }),
    [
      eventType,
      identifier,
      ipAddress,
    ],
  );

  const auditQuery =
    useAuthenticationAuditList(
      parameters,
      canRead,
    );

  if (!authentication) {
    return null;
  }

  if (!canRead) {
    return (
      <section
        className="
          rounded-2xl border
          border-amber-200
          bg-amber-50 p-6
        "
      >
        <h1
          className="
            text-lg font-semibold
            text-amber-900
          "
        >
          Audit access restricted
        </h1>

        <p
          className="
            mt-2 text-sm
            text-amber-800
          "
        >
          Your role does not include the
          accounting_audit.read permission.
        </p>
      </section>
    );
  }

  const logs =
    auditQuery.data
      ?.authentication_audit_logs
    ??
    [];

  return (
    <section className="space-y-6">
      <div
        className="
          flex flex-col gap-4
          sm:flex-row
          sm:items-center
          sm:justify-between
        "
      >
        <div>
          <div
            className="
              flex items-center gap-2
            "
          >
            <ShieldCheck
              size={25}
              className="text-blue-600"
            />

            <h1
              className="
                text-2xl font-bold
                text-slate-900
              "
            >
              Authentication Audit
            </h1>
          </div>

          <p
            className="
              mt-1 text-sm
              text-slate-600
            "
          >
            Review organization login,
            logout, blocked access, and
            authentication integrity events.
          </p>
        </div>

        <button
          type="button"
          disabled={
            auditQuery.isFetching
          }
          onClick={() => {
            void auditQuery.refetch();
          }}
          className="
            inline-flex items-center
            justify-center gap-2
            rounded-lg border
            border-slate-300
            bg-white px-4 py-2
            text-sm font-semibold
            text-slate-700
            hover:bg-slate-50
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          <RefreshCw
            size={16}
            className={
              auditQuery.isFetching
                ? "animate-spin"
                : undefined
            }
          />

          Refresh
        </button>
      </div>

      <div
        className="
          grid gap-4 rounded-2xl
          border border-slate-200
          bg-white p-4 shadow-sm
          md:grid-cols-3
        "
      >
        <label className="space-y-1.5">
          <span
            className="
              text-sm font-semibold
              text-slate-700
            "
          >
            Event
          </span>

          <SearchSelect
            value={eventType}
            onChange={(event) => {
              setEventType(
                event.target.value as (
                  AuthenticationAuditEventType
                  |
                  ""
                ),
              );
            }}
            className="
              h-10 w-full rounded-lg
              border border-slate-300
              bg-white px-3
              text-sm text-slate-900
              outline-none
              focus:border-blue-500
              focus:ring-2
              focus:ring-blue-100
            "
          >
            <option value="">
              All events
            </option>

            {EVENT_OPTIONS.map(
              (option) => (
                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label}
                </option>
              ),
            )}
          </SearchSelect>
        </label>

        <label className="space-y-1.5">
          <span
            className="
              text-sm font-semibold
              text-slate-700
            "
          >
            User / identifier
          </span>

          <div className="relative">
            <Search
              size={17}
              className="
                pointer-events-none
                absolute left-3 top-1/2
                -translate-y-1/2
                text-slate-400
              "
            />

            <input
              type="search"
              value={identifier}
              placeholder="Email or identifier"
              onChange={(event) => {
                setIdentifier(
                  event.target.value,
                );
              }}
              className="
                h-10 w-full rounded-lg
                border border-slate-300
                bg-white pl-9 pr-3
                text-sm text-slate-900
                placeholder:text-slate-400
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-100
              "
            />
          </div>
        </label>

        <label className="space-y-1.5">
          <span
            className="
              text-sm font-semibold
              text-slate-700
            "
          >
            IP address
          </span>

          <input
            type="search"
            value={ipAddress}
            placeholder="Example: 127.0.0.1"
            onChange={(event) => {
              setIpAddress(
                event.target.value,
              );
            }}
            className="
              h-10 w-full rounded-lg
              border border-slate-300
              bg-white px-3
              text-sm text-slate-900
              placeholder:text-slate-400
              outline-none
              focus:border-blue-500
              focus:ring-2
              focus:ring-blue-100
            "
          />
        </label>
      </div>

      <div
        className="
          overflow-hidden rounded-2xl
          border border-slate-200
          bg-white shadow-sm
        "
      >
        {auditQuery.isPending ? (
          <div
            className="
              flex min-h-72
              items-center justify-center
              text-sm text-slate-500
            "
          >
            Loading authentication audit…
          </div>
        ) : auditQuery.isError ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              gap-3 p-6 text-center
            "
          >
            <p
              className="
                text-sm text-red-700
              "
            >
              {auditQuery.error.message}
            </p>

            <button
              type="button"
              onClick={() => {
                void auditQuery.refetch();
              }}
              className="
                rounded-lg bg-slate-900
                px-4 py-2
                text-sm font-semibold
                text-white
              "
            >
              Try again
            </button>
          </div>
        ) : logs.length === 0 ? (
          <div
            className="
              flex min-h-72 flex-col
              items-center justify-center
              p-6 text-center
            "
          >
            <ShieldCheck
              size={36}
              className="text-slate-300"
            />

            <h2
              className="
                mt-3 font-semibold
                text-slate-900
              "
            >
              No audit events found
            </h2>

            <p
              className="
                mt-1 text-sm
                text-slate-500
              "
            >
              Change the filters or wait
              for new authentication activity.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table
              className="
                min-w-full divide-y
                divide-slate-200
              "
            >
              <thead className="bg-slate-50">
                <tr>
                  {[
                    "Event",
                    "User",
                    "Identifier",
                    "IP address",
                    "Time",
                    "Integrity",
                  ].map(
                    (heading) => (
                      <th
                        key={heading}
                        scope="col"
                        className="
                          whitespace-nowrap
                          px-4 py-3
                          text-left text-xs
                          font-semibold uppercase
                          tracking-wide
                          text-slate-500
                        "
                      >
                        {heading}
                      </th>
                    ),
                  )}
                </tr>
              </thead>

              <tbody
                className="
                  divide-y divide-slate-100
                "
              >
                {logs.map(
                  (log) => (
                    <tr
                      key={log.id}
                      className="
                        hover:bg-slate-50
                      "
                    >
                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                        "
                      >
                        <span
                          className="
                            inline-flex
                            rounded-full border
                            border-blue-200
                            bg-blue-50
                            px-2.5 py-1
                            text-xs font-semibold
                            text-blue-700
                          "
                        >
                          {eventLabel(
                            log.event_type,
                          )}
                        </span>
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                          text-sm text-slate-700
                        "
                      >
                        {
                          log.user?.email
                          ??
                          "—"
                        }
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                          text-sm text-slate-600
                        "
                      >
                        {
                          log.identifier
                          ||
                          "—"
                        }
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                          font-mono text-xs
                          text-slate-600
                        "
                      >
                        {
                          log.ip_address
                          ||
                          "—"
                        }
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                          text-sm text-slate-600
                        "
                      >
                        {formatDateTime(
                          log.created_at,
                        )}
                      </td>

                      <td
                        className="
                          whitespace-nowrap
                          px-4 py-4
                        "
                      >
                        <span
                          className={`
                            inline-flex
                            rounded-full border
                            px-2.5 py-1
                            text-xs font-semibold
                            ${
                              (
                                log.integrity.hashed
                                &&
                                log.integrity.verified
                              )
                                ? (
                                    "border-emerald-200 "
                                    +
                                    "bg-emerald-50 "
                                    +
                                    "text-emerald-700"
                                  )
                                : (
                                    "border-red-200 "
                                    +
                                    "bg-red-50 "
                                    +
                                    "text-red-700"
                                  )
                            }
                          `}
                        >
                          {
                            (
                              log.integrity.hashed
                              &&
                              log.integrity.verified
                            )
                              ? "Verified"
                              : "Warning"
                          }
                        </span>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}

        {!auditQuery.isPending
        && !auditQuery.isError ? (
          <div
            className="
              border-t border-slate-200
              px-4 py-3
            "
          >
            <p
              className="
                text-sm text-slate-600
              "
            >
              Showing {logs.length} of up to
              {" "}
              {parameters.limit}
              {" "}
              authentication events.
            </p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
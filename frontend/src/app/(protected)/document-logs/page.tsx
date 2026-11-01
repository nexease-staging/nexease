"use client";
import SearchSelect from "@/components/search-select";


import {
  useState,
} from "react";

import {
  FileClock,
  Mail,
  RefreshCw,
  Search,
} from "lucide-react";

import {
  useDocumentAccessLogs,
  useDocumentAccessLogSummary,
  useDocumentDeliveryLogs,
  useDocumentDeliveryLogSummary,
} from "@/features/documents/hooks";

import type {
  DocumentAccessLogParameters,
  DocumentDeliveryLogParameters,
  DocumentType,
} from "@/features/documents/types";

import {
  APIRequestError,
} from "@/lib/api/client";

const documentTypes: Array<{
  value: DocumentType;
  label: string;
}> = [
  {
    value: "INVOICE",
    label: "Invoice",
  },
  {
    value: "SALES_ORDER",
    label: "Sales order",
  },
  {
    value: "CREDIT_NOTE",
    label: "Credit note",
  },
  {
    value: "CUSTOMER_PAYMENT",
    label: "Customer payment",
  },
  {
    value: "PURCHASE_ORDER",
    label: "Purchase order",
  },
  {
    value: "VENDOR_BILL",
    label: "Vendor bill",
  },
  {
    value: "VENDOR_DEBIT_NOTE",
    label: "Vendor debit note",
  },
  {
    value: "SUPPLIER_PAYMENT",
    label: "Supplier payment",
  },
  {
    value: "GOODS_RECEIPT",
    label: "Goods receipt",
  },
];

type ActivityTab =
  | "access"
  | "delivery";

function getErrorMessage(
  error: unknown,
): string {
  if (
    error
    instanceof
    APIRequestError
  ) {
    return error.message;
  }

  if (
    error
    instanceof
    Error
  ) {
    return error.message;
  }

  return "Unable to load document activity.";
}

function formatDateTime(
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
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(date);
}

function formatLabel(
  value: string,
): string {
  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}

function formatSummaryValue(
  value: unknown,
): string {
  if (
    value === null
    ||
    value === undefined
  ) {
    return "—";
  }

  if (
    typeof value
    ===
    "boolean"
  ) {
    return value
      ? "Yes"
      : "No";
  }

  if (
    typeof value
      ===
      "string"
    ||
    typeof value
      ===
      "number"
  ) {
    return String(value);
  }

  if (
    Array.isArray(value)
  ) {
    return value
      .map((item) => {
        if (
          typeof item
          !==
          "object"
          ||
          item === null
        ) {
          return String(item);
        }

        const record =
          item as Record<
            string,
            unknown
          >;

        const label =
          record.document_type
          ??
          record.status
          ??
          record.channel
          ??
          record.document_number
          ??
          record.recipient
          ??
          record.id;

        const count =
          record.count;

        if (
          label !== undefined
          &&
          count !== undefined
        ) {
          return `${formatLabel(
            String(label),
          )}: ${String(count)}`;
        }

        if (
          record.document_number
          !==
          undefined
        ) {
          return formatLabel(
            String(
              record.document_number,
            ),
          );
        }

        return "Activity";
      })
      .join(" • ");
  }

  return "—";
}

function isSummaryList(
  value: unknown,
): value is Array<
  Record<string, unknown>
> {
  return (
    Array.isArray(value)
    &&
    value.every(
      (item) =>
        typeof item
          ===
          "object"
        &&
        item !== null,
    )
  );
}

export default function DocumentLogsPage() {
  const [
    activeTab,
    setActiveTab,
  ] = useState<ActivityTab>(
    "access",
  );

  const [
    accessDocumentType,
    setAccessDocumentType,
  ] = useState("");

  const [
    accessAction,
    setAccessAction,
  ] = useState("");

  const [
    accessDocumentNumber,
    setAccessDocumentNumber,
  ] = useState("");

  const [
    accessParameters,
    setAccessParameters,
  ] = useState<
    DocumentAccessLogParameters
  >({
    limit: 100,
  });

  const [
    deliveryDocumentType,
    setDeliveryDocumentType,
  ] = useState("");

  const [
    deliveryStatus,
    setDeliveryStatus,
  ] = useState("");

  const [
    deliveryRecipient,
    setDeliveryRecipient,
  ] = useState("");

  const [
    deliveryDocumentNumber,
    setDeliveryDocumentNumber,
  ] = useState("");

  const [
    deliveryParameters,
    setDeliveryParameters,
  ] = useState<
    DocumentDeliveryLogParameters
  >({
    limit: 100,
  });

  const accessQuery =
    useDocumentAccessLogs(
      accessParameters,
      activeTab === "access",
    );

  const accessSummaryQuery =
    useDocumentAccessLogSummary(
      activeTab === "access",
    );

  const deliveryQuery =
    useDocumentDeliveryLogs(
      deliveryParameters,
      activeTab === "delivery",
    );

  const deliverySummaryQuery =
    useDocumentDeliveryLogSummary(
      activeTab === "delivery",
    );

  function applyAccessFilters():
    void {
    setAccessParameters({
      document_type:
        accessDocumentType
        ||
        undefined,

      action:
        accessAction.trim()
        ||
        undefined,

      document_number:
        accessDocumentNumber
          .trim()
        ||
        undefined,

      limit: 100,
    });
  }

  function clearAccessFilters():
    void {
    setAccessDocumentType("");
    setAccessAction("");
    setAccessDocumentNumber("");

    setAccessParameters({
      limit: 100,
    });
  }

  function applyDeliveryFilters():
    void {
    setDeliveryParameters({
      document_type:
        deliveryDocumentType
        ||
        undefined,

      status:
        deliveryStatus.trim()
        ||
        undefined,

      recipient:
        deliveryRecipient.trim()
        ||
        undefined,

      document_number:
        deliveryDocumentNumber
          .trim()
        ||
        undefined,

      limit: 100,
    });
  }

  function clearDeliveryFilters():
    void {
    setDeliveryDocumentType("");
    setDeliveryStatus("");
    setDeliveryRecipient("");
    setDeliveryDocumentNumber("");

    setDeliveryParameters({
      limit: 100,
    });
  }

  const accessLogs =
    accessQuery
      .data
      ?.logs
    ??
    [];

  const deliveryLogs =
    deliveryQuery
      .data
      ?.logs
    ??
    [];

    const accessSummary =
    accessSummaryQuery.data
    ??
    {};

    const deliverySummary =
    deliverySummaryQuery.data
    ??
    {};

  return (
    <div
      className="
        mx-auto max-w-7xl
        space-y-6
      "
    >
      <header>
        <p
          className="
            text-sm font-semibold
            text-blue-600
          "
        >
          Documents
        </p>

        <h1
          className="
            mt-1 text-3xl
            font-bold text-slate-900
          "
        >
          Document Activity
        </h1>

        <p
          className="
            mt-2 max-w-3xl
            text-sm leading-6
            text-slate-600
          "
        >
          Review PDF access,
          document activity and
          email-delivery history.
        </p>
      </header>

      <div
        className="
          inline-flex rounded-xl
          border border-slate-200
          bg-white p-1 shadow-sm
        "
      >
        <button
          type="button"
          onClick={() => {
            setActiveTab(
              "access",
            );
          }}
          className={`
            inline-flex items-center
            gap-2 rounded-lg
            px-4 py-2 text-sm
            font-semibold
            ${
              activeTab
              ===
              "access"
                ? (
                    "bg-blue-600 "
                    +
                    "text-white"
                  )
                : (
                    "text-slate-600 "
                    +
                    "hover:bg-slate-50"
                  )
            }
          `}
        >
          <FileClock size={17} />
          Access Logs
        </button>

        <button
          type="button"
          onClick={() => {
            setActiveTab(
              "delivery",
            );
          }}
          className={`
            inline-flex items-center
            gap-2 rounded-lg
            px-4 py-2 text-sm
            font-semibold
            ${
              activeTab
              ===
              "delivery"
                ? (
                    "bg-blue-600 "
                    +
                    "text-white"
                  )
                : (
                    "text-slate-600 "
                    +
                    "hover:bg-slate-50"
                  )
            }
          `}
        >
          <Mail size={17} />
          Delivery Logs
        </button>
      </div>

      {activeTab === "access"
        ? (
            
            <>
            <SummarySection
              title="Access Summary"
              summary={
                accessSummary
              }
              isLoading={
                accessSummaryQuery
                  .isLoading
              }
              error={
                accessSummaryQuery
                  .error
              }
            />

            <section
              className="
                rounded-2xl border
                border-slate-200
                bg-white p-5
                shadow-sm
              "
            >
              <div
                className="nx-list-filters
                  grid gap-4
                  md:grid-cols-3
                "
              >
                <DocumentTypeField
                  value={
                    accessDocumentType
                  }
                  onChange={
                    setAccessDocumentType
                  }
                />

                <label
                  className="
                    block text-sm
                    font-medium
                    text-slate-700
                  "
                >
                  Action

                  <input
                    type="text"
                    value={
                      accessAction
                    }
                    onChange={(event) => {
                      setAccessAction(
                        event
                          .currentTarget
                          .value,
                      );
                    }}
                    placeholder={
                      "e.g. PDF"
                    }
                    className="
                      mt-2 w-full
                      rounded-lg border
                      border-slate-300
                      px-3 py-2
                      text-sm outline-none
                      focus:border-blue-500
                      focus:ring-2
                      focus:ring-blue-100
                    "
                  />
                </label>

                <label
                  className="
                    block text-sm
                    font-medium
                    text-slate-700
                  "
                >
                  Document number

                  <div
                    className="
                      relative mt-2
                    "
                  >
                    <Search
                      size={16}
                      className="
                        pointer-events-none
                        absolute left-3
                        top-1/2
                        -translate-y-1/2
                        text-slate-400
                      "
                    />

                    <input
                      type="text"
                      value={
                        accessDocumentNumber
                      }
                      onChange={
                        (event) => {
                          setAccessDocumentNumber(
                            event
                              .currentTarget
                              .value,
                          );
                        }
                      }
                      className="
                        w-full rounded-lg
                        border
                        border-slate-300
                        py-2 pl-9 pr-3
                        text-sm outline-none
                        focus:border-blue-500
                        focus:ring-2
                        focus:ring-blue-100
                      "
                    />
                  </div>
                </label>
              </div>

              <FilterActions
                onApply={
                  applyAccessFilters
                }
                onClear={
                  clearAccessFilters
                }
                disabled={
                  accessQuery
                    .isFetching
                }
              />
            </section>

            <AccessLogTable
              logs={accessLogs}
              isLoading={
                accessQuery
                  .isLoading
                ||
                accessQuery
                  .isFetching
              }
              error={
                accessQuery.error
              }
            />
          </>
        )
        : (
          <>
            <SummarySection
              title="Delivery Summary"
              summary={
                deliverySummary
              }
              isLoading={
                deliverySummaryQuery
                  .isLoading
              }
              error={
                deliverySummaryQuery
                  .error
              }
            />

            <section
              className="
                rounded-2xl border
                border-slate-200
                bg-white p-5
                shadow-sm
              "
            >
              <div
                className="nx-list-filters
                  grid gap-4
                  md:grid-cols-2
                  xl:grid-cols-4
                "
              >
                <DocumentTypeField
                  value={
                    deliveryDocumentType
                  }
                  onChange={
                    setDeliveryDocumentType
                  }
                />

                <label
                  className="
                    block text-sm
                    font-medium
                    text-slate-700
                  "
                >
                  Status

                  <input
                    type="text"
                    value={
                      deliveryStatus
                    }
                    onChange={(event) => {
                      setDeliveryStatus(
                        event
                          .currentTarget
                          .value,
                      );
                    }}
                    placeholder={
                      "Delivery status"
                    }
                    className="
                      mt-2 w-full
                      rounded-lg border
                      border-slate-300
                      px-3 py-2
                      text-sm outline-none
                    "
                  />
                </label>

                <label
                  className="
                    block text-sm
                    font-medium
                    text-slate-700
                  "
                >
                  Recipient

                  <input
                    type="text"
                    value={
                      deliveryRecipient
                    }
                    onChange={(event) => {
                      setDeliveryRecipient(
                        event
                          .currentTarget
                          .value,
                      );
                    }}
                    placeholder={
                      "Email recipient"
                    }
                    className="
                      mt-2 w-full
                      rounded-lg border
                      border-slate-300
                      px-3 py-2
                      text-sm outline-none
                    "
                  />
                </label>

                <label
                  className="
                    block text-sm
                    font-medium
                    text-slate-700
                  "
                >
                  Document number

                  <input
                    type="text"
                    value={
                      deliveryDocumentNumber
                    }
                    onChange={(event) => {
                      setDeliveryDocumentNumber(
                        event
                          .currentTarget
                          .value,
                      );
                    }}
                    className="
                      mt-2 w-full
                      rounded-lg border
                      border-slate-300
                      px-3 py-2
                      text-sm outline-none
                    "
                  />
                </label>
              </div>

              <FilterActions
                onApply={
                  applyDeliveryFilters
                }
                onClear={
                  clearDeliveryFilters
                }
                disabled={
                  deliveryQuery
                    .isFetching
                }
              />
            </section>

            <DeliveryLogTable
              logs={deliveryLogs}
              isLoading={
                deliveryQuery
                  .isLoading
                ||
                deliveryQuery
                  .isFetching
              }
              error={
                deliveryQuery.error
              }
            />
          </>
        )}
    </div>
  );
}

function DocumentTypeField({
  value,
  onChange,
}: {
  value: string;
  onChange: (
    value: string,
  ) => void;
}) {
  return (
    <label
      className="
        block text-sm
        font-medium text-slate-700
      "
    >
      Document type

      <SearchSelect
        value={value}
        onChange={(event) => {
          onChange(
            event.currentTarget.value,
          );
        }}
        className="
          mt-2 w-full rounded-lg
          border border-slate-300
          bg-white px-3 py-2
          text-sm outline-none
          focus:border-blue-500
          focus:ring-2
          focus:ring-blue-100
        "
      >
        <option value="">
          All document types
        </option>

        {documentTypes.map(
          (documentType) => (
            <option
              key={
                documentType.value
              }
              value={
                documentType.value
              }
            >
              {documentType.label}
            </option>
          ),
        )}
      </SearchSelect>
    </label>
  );
}

function FilterActions({
  onApply,
  onClear,
  disabled,
}: {
  onApply: () => void;
  onClear: () => void;
  disabled: boolean;
}) {
  return (
    <div
      className="
        mt-4 flex flex-wrap
        justify-end gap-2
      "
    >
      <button
        type="button"
        disabled={disabled}
        onClick={onClear}
        className="
          rounded-lg border
          border-slate-300
          bg-white px-4 py-2
          text-sm font-semibold
          text-slate-700
          hover:bg-slate-50
          disabled:opacity-50
        "
      >
        Clear
      </button>

      <button
        type="button"
        disabled={disabled}
        onClick={onApply}
        className="
          rounded-lg bg-blue-600
          px-4 py-2
          text-sm font-semibold
          text-white
          hover:bg-blue-700
          disabled:opacity-50
        "
      >
        Apply filters
      </button>
    </div>
  );
}

function SummarySection({
  title,
  summary,
  isLoading,
  error,
}: {
  title: string;
  summary:
    Record<string, unknown>;
  isLoading: boolean;
  error: unknown;
}) {
  const entries =
    Object.entries(summary);

  return (
    <section
      className="
        rounded-2xl border
        border-slate-200
        bg-white p-5 shadow-sm
      "
    >
      <h2
        className="
          font-bold text-slate-900
        "
      >
        {title}
      </h2>

      {isLoading ? (
        <p
          className="
            mt-4 text-sm
            text-slate-500
          "
        >
          Loading summary...
        </p>
      ) : error ? (
        <p
          role="alert"
          className="
            mt-4 text-sm
            text-red-700
          "
        >
          {getErrorMessage(error)}
        </p>
      ) : entries.length === 0 ? (
        <p
          className="
            mt-4 text-sm
            text-slate-500
          "
        >
          No summary data available.
        </p>
      ) : (
        <div
          className="
            mt-4 grid gap-3
            sm:grid-cols-2
            lg:grid-cols-4
          "
        >
            {entries.map(
            ([key, value]) => (
                <div
                key={key}
                className="
                    rounded-xl
                    border border-slate-200
                    bg-slate-50 p-4
                "
                >
                <p
                    className="
                    text-xs font-semibold
                    uppercase tracking-wide
                    text-slate-500
                    "
                >
                    {formatLabel(key)}
                </p>

                {isSummaryList(value) ? (
                    <div
                    className="
                        mt-3 space-y-2
                    "
                    >
                    {value.map(
                        (item, index) => {
                        const label =
                            item.document_type
                            ??
                            item.status
                            ??
                            item.channel
                            ??
                            item.document_number
                            ??
                            item.recipient
                            ??
                            `Item ${index + 1}`;

                        const count =
                            item.count;

                        return (
                            <div
                            key={`${key}-${index}`}
                            className="
                                flex items-center
                                justify-between
                                gap-4 rounded-lg
                                border border-slate-200
                                bg-white px-3 py-2
                            "
                            >
                            <span
                                className="
                                text-sm font-medium
                                text-slate-700
                                "
                            >
                                {formatLabel(
                                String(label),
                                )}
                            </span>

                            {count !== undefined ? (
                                <span
                                className="
                                    text-sm font-bold
                                    text-slate-900
                                "
                                >
                                {String(count)}
                                </span>
                            ) : null}
                            </div>
                        );
                        },
                    )}
                    </div>
                ) : (
                    <p
                    className="
                        mt-2 break-words
                        text-sm font-bold
                        text-slate-900
                    "
                    >
                    {
                        formatSummaryValue(
                        value,
                        )
                    }
                    </p>
                )}
                </div>
            ),
            )}        </div>
      )}
    </section>
  );
}

function AccessLogTable({
  logs,
  isLoading,
  error,
}: {
  logs: Array<{
    id: string;
    user:
      | {
          id: string;
          email: string;
        }
      | null;
    document_type: string;
    document_number: string;
    action: string;
    created_at:
      | string
      | null;
  }>;
  isLoading: boolean;
  error: unknown;
}) {
  return (
    <LogSection
      title="Access history"
      icon={
        <FileClock size={19} />
      }
    >
      {isLoading ? (
        <LoadingRow
          text="Loading access logs..."
        />
      ) : error ? (
        <ErrorRow
          message={
            getErrorMessage(error)
          }
        />
      ) : logs.length === 0 ? (
        <EmptyRow
          text={
            "No document access logs found."
          }
        />
      ) : (
        <div className="overflow-x-auto">
          <table
            className="
              min-w-full divide-y
              divide-slate-200
            "
          >
            <thead
              className="bg-slate-50"
            >
              <tr>
                {[
                  "Date",
                  "Document",
                  "Number",
                  "Action",
                  "User",
                ].map(
                  (heading) => (
                    <TableHeader
                      key={heading}
                    >
                      {heading}
                    </TableHeader>
                  ),
                )}
              </tr>
            </thead>

            <tbody
              className="
                divide-y
                divide-slate-100
              "
            >
              {logs.map(
                (log) => (
                  <tr key={log.id}>
                    <TableCell>
                      {
                        formatDateTime(
                          log.created_at,
                        )
                      }
                    </TableCell>

                    <TableCell>
                      {
                        formatLabel(
                          log.document_type,
                        )
                      }
                    </TableCell>

                    <TableCell>
                      {
                        log.document_number
                      }
                    </TableCell>

                    <TableCell>
                      {
                        formatLabel(
                          log.action,
                        )
                      }
                    </TableCell>

                    <TableCell>
                      {
                        log.user
                          ?.email
                        ??
                        "System"
                      }
                    </TableCell>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      )}
    </LogSection>
  );
}

function DeliveryLogTable({
  logs,
  isLoading,
  error,
}: {
  logs: Array<{
    id: string;
    document_type: string;
    document_number: string;
    channel: string;
    recipient: string;
    status: string;
    error_message:
      | string
      | null;
    sent_at:
      | string
      | null;
    created_at:
      | string
      | null;
  }>;
  isLoading: boolean;
  error: unknown;
}) {
  return (
    <LogSection
      title="Delivery history"
      icon={<Mail size={19} />}
    >
      {isLoading ? (
        <LoadingRow
          text={
            "Loading delivery logs..."
          }
        />
      ) : error ? (
        <ErrorRow
          message={
            getErrorMessage(error)
          }
        />
      ) : logs.length === 0 ? (
        <EmptyRow
          text={
            "No document delivery logs found."
          }
        />
      ) : (
        <div className="overflow-x-auto">
          <table
            className="
              min-w-full divide-y
              divide-slate-200
            "
          >
            <thead
              className="bg-slate-50"
            >
              <tr>
                {[
                  "Date",
                  "Document",
                  "Number",
                  "Recipient",
                  "Channel",
                  "Status",
                  "Error",
                ].map(
                  (heading) => (
                    <TableHeader
                      key={heading}
                    >
                      {heading}
                    </TableHeader>
                  ),
                )}
              </tr>
            </thead>

            <tbody
              className="
                divide-y
                divide-slate-100
              "
            >
              {logs.map(
                (log) => (
                  <tr key={log.id}>
                    <TableCell>
                      {
                        formatDateTime(
                          log.sent_at
                          ??
                          log.created_at,
                        )
                      }
                    </TableCell>

                    <TableCell>
                      {
                        formatLabel(
                          log.document_type,
                        )
                      }
                    </TableCell>

                    <TableCell>
                      {
                        log.document_number
                      }
                    </TableCell>

                    <TableCell>
                      {log.recipient}
                    </TableCell>

                    <TableCell>
                      {
                        formatLabel(
                          log.channel,
                        )
                      }
                    </TableCell>

                    <TableCell>
                      {
                        formatLabel(
                          log.status,
                        )
                      }
                    </TableCell>

                    <TableCell>
                      {
                        log.error_message
                        ??
                        "—"
                      }
                    </TableCell>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      )}
    </LogSection>
  );
}

function LogSection({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section
      className="
        overflow-hidden
        rounded-2xl border
        border-slate-200
        bg-white shadow-sm
      "
    >
      <header
        className="
          flex items-center
          gap-2 border-b
          border-slate-200
          px-5 py-4
        "
      >
        {icon}

        <h2
          className="
            font-bold text-slate-900
          "
        >
          {title}
        </h2>
      </header>

      {children}
    </section>
  );
}

function TableHeader({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <th
      className="
        whitespace-nowrap
        px-4 py-3
        text-left text-xs
        font-semibold uppercase
        tracking-wide
        text-slate-500
      "
    >
      {children}
    </th>
  );
}

function TableCell({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <td
      className="
        whitespace-nowrap
        px-4 py-3 text-sm
        text-slate-700
      "
    >
      {children}
    </td>
  );
}

function LoadingRow({
  text,
}: {
  text: string;
}) {
  return (
    <div
      className="
        flex items-center gap-2
        px-6 py-14
        text-sm text-slate-500
      "
    >
      <RefreshCw
        size={17}
        className="animate-spin"
      />

      {text}
    </div>
  );
}

function ErrorRow({
  message,
}: {
  message: string;
}) {
  return (
    <div
      role="alert"
      className="
        bg-red-50 px-6 py-10
        text-sm font-semibold
        text-red-700
      "
    >
      {message}
    </div>
  );
}

function EmptyRow({
  text,
}: {
  text: string;
}) {
  return (
    <div
      className="
        px-6 py-14 text-center
        text-sm text-slate-500
      "
    >
      {text}
    </div>
  );
}
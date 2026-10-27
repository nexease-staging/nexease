"use client";

import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  Landmark,
  ReceiptText,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import ReportExportActions from "@/features/documents/components/report-export-actions";

import {
  useFinanceAudit,
} from "@/features/accounting/hooks";

import {
  APIRequestError,
} from "@/lib/api/client";

function getErrorMessage(
  error: unknown,
): string {
  if (error instanceof APIRequestError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to load finance audit.";
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

function formatValue(
  value: unknown,
): string {
  if (
    value === null
    ||
    value === undefined
  ) {
    return "—";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (
    typeof value === "string"
    ||
    typeof value === "number"
  ) {
    return String(value);
  }

  return JSON.stringify(value);
}

export default function FinanceAuditPage() {
  const auditQuery =
    useFinanceAudit();

  const audit =
    auditQuery.data;

  return (
    <div
      className="
        mx-auto max-w-7xl
        space-y-6
      "
    >
        <header
        className="
            flex flex-col gap-4
            sm:flex-row
            sm:items-start
            sm:justify-between
        "
        >
        <div>
            <p
            className="
                text-sm font-semibold
                text-blue-600
            "
            >
            Finance
            </p>

            <h1
            className="
                mt-1 text-3xl
                font-bold text-slate-900
            "
            >
            Finance Audit
            </h1>

            <p
            className="
                mt-2 text-sm
                text-slate-600
            "
            >
            Review financial exceptions,
            reconciliation issues and
            records requiring attention.
            </p>
        </div>

        <ReportExportActions
            resourceType="FINANCE_AUDIT"
            disabled={
            auditQuery.isFetching
            }
        />
        </header>

      {auditQuery.isLoading && (
        <section
          className="
            rounded-2xl border
            border-slate-200
            bg-white p-8
            shadow-sm
          "
        >
          <div
            className="
              flex items-center
              gap-2 text-slate-600
            "
          >
            <RefreshCw
              size={18}
              className="animate-spin"
            />

            Loading finance audit...
          </div>
        </section>
      )}

      {auditQuery.error && (
        <section
          className="
            rounded-2xl border
            border-red-200
            bg-red-50 p-6
          "
        >
          <p
            className="
              font-semibold
              text-red-900
            "
          >
            Unable to load finance audit
          </p>

          <p
            className="
              mt-2 text-sm
              text-red-700
            "
          >
            {getErrorMessage(
              auditQuery.error,
            )}
          </p>
        </section>
      )}

      {audit && (
        <>
          <section
            className="
              grid gap-4
              sm:grid-cols-3
            "
          >
            <SummaryCard
              title="Overall Status"
              value={
                audit.healthy
                  ? "Healthy"
                  : "Attention Required"
              }
              icon={
                audit.healthy
                  ? (
                    <CheckCircle2
                      size={20}
                    />
                  )
                  : (
                    <AlertTriangle
                      size={20}
                    />
                  )
              }
            />

            <SummaryCard
              title="Critical Issues"
              value={String(
                audit.critical_exception_count,
              )}
              icon={
                <AlertTriangle
                  size={20}
                />
              }
            />

            <SummaryCard
              title="Needs Attention"
              value={String(
                audit.attention_count,
              )}
              icon={
                <ShieldCheck
                  size={20}
                />
              }
            />
          </section>

          <div
            className="
              grid gap-6
              xl:grid-cols-2
            "
          >
            <AuditSection
            title="Unmatched Statement Lines"
            description={
                "Bank statement lines that remain unmatched."
            }
            items={
                audit
                .statement_exceptions
                .unmatched_lines
            }
            icon={
                <Landmark size={20} />
            }
            />

            <AuditSection
            title="Invalid Statement Matches"
            description={
                "Statement lines with invalid reconciliation matches."
            }
            items={
                audit
                .statement_exceptions
                .invalid_matched_lines
            }
            icon={
                <AlertTriangle size={20} />
            }
            />

            <AuditSection
            title="Stale Statement Links"
            description={
                "Statement lines containing unresolved stale links."
            }
            items={
                audit
                .statement_exceptions
                .stale_unresolved_links
            }
            icon={
                <AlertTriangle size={20} />
            }
            />

            <AuditSection
            title="Unreconciled Transactions"
            description={
                "Bank transactions that have not been reconciled."
            }
            items={
                audit
                .transaction_exceptions
                .unreconciled_transactions
            }
            icon={
                <ReceiptText size={20} />
            }
            />

            <AuditSection
            title="Duplicate Matches"
            description={
                "Bank transactions with duplicate reconciliation matches."
            }
            items={
                audit
                .transaction_exceptions
                .duplicate_matches
            }
            icon={
                <AlertTriangle size={20} />
            }
            />

            <AuditSection
            title="Pending Payment Suggestions"
            description={
                "Payment suggestions waiting for review."
            }
            items={
                audit
                .suggestion_exceptions
                .pending
            }
            icon={
                <ShieldCheck size={20} />
            }
            />

            <AuditSection
            title="Confirmed but Unexecuted"
            description={
                "Confirmed payment suggestions not yet executed."
            }
            items={
                audit
                .suggestion_exceptions
                .confirmed_unexecuted
            }
            icon={
                <ShieldCheck size={20} />
            }
            />

            <AuditSection
            title="Rejected Payment Suggestions"
            description={
                "Payment suggestions that were rejected."
            }
            items={
                audit
                .suggestion_exceptions
                .rejected
            }
            icon={
                <ShieldCheck size={20} />
            }
            />

            <AuditSection
            title="Invalid Payment Execution State"
            description={
                "Payment suggestions in an invalid execution state."
            }
            items={
                audit
                .suggestion_exceptions
                .invalid_execution_state
            }
            icon={
                <AlertTriangle size={20} />
            }
            />

            <AuditSection
            title="Customer Invoice Exceptions"
            description={
                "Receivable records requiring review."
            }
            items={
                audit.invoice_exceptions
            }
            icon={
                <FileText size={20} />
            }
            />

            <AuditSection
              title="Vendor Bill Exceptions"
              description={
                "Payable records requiring review."
              }
              items={
                audit.vendor_bill_exceptions
              }
              icon={
                <FileText size={20} />
              }
            />
          </div>
        </>
      )}
    </div>
  );
}

function SummaryCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <div
      className="
        rounded-2xl border
        border-slate-200
        bg-white p-5
        shadow-sm
      "
    >
      <div
        className="
          flex items-start
          justify-between gap-4
        "
      >
        <div>
          <p
            className="
              text-sm font-medium
              text-slate-500
            "
          >
            {title}
          </p>

          <p
            className="
              mt-2 text-2xl
              font-bold text-slate-900
            "
          >
            {value}
          </p>
        </div>

        <div
          className="
            rounded-xl bg-slate-100
            p-3 text-slate-700
          "
        >
          {icon}
        </div>
      </div>
    </div>
  );
}

function AuditSection({
  title,
  description,
  items,
  icon,
}: {
  title: string;
  description: string;
  items:
    Record<string, unknown>[];
  icon: React.ReactNode;
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
      <div
        className="
          flex items-start
          justify-between gap-4
          border-b border-slate-200
          px-6 py-5
        "
      >
        <div>
          <div
            className="
              flex items-center gap-2
            "
          >
            <span
              className="text-slate-700"
            >
              {icon}
            </span>

            <h2
              className="
                text-lg font-semibold
                text-slate-900
              "
            >
              {title}
            </h2>
          </div>

          <p
            className="
              mt-1 text-sm
              text-slate-500
            "
          >
            {description}
          </p>
        </div>

        <span
          className="
            rounded-full
            bg-slate-100
            px-2.5 py-1
            text-xs font-semibold
            text-slate-700
          "
        >
          {items.length}
        </span>
      </div>

      {items.length === 0 ? (
        <div
          className="
            px-6 py-8
            text-center
          "
        >
          <CheckCircle2
            size={28}
            className="
              mx-auto text-slate-400
            "
          />

          <p
            className="
              mt-3 text-sm
              font-medium
              text-slate-700
            "
          >
            No exceptions found
          </p>

          <p
            className="
              mt-1 text-xs
              text-slate-500
            "
          >
            Nothing currently requires
            review in this category.
          </p>
        </div>
      ) : (
        <div
          className="
            divide-y
            divide-slate-100
          "
        >
          {items.map(
            (item, index) => (
              <AuditItem
                key={index}
                item={item}
              />
            ),
          )}
        </div>
      )}
    </section>
  );
}

function AuditItem({
  item,
}: {
  item: Record<string, unknown>;
}) {
  const entries =
    Object.entries(item);

  return (
    <div className="px-6 py-4">
      {entries.length === 0 ? (
        <p
          className="
            text-sm text-slate-500
          "
        >
          No details available.
        </p>
      ) : (
        <dl
          className="
            grid gap-3
            sm:grid-cols-2
          "
        >
          {entries.map(
            ([key, value]) => (
              <div key={key}>
                <dt
                  className="
                    text-xs font-semibold
                    uppercase tracking-wide
                    text-slate-400
                  "
                >
                  {formatLabel(key)}
                </dt>

                <dd
                  className="
                    mt-1 break-words
                    text-sm text-slate-700
                  "
                >
                  {formatValue(value)}
                </dd>
              </div>
            ),
          )}
        </dl>
      )}
    </div>
  );
}
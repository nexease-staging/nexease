"use client";
import { useState } from "react";
import { FileClock, Mail, RefreshCw, Search } from "lucide-react";
import NexDialog from "@/components/nex-dialog";
import {
  useDocumentAccessLogs,
  useDocumentDeliveryLogs,
  useDocumentAccessLogSummary,
  useDocumentDeliveryLogSummary,
} from "@/features/documents/hooks";
import type {
  DocumentAccessLog,
  DocumentDeliveryLog,
} from "@/features/documents/types";

const kinds = [
  "INVOICE",
  "SALES_ORDER",
  "CREDIT_NOTE",
  "CUSTOMER_PAYMENT",
  "PURCHASE_ORDER",
  "VENDOR_BILL",
  "VENDOR_DEBIT_NOTE",
  "SUPPLIER_PAYMENT",
  "GOODS_RECEIPT",
];
const label = (value: string) =>
  value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
const date = (value: string | null) =>
  value && Number.isFinite(Date.parse(value))
    ? new Date(value).toLocaleString("en-IN")
    : "—";
export default function DocumentLogsPage() {
  const [tab, setTab] = useState<"access" | "delivery">("access");
  const [kind, setKind] = useState("");
  const [number, setNumber] = useState("");
  const [status, setStatus] = useState("");
  const [action, setAction] = useState("");
  const [recipient, setRecipient] = useState("");
  const [filters, setFilters] = useState<{
    document_type?: string;
    document_number?: string;
    status?: string;
    action?: string;
    recipient?: string;
  }>({});
  const [selected, setSelected] = useState<
    DocumentAccessLog | DocumentDeliveryLog | null
  >(null);
  const access = useDocumentAccessLogs(
    { ...filters, limit: 100 },
    tab === "access",
  );
  const delivery = useDocumentDeliveryLogs(
    { ...filters, limit: 100 },
    tab === "delivery",
  );
  const accessSummary = useDocumentAccessLogSummary(tab === "access");
  const deliverySummary = useDocumentDeliveryLogSummary(tab === "delivery");
  const summary = tab === "access" ? accessSummary : deliverySummary;
  const query = tab === "access" ? access : delivery;
  const logs = query.data?.logs ?? [];
  return (
    <div className="space-y-5 text-slate-900">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold">Document activity</h1>
          <p className="mt-2 text-sm text-slate-500">
            PDF access and email delivery history for your organization.
          </p>
        </div>
        <button
          className="nx-button nx-secondary"
          disabled={query.isFetching}
          onClick={() => {
            void query.refetch();
            void summary.refetch();
          }}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>
      <div
        role="tablist"
        aria-label="Document activity type"
        className="flex gap-2"
      >
        {(["access", "delivery"] as const).map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            className={"nx-button " + (tab === t ? "" : "nx-secondary")}
            onClick={() => {
              setTab(t);
              setFilters({});
              setKind("");
              setNumber("");
              setStatus("");
              setAction("");
              setRecipient("");
            }}
          >
            {t === "access" ? <FileClock size={16} /> : <Mail size={16} />}{" "}
            {t === "access" ? "Access logs" : "Delivery logs"}
          </button>
        ))}
      </div>
      {summary.data && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {Object.entries(summary.data)
            .filter(([, v]) => typeof v === "number" || typeof v === "string")
            .map(([k, v]) => (
              <section key={k} className="nx-panel">
                <p className="text-xs text-slate-500">{label(k)}</p>
                <p className="mt-2 text-2xl font-semibold">{String(v)}</p>
              </section>
            ))}
        </div>
      )}
      <section className="nx-panel">
        <form
          className="flex flex-wrap items-end gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            setFilters({
              document_type: kind || undefined,
              document_number: number.trim() || undefined,
              ...(tab === "delivery"
                ? {
                    status: status || undefined,
                    recipient: recipient.trim() || undefined,
                  }
                : { action: action.trim() || undefined }),
            });
          }}
        >
          <label className="text-sm">
            Document type
            <select
              className="nx-input"
              value={kind}
              onChange={(e) => setKind(e.target.value)}
            >
              <option value="">All document types</option>
              {kinds.map((k) => (
                <option key={k} value={k}>
                  {label(k)}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Document number
            <input
              className="nx-input"
              value={number}
              onChange={(e) => setNumber(e.target.value)}
              placeholder="Search document number"
            />
          </label>
          {tab === "delivery" && (
            <label className="text-sm">
              Status
              <select
                className="nx-input"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="">All statuses</option>
                {["PENDING", "SENT", "FAILED"].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>
          )}
          <label className="text-sm">
            {tab === "access" ? "Action" : "Recipient"}
            <input
              className="nx-input"
              value={tab === "access" ? action : recipient}
              onChange={(e) =>
                tab === "access"
                  ? setAction(e.target.value)
                  : setRecipient(e.target.value)
              }
            />
          </label>
          <button className="nx-button">
            <Search size={16} />
            Apply filters
          </button>
          <button
            type="button"
            className="nx-button nx-secondary"
            onClick={() => {
              setFilters({});
              setKind("");
              setNumber("");
              setStatus("");
              setAction("");
              setRecipient("");
            }}
          >
            Clear filters
          </button>
        </form>
      </section>
      {query.error ? (
        <section role="alert" className="nx-panel border-red-200">
          <p>{query.error.message}</p>
          <p className="mt-2 text-sm">
            Your role needs Accounting audit read permission to view
            organization-wide document logs.
          </p>
          <button
            className="nx-button nx-secondary mt-3"
            onClick={() => void query.refetch()}
          >
            Retry
          </button>
        </section>
      ) : (
        <section className="nx-panel">
          {query.isLoading ? (
            <p role="status">Loading document activity…</p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr>
                      {[
                        "Date",
                        "Document",
                        "Type",
                        tab === "access" ? "Action" : "Status",
                        tab === "access" ? "User" : "Recipient",
                        "Details",
                      ].map((h) => (
                        <th key={h} className="whitespace-nowrap border-b p-3">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log) => (
                      <tr key={log.id} className="border-b hover:bg-slate-50">
                        <td className="whitespace-nowrap p-3">
                          {date(log.created_at)}
                        </td>
                        <td className="p-3 font-medium">
                          {log.document_number || "—"}
                        </td>
                        <td className="p-3">{label(log.document_type)}</td>
                        <td className="p-3">
                          {"status" in log ? log.status : log.action}
                        </td>
                        <td className="p-3">
                          {"recipient" in log
                            ? log.recipient
                            : (log.user?.email ?? "Deleted user")}
                        </td>
                        <td className="p-3">
                          <button
                            className="nx-button nx-secondary nx-btn-sm"
                            onClick={() => setSelected(log)}
                          >
                            View details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {!logs.length && (
                <p className="py-12 text-center text-slate-500">
                  No document activity matches these filters.
                </p>
              )}
              <p className="mt-4 text-xs text-slate-500">
                Showing the latest {logs.length} matching records, up to 100.
                Use filters to narrow the history.
              </p>
            </>
          )}
        </section>
      )}
      {selected && (
        <NexDialog
          title={"Document " + ("status" in selected ? "delivery" : "access")}
          onClose={() => setSelected(null)}
        >
          <dl className="space-y-3">
            {Object.entries(selected)
              .filter(([k]) => k !== "id")
              .map(([key, value]) => (
                <div key={key} className="grid grid-cols-3 gap-3 border-b pb-2">
                  <dt className="text-sm text-slate-500">{label(key)}</dt>
                  <dd className="col-span-2 break-words text-sm">
                    {key.endsWith("_at")
                      ? date(value as string | null)
                      : value === null
                        ? "—"
                        : typeof value === "object"
                          ? "email" in value
                            ? String(value.email)
                            : "—"
                          : typeof value === "boolean"
                            ? value
                              ? "Yes"
                              : "No"
                            : String(value)}
                  </dd>
                </div>
              ))}
          </dl>
        </NexDialog>
      )}
    </div>
  );
}

"use client";

import {
  useState,
} from "react";

import {
  Download,
  FileSpreadsheet,
} from "lucide-react";

import {
  useExportResource,
} from "@/features/documents/hooks";

import type {
  ExportFormat,
  ExportResourceType,
} from "@/features/documents/types";

import {
  APIRequestError,
} from "@/lib/api/client";

interface ReportExportActionsProps {
  resourceType: ExportResourceType;
  parameters?: Record<
    string,
    string | number | boolean | undefined
  >;
  disabled?: boolean;
}

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

  return "Unable to export the report.";
}

export default function ReportExportActions({
  resourceType,
  parameters = {},
  disabled = false,
}: ReportExportActionsProps) {
  const [
    exportError,
    setExportError,
  ] = useState<string | null>(
    null,
  );

  const exportMutation =
    useExportResource();

  async function handleExport(
    format: ExportFormat,
  ): Promise<void> {
    setExportError(null);

    try {
      await exportMutation.mutateAsync({
        resourceType,
        format,
        parameters,
      });
    } catch (error) {
      setExportError(
        getErrorMessage(error),
      );
    }
  }

  const actionDisabled =
    disabled
    ||
    exportMutation.isPending;

  return (
    <div>
      <div
        className="
          flex flex-wrap items-center
          gap-2
        "
      >
        <button
          type="button"
          disabled={actionDisabled}
          onClick={() => {
            void handleExport("csv");
          }}
          className="
            inline-flex items-center
            gap-2 rounded-lg border
            border-slate-300 bg-white
            px-3 py-2 text-sm
            font-semibold text-slate-700
            hover:bg-slate-50
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          <Download size={16} />

          {exportMutation.isPending
            ? "Exporting..."
            : "CSV"}
        </button>

        <button
          type="button"
          disabled={actionDisabled}
          onClick={() => {
            void handleExport("xlsx");
          }}
          className="
            inline-flex items-center
            gap-2 rounded-lg border
            border-emerald-200 bg-white
            px-3 py-2 text-sm
            font-semibold text-emerald-700
            hover:bg-emerald-50
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          <FileSpreadsheet
            size={16}
          />

          XLSX
        </button>
      </div>

      {exportError ? (
        <p
          role="alert"
          className="
            mt-2 text-xs text-red-700
          "
        >
          {exportError}
        </p>
      ) : null}
    </div>
  );
}
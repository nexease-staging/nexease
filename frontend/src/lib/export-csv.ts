import { downloadBlob } from "@/lib/browser/download";

export interface CsvColumn<T> {
  header: string;
  value: (row: T) => string | number | null | undefined;
}

// Spreadsheet apps execute cells that start with these characters as formulas.
const FORMULA_START = /^[=+\-@\t\r]/;

function cell(raw: string | number | null | undefined): string {
  if (raw === null || raw === undefined) return "";
  let text = String(raw);
  if (typeof raw === "string" && FORMULA_START.test(text)) text = "'" + text;
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function toCsv<T>(rows: readonly T[], columns: readonly CsvColumn<T>[]): string {
  const lines = [columns.map((c) => cell(c.header)).join(",")];
  for (const row of rows) lines.push(columns.map((c) => cell(c.value(row))).join(","));
  // BOM so Excel opens ₹ and Indian names correctly.
  return "﻿" + lines.join("\r\n");
}

export async function downloadCsv<T>(filename: string, rows: readonly T[], columns: readonly CsvColumn<T>[]): Promise<void> {
  const blob = new Blob([toCsv(rows, columns)], { type: "text/csv;charset=utf-8" });
  await downloadBlob(blob, filename.endsWith(".csv") ? filename : `${filename}.csv`);
}

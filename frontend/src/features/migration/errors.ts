/** Preserve API validation details instead of displaying only the generic heading. */
export function migrationErrorMessage(error: unknown, fallback: string): string {
  if (!(error instanceof Error)) return fallback;
  const details = (error as Error & {details?: Record<string, unknown>}).details;
  const lines: string[] = [];
  for (const [field, value] of Object.entries(details ?? {})) {
    for (const message of Array.isArray(value) ? value : [value]) {
      if (typeof message === "string") lines.push(`${field}: ${message}`);
    }
  }
  return [error.message, ...lines].filter((line, i, all) => all.indexOf(line) === i).join("\n");
}

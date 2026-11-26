import { formatMoney } from "@/lib/format";
import { whatsappNumber } from "@/lib/phone";
import type { OpenDocument, PartySummary } from "./api";

/** Plain, polite payment reminder. Lists up to five invoices so the message stays readable. */
export function reminderText(party: Pick<PartySummary, "name" | "outstanding" | "overdue">, business: string, documents: OpenDocument[] = []) {
  const lines = [`Namaste ${party.name},`, "", `This is a friendly reminder from ${business || "us"}.`];
  lines.push(Number(party.overdue) > 0
    ? `${formatMoney(party.overdue)} is overdue, out of ${formatMoney(party.outstanding)} outstanding.`
    : `${formatMoney(party.outstanding)} is outstanding.`);
  if (documents.length) {
    lines.push("");
    for (const d of documents.slice(0, 5)) {
      lines.push(`• ${d.number}: ${formatMoney(d.outstanding)}${d.days_overdue > 0 ? ` (${d.days_overdue} days overdue)` : d.due_date ? ` (due ${d.due_date})` : ""}`);
    }
    if (documents.length > 5) lines.push(`• and ${documents.length - 5} more`);
  }
  lines.push("", "Please share the payment details once paid. Thank you!");
  return lines.join("\n");
}

export function whatsappUrl(phone: string, text: string) {
  const number = whatsappNumber(phone);
  return `https://wa.me/${number ?? ""}?text=${encodeURIComponent(text)}`;
}

export function mailtoUrl(email: string, subject: string, text: string) {
  return `mailto:${encodeURIComponent(email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(text)}`;
}

export function openExternal(url: string) {
  if (url.startsWith("mailto:")) window.location.href = url;
  else window.open(url, "_blank", "noopener,noreferrer");
}

/** Oldest-due-first split of an amount across open documents (documents arrive sorted). */
export function autoAllocate(documents: OpenDocument[], amount: number): Record<string, string> {
  let left = Math.round(amount * 100);
  const result: Record<string, string> = {};
  for (const d of documents) {
    if (left <= 0) break;
    const take = Math.min(left, Math.round(Number(d.outstanding) * 100));
    if (take > 0) result[d.id] = (take / 100).toFixed(2);
    left -= take;
  }
  return result;
}

export function newRequestKey() {
  const random = typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return `pay-${random}`.replace(/[^A-Za-z0-9_-]/g, "").slice(0, 60);
}

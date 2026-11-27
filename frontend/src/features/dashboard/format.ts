/** Formatting and period helpers for the dashboard. Pure functions, unit tested. */

export const num = (value: string | number | null | undefined): number => {
  const n = Number(value ?? 0);
  return Number.isFinite(n) ? n : 0;
};

const full = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });

/** ₹12,48,731 (whole rupees, Indian grouping). */
export const rupees = (value: string | number | null | undefined): string => full.format(Math.round(num(value)));

/** ₹12.5 L / ₹1.2 Cr / ₹48.2K for headline figures; the exact value goes in a title or tooltip. */
export function compact(value: string | number | null | undefined): string {
  const n = num(value);
  const sign = n < 0 ? "-" : "";
  const a = Math.abs(n);
  const trim = (x: number) => String(+x.toFixed(x >= 100 ? 0 : x >= 10 ? 1 : 2));
  if (a >= 1e7) return `${sign}₹${trim(a / 1e7)} Cr`;
  if (a >= 1e5) return `${sign}₹${trim(a / 1e5)} L`;
  if (a >= 1e3) return `${sign}₹${trim(a / 1e3)}K`;
  return `${sign}₹${Math.round(a)}`;
}

/** Axis ticks: 0, 2L, 4L … without the rupee sign to keep the axis quiet. */
export function axis(value: number): string {
  const a = Math.abs(value);
  const s = value < 0 ? "-" : "";
  if (a >= 1e7) return `${s}${+(a / 1e7).toFixed(1)}Cr`;
  if (a >= 1e5) return `${s}${+(a / 1e5).toFixed(1)}L`;
  if (a >= 1e3) return `${s}${+(a / 1e3).toFixed(0)}K`;
  return `${s}${a}`;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2026-03" → "Mar", "2026-03-14" → "14 Mar", anything else is shown as given. */
export function periodLabel(period: string): string {
  const m = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(period);
  if (!m) return period;
  const month = MONTHS[Number(m[2]) - 1] ?? m[2];
  return m[3] ? `${Number(m[3])} ${month}` : month;
}

export function longDate(iso: string): string {
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  if (Number.isNaN(d.getTime())) return iso;
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

export function relativeDay(iso: string, now = new Date()): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const day = (x: Date) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const diff = Math.round((day(now) - day(d)) / 86400000);
  const time = d.toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit" });
  if (diff === 0) return `Today, ${time}`;
  if (diff === 1) return `Yesterday, ${time}`;
  return `${d.getDate()} ${MONTHS[d.getMonth()]}`;
}

export const isoDate = (date: Date) => new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 10);

export type PresetKey = "month" | "quarter" | "fy" | "last_fy" | "custom";

export const PRESETS: { key: Exclude<PresetKey, "custom">; label: string }[] = [
  { key: "month", label: "This month" },
  { key: "quarter", label: "This quarter" },
  { key: "fy", label: "This FY" },
  { key: "last_fy", label: "Last FY" },
];

/** Indian financial year runs April to March; quarters follow it (Apr–Jun is Q1). */
export function presetRange(key: Exclude<PresetKey, "custom">, today = new Date()): { start_date: string; end_date: string } {
  const y = today.getFullYear();
  const m = today.getMonth();
  const fyStart = m >= 3 ? y : y - 1;
  if (key === "month") return { start_date: isoDate(new Date(y, m, 1)), end_date: isoDate(today) };
  if (key === "quarter") {
    const q = Math.floor(((m - 3 + 12) % 12) / 3);
    const startMonth = (3 + q * 3) % 12;
    const startYear = startMonth > m ? y - 1 : y;
    return { start_date: isoDate(new Date(startYear, startMonth, 1)), end_date: isoDate(today) };
  }
  if (key === "fy") return { start_date: isoDate(new Date(fyStart, 3, 1)), end_date: isoDate(today) };
  return { start_date: isoDate(new Date(fyStart - 1, 3, 1)), end_date: isoDate(new Date(fyStart, 2, 31)) };
}

export function greeting(now = new Date()): string {
  const h = now.getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

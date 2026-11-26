/*
 * How each schema-driven register reads as a compact row: title, subtitle, meta columns,
 * amount and status. Registers without a presenter fall back to their first fields.
 */
import type { Tone } from "@/components/ui/badge";

export type Value = string | boolean;
export type Row = { id: string; key: string; revision: number; data: Record<string, Value> };
export type Field = { label: string; type: string; required: boolean; choices?: string[] };
export type Lookup = (type: string, value: Value | undefined) => string;

export interface Presented {
  title: string;
  subtitle: string;
  meta: string[];
  amount?: string;
  amountHint?: string;
  status?: { label: string; tone: Tone };
}

export interface Presenter {
  noun: string;
  columns: string[];
  present: (d: Record<string, Value>, name: Lookup, key: string) => Presented;
  /** Status filter chips: [value, label]; value "" means all. */
  filters?: Array<[string, string]>;
  filterField?: string;
  /** Form sections: [title, field keys, collapsed?]. Unlisted fields go in a final "More" section. */
  sections?: Array<[string, string[], boolean?]>;
}

const rupees = (v: Value | number | undefined, decimals = 0) => {
  const n = Number(v || 0);
  return n.toLocaleString("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: decimals, maximumFractionDigits: 2 });
};
const day = (v: Value | undefined) => {
  if (!v) return "";
  const d = new Date(String(v) + (String(v).length === 7 ? "-01" : "") + "T00:00:00");
  if (Number.isNaN(d.getTime())) return String(v);
  return String(v).length === 7
    ? d.toLocaleDateString("en-IN", { month: "short", year: "numeric" })
    : d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
};
const span = (a: Value | undefined, b: Value | undefined) => (a && b && a !== b ? `${day(a)} – ${day(b)}` : day(a || b));
const cap = (v: Value | undefined) => (v ? String(v).charAt(0).toUpperCase() + String(v).slice(1).replaceAll("_", " ") : "");
const join = (...parts: Array<string | false | undefined>) => parts.filter(Boolean).join(" · ");
const PER: Record<string, string> = { monthly: "month", daily: "day", hourly: "hour", piece: "piece" };
const STATUS: Record<string, { label: string; tone: Tone }> = {
  active: { label: "Active", tone: "success" }, inactive: { label: "Inactive", tone: "neutral" },
  completed: { label: "Completed", tone: "info" }, cancelled: { label: "Cancelled", tone: "neutral" },
  draft: { label: "Draft", tone: "warning" }, approved: { label: "Approved", tone: "success" },
  requested: { label: "Requested", tone: "warning" }, rejected: { label: "Rejected", tone: "danger" },
};
const status = (v: Value | undefined) => STATUS[String(v)] ?? (v ? { label: cap(v), tone: "neutral" as Tone } : undefined);
const active = (v: Value | undefined) => (v ? STATUS.active : STATUS.inactive);

export const presenters: Record<string, Presenter> = {
  employees: {
    noun: "employee",
    columns: ["Employee", "Phone", "Joined", "Pay rate"],
    filters: [["active", "Active"], ["inactive", "Inactive"], ["", "All"]],
    filterField: "active",
    present: (d, _n, key) => ({
      title: String(d.name || "—"),
      subtitle: join(String(d.code || key), String(d.designation || "") || cap(d.employment_type), d.department ? String(d.department) : ""),
      meta: [String(d.phone || "—"), day(d.joining_date) || "—"],
      amount: d.rate ? `${rupees(d.rate)}/${PER[String(d.basis)] ?? String(d.basis)}` : undefined,
      amountHint: join(d.pf_member === true && "PF", d.esi_member === true && "ESI") || undefined,
      status: active(d.active),
    }),
    sections: [
      ["Basic details", ["name", "code", "employment_type", "designation", "department", "phone", "email", "joining_date", "end_date", "active"]],
      ["Pay", ["basis", "rate", "overtime_rate"]],
      ["Bank and statutory details", ["pf_member", "esi_member", "uan", "esi_number", "bank_account", "ifsc"], true],
    ],
  },
  sites: {
    noun: "site",
    columns: ["Site", "Supervisor", "Started", "Billing rate"],
    filters: [["active", "Active"], ["inactive", "Inactive"], ["", "All"]],
    filterField: "active",
    present: (d, name, key) => ({
      title: String(d.name || "—"),
      subtitle: join(String(d.code || key), d.customer_code ? name("customers", d.customer_code) : "", d.address ? String(d.address) : ""),
      meta: [String(d.supervisor || "—"), day(d.start_date) || "—"],
      amount: Number(d.billing_rate) ? `${rupees(d.billing_rate)}/day` : undefined,
      amountHint: Number(d.client_ot_rate) ? `OT ${rupees(d.client_ot_rate)}/hr` : undefined,
      status: active(d.active),
    }),
    sections: [["Site", ["name", "code", "customer_code", "address", "supervisor", "phone", "start_date", "end_date", "active"]], ["Billing", ["billing_rate", "client_ot_rate"]]],
  },
  assignments: {
    noun: "assignment",
    columns: ["Worker / site", "Period", "Role", "Billing rate"],
    filters: [["active", "Active"], ["completed", "Completed"], ["cancelled", "Cancelled"], ["", "All"]],
    filterField: "status",
    present: (d, name) => ({
      title: name("employees", d.employee_id) || "—",
      subtitle: join(name("sites", d.site_id), d.shift ? `${d.shift} shift` : ""),
      meta: [span(d.start_date, d.end_date) || "—", String(d.role || "—")],
      amount: Number(d.billing_rate) ? `${rupees(d.billing_rate)}/day` : undefined,
      status: status(d.status),
    }),
  },
  timesheets: {
    noun: "timesheet",
    columns: ["Worker / site", "Hours", "Billable", "Value"],
    filters: [["draft", "Draft"], ["approved", "Approved"], ["", "All"]],
    filterField: "status",
    present: (d, name) => ({
      title: name("employees", d.employee_id) || "—",
      subtitle: join(d.site_id ? name("sites", d.site_id) : "In-house", day(d.date), d.shift ? `${d.shift} shift` : ""),
      meta: [`${Number(d.hours || 0)} h${Number(d.overtime_hours) ? ` + ${Number(d.overtime_hours)} OT` : ""}`, `${Number(d.billable_units || 0)} × ${rupees(d.billing_rate)}`],
      amount: rupees(Number(d.billable_units || 0) * Number(d.billing_rate || 0)),
      status: status(d.status),
    }),
  },
  leave_requests: {
    noun: "leave request",
    columns: ["Employee", "Dates", "Notes", "Days"],
    filters: [["requested", "Requested"], ["approved", "Approved"], ["rejected", "Rejected"], ["", "All"]],
    filterField: "status",
    present: (d, name) => ({
      title: name("employees", d.employee_id) || "—",
      subtitle: join(`${cap(d.leave_type)} leave`, span(d.start_date, d.end_date)),
      meta: [span(d.start_date, d.end_date) || "—", String(d.notes || "—")],
      amount: `${Number(d.days || 0)} day${Number(d.days) === 1 ? "" : "s"}`,
      status: status(d.status),
    }),
  },
  advances: {
    noun: "advance",
    columns: ["Employee", "Mode", "Recovered", "Advance"],
    filters: [["open", "Outstanding"], ["closed", "Recovered"], ["", "All"]],
    filterField: "__advance",
    present: (d, name) => {
      const due = Number(d.amount || 0) - Number(d.recovered || 0);
      return {
        title: name("employees", d.employee_id) || "—",
        subtitle: join(day(d.date), d.reference ? `Ref ${d.reference}` : ""),
        meta: [String(d.payment_mode || "—"), rupees(d.recovered)],
        amount: rupees(d.amount),
        amountHint: due > 0 ? `${rupees(due)} to recover` : undefined,
        status: due > 0 ? { label: "Outstanding", tone: "warning" } : { label: "Recovered", tone: "success" },
      };
    },
  },
  attendance: {
    noun: "pay input",
    columns: ["Employee / month", "Paid days", "Overtime", "Additions"],
    present: (d, name) => ({
      title: name("employees", d.employee_id) || "—",
      subtitle: day(d.month),
      meta: [`${Number(d.paid_days || 0)} of ${Number(d.period_days || 0)}`, `${Number(d.overtime_hours || 0)} h`],
      amount: rupees(Number(d.allowances || 0) + Number(d.bonus || 0) + Number(d.arrears || 0)),
      amountHint: Number(d.advance_recovery) ? `Recover ${rupees(d.advance_recovery)}` : undefined,
    }),
    sections: [
      ["Employee and days", ["employee_id", "month", "period_days", "paid_days", "hours", "units", "overtime_hours"]],
      ["Additions", ["allowances", "bonus", "arrears"]],
      ["Statutory and deductions", ["pf_wages", "esi_wages", "esi_employee_exempt", "tds", "professional_tax", "lwf", "advance_recovery", "other_deductions"], true],
    ],
  },
  expenses: {
    noun: "expense",
    columns: ["Expense", "Mode", "Reference", "Amount"],
    present: (d) => ({
      title: String(d.description || d.category || "—"),
      subtitle: join(day(d.date), String(d.category || ""), d.payee ? `Paid to ${d.payee}` : ""),
      meta: [String(d.payment_mode || "—"), String(d.reference || "—")],
      amount: rupees(d.amount, 2),
    }),
  },
  policy: {
    noun: "policy",
    columns: ["Period", "PF % (emp / employer)", "ESI % (emp / employer)", ""],
    present: (d) => ({
      title: span(d.effective_from, d.effective_to) || "—",
      subtitle: String(d.notes || ""),
      meta: [`${d.pf_employee_rate ?? 0}% / ${d.pf_employer_rate ?? 0}%`, `${d.esi_employee_rate ?? 0}% / ${d.esi_employer_rate ?? 0}%`],
      status: d.confirmed ? { label: "Verified", tone: "success" } : { label: "Not verified", tone: "warning" },
    }),
  },
  gst_settings: {
    noun: "GST registration",
    columns: ["Registration", "Type", "Returns", ""],
    present: (d) => ({ title: String(d.legal_name || "—"), subtitle: join(String(d.gstin || ""), d.state_code ? `State ${d.state_code}` : ""), meta: [cap(d.registration), cap(d.frequency)] }),
  },
  gst_adjustments: {
    noun: "GST entry",
    columns: ["Party / document", "Supply", "HSN / SAC", "Taxable value"],
    present: (d) => ({
      title: String(d.party_name || "—"),
      subtitle: join(String(d.document_number || ""), day(d.date), cap(d.direction)),
      meta: [cap(d.supply), String(d.hsn || "—")],
      amount: rupees(d.taxable, 2),
      amountHint: Number(d.igst) ? `IGST ${rupees(d.igst, 2)}` : Number(d.cgst) ? `CGST+SGST ${rupees(Number(d.cgst) + Number(d.sgst || 0), 2)}` : undefined,
    }),
  },
};

/** Generic row for registers without a presenter: first field as title, the next two as subtitle. */
export function fallbackPresenter(fields: Record<string, Field>, label: string): Presenter {
  const keys = Object.keys(fields);
  return {
    noun: "record",
    columns: [fields[keys[0]]?.label ?? label, fields[keys[3]]?.label ?? "", fields[keys[4]]?.label ?? "", ""],
    present: (d, name) => {
      const show = (k: string | undefined) => {
        if (!k) return "";
        const f = fields[k];
        const v = d[k];
        if (f.type === "boolean") return v ? "Yes" : "No";
        if (["employees", "sites", "customers"].includes(f.type)) return name(f.type, v);
        return v === undefined || v === "" ? "" : String(v);
      };
      return { title: show(keys[0]) || "—", subtitle: join(show(keys[1]), show(keys[2])), meta: [show(keys[3]) || "—", show(keys[4]) || "—"] };
    },
  };
}

/** Client-side status filter over the loaded records (the server returns at most 1,000). */
export function matchesFilter(p: Presenter, d: Record<string, Value>, filter: string) {
  if (!filter || !p.filterField) return true;
  if (p.filterField === "active") return filter === "active" ? d.active === true : d.active !== true;
  if (p.filterField === "__advance") {
    const due = Number(d.amount || 0) - Number(d.recovered || 0);
    return filter === "open" ? due > 0 : due <= 0;
  }
  return String(d[p.filterField]) === filter;
}

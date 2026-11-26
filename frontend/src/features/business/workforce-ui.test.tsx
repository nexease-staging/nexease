import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import BusinessWorkspace from "./workspace";
import ApprovalsInbox from "./workforce-approvals";
import { presenters } from "./record-presenters";
import { apiRequest } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn(), apiBinaryRequest: vi.fn() }));
vi.mock("./gst-lookup", () => ({ default: () => null }));
vi.mock("@/components/search-select", () => ({ default: ({ "aria-label": label, children, ...rest }: React.SelectHTMLAttributes<HTMLSelectElement>) => <select aria-label={label} {...rest}>{children}</select> }));
vi.mock("@/features/auth/auth-context", () => ({ useAuth: () => ({ authentication: { role: { permissions: ["payroll.read", "payroll.manage"] } } }) }));

const leaveSchema = { label: "Leave register", permission: "payroll", fields: {
  employee_id: { label: "Employee", type: "employees", required: true }, start_date: { label: "From date", type: "date", required: true },
  end_date: { label: "To date", type: "date", required: true }, leave_type: { label: "Leave type", type: "select", required: true, choices: ["paid", "casual"] },
  days: { label: "Days", type: "number", required: true }, status: { label: "Status", type: "select", required: true, choices: ["requested", "approved", "rejected"] },
} };
const leave = (id: string, status: string) => ({ id, key: id, revision: 1, data: { employee_id: "e1", start_date: "2026-11-27", end_date: "2026-11-28", leave_type: "casual", days: "2", status } });

function serve(extra: (path: string, options?: { body?: unknown }) => unknown = () => undefined) {
  vi.mocked(apiRequest).mockImplementation(((path: string, options?: { body?: unknown }) => {
    const custom = extra(path, options);
    if (custom) return Promise.resolve(custom);
    if (path === "/business/configuration/") return Promise.resolve({ data: { schemas: { leave_requests: leaveSchema } } });
    if (path.startsWith("/business/records/leave_requests/")) return Promise.resolve({ data: { records: [leave("l1", "requested"), leave("l2", "approved")], total: 2 } });
    if (path === "/business/workers/") return Promise.resolve({ data: { records: [{ id: "e1", key: "E1", revision: 1, data: { name: "Asha Patil", code: "E1" } }] } });
    return Promise.resolve({ data: { failed: [], updated: [] } });
  }) as never);
}

const wrap = (node: React.ReactNode) => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{node}</QueryClientProvider>);

beforeEach(() => vi.clearAllMocks());

describe("BusinessWorkspace", () => {
  it("shows readable leave rows, filters by status and approves in one tap", async () => {
    serve();
    wrap(<BusinessWorkspace kinds={["leave_requests"]} title="Leave & approvals" description="x" />);
    const list = await screen.findByRole("list", { name: "Leave register" });
    await within(list).findByText("Asha Patil");
    expect(within(list).getAllByRole("listitem")).toHaveLength(1); // "Requested" filter first
    expect(within(list).getByText("2 days")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Approve Asha Patil" }));
    await waitFor(() => expect(apiRequest).toHaveBeenCalledWith("/business/workforce/approvals/", { method: "POST", body: { kind: "leave_requests", ids: ["l1"], status: "approved" } }));
    fireEvent.click(screen.getByRole("button", { name: "All" }));
    expect(within(list).getAllByRole("listitem")).toHaveLength(2);
  });

  it("opens a grouped form sheet for a new record", async () => {
    serve();
    wrap(<BusinessWorkspace kinds={["leave_requests"]} title="Leave & approvals" description="x" />);
    await screen.findByRole("list", { name: "Leave register" });
    fireEvent.click(screen.getAllByRole("button", { name: "Add leave request" })[0]);
    const dialog = screen.getByRole("dialog", { name: "New leave request" });
    expect(within(dialog).getByLabelText("Days *")).toHaveValue(0);
    expect(within(dialog).getByRole("button", { name: "Save record" })).toBeInTheDocument();
  });
});

describe("ApprovalsInbox", () => {
  it("selects several requests and approves them together", async () => {
    const item = (id: string, name: string) => ({ ...leave(id, "requested"), employee: { name, code: id } });
    serve((path, options) => (path === "/business/workforce/approvals/" && !options
      ? { data: { today: "2026-11-26", can_manage: { leave_requests: true, timesheets: false }, leave: [item("l1", "Asha Patil"), item("l2", "Ravi Kumar")], timesheets: [], on_leave_today: [{ id: "x", employee: "Meena", until: "2026-11-27", leave_type: "sick" }] } }
      : undefined));
    wrap(<ApprovalsInbox />);
    fireEvent.click(await screen.findByRole("button", { name: "Select all" }));
    fireEvent.click(screen.getByRole("button", { name: "Approve 2" }));
    await waitFor(() => expect(apiRequest).toHaveBeenCalledWith("/business/workforce/approvals/", { method: "POST", body: { kind: "leave_requests", ids: ["l1", "l2"], status: "approved" } }));
    expect(screen.getByText(/On leave today: Meena/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: /Timesheets/ }));
    expect(screen.getByText(/All timesheets are approved/)).toBeInTheDocument();
  });
});

describe("presenters", () => {
  const name = (_: string, v: unknown) => (v === "e1" ? "Asha Patil" : v === "s1" ? "Hinjewadi" : String(v ?? ""));
  it("formats employees, timesheets and advances", () => {
    const emp = presenters.employees.present({ name: "Asha", code: "E1", designation: "Mason", rate: "800", basis: "daily", pf_member: true, active: true }, name, "E1");
    expect([emp.subtitle, emp.amount, emp.amountHint, emp.status?.label]).toEqual(["E1 · Mason", "₹800/day", "PF", "Active"]);
    const sheet = presenters.timesheets.present({ employee_id: "e1", site_id: "s1", date: "2026-11-26", shift: "Day", hours: "8", overtime_hours: "2", billable_units: "1", billing_rate: "1200", status: "draft" }, name, "");
    expect([sheet.meta[0], sheet.amount, sheet.status?.label]).toEqual(["8 h + 2 OT", "₹1,200", "Draft"]);
    const adv = presenters.advances.present({ employee_id: "e1", amount: "5000", recovered: "2000" }, name, "");
    expect([adv.amountHint, adv.status?.label]).toEqual(["₹3,000 to recover", "Outstanding"]);
  });
});

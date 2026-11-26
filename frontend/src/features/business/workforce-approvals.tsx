"use client";

import { useState } from "react";
import { CalendarCheck, CheckCircle2, Circle, ClipboardCheck, X } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CompactList, CompactRow } from "@/components/list/list-kit";
import { Badge } from "@/components/ui/badge";
import { apiRequest } from "@/lib/api/client";

type Item = { id: string; revision: number; data: Record<string, string>; employee: { name: string; code: string }; site?: { name: string } };
export interface ApprovalInbox {
  today: string;
  can_manage: { leave_requests: boolean; timesheets: boolean };
  leave: Item[];
  timesheets: Item[];
  on_leave_today: Array<{ id: string; employee: string; until: string; leave_type: string }>;
}

const short = (v?: string) => (v ? new Date(v + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : "");
const range = (a?: string, b?: string) => (a && b && a !== b ? `${short(a)} – ${short(b)}` : short(a || b));

export function useApprovals() {
  return useQuery({ queryKey: ["workforce-approvals"], queryFn: async () => (await apiRequest<ApprovalInbox>("/business/workforce/approvals/")).data, staleTime: 15_000 });
}

/** Pending leave and draft timesheets: tap to select, approve one or many at once. */
export default function ApprovalsInbox() {
  const qc = useQueryClient();
  const inbox = useApprovals();
  const [tab, setTab] = useState<"leave_requests" | "timesheets">("leave_requests");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const data = inbox.data;
  if (inbox.isPending) return <div className="nx-skeleton h-40" aria-busy="true" aria-label="Loading approvals" />;
  if (inbox.error || !data) return <p role="alert" className="nxl-error">{inbox.error?.message ?? "Could not load approvals."}</p>;

  const items = tab === "leave_requests" ? data.leave : data.timesheets;
  const canManage = data.can_manage[tab];
  const visible = new Set(items.map((i) => i.id));
  const chosen = [...selected].filter((id) => visible.has(id));
  const toggle = (id: string) => setSelected((prev) => { const next = new Set(prev); if (next.has(id)) next.delete(id); else next.add(id); return next; });

  async function decide(ids: string[], status: "approved" | "rejected") {
    setBusy(true); setMessage("");
    try {
      const result = await apiRequest<{ failed: Array<{ id: string; message: string }> }>("/business/workforce/approvals/", { method: "POST", body: { kind: tab, ids, status } });
      if (result.data.failed.length) setMessage(result.data.failed.map((f) => f.message).filter((m, i, all) => all.indexOf(m) === i).join(" "));
      setSelected(new Set());
      await Promise.all([qc.invalidateQueries({ queryKey: ["workforce-approvals"] }), qc.invalidateQueries({ queryKey: ["workforce-overview"] }), qc.invalidateQueries({ queryKey: ["business-records"] })]);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Could not update.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="nxl-panel" aria-label="Approvals">
      <header className="nxw-panel-head">
        <h2><ClipboardCheck size={17} aria-hidden="true" />Approvals</h2>
        <div className="nxf-segment" role="tablist" aria-label="Approval type">
          <button type="button" role="tab" aria-selected={tab === "leave_requests"} onClick={() => setTab("leave_requests")}>Leave <b>{data.leave.length}</b></button>
          <button type="button" role="tab" aria-selected={tab === "timesheets"} onClick={() => setTab("timesheets")}>Timesheets <b>{data.timesheets.length}</b></button>
        </div>
      </header>
      {message ? <p role="alert" className="nxl-error">{message}</p> : null}
      {!items.length ? (
        <p className="nxw-empty"><CheckCircle2 size={18} aria-hidden="true" />Nothing waiting. {tab === "leave_requests" ? "All leave requests are decided." : "All timesheets are approved."}</p>
      ) : (
        <>
          {canManage ? (
            <div className="nxw-bulk">
              <span>{chosen.length ? `${chosen.length} selected` : "Tap rows to select"}</span>
              <span className="flex gap-2">
                <button type="button" className="nx-button nx-secondary nx-btn-sm" disabled={busy} onClick={() => setSelected(chosen.length === items.length ? new Set() : new Set(items.map((i) => i.id)))}>{chosen.length === items.length ? "Clear" : "Select all"}</button>
                {tab === "leave_requests" ? <button type="button" className="nx-button nx-secondary nx-btn-sm" disabled={busy || !chosen.length} onClick={() => void decide(chosen, "rejected")}><X size={15} />Reject</button> : null}
                <button type="button" className="nx-button nx-btn-sm" disabled={busy || !chosen.length} onClick={() => void decide(chosen, "approved")}><CheckCircle2 size={15} />{busy ? "Saving…" : `Approve${chosen.length ? ` ${chosen.length}` : ""}`}</button>
              </span>
            </div>
          ) : null}
          <CompactList label={tab === "leave_requests" ? "Pending leave" : "Draft timesheets"} columns={[{ label: "Employee" }, { label: tab === "leave_requests" ? "Dates" : "Site" }, { label: tab === "leave_requests" ? "Days" : "Hours" }]}>
            {items.map((i) => {
              const on = selected.has(i.id);
              const Mark = on ? CheckCircle2 : Circle;
              const d = i.data;
              return (
                <CompactRow
                  key={i.id}
                  onOpen={canManage ? () => toggle(i.id) : undefined}
                  openLabel={`${on ? "Unselect" : "Select"} ${i.employee.name}`}
                  title={<span className="inline-flex items-center gap-2">{canManage ? <Mark size={16} aria-hidden="true" style={{ color: on ? "var(--nx-primary)" : "var(--nx-text-muted)" }} /> : null}{i.employee.name || "—"}</span>}
                  subtitle={tab === "leave_requests" ? `${d.leave_type} leave · ${range(d.start_date, d.end_date)}${d.notes ? ` · ${d.notes}` : ""}` : `${i.site?.name ?? ""} · ${short(d.date)} · ${d.shift} shift`}
                  meta={[tab === "leave_requests" ? range(d.start_date, d.end_date) : i.site?.name ?? ""]}
                  amount={tab === "leave_requests" ? `${Number(d.days)} day${Number(d.days) === 1 ? "" : "s"}` : `${Number(d.hours)} h${Number(d.overtime_hours) ? ` + ${Number(d.overtime_hours)} OT` : ""}`}
                  badge={<Badge tone="warning">{tab === "leave_requests" ? "Requested" : "Draft"}</Badge>}
                  actions={canManage ? [{ icon: CheckCircle2, label: `Approve ${i.employee.name}`, onClick: () => void decide([i.id], "approved"), disabled: busy }] : []}
                />
              );
            })}
          </CompactList>
        </>
      )}
      {data.on_leave_today.length ? (
        <p className="nxw-onleave"><CalendarCheck size={15} aria-hidden="true" />On leave today: {data.on_leave_today.map((l) => `${l.employee} (until ${short(l.until)})`).join(", ")}</p>
      ) : null}
    </section>
  );
}

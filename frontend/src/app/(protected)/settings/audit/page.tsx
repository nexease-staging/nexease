"use client";

import { useState } from "react";
import { FileSpreadsheet, LogIn, LogOut, ShieldAlert, ShieldCheck, ShieldX } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, useDebounced } from "@/components/list/list-kit";
import { Badge, type Tone } from "@/components/ui/badge";
import EmptyState from "@/components/ui/empty-state";
import { notify } from "@/components/nex-feedback";
import { useAuth } from "@/features/auth/auth-context";
import { useAuthenticationAuditList } from "@/features/audit/hooks";
import type { AuthenticationAuditEventType } from "@/features/audit/types";
import { downloadCsv } from "@/lib/export-csv";
import { hasPermission } from "@/lib/authorization/permissions";

type Filter = "" | AuthenticationAuditEventType;
const EVENTS: Record<AuthenticationAuditEventType, { label: string; tone: Tone; icon: typeof LogIn }> = {
  LOGIN_SUCCESS: { label: "Signed in", tone: "success", icon: LogIn },
  LOGIN_FAILED: { label: "Wrong password", tone: "warning", icon: ShieldAlert },
  LOGIN_BLOCKED: { label: "Blocked", tone: "danger", icon: ShieldX },
  LOGOUT: { label: "Signed out", tone: "neutral", icon: LogOut },
  LOGOUT_ALL: { label: "Signed out everywhere", tone: "info", icon: LogOut },
};
const filters: Array<{ value: Filter; label: string }> = [{ value: "", label: "All" }, { value: "LOGIN_FAILED", label: "Failed" }, { value: "LOGIN_BLOCKED", label: "Blocked" }, { value: "LOGIN_SUCCESS", label: "Sign-ins" }];
const when = (iso: string | null) => (iso ? new Date(iso).toLocaleString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "—");

export default function AuditPage() {
  const { authentication } = useAuth();
  const canRead = hasPermission(authentication?.role.permissions ?? [], "accounting_audit.read");
  const [filter, setFilter] = useState<Filter>("");
  const [searchInput, setSearchInput] = useState("");
  const identifier = useDebounced(searchInput.trim());
  const logs = useAuthenticationAuditList({ event_type: filter || undefined, identifier: identifier || undefined, limit: 200 }, canRead);
  if (!authentication) return null;
  if (!canRead) return <div className="nx-card"><EmptyState icon={ShieldCheck} title="Login activity unavailable" description="Your role does not include the accounting_audit.read permission." /></div>;
  const rows = logs.data?.authentication_audit_logs ?? [];

  function exportCsv() {
    void downloadCsv("NexEase-login-activity", rows, [
      { header: "Time", value: (r) => r.created_at }, { header: "Event", value: (r) => EVENTS[r.event_type]?.label ?? r.event_type },
      { header: "User", value: (r) => r.user?.email ?? r.identifier }, { header: "IP address", value: (r) => r.ip_address },
      { header: "Tamper check", value: (r) => (r.integrity.verified ? "Verified" : r.integrity.hashed ? "Not verified" : "Not sealed") },
    ]).catch((e: unknown) => notify(e instanceof Error ? e.message : "Export failed.", "error"));
  }

  return (
    <ListScreen<Filter>
      title="Login activity"
      subtitle="The latest 200 sign-ins, sign-outs, failed passwords and blocked attempts."
      actions={[{ icon: FileSpreadsheet, label: "Export login activity", onClick: exportCsv, disabled: !rows.length }]}
      onRefresh={() => void logs.refetch()}
      refreshing={logs.isFetching}
      search={{ value: searchInput, onChange: setSearchInput, placeholder: "Search by email used to sign in", label: "Search login activity" }}
      chips={{ options: filters, value: filter, onChange: setFilter, label: "Event type" }}
    >
      <ListState loading={logs.isPending} error={logs.error} onRetry={() => void logs.refetch()} isEmpty={!rows.length} emptyIcon={ShieldCheck}
        emptyTitle={filter || identifier ? "Nothing matches" : "No login activity yet"}>
        <CompactList label="Login activity" columns={[{ label: "Who" }, { label: "IP address" }, { label: "When" }]}>
          {rows.map((r) => {
            const e = EVENTS[r.event_type] ?? { label: r.event_type, tone: "neutral" as Tone, icon: LogIn };
            return (
              <CompactRow key={r.id}
                title={<span className="inline-flex items-center gap-2"><e.icon size={15} aria-hidden="true" />{r.user?.email ?? r.identifier ?? "Unknown"}</span>}
                subtitle={`${e.label}${r.ip_address ? ` · ${r.ip_address}` : ""}`}
                meta={[r.ip_address ?? "—"]}
                amount={when(r.created_at)}
                amountHint={r.integrity.hashed ? (r.integrity.verified ? "Tamper check passed" : "Tamper check failed") : undefined}
                badge={<Badge tone={e.tone}>{e.label}</Badge>} />
            );
          })}
        </CompactList>
      </ListState>
    </ListScreen>
  );
}

"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ChevronRight, Clock, FileSpreadsheet, Search, Star } from "lucide-react";
import EmptyState from "@/components/ui/empty-state";
import { useAuth } from "@/features/auth/auth-context";
import { hasPermission } from "@/lib/authorization/permissions";
import { allReports, favourites, recent, reportGroups, reportHref, type ReportEntry } from "../catalog";

function ReportLink({ report, starred, onStar }: { report: ReportEntry; starred: boolean; onStar: () => void }) {
  const Icon = report.icon;
  return (
    <li className="nxr-item">
      <Link href={reportHref(report.id)} className="nxr-item-link">
        <span className="nxr-item-icon"><Icon size={18} aria-hidden="true" /></span>
        <span className="min-w-0">
          <strong>{report.title}</strong>
          <span>{report.description}</span>
        </span>
        <ChevronRight size={16} aria-hidden="true" className="nxr-item-go" />
      </Link>
      <button type="button" className="nxr-star" aria-pressed={starred} aria-label={`${starred ? "Remove" : "Add"} ${report.title} ${starred ? "from" : "to"} favourites`} onClick={onStar}>
        <Star size={16} aria-hidden="true" />
      </button>
    </li>
  );
}

/** Catalogue of every report the user's role can open, with search, favourites and recents. */
export default function ReportsHub() {
  const { authentication } = useAuth();
  const permissions = useMemo(() => authentication?.role.permissions ?? [], [authentication]);
  const [search, setSearch] = useState("");
  const [starred, setStarred] = useState<string[]>(() => favourites.list());
  const [recentIds] = useState<string[]>(() => recent.list());
  const allowed = (report: ReportEntry) => report.permissions.some((p) => hasPermission(permissions, p));

  const term = search.trim().toLowerCase();
  const groups = useMemo(() => reportGroups
    .map((g) => ({ ...g, reports: g.reports.filter((r) => r.permissions.some((p) => hasPermission(permissions, p)) && (!term || `${g.name} ${r.title} ${r.description}`.toLowerCase().includes(term))) }))
    .filter((g) => g.reports.length), [permissions, term]);

  if (!authentication) return null;
  const pinned = starred.map((id) => allReports.find((r) => r.id === id)).filter((r): r is (typeof allReports)[number] => Boolean(r && allowed(r)));
  const recents = recentIds.map((id) => allReports.find((r) => r.id === id)).filter((r): r is (typeof allReports)[number] => Boolean(r && allowed(r))).slice(0, 4);
  const toggle = (id: string) => setStarred(favourites.toggle(id));

  return (
    <div className="nxl-screen">
      <header className="nxl-header">
        <div className="min-w-0">
          <h1>Reports</h1>
          <p className="nx-muted">Sales, purchases, GST, stock, profit and accounts. Star the ones you use most.</p>
        </div>
      </header>
      <label className="nxl-search nxr-hub-search">
        <Search size={16} aria-hidden="true" />
        <input type="search" aria-label="Search reports" placeholder="Search reports, e.g. HSN, profit, customer" value={search} onChange={(e) => setSearch(e.target.value)} />
      </label>

      {!term && (pinned.length || recents.length) ? (
        <div className="nxr-quick">
          {pinned.length ? (
            <section className="nxl-panel">
              <h2 className="nxr-group-title"><Star size={15} aria-hidden="true" />Favourites</h2>
              <ul className="nxr-list">{pinned.map((r) => <ReportLink key={r.id} report={r} starred onStar={() => toggle(r.id)} />)}</ul>
            </section>
          ) : null}
          {recents.length ? (
            <section className="nxl-panel">
              <h2 className="nxr-group-title"><Clock size={15} aria-hidden="true" />Recently opened</h2>
              <ul className="nxr-list">{recents.map((r) => <ReportLink key={r.id} report={r} starred={starred.includes(r.id)} onStar={() => toggle(r.id)} />)}</ul>
            </section>
          ) : null}
        </div>
      ) : null}

      {groups.length ? (
        <div className="nxr-groups">
          {groups.map((g) => (
            <section key={g.name} className="nxl-panel" aria-label={g.name}>
              <h2 className="nxr-group-title">{g.name}<span>{g.reports.length}</span></h2>
              <ul className="nxr-list">{g.reports.map((r) => <ReportLink key={r.id} report={r} starred={starred.includes(r.id)} onStar={() => toggle(r.id)} />)}</ul>
            </section>
          ))}
        </div>
      ) : (
        <div className="nxl-panel"><EmptyState icon={FileSpreadsheet} title={term ? "No report matches" : "No reports for your role"} description={term ? "Try another word, like GST, stock or customer." : "Ask an administrator for read access to sales, purchases or accounts."} /></div>
      )}
    </div>
  );
}

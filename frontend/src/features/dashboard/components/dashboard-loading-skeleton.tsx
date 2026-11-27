export default function DashboardLoadingSkeleton() {
  return (
    <div className="nxd-skeleton" role="status" aria-label="Loading dashboard">
      <span className="nxd-sk nxd-sk-band" />
      <span className="nxd-sk nxd-sk-strip" />
      <div className="nxd-grid">
        <span className="nxd-sk nxd-sk-card nxd-span-2" />
        <span className="nxd-sk nxd-sk-card" />
        <span className="nxd-sk nxd-sk-card nxd-span-2" />
        <span className="nxd-sk nxd-sk-card" />
      </div>
      <span className="sr-only">Loading your figures…</span>
    </div>
  );
}

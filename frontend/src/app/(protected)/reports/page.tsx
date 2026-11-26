"use client";

import dynamic from "next/dynamic";

// Favourites and recents come from this browser's storage, so render on the client only.
const ReportsHub = dynamic(() => import("@/features/reports/components/reports-hub"), { ssr: false });

export default function ReportsPage() {
  return <ReportsHub />;
}

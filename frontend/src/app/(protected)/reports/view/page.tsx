"use client";

import dynamic from "next/dynamic";

// The report id lives in ?id= so the page works in the static mobile build; render on the client only.
const ReportViewer = dynamic(() => import("@/features/reports/components/report-viewer"), { ssr: false });

function currentId() {
  return typeof window === "undefined" ? "" : new URLSearchParams(window.location.search).get("id") ?? "";
}

export default function ReportViewPage() {
  return <ReportViewer id={currentId()} />;
}

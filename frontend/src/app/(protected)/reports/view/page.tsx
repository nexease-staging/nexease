"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";

// The report id lives in ?id= so the page works in the static mobile build; render on the client only.
const ReportViewer = dynamic(() => import("@/features/reports/components/report-viewer"), { ssr: false });

function ReportFromQuery() {
  // useSearchParams (not window.location) is updated before render on in-app navigation.
  const id = useSearchParams().get("id") ?? "";
  return <ReportViewer key={id} id={id} />;
}

export default function ReportViewPage() {
  return (
    <Suspense fallback={null}>
      <ReportFromQuery />
    </Suspense>
  );
}

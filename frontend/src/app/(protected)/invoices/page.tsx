"use client";

import { Suspense } from "react";
import InvoicesView from "@/features/invoices/components/invoices-view";

// useSearchParams() needs a Suspense boundary for the static export used by the Capacitor mobile build.
export default function InvoicesPage() {
  return (
    <Suspense fallback={null}>
      <InvoicesView />
    </Suspense>
  );
}

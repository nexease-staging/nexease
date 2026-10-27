"use client";

import RequireAuth from "@/features/auth/components/require-auth";

import DashboardShell from "@/features/dashboard/components/dashboard-shell";


export default function DashboardPage() {
  return (
    <RequireAuth>
      <DashboardShell />
    </RequireAuth>
  );
}
"use client";

import {
  useState,
  type ReactNode,
} from "react";

import {EasyNav} from "@/components/mobile/easy-workspace";
import NexFeedback from "@/components/nex-feedback";
import Assistant from "@/features/saas/assistant";
import QuickCreate from "@/components/layout/quick-create";
import CommandPalette from "@/components/layout/command-palette";
import Link from "next/link";
import RequireAuth from "@/features/auth/components/require-auth";

import AppHeader from "@/components/layout/app-header";
import AppSidebar from "@/components/layout/app-sidebar";

export default function AppShell({
  children,
}: {
  children: ReactNode;
}) {
  const [
    mobileOpen,
    setMobileOpen,
  ] = useState(false);

  const [
    collapsed,
    setCollapsed,
  ] = useState(true);

  return (
    <RequireAuth>
      <div
        className="
          nx-app-shell flex h-dvh overflow-hidden
          bg-slate-50
        "
      >
        <AppSidebar
          mobileOpen={mobileOpen}
          collapsed={collapsed}
          onCloseMobile={() => {
            setMobileOpen(false);
          }}
          onToggleCollapsed={() => {
            setCollapsed(
              (current) => !current,
            );
          }}
        />

        <div
          className="
            min-w-0 flex-1 flex flex-col overflow-hidden
          "
        >
          <AppHeader
            onOpenMobile={() => {
              setMobileOpen(true);
            }}
          />

          <main className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4 sm:p-6">
            <div className="mb-3 text-right"><Link href="/subscription" className="text-sm font-semibold text-emerald-800">Subscription & usage</Link></div>
            {children}
          </main><div className="md:hidden"><EasyNav/></div>
        </div>
      </div>
      <Assistant/><NexFeedback/><QuickCreate variant="fab"/><CommandPalette/>
    </RequireAuth>
  );
}
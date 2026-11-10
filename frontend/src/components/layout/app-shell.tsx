"use client";

import {
  useState,
  type ReactNode,
} from "react";

import {EasyNav} from "@/components/mobile/easy-workspace";
import NexFeedback from "@/components/nex-feedback";
import PlanAccessGate from "@/features/saas/plan-access-gate";
import Assistant from "@/features/saas/assistant";

import CommandPalette from "@/components/layout/command-palette";
import RequireAuth from "@/features/auth/components/require-auth";

import ModuleNavigation from "@/components/layout/module-navigation";

import PullToRefresh from "@/components/mobile/pull-to-refresh";

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
  ] = useState(false);

  return (
    <RequireAuth>
      <div
        className="
          nx-app-shell flex h-dvh overflow-hidden
          bg-slate-50
        "
      >
        <div className="nx-drawer-wrapper" data-open={mobileOpen}>
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
        </div>

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

          <ModuleNavigation/>
          <main className="nx-workspace-main min-h-0 flex-1 overflow-y-auto overscroll-contain p-4 sm:p-6">
            <PlanAccessGate>{children}</PlanAccessGate>
            <footer className="nx-workspace-footer"><span>© {new Date().getFullYear()} NexEase</span><a href="https://wa.me/919209753378" target="_blank" rel="noopener noreferrer">WhatsApp support ↗</a></footer>
          </main><div className="md:hidden"><EasyNav/></div>
        </div>
      </div>
      <PullToRefresh/><Assistant/><NexFeedback/><CommandPalette/>
    </RequireAuth>
  );
}
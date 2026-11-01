"use client";

import { useQuery } from "@tanstack/react-query";
import { getConfig } from "@/features/business/workspace";
import { useState } from "react";
import Link from "next/link";

import {
  usePathname,
} from "next/navigation";

import {
  Boxes,
  PanelLeftClose,
  PanelLeftOpen,
  X,
} from "lucide-react";

import {
  navigationSections, workforceSections,
} from "@/config/navigation";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  hasPermission,
} from "@/lib/authorization/permissions";

interface AppSidebarProps {
  mobileOpen: boolean;
  collapsed: boolean;
  onCloseMobile: () => void;
  onToggleCollapsed: () => void;
}

export default function AppSidebar({
  mobileOpen,
  collapsed,
  onCloseMobile,
  onToggleCollapsed,
}: AppSidebarProps) {
  const pathname = usePathname();
  const compact = collapsed && !mobileOpen;
  const config = useQuery({queryKey:["business-config"],queryFn:getConfig});
  const [closed, setClosed] = useState<Record<string, boolean>>(Object.fromEntries(navigationSections.map(s => [s.label, true])));

  const {
    authentication,
  } = useAuth();

  const permissions =
    authentication
      ?.role
      .permissions
    ??
    [];

  const workforceMode=pathname.startsWith("/workforce");
  const visibleSections =
    (workforceMode?workforceSections:navigationSections)
      .filter(section => section.label !== 'Workforce' || config.data?.modules?.workforce !== false)
      .filter(section => !['Finance','Taxation','Barcode'].includes(section.label) || config.data?.modules?.[section.label.toLowerCase()] !== false)
      .filter(section => section.label !== 'Expenses' || config.data?.modules?.expenses !== false)
      .filter(section => section.label === 'Expenses' || !config.data || ["Overview", "Administration", "Barcode"].includes(section.label) || config.data.profile.modules.includes(section.label))
      .map((section) => ({
        ...section,

        items: section.items.filter(
          (item) =>
            (item.href !== '/workforce/accounts' || config.data?.modules?.finance !== false) &&
            hasPermission(
              permissions,
              item.permission,
            ),
        ),
      }))
      .filter(
        (section) =>
          section.items.length > 0,
      );

  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={onCloseMobile}
          className="
            fixed inset-0 z-40
            bg-slate-950/40 backdrop-blur-sm
            lg:hidden
          "
        />
      )}

      <aside
        className={`
          fixed inset-y-0 left-0 z-50
          flex h-dvh shrink-0 w-72 flex-col overflow-hidden
          border-r border-slate-200
          bg-white transition-all duration-200
          lg:static lg:z-auto
          ${
            mobileOpen
              ? "translate-x-0"
              : "-translate-x-full lg:translate-x-0"
          }
          ${
            compact
              ? "lg:w-20"
              : "lg:w-72"
          }
        `}
      >
        <div
          className="
            flex h-16 shrink-0 items-center
            border-b border-slate-200
            px-4
          "
        >
          <div
            className="
              flex min-w-0 flex-1
              items-center gap-3
            "
          >
            <div
              className="
                flex size-10 shrink-0
                items-center justify-center
                rounded-xl bg-blue-600
                text-white
              "
            >
              <img src="/nexease-logo.jpeg" alt="NexEase" className="size-10 rounded-xl object-contain"/>
            </div>

            {!compact && (
              <div className="min-w-0">
                {config.data?.logo&&<img src={config.data.logo} alt="Organisation logo" className="h-8 max-w-32 object-contain"/>}
                <p
                  className="
                    truncate font-bold
                    text-slate-900
                  "
                >
                  NexEase
                </p>

                <p
                  className="
                    truncate text-xs
                    text-slate-500
                  "
                >
                  {pathname.startsWith("/workforce")?"Workforce workspace":"Business Management"}
                </p>
              </div>
            )}
          </div>

          <button
            type="button"
            aria-label="Close navigation"
            onClick={onCloseMobile}
            className="
              rounded-lg p-2 text-slate-500
              hover:bg-slate-100
              lg:hidden
            "
          >
            <X size={20} />
          </button>
        </div>

        <nav
          className="
            min-h-0 flex-1 overflow-y-auto overscroll-contain
            px-3 py-4
          "
        >
          {workforceMode && <Link href="/dashboard" className="block mb-5 rounded-xl bg-slate-100 p-3 text-sm">← Back to business</Link>}
          {visibleSections.map(
            (section) => (
              <div
                key={section.label}
                className="mb-6"
              >
                {!compact && (
                  <button type="button" aria-expanded={!closed[section.label]} onClick={() => setClosed({...closed,[section.label]:!closed[section.label]})}
                    className="
                      mb-2 px-3 text-xs
                      font-semibold uppercase
                      tracking-wider
                      text-slate-400
                    "
                  >
                    {section.label} {closed[section.label] ? "＋" : "−"}
                  </button>
                )}

                <div className="space-y-1" hidden={!compact && !!closed[section.label]}>
                  {section.items.map(
                    (item) => {
                      const active =
                        pathname
                          ===
                          item.href
                        ||
                        (item.href!=="/workforce" && pathname.startsWith(`${item.href}/`));

                      const Icon =
                        item.icon;

                      return (
                        <Link
                          key={item.href}
                          href={item.href}
                          title={
                            compact
                              ? item.label
                              : undefined
                          }
                          onClick={
                            onCloseMobile
                          }
                          className={`
                            flex items-center
                            rounded-lg px-3 py-2.5
                            text-sm font-medium
                            transition
                            ${
                              compact
                                ? "lg:justify-center"
                                : "gap-3"
                            }
                            ${
                              active
                                ? "bg-blue-50 text-blue-700"
                                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                            }
                          `}
                        >
                          <Icon
                            size={19}
                            className="shrink-0"
                          />

                          {!compact && (
                            <span>
                              {item.label}
                            </span>
                          )}
                        </Link>
                      );
                    },
                  )}
                </div>
              </div>
            ),
          )}
        </nav>

        <div
          className="
            hidden border-t
            border-slate-200 p-3
            lg:block
          "
        >
          <button
            type="button"
            onClick={onToggleCollapsed}
            className="
              flex w-full items-center
              justify-center gap-2
              rounded-lg px-3 py-2
              text-sm font-medium
              text-slate-600
              hover:bg-slate-100
            "
          >
            {compact ? (
              <PanelLeftOpen size={19} />
            ) : (
              <>
                <PanelLeftClose size={19} />
                <span>Collapse sidebar</span>
              </>
            )}
          </button>
        </div>
      </aside>
    </>
  );
}
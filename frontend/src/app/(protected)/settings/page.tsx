"use client";
import { ThemeToggle } from "@/components/theme-provider";

import Link from "next/link";

import {
  Building2,
  ChevronRight,
  KeyRound,
  Settings,
  ShieldCheck,
  Tags,
  Users,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import {
  hasPermission,
} from "@/lib/authorization/permissions";


interface AdministrationCard {
  title: string;
  description: string;
  href: string;
  permission: string;
  icon: typeof Settings;
}


const administrationCards:
  AdministrationCard[] = [
{title:"Business modules & books",description:"Enable workforce and expenses, prepare system accounts, and export accountant data.",href:"/settings/modules",permission:"organizations.update",icon:Settings},
{title:"Numbering",description:"Automatic and manual references, prefixes and sequences.",href:"/settings/numbering",permission:"organizations.update",icon:Settings},
    {
    title: "Organization",
    description:
        "Manage company profile, contact details, currency, country, and timezone.",
    href: "/settings/organization",
    permission:
        "organizations.update",
    icon: Building2,
    },
    {
      title: "Categories",
      description:
        "Manage product categories used to organize your inventory and products.",
      href: "/settings/categories",
      permission:
        "products.read",
      icon: Tags,
    },
    {
      title: "Users",
      description:
        "Manage organization users, account access, roles, and active status.",
      href: "/settings/users",
      permission:
        "users.read",
      icon: Users,
    },
    {
      title: "Roles",
      description:
        "Create and manage roles, permissions, and role availability.",
      href: "/settings/roles",
      permission:
        "roles.read",
      icon: ShieldCheck,
    },
    {
      title: "Permissions",
      description:
        "Review application permissions available for assignment to roles.",
      href: "/settings/permissions",
      permission:
        "permissions.read",
      icon: KeyRound,
    },
    {
      title: "Authentication Audit",
      description:
        "Review login, logout, blocked access, and authentication security activity.",
      href: "/settings/audit",
      permission:
        "accounting_audit.read",
      icon: ShieldCheck,
    },
  ];


export default function SettingsPage() {
  const {
    authentication,
  } = useAuth();

  if (!authentication) {
    return null;
  }

  const permissions =
    authentication
      .role
      .permissions
    ??
    [];

  const visibleCards =
    administrationCards.filter(
      (card) =>
        hasPermission(
          permissions,
          card.permission,
        ),
    );

  return (
    <section className="space-y-6">
<section className="nx-panel mb-6"><h2 className="text-lg font-semibold mb-3">Appearance</h2><ThemeToggle /></section>
      <div>
        <div
          className="
            flex items-center gap-2
          "
        >
          <Settings
            size={26}
            className="text-blue-600"
          />

          <h1
            className="
              text-2xl font-bold
              text-slate-900
            "
          >
            Administration
          </h1>
        </div>

        <p
          className="
            mt-1 max-w-2xl
            text-sm leading-6
            text-slate-600
          "
        >
          Manage your organization,
          users, roles, permissions,
          and security activity from
          one place.
        </p>
      </div>

      {visibleCards.length === 0 ? (
        <div
          className="
            rounded-2xl border
            border-amber-200
            bg-amber-50 p-6
          "
        >
          <h2
            className="
              font-semibold
              text-amber-900
            "
          >
            Administration access restricted
          </h2>

          <p
            className="
              mt-2 text-sm
              text-amber-800
            "
          >
            Your current role does not
            include access to any
            Administration sections.
          </p>
        </div>
      ) : (
        <div
          className="
            grid gap-4
            md:grid-cols-2
            xl:grid-cols-2
          "
        >
          {visibleCards.map(
            (card) => {
              const Icon =
                card.icon;

              return (
                <Link
                  key={card.href}
                  href={card.href}
                  className="
                    group rounded-2xl
                    border border-slate-200
                    bg-white p-5
                    shadow-sm
                    transition
                    hover:border-blue-200
                    hover:shadow-md
                  "
                >
                  <div
                    className="
                      flex items-start
                      justify-between
                      gap-4
                    "
                  >
                    <div
                      className="
                        flex items-start
                        gap-4
                      "
                    >
                      <div
                        className="
                          rounded-xl
                          bg-blue-50
                          p-3
                          text-blue-600
                          transition
                          group-hover:bg-blue-100
                        "
                      >
                        <Icon
                          size={22}
                        />
                      </div>

                      <div>
                        <h2
                          className="
                            font-semibold
                            text-slate-900
                          "
                        >
                          {card.title}
                        </h2>

                        <p
                          className="
                            mt-1
                            text-sm
                            leading-6
                            text-slate-600
                          "
                        >
                          {
                            card.description
                          }
                        </p>
                      </div>
                    </div>

                    <ChevronRight
                      size={19}
                      className="
                        mt-1 shrink-0
                        text-slate-400
                        transition
                        group-hover:
                          translate-x-1
                        group-hover:
                          text-blue-600
                      "
                    />
                  </div>
                </Link>
              );
            },
          )}
        </div>
      )}

      <div
        className="
          rounded-2xl border
          border-slate-200
          bg-slate-50 p-5
        "
      >
        <h2
          className="
            text-sm font-semibold
            text-slate-900
          "
        >
          Access control
        </h2>

        <p
          className="
            mt-1 text-sm
            leading-6 text-slate-600
          "
        >
          Administration sections are
          displayed according to the
          permissions assigned to your
          current role. Backend permission
          checks remain authoritative for
          protected operations.
        </p>
      </div>
    </section>
  );
}
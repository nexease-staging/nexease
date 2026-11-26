"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Blocks, Building2, CheckCircle2, ChevronRight, Circle, FileText, Hash, KeyRound, Mail, Palette, Search,
  ShieldCheck, Tags, UserCog, Users, type LucideIcon,
} from "lucide-react";
import { ThemeToggle } from "@/components/theme-provider";
import MailboxSettings from "@/features/business/mailbox-settings";
import { useAuth } from "@/features/auth/auth-context";
import { apiRequest } from "@/lib/api/client";
import { hasPermission } from "@/lib/authorization/permissions";

interface SetupItem { key: string; title: string; description: string; href: string; done: boolean }
interface SetupStatus { items: SetupItem[]; done: number; total: number; percent: number }
interface Card { title: string; description: string; href: string; permission: string; icon: LucideIcon }

const groups: Array<{ name: string; cards: Card[] }> = [
  {
    name: "Business",
    cards: [
      { title: "Business profile", description: "Name, address, phone, email, currency and time zone.", href: "/settings/organization", permission: "organizations.update", icon: Building2 },
      { title: "Invoice formats & logo", description: "Logo, template, bank details, terms and signature.", href: "/settings/invoices", permission: "organizations.update", icon: FileText },
      { title: "Numbering", description: "Prefixes and next numbers for invoices, bills, receipts and codes.", href: "/settings/numbering", permission: "organizations.update", icon: Hash },
      { title: "Business modules & books", description: "Turn workforce, expenses and GST on or off; accountant export.", href: "/settings/modules", permission: "organizations.update", icon: Blocks },
      { title: "Categories & units", description: "Product categories and units of measure.", href: "/settings/categories", permission: "products.read", icon: Tags },
    ],
  },
  {
    name: "Team & security",
    cards: [
      { title: "Users", description: "Invite staff, change roles, turn access on or off.", href: "/settings/users", permission: "users.read", icon: Users },
      { title: "Roles", description: "What each role can see and do.", href: "/settings/roles", permission: "roles.read", icon: UserCog },
      { title: "Permissions", description: "Every permission, grouped by module.", href: "/settings/permissions", permission: "permissions.read", icon: KeyRound },
      { title: "Login activity", description: "Sign-ins, failed attempts and blocked access.", href: "/settings/audit", permission: "accounting_audit.read", icon: ShieldCheck },
    ],
  },
];

export default function SettingsHub() {
  const { authentication } = useAuth();
  const permissions = useMemo(() => authentication?.role.permissions ?? [], [authentication]);
  const [search, setSearch] = useState("");
  const [showDone, setShowDone] = useState(false);
  const setup = useQuery({ queryKey: ["setup-status"], queryFn: async () => (await apiRequest<SetupStatus>("/business/setup-status/")).data, staleTime: 60_000 });
  const term = search.trim().toLowerCase();
  const visible = useMemo(() => groups
    .map((g) => ({ ...g, cards: g.cards.filter((c) => hasPermission(permissions, c.permission) && (!term || `${g.name} ${c.title} ${c.description}`.toLowerCase().includes(term))) }))
    .filter((g) => g.cards.length), [permissions, term]);
  if (!authentication) return null;
  const s = setup.data;
  const todo = s?.items.filter((i) => !i.done) ?? [];
  const finished = s?.items.filter((i) => i.done) ?? [];
  const show = (words: string) => !term || words.toLowerCase().includes(term);

  return (
    <div className="nxl-screen">
      <header className="nxl-header">
        <div className="min-w-0">
          <h1>Settings</h1>
          <p className="nx-muted">{authentication.organization?.name ?? "Your business"} · business details, team, numbering and appearance.</p>
        </div>
      </header>

      <label className="nxr-hub-search">
        <Search size={16} aria-hidden="true" />
        <input type="search" aria-label="Search settings" placeholder="Search settings, e.g. logo, users, numbering" value={search} onChange={(e) => setSearch(e.target.value)} />
      </label>

      {!term && s && s.done < s.total ? (
        <section className="nxl-panel nxs-setup" aria-label="Setup checklist">
          <div className="nxs-setup-head">
            <div>
              <h2>Finish setting up</h2>
              <p>{s.done} of {s.total} done. Each step takes a minute or two.</p>
            </div>
            <div className="nxs-ring" role="img" aria-label={`${s.percent}% complete`} style={{ ["--p" as string]: `${s.percent}%` }}><span>{s.percent}%</span></div>
          </div>
          <div className="nxs-bar" aria-hidden="true"><span style={{ width: `${s.percent}%` }} /></div>
          <ul className="nxs-steps">
            {todo.map((i) => (
              <li key={i.key}>
                <Link href={i.href}>
                  <Circle size={18} aria-hidden="true" />
                  <span><strong>{i.title}</strong><span>{i.description}</span></span>
                  <ChevronRight size={16} aria-hidden="true" />
                </Link>
              </li>
            ))}
          </ul>
          {finished.length ? (
            <button type="button" className="nxs-toggle" aria-expanded={showDone} onClick={() => setShowDone(!showDone)}>{showDone ? "Hide" : "Show"} {finished.length} done</button>
          ) : null}
          {showDone ? (
            <ul className="nxs-steps" aria-label="Done">
              {finished.map((i) => <li key={i.key} data-done><Link href={i.href}><CheckCircle2 size={18} aria-hidden="true" /><span><strong>{i.title}</strong></span></Link></li>)}
            </ul>
          ) : null}
        </section>
      ) : null}

      <div className="nxr-groups">
        {visible.map((g) => (
          <section key={g.name} className="nxl-panel" aria-label={g.name}>
            <h2 className="nxr-group-title">{g.name}</h2>
            <ul className="nxr-list">
              {g.cards.map((c) => (
                <li key={c.href} className="nxr-item">
                  <Link href={c.href} className="nxr-item-link">
                    <span className="nxr-item-icon"><c.icon size={18} aria-hidden="true" /></span>
                    <span className="min-w-0"><strong>{c.title}</strong><span>{c.description}</span></span>
                    <ChevronRight size={16} aria-hidden="true" className="nxr-item-go" />
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ))}
        {show("appearance dark light theme mode") ? (
          <section className="nxl-panel" aria-label="Appearance">
            <h2 className="nxr-group-title"><Palette size={15} aria-hidden="true" />Appearance</h2>
            <div className="flex flex-wrap items-center justify-between gap-3 px-4 pb-4 text-sm">
              <span className="nx-muted">Light or dark screens on this device.</span>
              <ThemeToggle />
            </div>
          </section>
        ) : null}
      </div>

      {show("email mailbox gmail outlook sending") ? (
        <section id="email" className="nxl-panel mt-4 p-4" aria-label="Email sending">
          <h2 className="nxr-group-title !p-0 !pb-3"><Mail size={15} aria-hidden="true" />Email sending</h2>
          <MailboxSettings />
        </section>
      ) : null}
    </div>
  );
}

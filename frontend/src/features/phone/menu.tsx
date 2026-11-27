"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BarChart3, Boxes, ChevronDown, ChevronRight, CircleHelp, FileText, Landmark, LogOut, Receipt, RefreshCw, Search, Settings, ShieldCheck, Users, Wallet, type LucideIcon } from "lucide-react";
import { useEasyFeatures } from "@/components/mobile/easy-workspace";
import MobileConnection from "@/components/mobile/mobile-connection";
import DeviceNotificationSettings from "@/components/mobile/device-notification-settings";
import { ThemeChooser } from "@/components/theme-provider";
import { useAuth } from "@/features/auth/auth-context";

const ICONS: Record<string, LucideIcon> = {
  Overview: BarChart3, Sales: FileText, Purchases: Receipt, Purchasing: Receipt, Inventory: Boxes, Finance: Landmark, Taxation: ShieldCheck, Expenses: Wallet,
  Workforce: Users, Administration: Settings, Reports: BarChart3, Tally: RefreshCw, Barcode: Boxes,
};
const FRIENDLY: Record<string, string> = { Overview: "Start here", Administration: "Admin & settings" };
const VERSION = process.env.NEXT_PUBLIC_APP_VERSION || "2.1";

function SettingsView({ onBack }: { onBack: () => void }) {
  const { authentication, signOut } = useAuth();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  if (!authentication) return null;
  const { user, organization, role } = authentication;
  const out = async () => {
    setBusy(true);
    try { await signOut(); router.replace("/login"); } finally { setBusy(false); }
  };
  return (
    <div className="nxp-page">
      <button type="button" className="nxp-crumb" onClick={onBack}><ChevronDown size={18} className="nxp-back" />Menu</button>
      <div className="nxp-card nxp-account">
        <span className="nxp-avatar" aria-hidden>{((user.first_name?.[0] || "") + (user.last_name?.[0] || "")).toUpperCase() || "U"}</span>
        <div className="min-w-0"><b>{user.full_name || `${user.first_name} ${user.last_name}`}</b><small>{user.email}</small><small>{organization.name} · {role.name}</small></div>
      </div>
      <h3 className="nxp-group">Appearance</h3>
      <ThemeChooser />
      <h3 className="nxp-group">Notifications</h3>
      <div className="nxp-card"><DeviceNotificationSettings /></div>
      <h3 className="nxp-group">Business</h3>
      <div className="nxp-card nxp-list">
        {[["Organization profile", "/settings/organization"], ["Invoice format & numbering", "/settings/invoices"], ["Users & roles", "/settings/users"], ["Tally sync", "/tally?tab=sync"], ["Plan & subscription", "/subscription"], ["All settings", "/settings"]].map(([l, h]) => (
          <Link key={h} href={h} className="nxp-row nxp-link"><div className="nxp-g"><b>{l}</b></div><ChevronRight size={16} /></Link>
        ))}
      </div>
      <div className="nxp-card nxp-list">
        <a href="https://wa.me/919209753378" target="_blank" rel="noopener noreferrer" className="nxp-row nxp-link"><div className="nxp-g"><b>Help & support</b><small>WhatsApp +91 92097 53378</small></div><CircleHelp size={18} /></a>
      </div>
      <button type="button" className="nxp-btn danger" disabled={busy} onClick={() => void out()}><LogOut size={18} />{busy ? "Signing out…" : "Log out"}</button>
      <MobileConnection />
      <p className="nxp-version">NexEase v{VERSION}</p>
    </div>
  );
}

const ORDER = ["Overview", "Sales", "Purchasing", "Purchases", "Inventory", "Expenses", "Finance", "Taxation", "Tally", "Workforce", "Barcode", "Administration"];
const rank = (label: string) => (ORDER.indexOf(label) + 1 || 99);

export default function PhoneMenu() {
  const sections = [...useEasyFeatures()].sort((a, b) => rank(a.label) - rank(b.label));
  const [open, setOpen] = useState("");
  const [term, setTerm] = useState("");
  const [settings, setSettings] = useState(false);
  useEffect(() => {
    // Opened from the gear in the top bar: /tools?settings=1
    const sync = () => setSettings(new URLSearchParams(window.location.search).get("settings") === "1");
    sync();
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);
  const showSettings = (on: boolean) => {
    window.history.pushState(window.history.state, "", on ? "/tools?settings=1" : "/tools");
    setSettings(on);
  };
  if (settings) return <SettingsView onBack={() => showSettings(false)} />;
  const t = term.trim().toLowerCase();
  const hits = t ? sections.flatMap((s) => s.items.map((i) => ({ ...i, group: s.label }))).filter((i) => `${i.label} ${i.group}`.toLowerCase().includes(t)) : null;
  return (
    <div className="nxp-page">
      <label className="nxp-search nxp-gap"><Search size={18} /><input aria-label="Search all features" placeholder="Search all features" value={term} onChange={(e) => setTerm(e.target.value)} /></label>
      {hits ? (
        <div className="nxp-card nxp-list">
          {hits.length ? hits.map((i) => <Link key={i.group + i.href} href={i.href} className="nxp-row nxp-link"><div className="nxp-g"><b>{i.label}</b><small>{FRIENDLY[i.group] ?? i.group}</small></div><ChevronRight size={16} /></Link>)
            : <div className="nxp-empty nxp-empty-sm">No feature matches “{term}”.</div>}
        </div>
      ) : sections.map((s) => {
        const Icon = ICONS[s.label] ?? FileText;
        const isOpen = open === s.label;
        return (
          <div className="nxp-card nxp-acc" key={s.label}>
            <button type="button" className="nxp-accbtn" aria-expanded={isOpen} onClick={() => setOpen(isOpen ? "" : s.label)}><Icon size={20} /><span>{FRIENDLY[s.label] ?? s.label}</span><small>{s.items.length}</small><ChevronDown size={18} className={"nxp-chev" + (isOpen ? " open" : "")} /></button>
            {isOpen ? <div className="nxp-accbody">{s.items.map((i) => <Link key={i.href} href={i.href} className="nxp-row nxp-link"><span className="nxp-g">{i.label}</span><ChevronRight size={16} /></Link>)}</div> : null}
          </div>
        );
      })}
      {!hits ? <button type="button" className="nxp-card nxp-acc nxp-accbtn" onClick={() => showSettings(true)}><Settings size={20} /><span>Settings</span><ChevronRight size={18} /></button> : null}
      <p className="nxp-version">NexEase v{VERSION}</p>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  ArrowDownLeft, ArrowUpRight, BarChart3, Boxes, ChevronDown, CircleHelp, ClipboardList, FileText, Home, Landmark, Menu, Package, PackagePlus, Plus, Receipt, Repeat,
  Settings, Truck, Undo2, UserPlus, Users, Wallet, X,
} from "lucide-react";
import { navigationSections, workforceSections } from "@/config/navigation";
import { useAuth } from "@/features/auth/auth-context";
import { runQuick, type QuickAction } from "@/features/mobile/quick-actions";
import NotificationMenu from "@/features/notifications/components/notification-menu";
import { hasPermission } from "@/lib/authorization/permissions";

/** Screens that are one of the four tabs: they show the logo; every other screen shows Back. */
const ROOTS = ["/home", "/overview", "/products", "/tools"];
const norm = (p: string) => p.replace(/\/$/, "") || "/";

const EXTRA_TITLES: Record<string, string> = { "/parties": "Parties", "/payments": "Payments", "/settings": "Settings", "/tally": "Tally" };

export function screenTitle(path: string) {
  const p = norm(path);
  if (EXTRA_TITLES[p]) return EXTRA_TITLES[p];
  const items = [...navigationSections, ...workforceSections].flatMap((s) => s.items);
  const exact = items.find((i) => norm(i.href.split("?")[0]) === p);
  if (exact) return exact.label;
  const prefix = items.filter((i) => p.startsWith(norm(i.href.split("?")[0]) + "/")).sort((a, b) => b.href.length - a.href.length)[0];
  return prefix?.label ?? "NexEase";
}

export function PhoneTopBar() {
  const path = norm(usePathname());
  const router = useRouter();
  const root = ROOTS.includes(path);
  return (
    <header className="nxp-top">
      {root ? <img className="nxp-logo" src="/nexease-brand-icon.png" width={38} height={38} alt="" />
        : <button type="button" className="nxp-ic" aria-label="Back" onClick={() => (window.history.length > 1 ? router.back() : router.push("/home"))}><ChevronDown className="nxp-back" size={22} /></button>}
      <h1>{root ? "NexEase" : screenTitle(path)}</h1>
      {!root ? <button type="button" className="nxp-ic" aria-label="Help for this page" onClick={() => document.querySelector<HTMLButtonElement>(".nx-page-help")?.click()}><CircleHelp size={20} /></button> : null}
      <div className="nxp-bell"><NotificationMenu /></div>
      <Link className="nxp-ic" aria-label="Settings" href="/tools?settings=1"><Settings size={21} /></Link>
    </header>
  );
}

type Create = { label: string; icon: typeof FileText; quick?: QuickAction; href?: string; perm: string };
const CREATE: [string, Create[]][] = [
  ["Sell", [
    { label: "Sale invoice", icon: FileText, quick: "sale", perm: "invoices.create" },
    { label: "Payment-In", icon: ArrowDownLeft, quick: "payment_in", perm: "invoices.record_payment" },
    { label: "Quotation", icon: ClipboardList, href: "/quotations?new=1", perm: "invoices.create" },
    { label: "Sales order", icon: FileText, href: "/sales-orders?new=1", perm: "sales_orders.create" },
    { label: "Delivery challan", icon: Truck, href: "/delivery-challans?new=1", perm: "invoices.create" },
    { label: "Sales return", icon: Undo2, href: "/sales-returns?new=1", perm: "credit_notes.create" },
  ]],
  ["Buy", [
    { label: "Purchase bill", icon: Receipt, quick: "purchase", perm: "bills.create" },
    { label: "Payment-Out", icon: ArrowUpRight, quick: "payment_out", perm: "bills.record_payment" },
    { label: "Purchase order", icon: FileText, href: "/purchase-orders?new=1", perm: "purchase_orders.create" },
    { label: "Receive goods", icon: Package, href: "/goods-receipts?new=1", perm: "goods_receipts.create" },
  ]],
  ["Money", [
    { label: "Expense", icon: Wallet, quick: "expense", perm: "expenses.manage" },
    { label: "Journal entry", icon: FileText, href: "/journal-entries?new=1", perm: "journal_entries.create" },
    { label: "Bank transfer", icon: Landmark, href: "/banking", perm: "bank_accounts.read" },
  ]],
  ["People & stock", [
    { label: "Customer", icon: UserPlus, quick: "customer", perm: "customers.create" },
    { label: "Supplier", icon: UserPlus, quick: "supplier", perm: "suppliers.create" },
    { label: "Item", icon: PackagePlus, quick: "item", perm: "products.create" },
    { label: "Stock transfer", icon: Repeat, href: "/stock-transfers?new=1", perm: "inventory.transfer" },
    { label: "Opening stock", icon: Boxes, href: "/inventory", perm: "inventory.adjust" },
    { label: "Attendance", icon: Users, href: "/workforce", perm: "labour.read" },
  ]],
];

export function CreateSheet({ onClose }: { onClose: () => void }) {
  const { authentication } = useAuth();
  const perms = authentication?.role.permissions ?? [];
  const router = useRouter();
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  const go = (c: Create) => {
    onClose();
    if (c.quick) runQuick(c.quick);
    else if (c.href) router.push(c.href);
  };
  return (
    <div className="nxp-sheet-bg" onClick={onClose}>
      <div className="nxp-sheet" role="dialog" aria-modal="true" aria-label="Create new" onClick={(e) => e.stopPropagation()}>
        <div className="nxp-sheet-head"><b>Create new</b><button type="button" className="nxp-ic" aria-label="Close" onClick={onClose}><X size={20} /></button></div>
        {CREATE.map(([title, list]) => {
          const allowed = list.filter((c) => hasPermission(perms, c.perm));
          if (!allowed.length) return null;
          return (
            <div key={title}>
              <h3>{title}</h3>
              <div className="nxp-grid3">{allowed.map((c) => <button key={c.label} type="button" onClick={() => go(c)}><span className="nxp-qi"><c.icon size={20} /></span>{c.label}</button>)}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const TABS = [
  { href: "/home", label: "Home", icon: Home, match: ["/home", "/parties", "/payments"] },
  { href: "/overview", label: "Dashboard", icon: BarChart3, match: ["/overview", "/dashboard", "/reports", "/tally"] },
  null,
  { href: "/products", label: "Items", icon: Package, match: ["/products", "/inventory", "/stock-movements", "/stock-transfers", "/warehouses", "/barcode"] },
  { href: "/tools", label: "Menu", icon: Menu, match: ["/tools", "/settings"] },
];

export function PhoneTabBar() {
  const path = norm(usePathname());
  const [sheet, setSheet] = useState(false);
  return (
    <>
      <nav className="nxp-nav" aria-label="Main navigation">
        {TABS.map((t) => t ? (
          <Link key={t.href} href={t.href} aria-current={t.match.some((m) => path === m || path.startsWith(m + "/")) ? "page" : undefined}><t.icon size={22} />{t.label}</Link>
        ) : (
          <button key="plus" type="button" className="nxp-plus" aria-label="Create new" onClick={() => setSheet(true)}><Plus size={28} /></button>
        ))}
      </nav>
      {sheet ? <CreateSheet onClose={() => setSheet(false)} /> : null}
    </>
  );
}

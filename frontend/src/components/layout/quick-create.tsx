"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Boxes, FilePlus2, Plus, ReceiptText, Wallet, X, Zap, type LucideIcon } from "lucide-react";
import { useAuth } from "@/features/auth/auth-context";
import { hasPermission } from "@/lib/authorization/permissions";

export const quickCreateActions: Array<{ label: string; hint: string; href: string; icon: LucideIcon; permission: string }> = [
  { label: "New invoice", hint: "Items, tax and terms", href: "/invoices?new=1", icon: FilePlus2, permission: "invoices.create" },
  { label: "Quick invoice", hint: "Customer, items, done", href: "/invoices?new=direct", icon: Zap, permission: "invoices.create" },
  { label: "Record payment", hint: "Against an open invoice", href: "/customer-payments", icon: Wallet, permission: "invoices.read" },
  { label: "Daily expense", hint: "Log a cash or bank expense", href: "/expenses", icon: ReceiptText, permission: "expenses.read" },
  { label: "Scan barcode", hint: "Look up or count stock", href: "/barcode", icon: Boxes, permission: "inventory.read" },
];

/** variant="header": desktop popover. variant="fab": floating button + bottom sheet on phones. */
export default function QuickCreate({ variant }: { variant: "header" | "fab" }) {
  const { authentication } = useAuth();
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    const onDown = (e: PointerEvent) => { if (!box.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onDown);
    return () => { document.removeEventListener("keydown", onKey); document.removeEventListener("pointerdown", onDown); };
  }, [open]);

  if (!authentication) return null;
  const permissions = authentication.role.permissions;
  const items = quickCreateActions.filter((a) => hasPermission(permissions, a.permission));
  if (items.length === 0) return null;

  const isFab = variant === "fab";
  const list = (
    <ul role="menu" aria-label="Create">
      {items.map(({ label, hint, href, icon: Icon }) => (
        <li key={href} role="none">
          <Link role="menuitem" href={href} className="nx-menu-item" onClick={() => setOpen(false)}>
            <span className="nx-icon-chip" data-tone="success"><Icon size={19} aria-hidden="true" /></span>
            <span><strong className="text-sm">{label}</strong><small>{hint}</small></span>
          </Link>
        </li>
      ))}
    </ul>
  );

  return (
    <div ref={box} className={isFab ? "md:hidden" : "relative hidden md:block"}>
      {isFab ? (
        <button type="button" className="nx-fab" aria-label="Create new" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
          {open ? <X size={24} /> : <Plus size={24} />}
        </button>
      ) : (
        <button type="button" className="nx-button nx-btn-sm" aria-expanded={open} aria-haspopup="menu" onClick={() => setOpen((v) => !v)}>
          <Plus size={16} aria-hidden="true" />Create
        </button>
      )}
      {open && isFab ? (
        <>
          <div className="nx-sheet-backdrop" onClick={() => setOpen(false)} />
          <div className="nx-sheet"><div className="nx-sheet-grip" />{list}</div>
        </>
      ) : null}
      {open && !isFab ? <div className="nx-popover">{list}</div> : null}
    </div>
  );
}

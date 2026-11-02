"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { CornerDownLeft, Search, type LucideIcon } from "lucide-react";
import { navigationSections, workforceSections } from "@/config/navigation";
import { useAuth } from "@/features/auth/auth-context";
import { getConfig } from "@/features/business/workspace";
import { hasPermission } from "@/lib/authorization/permissions";
import { quickCreateActions } from "@/components/layout/quick-create";

const OPEN_EVENT = "nx:command-palette";
type Entry = { key: string; label: string; group: string; href: string; icon: LucideIcon };

/** Header button (icon on phones, "Search  Ctrl K" on desktop). */
export function CommandPaletteTrigger() {
  return (
    <button type="button" aria-label="Search and jump to…" onClick={() => window.dispatchEvent(new Event(OPEN_EVENT))}
      className="nx-icon-btn md:w-auto md:gap-2 md:px-3 md:text-sm">
      <Search size={18} aria-hidden="true" />
      <span className="nx-muted hidden md:inline">Search</span>
      <kbd className="nx-kbd hidden md:inline">Ctrl K</kbd>
    </button>
  );
}

export default function CommandPalette() {
  const router = useRouter();
  const { authentication } = useAuth();
  const config = useQuery({ queryKey: ["business-config"], queryFn: getConfig, enabled: !!authentication });
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [index, setIndex] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const permissions = authentication?.role.permissions;

  const entries = useMemo<Entry[]>(() => {
    const perms = permissions ?? [];
    const modules = config.data?.modules;
    const seen = new Set<string>();
    const out: Entry[] = quickCreateActions
      .filter((a) => hasPermission(perms, a.permission))
      .map((a) => ({ key: "a:" + a.href, label: a.label, group: "Create", href: a.href, icon: a.icon }));
    for (const section of [...navigationSections, ...workforceSections]) {
      const flag = section.label.toLowerCase();
      if (modules && ["workforce", "expenses", "finance", "taxation", "barcode"].includes(flag) && modules[flag] === false) continue;
      for (const item of section.items) {
        if (!hasPermission(perms, item.permission)) continue;
        const key = "n:" + item.href;
        if (seen.has(key)) continue;
        seen.add(key);
        out.push({ key, label: item.label, group: section.label, href: item.href, icon: item.icon });
      }
    }
    return out;
  }, [permissions, config.data?.modules]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (q ? entries.filter((e) => (e.label + " " + e.group).toLowerCase().includes(q)) : entries).slice(0, 30);
  }, [entries, query]);

  useEffect(() => {
    const toggle = () => { setQuery(""); setIndex(0); setOpen((v) => !v); };
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); toggle(); }
      else if (e.key === "Escape") setOpen(false);
    };
    const onOpen = () => { setQuery(""); setIndex(0); setOpen(true); };
    window.addEventListener("keydown", onKey);
    window.addEventListener(OPEN_EVENT, onOpen);
    return () => { window.removeEventListener("keydown", onKey); window.removeEventListener(OPEN_EVENT, onOpen); };
  }, []);

  useEffect(() => { if (open) input.current?.focus(); }, [open]);

  if (!open || !authentication) return null;

  const go = (entry?: Entry) => { if (!entry) return; setOpen(false); router.push(entry.href); };
  const onInputKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setIndex((i) => Math.min(i + 1, results.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setIndex((i) => Math.max(i - 1, 0)); }
    else if (e.key === "Enter") { e.preventDefault(); go(results[index]); }
  };

  return (
    <>
      <div className="nx-sheet-backdrop" style={{ zIndex: 69 }} onClick={() => setOpen(false)} />
      <div className="nx-palette" role="dialog" aria-modal="true" aria-label="Search and jump to">
        <input ref={input} value={query} onChange={(e) => { setQuery(e.target.value); setIndex(0); }} onKeyDown={onInputKey}
          placeholder="Jump to a page or start something new…" aria-label="Search" />
        <ul role="listbox">
          {results.length === 0 ? <li className="nx-muted p-4 text-sm">No matches.</li> : results.map((e, i) => (
            <li key={e.key} role="option" aria-selected={i === index}>
              <button type="button" className="nx-menu-item" aria-selected={i === index} onMouseEnter={() => setIndex(i)} onClick={() => go(e)}>
                <e.icon size={18} aria-hidden="true" />
                <span className="flex-1"><strong className="text-sm">{e.label}</strong><small>{e.group}</small></span>
                {i === index ? <CornerDownLeft size={14} className="nx-muted" aria-hidden="true" /> : null}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}

"use client";

import { useEffect, type ReactNode } from "react";
import { X, type LucideIcon } from "lucide-react";

export function Loading() {
  return <div className="nxp-skel" aria-label="Loading"><i /><i /><i /></div>;
}

export function ErrorState({ error, retry }: { error: unknown; retry: () => void }) {
  return <div className="nxp-empty"><p>{(error as Error)?.message || "Could not load. Check your connection."}</p><button type="button" className="nxp-btn ghost" onClick={retry}>Try again</button></div>;
}

export function Empty({ icon: Icon, text, cta, onCta }: { icon: LucideIcon; text: string; cta?: string; onCta?: () => void }) {
  return <div className="nxp-empty"><div className="nxp-qi big"><Icon size={28} /></div><p>{text}</p>{cta && onCta ? <button type="button" className="nxp-btn" onClick={onCta}>{cta}</button> : null}</div>;
}

/** Bottom sheet used for details on the phone. Closes on backdrop tap, Escape or the X. */
export function Sheet({ title, sub, onClose, children }: { title: ReactNode; sub?: ReactNode; onClose: () => void; children: ReactNode }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="nxp-sheet-bg" onClick={onClose}>
      <div className="nxp-sheet" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="nxp-sheet-head"><div className="min-w-0"><b>{title}</b>{sub ? <small>{sub}</small> : null}</div><button type="button" className="nxp-ic" aria-label="Close" onClick={onClose}><X size={20} /></button></div>
        {children}
      </div>
    </div>
  );
}

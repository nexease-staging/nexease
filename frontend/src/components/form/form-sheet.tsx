"use client";

/*
 * NexEase form kit: one shell for every create/edit form, web and mobile.
 *
 *   <FormSheet title onClose busy footer?>   // full screen on phones, centred panel on web
 *     <FormSection title icon>…fields…</FormSection>
 *     <FormActions total?>…buttons…</FormActions>  // optional in-form sticky action row
 *   </FormSheet>
 *
 * Inputs, selects and textareas inside the sheet are styled by nx-form.css, so older forms
 * get the same look without rewriting every field.
 */

import { useEffect, useId, useRef, type ReactNode } from "react";
import { X, type LucideIcon } from "lucide-react";

export function FormSheet({
  title,
  subtitle,
  onClose,
  busy = false,
  size = "lg",
  footer,
  titleId,
  closeLabel = "Close",
  children,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  onClose: () => void;
  busy?: boolean;
  size?: "md" | "lg" | "xl";
  footer?: ReactNode;
  titleId?: string;
  closeLabel?: string;
  children: ReactNode;
}) {
  const generated = useId();
  const headingId = titleId ?? generated;
  const panel = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  const busyRef = useRef(busy);
  useEffect(() => {
    closeRef.current = onClose;
    busyRef.current = busy;
  }, [onClose, busy]);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    panel.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busyRef.current) {
        event.stopPropagation();
        closeRef.current();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      previous?.focus?.();
    };
  }, []);

  return (
    <div className="nxf-overlay" role="presentation">
      <div ref={panel} tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby={headingId} className="nxf-sheet" data-size={size}>
        <header className="nxf-header">
          <div className="min-w-0">
            <h2 id={headingId}>{title}</h2>
            {subtitle ? <p>{subtitle}</p> : null}
          </div>
          <button type="button" className="nxf-close" aria-label={closeLabel} title={closeLabel} disabled={busy} onClick={onClose}>
            <X size={20} aria-hidden="true" />
          </button>
        </header>
        <div className="nxf-body">{children}</div>
        {footer ? <footer className="nxf-footer">{footer}</footer> : null}
      </div>
    </div>
  );
}

export function FormSection({ title, icon: Icon, aside, children, className = "" }: { title?: ReactNode; icon?: LucideIcon; aside?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`nxf-section ${className}`}>
      {title ? (
        <div className="nxf-section-head">
          <h3>{Icon ? <Icon size={16} aria-hidden="true" /> : null}{title}</h3>
          {aside}
        </div>
      ) : null}
      {children}
    </section>
  );
}

/** Action row: in a form it sticks to the bottom of the scrolling sheet. */
export function FormActions({ total, hint, children }: { total?: ReactNode; hint?: ReactNode; children: ReactNode }) {
  return (
    <div className="nxf-actions">
      {total !== undefined ? <div className="nxf-total"><span>Total</span><strong>{total}</strong></div> : hint ? <p className="nxf-hint">{hint}</p> : <span />}
      <div className="nxf-buttons">{children}</div>
    </div>
  );
}

export function FieldHint({ children }: { children: ReactNode }) {
  return <span className="nxf-field-hint">{children}</span>;
}

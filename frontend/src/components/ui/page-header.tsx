import type { ReactNode } from "react";

export default function PageHeader({ title, description, eyebrow, actions }: { title: string; description?: string; eyebrow?: string; actions?: ReactNode }) {
  return (
    <header className="nx-page-header flex flex-wrap items-center justify-between gap-3">
      <div className="min-w-0">
        {eyebrow ? <p className="nx-muted text-[11px] font-bold uppercase tracking-[.14em]">{eyebrow}</p> : null}
        <h1 className="text-2xl font-bold tracking-tight sm:text-[28px]">{title}</h1>
        {description ? <p className="nx-muted mt-1 max-w-2xl text-sm">{description}</p> : null}
      </div>
      {actions ? <div className="nx-page-actions flex items-center gap-2">{actions}</div> : null}
    </header>
  );
}

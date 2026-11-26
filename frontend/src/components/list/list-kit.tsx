"use client";

/*
 * NexEase list kit: one compact, Go GST Bill-style list pattern shared by every module.
 *
 *   <ListScreen title primary actions search chips onOpenFilters pager>
 *     <ListState query empty>  // loading / error / empty handling
 *       <CompactList columns>  // header labels on web
 *         <CompactRow title subtitle meta amount badge actions onOpen/>
 *
 * Web: header with icon actions + labelled primary button; rows show extra meta columns.
 * Mobile: same rows (party, number · date, amount, status) and a sticky bottom action bar.
 */

import { useEffect, useState, type CSSProperties, type ReactNode } from "react";
import { ChevronLeft, ChevronRight, RefreshCw, Search, SlidersHorizontal, type LucideIcon } from "lucide-react";
import EmptyState from "@/components/ui/empty-state";
import { Badge, type Tone } from "@/components/ui/badge";

export function useDebounced<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

export interface ListAction {
  icon: LucideIcon;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  busy?: boolean;
}

export function ActionIcon({ icon: Icon, label, onClick, disabled, busy, size = "md" }: ListAction & { size?: "sm" | "md" }) {
  return (
    <button
      type="button"
      className="nxl-icon"
      data-size={size}
      aria-label={label}
      title={label}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      onClick={(event) => {
        event.stopPropagation();
        onClick();
      }}
    >
      <Icon size={size === "sm" ? 16 : 18} strokeWidth={1.8} aria-hidden="true" className={busy ? "animate-pulse" : undefined} />
    </button>
  );
}

export interface ChipOption<V extends string> {
  value: V;
  label: string;
}

export interface Pagination {
  page: number;
  total_pages: number;
  total_items: number;
  has_next: boolean;
  has_previous: boolean;
}

export function Pager({ pagination, noun, onPage }: { pagination?: Pagination | null; noun: string; onPage: (page: number) => void }) {
  if (!pagination) return null;
  return (
    <footer className="nxl-pager">
      <span>
        {pagination.total_items} {noun}
        {pagination.total_pages > 1 ? ` · page ${pagination.page} of ${pagination.total_pages}` : ""}
      </span>
      {pagination.total_pages > 1 ? (
        <span className="flex gap-1.5">
          <ActionIcon icon={ChevronLeft} label="Previous page" size="sm" disabled={!pagination.has_previous} onClick={() => onPage(Math.max(1, pagination.page - 1))} />
          <ActionIcon icon={ChevronRight} label="Next page" size="sm" disabled={!pagination.has_next} onClick={() => onPage(pagination.page + 1)} />
        </span>
      ) : null}
    </footer>
  );
}

export function ListScreen<V extends string>({
  title,
  subtitle,
  primary,
  actions = [],
  search,
  chips,
  onOpenFilters,
  filtersActive = false,
  onRefresh,
  refreshing = false,
  above,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  primary?: { label: string; icon: LucideIcon; onClick: () => void } | null;
  actions?: ListAction[];
  search?: { value: string; onChange: (value: string) => void; placeholder: string; label?: string };
  chips?: { options: ChipOption<V>[]; value: V; onChange: (value: V) => void; label: string };
  onOpenFilters?: () => void;
  filtersActive?: boolean;
  onRefresh?: () => void;
  refreshing?: boolean;
  above?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
}) {
  const toolbar: ListAction[] = [
    ...actions,
    ...(onRefresh ? [{ icon: RefreshCw, label: `Refresh ${title.toLowerCase()}`, onClick: onRefresh, busy: refreshing }] : []),
  ];
  const PrimaryIcon = primary?.icon;
  return (
    <div className="nxl-screen">
      <header className="nxl-header">
        <div className="min-w-0">
          <h1>{title}</h1>
          {subtitle ? <p className="nx-muted">{subtitle}</p> : null}
        </div>
        <div className="nxl-toolbar">
          {toolbar.map((action) => <ActionIcon key={action.label} {...action} />)}
          {primary && PrimaryIcon ? (
            <button type="button" className="nx-button nxl-primary" onClick={primary.onClick}>
              <PrimaryIcon size={17} aria-hidden="true" />
              {primary.label}
            </button>
          ) : null}
        </div>
      </header>

      {above}

      <section className="nxl-panel">
        {search || onOpenFilters ? (
          <div className="nxl-filters">
            {search ? (
              <label className="nxl-search">
                <Search size={16} aria-hidden="true" />
                <input
                  type="search"
                  aria-label={search.label ?? search.placeholder}
                  placeholder={search.placeholder}
                  value={search.value}
                  onChange={(event) => search.onChange(event.target.value)}
                />
              </label>
            ) : null}
            {onOpenFilters ? (
              <button type="button" className="nxl-icon" data-active={filtersActive || undefined} aria-label="More filters" title="More filters" onClick={onOpenFilters}>
                <SlidersHorizontal size={18} strokeWidth={1.8} aria-hidden="true" />
              </button>
            ) : null}
          </div>
        ) : null}
        {chips ? (
          <div className="nx-chip-row nxl-chips" role="group" aria-label={chips.label}>
            {chips.options.map((option) => (
              <button key={option.value || "all"} type="button" className="nx-chip" aria-pressed={chips.value === option.value} onClick={() => chips.onChange(option.value)}>
                {option.label}
              </button>
            ))}
          </div>
        ) : null}
        {children}
        {footer}
      </section>

      {primary && PrimaryIcon ? (
        <div className="nxl-actionbar" role="toolbar" aria-label={`${title} actions`}>
          {toolbar.slice(0, 3).map((action) => <ActionIcon key={action.label} {...action} />)}
          <button type="button" className="nx-button nxl-actionbar-primary" onClick={primary.onClick}>
            <PrimaryIcon size={18} aria-hidden="true" />
            {primary.label}
          </button>
        </div>
      ) : null}
    </div>
  );
}

export function ListState({
  loading,
  error,
  onRetry,
  isEmpty,
  emptyIcon,
  emptyTitle,
  emptyDescription,
  emptyAction,
  children,
}: {
  loading: boolean;
  error?: unknown;
  onRetry?: () => void;
  isEmpty: boolean;
  emptyIcon: LucideIcon;
  emptyTitle: string;
  emptyDescription?: string;
  emptyAction?: ReactNode;
  children: ReactNode;
}) {
  if (error) {
    return (
      <div role="alert" className="nxl-error">
        <span>{error instanceof Error ? error.message : "Could not load this list."}</span>
        {onRetry ? <button type="button" className="nx-button nx-secondary nx-btn-sm" onClick={onRetry}>Retry</button> : null}
      </div>
    );
  }
  if (loading) {
    return (
      <div className="space-y-2 p-3" aria-busy="true" aria-label="Loading">
        {Array.from({ length: 6 }, (_, i) => <div key={i} className="nx-skeleton h-12" />)}
      </div>
    );
  }
  if (isEmpty) return <EmptyState icon={emptyIcon} title={emptyTitle} description={emptyDescription} action={emptyAction} />;
  return <>{children}</>;
}

export interface Column {
  label: string;
  align?: "end";
}

/** columns = labels for the web header: [primary, ...meta, amount]. Meta columns are hidden on phones. */
export function CompactList({ columns, children, label }: { columns: Column[]; children: ReactNode; label: string }) {
  const metaCount = Math.max(0, columns.length - 2);
  return (
    <div className="nxl-list" style={{ "--nxl-meta": metaCount } as CSSProperties}>
      <div className="nxl-row nxl-head" aria-hidden="true">
        {columns.map((column, index) => (
          <span key={column.label + index} className={index === 0 ? "" : index === columns.length - 1 ? "nxl-end" : `nxl-meta${column.align === "end" ? " nxl-end" : ""}`}>
            {column.label}
          </span>
        ))}
        <span />
      </div>
      <ul aria-label={label}>{children}</ul>
    </div>
  );
}

export function CompactRow({
  title,
  subtitle,
  meta = [],
  amount,
  amountHint,
  amountTone,
  badge,
  actions = [],
  onOpen,
  openLabel,
  expanded,
  children,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  meta?: ReactNode[];
  amount?: ReactNode;
  amountHint?: ReactNode;
  amountTone?: Tone;
  badge?: ReactNode;
  actions?: ListAction[];
  onOpen?: () => void;
  openLabel?: string;
  /** When set, the row behaves as a disclosure and shows `children` below it while expanded. */
  expanded?: boolean;
  children?: ReactNode;
}) {
  return (
    <li className="nxl-row" data-clickable={onOpen ? true : undefined} data-expanded={expanded || undefined}>
      {onOpen ? <button type="button" className="nxl-open" aria-label={openLabel ?? "Open"} aria-expanded={expanded} onClick={onOpen} /> : null}
      <div className="nxl-main">
        <strong className="nxl-title">{title}</strong>
        {subtitle ? <span className="nxl-sub">{subtitle}</span> : null}
      </div>
      {meta.map((value, index) => <span key={index} className="nxl-meta">{value}</span>)}
      <div className="nxl-end nxl-amount" data-tone={amountTone}>
        {amount !== undefined ? <strong>{amount}</strong> : null}
        {amountHint ? <span className="nxl-sub">{amountHint}</span> : null}
        {badge ? <span className="nxl-badge-slot">{badge}</span> : null}
      </div>
      <div className="nxl-actions">
        {actions.map((action) => <ActionIcon key={action.label} size="sm" {...action} />)}
      </div>
      {expanded && children ? <div className="nxl-expand">{children}</div> : null}
    </li>
  );
}

export interface StatusStyle {
  label: string;
  tone: Tone;
  icon?: LucideIcon;
}

export function StatusBadge<S extends string>({ status, map }: { status: S; map: Record<S, StatusStyle> }) {
  const style = map[status] ?? { label: String(status).replaceAll("_", " ").toLowerCase(), tone: "neutral" as Tone };
  return <Badge tone={style.tone} icon={style.icon}>{style.label}</Badge>;
}

import Link from "next/link";
import { ArrowUpRight, type LucideIcon } from "lucide-react";
import type { Tone } from "@/components/ui/badge";

export default function StatCard({ label, value, hint, icon: Icon, tone = "neutral", href, loading = false, title }: {
  label: string; value: string; hint?: string; icon: LucideIcon; tone?: Tone; href?: string; loading?: boolean; title?: string;
}) {
  const body = (
    <>
      <span className="nx-icon-chip" data-tone={tone}><Icon size={20} aria-hidden="true" /></span>
      <span className="min-w-0 flex-1">
        <span className="nx-muted block text-xs font-semibold">{label}</span>
        {loading ? (
          <span className="nx-skeleton mt-2 block h-6 w-24" aria-hidden="true" />
        ) : (
          <strong className="mt-0.5 block truncate text-xl font-bold tracking-tight tabular-nums" title={title}>{value}</strong>
        )}
        {hint && !loading ? <span className="nx-muted block truncate text-xs">{hint}</span> : null}
      </span>
      {href ? <ArrowUpRight size={16} className="nx-muted shrink-0" aria-hidden="true" /> : null}
    </>
  );
  const cls = "nx-card flex items-start gap-3 p-4";
  return href ? <Link href={href} className={`${cls} nx-card-link`}>{body}</Link> : <div className={cls}>{body}</div>;
}

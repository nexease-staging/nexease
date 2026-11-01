import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

export default function EmptyState({ icon: Icon, title, description, action }: { icon: LucideIcon; title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center px-4 py-14 text-center">
      <span className="nx-icon-chip mb-4 !h-14 !w-14 !rounded-2xl"><Icon size={26} aria-hidden="true" /></span>
      <h3 className="text-base font-bold">{title}</h3>
      {description ? <p className="nx-muted mt-1 max-w-sm text-sm">{description}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

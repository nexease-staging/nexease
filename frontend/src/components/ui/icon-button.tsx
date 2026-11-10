import type { ButtonHTMLAttributes } from 'react';
import type { LucideIcon } from 'lucide-react';
export default function IconButton({icon: Icon,label,...props}:ButtonHTMLAttributes<HTMLButtonElement>&{icon:LucideIcon;label:string}) {
 return <button {...props} type={props.type ?? 'button'} className={`nx-icon-btn ${props.className ?? ''}`} aria-label={label} title={label}><Icon size={18} strokeWidth={1.75} aria-hidden="true"/></button>;
}

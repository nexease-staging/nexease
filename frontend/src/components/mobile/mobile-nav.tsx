"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, FileText, Menu } from 'lucide-react';
import { useAuth } from '@/features/auth/auth-context';
import { hasPermission } from '@/lib/authorization/permissions';
export default function MobileNav({ onMenu }: { onMenu: () => void }) {
  const path = usePathname(); const { authentication } = useAuth();
  const invoices = hasPermission(authentication?.role.permissions ?? [], 'invoices.read');
  return <nav className="nx-bottom-nav" aria-label="Mobile navigation">
    <Link href="/dashboard" aria-current={path.startsWith('/dashboard') ? 'page' : undefined}><LayoutDashboard size={21}/><span>Home</span></Link>
    {invoices && <Link href="/invoices" aria-current={path.startsWith('/invoices') ? 'page' : undefined}><FileText size={21}/><span>Invoices</span></Link>}
    <button onClick={onMenu}><Menu size={21}/><span>All features</span></button>
  </nav>;
}

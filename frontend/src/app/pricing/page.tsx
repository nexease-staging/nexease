import SiteFooter from "@/components/site-footer";
import Link from 'next/link';
import Pricing from '@/features/saas/pricing';
import ServicePricing from '@/features/saas/service-pricing';
export default function PricingPage(){return <main className="min-h-screen bg-slate-50 text-slate-900"><nav className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-6"><Link href="/" className="flex items-center gap-2 text-2xl font-bold"><img src="/nexease-brand-icon.png" width="36" height="36" alt=""/>NexEase</Link><div className="flex gap-6"><Link href="/">Home</Link><Link href="/deadlines">Deadlines</Link><Link href="/login">Log in</Link></div></nav><ServicePricing/><Pricing/><SiteFooter/></main>}

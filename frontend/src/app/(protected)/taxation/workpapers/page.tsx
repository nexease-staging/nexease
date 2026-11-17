import Link from 'next/link';
import TaxPanel from '@/features/business/tax-panel';
export default function Workpapers(){
  return <section className="space-y-4"><header className="flex items-center justify-between gap-3"><h1 className="text-2xl font-bold">Tax workpapers</h1><Link className="nx-button nx-secondary" href="/taxation">GST review</Link></header><TaxPanel/></section>;
}

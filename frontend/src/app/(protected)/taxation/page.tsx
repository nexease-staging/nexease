import GstSourceReview from "@/features/business/gst-source-review";
import BusinessWorkspace from '@/features/business/workspace';
import Link from 'next/link';
export default function Page(){return <><header className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-2xl font-bold">GST review</h1><Link className="nx-button nx-secondary" href="/taxation/workpapers">Tax workpapers</Link></header><GstSourceReview/><BusinessWorkspace kinds={['gst_settings','gst_adjustments']} title="GST review workspace" description="Maintain registration details and reviewed tax classifications for reconciliation."/></>}

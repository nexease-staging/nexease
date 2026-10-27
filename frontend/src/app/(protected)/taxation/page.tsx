import BusinessWorkspace from '@/features/business/workspace';
import TaxPanel from '@/features/business/tax-panel';
export default function Page(){return <><TaxPanel/><BusinessWorkspace kinds={['gst_settings','gst_adjustments']} title="GST review workspace" description="Maintain registration details and reviewed tax classifications for reconciliation."/></>}

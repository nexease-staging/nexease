import {BulkAssignments} from "@/features/business/pro-panels";
import {WorkforceBalances,DailyAttendance,LabourBilling} from "@/features/business/automation-panel";
import LabourReport from "@/features/business/labour-report";
import BusinessWorkspace from "@/features/business/workspace";
export default function Page(){return <><WorkforceBalances/><DailyAttendance/><BulkAssignments/><BusinessWorkspace kinds={['sites', 'assignments', 'timesheets']} title="Labour & client sites" description="Assign workers to client sites and shifts. Overlapping assignments in the same shift are blocked." /><LabourBilling/><LabourReport /></>;}
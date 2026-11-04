import {render,screen} from '@testing-library/react';
import {describe,it,expect,vi} from 'vitest';
import PlanAccessGate from './plan-access-gate';
import DashboardOverview from '@/features/dashboard/components/dashboard-overview';
const fixture=vi.hoisted(()=>({path:'/banking',modules:{finance:false,workforce:false,taxation:false}}));
vi.mock('next/navigation',()=>({usePathname:()=>fixture.path}));
vi.mock('@tanstack/react-query',()=>({useQuery:()=>({data:{modules:fixture.modules},isLoading:false})}));
vi.mock('@/features/business/workspace',()=>({getConfig:vi.fn()}));
vi.mock('@/features/auth/auth-context',()=>({useAuth:()=>({authentication:{organization:{name:'Example Company'},user:{first_name:'Nitin'},role:{permissions:['invoices.create','invoices.read']}}})}));
describe('Plan access and dashboard trim',()=>{
 it('does not mount a forbidden Finance screen reached by direct URL',()=>{fixture.path='/banking';fixture.modules.finance=false;render(<PlanAccessGate><div>Private bank data</div></PlanAccessGate>);expect(screen.queryByText('Private bank data')).not.toBeInTheDocument();expect(screen.getByRole('link',{name:'View subscription'})).toBeVisible()});
 it('allows Finance when enabled and leaves the base inventory screen alone',()=>{fixture.path='/banking';fixture.modules.finance=true;const v=render(<PlanAccessGate><div>Private bank data</div></PlanAccessGate>);expect(screen.getByText('Private bank data')).toBeVisible();fixture.path='/inventory';fixture.modules.finance=false;v.rerender(<PlanAccessGate><div>Inventory screen</div></PlanAccessGate>);expect(screen.getByText('Inventory screen')).toBeVisible()});
 it('keeps greeting and quick actions while removing just the two requested sections',()=>{render(<DashboardOverview isLoading={false}/>);expect(screen.getByText('Welcome back, Nitin')).toBeVisible();expect(screen.getByRole('navigation',{name:'Quick actions'})).toBeVisible();expect(screen.queryByRole('region',{name:'Needs attention'})).not.toBeInTheDocument();expect(screen.queryByText('Recent activity')).not.toBeInTheDocument()});
});

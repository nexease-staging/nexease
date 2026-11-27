import {render,screen} from '@testing-library/react';
import {describe,it,expect,vi} from 'vitest';
import PlanAccessGate from './plan-access-gate';
const fixture=vi.hoisted(()=>({path:'/banking',modules:{finance:false,workforce:false,taxation:false}}));
vi.mock('next/navigation',()=>({usePathname:()=>fixture.path}));
vi.mock('@tanstack/react-query',()=>({useQuery:()=>({data:{modules:fixture.modules},isLoading:false})}));
vi.mock('@/features/business/workspace',()=>({getConfig:vi.fn()}));
vi.mock('@/features/auth/auth-context',()=>({useAuth:()=>({authentication:{organization:{name:'Example Company'},user:{first_name:'Nitin'},role:{permissions:['invoices.create','invoices.read']}}})}));
describe('Plan access',()=>{
 it('does not mount a forbidden Finance screen reached by direct URL',()=>{fixture.path='/banking';fixture.modules.finance=false;render(<PlanAccessGate><div>Private bank data</div></PlanAccessGate>);expect(screen.queryByText('Private bank data')).not.toBeInTheDocument();expect(screen.getByRole('link',{name:'View subscription'})).toBeVisible()});
 it('allows Finance when enabled and leaves the base inventory screen alone',()=>{fixture.path='/banking';fixture.modules.finance=true;const v=render(<PlanAccessGate><div>Private bank data</div></PlanAccessGate>);expect(screen.getByText('Private bank data')).toBeVisible();fixture.path='/inventory';fixture.modules.finance=false;v.rerender(<PlanAccessGate><div>Inventory screen</div></PlanAccessGate>);expect(screen.getByText('Inventory screen')).toBeVisible()});
});

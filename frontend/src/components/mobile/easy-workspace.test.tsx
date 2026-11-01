import {describe,it,expect,vi,beforeEach} from 'vitest';
import {render,screen,fireEvent} from '@testing-library/react';
import {hasPermission} from '@/lib/authorization/permissions';
import {EasyHome,EasyTools} from './easy-workspace';
vi.mock('next/navigation',()=>({usePathname:()=>'/home'}));
vi.mock('@/features/auth/auth-context',()=>({useAuth:()=>({authentication:{role:{permissions:[]}}})}));
vi.mock('@/lib/authorization/permissions',()=>({hasPermission:vi.fn((_:unknown,p?:string)=>!p||p==='invoices.read')}));
vi.mock('./mobile-connection',()=>({default:()=>null}));
vi.mock('@tanstack/react-query',()=>({useQuery:({queryKey}:{queryKey:string[]})=>queryKey[0]==='business-config'?{data:undefined}:{isSuccess:true,data:{kpis:{total_sales:'100',receivables:'20',payables:'10'},alerts:{overdue_invoices:1,overdue_bills:0,out_of_stock_items:0}}}}));
beforeEach(()=>localStorage.clear());
describe('Easy mobile workspace',()=>{
 it('keeps actions constrained by role permissions',()=>{render(<EasyHome/>);expect(screen.getByText('Bill a customer')).toBeInTheDocument();expect(screen.queryByText('Add an expense')).not.toBeInTheDocument();expect(screen.queryByText('Manage my team')).not.toBeInTheDocument()});
 it('allows period selection and hiding balances',()=>{render(<EasyHome/>);fireEvent.click(screen.getByLabelText('Today'));expect(screen.getByLabelText('Today')).toBeChecked();fireEvent.click(screen.getByLabelText('Hide amounts'));expect(screen.getAllByText('••••')).toHaveLength(3)});
 it('persists advanced-tool preference and searches permitted tools',()=>{render(<EasyTools/>);fireEvent.click(screen.getByRole('switch'));expect(localStorage.getItem('nx.advanced')).toBe('true');fireEvent.change(screen.getByLabelText('Find a feature'),{target:{value:'no-such-feature'}});expect(screen.getByRole('status')).toHaveTextContent('No matching tools')});
});

it('merges Workforce tools into one section for users with access',()=>{
 vi.mocked(hasPermission).mockImplementation(()=>true);
 render(<EasyTools/>);
 expect(screen.getAllByRole('heading',{name:'Workforce'})).toHaveLength(1);
 const links=screen.getAllByRole('link').map(link=>link.getAttribute('href'));
 expect(links.filter(href=>href==='/workforce')).toHaveLength(1);
 expect(links).toContain('/workforce/sites');
});

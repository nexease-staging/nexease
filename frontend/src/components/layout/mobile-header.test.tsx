import {render,screen,fireEvent} from '@testing-library/react';
import {describe,it,expect,vi} from 'vitest';
import AppHeader from './app-header';
import AppSidebar from './app-sidebar';
vi.mock('next/navigation',()=>({useRouter:()=>({replace:vi.fn(),refresh:vi.fn()}),usePathname:()=>'/home'}));
vi.mock('@tanstack/react-query',()=>({useQuery:()=>({data:{logo:'/brand.png',modules:{},profile:{modules:['Workforce','Sales','Inventory']}}})}));
vi.mock('@/features/business/workspace',()=>({getConfig:vi.fn()}));
vi.mock('@/features/auth/auth-context',()=>({useAuth:()=>({signOut:vi.fn(),authentication:{user:{id:'u',first_name:'Nitin',last_name:'V',email:'test@example.test'},organization:{name:'Example Company'},role:{name:'Admin',permissions:['organizations.update','invoices.read','payroll.read']}}})}));
vi.mock('@/features/notifications/components/notification-menu',()=>({default:()=> <button>Notifications</button>}));
vi.mock('@/components/mobile/device-notification-settings',()=>({default:()=>null}));
vi.mock('@/components/nex-dialog',()=>({default:({children,title}:{children:React.ReactNode;title:string})=><div role="dialog" aria-label={title}>{children}</div>}));
describe('Header and mobile drawer',()=>{
 it('shows link labels when the desktop sidebar is collapsed but mobile drawer is open',()=>{render(<AppSidebar collapsed mobileOpen onCloseMobile={vi.fn()} onToggleCollapsed={vi.fn()}/>);fireEvent.click(screen.getByRole('button',{name:/Overview/}));expect(screen.getByRole('link',{name:'Dashboard'})).toBeVisible()});
 it('opens account controls with company branding and profile',()=>{render(<AppHeader onOpenMobile={vi.fn()}/>);expect(screen.getByAltText('Example Company logo')).toBeVisible();fireEvent.click(screen.getByRole('button',{name:'Open account menu'}));expect(screen.getByRole('link',{name:/Subscription/})).toHaveAttribute('href','/subscription');expect(screen.getByRole('button',{name:'Log out'})).toBeVisible();fireEvent.click(screen.getByRole('button',{name:'My profile'}));expect(screen.getByRole('dialog',{name:'My profile'})).toHaveTextContent('test@example.test')});
 it('closes account menu on Escape',()=>{render(<AppHeader onOpenMobile={vi.fn()}/>);fireEvent.click(screen.getByRole('button',{name:'Open account menu'}));fireEvent.keyDown(document,{key:'Escape'});expect(screen.queryByRole('button',{name:'Log out'})).not.toBeInTheDocument()});
});

 it('starts expanded with closed groups and opens only one group',()=>{render(<AppSidebar collapsed={false} mobileOpen={false} onCloseMobile={vi.fn()} onToggleCollapsed={vi.fn()}/>);expect(screen.getByRole('button',{name:'Collapse sidebar'})).toBeVisible();const overview=screen.getByRole('button',{name:/Overview/}),sales=screen.getByRole('button',{name:/Sales/});expect(overview).toHaveAttribute('aria-expanded','false');expect(sales).toHaveAttribute('aria-expanded','false');fireEvent.click(overview);expect(overview).toHaveAttribute('aria-expanded','true');fireEvent.click(sales);expect(overview).toHaveAttribute('aria-expanded','false');expect(sales).toHaveAttribute('aria-expanded','true');fireEvent.click(sales);expect(sales).toHaveAttribute('aria-expanded','false')});
 it('uses NexEase branding in sidebar while retaining the organisation subtitle',()=>{render(<AppSidebar collapsed={false} mobileOpen={false} onCloseMobile={vi.fn()} onToggleCollapsed={vi.fn()}/>);expect(screen.getByAltText('NexEase logo')).toHaveAttribute('src','/nexease-brand-icon.png');expect(screen.getByText('NexEase')).toBeVisible();expect(screen.getByText('Example Company')).toBeVisible()});

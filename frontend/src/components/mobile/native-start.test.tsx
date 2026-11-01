import {render,screen,waitFor} from '@testing-library/react';
import {describe,it,expect,vi,beforeEach} from 'vitest';
import NativeStart from './native-start';
const state=vi.hoisted(()=>({native:true,status:'authenticated',replace:vi.fn()}));
vi.mock('@capacitor/core',()=>({Capacitor:{isNativePlatform:()=>state.native}}));
vi.mock('next/navigation',()=>({usePathname:()=> '/',useRouter:()=>({replace:state.replace})}));
vi.mock('@/features/auth/auth-context',()=>({useAuth:()=>({status:state.status})}));
beforeEach(()=>{vi.clearAllMocks();state.native=true;state.status='authenticated'});
describe('Native launch',()=>{
 it('restores an authenticated native user to Home',async()=>{render(<NativeStart>Landing</NativeStart>);await waitFor(()=>expect(state.replace).toHaveBeenCalledWith('/home'))});
 it('opens login for an expired native session',async()=>{state.status='unauthenticated';render(<NativeStart>Landing</NativeStart>);await waitFor(()=>expect(state.replace).toHaveBeenCalledWith('/login'))});
 it('returns signed-in web users to the dashboard',async()=>{state.native=false;render(<NativeStart>Landing</NativeStart>);await waitFor(()=>expect(state.replace).toHaveBeenCalledWith('/dashboard'))});
 it('keeps the web landing page for signed-out visitors',()=>{state.native=false;state.status='unauthenticated';render(<NativeStart>Landing</NativeStart>);expect(screen.getByText('Landing')).toBeVisible();expect(state.replace).not.toHaveBeenCalled()});
});

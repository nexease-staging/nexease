import {render, waitFor} from '@testing-library/react';
import {describe, it, expect, vi, beforeEach} from 'vitest';
import LoginForm from './login-form';
const mocks=vi.hoisted(()=>({native:false,replace:vi.fn(),refresh:vi.fn()}));
vi.mock('@capacitor/core',()=>({Capacitor:{isNativePlatform:()=>mocks.native}}));
vi.mock('next/navigation',()=>({useRouter:()=>({replace:mocks.replace,refresh:mocks.refresh}),useSearchParams:()=>new URLSearchParams()}));
vi.mock('@/features/auth/auth-context',()=>({useAuth:()=>({isAuthenticated:true,status:'authenticated',signIn:vi.fn()})}));
vi.mock('@/lib/api/client',()=>({APIRequestError:class extends Error {}}));
beforeEach(()=>vi.clearAllMocks());
describe('login destination',()=>{
 it('opens the web dashboard in a browser',async()=>{mocks.native=false;render(<LoginForm/>);await waitFor(()=>expect(mocks.replace).toHaveBeenCalledWith('/dashboard'));});
 it('keeps the native app home',async()=>{mocks.native=true;render(<LoginForm/>);await waitFor(()=>expect(mocks.replace).toHaveBeenCalledWith('/home'));});
});

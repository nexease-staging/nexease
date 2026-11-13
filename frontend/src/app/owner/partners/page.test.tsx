import {render,screen,fireEvent,within,waitFor} from '@testing-library/react';
import {beforeAll,beforeEach,it,expect,vi} from 'vitest';
import Page from './page';
import {apiRequest} from '@/lib/api/client';
vi.mock('@/lib/api/client',()=>({apiRequest:vi.fn()}));
beforeAll(()=>{HTMLDialogElement.prototype.showModal=function(){this.open=true;};});
beforeEach(()=>{vi.clearAllMocks();vi.mocked(apiRequest).mockImplementation(async()=>({data:{partners:[{id:'p1',name:'Partner',email:'p@example.com',status:'pending',email_verified:true}],total:1}} as never));});
it('shows rejected approval inside the open dialog',async()=>{
 render(<Page/>);fireEvent.click(await screen.findByRole('button',{name:'Review application'}));
 vi.mocked(apiRequest).mockRejectedValueOnce(new Error('Fresh owner password and authenticator code are required.'));
 const dialog=screen.getByRole('dialog');
 fireEvent.submit(within(dialog).getByRole('button',{name:'Save decision'}).closest('form')!);
 await waitFor(()=>expect(within(dialog).getByRole('alert')).toHaveTextContent('Fresh owner password'));
 expect(dialog).toBeVisible();
});
it('explains and blocks approval before email verification',async()=>{
 vi.mocked(apiRequest).mockResolvedValue({data:{partners:[{id:'p1',name:'Partner',email:'p@example.com',status:'pending',email_verified:false}],total:1}} as never);
 render(<Page/>);fireEvent.click(await screen.findByRole('button',{name:'Review application'}));
 expect(within(screen.getByRole('dialog')).getByRole('button',{name:'Save decision'})).toBeDisabled();
 expect(within(screen.getByRole('dialog')).getByRole('status')).toHaveTextContent('email verification');
});

import {describe,it,expect,vi,beforeEach} from 'vitest';
import {render,screen,fireEvent,waitFor} from '@testing-library/react';
import ContactNexEase from './contact-nexease';
import {apiRequest} from '@/lib/api/client';
vi.mock('@/lib/api/client',()=>({apiRequest:vi.fn()}));
const api=vi.mocked(apiRequest);
beforeEach(()=>{api.mockReset();});
describe('Quotation form',()=>{
 it('submits enquiry details and consent without a browser-controlled destination',async()=>{
  api.mockResolvedValue({data:{reference:'quote-123'}} as never);render(<ContactNexEase/>);
  fireEvent.change(screen.getByLabelText('Your name'),{target:{value:'Nitin'}});
  fireEvent.change(screen.getByLabelText('Email'),{target:{value:'nitin@example.com'}});
  fireEvent.change(screen.getByLabelText('What do you need?'),{target:{value:'Inventory for two warehouses'}});
  fireEvent.click(screen.getByRole('checkbox'));
  fireEvent.submit(screen.getByRole('button',{name:'Send enquiry'}).closest('form')!);
  await screen.findByText(/quote-123/);
  expect(api).toHaveBeenCalledWith('/public/quotation/',expect.objectContaining({method:'POST',body:expect.objectContaining({name:'Nitin',email:'nitin@example.com',consent:true})}));
  expect((api.mock.calls[0][1] as {body:Record<string,unknown>}).body).not.toHaveProperty('to');
 });
 it('keeps an unsuccessful enquiry editable and displays the error',async()=>{
  api.mockRejectedValue(new Error('Please retry shortly.'));render(<ContactNexEase/>);
  fireEvent.change(screen.getByLabelText('Your name'),{target:{value:'Nitin'}});
  fireEvent.submit(screen.getByRole('button',{name:'Send enquiry'}).closest('form')!);
  await waitFor(()=>expect(screen.getByRole('status')).toHaveTextContent('Please retry shortly.'));
  expect(screen.getByLabelText('Your name')).toHaveValue('Nitin');
 });
});

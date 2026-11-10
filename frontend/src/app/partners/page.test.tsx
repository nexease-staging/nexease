import {render,screen,fireEvent} from '@testing-library/react';
import {beforeEach,describe,expect,it,vi} from 'vitest';
import Partners from './page';
const request=vi.hoisted(()=>vi.fn());
vi.mock('@/lib/api/client',()=>({apiRequest:request}));
vi.mock('next/link',()=>({default:({children,href}:{children:React.ReactNode;href:string})=><a href={href}>{children}</a>}));
describe('Partner portal',()=>{
 beforeEach(()=>{request.mockReset();});
 it('shows registration without implying approval',async()=>{
  request.mockResolvedValue({data:{partner:null}});render(<Partners/>);
  fireEvent.click(await screen.findByRole('button',{name:'Become a partner'}));
  expect(screen.getByRole('heading',{name:'Apply to become a partner'})).toBeInTheDocument();
  expect(screen.getByLabelText('Name')).toBeInTheDocument();
 });
 it('keeps pending applicants out of statements',async()=>{
  request.mockResolvedValue({data:{partner:{name:'P',email:'p@example.com',status:'pending'}}});render(<Partners/>);
  expect(await screen.findByText('Application awaiting review')).toBeInTheDocument();
  expect(request).toHaveBeenCalledTimes(1);
  expect(screen.queryByText('Commission statement')).not.toBeInTheDocument();
 });
 it('shows GST holds without inventing earnings',async()=>{
  request.mockImplementation((path:string)=>Promise.resolve({data:path.includes('session')?{partner:{name:'P',email:'p@example.com',status:'approved',referral_code:'abc'}}:{entries:[{payment_id:'pay1',paid_at:100,percent:20,amount_paise:null,status:'tax_review_required'}],totals:{review_paise:0,held:1},total:1,referral_total:0,referrals:[]}}));
  render(<Partners/>);
  expect(await screen.findByText('Awaiting GST review')).toBeInTheDocument();
  expect(screen.getByText('Live payments only. These amounts are not a payout confirmation.')).toBeInTheDocument();
  expect((screen.getByLabelText('Your referral link') as HTMLInputElement).value).toContain('/signup?ref=abc');
 });
});

import {QueryClient,QueryClientProvider} from "@tanstack/react-query";
import {describe,it,expect,vi,beforeEach} from 'vitest';
import {render,screen,waitFor,fireEvent} from '@testing-library/react';
import Pricing from './pricing';
import Assistant from './assistant';
import Owner from '@/app/owner/page';
const {api}=vi.hoisted(()=>({api:vi.fn()}));
vi.mock('@/lib/api/client',()=>({apiRequest:api,apiBinaryRequest:vi.fn(),clearCSRFToken:vi.fn()}));
const plans=[{code:'basic',name:'NexEase',price:749,limits:{users:2,invoices:100},features:[],published:false},{code:'plus',name:'NexEase Plus',price:1499,limits:{users:5},features:['workforce'],published:false},{code:'pro',name:'NexEase Pro',price:1999,limits:{ai:300,scan_pages:100},features:['ai'],published:false}];
beforeEach(()=>vi.clearAllMocks());
describe('SaaS customer and owner screens',()=>{
 it('renders configured prices and does not claim checkout is enabled',async()=>{api.mockResolvedValue({data:{plans,payments_enabled:false,price_note:'Final price includes applicable tax.'}});render(<Pricing/>);expect(await screen.findByText('₹749')).toBeInTheDocument();expect(screen.getByText('₹1,499')).toBeInTheDocument();expect(screen.getByText('₹1,999')).toBeInTheDocument();expect(screen.getAllByText(/checkout is being prepared/)).toHaveLength(3);});
 it('does not offer entry creation to a basic member',async()=>{api.mockResolvedValue({data:{membership:{features:[],status:'active',end:'2099-01-01T00:00:00'}}});render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Assistant/></QueryClientProvider>);fireEvent.click(screen.getByLabelText('Open NexEase AI'));expect(await screen.findByText('Included with NexEase Pro')).toBeInTheDocument();expect(screen.queryByRole('button',{name:'Prepare entry'})).not.toBeInTheDocument();});
 it('requires data-processing consent and prepares without confirming',async()=>{api.mockImplementation(async(path:string,options?:{method:string})=>{if(path.includes('subscription'))return {data:{membership:{features:['ai'],status:'active',end:'2099-01-01T00:00:00',suspended:false}}};if(options?.method==='POST')return {data:{id:'p1',kind:'question',state:'review',data:{kind:'question',fields:{},items:[],questions:['Which date?'],warnings:[]},warnings:[],result:{}}};return {data:{enabled:true,history:[],usage:{requests:0,pages:0},accounts:[],employees:[]}};});render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Assistant/></QueryClientProvider>);fireEvent.click(screen.getByLabelText('Open NexEase AI'));const prompt=await screen.findByLabelText('AI instruction');fireEvent.change(prompt,{target:{value:'Record petrol'}});expect(screen.getByRole('button',{name:'Prepare entry'})).toBeDisabled();fireEvent.keyDown(prompt,{key:'Enter'});expect(api.mock.calls.some(([,o])=>o?.method==='POST')).toBe(false);fireEvent.click(screen.getByRole('checkbox'));fireEvent.keyDown(prompt,{key:'Enter',shiftKey:true});expect(api.mock.calls.some(([,o])=>o?.method==='POST')).toBe(false);fireEvent.keyDown(prompt,{key:'Enter',isComposing:true});expect(api.mock.calls.some(([,o])=>o?.method==='POST')).toBe(false);fireEvent.keyDown(prompt,{key:'Enter'});expect(await screen.findByText('Which date?')).toBeInTheDocument();expect(api.mock.calls.some(([p])=>p.includes('/confirm/'))).toBe(false);});
 it('owner sign-in asks for an authenticator code and never shows a customer report anonymously',async()=>{api.mockResolvedValue({data:{authenticated:false}});render(<Owner/>);await waitFor(()=>expect(api).toHaveBeenCalled());expect(screen.getByLabelText('Authenticator code')).toBeRequired();expect(screen.queryByText('Owner audit history')).not.toBeInTheDocument();});
});

it('shows extracted category values for review and clears them for a new request',async()=>{
 api.mockImplementation(async(path:string,options?:{method:string})=>{
  if(path.includes('subscription'))return {data:{membership:{features:['ai'],status:'active',end:'2099-01-01T00:00:00',suspended:false}}};
  if(options?.method==='POST')return {data:{id:'category-proposal',kind:'category',state:'review',data:{kind:'category',fields:{name:'Safety Equipment',description:'Helmets and gloves'},items:[],questions:[],warnings:[]},warnings:[],result:{}}};
  return {data:{enabled:true,history:[],usage:{requests:0,pages:0},accounts:[],employees:[]}};
 });
 render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Assistant/></QueryClientProvider>);
 fireEvent.click(screen.getByLabelText('Open NexEase AI'));fireEvent.change(await screen.findByLabelText('AI instruction'),{target:{value:'Create category Safety Equipment, description Helmets and gloves'}});fireEvent.click(screen.getByRole('checkbox'));fireEvent.click(screen.getByText('Prepare entry'));
 expect(await screen.findByDisplayValue('Safety Equipment')).toBeVisible();expect(screen.getByDisplayValue('Helmets and gloves')).toBeVisible();expect(api.mock.calls.some(([p])=>p.includes('/confirm/'))).toBe(false);
 fireEvent.click(screen.getByText('New request'));expect(screen.queryByDisplayValue('Safety Equipment')).not.toBeInTheDocument();
});
it('shows extracted invoice customer, PO and item amounts without retyping',async()=>{
 api.mockImplementation(async(path:string,options?:{method:string})=>{
  if(path.includes('subscription'))return {data:{membership:{features:['ai'],status:'active',end:'2099-01-01T00:00:00',suspended:false}}};
  if(options?.method==='POST')return {data:{id:'invoice-proposal',kind:'invoice',state:'review',data:{kind:'invoice',fields:{party_name:'Acme Supplies',po_number:'PO-24',date:'2026-11-02'},items:[{name:'Helmet',quantity:'3',unit_price:'500',tax_rate:'18',discount:'0'}],questions:[],warnings:[]},warnings:[],result:{}}};
  return {data:{enabled:true,history:[],usage:{requests:0,pages:0},accounts:[],employees:[]}};
 });
 render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Assistant/></QueryClientProvider>);
 fireEvent.click(screen.getByLabelText('Open NexEase AI'));fireEvent.change(await screen.findByLabelText('AI instruction'),{target:{value:'Invoice Acme Supplies PO-24 for 3 Helmets at 500 with 18% GST'}});fireEvent.click(screen.getByRole('checkbox'));fireEvent.click(screen.getByText('Prepare entry'));
 expect(await screen.findByDisplayValue('Acme Supplies')).toBeVisible();for(const value of ['PO-24','Helmet','3','500','18'])expect(screen.getByDisplayValue(value)).toBeVisible();
});

import {beforeAll,beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import InvoiceDialog from './invoice-dialog';
import {apiRequest} from '@/lib/api/client';
import {createInvoice} from '@/features/invoices/api';
vi.mock('@/features/auth/auth-context',()=>({useAuth:()=>({authentication:{role:{permissions:[]}}})}));
vi.mock('@/features/invoices/hooks',()=>({useInvoiceBankAccounts:()=>({data:{bank_accounts:[]}})}));
vi.mock('@/lib/api/client',()=>({apiRequest:vi.fn()}));
vi.mock('@/features/invoices/api',()=>({createInvoice:vi.fn()}));
vi.mock('@/features/sales-orders/hooks',()=>({useSalesOrderList:()=>({data:{sales_orders:[{id:'so1',so_number:'SO-001',customer:{name:'QA Client'}}]}})}));
vi.mock('@/components/master-lookup',()=>({default:()=>null}));
vi.mock('@/features/business/barcode-scan',()=>({default:({renderInput}:{renderInput?:(onScan:(value:string)=>void,ref:{current:HTMLInputElement|null},ready:boolean)=>import('react').ReactNode})=>renderInput?.(()=>{},{current:null},false)??null}));
vi.mock('@/features/business/gst-lookup',()=>({default:()=>null}));
beforeAll(()=>{HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','')};HTMLDialogElement.prototype.close=function(){this.removeAttribute('open')}});
beforeEach(()=>{vi.clearAllMocks();vi.mocked(apiRequest).mockImplementation(async path=>({data:path.includes('/lookup/')?{records:[]}:{id:'invoice1'}} as never));vi.mocked(createInvoice).mockResolvedValue({id:'invoice2'} as never)});
function mount(mode:'direct'|'order'='direct'){const onClose=vi.fn(),onCreated=vi.fn();render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><InvoiceDialog open initialMode={mode} onClose={onClose} onCreated={onCreated}/></QueryClientProvider>);return {onClose,onCreated}}
describe('Shared invoice creation',()=>{
 it('requires customer and items but not code/email/PO on direct invoices',()=>{mount();expect(screen.getByLabelText('Customer name *')).toBeRequired();expect(screen.getByLabelText('Customer code (automatic if blank)')).not.toBeRequired();expect(screen.getByLabelText('Email')).not.toBeRequired();expect(screen.getByLabelText('sku line 1')).not.toBeRequired();expect(screen.getByLabelText('PO number')).not.toBeRequired()});
 it('saves a minimal direct invoice and returns its ID',async()=>{const callbacks=mount();fireEvent.change(screen.getByLabelText('Customer name *'),{target:{value:'New customer'}});fireEvent.change(screen.getByLabelText('GST treatment'),{target:{value:'unregistered'}});fireEvent.change(screen.getByLabelText('name line 1'),{target:{value:'Service'}});fireEvent.change(screen.getByLabelText('unit_price line 1'),{target:{value:'100'}});fireEvent.click(screen.getByRole('button',{name:'Save draft invoice'}));await waitFor(()=>expect(callbacks.onCreated).toHaveBeenCalledWith('invoice1'));expect(apiRequest).toHaveBeenCalledWith('/business/direct-invoices/',expect.objectContaining({body:expect.objectContaining({customer:expect.objectContaining({name:'New customer'})})}))});
 it('shows the total after discounts and GST across items',()=>{
  mount();
  fireEvent.change(screen.getByLabelText('unit_price line 1'),{target:{value:'100'}});
  fireEvent.change(screen.getByLabelText('quantity line 1'),{target:{value:'2'}});
  fireEvent.change(screen.getByLabelText('discount line 1'),{target:{value:'50'}});
  fireEvent.change(screen.getByLabelText('tax_rate line 1'),{target:{value:'18'}});
  fireEvent.click(screen.getByRole('button',{name:'Add item'}));
  fireEvent.change(screen.getByLabelText('unit_price line 2'),{target:{value:'25'}});
  expect(screen.getByLabelText('Estimated total')).toHaveTextContent('₹202.00');
 });
 it('uses the same dialog for an order invoice',async()=>{const callbacks=mount('order');fireEvent.change(screen.getByLabelText('Fulfilled sales order *'),{target:{value:'so1'}});fireEvent.change(screen.getByLabelText('GST treatment'),{target:{value:'unregistered'}});fireEvent.click(screen.getByRole('button',{name:'Save draft invoice'}));await waitFor(()=>expect(callbacks.onCreated).toHaveBeenCalledWith('invoice2'));expect(createInvoice).toHaveBeenCalledWith(expect.objectContaining({sales_order_id:'so1'}));expect(apiRequest).not.toHaveBeenCalled()});
 it('switches modes without creating records and closes safely',()=>{const callbacks=mount();fireEvent.click(screen.getByRole('button',{name:'From sales order'}));expect(screen.getByLabelText('Fulfilled sales order *')).toBeRequired();fireEvent.click(screen.getByRole('button',{name:'Close invoice'}));expect(callbacks.onClose).toHaveBeenCalled();expect(apiRequest).not.toHaveBeenCalled()});
});

it('blocks two synchronous submits while the create request is pending',async()=>{
 mount('order');
 vi.mocked(createInvoice).mockReturnValue(new Promise(()=>{}));
 const form=screen.getByRole('button',{name:'Save draft invoice'}).closest('form')!;
 fireEvent.change(screen.getByLabelText('Fulfilled sales order *'),{target:{value:'so1'}});
 fireEvent.submit(form);fireEvent.submit(form);
 expect(createInvoice).toHaveBeenCalledTimes(1);
});

it('saves a percent discount as the calculated rupee line discount',async()=>{
 const callbacks=mount();
 fireEvent.change(screen.getByLabelText('Customer name *'),{target:{value:'Customer'}});
 fireEvent.change(screen.getByLabelText('GST treatment'),{target:{value:'unregistered'}});
 fireEvent.change(screen.getByLabelText('name line 1'),{target:{value:'Service'}});
 fireEvent.change(screen.getByLabelText('unit_price line 1'),{target:{value:'100'}});
 fireEvent.change(screen.getByLabelText('quantity line 1'),{target:{value:'3'}});
 fireEvent.click(screen.getByRole('button',{name:'Discount in percent'}));
 fireEvent.change(screen.getByLabelText('discount line 1'),{target:{value:'10'}});
 expect(screen.getByLabelText('Estimated total')).toHaveTextContent('₹270.00');
 fireEvent.click(screen.getByRole('button',{name:'Save draft invoice'}));
 await waitFor(()=>expect(callbacks.onCreated).toHaveBeenCalled());
 expect(apiRequest).toHaveBeenCalledWith('/business/direct-invoices/',expect.objectContaining({body:expect.objectContaining({items:[expect.objectContaining({discount:'30.00'})]})}));
});

it('opens a reviewed quotation as a direct draft and submits the quotation link',async()=>{
 const quote={number:"EST-42",date:"2026-11-17",valid_until:"",notes:"Deliver together",customer:"Quoted Buyer",
   total:"224.20",items:[{name:"Quoted item",quantity:"2",unit_price:"100",tax_rate:"18",discount:"10",total:"224.20"}]};
 render(<QueryClientProvider client={new QueryClient()}><InvoiceDialog open sourceQuote={quote} initialMode="direct" onClose={vi.fn()}/></QueryClientProvider>);
 expect(screen.getByLabelText("Customer name *")).toHaveValue("Quoted Buyer");
 expect(screen.getByLabelText("Notes")).toHaveValue("Deliver together");
 expect(screen.getByLabelText("Estimated total")).toHaveTextContent("₹224.20");
 expect(screen.queryByRole("button",{name:"Cash"})).toBeNull();
 fireEvent.change(screen.getByLabelText("GST treatment"),{target:{value:"unregistered"}});
 fireEvent.click(screen.getByRole("button",{name:"Save draft invoice"}));
 await waitFor(()=>expect(apiRequest).toHaveBeenCalledWith("/business/direct-invoices/?quotation=EST-42",expect.objectContaining({method:"POST"})));
});

describe('HSN/SAC and GST treatment',()=>{
 it('blocks a taxable invoice without HSN/SAC before calling the server',async()=>{
  mount();
  fireEvent.change(screen.getByLabelText('Customer name *'),{target:{value:'Customer'}});
  fireEvent.change(screen.getByLabelText('GST treatment'),{target:{value:'taxable'}});
  fireEvent.change(screen.getByLabelText('Place of supply *'),{target:{value:'27'}});
  fireEvent.change(screen.getByLabelText('name line 1'),{target:{value:'Cement'}});
  fireEvent.change(screen.getByLabelText('unit_price line 1'),{target:{value:'400'}});
  expect(screen.getByLabelText('hsn_code line 1').closest('label')).toHaveTextContent('HSN/SAC *');
  fireEvent.click(screen.getByRole('button',{name:'Save draft invoice'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('HSN/SAC is required');
  expect(screen.getByLabelText('hsn_code line 1')).toHaveAttribute('aria-invalid','true');
  expect(apiRequest).not.toHaveBeenCalledWith('/business/direct-invoices/',expect.anything());
 });
 it('saves an exempt sale without HSN/SAC and zeroes GST on the lines',async()=>{
  const callbacks=mount();
  fireEvent.change(screen.getByLabelText('Customer name *'),{target:{value:'Customer'}});
  fireEvent.change(screen.getByLabelText('name line 1'),{target:{value:'Loose rice'}});
  fireEvent.change(screen.getByLabelText('unit_price line 1'),{target:{value:'60'}});
  fireEvent.change(screen.getByLabelText('tax_rate line 1'),{target:{value:'5'}});
  fireEvent.change(screen.getByLabelText('GST treatment'),{target:{value:'exempt'}});
  expect(screen.getByText(/GST set to 0% on every line/)).toHaveAttribute('role','status');
  expect(screen.getByLabelText('tax_rate line 1')).toHaveValue(0);
  expect(screen.getByLabelText('hsn_code line 1').closest('label')).toHaveTextContent('HSN/SAC (optional)');
  fireEvent.change(screen.getByLabelText('Place of supply *'),{target:{value:'27'}});
  fireEvent.click(screen.getByRole('button',{name:'Save draft invoice'}));
  await waitFor(()=>expect(callbacks.onCreated).toHaveBeenCalledWith('invoice1'));
  expect(apiRequest).toHaveBeenCalledWith('/business/direct-invoices/',expect.objectContaining({body:expect.objectContaining({items:[expect.objectContaining({hsn_code:'',tax_rate:'0'})],billing_details:expect.objectContaining({supply_type:'exempt'})})}));
 });
 it('restores GST rates when switching back to taxable',()=>{
  mount();
  fireEvent.change(screen.getByLabelText('tax_rate line 1'),{target:{value:'18'}});
  fireEvent.change(screen.getByLabelText('GST treatment'),{target:{value:'nil_rated'}});
  fireEvent.change(screen.getByLabelText('GST treatment'),{target:{value:'taxable'}});
  expect(screen.getByLabelText('tax_rate line 1')).toHaveValue(18);
 });
});

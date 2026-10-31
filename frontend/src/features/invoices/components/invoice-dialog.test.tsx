import {beforeAll,beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import InvoiceDialog from './invoice-dialog';
import {apiRequest} from '@/lib/api/client';
import {createInvoice} from '@/features/invoices/api';
vi.mock('@/lib/api/client',()=>({apiRequest:vi.fn()}));
vi.mock('@/features/invoices/api',()=>({createInvoice:vi.fn()}));
vi.mock('@/features/sales-orders/hooks',()=>({useSalesOrderList:()=>({data:{sales_orders:[{id:'so1',so_number:'SO-001',customer:{name:'QA Client'}}]}})}));
vi.mock('@/components/master-lookup',()=>({default:()=>null}));
vi.mock('@/features/business/barcode-scan',()=>({default:()=>null}));
vi.mock('@/features/business/gst-lookup',()=>({default:()=>null}));
beforeAll(()=>{HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','')};HTMLDialogElement.prototype.close=function(){this.removeAttribute('open')}});
beforeEach(()=>{vi.clearAllMocks();vi.mocked(apiRequest).mockResolvedValue({data:{id:'invoice1'}} as never);vi.mocked(createInvoice).mockResolvedValue({id:'invoice2'} as never)});
function mount(mode:'direct'|'order'='direct'){const onClose=vi.fn(),onCreated=vi.fn();render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><InvoiceDialog open initialMode={mode} onClose={onClose} onCreated={onCreated}/></QueryClientProvider>);return {onClose,onCreated}}
describe('Shared invoice creation',()=>{
 it('requires customer and items but not code/email/PO on direct invoices',()=>{mount();expect(screen.getByLabelText('Customer name *')).toBeRequired();expect(screen.getByLabelText('Customer code (automatic if blank)')).not.toBeRequired();expect(screen.getByLabelText('Email')).not.toBeRequired();expect(screen.getByLabelText('sku line 1')).not.toBeRequired();expect(screen.getByLabelText('PO number')).not.toBeRequired()});
 it('saves a minimal direct invoice and returns its ID',async()=>{const callbacks=mount();fireEvent.change(screen.getByLabelText('Customer name *'),{target:{value:'New customer'}});fireEvent.change(screen.getByLabelText('GST treatment'),{target:{value:'unregistered'}});fireEvent.change(screen.getByLabelText('name line 1'),{target:{value:'Service'}});fireEvent.change(screen.getByLabelText('unit_price line 1'),{target:{value:'100'}});fireEvent.click(screen.getByRole('button',{name:'Save draft invoice'}));await waitFor(()=>expect(callbacks.onCreated).toHaveBeenCalledWith('invoice1'));expect(apiRequest).toHaveBeenCalledWith('/business/direct-invoices/',expect.objectContaining({body:expect.objectContaining({customer:expect.objectContaining({name:'New customer'})})}))});
 it('uses the same dialog for an order invoice',async()=>{const callbacks=mount('order');fireEvent.change(screen.getByLabelText('Fulfilled sales order *'),{target:{value:'so1'}});fireEvent.change(screen.getByLabelText('GST treatment'),{target:{value:'unregistered'}});fireEvent.click(screen.getByRole('button',{name:'Save draft invoice'}));await waitFor(()=>expect(callbacks.onCreated).toHaveBeenCalledWith('invoice2'));expect(createInvoice).toHaveBeenCalledWith(expect.objectContaining({sales_order_id:'so1'}));expect(apiRequest).not.toHaveBeenCalled()});
 it('switches modes without creating records and closes safely',()=>{const callbacks=mount();fireEvent.click(screen.getByRole('button',{name:'From sales order'}));expect(screen.getByLabelText('Fulfilled sales order *')).toBeRequired();fireEvent.click(screen.getByRole('button',{name:'Close invoice'}));expect(callbacks.onClose).toHaveBeenCalled();expect(apiRequest).not.toHaveBeenCalled()});
});

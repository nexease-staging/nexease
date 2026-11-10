import {render,screen,fireEvent,act,waitFor} from '@testing-library/react';
import {describe,it,expect,vi,beforeAll} from 'vitest';
import {NumberDialog} from './numbering-ui';
vi.mock('@/lib/api/client',()=>({apiRequest:vi.fn().mockResolvedValue({data:{series:[{kind:'Invoice',mode:'automatic',prefix:'INV-',next:12,padding:5}]}})}));
beforeAll(()=>{HTMLDialogElement.prototype.showModal=vi.fn(function(this:HTMLDialogElement){this.setAttribute('open','')});HTMLDialogElement.prototype.close=vi.fn(function(this:HTMLDialogElement){this.removeAttribute('open')})});
describe('Numbering choice' ,()=>{
 it('opens in the native top layer above an invoice modal',async()=>{const parent=document.createElement('dialog');document.body.appendChild(parent);parent.showModal();render(<NumberDialog/>);const resolve=vi.fn();act(()=>window.dispatchEvent(new CustomEvent('nexease-number',{detail:{kind:'Invoice',existing:'',resolve}})));await screen.findByText('Automatic · INV-00012');const modal=screen.getByRole('dialog',{name:'Document numbering'});expect(modal.tagName).toBe('DIALOG');expect(modal).toHaveAttribute('open');expect(HTMLDialogElement.prototype.showModal).toHaveBeenCalled();fireEvent(modal,new Event('cancel',{bubbles:true,cancelable:true}));expect(resolve).toHaveBeenCalledWith(null);expect(parent.open).toBe(true);parent.remove();});
 it('resolves pending creation on unmount',()=>{const view=render(<NumberDialog/>);const resolve=vi.fn();act(()=>window.dispatchEvent(new CustomEvent('nexease-number',{detail:{kind:'Invoice',existing:'',resolve}})));view.unmount();expect(resolve).toHaveBeenCalledWith(null);});
 it('shows automatic preview and returns selected mode',async()=>{render(<NumberDialog/>);const resolve=vi.fn();act(()=>window.dispatchEvent(new CustomEvent('nexease-number',{detail:{kind:'Invoice',existing:'',resolve}})));await screen.findByText('Automatic · INV-00012');fireEvent.click(screen.getByText('Save with this numbering'));expect(resolve).toHaveBeenCalledWith({kind:'Invoice',mode:'automatic',number:''});});
 it('preserves manual number and supports cancel',async()=>{render(<NumberDialog/>);const resolve=vi.fn();act(()=>window.dispatchEvent(new CustomEvent('nexease-number',{detail:{kind:'Invoice',existing:'CUSTOM-1',resolve}})));await waitFor(()=>expect(screen.getByLabelText('Manual document number')).toHaveValue('CUSTOM-1'));fireEvent.click(screen.getByText('Cancel'));expect(resolve).toHaveBeenCalledWith(null);});
});

it('uses the server financial-year preview without changing the configured prefix',async()=>{
 const {apiRequest}=await import('@/lib/api/client');
 vi.mocked(apiRequest).mockResolvedValueOnce({data:{series:[{kind:'Invoice',mode:'automatic',prefix:'INV-',next:1,padding:5,financial_year:true,preview:'INV-26-27/00001'}]}} as Awaited<ReturnType<typeof apiRequest>>);
 render(<NumberDialog/>);
 act(()=>window.dispatchEvent(new CustomEvent('nexease-number',{detail:{kind:'Invoice',existing:'',resolve:vi.fn()}})));
 expect(await screen.findByText('Automatic · INV-26-27/00001')).toBeVisible();
});

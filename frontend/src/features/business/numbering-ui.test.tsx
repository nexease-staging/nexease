import {render,screen,fireEvent,act,waitFor} from '@testing-library/react';
import {describe,it,expect,vi} from 'vitest';
import {NumberDialog} from './numbering-ui';
vi.mock('@/lib/api/client',()=>({apiRequest:vi.fn().mockResolvedValue({data:{series:[{kind:'Invoice',mode:'automatic',prefix:'INV-',next:12,padding:5}]}})}));
describe('Numbering choice',()=>{
 it('shows automatic preview and returns selected mode',async()=>{render(<NumberDialog/>);const resolve=vi.fn();act(()=>window.dispatchEvent(new CustomEvent('nexease-number',{detail:{kind:'Invoice',existing:'',resolve}})));await screen.findByText('Automatic · INV-00012');fireEvent.click(screen.getByText('Save with this numbering'));expect(resolve).toHaveBeenCalledWith({kind:'Invoice',mode:'automatic',number:''});});
 it('preserves manual number and supports cancel',async()=>{render(<NumberDialog/>);const resolve=vi.fn();act(()=>window.dispatchEvent(new CustomEvent('nexease-number',{detail:{kind:'Invoice',existing:'CUSTOM-1',resolve}})));await waitFor(()=>expect(screen.getByLabelText('Manual document number')).toHaveValue('CUSTOM-1'));fireEvent.click(screen.getByText('Cancel'));expect(resolve).toHaveBeenCalledWith(null);});
});

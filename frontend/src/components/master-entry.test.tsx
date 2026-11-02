import {useState} from 'react';
import {render,screen,fireEvent,waitFor} from '@testing-library/react';
import {beforeEach,expect,it,vi} from 'vitest';
import MasterEntry from './master-entry';
import {apiRequest} from '@/lib/api/client';
vi.mock('@/lib/api/client',()=>({apiRequest:vi.fn()}));
beforeEach(()=>{vi.clearAllMocks();vi.mocked(apiRequest).mockResolvedValue({data:{records:[{id:'c1',name:'Acme',code:'C1'}]}} as never)});
function Example({select=vi.fn(),scan=vi.fn(),scanMode=false}:{select?:Function;scan?:Function;scanMode?:boolean}){const [value,setValue]=useState('');return <MasterEntry kind="customers" label="Customer" value={value} onChange={setValue} onSelect={r=>{select(r);setValue(r.name)}} scanMode={scanMode} onScan={v=>scan(v)}/>}
it('uses one input to choose an existing record or retain a new name',async()=>{const select=vi.fn();render(<Example select={select}/>);const input=screen.getByRole('combobox');fireEvent.change(input,{target:{value:'Acm'}});fireEvent.click(await screen.findByRole('option',{name:'Acme · C1'}));expect(select).toHaveBeenCalledWith(expect.objectContaining({id:'c1'}));expect(input).toHaveValue('Acme');fireEvent.change(input,{target:{value:'New customer'}});expect(input).toHaveValue('New customer');expect(screen.getAllByRole('combobox')).toHaveLength(1)});
it('does not select a stale match on Enter while typing a new name',async()=>{const select=vi.fn();render(<Example select={select}/>);const input=screen.getByRole('combobox');fireEvent.change(input,{target:{value:'Acm'}});await screen.findByRole('option');fireEvent.change(input,{target:{value:'Different'}});fireEvent.keyDown(input,{key:'Enter'});expect(select).not.toHaveBeenCalled();expect(input).toHaveValue('Different')});
it('routes keyboard scanner input to decoding lookup without selecting a name',async()=>{const scan=vi.fn();render(<Example scan={scan} scanMode/>);const input=screen.getByRole('combobox');fireEvent.change(input,{target:{value:'000123'}});fireEvent.keyDown(input,{key:'Enter'});expect(scan).toHaveBeenCalledWith('000123');await waitFor(()=>expect(apiRequest).not.toHaveBeenCalled())});

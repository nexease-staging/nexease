import {render,screen,fireEvent,waitFor} from '@testing-library/react';
import {it,expect,vi,beforeEach} from 'vitest';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {apiRequest} from '@/lib/api/client';
import HSNSuggestions from './hsn-suggestions';
vi.mock('@/lib/api/client',()=>({apiRequest:vi.fn()}));
const data={results:[{code:'2201',description:'WATERS INCLUDING NATURAL WATERS',item_type:'goods'}],total:1,retrieved:'2026-11-08'};
beforeEach(()=>{vi.clearAllMocks();vi.mocked(apiRequest).mockResolvedValue({data} as never)});
function wrap(child:React.ReactNode){const client=new QueryClient({defaultOptions:{queries:{retry:false}}});return render(<QueryClientProvider client={client}>{child}</QueryClientProvider>)}
it('searches the product name, fills only after selection and never submits',async()=>{
 const select=vi.fn(),submit=vi.fn();wrap(<form onSubmit={submit}><HSNSuggestions name="water" itemType="goods" onSelect={select}/></form>);
 await screen.findByRole('button',{name:/2201/});expect(select).not.toHaveBeenCalled();
 expect(apiRequest).toHaveBeenCalledWith('/business/hsn-suggestions/?q=water&item_type=goods');
 fireEvent.click(screen.getByRole('button',{name:/2201/}));expect(select).toHaveBeenCalledWith('2201');expect(submit).not.toHaveBeenCalled();expect(screen.getByRole('status')).toHaveTextContent('Review');
});
it('does not query short names or invent codes for no matches',async()=>{
 vi.mocked(apiRequest).mockResolvedValue({data:{...data,results:[],total:0}} as never);
 const select=vi.fn();wrap(<HSNSuggestions name="ab" itemType="goods" onSelect={select}/>);
 expect(apiRequest).not.toHaveBeenCalled();fireEvent.change(screen.getByLabelText('Find HSN / SAC'),{target:{value:'unknown'}});
 await screen.findByText(/No matches/);expect(select).not.toHaveBeenCalled();
});
it('supports a separate search description and preserves manual code ownership',async()=>{
 const select=vi.fn();wrap(<HSNSuggestions name="brand" itemType="service" onSelect={select}/>);
 fireEvent.change(screen.getByLabelText('Find HSN / SAC'),{target:{value:'accounting'}});
 await waitFor(()=>expect(apiRequest).toHaveBeenCalledWith('/business/hsn-suggestions/?q=accounting&item_type=service'));
 expect(select).not.toHaveBeenCalled();
});
it('shows an error without blocking manual entry or saving',async()=>{
 vi.mocked(apiRequest).mockRejectedValue(new Error('Offline'));const select=vi.fn();wrap(<HSNSuggestions name="water" itemType="goods" onSelect={select}/>);
 await screen.findByRole('alert',{}, {timeout:3500});expect(select).not.toHaveBeenCalled();
});

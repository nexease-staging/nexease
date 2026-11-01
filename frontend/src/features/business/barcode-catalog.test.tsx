import {render,screen,fireEvent,waitFor} from '@testing-library/react';
import {describe,it,expect,vi,beforeEach} from 'vitest';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import BarcodeCatalog from './barcode-catalog';
import {apiRequest} from '@/lib/api/client';
import {exportWorkbook} from './workspace';
vi.mock('@/lib/api/client',()=>({apiRequest:vi.fn()}));
vi.mock('./workspace',()=>({exportWorkbook:vi.fn().mockResolvedValue(undefined)}));
vi.mock('./barcode-scan',()=>({default:()=>null}));
vi.mock('@/components/nex-feedback',()=>({confirmAction:vi.fn().mockResolvedValue(true)}));
beforeEach(()=>{vi.clearAllMocks();vi.mocked(apiRequest).mockResolvedValue({data:{results:[{id:'p1',name:'Safety Helmet',sku:'HELMET',barcode:'000123',item_type:'goods',is_active:true}],total:1,page:1,page_size:50,can_generate:false}} as never)});
function show(){render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><BarcodeCatalog/></QueryClientProvider>)}
describe('Saved barcode catalogue',()=>{
 it('lists saved products without scanning and downloads the whole catalogue',async()=>{show();await screen.findByText('Safety Helmet');expect(screen.getByText('000123')).toBeVisible();fireEvent.click(screen.getByText('Download all barcodes (Excel)'));await waitFor(()=>expect(exportWorkbook).toHaveBeenCalledWith('/business/barcode/export/','NexEase-Barcode-List.xlsx'));expect(screen.queryByText('Generate missing barcodes')).not.toBeInTheDocument()});
 it('downloads printable labels only for selected products',async()=>{show();await screen.findByText('Safety Helmet');expect(screen.getByText('Download selected labels (0)')).toBeDisabled();fireEvent.click(screen.getByLabelText('Select Safety Helmet'));fireEvent.click(screen.getByText('Download selected labels (1)'));await waitFor(()=>expect(exportWorkbook).toHaveBeenCalledWith('/business/barcode/labels/?ids=p1','NexEase-Barcodes.pdf'))});
});

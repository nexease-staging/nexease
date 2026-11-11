import {render,screen,fireEvent,act} from '@testing-library/react';
import {it,expect,vi} from 'vitest';
import BusinessWorkspace from './workspace';
import {apiRequest} from '@/lib/api/client';
vi.mock('@/lib/api/client',()=>({apiRequest:vi.fn(),apiBinaryRequest:vi.fn()}));
vi.mock('@/lib/browser/download',()=>({downloadBlob:vi.fn()}));
vi.mock('./gst-lookup',()=>({default:()=>null}));
vi.mock('@/components/search-select',()=>({default:()=>null}));
vi.mock('@/components/nex-dialog',()=>({default:({children}:{children:React.ReactNode})=><div role="dialog">{children}</div>}));
vi.mock('@tanstack/react-query',()=>({
 useQueryClient:()=>({invalidateQueries:()=>Promise.resolve()}),
 useQuery:({queryKey}:{queryKey:string[]})=>queryKey[0]==='business-config'
  ?{data:{schemas:{sites:{label:'Sites',permission:'labour',fields:{name:{label:'Name',type:'text',required:true}}}}}}
  :{data:{records:[],total:0}}
}));
it('submits a shared register only once while the first request is pending',async()=>{
 let finish!:(value:unknown)=>void;
 vi.mocked(apiRequest).mockImplementation(()=>new Promise(resolve=>{finish=resolve;}) as never);
 render(<BusinessWorkspace kinds={['sites']} title="Sites" description="Client sites"/>);
 fireEvent.click(screen.getByRole('button',{name:'Add record'}));
 fireEvent.change(screen.getByLabelText('Name *'),{target:{value:'Pune site'}});
 const save=screen.getByRole('button',{name:'Save record'});
 const form=save.closest('form')!;
 fireEvent.submit(form);fireEvent.submit(form);
 expect(apiRequest).toHaveBeenCalledTimes(1);
 expect(screen.getByRole('button',{name:'Cancel'})).toBeDisabled();
 await act(async()=>{finish({data:{}});});
 expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});

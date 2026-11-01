import {beforeEach,describe,expect,it,vi} from 'vitest';
import {Capacitor,CapacitorHttp} from '@capacitor/core';
import {apiFetch} from './transport';
vi.mock('@capacitor/core',()=>({Capacitor:{isNativePlatform:vi.fn(()=>true)},CapacitorHttp:{request:vi.fn()}}));
beforeEach(()=>{vi.clearAllMocks();vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true);vi.mocked(CapacitorHttp.request).mockResolvedValue({status:200,headers:{'Content-Type':'application/json'},data:{success:true},url:'https://example.test/api/v1/'});});
describe('Native API transport',()=>{
 it('sends origin, referer and CSRF directly without constructing a browser Request',async()=>{
  const spy=vi.spyOn(globalThis,'fetch');await apiFetch('https://example.test/api/v1/auth/login/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':'test-token','X-NexEase-Numbering':'test-number'},body:JSON.stringify({email:'demo@example.test',password:'test-only'})});
  expect(spy).not.toHaveBeenCalled();spy.mockRestore();
  expect(CapacitorHttp.request).toHaveBeenCalledWith(expect.objectContaining({method:'POST',headers:expect.objectContaining({origin:'https://localhost',referer:'https://localhost/','x-csrftoken':'test-token','x-nexease-numbering':'test-number'}),data:{email:'demo@example.test',password:'test-only'},disableRedirects:true}));
 });
 it('uses the same native transport for CSRF bootstrap',async()=>{await apiFetch('https://example.test/api/v1/auth/csrf/');expect(CapacitorHttp.request).toHaveBeenCalledWith(expect.objectContaining({method:'GET',headers:expect.objectContaining({origin:'https://localhost'})}));});
 it('preserves JSON errors for the CSRF retry handler',async()=>{vi.mocked(CapacitorHttp.request).mockResolvedValue({status:403,headers:{'Content-Type':'application/json'},data:{success:false,error:{code:'CSRF_FAILED'}},url:''});const r=await apiFetch('https://example.test/');expect(r.status).toBe(403);expect(await r.json()).toEqual({success:false,error:{code:'CSRF_FAILED'}});});
 it('converts uploaded file and text fields for the native bridge',async()=>{const f=new FormData();f.append('message','Review');f.append('file',new File(['abc'],'bill.txt',{type:'text/plain'}));await apiFetch('https://example.test/',{method:'POST',body:f,headers:{'X-CSRFToken':'token'}});expect(CapacitorHttp.request).toHaveBeenCalledWith(expect.objectContaining({dataType:'formData',data:[{key:'message',value:'Review',type:'string'},{key:'file',value:'YWJj',type:'base64File',contentType:'text/plain',fileName:'bill.txt'}]}));});
 it('decodes binary exports',async()=>{vi.mocked(CapacitorHttp.request).mockResolvedValue({status:200,headers:{'Content-Type':'application/pdf'},data:btoa('%PDF-test'),url:''});const r=await apiFetch('https://example.test/',{},true);expect(await r.text()).toBe('%PDF-test');});
 it('handles empty responses',async()=>{vi.mocked(CapacitorHttp.request).mockResolvedValue({status:204,headers:{},data:'',url:''});expect((await apiFetch('https://example.test/')).status).toBe(204);});
 it('retains ordinary browser fetch on the web',async()=>{vi.mocked(Capacitor.isNativePlatform).mockReturnValue(false);const response=new Response('{}');const spy=vi.spyOn(globalThis,'fetch').mockResolvedValue(response);expect(await apiFetch('https://example.test/',{credentials:'include'})).toBe(response);expect(CapacitorHttp.request).not.toHaveBeenCalled();spy.mockRestore();});
 it('rejects insecure native endpoints',async()=>{await expect(apiFetch('http://example.test/')).rejects.toThrow('HTTPS');expect(CapacitorHttp.request).not.toHaveBeenCalled();});
});

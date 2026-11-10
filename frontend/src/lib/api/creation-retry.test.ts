import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {webcrypto} from 'node:crypto';
import {apiFetch} from './transport';
import {apiRequest,clearCSRFToken} from './client';
import {creationRetryKey} from './creation-retry';
vi.mock('./transport',()=>({apiFetch:vi.fn()}));
vi.mock('@/components/nex-feedback',()=>({notify:vi.fn()}));
vi.mock('@/lib/mobile-config',()=>({savedServer:()=>''}));
const reply=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json'}});
beforeEach(()=>{vi.clearAllMocks();clearCSRFToken();localStorage.clear();vi.stubGlobal('crypto',webcrypto);delete document.documentElement.dataset.numberDialog;});
afterEach(()=>{vi.unstubAllGlobals();vi.restoreAllMocks();localStorage.clear();});
describe('invoice creation retry transport',()=>{
 it('retains the same request key after a lost response and clears it on success',async()=>{
  const keys:string[]=[];let lose=true;
  vi.mocked(apiFetch).mockImplementation(async(url,options)=>{
   if(String(url).includes('/csrf/'))return reply({success:true,data:{csrf:{token:'test'}}});
   keys.push(new Headers(options?.headers).get('X-NexEase-Request-Key')!);
   if(lose){lose=false;throw new Error('Lost response');}
   return reply({success:true,data:{id:'invoice1'}});
  });
  const options={method:'POST',body:{customer:{name:'Private customer'},items:[]}};
  await expect(apiRequest('/business/direct-invoices/',options)).rejects.toThrow('Lost response');
  expect(JSON.stringify(localStorage)).not.toContain('Private customer');
  await apiRequest('/business/direct-invoices/',options);
  expect(keys[0]).toBeTruthy();expect(keys[1]).toBe(keys[0]);
  expect(localStorage.length).toBe(0);
 });
 it('keeps its identity through a CSRF refresh',async()=>{
  const keys:string[]=[];
  vi.mocked(apiFetch).mockImplementation(async(url,options)=>{
   if(String(url).includes('/csrf/'))return reply({success:true,data:{csrf:{token:'test'}}});
   keys.push(new Headers(options?.headers).get('X-NexEase-Request-Key')!);
   return keys.length===1?reply({success:false,error:{code:'CSRF_FAILED',message:'Refresh'}},403):reply({success:true,data:{invoice:{id:'invoice1'}}},201);
  });
  await apiRequest('/invoices/',{method:'POST',body:{sales_order_id:'so1'}});
  expect(keys).toHaveLength(2);expect(keys[1]).toBe(keys[0]);expect(localStorage.length).toBe(0);
 });
 it('does not send if durable retry storage is unavailable',async()=>{
  vi.spyOn(Storage.prototype,'setItem').mockImplementation(()=>{throw new Error('Storage unavailable');});
  await expect(apiRequest('/invoices/',{method:'POST',body:{}})).rejects.toThrow('Storage unavailable');
  expect(apiFetch).not.toHaveBeenCalled();
 });
 it('separates changed input and numbering preferences',async()=>{
  const first=await creationRetryKey('/invoices/',{amount:'1'},null);
  expect((await creationRetryKey('/invoices/',{amount:'1'},null)).key).toBe(first.key);
  expect((await creationRetryKey('/invoices/',{amount:'2'},null)).key).not.toBe(first.key);
  expect((await creationRetryKey('/invoices/',{amount:'1'},'{"mode":"manual"}')).key).not.toBe(first.key);
 });
});

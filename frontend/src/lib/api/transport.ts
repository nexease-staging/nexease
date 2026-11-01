import { Capacitor, CapacitorHttp, type HttpOptions } from '@capacitor/core';

/** Use the native bridge directly: browser Request construction strips Origin/Referer. */
export async function apiFetch(url: string, options: RequestInit = {}, binary = false): Promise<Response> {
  if (!Capacitor.isNativePlatform()) return fetch(url, options);
  if (new URL(url).protocol !== 'https:') throw new Error('A secure HTTPS backend is required.');
  if (options.signal?.aborted) throw new DOMException('Request cancelled', 'AbortError');
  const headers = new Headers(options.headers);
  headers.set('Origin', 'https://localhost');
  headers.set('Referer', 'https://localhost/');
  let data: HttpOptions['data'];
  let dataType: HttpOptions['dataType'];
  if (options.body instanceof FormData) {
    const entries: {key:string; value:string; type:string; contentType?:string; fileName?:string}[] = [];
    for (const [key, value] of options.body.entries()) {
      if (typeof value === 'string') entries.push({key, value, type:'string'});
      else {
        const encoded = await new Promise<string>((resolve,reject)=>{
          const reader=new FileReader();
          reader.onload=()=>resolve(String(reader.result).split(',')[1]);
          reader.onerror=()=>reject(new Error('Unable to read upload.'));
          reader.readAsDataURL(value);
        });
        entries.push({key,value:encoded,type:'base64File',contentType:value.type||'application/octet-stream',fileName:value.name});
      }
    }
    data=entries; dataType='formData'; headers.set('Content-Type','multipart/form-data');
  } else if (typeof options.body === 'string') {
    data=headers.get('content-type')?.includes('application/json') ? JSON.parse(options.body) : options.body;
  } else if (options.body != null) {
    throw new Error('Unsupported request body. Use JSON or a file upload form.');
  }
  const result=await CapacitorHttp.request({
    url, method:options.method||'GET', headers:Object.fromEntries(headers.entries()),
    data, dataType, responseType:binary?'arraybuffer':'text',
    connectTimeout:60000, readTimeout:120000, disableRedirects:true,
  });
  const responseHeaders=new Headers(result.headers);
  const json=responseHeaders.get('content-type')?.includes('application/json');
  let body:BodyInit|null;
  if ([204,205,304].includes(result.status)||options.method==='HEAD') body=null;
  else if (json) body=typeof result.data==='string'?result.data:JSON.stringify(result.data);
  else if (binary) body=Uint8Array.from(atob(String(result.data)),c=>c.charCodeAt(0)).buffer;
  else body=typeof result.data==='string'?result.data:JSON.stringify(result.data);
  return new Response(body,{status:result.status,headers:responseHeaders});
}

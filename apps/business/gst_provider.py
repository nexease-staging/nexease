"""Sandbox public GSTIN adapter; credentials never leave the backend."""
import json,os,time,hashlib
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError
from django.core.cache import cache

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def request_json(url,headers,body):
    req=Request(url,data=json.dumps(body).encode(),headers={'Accept':'application/json','Content-Type':'application/json',**headers},method='POST')
    with build_opener(NoRedirect()).open(req,timeout=12) as response:raw=response.read(262145)
    if len(raw)>262144:raise ValueError('GST provider response exceeded the limit.')
    result=json.loads(raw)
    if not isinstance(result,dict):raise ValueError('Invalid GST provider response.')
    return result

def sandbox_lookup(gstin):
    key=os.getenv('GST_SANDBOX_API_KEY','').strip();secret=os.getenv('GST_SANDBOX_API_SECRET','').strip()
    if not key or not secret:raise ValueError('GST lookup is not configured. Ask the owner to add Sandbox API credentials.')
    environment=os.getenv('GST_SANDBOX_ENV','test')
    if environment not in ('test','live'):raise ValueError('GST_SANDBOX_ENV must be test or live.')
    base='https://api.sandbox.co.in' if environment=='live' else 'https://test-api.sandbox.co.in'
    headers={'x-api-key':key}
    version=os.getenv('GST_SANDBOX_API_VERSION','').strip()
    if version:headers['x-api-version']=version
    token_key='gst-sandbox-token:'+hashlib.sha256((environment+key+secret).encode()).hexdigest()
    def authenticate():
        result=request_json(base+'/authenticate',{**headers,'x-api-secret':secret},{})
        token=result.get('data',{}).get('access_token')
        if not isinstance(token,str) or not token:raise ValueError('GST provider authentication failed. Check credentials and environment.')
        cache.set(token_key,token,23*3600);return token
    token=cache.get(token_key) or authenticate()
    try:result=request_json(base+'/gst/compliance/public/gstin/search',{**headers,'authorization':token,'x-accept-cache':'true'},{'gstin':gstin})
    except HTTPError as e:
        if e.code!=401:raise
        cache.delete(token_key);token=authenticate()
        result=request_json(base+'/gst/compliance/public/gstin/search',{**headers,'authorization':token,'x-accept-cache':'true'},{'gstin':gstin})
    return normalize_taxpayer(result,gstin)

def normalize_taxpayer(result,gstin):
    data=result
    for _ in range(5):
        if data.get('gstin'):break
        child=next((data[k] for k in ('data','taxpayerInfo','result') if isinstance(data.get(k),dict)),None)
        if child is None:break
        data=child
    if str(data.get('gstin','')).upper()!=gstin:raise ValueError('GST provider did not return the requested taxpayer.')
    legal=str(data.get('lgnm') or '').strip();trade=str(data.get('tradeNam') or '').strip()
    if not legal and not trade:raise ValueError('GST provider returned no business name.')
    principal=data.get('pradr') or {};principal=principal if isinstance(principal,dict) else {}
    addr=principal.get('addr') or {};addr=addr if isinstance(addr,dict) else {}
    address=', '.join(str(addr[k]).strip() for k in ('bno','flno','bnm','st','loc','dst','stcd','pncd') if addr.get(k))
    return {'gstin':gstin,'name':(trade or legal)[:200],'legal_name':legal[:200],'trade_name':trade[:200],'address':address[:500],'state':gstin[:2],'state_name':str(addr.get('stcd') or '')[:100],'pincode':str(addr.get('pncd') or '')[:20],'city':str(addr.get('dst') or addr.get('loc') or '')[:100],'status':str(data.get('sts') or '')[:80],'registration_type':str(data.get('dty') or '')[:80],'email':'','phone':'','source':'Sandbox GST taxpayer lookup ('+os.getenv('GST_SANDBOX_ENV','test')+') - verify before saving'}

"""Sandbox public GSTIN lookup with safe, actionable failure diagnostics."""
import hashlib,json,logging,os,re,ssl
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError,URLError
from django.core.cache import cache
log=logging.getLogger(__name__)

class GSTLookupError(ValueError):
    def __init__(self,code,message,*,stage='configuration',status=None,reference=''):
        self.code=code;self.stage=stage;self.status=status
        self.reference=reference if re.fullmatch(r'[a-fA-F0-9-]{8,64}',str(reference)) else ''
        super().__init__(message)
    def public_message(self):
        return f'{self.code}: {self}'+(f' Reference: {self.reference}.' if self.reference else '')+' No records were changed.'

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def _reference(result):return result.get('transaction_id','') if isinstance(result,dict) else ''

def _http_error(status,stage,result=None):
    suffix=' at authentication' if stage=='authentication' else ' during taxpayer search'
    messages={401:('GST_AUTH_REJECTED','Sandbox rejected authentication (HTTP 401). Check that API Key and API Secret are a matching active pair for the selected Test/Live environment.'),403:('GST_ACCESS_DENIED','Sandbox denied access (HTTP 403)'+suffix+'. Check GST Public Search API access, key permissions, account restrictions and matching Test/Live environment in Sandbox Console.'),402:('GST_PROVIDER_BILLING','Sandbox requires billing or credits (HTTP 402). Check the provider account balance and product subscription.'),404:('GST_ENDPOINT_NOT_FOUND','Sandbox endpoint was not found (HTTP 404)'+suffix+'. Verify your API product and current provider documentation.'),422:('GST_REQUEST_REJECTED','Sandbox rejected request validation (HTTP 422)'+suffix+'. Check GSTIN, provider API version and supported test case.'),429:('GST_PROVIDER_LIMIT','Sandbox rate or usage limit reached (HTTP 429). Wait before retrying and check provider limits.')}
    code,message=messages.get(status,('GST_PROVIDER_UNAVAILABLE' if status>=500 else 'GST_PROVIDER_REJECTED',f'Sandbox returned HTTP {status}'+suffix+'. '+('Retry later or check provider service status.' if status>=500 else 'Check the provider transaction in Sandbox Console.')))
    return GSTLookupError(code,message,stage=stage,status=status,reference=_reference(result))

def _envelope(result,stage):
    code=result.get('code')
    if code is not None and str(code) not in ('200','201'):
        if str(code).isdigit() and 400<=int(code)<=599:raise _http_error(int(code),stage,result)
        raise GSTLookupError('GST_PROVIDER_REJECTED','Sandbox returned a business error. Check the provider transaction in Sandbox Console.',stage=stage,reference=_reference(result))
    data=result.get('data')
    if stage=='taxpayer search' and isinstance(data,dict) and str(data.get('status_cd','1')) not in ('1',''):
        err=data.get('error') or {};err=err if isinstance(err,dict) else {}
        if err.get('error_cd')=='FO8000':
            raise GSTLookupError('GST_NOT_FOUND','Sandbox returned no taxpayer record. Check the GSTIN; in Test mode use a supported provider test case.',stage=stage,reference=_reference(result))
        raise GSTLookupError('GST_TAXPAYER_REJECTED','GST taxpayer search returned a GSTN business error. Check the transaction in Sandbox Console; Test mode supports provider test cases, not arbitrary live GSTINs.',stage=stage,reference=_reference(result))

def request_json(url,headers,body):
    stage='authentication' if url.endswith('/authenticate') else 'taxpayer search'
    encoded=None if body is None else json.dumps(body).encode()
    req=Request(url,data=encoded,headers={'Accept':'application/json',**({'Content-Type':'application/json'} if encoded is not None else {}),**headers},method='POST')
    try:
        with build_opener(NoRedirect()).open(req,timeout=20) as response:raw=response.read(262145)
    except HTTPError as exc:
        # Never echo provider payloads: they can contain credentials or taxpayer data.
        try:result=json.loads(exc.read(65536))
        except (ValueError,OSError):result={}
        raise _http_error(exc.code,stage,result) from None
    except URLError as exc:
        if isinstance(exc.reason,ssl.SSLError):raise GSTLookupError('GST_TLS_ERROR','TLS certificate verification failed while reaching Sandbox. Check the backend certificate environment; do not disable certificate verification.',stage=stage) from None
        raise GSTLookupError('GST_NETWORK_ERROR','The backend could not reach Sandbox. Check backend DNS/network access and retry.',stage=stage) from None
    except (TimeoutError,OSError):raise GSTLookupError('GST_TIMEOUT','Sandbox could not be reached within the request timeout. Retry later.',stage=stage) from None
    if len(raw)>262144:raise GSTLookupError('GST_RESPONSE_INVALID','Sandbox response exceeded the size limit.',stage=stage)
    try:result=json.loads(raw)
    except (ValueError,UnicodeError):raise GSTLookupError('GST_RESPONSE_INVALID','Sandbox returned a non-JSON response. Check service availability and provider API access.',stage=stage) from None
    if not isinstance(result,dict):raise GSTLookupError('GST_RESPONSE_INVALID','Sandbox returned an unexpected response format.',stage=stage)
    _envelope(result,stage)
    return result

def configuration():
    key=os.getenv('GST_SANDBOX_API_KEY','').strip();secret=os.getenv('GST_SANDBOX_API_SECRET','').strip()
    if not key or not secret:raise GSTLookupError('GST_CONFIG_MISSING','Set GST_SANDBOX_API_KEY and GST_SANDBOX_API_SECRET in the backend environment and redeploy.')
    environment=os.getenv('GST_SANDBOX_ENV','test').strip().lower()
    if environment not in ('test','live'):raise GSTLookupError('GST_ENV_INVALID','GST_SANDBOX_ENV must be test or live, matching the credentials.')
    for label,value in [('API Key',key),('API Secret',secret)]:
        if '\n' in value or '\r' in value or value[:1] in ('"',"'"):raise GSTLookupError('GST_CONFIG_INVALID',label+' contains quotes or line breaks. Paste the plain value in the backend environment.')
        hint=next((mode for mode in ('test','live') if re.match(r'^(key|secret)_'+mode+r'',value)),None)
        if hint and hint!=environment:raise GSTLookupError('GST_ENV_MISMATCH',f'{label} appears to be {hint.upper()}, but GST_SANDBOX_ENV is {environment}. Use a matching pair and matching environment; do not share the values.')
    return key,secret,environment

def sandbox_lookup(gstin):
    key,secret,environment=configuration()
    base='https://api.sandbox.co.in' if environment=='live' else 'https://test-api.sandbox.co.in'
    headers={'x-api-key':key};version=os.getenv('GST_SANDBOX_API_VERSION','').strip()
    if version:headers['x-api-version']=version
    token_key='gst-sandbox-v2:'+hashlib.sha256((environment+key+secret+version).encode()).hexdigest()
    def authenticate():
        result=request_json(base+'/authenticate',{**headers,'x-api-secret':secret},None)
        _envelope(result,'authentication');data=result.get('data');token=data.get('access_token') if isinstance(data,dict) else None
        if not isinstance(token,str) or not token.strip() or '\n' in token or '\r' in token:raise GSTLookupError('GST_AUTH_RESPONSE_INVALID','Sandbox authentication returned no usable access_token. Check the provider transaction and API access.',stage='authentication',reference=_reference(result))
        cache.set(token_key,token,23*3600);return token
    def search(token):return request_json(base+'/gst/compliance/public/gstin/search',{**headers,'x-api-version':version or '1.0.0','authorization':token,'x-accept-cache':'true'},{'gstin':gstin})
    token=cache.get(token_key) or authenticate()
    try:result=search(token)
    except GSTLookupError as exc:
        if exc.status!=401:raise
        cache.delete(token_key);result=search(authenticate())
    _envelope(result,'taxpayer search')
    return normalize_taxpayer(result,gstin)

def normalize_taxpayer(result,gstin):
    _envelope(result,'taxpayer search');data=result
    for _ in range(5):
        if data.get('gstin'):break
        child=next((data[k] for k in ('data','taxpayerInfo','result') if isinstance(data.get(k),dict)),None)
        if child is None:break
        data=child
    returned=str(data.get('gstin','')).strip().upper()
    if not returned:raise GSTLookupError('GST_TAXPAYER_DATA_MISSING','Sandbox returned no usable taxpayer details. Check the provider transaction. In Test mode use a supported provider test GSTIN.',stage='taxpayer search',reference=_reference(result))
    if returned!=gstin:raise GSTLookupError('GST_GSTIN_MISMATCH','The provider returned a different GSTIN. Details were not applied. Test responses may be fixed fixtures; do not use them for live customer records.',stage='taxpayer search',reference=_reference(result))
    legal=str(data.get('lgnm') or '').strip();trade=str(data.get('tradeNam') or '').strip()
    if not legal and not trade:raise GSTLookupError('GST_TAXPAYER_DATA_MISSING','The provider returned no business name. Review the provider transaction.',stage='taxpayer search',reference=_reference(result))
    principal=data.get('pradr') or {};principal=principal if isinstance(principal,dict) else {}
    addr=principal.get('addr') or {};addr=addr if isinstance(addr,dict) else {}
    address=', '.join(str(addr[k]).strip() for k in ('bno','flno','bnm','st','loc','dst','stcd','pncd') if addr.get(k))
    return {'gstin':gstin,'name':(trade or legal)[:200],'legal_name':legal[:200],'trade_name':trade[:200],'address':address[:500],'state':gstin[:2],'state_name':str(addr.get('stcd') or '')[:100],'pincode':str(addr.get('pncd') or '')[:20],'city':str(addr.get('dst') or addr.get('loc') or '')[:100],'status':str(data.get('sts') or '')[:80],'registration_type':str(data.get('dty') or '')[:80],'email':'','phone':'','source':'Sandbox GST taxpayer lookup ('+os.getenv('GST_SANDBOX_ENV','test').strip().lower()+') - verify before saving'}

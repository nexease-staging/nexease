"""GST lookup via tenant masters or an explicitly configured provider adapter."""
import os,re,json
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.parse import urlparse, urlencode
from urllib.error import URLError, HTTPError
from django.views.decorators.http import require_http_methods
from apps.core.api.decorators import api_login_required,api_rate_limit
from apps.core.services.api_response_service import APIResponseService as R
from .views import permitted
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

@api_login_required
@api_rate_limit(scope='gst.lookup',limit=30,window_seconds=60)
@require_http_methods(['GET'])
def lookup(request):
    if not any(permitted(request,p) for p in ['customers.create','customers.read','invoices.create','sales_orders.create']):return R.forbidden(message='Customer or sales access required.',request=request)
    gstin=request.GET.get('gstin','').strip().upper()
    if not re.fullmatch(r'\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]',gstin):return R.validation_error(message='Enter a valid 15-character GSTIN.',request=request)
    from apps.sales.models import Customer
    c=Customer.objects(organization=request.api_organization,gstin=gstin,is_active=True).first()
    if c:return R.success(data={'id':str(c.id),'code':c.code,'name':c.name,'address':c.billing_address or '', 'state':c.state or '', 'gstin':gstin,'email':c.email or '', 'phone':c.phone or '', 'source':'Existing organisation customer'},request=request)
    url=os.getenv('GST_LOOKUP_URL','');token=os.getenv('GST_LOOKUP_TOKEN','')
    if not url or not token:return R.validation_error(message='No existing customer matches. External GST lookup is not configured. Enter details manually or ask the owner to configure a GST provider adapter.',request=request)
    parsed=urlparse(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:return R.validation_error(message='GST provider configuration is invalid.',request=request)
    try:
        req=Request(url+('&' if '?' in url else '?')+urlencode({'gstin':gstin}),headers={'Authorization':'Bearer '+token,'Accept':'application/json'})
        with build_opener(NoRedirect()).open(req,timeout=12) as response:
            raw=response.read(65537)
        if len(raw)>65536:raise ValueError()
        data=json.loads(raw)
        if not isinstance(data,dict) or data.get('gstin')!=gstin or not isinstance(data.get('name'),str) or not data['name'].strip():raise ValueError()
        clean={k:str(data.get(k) or '')[:limit] for k,limit in [('name',200),('address',500),('state',100),('gstin',15),('email',254),('phone',30)]}
        clean['source']='Configured GST provider — review before saving'
        return R.success(data=clean,request=request)
    except (URLError,HTTPError,ValueError,TimeoutError,OSError):return R.validation_error(message='GST lookup is unavailable or returned invalid data. Retry later or enter the details manually.',request=request)

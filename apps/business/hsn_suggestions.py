"""Read-only search of a bundled official GSTN directory; never changes taxes or records."""
import json
import re
from functools import lru_cache
from pathlib import Path
from django.views.decorators.http import require_GET
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from .views import permitted


def words(value):
    return ' '.join(re.findall(r'[a-z0-9]+',value.casefold()))


@lru_cache(maxsize=1)
def directory():
    data=json.loads((Path(__file__).resolve().parents[1]/'products/data/hsn-sac.json').read_text(encoding='utf-8'))
    return data,tuple((c,d,k,words(d)) for c,d,k in data['rows'])


# Search vocabulary only: the user must choose the tariff description that applies.
ALIASES={'mobile phone':'smartphone','mobile phones':'smartphone','iphone':'smartphone',
         'laptop':'portable automatic data processing','shoes':'footwear',
         'bisleri':'water','bookkeeping':'accounting'}


@lru_cache(maxsize=128)
def search(query,kind):
    data,rows=directory()
    tokens=query.split()
    numeric=query.isdigit()
    def find(terms):
        return [(code,description,typ,text) for code,description,typ,text in rows if typ==kind and
                (code.startswith(query) if numeric else all(t in text for t in terms))]
    found=find(tokens)
    expanded=''
    if not found and query in ALIASES:
        expanded=ALIASES[query];found=find(expanded.split())
    found.sort(key=lambda r:(0 if r[0]==query or r[3]==query else 1,len(r[0]),len(r[3]),r[0]))
    return {'results':[{'code':c,'description':d,'item_type':t} for c,d,t,_ in found[:12]],
            'total':len(found),'expanded_query':expanded,'source':data['source'],
            'retrieved':data['retrieved']}


@api_login_required
@require_GET
def suggestions(request):
    if not any(permitted(request,p) for p in ('products.read','products.create','products.update')):
        return R.forbidden(message='Product access required.',request=request)
    query=request.GET.get('q','').strip()
    kind=request.GET.get('item_type','goods')
    if len(query)>100 or kind not in ('goods','service'):
        return R.validation_error(message='Use at most 100 characters and choose Goods or Service.',request=request)
    query=words(query)
    if len(query)<3:
        return R.success(data={'results':[],'total':0},request=request)
    return R.success(data=search(query,kind),request=request)

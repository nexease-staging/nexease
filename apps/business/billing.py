"""Invoice snapshots and reviewed outward-tax classification. No automatic filing."""
import re, base64
from io import BytesIO
from datetime import date
from decimal import Decimal
from django.views.decorators.http import require_http_methods
from mongoengine.errors import ValidationError
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from .models import BusinessRecord as Record
from .views import permitted, payload, audit
from .automation import write_lock
from .payroll import money

TEMPLATES = [
    ('classic','Classic ledger','#243447','grid'), ('modern','Modern blue','#2563eb','stripe'),
    ('minimal','Minimal ink','#334155','minimal'), ('executive','Executive navy','#172554','banner'),
    ('emerald','Emerald studio','#047857','stripe'), ('service','Service statement','#6d28d9','service'),
    ('contractor','Contractor works','#b45309','grid'), ('compact','Compact register','#475569','compact'),
    ('elegant','Elegant violet','#7c3aed','minimal'), ('bold','Bold graphite','#18181b','banner'),
]
TEXT_FIELDS={'po_number':100,'po_date':10,'service_from':10,'service_to':10,'site_name':200,'shipping_address':1000,'payment_terms':1000,'bank_details':1000,'terms':2000,'signatory':200,'place_of_supply':2,'supply_type':30,'template':30}
SUPPLIES=('taxable','exempt','nil_rated','non_gst','unregistered')
def settings(org):
    r=Record.objects(organization=org,kind='invoice_settings',key='default').first()
    return r.data if r else {'template':'classic'}

def clean_details(raw, org, items):
    if not isinstance(raw,dict) or set(raw)-set(TEXT_FIELDS):raise ValueError('Unknown invoice detail fields.')
    d={}
    for k,v in raw.items():
        if not isinstance(v,str) or len(v)>TEXT_FIELDS[k]:raise ValueError('Invalid '+k)
        d[k]=v.strip()
    for k in ('po_date','service_from','service_to'):
        if d.get(k):date.fromisoformat(d[k])
    if d.get('service_from') and d.get('service_to') and d['service_from']>d['service_to']:raise ValueError('Service end precedes start.')
    if d.get('template','classic') not in [t[0] for t in TEMPLATES]:raise ValueError('Select an invoice format.')
    supply=d.get('supply_type','')
    if supply not in SUPPLIES:raise ValueError('Choose GST taxable or an explicit non-taxable classification.')
    reg=Record.objects(organization=org,kind='gst_settings',key='registration').first()
    r=reg.data if reg else {}
    if supply!='unregistered':
        if r.get('registration')!='regular':raise ValueError('Configure a regular GST registration in Taxation first. Composition billing requires separate review.')
        if not re.fullmatch(r'[0-9]{2}',d.get('place_of_supply','')):raise ValueError('Enter the two-digit place-of-supply state code.')
        if not re.fullmatch(r'[0-9]{2}',r.get('state_code','')):raise ValueError('Configure supplier state code.')
        if not r.get('gstin'):raise ValueError('Configure supplier GSTIN.')
    elif r.get('registration') in ('regular','composition'):raise ValueError('Registered businesses must select the applicable supply classification, not unregistered.')
    if supply!='taxable' and any(Decimal(str(i.tax_rate))!=0 for i in items):raise ValueError('Non-taxable invoices must have zero tax rates. Correct the lines first.')
    for i in items:
        if not i.item_name:i.item_name=i.product.name
        if not i.hsn_code:i.hsn_code=i.product.hsn_code
        if not i.unit:i.unit=i.product.unit
        i.item_type=i.product.item_type
        if supply!='unregistered' and not re.fullmatch(r'[0-9]{4}|[0-9]{6}|[0-9]{8}',i.hsn_code or ''):raise ValueError('Enter HSN/SAC for every GST invoice line in the product master.')
        if i.item_type=='service' and i.hsn_code and len(i.hsn_code)!=6:raise ValueError('Service lines require a six-digit SAC.')
    d['supplier_gstin']=r.get('gstin','') if supply!='unregistered' else ''
    d['supplier_state']=r.get('state_code','')
    d['tax_reviewed']=True
    return d

def tax_heads(invoice):
    d=invoice.billing_details; total=Decimal(str(invoice.tax_amount))
    if d.get('supply_type')!='taxable':return Decimal(0),Decimal(0),Decimal(0)
    if d.get('supplier_state')!=d.get('place_of_supply'):return Decimal(0),Decimal(0),total
    cgst=sum((Decimal(money(Decimal(str(i.line_tax))/2)) for i in invoice.items),Decimal(0))
    return cgst,total-cgst,Decimal(0)

@api_login_required
@require_http_methods(['GET','POST'])
@write_lock
def invoice_settings(request):
    if not permitted(request,'organizations.update'):return R.forbidden(message='Administrator permission required.',request=request)
    try:
        if request.method=='POST':
            p=payload(request)
            allowed={'template','logo','bank_details','payment_terms','terms','signatory'}
            if set(p)-allowed:raise ValueError('Unknown setting.')
            for k,v in p.items():
                if not isinstance(v,str) or len(v)>(400000 if k=='logo' else 2000):raise ValueError('Invalid '+k)
            if p.get('template') not in [t[0] for t in TEMPLATES]:raise ValueError('Choose a template.')
            if p.get('logo'):
                from PIL import Image
                prefix,encoded=p['logo'].split(',',1)
                if prefix not in ('data:image/png;base64','data:image/jpeg;base64'):raise ValueError('Use PNG or JPEG.')
                blob=base64.b64decode(encoded,validate=True)
                im=Image.open(BytesIO(blob))
                if im.width*im.height>4000000:raise ValueError('Resize logo below 4 megapixels.')
                im.verify()
            Record.objects(organization=request.api_organization,kind='invoice_settings',key='default').update_one(upsert=True,set__data=p,set__created_by=request.api_user,inc__revision=1)
            audit(request,'invoice_settings',request.api_organization.id,'update')
        return R.success(data={'settings':settings(request.api_organization),'templates':[dict(id=i,name=n,color=c,layout=l) for i,n,c,l in TEMPLATES]},request=request)
    except (ValueError,TypeError,ValidationError,OSError) as e:return R.validation_error(message=str(e),request=request)

@api_login_required
@require_http_methods(['GET','POST'])
@write_lock
def invoice_details(request,invoice_id):
    from apps.sales.models import Invoice
    if not permitted(request,'invoices.read' if request.method=='GET' else 'invoices.create'):return R.forbidden(message='Permission denied.',request=request)
    try:
        inv=Invoice.objects(organization=request.api_organization,id=invoice_id).first()
        if not inv:return R.not_found(message='Invoice not found.',request=request)
        if request.method=='POST':
            from .enhancements import is_admin
            if getattr(request.api_organization,'invoice_admin_only',True) and not is_admin(request.api_user):return R.forbidden(message='Only a system Admin can edit invoice details.',request=request)
            if inv.status!='DRAFT':raise ValueError('Issued invoice details are locked.')
            clean=clean_details(payload(request),request.api_organization,inv.items)
            branding=settings(request.api_organization)
            inv.billing_details={**branding,**clean}
            changed=Invoice.objects(organization=request.api_organization,id=inv.id,status='DRAFT').update_one(set__billing_details=inv.billing_details,set__items=inv.items)
            if not changed:raise ValueError('Invoice changed while editing. Reload before continuing.')
            audit(request,'invoice',inv.id,'details')
        return R.success(data={'details':inv.billing_details,'templates':[{'id':i,'name':n} for i,n,_,_ in TEMPLATES]},request=request)
    except (ValueError,TypeError,ValidationError) as e:return R.validation_error(message=str(e),request=request)

def invoice_account(org,user,key):
    """Provision only named control accounts; never replace a user's account."""
    from apps.finance.models import ChartOfAccount
    from mongoengine.errors import NotUniqueError
    definitions={'SERVICE_REVENUE':('NX-SERVICE','Service revenue','REVENUE','OPERATING_REVENUE'),'OUTPUT_CGST':('NX-CGST','Output CGST','LIABILITY','CURRENT_LIABILITY'),'OUTPUT_SGST':('NX-SGST','Output SGST / UTGST','LIABILITY','CURRENT_LIABILITY'),'OUTPUT_IGST':('NX-IGST','Output IGST','LIABILITY','CURRENT_LIABILITY')}
    code,name,kind,subtype=definitions[key]
    a=ChartOfAccount.objects(organization=org,system_key=key).first()
    if a:
        if not a.is_active or a.account_type!=kind:raise ValueError('Review inactive or mismatched control account: '+key)
        return a
    if ChartOfAccount.objects(organization=org,account_code=code).first():raise ValueError('Control account code already used: '+code)
    try:return ChartOfAccount(organization=org,created_by=user,account_code=code,account_name=name,account_type=kind,account_subtype=subtype,normal_balance='CREDIT',system_key=key,is_system_account=True,allow_manual_posting=False).save()
    except NotUniqueError:
        a=ChartOfAccount.objects(organization=org,system_key=key,is_active=True,account_type=kind).first()
        if not a:raise ValueError('Concurrent control account conflict. Reload and retry.')
        return a

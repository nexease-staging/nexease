"""Tenant-scoped Sandbox IRP integration for domestic B2B tax invoices."""
import base64
import hashlib
import json
import os
import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from cryptography.fernet import Fernet, InvalidToken
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from mongoengine.connection import get_db
from mongoengine.errors import ValidationError

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.saas.entitlements import has_einvoice, org_lock
from apps.sales.models import Invoice
from .gst_provider import NoRedirect, configuration, request_json
from .models import BusinessRecord
from .views import audit, payload, permitted

PREFIX = '/gst/compliance/e-invoice/tax-payer'
GSTIN = r'[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]'
IRN = r'[a-fA-F0-9]{64}'
ELIGIBLE = ('ISSUED', 'PARTIALLY_PAID', 'PAID')


def cipher():
    try:
        return Fernet(os.environ.get('EINVOICE_ENCRYPTION_KEY', '').encode())
    except ValueError:
        raise ValueError('Configure EINVOICE_ENCRYPTION_KEY on the backend.') from None


def registration(org):
    record = BusinessRecord.objects(organization=org, kind='gst_settings', key='registration').first()
    return record.data if record else {}


def settings_key(org, env):
    return f'{org.id}:{env}'


def call(base, path, headers, body=None):
    raw = json.dumps(body).encode() if body is not None else None
    req = Request(base+path, data=raw, headers={'Accept':'application/json', 'Content-Type':'application/json', **headers})
    try:
        with build_opener(NoRedirect()).open(req, timeout=20) as response:
            data = json.loads(response.read(524288))
    except HTTPError as exc:
        raise ValueError(f'Sandbox e-invoice request returned HTTP {exc.code}. Check live access and provider logs.') from None
    except (URLError, OSError, ValueError):
        raise ValueError('Sandbox response could not be verified. Check the IRP before submitting again.') from None
    if not isinstance(data,dict):
        raise ValueError('Unexpected Sandbox response.')
    return data


def unwrap(result):
    data=result
    for _ in range(4):
        if str(data.get('code',200)) not in ('200','201') or str(data.get('status_cd',data.get('Status',1))) in ('0','false','False'):
            ref=str(result.get('transaction_id',''))
            suffix=f' Reference: {ref}.' if re.fullmatch(r'[a-fA-F0-9-]{8,64}',ref) else ''
            raise ValueError('IRP rejected the request. Review the provider transaction.'+suffix)
        child=data.get('data',data.get('Data'))
        if isinstance(child,str) and child.startswith('{'):
            try:child=json.loads(child)
            except ValueError:raise ValueError('Invalid Sandbox response data.') from None
        if not isinstance(child,dict):
            return data
        data=child
    return data


def session(org, seller_gstin, *, eway=False):
    key, secret, env = configuration()
    saved=get_db().nexease_einvoice_settings.find_one({'_id':settings_key(org,env)})
    if not saved or saved['gstin']!=seller_gstin:
        raise ValueError('An administrator must connect IRP credentials for the invoice seller GSTIN.')
    base='https://api.sandbox.co.in' if env=='live' else 'https://test-api.sandbox.co.in'
    version='EWAY_SANDBOX_API_VERSION' if eway else 'EINVOICE_SANDBOX_API_VERSION'
    headers={'x-api-key':key,'x-api-version':os.getenv(version,'1.0.0'),'x-source':'primary'}
    token_key=('nx-eway:' if eway else 'nx-irp:')+hashlib.sha256((key+saved['credentials']).encode()).hexdigest()
    token=cache.get(token_key)
    if not token:
        try:
            credentials=json.loads(cipher().decrypt(saved['credentials'].encode()))
        except (InvalidToken,ValueError):
            raise ValueError('IRP credentials cannot be read. Verify the encryption key or reconnect.') from None
        auth=request_json(base+'/authenticate',{'x-api-key':key,'x-api-secret':secret},None)
        jwt=unwrap(auth).get('access_token')
        if not jwt:
            raise ValueError('Sandbox API authentication did not return an access token.')
        auth_route='/gst/compliance/e-way-bill/tax-payer/authenticate' if eway else PREFIX+'/authenticate?force=false'
        data=unwrap(call(base,auth_route,{**headers,'authorization':jwt},{
            'gstin':seller_gstin,'username':credentials['username'],
            'password':base64.b64encode(credentials['password'].encode()).decode().rstrip('='),
        }))
        token=data.get('access_token') or data.get('AuthToken') or data.get('auth_token')
        if not isinstance(token,str) or not token or '\r' in token or '\n' in token:
            raise ValueError('IRP authentication did not return an access token.')
        cache.set(token_key,token,5*3600)
    return base,{**headers,'authorization':token},saved


def money(value):
    return Decimal(str(value)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)


def require_text(value,label,minimum,maximum):
    value=str(value or '').strip()
    if not minimum<=len(value)<=maximum:
        raise ValueError(f'Enter {label} ({minimum}–{maximum} characters).')
    return value


def pin(value):
    if not re.fullmatch(r'[1-9][0-9]{5}',str(value)):
        raise ValueError('Enter a valid six-digit PIN code for the seller and buyer.')
    return int(value)


def build_document(inv,reg,seller):
    d=inv.billing_details or {}
    gstin=d.get('supplier_gstin','')
    buyer=(inv.customer_gstin or '').upper()
    pos=d.get('place_of_supply','')
    if inv.status not in ELIGIBLE or not d.get('tax_reviewed') or d.get('supply_type')!='taxable':
        raise ValueError('Choose an issued, reviewed GST tax invoice.')
    if reg.get('registration')!='regular' or gstin!=reg.get('gstin') or not re.fullmatch(GSTIN,gstin):
        raise ValueError('Invoice seller GSTIN must match the workspace regular GST registration.')
    if getattr(inv,'billing_country','India').strip().lower() not in ('india','in'):
        raise ValueError('Only domestic B2B invoices are supported.')
    if not re.fullmatch(GSTIN,buyer) or not re.fullmatch(r'[0-9]{2}',pos):
        raise ValueError('Domestic B2B e-invoicing requires a buyer GSTIN and place of supply.')
    if d.get('supplier_state')!=gstin[:2] or (gstin[:2]==pos and buyer[:2]!=pos):
        raise ValueError('Review seller, buyer and place-of-supply states before generating the IRN.')
    if not re.fullmatch(r'[1-9A-Z][A-Z0-9/-]{0,15}',inv.invoice_number):
        raise ValueError('IRP invoice number must be uppercase, at most 16 characters, and not start with 0, / or -.')
    rows=[]; taxable=cgst=sgst=igst=discount=Decimal(0)
    for index,i in enumerate(inv.items,1):
        service=i.item_type=='service'
        if not re.fullmatch(r'[0-9]{6}' if service else r'[0-9]{4}(?:[0-9]{2}){0,2}',i.hsn_code or ''):
            raise ValueError('Review HSN/SAC on every invoice item.')
        qty=money(i.quantity);price=money(i.unit_price);gross=money(i.line_subtotal);disc=money(i.discount)
        base=gross-disc;tax=money(i.line_tax);rate=money(i.tax_rate)
        if base<0 or money(qty*price)!=gross or money(base*rate/100)!=tax or money(base+tax)!=money(i.line_total):
            raise ValueError('Invoice line amounts do not reconcile. Review prices, discounts and GST.')
        half=money(tax/2) if gstin[:2]==pos else Decimal(0)
        other=tax-half if gstin[:2]==pos else Decimal(0)
        inter=tax if gstin[:2]!=pos else Decimal(0)
        row={'SlNo':str(index),'PrdDesc':(i.item_name or i.product.name)[:300],'IsServc':'Y' if service else 'N','HsnCd':i.hsn_code,
             'Qty':float(qty),'UnitPrice':float(price),'TotAmt':float(gross),'Discount':float(disc),
             'AssAmt':float(base),'GstRt':float(rate),'IgstAmt':float(inter),'CgstAmt':float(half),'SgstAmt':float(other),'TotItemVal':float(base+tax)}
        if not service:
            unit=str(i.unit or '').upper().strip()
            unit={'PIECE':'PCS','PIECES':'PCS','PC':'PCS','NOS':'NOS','UNIT':'UNT','UNITS':'UNT','KG':'KGS','L':'LTR','BOX':'BOX','PACK':'PAC','BOTTLE':'BTL'}.get(unit,unit)
            if not re.fullmatch(r'[A-Z]{3}',unit):
                raise ValueError('Use a three-letter GST unit code for each goods line (e.g. PCS, KGS, LTR).')
            row['Unit']=unit
        rows.append(row);taxable+=base;cgst+=half;sgst+=other;igst+=inter;discount+=disc
    total=taxable+cgst+sgst+igst
    if not rows or discount!=money(inv.discount_amount) or taxable+discount!=money(inv.subtotal) or cgst+sgst+igst!=money(inv.tax_amount) or total!=money(inv.total_amount):
        raise ValueError('Invoice totals do not reconcile with the IRP payload.')
    return {
        'Version':'1.1','TranDtls':{'TaxSch':'GST','SupTyp':'B2B','RegRev':'N','IgstOnIntra':'N'},
        'DocDtls':{'Typ':'INV','No':inv.invoice_number,'Dt':inv.invoice_date.strftime('%d/%m/%Y')},
        'SellerDtls':{'Gstin':gstin,'LglNm':require_text(reg.get('legal_name'), 'seller legal name',3,100),
                      'Addr1':require_text(seller.get('address'),'seller address',1,100),
                      'Loc':require_text(seller.get('city'),'seller city',1,50),'Pin':pin(seller.get('pincode')),'Stcd':gstin[:2]},
        'BuyerDtls':{'Gstin':buyer,'LglNm':require_text(inv.billing_name,'buyer legal name',3,100),
                     'Addr1':require_text(inv.billing_address,'buyer billing address',1,100),
                     'Loc':require_text(inv.billing_city,'buyer city',1,50),'Pin':pin(inv.billing_pincode),'Stcd':buyer[:2],'Pos':pos},
        'ItemList':rows,'ValDtls':{'AssVal':float(taxable),'CgstVal':float(cgst),'SgstVal':float(sgst),'IgstVal':float(igst),'TotInvVal':float(total)},
    }


def saved_result(result, document):
    data=unwrap(result)
    irn=data.get('Irn','')
    qr=data.get('SignedQRCode','')
    expected=hashlib.sha256((document['SellerDtls']['Gstin']+financial_year(document['DocDtls']['Dt'])+'INV'+document['DocDtls']['No']).encode()).hexdigest()
    if not re.fullmatch(IRN,str(irn)) or irn.lower()!=expected or not isinstance(qr,str) or not 1<=len(qr)<=4096:
        raise ValueError('IRP response did not match this invoice. Verify the document in the IRP before proceeding.')
    status=str(data.get('Status','ACT')).upper()
    if status not in ('ACT','ACTIVE','CNL','CANCELLED'):
        raise ValueError('IRP returned an unrecognized invoice status.')
    return {'status':'cancelled' if status in ('CNL','CANCELLED') else 'registered','irn':irn,'qr':qr,
            'ack_no':str(data.get('AckNo',''))[:30], 'ack_date':str(data.get('AckDt',''))[:40]}


def financial_year(value):
    date=datetime.strptime(value,'%d/%m/%Y')
    start=date.year-(date.month<4)
    return f'{start}-{str(start+1)[-2:]}'


def public(inv):
    data=inv.einvoice or {}
    return {'id':str(inv.id),'number':inv.invoice_number,'date':inv.invoice_date.date().isoformat(),
            'customer':inv.billing_name,'invoice_status':inv.status,
            **{k:data[k] for k in ('status','irn','ack_no','ack_date','environment') if k in data}}


@api_login_required
@require_http_methods(['GET','POST'])
def einvoices(request):
    org=request.api_organization
    if not has_einvoice(org) or not permitted(request,'invoices.read'):
        return R.forbidden(message='E-invoicing requires an active Pro plan and invoice access.',request=request)
    admin=permitted(request,'organizations.update')
    try:
        env=os.getenv('GST_SANDBOX_ENV','test').strip().lower()
        reg=registration(org)
        if request.method=='GET':
            query=Invoice.objects(organization=org,status__in=[*ELIGIBLE,'CANCELLED'])
            search=request.GET.get('search','').strip()[:50]
            if search:query=query.filter(invoice_number__icontains=search)
            from mongoengine.queryset.visitor import Q
            query=query.filter(Q(customer_gstin__ne='')|Q(einvoice__status__exists=True))
            saved=get_db().nexease_einvoice_settings.find_one({'_id':settings_key(org,env)})
            return R.success(data={'records':[public(x) for x in query.order_by('-invoice_date').limit(100)],
                'configured':bool(saved and saved['gstin']==reg.get('gstin')),'gstin':reg.get('gstin',''),'environment':env,
                'can_configure':admin,'can_issue':permitted(request,'invoices.issue'),'can_cancel':permitted(request,'invoices.cancel')},request=request)
        data=payload(request);action=data.get('action')
        if action=='configure':
            if not admin:return R.forbidden(message='Organization administrator required.',request=request)
            _,_,env=configuration()
            gstin=reg.get('gstin','')
            if reg.get('registration')!='regular' or not re.fullmatch(GSTIN,gstin):raise ValueError('Set a regular seller GSTIN under Taxation first.')
            fields={k:require_text(data.get(k),k,1,n) for k,n in [('username',100),('address',100),('city',50),('pincode',6)]}
            password=data.get('password')
            if not isinstance(password,str) or not 1<=len(password)<=200:raise ValueError('Enter the IRP API password.')
            pin(fields['pincode'])
            credentials=cipher().encrypt(json.dumps({'username':fields.pop('username'),'password':password}).encode()).decode()
            with org_lock(org.id):
                get_db().nexease_einvoice_settings.update_one({'_id':settings_key(org,env)},{'$set':{**fields,'gstin':gstin,'credentials':credentials}},upsert=True)
            audit(request,'einvoice',org.id,'configure')
            return R.success(data={'configured':True},request=request)
        if action not in ('generate','recover','cancel','check-cancellation'):
            raise ValueError('Choose a valid e-invoice action.')
        if not permitted(request,'invoices.cancel' if action in ('cancel','check-cancellation') else 'invoices.issue'):
            return R.forbidden(message='Invoice issue or cancellation permission required.',request=request)
        if data.get('confirm') is not True:raise ValueError('Review and confirm this IRP action.')
        with org_lock(org.id):
            inv=Invoice.objects(organization=org,id=data.get('id')).first()
            if not inv:return R.not_found(message='Invoice not found.',request=request)
            old=inv.einvoice or {};status=old.get('status')
            if old and old.get('environment')!=env:raise ValueError('This invoice has an IRP record in another environment. Use a different invoice for live testing.')
            if action=='generate' and inv.eway_status:
                raise ValueError('Resolve the linked e-way bill before submitting an e-invoice.')
            if action=='cancel' and inv.eway_status:
                raise ValueError('Resolve or cancel the linked e-way bill before cancelling the IRN.')
            if action=='generate' and status:
                raise ValueError('This invoice already has an IRP record. Recover a pending request instead of submitting again.')
            if action=='recover' and status!='pending':raise ValueError('This invoice is not pending recovery.')
            if action in ('cancel','check-cancellation') and status not in ('registered','cancel_pending'):raise ValueError('An active IRN is required.')
            if action=='cancel' and status=='cancel_pending':raise ValueError('Check the cancellation outcome before retrying.')
            if action=='generate':
                from apps.saas.provider_guard import reserve_einvoice
                reserve_einvoice(org,inv.id,env)
            base,headers,seller=session(org,(inv.billing_details or {}).get('supplier_gstin',''))
            document=old.get('document') if old else build_document(inv,reg,seller)
            route=PREFIX+'/invoice'
            if action=='generate' and data.get('transport') is not None:
                from .ewaybill import transport
                if not isinstance(data['transport'],dict) or any(i['IsServc']=='Y' for i in document['ItemList']):
                    raise ValueError('Combined generation requires a goods-only invoice and transport details.')
                if document['BuyerDtls']['Stcd']!=document['BuyerDtls']['Pos'] or (inv.billing_details or {}).get('shipping_address') not in ('',None,inv.billing_address):
                    raise ValueError('Use the portal for a separate ship-to address or state.')
                document['EwbDtls']={k:v for k,v in transport(data['transport']).items() if v!=''}
            if action=='generate':
                claimed=Invoice.objects(id=inv.id,organization=org,status=inv.status,updated_at=inv.updated_at,
                                        einvoice__status__exists=False,eway_status__in=['',None]).update_one(
                    set__einvoice={'status':'pending','environment':env,'document':document},
                    set__updated_at=datetime.utcnow(),set__eway_status='pending' if 'EwbDtls' in document else '')
                if not claimed:
                    raise ValueError('Invoice changed. Reload it before submitting.')
                if 'EwbDtls' in document:
                    from .ewaybill import key_for
                    get_db().nexease_eway_bills.update_one({'_id':key_for(org,env,'invoice',str(inv.id))},{'$setOnInsert':{
                        'organization_id':str(org.id),'environment':env,'kind':'invoice','source_id':str(inv.id),
                        'document':inv.invoice_number,'status':'pending','created_at':datetime.utcnow()}},upsert=True)
                reply=call(base,route,headers,document)
                result=saved_result(reply,document)
            elif action in ('recover','check-cancellation'):
                doc=document['DocDtls']
                query=urlencode(dict(document_type=doc['Typ'],document_number=doc['No'],document_date=doc['Dt']))
                reply=call(base,route+'?'+query,headers)
                result=saved_result(reply,document)
            else:
                reason=str(data.get('reason',''));remarks=require_text(data.get('remarks'),'cancellation remarks',3,100)
                if reason not in ('1','2','3','4'):raise ValueError('Select a cancellation reason.')
                irn=old['irn']
                inv.update(set__einvoice={**old,'status':'cancel_pending'})
                reply=unwrap(call(base,route+'/'+irn+'/cancel',headers,{'Irn':irn,'CnlRsn':reason,'CnlRem':remarks}))
                if reply.get('Irn')!=irn or not reply.get('CancelDate'):
                    raise ValueError('IRP cancellation could not be verified. Check the cancellation outcome.')
                result={**old,'status':'cancelled','cancel_date':str(reply['CancelDate'])[:40]}
            if 'EwbDtls' in document and action in ('generate','recover'):
                from .ewaybill import key_for,response_fields
                key=key_for(org,env,'invoice',str(inv.id))
                status='pending';ewb={}
                try:
                    ewb=response_fields(unwrap(reply));status='generated'
                except ValueError:
                    pass
                coll=get_db().nexease_eway_bills
                existing=coll.find_one({'_id':key})
                if existing and existing['status'] in ('portal_recorded','portal_cancelled'):
                    status='' if existing['status']=='portal_cancelled' else existing['status']
                else:coll.update_one({'_id':key},{'$set':{
                    **ewb,'organization_id':str(org.id),'environment':env,'kind':'invoice','source_id':str(inv.id),
                    'document':inv.invoice_number,'status':status},'$setOnInsert':{'created_at':datetime.utcnow()}},upsert=True)
                inv.update(set__eway_status=status)
            inv.update(set__einvoice={**result,'environment':env,'document':document})
            inv.reload()
            audit(request,'einvoice',inv.id,action)
        return R.success(data=public(inv),request=request)
    except (ValueError,ValidationError) as exc:
        return R.validation_error(message=str(exc),request=request)

@api_login_required
@require_http_methods(['GET'])
def einvoice_pdf(request, invoice_id):
    from django.http import HttpResponse
    from .print_documents import invoice_pdf
    org=request.api_organization
    if not has_einvoice(org) or not permitted(request,'invoices.read'):
        return R.forbidden(message='E-invoicing requires an active Pro plan and invoice access.',request=request)
    try:
        inv=Invoice.objects(organization=org,id=invoice_id).first()
    except ValidationError:
        inv=None
    if not inv:return R.not_found(message='Invoice not found.',request=request)
    response=HttpResponse(invoice_pdf(inv),content_type='application/pdf')
    response['Content-Disposition']='attachment; filename="NexEase-Invoice.pdf"'
    return response

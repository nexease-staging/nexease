"""Outward e-way bills based on existing tenant sales documents."""
from datetime import date, datetime
import os
import re
from decimal import InvalidOperation

from django.views.decorators.http import require_http_methods
from mongoengine.connection import get_db
from mongoengine.errors import ValidationError
from pymongo.errors import DuplicateKeyError

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.sales.models import Invoice
from apps.saas.entitlements import has_einvoice, org_lock
from .einvoice import ELIGIBLE, GSTIN, build_document, call, money, pin, registration, require_text, session, unwrap
from .views import audit, payload, permitted

BILL = '/gst/compliance/e-way-bill/consignor/bill'
PORTAL = 'https://ewaybillgst.gov.in/'


def transport(data):
    mode=str(data.get('mode',''))
    if mode not in ('1','2','3','4'):raise ValueError('Select a transport mode.')
    distance=str(data.get('distance',''))
    if not re.fullmatch(r'[1-9][0-9]{0,3}',distance) or int(distance)>4000:
        raise ValueError('Enter the reviewed distance in km (1–4000).')
    vehicle=re.sub(r'[ -]','',str(data.get('vehicle','')).upper())
    if mode=='1' and not re.fullmatch(r'[A-Z0-9]{7,15}',vehicle):
        raise ValueError('Enter the road vehicle registration number.')
    doc=str(data.get('transport_doc','')).strip()
    when=str(data.get('transport_date','')).strip()
    if len(doc)>15 or (mode!='1' and (not doc or not when)):
        raise ValueError('Enter transport document number and date for rail, air or ship.')
    if bool(doc)!=bool(when):raise ValueError('Provide both transport document number and date.')
    tid=str(data.get('transporter_id','')).upper().strip()
    if tid and not re.fullmatch(r'[0-9A-Z]{15}',tid):raise ValueError('Enter a 15-character transporter ID.')
    vtype=str(data.get('vehicle_type','R'))
    if vtype not in ('R','O'):raise ValueError('Select regular or over-dimensional vehicle.')
    return {'TransMode':mode,'Distance':int(distance),'VehNo':vehicle if mode=='1' else '',
            'VehType':vtype if mode=='1' else '', 'TransId':tid,'TransDocNo':doc,
            'TransDocDt':date.fromisoformat(when).strftime('%d/%m/%Y') if when else ''}


def build(source, kind, reg, seller, fields):
    t=transport(fields)
    if kind=='invoice':
        if any(i.item_type=='service' for i in source.items):
            raise ValueError('This e-way bill workflow requires a goods-only invoice.')
        doc=build_document(source,reg,seller)
        frm,to=doc['SellerDtls'],doc['BuyerDtls']
        details=doc['DocDtls']
        vals=doc['ValDtls']
        items=[{'productName':i['PrdDesc'][:100],'hsnCode':int(i['HsnCd']),'quantity':i['Qty'],
                'qtyUnit':i['Unit'],'taxableAmount':i['AssAmt'],'cgstRate':i['GstRt']/2 if frm['Stcd']==to['Pos'] else 0,
                'sgstRate':i['GstRt']/2 if frm['Stcd']==to['Pos'] else 0,
                'igstRate':i['GstRt'] if frm['Stcd']!=to['Pos'] else 0,'cessRate':0} for i in doc['ItemList']]
        reason='1'
        if (source.billing_details or {}).get('shipping_address') not in ('',None,source.billing_address):
            raise ValueError('Use the portal for a separate ship-to address.')
        if to['Stcd']!=to['Pos']:raise ValueError('Use the portal for a separate ship-to state.')
    else:
        reason={'job_work':'4','non_supply':'8','liquid_gas':'8','notified':'8'}.get(source['reason'])
        if not reason:raise ValueError('Unsupported challan reason.')
        gstin=source['seller_gstin'];buyer=source['customer_gstin'] or 'URP'
        if gstin!=reg.get('gstin') or not re.fullmatch(GSTIN,gstin):
            raise ValueError('Challan seller GSTIN must match the configured registration.')
        if buyer!='URP' and buyer[:2]!=source['pos']:raise ValueError('Use the portal for a separate ship-to state.')
        frm={'Gstin':gstin,'LglNm':source['seller_name'],'Stcd':gstin[:2],'Addr1':source['seller_address'],'Loc':seller['city'],'Pin':pin(seller['pincode'])}
        to={'Gstin':buyer,'LglNm':source['customer_name'],'Stcd':source['pos'],'Addr1':source['address'],
            'Loc':require_text(fields.get('destination_city'),'delivery city',1,50),'Pin':pin(fields.get('destination_pin'))}
        details={'Typ':'CHL','No':source['number'],'Dt':date.fromisoformat(source['date']).strftime('%d/%m/%Y')}
        vals={key:float(sum(money(i[field]) for i in source['items'])) for key,field in
              [('AssVal','value'),('CgstVal','cgst'),('SgstVal','sgst'),('IgstVal','igst')]}
        vals['TotInvVal']=round(sum(vals.values()),2)
        items=[]
        for i in source['items']:
            qty=money(i['qty']);rate=float(money(i['rate']))
            unit=str(i['unit']).upper().strip()
            unit={'PIECE':'PCS','PIECES':'PCS','UNIT':'UNT','KG':'KGS','L':'LTR','PACK':'PAC','BOTTLE':'BTL'}.get(unit,unit)
            if qty<=0 or not re.fullmatch(r'[A-Z]{3}',unit):raise ValueError('E-way bill requires final positive quantities and three-letter GST unit codes.')
            intra=frm['Stcd']==to['Stcd']
            items.append({'productName':i['name'][:100],'hsnCode':int(i['hsn']),'quantity':float(qty),
                          'qtyUnit':unit,'taxableAmount':float(money(i['value'])),'cgstRate':rate/2 if intra else 0,
                          'sgstRate':rate/2 if intra else 0,'igstRate':0 if intra else rate,'cessRate':0})
    if not re.fullmatch(r'[A-Z0-9/-]{1,16}',details['No']):raise ValueError('Document number must contain at most 16 letters, digits, slashes or dashes.')
    body={'supplyType':'O','subSupplyType':reason,'docType':details['Typ'],'docNo':details['No'],'docDate':details['Dt'],
          'transactionType':1,'totalValue':vals['AssVal'],'cgstValue':vals['CgstVal'],'sgstValue':vals['SgstVal'],
          'igstValue':vals['IgstVal'],'cessValue':0,'cessNonAdvolValue':0,'otherValue':0,'totInvValue':vals['TotInvVal'],
          'itemList':items,'transMode':t['TransMode'],'transDistance':str(t['Distance']),'vehicleNo':t['VehNo'],
          'vehicleType':t['VehType'],'transporterId':t['TransId'],'transDocNo':t['TransDocNo'],'transDocDate':t['TransDocDt']}
    if reason=='8':body['subSupplyDesc']={'non_supply':'Other than supply','liquid_gas':'Liquid gas','notified':'Other notified movement'}[source['reason']]
    for prefix,party in [('from',frm),('to',to)]:
        address=require_text(party['Addr1'],prefix+' address',1,240)
        body.update({prefix+'Gstin':party['Gstin'],prefix+'TrdName':party['LglNm'][:100],prefix+'Addr1':address[:120],
                     prefix+'Addr2':address[120:],prefix+'Place':party['Loc'],prefix+'Pincode':party['Pin'],
                     prefix+'StateCode':int(party['Stcd']),'act'+prefix.title()+'StateCode':int(party['Stcd'])})
    return body


def response_fields(data):
    number=str(data.get('ewayBillNo') or data.get('ewbNo') or data.get('EwbNo') or '')
    if not re.fullmatch(r'[0-9]{12}',number):raise ValueError('No valid e-way bill number returned. Verify the original document in the portal.')
    return {'number':number,'generated_at':str(data.get('ewayBillDate') or data.get('EwbDt') or '')[:50],
            'valid_until':str(data.get('validUpto') or data.get('EwbValidTill') or '')[:50]}


def key_for(org,env,kind,source_id):
    return f'{org.id}:{env}:{kind}:{source_id}'


@api_login_required
@require_http_methods(['GET','POST'])
def eway_bills(request):
    org=request.api_organization;orgid=str(org.id)
    if not has_einvoice(org) or not permitted(request,'invoices.read'):
        return R.forbidden(message='E-way bills require active Pro and Sales access.',request=request)
    db=get_db();coll=db.nexease_eway_bills
    env=os.getenv('GST_SANDBOX_ENV','test').strip().lower()
    reg=registration(org);gstin=reg.get('gstin','')
    try:
        if request.method=='GET':
            saved=db.nexease_einvoice_settings.find_one({'_id':f'{orgid}:{env}'})
            records=list(coll.find({'organization_id':orgid,'environment':env},{'_id':0,'body':0,'created_at':0}).sort('created_at',-1).limit(100))
            invoices=Invoice.objects(organization=org,status__in=ELIGIBLE).only('invoice_number','einvoice','billing_name').order_by('-invoice_date').limit(100)
            challans=db.nexease_delivery_challans.find({'organization_id':orgid,'status':'issued'},{'number':1,'customer_name':1}).sort('created_at',-1).limit(100)
            return R.success(data={'records':records,'environment':env,'configured':bool(saved and saved['gstin']==gstin),
                'can_issue':permitted(request,'invoices.issue'),'can_cancel':permitted(request,'invoices.cancel'),
                'sources':[{'id':str(i.id),'kind':'invoice','document':i.invoice_number,'customer':i.billing_name,'irp':(i.einvoice or {}).get('status','')} for i in invoices]+
                [{'id':c['_id'],'kind':'challan','document':c['number'],'customer':c['customer_name']} for c in challans]},request=request)
        data=payload(request)
        action=data.get('action','generate')
        if action not in ('generate','record','record-cancellation'):raise ValueError('Invalid e-way bill action.')
        if not permitted(request,'invoices.cancel' if action=='record-cancellation' else 'invoices.issue'):return R.forbidden(message='Sales issue or cancellation permission required.',request=request)
        if data.get('confirm') is not True:raise ValueError('Review and confirm this government submission.')
        kind=data.get('kind');source_id=str(data.get('id',''))
        if kind not in ('invoice','challan'):raise ValueError('Choose an invoice or delivery challan.')
        with org_lock(org.id):
            key=key_for(org,env,kind,source_id)
            existing=coll.find_one({'_id':key})
            if action=='generate' and existing:raise ValueError('A request already exists for this document. Verify its status before any further action.')
            if kind=='invoice':
                source=Invoice.objects(organization=org,id=source_id,status__in=ELIGIBLE).first()
                if not source:raise ValueError('Choose an issued sales invoice.')
                if action=='generate' and source.einvoice:raise ValueError('Use the IRP for an invoice that already has an IRN submission.')
                if action=='generate' and data.get('no_irn_required') is not True:raise ValueError('Confirm this invoice does not require an IRN. Otherwise use combined generation from E-Invoices.')
                number=source.invoice_number
            else:
                source=db.nexease_delivery_challans.find_one({'_id':source_id,'organization_id':orgid,'status':'issued'})
                if not source:raise ValueError('Choose an issued delivery challan.')
                if action=='generate' and source.get('invoice_id'):raise ValueError('Use the linked invoice for this movement to avoid a second e-way bill.')
                number=source['number']
            if action!='generate':
                if data.get('portal_verified') is not True:raise ValueError('Check this exact document in the E-Way Bill Portal first.')
                ewb=str(data.get('number','')).strip()
                if not re.fullmatch(r'[0-9]{12}',ewb):raise ValueError('Enter the 12-digit e-way bill number shown on the portal.')
                if existing and existing.get('number') not in (None,'',ewb):raise ValueError('The number must match the linked e-way bill.')
                if action=='record-cancellation' and (not existing or existing.get('status')=='portal_cancelled'):
                    raise ValueError('Record the portal e-way bill before recording its cancellation.')
                if action=='record' and existing and existing.get('status') in ('generated','portal_cancelled','portal_recorded'):
                    raise ValueError('This e-way bill is already recorded.')
                status='portal_cancelled' if action=='record-cancellation' else 'portal_recorded'
                coll.update_one({'_id':key},{'$set':{'number':ewb,'status':status,'organization_id':orgid,'environment':env,
                    'kind':kind,'source_id':source_id,'document':number},'$setOnInsert':{'created_at':datetime.utcnow()}},upsert=True)
                if kind=='invoice':source.update(set__eway_status='' if status=='portal_cancelled' else status)
                audit(request,'ewaybill',source_id,action)
                return R.success(data={'number':ewb,'status':status},request=request)
            base,headers,seller=session(org,gstin,eway=True)
            body=build(source,kind,reg,seller,data)
            coll.insert_one({'_id':key,'organization_id':orgid,'environment':env,'kind':kind,'source_id':source_id,
                             'document':number,'status':'pending','body':body,'created_at':datetime.utcnow()})
            if kind=='invoice':
                changed=Invoice.objects(organization=org,id=source.id,status=source.status,updated_at=source.updated_at,
                                        eway_status__in=['',None]).update_one(set__eway_status='pending',set__updated_at=datetime.utcnow())
                if not changed:
                    coll.delete_one({'_id':key})
                    raise ValueError('Invoice changed. Reload it before submitting.')
            result=response_fields(unwrap(call(base,BILL,headers,body)))
            coll.update_one({'_id':key},{'$set':{**result,'status':'generated'}})
            if kind=='invoice':source.update(set__eway_status='generated')
            audit(request,'ewaybill',source_id,'generate')
        return R.success(data=result,request=request)
    except (ValueError,TypeError,ValidationError,InvalidOperation,DuplicateKeyError) as exc:
        message=str(exc) if isinstance(exc,(ValueError,ValidationError)) else 'Invalid e-way bill details or a request is already in progress.'
        return R.validation_error(message=message,request=request)

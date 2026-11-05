"""Delivery movement documents; stock and accounting remain in their own workflows."""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from uuid import uuid4
from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from mongoengine.connection import get_db
from mongoengine.errors import ValidationError
from pymongo import ReturnDocument
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.products.models import Product
from apps.sales.models import Customer, Invoice
from apps.saas.entitlements import org_lock
from .einvoice import GSTIN, money, registration, require_text
from .print_documents import document_styles
from .views import audit, payload, permitted

REASONS={'job_work':'Job work','non_supply':'Movement other than supply','liquid_gas':'Liquid gas — quantity not known at dispatch','notified':'Other notified movement'}


def render_pdf(doc):
    buf=BytesIO();styles=document_styles()
    def p(value,style='Normal'):
        return Paragraph(escape(str(value or '—')).replace('\n','<br/>'),styles[style])
    story=[]
    for label in ('Original for consignee','Duplicate for transporter','Triplicate for consignor'):
        if story:story.append(PageBreak())
        story += [p('Delivery challan','Title'),p(label,'Heading3')]
        if doc['status']=='cancelled':story += [p('CANCELLED','Heading2')]
        story += [p(doc['number']+' · '+doc['date']),p('Reason: '+REASONS[doc['reason']]),Spacer(1,10)]
        parties=Table([[p('Consignor','Heading4'),p('Consignee','Heading4')],
            [p(doc['seller_name']+'\n'+doc['seller_address']+'\nGSTIN: '+(doc['seller_gstin'] or 'Unregistered')),
             p(doc['customer_name']+'\n'+doc['address']+'\nGSTIN: '+(doc['customer_gstin'] or 'Unregistered'))]],colWidths=[250,250])
        parties.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
        story += [parties,p('Place of supply: '+doc['pos']),p('Transport reference: '+doc['transport']),
                  p('Linked invoice: '+doc['invoice_number']),Spacer(1,12)]
        rows=[['Description','HSN','Qty / UOM','Taxable ₹','GST %','Tax ₹']]
        for line in doc['items']:
            tax=sum(Decimal(line[k]) for k in ('cgst','sgst','igst'))
            rows.append([line['name'],line['hsn'],('Provisional' if Decimal(line['qty'])==0 else line['qty']+' '+line['unit']),line['value'],line['rate'],str(tax)])
        table=Table([[p(c) for c in row] for row in rows],colWidths=[166,56,76,72,55,75],repeatRows=1)
        table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.25,colors.lightgrey),('BACKGROUND',(0,0),(-1,0),colors.whitesmoke)]))
        story += [table,Spacer(1,10)]
        for key,label in (('value','Taxable value'),('cgst','CGST'),('sgst','SGST / UTGST'),('igst','IGST')):
            story += [p(label+': INR '+str(sum(Decimal(line[key]) for line in doc['items'])))]
        story += [p('Notes: '+doc['notes']),Spacer(1,20),p('Authorised signature: ______________________')]
    SimpleDocTemplate(buf,pagesize=A4,title=doc['number'],leftMargin=40,rightMargin=40).build(story)
    return buf.getvalue()


def make_challan(org,data):
    customer=Customer.objects(id=data.get('customer_id'),organization=org,is_active=True).first()
    if not customer:raise ValueError('Choose an active customer.')
    inv=None
    if data.get('invoice_number'):
        inv=Invoice.objects(invoice_number=str(data['invoice_number']).strip(),organization=org,customer=customer,status__ne='CANCELLED').first()
        if not inv:raise ValueError('Select an invoice belonging to this customer.')
    reason=data.get('reason')
    if reason not in REASONS:raise ValueError('Select a delivery challan reason.')
    dispatch=date.fromisoformat(data.get('date') or '')
    reg=registration(org);gstin=reg.get('gstin','')
    pos=require_text(data.get('pos'),'place-of-supply state code',2,2)
    if not re.fullmatch(r'[0-9]{2}',pos):raise ValueError('Enter a two-digit place-of-supply state code.')
    if gstin and not re.fullmatch(GSTIN,gstin):raise ValueError('Review the seller GST registration.')
    if customer.gstin and not re.fullmatch(GSTIN,customer.gstin):raise ValueError('Review the consignee GSTIN.')
    address=require_text(data.get('address') or customer.shipping_address or customer.billing_address,'delivery address',1,500)
    seller_address=require_text(org.address,'workspace address in Organization settings',1,500)
    transport=str(data.get('transport') or '').strip()[:100]
    notes=str(data.get('notes') or '').strip()[:500]
    rows=data.get('items')
    if not isinstance(rows,list) or not 1<=len(rows)<=50:raise ValueError('Add between 1 and 50 goods lines.')
    items=[];seen=set()
    for item in rows:
        if not isinstance(item,dict):raise ValueError('Invalid goods line.')
        product=Product.objects(id=item.get('product_id'),organization=org,is_active=True).first()
        if not product or product.item_type=='service':raise ValueError('Select an active goods product.')
        if str(product.id) in seen:raise ValueError('Combine repeated products into one line.')
        seen.add(str(product.id))
        if inv and not any(i.product.id==product.id for i in inv.items):raise ValueError('Linked challan goods must appear on the invoice.')
        hsn=product.hsn_code or ''
        if not re.fullmatch(r'[0-9]{4}(?:[0-9]{2}){0,2}',hsn):raise ValueError('Enter the HSN in the product master: '+product.name)
        qty=money(item.get('qty'));value=money(item.get('value'));rate=money(item.get('rate'))
        if not all(x.is_finite() for x in (qty,value,rate)) or not (0<=qty<=100000000 if reason=='liquid_gas' else 0<qty<=100000000) or not 0<=value<=1000000000 or not 0<=rate<=100:
            raise ValueError('Check quantity, taxable value and GST rate.')
        if not qty and not notes:raise ValueError('Explain the provisional liquid gas quantity in Notes.')
        if rate and not gstin:raise ValueError('A GST registration is required for taxable lines.')
        tax=money(value*rate/100);cg=money(tax/2) if gstin[:2]==pos else Decimal(0);sg=tax-cg if gstin[:2]==pos else Decimal(0)
        items.append(dict(product_id=str(product.id),name=product.name,hsn=hsn,unit=product.unit,qty=str(qty),
                          value=str(value),rate=str(rate),cgst=str(cg),sgst=str(sg),igst=str(tax-cg-sg)))
    db=get_db();orgid=str(org.id)
    year=dispatch.year-(dispatch.month<4)
    with org_lock(orgid):
        seq=db.nexease_challan_counters.find_one_and_update({'_id':f'{orgid}:{year}'},{'$inc':{'value':1}},upsert=True,return_document=ReturnDocument.AFTER)['value']
        if seq>999999:raise ValueError('Delivery challan series exhausted for this year.')
        doc=dict(_id=uuid4().hex,organization_id=orgid,number=f'DC-{year}-{seq:06}',date=dispatch.isoformat(),
                 reason=reason,seller_name=reg.get('legal_name') or org.name,seller_address=seller_address,seller_gstin=gstin,
                 customer_id=str(customer.id),customer_name=customer.name,customer_gstin=customer.gstin or '',address=address,
                 invoice_id=str(inv.id) if inv else '',invoice_number=inv.invoice_number if inv else '',pos=pos,transport=transport,
                 notes=notes,items=items,status='issued',created_at=datetime.utcnow())
        db.nexease_delivery_challans.insert_one(doc)
    return doc


def summary(doc):
    return {'id':doc['_id'],**{k:doc[k] for k in ('number','date','customer_name','invoice_number','status','reason')}}


@api_login_required
@require_http_methods(['GET','POST'])
def challans(request,doc_id=None):
    org=request.api_organization;orgid=str(org.id)
    if not permitted(request,'invoices.read'):
        return R.forbidden(message='Sales invoice access required.',request=request)
    coll=get_db().nexease_delivery_challans
    try:
        if request.method=='GET':
            if doc_id:
                doc=coll.find_one({'_id':doc_id,'organization_id':orgid})
                if not doc:return R.not_found(message='Delivery challan not found.',request=request)
                response=HttpResponse(render_pdf(doc),content_type='application/pdf')
                response['Content-Disposition']=f'attachment; filename="{doc["number"]}.pdf"'
                return response
            q={'organization_id':orgid}
            search=request.GET.get('search','').strip()[:60]
            if search:
                q['$or']=[{k:{'$regex':re.escape(search),'$options':'i'}} for k in ('number','customer_name','invoice_number')]
            return R.success(data={'records':[summary(d) for d in coll.find(q).sort('created_at',-1).limit(100)],
                                   'can_create':permitted(request,'invoices.create'),'can_cancel':permitted(request,'invoices.cancel')},request=request)
        data=payload(request)
        if data.get('confirm') is not True:raise ValueError('Review and confirm the delivery challan action.')
        if doc_id:
            if not permitted(request,'invoices.cancel'):return R.forbidden(message='Invoice cancellation permission required.',request=request)
            with org_lock(org.id):
                if get_db().nexease_eway_bills.find_one({'organization_id':orgid,'kind':'challan','source_id':doc_id,'status':{'$ne':'portal_cancelled'}}):
                    raise ValueError('Resolve the linked e-way bill before cancelling this challan.')
                result=coll.update_one({'_id':doc_id,'organization_id':orgid,'status':'issued'},{'$set':{'status':'cancelled','cancelled_at':datetime.utcnow()}})
            if not result.modified_count:return R.not_found(message='No issued delivery challan found.',request=request)
            audit(request,'delivery_challan',doc_id,'cancel')
            return R.success(data={},request=request)
        if not permitted(request,'invoices.create') or not all(permitted(request,p) for p in ('customers.read','products.read')):
            return R.forbidden(message='Invoice creation, customer and product permissions required.',request=request)
        doc=make_challan(org,data)
        audit(request,'delivery_challan',doc['_id'],'issue')
        return R.success(data=summary(doc),request=request)
    except (ValueError,TypeError,InvalidOperation,ValidationError) as exc:
        return R.validation_error(message='Enter valid quantity, taxable value and GST rate.' if isinstance(exc,InvalidOperation) else str(exc),request=request)

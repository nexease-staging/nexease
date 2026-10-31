"""Tenant-scoped operational helpers for the October workflow update."""
import re
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from mongoengine.errors import ValidationError
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from .views import permitted, payload, audit, validate, key_for
from .models import BusinessRecord as Record
from .automation import write_lock, bounds, payrow


def is_admin(user):
    role=getattr(user,'role',None)
    return bool(role and role.is_active and role.is_system and role.name=='Admin' and str(role.organization.id)==str(user.organization.id))


def module_for(path):
    if '/saas/ai' in path:return 'ai'
    if '/business/barcode' in path:return 'barcode'
    if any(x in path for x in ['/business/gst','/business/records/gst_']):return 'taxation'
    if any(x in path for x in ['/business/expenses','/business/records/expenses']):return 'expenses'
    if any(x in path for x in ['/business/workforce/','/business/payroll','/business/daily-work','/business/bulk-assign','/business/labour','/business/workers','/business/balances']):return 'workforce'
    if '/business/records/' in path:return 'workforce'
    if any(x in path for x in ['/chart-of-accounts/','/journal-entries/','/general-ledger/','/trial-balance/','/bank-','/cash-flow/','/finance-audit/','/financial-dashboard/','/finance-dashboard/','/accounting-','/business/books-sync/','/business/accountant-export/']):return 'finance'


@api_login_required
@require_http_methods(['POST'])
def invoice_zip(request):
    if not permitted(request,'invoices.read'):return R.forbidden(message='Invoice read access required.',request=request)
    from apps.sales.models import Invoice
    from apps.finance.services.document_api_service import DocumentAPIService
    try:
        ids=payload(request).get('ids',[])
        if not isinstance(ids,list) or not 1<=len(ids)<=50 or any(not isinstance(i,str) for i in ids):raise ValueError('Select 1–50 invoices.')
        ids=list(dict.fromkeys(ids));invoices=list(Invoice.objects(organization=request.api_organization,id__in=ids))
        if len(invoices)!=len(ids):raise ValueError('One or more invoices are unavailable in this organisation.')
        out=BytesIO()
        with ZipFile(out,'w',ZIP_DEFLATED) as z:
            for inv in invoices:
                result=DocumentAPIService.generate_pdf(user=request.api_user,organization=request.api_organization,document_type='invoice',document_id=str(inv.id))
                name=re.sub(r'[^A-Za-z0-9_.-]','_',inv.invoice_number)
                z.writestr(name+'-'+str(inv.id)+'.pdf',result['content'])
                if out.tell()>50*1024*1024:raise ValueError('ZIP exceeds 50 MB. Select fewer invoices.')
        response=HttpResponse(out.getvalue(),content_type='application/zip');response['Content-Disposition']='attachment; filename="NexEase-Invoices.zip"';response['Cache-Control']='no-store';return response
    except (ValueError,TypeError,ValidationError) as e:return R.validation_error(message=str(e),request=request)


@api_login_required
@require_http_methods(['GET','POST'])
@write_lock
def populate_inputs(request):
    if not permitted(request,'payroll.manage'):return R.forbidden(message='Payroll management access required.',request=request)
    from .payroll_api import applicable_policy
    try:
        params=payload(request) if request.method=='POST' else request.GET
        month=params.get('month','');first,last=bounds(month);org=request.api_organization
        if Record.objects(organization=org,kind='payruns',key=month,data__status__in=['approved','paid']).first():raise ValueError('Approved payroll month is locked.')
        policy=applicable_policy(org,first,last);prepared=[]
        for e in Record.objects(organization=org,kind='employees'):
            if not (e.data.get('active') or e.data.get('end_date')) or e.data['joining_date']>last.isoformat() or (e.data.get('end_date') and e.data['end_date']<first.isoformat()):continue
            if request.method=='GET' and str(e.id)!=params.get('employee_id'):continue
            row=payrow(org,e,month,policy,'automatic');clean=validate('attendance',row['inputs'],org);prepared.append((e,clean))
        if request.method=='GET':
            if len(prepared)!=1:raise ValueError('Select an employee employed in this month.')
            return R.success(data={'inputs':prepared[0][1]},request=request)
        for e,clean in prepared:
            key=key_for('attendance',clean)
            Record.objects(organization=org,kind='attendance',key=key).update_one(upsert=True,set__data=clean,set__created_by=request.api_user,inc__revision=1)
        audit(request,'attendance',month,'populate-approved-sources')
        return R.success(data={'count':len(prepared),'message':f'{len(prepared)} monthly inputs populated from approved attendance and paid leave. Existing allowances and statutory inputs retained. Review before approval.'},request=request)
    except (ValueError,TypeError,ValidationError) as e:return R.validation_error(message=str(e),request=request)


@api_login_required
@require_http_methods(['GET'])
def barcode_lookup(request):
    from apps.products.models import Product
    from apps.inventory.models import Inventory
    from mongoengine.queryset.visitor import Q
    if not permitted(request,'products.read') or not permitted(request,'inventory.read'):return R.forbidden(message='Product and inventory read permissions required.',request=request)
    code=request.GET.get('code','').strip()
    if not code or len(code)>100:return R.validation_error(message='Scan a barcode or enter a SKU.',request=request)
    rows=list(Product.objects(Q(barcode=code)|Q(sku=code),organization=request.api_organization,is_active=True).limit(2))
    if len(rows)!=1:return R.validation_error(message='No unique active product matches. Assign the barcode on Products first.',request=request)
    p=rows[0];stock=[{'warehouse':x.warehouse.name,'quantity':str(x.quantity),'reserved':str(x.reserved_quantity),'available':str(x.quantity-x.reserved_quantity)} for x in Inventory.objects(organization=request.api_organization,product=p)]
    return R.success(data={'id':str(p.id),'name':p.name,'code':p.sku,'barcode':p.barcode,'item_type':p.item_type,'hsn_code':p.hsn_code,'unit':p.unit,'selling_price':str(p.selling_price),'stock':stock},request=request)


@api_login_required
@require_http_methods(['GET'])
def barcode_labels(request):
    from apps.products.models import Product
    from reportlab.graphics.barcode import createBarcodeDrawing
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    if not permitted(request,'products.read'):return R.forbidden(message='Product read permission required.',request=request)
    try:
        ids=request.GET.get('ids','').split(',');copies=int(request.GET.get('copies','1'))
        if not 1<=len(ids)<=50 or not 1<=copies<=20 or len(ids)*copies>200:raise ValueError('Maximum 50 products, 20 copies each and 200 labels total.')
        products=list(Product.objects(organization=request.api_organization,id__in=ids,is_active=True))
        if len(products)!=len(set(ids)):raise ValueError('Product not found.')
        for p in products:
            value=p.barcode or p.sku
            if not re.fullmatch(r'[\x20-\x7e]{1,48}',value):raise ValueError('Printable Code128 labels require 1–48 ASCII characters.')
        out=BytesIO();c=Canvas(out,pagesize=A4);n=0
        for p in products:
            for _ in range(copies):
                if n and n%24==0:c.showPage()
                x=30+(n%2)*280;y=785-((n%24)//2)*64;drawing=createBarcodeDrawing('Code128',value=p.barcode or p.sku,barHeight=25,humanReadable=True)
                scale=min(1,250/drawing.width);c.saveState();c.translate(x,y);c.scale(scale,scale);drawing.drawOn(c,0,0);c.restoreState();c.setFont('Helvetica',8);c.drawString(x,y-13,p.name[:48]);n+=1
        c.save();r=HttpResponse(out.getvalue(),content_type='application/pdf');r['Content-Disposition']='attachment; filename="NexEase-Barcodes.pdf"';r['Cache-Control']='no-store';return r
    except (ValueError,ValidationError) as e:return R.validation_error(message=str(e),request=request)

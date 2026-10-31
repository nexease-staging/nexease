from datetime import date,datetime,timedelta
from decimal import Decimal
import re
from django.views.decorators.http import require_http_methods
from mongoengine.errors import ValidationError,NotUniqueError
from mongoengine.connection import get_db
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from .views import payload,permitted,validate,key_for,audit
from .models import BusinessRecord as Record
from .payroll import amount,money
from .automation import write_lock,advances,run_data,bounds
from .numbering import REGISTRY,settings,allocate,choice

@api_login_required
@require_http_methods(['GET','POST'])
def numbers(request):
    if request.method!='GET' and not permitted(request,'organizations.update'):return R.forbidden(message='Administrator permission required.',request=request)
    try:
        if request.method=='POST':
            p=payload(request);kind=p.get('kind');mode=p.get('mode');prefix=str(p.get('prefix','')).upper();n=int(p.get('next',1));pad=int(p.get('padding',5))
            if kind not in REGISTRY or mode not in ('automatic','manual') or not re.fullmatch(r'[A-Z0-9._/-]{0,20}',prefix) or not 1<=n<=999999999 or not 1<=pad<=12:raise ValueError('Invalid numbering settings.')
            get_db().nexease_numbering.update_one({'_id':str(request.api_organization.id)+':'+kind},{'$set':{'mode':mode,'prefix':prefix,'padding':pad},'$max':{'next':n}},upsert=True);audit(request,'numbering',kind,'configure')
        return R.success(data={'series':[settings(request.api_organization,k) for k in REGISTRY]},request=request)
    except (ValueError,TypeError) as e:return R.validation_error(message=str(e),request=request)

@api_login_required
@require_http_methods(['GET'])
def clients(request):
    if not permitted(request,'labour.read'):return R.forbidden(message='Permission denied.',request=request)
    from apps.sales.models import Customer
    return R.success(data={'records':[{'id':str(c.id),'data':{'code':c.code,'name':c.name}} for c in Customer.objects(organization=request.api_organization,is_active=True).order_by('name').limit(1000)]},request=request)

@api_login_required
@require_http_methods(['GET','POST'])
@write_lock
def daily_work(request):
    if not permitted(request,'labour.read' if request.method=='GET' else 'labour.manage'):return R.forbidden(message='Permission denied.',request=request)
    org=request.api_organization
    try:
        p=payload(request) if request.method=='POST' else request.GET;when=date.fromisoformat(p.get('date','')).isoformat()
        prefs=Record.objects(organization=org,kind='workforce_preferences',key='default').first();default_hours=prefs.data.get('daily_hours','8') if prefs else '8'
        assignments=list(Record.objects(organization=org,kind='assignments',data__status='active',data__start_date__lte=when,data__end_date__gte=when))
        available={};rows=[]
        for a in assignments:
            e=Record.objects(id=a.data['employee_id'],organization=org,kind='employees').first();site=Record.objects(id=a.data['site_id'],organization=org,kind='sites').first()
            if not e or not site or not e.data.get('active') or e.data['joining_date']>when or (e.data.get('end_date') and e.data['end_date']<when):continue
            available[str(a.id)]=a
            existing=Record.objects(organization=org,kind='timesheets',key=a.data['employee_id']+':'+when+':'+a.data['shift'].casefold()).first()
            rows.append({'site_id':str(site.id),'yesterday':bool(Record.objects(organization=org,kind='timesheets',data__employee_id=str(e.id),data__site_id=str(site.id),data__date=(date.fromisoformat(when)-timedelta(days=1)).isoformat(),data__status='approved').first()),'assignment_id':str(a.id),'employee':e.data['name'],'site':site.data['name'],'shift':a.data['shift'],'hours':default_hours,'overtime_hours':'0','billable_units':'1','recorded':bool(existing)})
        for e in Record.objects(organization=org,kind='employees',data__active=True,data__employment_type='inhouse'):
            if e.data['joining_date']>when or (e.data.get('end_date') and e.data['end_date']<when):continue
            aid='internal:'+str(e.id)
            available[aid]=type('Internal',(),{'data':{'employee_id':str(e.id),'site_id':'','shift':'OFFICE','billing_rate':'0'}})()
            existing=Record.objects(organization=org,kind='timesheets',key=str(e.id)+':'+when+':office').first()
            rows.append({'site_id':'internal','assignment_id':aid,'employee':e.data['name'],'site':'In-house staff','shift':'OFFICE','hours':default_hours,'overtime_hours':'0','billable_units':'0','recorded':bool(existing),'yesterday':bool(Record.objects(organization=org,kind='timesheets',data__employee_id=str(e.id),data__date=(date.fromisoformat(when)-timedelta(days=1)).isoformat(),data__status='approved').first())})
        if request.method=='GET':
            if p.get('site_id'):rows=[r for r in rows if r['site_id']==p['site_id']]
            return R.success(data={'rows':rows},request=request)
        incoming=p.get('rows',[])
        if not isinstance(incoming,list) or not 1<=len(incoming)<=500:raise ValueError('Select between 1 and 500 workers.')
        prepared=[];seen=set();hours={}
        for row in incoming:
            aid=row.get('assignment_id');a=available.get(aid)
            if not a or aid in seen:raise ValueError('Invalid or duplicate assignment.')
            seen.add(aid);d={'employee_id':a.data['employee_id'],'site_id':a.data['site_id'],'date':when,'shift':a.data['shift'],'hours':row.get('hours',default_hours),'overtime_hours':row.get('overtime_hours','0'),'billable_units':row.get('billable_units','1'),'billing_rate':a.data.get('billing_rate','0'),'status':'approved','notes':'Daily attendance board'}
            d=validate('timesheets',d,org);key=key_for('timesheets',d)
            if Record.objects(organization=org,kind='timesheets',key=key).first():raise ValueError('Work already recorded. Reload the board.')
            eid=d['employee_id'];hours[eid]=hours.get(eid,Decimal(0))+amount(d['hours'])+amount(d['overtime_hours'])
            existing=sum((amount(t.data['hours'])+amount(t.data.get('overtime_hours',0)) for t in Record.objects(organization=org,kind='timesheets',data__employee_id=eid,data__date=when)),Decimal(0))
            if hours[eid]+existing>24:raise ValueError('Combined daily hours exceed 24.')
            prepared.append((key,d))
        for key,d in prepared:
            x=Record(organization=org,kind='timesheets',key=key,data=d,created_by=request.api_user).save();audit(request,'timesheets',x.id,'daily-attendance')
        return R.success(data={'created':len(prepared)},request=request)
    except (ValueError,TypeError,ValidationError,NotUniqueError) as e:return R.validation_error(message=str(e),request=request)

@api_login_required
@require_http_methods(['GET'])
def balances(request):
    org=request.api_organization;data={}
    if permitted(request,'payroll.read'):
        data['salary_outstanding']=money(sum((amount(run_data(r)['data']['outstanding_total']) for r in Record.objects(organization=org,kind='payruns',data__status__in=['approved','paid'])),Decimal(0)))
        data['advance_outstanding']=money(sum((amount(a['outstanding']) for e in Record.objects(organization=org,kind='employees') for a in advances(org,str(e.id))),Decimal(0)))
    if permitted(request,'labour.read') and permitted(request,'invoices.read'):
        from apps.sales.models import Customer,Invoice
        sites=[]
        for site in Record.objects(organization=org,kind='sites'):
            linked={tid for i in Invoice.objects(organization=org,workforce_billing_key__startswith=str(site.id)+':') for tid in i.workforce_timesheet_ids}
            work=list(Record.objects(organization=org,kind='timesheets',data__site_id=str(site.id),data__status='approved'))
            total=sum((amount(w.data['billable_units'])*amount(w.data['billing_rate']) for w in work),Decimal(0));unbilled=sum((amount(w.data['billable_units'])*amount(w.data['billing_rate']) for w in work if str(w.id) not in linked),Decimal(0))
            sites.append({'site_id':str(site.id),'site':site.data['name'],'customer_code':site.data.get('customer_code',''),'approved_work_value':money(total),'unbilled':money(unbilled)})
        data['sites']=sites;data['clients']=[]
        for c in Customer.objects(organization=org,code__in=list({s['customer_code'] for s in sites if s['customer_code']})):
            due=sum((Decimal(str(i.balance_due)) for i in Invoice.objects(organization=org,customer=c,status__in=['ISSUED','PARTIALLY_PAID'])),Decimal(0));data['clients'].append({'code':c.code,'customer':c.name,'outstanding':money(due)})
    if not data:return R.forbidden(message='Workforce access required.',request=request)
    return R.success(data=data,request=request)

@api_login_required
@require_http_methods(['POST'])
@write_lock
def labour_invoice(request):
    if not permitted(request,'labour.manage') or not permitted(request,'invoices.create'):return R.forbidden(message='Labour management and invoice creation permissions required.',request=request)
    from apps.sales.models import Invoice,InvoiceItem,Customer
    from apps.products.models import Category,Product
    org=request.api_organization
    try:
        p=payload(request);month=str(p.get('month',''));first,last=bounds(month);site=Record.objects(id=p.get('site_id'),organization=org,kind='sites').first()
        if not site:raise ValueError('Choose a site.')
        key=str(site.id)+':'+month;old=Invoice.objects(organization=org,workforce_billing_key=key).first()
        if old:return R.success(data={'invoice_number':old.invoice_number,'existing':True},request=request)
        customer=Customer.objects(organization=org,code=site.data.get('customer_code'),is_active=True).first()
        if not customer:raise ValueError('Link an active customer to this site.')
        work=[w for w in Record.objects(organization=org,kind='timesheets',data__site_id=str(site.id),data__status='approved') if first.isoformat()<=w.data['date']<=last.isoformat()]
        subtotal=Decimal(money(sum((amount(w.data['billable_units'])*amount(w.data['billing_rate']) for w in work),Decimal(0))))
        if subtotal<=0:raise ValueError('No approved billable work in this month.')
        rate=amount(p.get('tax_rate'),'Tax rate','100');tax=Decimal(money(subtotal*rate/100));total=subtotal+tax
        when=datetime.fromisoformat(p.get('invoice_date',''));due=datetime.fromisoformat(p['due_date']) if p.get('due_date') else None
        if due and due<when:raise ValueError('Due date precedes invoice date.')
        product=Product.objects(organization=org,sku='LABOUR-SERVICE',is_active=True).first()
        if not product:
            if not permitted(request,'products.create'):raise ValueError('Ask an administrator to create the LABOUR-SERVICE product.')
            category=Category.objects(organization=org,name='Labour services').first() or Category(organization=org,name='Labour services').save()
            product=Product(organization=org,sku='LABOUR-SERVICE',name='Labour supply services',category=category,unit='MONTH',item_type='service',hsn_code=p.get('hsn_code','')).save()
        if product.item_type!='service':raise ValueError('LABOUR-SERVICE must be migrated to a service master by the upgrade command.')
        from .billing import clean_details,settings
        line=InvoiceItem(product=product,item_type='service',item_name=product.name,hsn_code=p.get('hsn_code') or product.hsn_code,unit='MONTH',quantity=1,unit_price=subtotal,tax_rate=rate,line_subtotal=subtotal,line_tax=tax,line_total=total)
        details={**settings(org),**clean_details({**p['billing_details'],'site_name':site.data['name'],'service_from':first.isoformat(),'service_to':last.isoformat()},org,[line])} if 'billing_details' in p else {}
        selected=choice.get();number=allocate(org,'Invoice',selected.get('number','') if selected and selected.get('mode')=='manual' else None)
        if Invoice.objects(organization=org,invoice_number=number).first():raise ValueError('Number exists. Choose another number or higher sequence.')
        token=choice.set(None)
        try:
            invoice=Invoice(organization=org,invoice_number=number,workforce_billing_key=key,workforce_timesheet_ids=[str(w.id) for w in work],customer=customer,invoice_date=when,due_date=due,items=[line],billing_details=details,subtotal=subtotal,tax_amount=tax,total_amount=total,balance_due=total,billing_name=customer.name,billing_address=customer.billing_address,billing_state=customer.state,customer_gstin=customer.gstin,created_by=request.api_user,direct_entry=True,stock_review_required=False,notes='Labour services: '+site.data['name']+' / '+month+'. Approved timesheets linked; no stock movement.').save()
        finally:choice.reset(token)
        audit(request,'labour_invoice',invoice.id,'draft-from-work')
        return R.success(data={'invoice_number':invoice.invoice_number,'existing':False},request=request)
    except (ValueError,TypeError,ValidationError,NotUniqueError) as e:return R.validation_error(message=str(e),request=request)

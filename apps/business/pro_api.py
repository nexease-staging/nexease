"""Professional workflow endpoints; every lookup is scoped to the authenticated tenant."""
from datetime import date,datetime,time
from io import BytesIO,StringIO
from zipfile import ZipFile,ZIP_DEFLATED
import csv
from uuid import uuid4
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from mongoengine.errors import ValidationError,NotUniqueError
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from .models import BusinessRecord as Record
from .views import permitted,payload,validate,audit,serialize
from .automation import write_lock
from .books import ensure_accounts,sync_record,CATEGORIES,MODES

@api_login_required
@require_http_methods(['GET','POST'])
@write_lock
def modules(request):
    org=request.api_organization
    if not permitted(request,'organizations.update'):return R.forbidden(message='Administrator permission required.',request=request)
    try:
        if request.method=='POST':
            p=payload(request)
            for name in ['workforce','expenses','taxation','finance','barcode','ai','invoice_admin_only']:
                if name not in p:p[name]=getattr(org,name if name=='invoice_admin_only' else name+'_enabled',True)
                if not isinstance(p.get(name),bool):raise ValueError('Module switches must be true or false.')
            for name in ['workforce','expenses','taxation','finance','barcode','ai']:setattr(org,name+'_enabled',p[name])
            org.invoice_admin_only=p['invoice_admin_only'];org.save();audit(request,'modules',org.id,'configure')
        return R.success(data={**{k:getattr(org,k+'_enabled',True) for k in ['workforce','expenses','taxation','finance','barcode','ai']},'invoice_admin_only':getattr(org,'invoice_admin_only',True)},request=request)
    except (ValueError,ValidationError) as e:return R.validation_error(message=str(e),request=request)

@api_login_required
@require_http_methods(['GET'])
def payment_accounts(request):
    if not any(permitted(request,p) for p in ['expenses.read','payroll.read','accounting_reports.read']):return R.forbidden(message='Permission denied.',request=request)
    from apps.finance.models import ChartOfAccount
    return R.success(data={'records':[{'id':str(a.id),'data':{'name':a.account_name,'code':a.account_code}} for a in ChartOfAccount.objects(organization=request.api_organization,is_active=True,account_type__in=['ASSET','LIABILITY']).order_by('account_code')]},request=request)

@api_login_required
@require_http_methods(['POST'])
@write_lock
def bulk_assign(request):
    if not permitted(request,'labour.manage'):return R.forbidden(message='Permission denied.',request=request)
    try:
        p=payload(request);org=request.api_organization;site=Record.objects(organization=org,kind='sites',id=p.get('site_id')).first()
        if not site or not site.data.get('active',True):raise ValueError('Choose an active site.')
        rows=p.get('rows',[])
        if not isinstance(rows,list) or not 1<=len(rows)<=500:raise ValueError('Select between 1 and 500 employees.')
        prepared=[];seen=set()
        for row in rows:
            eid=row.get('employee_id')
            if eid in seen:raise ValueError('An employee was selected twice.')
            seen.add(eid)
            e=Record.objects(organization=org,kind='employees',id=eid).first()
            if not e or not e.data.get('active') or e.data.get('employment_type')=='inhouse':raise ValueError('Select active site workers.')
            d={'employee_id':eid,'site_id':str(site.id),'start_date':p.get('start_date'),'end_date':p.get('end_date'),'shift':p.get('shift'),'role':row.get('role',''),'billing_rate':row.get('billing_rate') if row.get('billing_rate') not in (None,'') else site.data.get('billing_rate','0'),'status':'active'}
            if d['start_date']<e.data['joining_date'] or (e.data.get('end_date') and d['end_date']>e.data['end_date']):raise ValueError('Assignment is outside employment dates for '+e.data['name'])
            old=Record.objects(organization=org,kind='assignments',data__employee_id=eid,data__site_id=str(site.id),data__start_date=d['start_date'],data__end_date=d['end_date'],data__shift=d['shift'],data__status='active').first()
            clean=validate('assignments',d,org,str(old.id) if old else None)
            if old:
                if old.data!=clean:raise ValueError('An existing assignment differs. Edit it separately.')
                continue
            prepared.append(clean)
        count=0
        for d in prepared:
            x=Record(organization=org,kind='assignments',key=uuid4().hex,data=d,created_by=request.api_user).save();audit(request,'assignments',x.id,'bulk-create');count+=1
        return R.success(data={'created':count,'message':f'{count} assignments created. Existing identical assignments were skipped.'},request=request)
    except (ValueError,TypeError,ValidationError,NotUniqueError) as e:return R.validation_error(message=str(e),request=request)

@api_login_required
@require_http_methods(['GET','POST'])
@write_lock
def books_sync(request):
    if not permitted(request,'organizations.update') or not permitted(request,'journal_entries.post'):return R.forbidden(message='Administrator and journal posting permissions required.',request=request)
    from apps.finance.models import JournalEntry
    org=request.api_organization
    try:
        if request.method=='POST':
            p=payload(request);ensure_accounts(org,request.api_user)
            if p.get('setup_only'):return R.success(data={'message':'System accounts are ready.'},request=request)
            if p.get('confirm') is not True:raise ValueError('Review the source list and confirm posting.')
            ids=p.get('record_ids',[])
            if not isinstance(ids,list) or len(ids)>500:raise ValueError('Select at most 500 records.')
            done=[];errors=[]
            for id in ids:
                x=Record.objects(organization=org,id=id,kind__in=['advances','expenses','payruns']).first()
                if not x:errors.append({'id':id,'error':'Record not found.'});continue
                try:sync_record(x,request.api_user);done.append(id);audit(request,'books_sync',id,'sync')
                except Exception as exc:errors.append({'id':id,'error':str(exc)})
            return R.success(data={'posted':done,'errors':errors},request=request)
        rows=[]
        for x in Record.objects(organization=org,kind__in=['advances','expenses','payruns']).order_by('-created_at').limit(1000):
            if x.kind=='payruns' and x.data.get('status') not in ('approved','paid'):continue
            types={'advances':'EMPLOYEE_ADVANCE','expenses':'DAILY_EXPENSE','payruns':'PAYROLL'}
            j=JournalEntry.objects(organization=org,source_type=types[x.kind],source_id=str(x.id),status='POSTED').first()
            expected=len(x.data.get('payments',[])) if x.kind=='payruns' else 0
            payments=JournalEntry.objects(organization=org,source_type='SALARY_PAYMENT',source_id__startswith=str(x.id)+':',status='POSTED').count() if expected else 0
            no_value=x.kind=='payruns' and not expected and all(float(r['result'].get('gross','0'))==0 and float(r['result'].get('employer_pf','0'))==0 and float(r['result'].get('employer_esi','0'))==0 for r in x.data.get('rows',[]))
            if no_value:continue
            rows.append({'id':str(x.id),'kind':x.kind,'reference':x.data.get('reference',x.key),'date':x.data.get('date',x.key),'posted':bool(j),'pending':not j or payments<expected})
        return R.success(data={'records':rows},request=request)
    except (ValueError,TypeError,ValidationError) as e:return R.validation_error(message=str(e),request=request)

@api_login_required
@require_http_methods(['POST'])
def invoice_descriptions(request,invoice_id):
    if not permitted(request,'invoices.issue'):return R.forbidden(message='Invoice issue permission required.',request=request)
    from .enhancements import is_admin
    if getattr(request.api_organization,'invoice_admin_only',True) and not is_admin(request.api_user):return R.forbidden(message='Only a system Admin can edit invoice descriptions.',request=request)
    from apps.sales.models import Invoice
    try:
        inv=Invoice.objects(id=invoice_id,organization=request.api_organization).first()
        if not inv:return R.not_found(message='Invoice not found.',request=request)
        if inv.status not in ('DRAFT','ISSUED','PARTIALLY_PAID','PAID'):raise ValueError('This invoice cannot be edited.')
        if inv.status!='DRAFT' and not is_admin(request.api_user):return R.forbidden(message='Only a system Admin can edit an issued invoice.',request=request)
        before=[{'description':i.description,'show':i.show_description} for i in inv.items]
        p=payload(request);items=p.get('items',[])
        if not isinstance(items,list) or len(items)!=len(inv.items):raise ValueError('Reload the invoice; item count changed.')
        for item,d in zip(inv.items,items):
            if not isinstance(d,dict) or not isinstance(d.get('description',''),str) or len(d.get('description',''))>2000 or not isinstance(d.get('show',False),bool):raise ValueError('Invalid description. Maximum 2000 characters per line.')
            item.description=d.get('description','').strip();item.show_description=d.get('show',False)
        updated=Invoice.objects(id=inv.id,organization=request.api_organization,status=inv.status,updated_at=inv.updated_at).update_one(set__items=inv.items,set__updated_at=datetime.utcnow())
        if not updated:raise ValueError('Invoice changed. Reload before saving.')
        from .models import BusinessAudit
        BusinessAudit(organization=request.api_organization,actor=request.api_user,kind='invoice_description',record_id=str(inv.id),action='update',details={'before':before,'after':items}).save()
        return R.success(data={'saved':True},request=request)
    except (ValueError,ValidationError) as e:return R.validation_error(message=str(e),request=request)

def csv_bytes(rows):
    s=StringIO();writer=csv.writer(s)
    for row in rows:writer.writerow([("'"+str(v) if isinstance(v,str) and v.startswith(('=','+','-','@')) else v) for v in row])
    return ('\ufeff'+s.getvalue()).encode('utf-8')

@api_login_required
@require_http_methods(['GET'])
def accountant_export(request):
    if not all(permitted(request,p) for p in ['accounting_reports.read','general_ledger.read','invoices.read','bills.read','payroll.read','expenses.read']):return R.forbidden(message='Sales, purchase, payroll, expense and accounting report access required for this complete export.',request=request)
    from apps.sales.models import Invoice,CustomerPayment,CreditNote
    from apps.purchasing.models import VendorBill,SupplierPayment,VendorDebitNote
    from apps.finance.models import JournalEntry,ChartOfAccount
    try:
        start=date.fromisoformat(request.GET.get('from',''));end=date.fromisoformat(request.GET.get('to',''))
        if end<start:raise ValueError('End date precedes start date.')
        lo=datetime.combine(start,time.min);hi=datetime.combine(end,time.max);org=request.api_organization;sheets={}
        for title,model,num,dt,party in [('Sales',Invoice,'invoice_number','invoice_date','customer'),('Purchases',VendorBill,'bill_number','bill_date','supplier'),('Sales_credit_notes',CreditNote,'credit_note_number','credit_note_date','customer'),('Purchase_debit_notes',VendorDebitNote,'debit_note_number','debit_note_date','supplier')]:
            if dt not in model._fields:dt=next((x for x in ['note_date','issue_date','created_at'] if x in model._fields),'created_at')
            rows=[['ID','Document','Date','Status','Party','GSTIN','SKU','Item','Quantity','Rate','Tax rate','Line taxable','Line tax','Line total','Document total','Balance due']]
            for x in model.objects(organization=org,**{dt+'__gte':lo,dt+'__lte':hi}).order_by(dt):
                who=getattr(x,party,None)
                for item in getattr(x,'items',[]):
                    prod=getattr(item,'product',None)
                    rows.append([str(x.id),getattr(x,num,''),getattr(x,dt).isoformat(),x.status,getattr(x,'billing_name',None) or getattr(x,'supplier_name',None) or getattr(who,'name',''),getattr(x,'customer_gstin',None) or getattr(x,'supplier_gstin',None) or getattr(who,'gstin',''),getattr(prod,'sku',''),getattr(prod,'name',''),str(getattr(item,'quantity',0)),str(getattr(item,'unit_price',0)),str(getattr(item,'tax_rate',0)),str(getattr(item,'line_subtotal',0)),str(getattr(item,'line_tax',0)),str(getattr(item,'line_total',0)),str(getattr(x,'total_amount',0)),str(getattr(x,'balance_due',0))])
            sheets[title]=rows
        for title,model in [('Customer_payments',CustomerPayment),('Supplier_payments',SupplierPayment)]:
            rows=[['Payment','Date','Amount','Reference']]
            dt='payment_date' if 'payment_date' in model._fields else 'created_at'
            for x in model.objects(organization=org,**{dt+'__gte':lo,dt+'__lte':hi}):rows.append([getattr(x,'payment_number',''),getattr(x,dt).isoformat(),str(getattr(x,'amount',getattr(x,'total_amount',0))),getattr(x,'reference_number','')])
            sheets[title]=rows
        gl=[['Date','Journal','Source','Source ID','Account code','Account','Description','Debit','Credit']];totals={}
        for j in JournalEntry.objects(organization=org,status__in=['POSTED','REVERSED'],journal_date__lte=hi).order_by('journal_date'):
            for l in j.lines:
                k=str(l.account.id);v=totals.setdefault(k,[l.account,0,0,0,0])
                if j.journal_date<lo:v[1]+=l.debit;v[2]+=l.credit
                else:
                    v[3]+=l.debit;v[4]+=l.credit;gl.append([j.journal_date.isoformat(),j.journal_number,j.source_type,j.source_id,l.account.account_code,l.account.account_name,l.description,str(l.debit),str(l.credit)])
        sheets['General_ledger']=gl
        sheets['Trial_balance']=[['Account','Name','Opening debit','Opening credit','Period debit','Period credit','Closing debit','Closing credit']]
        for a,od,oc,dr,cr in sorted(totals.values(),key=lambda v:v[0].account_code):
            opening=od-oc;closing=opening+dr-cr;sheets['Trial_balance'].append([a.account_code,a.account_name,str(max(opening,0)),str(max(-opening,0)),str(dr),str(cr),str(max(closing,0)),str(max(-closing,0))])
        for kind in ['expenses','advances','payruns']:
            data=[]
            for x in Record.objects(organization=org,kind=kind):
                when=x.data.get('date',x.key+'-01' if kind=='payruns' else '')
                if start.isoformat()<=when<=end.isoformat():data.append(x)
            if kind=='payruns':
                rows=[['Month','Status','Employee code','Employee','Gross','Deductions','Net','Paid','Outstanding']]
                from .automation import run_data
                for x in data:
                    for r in run_data(x)['data']['rows']:rows.append([x.key,x.data['status'],r['employee'].get('code'),r['employee']['name'],r['result']['gross'],r['result']['deductions'],r['result']['net'],r['paid'],r['outstanding']])
            else:
                fields=list(__import__('apps.business.schema',fromlist=['SCHEMAS']).SCHEMAS[kind]['fields']);rows=[['ID']+fields]+[[str(x.id)]+[x.data.get(k,'') for k in fields] for x in data]
            sheets[kind]=rows
        out=BytesIO()
        with ZipFile(out,'w',ZIP_DEFLATED) as z:
            for name,rows in sheets.items():z.writestr(name+'.csv',csv_bytes(rows))
            z.writestr('READ_ME.txt','Sales and purchase registers include drafts/cancelled documents with explicit status. Only posted/reversed-original journals and their posted reversal entries affect GL/TB.\nAmounts are transaction values, not filed tax returns. Expense amounts include tax and do not claim ITC.\nCheck books sync for historical/pending workforce records. Purchase orders are commitments, not expenses.\nPayment account defaults: Cash, Bank control, or Credit card payable. No automatic bank statement lines are fabricated.\nPayroll deductions remain in a control liability for accountant allocation and remittance.\n')
        response=HttpResponse(out.getvalue(),content_type='application/zip');response['Content-Disposition']='attachment; filename="NexEase-Accountant-Pack.zip"';return response
    except (ValueError,ValidationError) as e:return R.validation_error(message=str(e),request=request)

@api_login_required
@require_http_methods(['GET'])
def lookup(request):
    from mongoengine.queryset.visitor import Q
    from apps.products.models import Product
    from apps.sales.models import Customer
    from apps.purchasing.models import Supplier
    kind=request.GET.get('kind');models={'products':Product,'customers':Customer,'suppliers':Supplier}
    if kind not in models:return R.validation_error(message='Unknown lookup.',request=request)
    if not permitted(request,kind+'.read'):return R.forbidden(message='Permission denied.',request=request)
    q=request.GET.get('q','').strip()[:100];code='sku' if kind=='products' else 'code'
    query=models[kind].objects(organization=request.api_organization,is_active=True)
    if q:query=query.filter(Q(name__icontains=q)|Q(**{code+'__icontains':q})|Q(**{('barcode' if kind=='products' else 'gstin')+'__icontains':q}))
    rows=[]
    for x in query.order_by('name').limit(40):
        d={'id':str(x.id),'name':x.name,'code':getattr(x,code)}
        fields=['unit','cost_price','selling_price','item_type','hsn_code'] if kind=='products' else ['phone','email','billing_address','address','gstin','state']
        d.update({f:str(getattr(x,f,'') or '') for f in fields});rows.append(d)
    return R.success(data={'records':rows},request=request)

@api_login_required
@require_http_methods(['GET'])
def expenses_export(request):
    if not permitted(request,'expenses.read'):return R.forbidden(message='Expense read permission required.',request=request)
    from .schema import SCHEMAS
    fields=list(SCHEMAS['expenses']['fields']);rows=[[SCHEMAS['expenses']['fields'][k]['label'] for k in fields]]
    for x in Record.objects(organization=request.api_organization,kind='expenses').order_by('data.date'):rows.append([x.data.get(k,'') for k in fields])
    response=HttpResponse(csv_bytes(rows),content_type='text/csv; charset=utf-8');response['Content-Disposition']='attachment; filename="NexEase-Expenses.csv"';return response

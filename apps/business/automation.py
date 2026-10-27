"""Workforce source aggregation, approval locks and balance calculations."""
from datetime import date,timedelta,datetime
from decimal import Decimal
from functools import wraps
from uuid import uuid4
import calendar
from mongoengine.connection import get_db
from pymongo.errors import DuplicateKeyError
from .models import BusinessRecord as Record
from .payroll import amount,money,calculate
from apps.core.services.api_response_service import APIResponseService as R

def write_lock(view):
    @wraps(view)
    def wrapped(request,*args,**kwargs):
        if request.method=='GET':return view(request,*args,**kwargs)
        collection=get_db().nexease_workforce_locks;key=str(request.api_organization.id);token=uuid4().hex
        try:collection.insert_one({'_id':key,'token':token,'at':datetime.utcnow()})
        except DuplicateKeyError:return R.validation_error(message='Another workforce update is running. Retry shortly. A lock left by a stopped server requires administrator recovery.',request=request)
        try:return view(request,*args,**kwargs)
        finally:collection.delete_one({'_id':key,'token':token})
    return wrapped

def bounds(month):
    first=date.fromisoformat(month+'-01');return first,first.replace(day=calendar.monthrange(first.year,first.month)[1])

def advances(org,eid,through='9999-12-31'):
    used={}
    for run in Record.objects(organization=org,kind='payruns',data__status__in=['approved','paid']):
        for row in run.data.get('rows',[]):
            if row['employee_id']==eid:
                for a in row.get('advance_allocations',[]):used[a['id']]=used.get(a['id'],Decimal(0))+amount(a['amount'])
    result=[]
    for a in Record.objects(organization=org,kind='advances',data__employee_id=eid).order_by('data.date','id'):
        if a.data['date']>through:continue
        remaining=amount(a.data['amount'])-amount(a.data.get('recovered',0))-used.get(str(a.id),Decimal(0))
        if remaining<0:raise ValueError('Advance is over-recovered: '+a.data['reference'])
        result.append({'id':str(a.id),'reference':a.data['reference'],'outstanding':money(remaining)})
    return result

def payrow(org,employee,month,policy,mode):
    first,last=bounds(month);eid=str(employee.id)
    inp=Record.objects(organization=org,kind='attendance',key=eid+':'+month).first()
    d=dict(inp.data if inp else {});source={'mode':mode}
    if mode=='manual':
        if not inp:raise ValueError('Missing monthly inputs: '+employee.data['name'])
    elif mode=='automatic':
        if employee.data['basis']=='piece':raise ValueError('Piece-rate payroll needs manual monthly units: '+employee.data['name'])
        if (employee.data.get('pf_member') or employee.data.get('esi_member')) and not inp:raise ValueError('Enter reviewed contribution wage bases in monthly inputs for '+employee.data['name'])
        work=[w for w in Record.objects(organization=org,kind='timesheets',data__employee_id=eid,data__status='approved').order_by('id') if first.isoformat()<=w.data['date']<=last.isoformat()]
        days={w.data['date'] for w in work if amount(w.data['hours'])+amount(w.data.get('overtime_hours',0))>0}
        start=max(first,date.fromisoformat(employee.data['joining_date']));end=min(last,date.fromisoformat(employee.data['end_date'])) if employee.data.get('end_date') else last
        if any(not start.isoformat()<=day<=end.isoformat() for day in days):raise ValueError('Work outside employment dates: '+employee.data['name'])
        paid=set()
        for leave in Record.objects(organization=org,kind='leave_requests',data__employee_id=eid,data__status='approved',data__leave_type='paid'):
            lo=date.fromisoformat(leave.data['start_date']);hi=date.fromisoformat(leave.data['end_date'])
            if lo>end or hi<start:continue
            if amount(leave.data['days'])!=(hi-lo).days+1:raise ValueError('Partial-day paid leave needs manual monthly inputs.')
            day=max(lo,start)
            while day<=min(hi,end):paid.add(day.isoformat());day+=timedelta(days=1)
        if days&paid:raise ValueError('Work overlaps paid leave: '+employee.data['name'])
        d.update(employee_id=eid,month=month,period_days=str(last.day),paid_days=str(len(days|paid)),hours=money(sum((amount(w.data['hours']) for w in work),Decimal(0))),overtime_hours=money(sum((amount(w.data.get('overtime_hours',0)) for w in work),Decimal(0))),advance_recovery='0')
        source.update(timesheet_ids=[str(w.id) for w in work],paid_leave_days=len(paid),worked_days=len(days))
        d['advance_recovery']=money(min(amount(calculate(employee.data,d,policy)['net']),sum((amount(a['outstanding']) for a in advances(org,eid,last.isoformat())),Decimal(0))))
    else:raise ValueError('Choose automatic or manual payroll inputs.')
    remaining=amount(d.get('advance_recovery',0));allocations=[]
    for a in advances(org,eid,last.isoformat()):
        value=min(remaining,amount(a['outstanding']))
        if value:allocations.append({'id':a['id'],'amount':money(value)});remaining-=value
    if remaining:raise ValueError('Advance deduction exceeds recorded advances: '+employee.data['name'])
    return {'employee_id':eid,'employee':employee.data,'inputs':d,'result':calculate(employee.data,d,policy),'advance_allocations':allocations,'source':source}

def run_data(run):
    d=dict(run.data);payments=d.get('payments',[]);rows=[]
    for original in d.get('rows',[]):
        row=dict(original);paid=sum((amount(p['amount']) for p in payments if p['employee_id']==row['employee_id']),Decimal(0))
        if d['status']=='paid' and not payments:paid=amount(row['result']['net'])
        row['paid']=money(paid);row['outstanding']=money(max(Decimal(0),amount(row['result']['net'])-paid)) if d['status'] in ('approved','paid') else '0.00'
        row['advance_outstanding']=money(sum((amount(a['outstanding']) for a in advances(run.organization,row['employee_id'])),Decimal(0)));rows.append(row)
    d.update(rows=rows,outstanding_total=money(sum((amount(r['outstanding']) for r in rows),Decimal(0))))
    return {'id':str(run.id),'key':run.key,'revision':run.revision,'data':d,'created_at':run.created_at.isoformat()}

def guard_source(kind,clean,org,record_id):
    if kind not in ('timesheets','leave_requests','advances'):return
    old=Record.objects(id=record_id,organization=org,kind=kind).first() if record_id else None
    ids={clean['employee_id'],old.data['employee_id'] if old else clean['employee_id']}
    for run in Record.objects(organization=org,kind='payruns',data__status__in=['approved','paid']):
        for row in run.data.get('rows',[]):
            if row['employee_id'] not in ids:continue
            if kind=='advances' and any(a['id']==str(record_id) for a in row.get('advance_allocations',[])):raise ValueError('Advance is linked to approved payroll and cannot be edited.')
            if kind!='advances' and row.get('source',{}).get('mode')=='automatic':
                for d in [clean]+([old.data] if old else []):
                    if d.get('date',d.get('start_date',''))[:7]<=run.key<=d.get('date',d.get('end_date',''))[:7]:raise ValueError('This month is locked by approved payroll.')
    if kind=='timesheets':
        from apps.sales.models import Invoice
        if Invoice.objects(organization=org,workforce_billing_key=clean['site_id']+':'+clean['date'][:7]).first() or (record_id and Invoice.objects(organization=org,workforce_timesheet_ids=str(record_id)).first()):raise ValueError('This site/month is linked to a client invoice.')

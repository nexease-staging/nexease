from datetime import datetime
from decimal import Decimal
from django.views.decorators.http import require_http_methods
from mongoengine.errors import ValidationError,NotUniqueError
from apps.core.api.decorators import api_login_required
from .views import payload,permitted,audit
from .models import BusinessRecord as Record
from .payroll import amount,money
from .automation import bounds,payrow,run_data,write_lock
from apps.core.services.api_response_service import APIResponseService as R

def applicable_policy(org,first,last):
    policies=[p.data for p in Record.objects(organization=org,kind='policy') if p.data['effective_from']<=first.isoformat() and p.data['effective_to']>=last.isoformat()]
    return policies[0] if len(policies)==1 else {}

@api_login_required
@require_http_methods(['GET','POST'])
@write_lock
def payroll(request):
    if not permitted(request,'payroll.read' if request.method=='GET' else 'payroll.manage'):return R.forbidden(message='Permission denied.',request=request)
    org=request.api_organization
    try:
        if request.method=='GET':return R.success(data={'records':[run_data(r) for r in Record.objects(organization=org,kind='payruns').order_by('-key').limit(120)]},request=request)
        p=payload(request);month=p.get('month','');first,last=bounds(month);action=p.get('action','calculate');run=Record.objects(organization=org,kind='payruns',key=month).first()
        if action in ('approve','payment','paid'):
            from .books import ensure_accounts,payment_account
            ensure_accounts(org,request.api_user)
        if action=='calculate':
            if run and run.data['status']!='draft':raise ValueError('Approved payroll is locked.')
            policy=applicable_policy(org,first,last)
            employees=[e for e in Record.objects(organization=org,kind='employees').order_by('key') if (e.data.get('active') or e.data.get('end_date')) and e.data['joining_date']<=last.isoformat() and (not e.data.get('end_date') or e.data['end_date']>=first.isoformat())]
            if not employees:raise ValueError('No employees for this month.')
            rows=[payrow(org,e,month,policy,p.get('mode','manual')) for e in employees]
            d={'month':month,'status':'draft','policy':policy,'rows':rows,'net_total':money(sum((amount(r['result']['net']) for r in rows),Decimal(0))),'created_by':str(request.api_user.id)}
            expected='draft'
        elif action=='approve':
            if not run or run.data['status']!='draft':raise ValueError('Calculate a draft first.')
            if applicable_policy(org,first,last)!=run.data['policy']:raise ValueError('Policy changed. Recalculate payroll.')
            for row in run.data['rows']:
                e=Record.objects(id=row['employee_id'],organization=org,kind='employees').first()
                if not e:raise ValueError('Employee missing. Recalculate payroll.')
                fresh=payrow(org,e,month,run.data['policy'],row.get('source',{}).get('mode','manual'))
                if ('source' in row and fresh['source']!=row['source']) or any(fresh.get(k)!=row.get(k) for k in ('employee','inputs','result')) or ('advance_allocations' in row and fresh['advance_allocations']!=row['advance_allocations']):raise ValueError('Source records changed. Refresh the draft before approval.')
                row['advance_allocations']=fresh['advance_allocations']
            d={**run.data,'status':'approved','approved_by':str(request.api_user.id),'approved_at':datetime.utcnow().isoformat()};expected='draft'
        elif action in ('payment','paid'):
            if not run or run.data['status']!='approved':raise ValueError('Approve payroll before recording payment.')
            payment_mode=p.get('payment_mode') or 'Bank transfer';payment_ac=p.get('payment_account','')
            payment_account(org,payment_mode,payment_ac)
            paid_date=p.get('payment_date') or datetime.utcnow().date().isoformat()
            from datetime import date
            date.fromisoformat(paid_date)
            if paid_date < first.isoformat():raise ValueError('Salary payment date precedes the payroll month.')
            reference=str(p.get('payment_reference','')).strip()
            if not reference or len(reference)>200:raise ValueError('Enter a payment reference.')
            payments=list(run.data.get('payments',[]));remaining=run_data(run)['data']['rows']
            if any(x['reference']==reference for x in payments):raise ValueError('Payment reference already recorded in this payroll.')
            if action=='paid':
                if payments:raise ValueError('Use individual payments to settle remaining balances.')
                payments=[{'employee_id':r['employee_id'],'amount':r['outstanding'],'reference':reference,'date':paid_date,'payment_mode':payment_mode,'payment_account':payment_ac} for r in remaining if amount(r['outstanding'])]
            else:
                eid=str(p.get('employee_id',''));row=next((r for r in remaining if r['employee_id']==eid),None);value=amount(p.get('amount'))
                if not row or value<=0 or value>amount(row['outstanding']):raise ValueError('Payment must be positive and no greater than this employee’s salary balance.')
                payments.append({'employee_id':eid,'amount':money(value),'reference':reference,'date':paid_date,'payment_mode':payment_mode,'payment_account':payment_ac})
            d={**run.data,'payments':payments};expected='approved'
            if sum((amount(x['amount']) for x in payments),Decimal(0))==amount(run.data['net_total']):d.update(status='paid',paid_at=datetime.utcnow().isoformat(),paid_by=str(request.api_user.id))
        else:raise ValueError('Unknown payroll action.')
        if run:
            run=Record.objects(id=run.id,organization=org,revision=p.get('revision'),data__status=expected).modify(new=True,set__data=d,inc__revision=1)
            if not run:raise ValueError('Payroll changed. Reload first.')
        else:run=Record(organization=org,kind='payruns',key=month,data=d,created_by=request.api_user).save()
        audit(request,'payruns',run.id,action)
        if action!='calculate':
            from .books import sync_record
            try:sync_record(run,request.api_user)
            except Exception as exc:return R.validation_error(message='Payroll saved but books sync needs attention. Do not repeat a payment. Retry pending books sync in Settings. '+str(exc),request=request)
        return R.success(data={'record':run_data(run)},request=request)
    except (ValueError,TypeError,ValidationError,NotUniqueError) as e:return R.validation_error(message=str(e),request=request)

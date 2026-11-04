"""Employee payable reporting and worker visibility; no duplicate liabilities."""
from datetime import datetime, timedelta
from decimal import Decimal
from django.views.decorators.http import require_GET
from mongoengine.connection import get_db
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from .models import BusinessRecord
from .views import permitted
from .payroll import money

@api_login_required
@require_GET
def employee_payables(request):
    if not permitted(request,'payroll.read'):return R.forbidden(message='Payroll read permission required.',request=request)
    rows=[]
    for run in BusinessRecord.objects(organization=request.api_organization,kind='payruns',data__status__in=['approved','paid']).only('key','data'):
        payments=run.data.get('payments',[])
        for row in run.data.get('rows',[]):
            net=Decimal(str(row['result']['net']))
            paid=sum((Decimal(str(p['amount'])) for p in payments if p['employee_id']==row['employee_id']),Decimal(0))
            if run.data['status']=='paid' and not payments:paid=net
            balance=max(Decimal(0),net-paid)
            if balance:rows.append({'employee_id':row['employee_id'],'name':row['employee']['name'],'month':run.key,'net':money(net),'paid':money(paid),'outstanding':money(balance)})
    return R.success(data={'rows':rows,'total':money(sum((Decimal(x['outstanding']) for x in rows),Decimal(0)))},request=request)

@api_login_required
@require_GET
def worker_health(request):
    # Only expose this tenant/user's queue totals, never another tenant's jobs.
    from apps.core.background_job_models import BackgroundJob
    q=BackgroundJob.objects(organization=request.api_organization,created_by=request.api_user,job_type='DOCUMENT_EMAIL')
    oldest=q.filter(status='PENDING').order_by('created_at').only('created_at').first()
    heartbeat=get_db().nexease_worker_health.find_one({'_id':'background'})
    active=bool(heartbeat and heartbeat['at']>datetime.utcnow()-timedelta(minutes=6))
    return R.success(data={'worker_active':active,'pending':q.filter(status='PENDING').count(),'failed':q.filter(status='FAILED').count(),'oldest_pending':oldest.created_at.isoformat() if oldest else None},request=request)

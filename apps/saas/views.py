import os,json,time,hmac,hashlib,secrets
from datetime import datetime,timedelta
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password,make_password
from mongoengine.errors import ValidationError
from mongoengine.queryset.visitor import Q
from mongoengine.connection import get_db
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.business.views import payload,permitted
from apps.organizations.models import Organization
from apps.accounts.models import User
from .models import Plan,Membership,Checkout,PlatformOwner,OwnerAudit
from .security import owner_required,current_owner,rate,verify_totp,log
from .entitlements import seed,state,usage,resource_count,org_lock,DEFAULTS
from . import gateway

def plan_json(p):return dict(code=p.code,name=p.name,price=p.price_paise/100,limits=p.limits,features=p.features,published=p.published)
def membership_json(m):return None if not m else dict(plan=m.plan,status=('expired' if m.end<=datetime.utcnow() and m.status in ('active','trial') else m.status),start=m.start.isoformat(),end=m.end.isoformat(),suspended=m.suspended,limits=m.limits,features=m.features,subscription_id=m.subscription_id)
def json_safe(obj):return json.loads(json.dumps(obj,default=str))

@require_http_methods(['GET'])
def plans(request):
 seed();return R.success(data={'plans':[plan_json(p) for p in Plan.objects.order_by('price_paise')],'payments_enabled':gateway.ready(),'price_note':'Per organization/month. Displayed checkout amount is the final amount; applicable tax is included.','terms_url':os.getenv('BILLING_TERMS_URL',''),'privacy_url':os.getenv('PRIVACY_URL',''),'refund_url':os.getenv('REFUND_POLICY_URL','')},request=request)

@api_login_required
@require_http_methods(['GET','POST'])
def subscription(request):
 org=request.api_organization;m=state(org)
 try:
  if request.method=='POST':
   if not permitted(request,'organizations.update'):return R.forbidden(message='Organization administrator required.',request=request)
   p=payload(request);action=p.get('action')
   if action=='checkout':
    code=p.get('plan');plan=Plan.objects(code=code,published=True,gateway_mode=gateway.mode()).first()
    if not plan:raise ValueError('Plan checkout has not been published by the owner.')
    if p.get('accept_terms') is not True:raise ValueError('Accept the subscription terms and recurring charge before checkout.')
    with org_lock(org.id):
     m=state(org)
     if m and m.status=='active' and m.gateway_mode==gateway.mode() and m.end>datetime.utcnow():raise ValueError('An active paid subscription already exists. Cancel renewal and change plans after its paid period ends; contact owner for assistance.')
     for k in ['users','products','warehouses','employees']:
      if resource_count(org,k)>plan.limits[k]:raise ValueError('Current '+k+' exceed this plan. Reduce them or choose a larger plan.')
     existing=Checkout.objects(organization_id=str(org.id),mode=gateway.mode(),status__in=['created','authenticated','pending','halted']).order_by('-created_at').first()
     if existing:
      if existing.plan!=code:raise ValueError('An unfinished checkout exists. Cancel it before choosing another plan.')
      c=existing
     else:
      result=gateway.api('subscriptions',{'plan_id':plan.razorpay_plan_id,'total_count':120,'quantity':1,'customer_notify':1,'notes':{'organization_id':str(org.id),'plan':code}})
      c=Checkout(subscription_id=result['id'],organization_id=str(org.id),plan=code,price_paise=plan.price_paise,features=plan.features,limits=plan.limits,mode=gateway.mode()).save()
     return R.success(data={'subscription_id':c.subscription_id,'key_id':os.getenv('RAZORPAY_KEY_ID'),'name':plan.name,'amount':c.price_paise},request=request)
   sid=p.get('subscription_id') or (m.subscription_id if m else '')
   c=Checkout.objects(subscription_id=sid,organization_id=str(org.id),mode=gateway.mode()).first()
   if not c:raise ValueError('Subscription not found.')
   if action=='verify':
    pid=str(p.get('razorpay_payment_id',''));signature=str(p.get('razorpay_signature',''))
    expected=hmac.new(os.environ.get('RAZORPAY_KEY_SECRET','').encode(),(pid+'|'+sid).encode(),hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(signature,expected):raise ValueError('Invalid payment signature.')
    return R.success(data=gateway.reconcile(sid,pid),request=request)
   if action=='refresh':return R.success(data=gateway.reconcile(sid),request=request)
   if action=='cancel':
    remote=gateway.api('subscriptions/'+sid)
    later=remote.get('status')=='active'
    gateway.api('subscriptions/'+sid+'/cancel',{'cancel_at_cycle_end':1 if later else 0})
    c.status='cancel_scheduled' if later else 'cancelled';c.save()
    return R.success(data={'message':'Renewal cancelled. Paid access remains until period end.' if later else 'Unfinished subscription cancelled.'},request=request)
   raise ValueError('Unknown subscription action.')
  recent=Checkout.objects(organization_id=str(org.id)).order_by('-created_at').first()
  return R.success(data={'membership':membership_json(m),'usage':usage(org,m),'resources':{k:resource_count(org,k) for k in ['users','products','warehouses','employees']},'pending_subscription_id':recent.subscription_id if recent and recent.status not in ('cancelled','completed','expired') else '', 'payments':json_safe(list(get_db().saas_payments.find({'organization_id':str(org.id),'mode':gateway.mode()},{'_id':0}).sort('paid_at',-1).limit(100))),'can_manage':permitted(request,'organizations.update')},request=request)
 except (ValueError,ValidationError) as e:return R.validation_error(message=str(e),request=request)

@csrf_exempt
@require_http_methods(['POST'])
def webhook(request):
 if not gateway.ready():return JsonResponse({'error':'disabled'},status=503)
 if len(request.body)>1000000:return JsonResponse({'error':'payload too large'},status=413)
 sig=request.headers.get('X-Razorpay-Signature','');expected=hmac.new(os.environ['RAZORPAY_WEBHOOK_SECRET'].encode(),request.body,hashlib.sha256).hexdigest()
 if not hmac.compare_digest(sig,expected):return JsonResponse({'error':'invalid signature'},status=400)
 try:
  p=json.loads(request.body);entity=p.get('payload',{});sub=entity.get('subscription',{}).get('entity',{});sid=sub.get('id')
  if not sid:
   payment=entity.get('payment',{}).get('entity',{})
   if not payment and entity.get('refund'):payment=gateway.api('payments/'+entity['refund']['entity']['payment_id'])
   if payment.get('invoice_id'):sid=gateway.api('invoices/'+payment['invoice_id']).get('subscription_id')
  if sid and Checkout.objects(subscription_id=sid,mode=gateway.mode()).first():gateway.reconcile(sid)
  # Activation is idempotent and reads provider state, so out-of-order events are safe.
  return JsonResponse({'received':True})
 except Exception:return JsonResponse({'error':'reconciliation failed; retry required'},status=503)

@require_http_methods(['GET','POST'])
def owner_session(request):
 if request.method=='GET':
  o=current_owner(request);return R.success(data={'authenticated':bool(o),'email':o.email if o else ''},request=request)
 try:
  p=payload(request)
  if p.get('action')=='logout':request.session.pop('nexease_owner',None);return R.success(data={},request=request)
  email=str(p.get('email','')).strip().lower();rate('owner-ip:'+request.META.get('REMOTE_ADDR',''),20);rate('owner-email:'+hashlib.sha256(email.encode()).hexdigest(),8)
  o=PlatformOwner.objects(email=email,active=True).first()
  valid=check_password(str(p.get('password','')),o.password if o else make_password('unused'))
  if not o or not valid or not verify_totp(o,str(p.get('code',''))):
   log(email[:200],'login-failed');return R.unauthorized(message='Invalid owner credentials or authenticator code.',request=request)
  request.session.cycle_key();request.session['nexease_owner']={'email':o.email,'generation':o.generation,'at':time.time()};log(o.email,'login')
  return R.success(data={'authenticated':True,'email':o.email},request=request)
 except (ValueError,ValidationError):return R.validation_error(message='Unable to sign in. Check credentials, configuration or try again later.',request=request)

@owner_required
@require_http_methods(['GET','POST'])
def owner_console(request):
 owner=request.platform_owner
 if request.method=='POST':
  p=payload(request);reason=str(p.get('reason','')).strip()
  if len(reason)<5:raise ValueError('Enter a reason for this owner action.')
  if not check_password(str(p.get('password','')),owner.password) or not verify_totp(owner,str(p.get('code',''))):raise ValueError('Fresh owner password and authenticator code are required.')
  action=p.get('action');oid=str(p.get('organization_id',''))
  details={k:p.get(k) for k in ('user_id','plan','days','price','limits','subscription_id') if k in p}
  log(owner.email,action+':attempt',oid,reason,details)
  if action in ('plan_save','plan_publish'):
   plan=Plan.objects(code=p.get('plan')).first()
   if not plan:raise ValueError('Unknown plan.')
   if action=='plan_save':
    price=Decimal(str(p.get('price')))
    if not price.is_finite() or not 1<=price<=100000 or price*100!=int(price*100):raise ValueError('Enter a valid INR price.')
    limits=p.get('limits')
    if not isinstance(limits,dict) or set(limits)!=set(DEFAULTS[plan.code][2]):raise ValueError('Supply all plan limits.')
    if any(type(v)!=int or v<0 or v>1000000 for v in limits.values()):raise ValueError('Limits must be nonnegative integers up to 1,000,000.')
    plan.price_paise=int(price*100);plan.limits=limits;plan.features=DEFAULTS[plan.code][3];plan.published=False;plan.revision+=1;plan.save()
   else:gateway.publish(plan)
  elif action=='grant_trial':
   org=Organization.objects(id=oid).first();plan=Plan.objects(code=p.get('plan')).first();days=int(p.get('days',14))
   if not org or not plan or not 1<=days<=90:raise ValueError('Select organization, plan and 1–90 days.')
   with org_lock(oid):
    m=state(org)
    if m and m.subscription_id and m.end>datetime.utcnow():raise ValueError('Do not overwrite a paid subscription. Cancel it through billing first.')
    m=m or Membership(organization_id=oid);m.plan=plan.code;m.status='trial';m.start=datetime.utcnow();m.end=m.start+timedelta(days=days);m.limits=plan.limits;m.features=plan.features;m.subscription_id='';m.gateway_mode='';m.save()
  elif action in ('workforce_on','workforce_off','expenses_on','expenses_off'):
   org=Organization.objects(id=oid).first()
   if not org:raise ValueError('Organization not found.')
   setattr(org,'workforce_enabled' if action.startswith('workforce') else 'expenses_enabled',action.endswith('_on'));org.save()
  elif action in ('suspend','restore'):
   org=Organization.objects(id=oid).first()
   if not org:raise ValueError('Organization not found.')
   m=state(org) or Membership(organization_id=oid);m.suspended=action=='suspend';m.save()
  elif action in ('disable_user','enable_user','revoke_sessions','reset_password'):
   u=User.objects(id=p.get('user_id'),organization=oid).first()
   if not u:raise ValueError('User not found in organization.')
   from apps.accounts.services import AuthenticationService
   if action=='disable_user':u.update(set__is_active=False);AuthenticationService.revoke_user_sessions(u)
   if action=='enable_user':
    from .entitlements import check_capacity
    with org_lock(oid):
     if not u.is_active:check_capacity(u.organization,'users');u.update(set__is_active=True)
   if action=='revoke_sessions':AuthenticationService.revoke_user_sessions(u)
   if action=='reset_password':
    from django.conf import settings
    if settings.EMAIL_MODE!='production':raise ValueError('Real password-reset email requires production SMTP configuration. No password was changed.')
    from apps.accounts.password_reset_service import PasswordResetService
    from apps.accounts.password_reset_email_service import PasswordResetEmailService
    token=PasswordResetService.create_reset_token(email=u.email)
    if not token:raise ValueError('User must be active before resetting password.')
    try:PasswordResetEmailService.send_reset_email(**token)
    except Exception:raise ValueError('Reset email could not be delivered. Check SMTP configuration. No password was changed.')
  elif action=='reconcile':gateway.reconcile(str(p.get('subscription_id','')))
  else:raise ValueError('Unsupported owner action.')
  log(owner.email,action+':completed',oid,reason,details)
  return R.success(data={'message':'Owner action completed.'},request=request)
 seed();q=str(request.GET.get('q',''))[:100];page=max(1,int(request.GET.get('page','1')));orgs=Organization.objects.filter(Q(name__icontains=q)|Q(email__icontains=q)).order_by('-created_at');rows=[]
 for o in orgs.skip((page-1)*25).limit(25):rows.append({'id':str(o.id),'name':o.name,'email':o.email,'active':o.is_active,'membership':membership_json(state(o)),'users':User.objects(organization=o).count()})
 return R.success(data={'organizations':rows,'total':orgs.count(),'page':page,'plans':[plan_json(p) for p in Plan.objects.order_by('price_paise')],'billing':json_safe(list(get_db().saas_payments.find({'mode':gateway.mode()},{'_id':0}).sort('paid_at',-1).limit(100))),'health':{'payments':gateway.ready(),'gateway_mode':gateway.mode(),'ai':os.getenv('AI_ENABLED','false')=='true' and bool(os.getenv('OPENAI_API_KEY'))},'audit':[dict(actor=a.actor,action=a.action,organization_id=a.organization_id,reason=a.reason,at=a.at.isoformat()) for a in OwnerAudit.objects.order_by('-at').limit(50)]},request=request)

@owner_required
@require_http_methods(['POST'])
def owner_report(request):
 p=payload(request);reason=str(p.get('reason','')).strip();oid=str(p.get('organization_id',''))
 if len(reason)<5:raise ValueError('Enter the support reason for accessing customer data.')
 org=Organization.objects(id=oid).first()
 if not org:raise ValueError('Organization not found.')
 log(request.platform_owner.email,'view-customer-report',oid,reason)
 from apps.sales.models import Invoice
 from apps.purchasing.models import VendorBill
 from apps.business.models import BusinessRecord
 from apps.finance.models import JournalEntry
 def documents(model,number):
  return [dict(id=str(x.id),number=getattr(x,number),status=x.status,total=str(x.total_amount),balance=str(x.balance_due)) for x in model.objects(organization=org).order_by('-created_at').limit(100)]
 users=[dict(id=str(u.id),email=u.email,name=u.first_name+' '+u.last_name,active=u.is_active,role=u.role.name if u.role else '') for u in User.objects(organization=org)]
 activity=list(get_db().saas_activity.find({'organization_id':oid},{'_id':0}).sort('at',-1).limit(100))
 ai=list(get_db().saas_ai_usage.find({'organization_id':oid},{'_id':0}).sort('period',-1).limit(12))
 return R.success(data={'organization':org.name,'users':users,'invoices':documents(Invoice,'invoice_number'),'bills':documents(VendorBill,'bill_number'),'membership':membership_json(state(org)),'usage':usage(org),'ai_usage':json_safe(ai),'activity':json_safe(activity),'payroll':[{'month':x.key,'status':x.data.get('status'),'outstanding':x.data.get('outstanding_total')} for x in BusinessRecord.objects(organization=org,kind='payruns').order_by('-created_at').limit(12)],'journals':[dict(number=j.journal_number,status=j.status,debit=str(j.total_debit),credit=str(j.total_credit)) for j in JournalEntry.objects(organization=org).order_by('-created_at').limit(100)]},request=request)

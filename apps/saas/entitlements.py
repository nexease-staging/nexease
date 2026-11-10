"""Tenant entitlements and serialized model writes, including imports/background jobs."""
import os,calendar
from datetime import datetime,timedelta
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import uuid4
from mongoengine.connection import get_db
from pymongo.errors import DuplicateKeyError
from mongoengine.errors import ValidationError
from .models import Plan,Membership
DEFAULTS={
 'free':('Free',0,dict(users=1,invoices=30,bills=30,products=100,warehouses=1,employees=0,ai=0,scan_pages=0,gst_lookups=0,einvoices=0),[]),
 'basic':('NexEase',749,dict(users=3,invoices=300,bills=100,products=500,warehouses=1,employees=0,ai=0,scan_pages=0,gst_lookups=0,einvoices=0),[]),
 'plus':('NexEase Plus',999,dict(users=10,invoices=1000,bills=500,products=5000,warehouses=3,employees=25,ai=0,scan_pages=0,gst_lookups=0,einvoices=0),['finance','advanced_reports','gst','workforce']),
 'pro':('NexEase Pro',1299,dict(users=25,invoices=3000,bills=2000,products=20000,warehouses=10,employees=50,ai=300,scan_pages=100,gst_lookups=0,einvoices=100),['finance','advanced_reports','gst','workforce','ai','einvoice'])}
ANNUAL_PRICES={'free':0,'basic':7499,'plus':9999,'pro':12999}

def enabled():return os.getenv('SAAS_ENFORCEMENT','true').lower()=='true'
def seed():
 for code,(name,price,limits,features) in DEFAULTS.items():
  Plan.objects(code=code).update_one(upsert=True,set_on_insert__name=name,set_on_insert__price_paise=price*100,set_on_insert__limits=limits,set_on_insert__features=features)
 # One-time, idempotent catalogue upgrade for installations still showing old prices.
 revision='launch-749-999-1299-annual-einvoice-v3'
 if not get_db().saas_catalog_revisions.find_one({'_id':revision}):
  for code,(_,price,_,features) in DEFAULTS.items():
   Plan.objects(code=code,price_paise__ne=price*100).update_one(set__price_paise=price*100,set__published=False,set__razorpay_plan_id='',inc__revision=1)
   Plan.objects(code=code).update_one(set__features=features)
  get_db().saas_catalog_revisions.update_one({'_id':revision},{'$set':{'applied_at':datetime.utcnow()}},upsert=True)

def effective_features(membership):
 # Tier policy overrides stale snapshots (e.g. a legacy Plus membership with AI).
 return list(DEFAULTS[membership.plan][3]) if membership and membership.plan in DEFAULTS else []

def has_einvoice(org):
 m=state(org)
 return bool(m and m.plan=='pro' and not m.suspended and m.status in ('active','trial')
             and m.start<=datetime.utcnow()<m.end and (not m.subscription_id or
             m.gateway_mode==('test' if os.getenv('RAZORPAY_KEY_ID','').startswith('rzp_test_') else 'live')))

def module_access(org):
 if not enabled():return {**{k:True for k in ('workforce','taxation','finance','ai')},'einvoice':has_einvoice(org)}
 m=state(org)
 active=m and not m.suspended and m.status in ('active','trial') and m.start<=datetime.utcnow()<m.end
 if m and m.subscription_id and m.gateway_mode!=('test' if os.getenv('RAZORPAY_KEY_ID','').startswith('rzp_test_') else 'live'):active=False
 f=effective_features(m) if active else []
 return {k:feature in f for k,feature in [('workforce','workforce'),('taxation','gst'),('finance','finance'),('ai','ai'),('einvoice','einvoice')]}

def state(org):
 m=Membership.objects(organization_id=str(org.id)).first()
 return m

def require(org,feature=None,write=False):
 if not enabled():return
 m=state(org)
 if m and m.suspended:raise ValidationError('Organization access is suspended. Contact NexEase support.')
 active=m and m.status in ('active','trial') and m.start<=datetime.utcnow()<m.end
 if m and m.subscription_id and m.gateway_mode!=('test' if os.getenv('RAZORPAY_KEY_ID','').startswith('rzp_test_') else 'live'):active=False
 if write and not active:raise ValidationError('An active subscription or owner-granted trial is required. Open Subscription.')
 if feature and (not active or feature not in effective_features(m)):raise ValidationError('This feature requires an active '+('Pro' if feature in ('ai','einvoice') else 'Plus or Pro')+' plan.')

def feature_for(path):
 if path.startswith('/finance/'):return 'finance'
 if any(x in path for x in ['/chart-of-accounts/','/journal-entries/','/general-ledger/','/trial-balance/','/bank-accounts/','/bank-transactions/','/bank-transfers/','/bank-statements/','/bank-payment-suggestions/','/document-logs/','/business/payment-accounts/','/business/books-sync/']):return 'finance'
 if any(s in path for s in ['/business/gst/','/business/records/gst_']):return 'gst'
 if any(s in path for s in ['/business/workforce/','/business/payroll','/business/daily-work/','/business/bulk-assign/','/business/labour','/business/workers/','/business/balances/','/business/employee-payables/']):return 'workforce'
 if '/business/records/' in path and path.split('/business/records/')[1].split('/')[0] not in ('expenses','gst_settings','gst_adjustments'):return 'workforce'
 if any(s in path for s in ['/accounting-reports/','/business/accountant-export/','/cash-flow/','/finance-audit/','/finance-dashboard/','/accounting-dashboard/','/exports/']):return 'advanced_reports'
 return None

held=ContextVar('saas_held',default=frozenset())
@contextmanager
def org_lock(orgid):
 orgid=str(orgid)
 if orgid in held.get():yield;return
 c=get_db().saas_write_locks;token=uuid4().hex
 try:c.insert_one({'_id':orgid,'token':token,'at':datetime.utcnow()})
 except DuplicateKeyError:raise ValidationError('Another update is running. Retry shortly. If a server stopped, ask the owner to recover its stale lock.')
 h=held.set(held.get()|{orgid})
 try:yield
 finally:held.reset(h);c.delete_one({'_id':orgid,'token':token})

def usage_period(m):
 if m.plan=='free':
  from .provider_guard import month_key
  return month_key(datetime.utcnow())
 if m.cycle!='yearly':return m.start.isoformat()
 now=datetime.utcnow()
 offset=max(0,(now.year-m.start.year)*12+now.month-m.start.month)
 def anniversary(n):
  year,month=divmod(m.start.year*12+m.start.month-1+n,12)
  return m.start.replace(year=year,month=month+1,day=min(m.start.day,calendar.monthrange(year,month+1)[1]))
 date=anniversary(offset)
 return (anniversary(offset-1) if offset and date>now else date).isoformat()

def usage(org,m=None):
 m=m or state(org)
 if not m:return {}
 return {k:get_db().saas_usage.count_documents({'organization_id':str(org.id),'period':usage_period(m),'kind':k}) for k in ['invoices','bills']}

def resource_count(org,key):
 from apps.accounts.models import User
 from apps.products.models import Product
 from apps.inventory.models import Warehouse
 from apps.business.models import BusinessRecord
 return {'users':lambda:User.objects(organization=org,is_active=True).count(),'products':lambda:Product.objects(organization=org).count(),'warehouses':lambda:Warehouse.objects(organization=org,is_active=True).count(),'employees':lambda:BusinessRecord.objects(organization=org,kind='employees',data__active=True).count()}[key]()

def check_capacity(org,key,extra=1):
 if not enabled():return
 require(org,write=True);m=state(org)
 if resource_count(org,key)+extra>m.limits.get(key,0):raise ValidationError(f'Plan limit reached for {key}. Reduce active resources or upgrade your subscription.')

def install_guards():
 from apps.accounts.models import User
 from apps.products.models import Product
 from apps.inventory.models import Warehouse
 from apps.sales.models import Invoice
 from apps.purchasing.models import VendorBill
 from apps.business.models import BusinessRecord
 for model in [User,Product,Warehouse,Invoice,VendorBill,BusinessRecord]:
  if getattr(model,'_saas_guarded',False):continue
  original=model.save
  def guarded(self,*args,_save=original,**kwargs):
   org=getattr(self,'organization',None)
   if not enabled() or not org:return _save(self,*args,**kwargs)
   # Initial signup user is permitted; subsequent users require a subscription.
   initial=isinstance(self,User) and not User.objects(organization=org).first() and not state(org)
   with org_lock(org.id):
    if not initial and not (isinstance(self,User) and self.id and User.objects(id=self.id).first()):require(org,write=True)
    old=type(self).objects(id=self.id).first() if self.id else None
    key=None
    if isinstance(self,User) and self.is_active and (not old or not old.is_active) and not initial:key='users'
    if isinstance(self,Product) and not old:key='products'
    if isinstance(self,Warehouse) and self.is_active and (not old or not old.is_active):key='warehouses'
    if isinstance(self,BusinessRecord):
     feature='gst' if self.kind.startswith('gst_') else ('workforce' if self.kind not in ('expenses','invoice_settings') else None)
     if feature:require(org,feature,True)
     if self.kind=='employees' and self.data.get('active') and (not old or not old.data.get('active')):key='employees'
    if key:check_capacity(org,key)
    u=None
    if isinstance(self,(Invoice,VendorBill)) and self.status not in ('DRAFT','CANCELLED'):
     kind='invoices' if isinstance(self,Invoice) else 'bills';m=state(org)
     # Existing issued records don't consume quota again on payment/cancellation edits.
     if not old or old.status=='DRAFT':
      uid=kind+':'+str(self.id or uuid4().hex)
      if not get_db().saas_usage.find_one({'_id':uid}):
       if usage(org,m).get(kind,0)>=m.limits.get(kind,0):raise ValidationError('Monthly '+kind+' allowance reached.')
       u={'_id':uid,'organization_id':str(org.id),'period':usage_period(m),'kind':kind}
       get_db().saas_usage.insert_one(u)
    try:
     result=_save(self,*args,**kwargs)
     if isinstance(self,(Invoice,VendorBill)) and self.status=='DRAFT' and old and old.status!='DRAFT':
      get_db().saas_usage.delete_one({'_id':('invoices' if isinstance(self,Invoice) else 'bills')+':'+str(self.id)})
     return result
    except Exception:
     if u:get_db().saas_usage.delete_one({'_id':u['_id']})
     raise
  model.save=guarded;model._saas_guarded=True

 # User reactivation uses an atomic queryset update in the existing service.
 from apps.accounts.user_management_service import UserManagementService
 original_activate=UserManagementService.activate_user
 if not getattr(original_activate,'_saas_guarded',False):
  def activate_user(*args,**kwargs):
   org=kwargs.get('organization');user=kwargs.get('user')
   if not enabled() or not org:return original_activate(*args,**kwargs)
   with org_lock(org.id):
    if user and not user.is_active:check_capacity(org,'users')
    return original_activate(*args,**kwargs)
  activate_user._saas_guarded=True;UserManagementService.activate_user=staticmethod(activate_user)


def grant_signup_trial(org):
 """One 14-day Plus trial for a newly created organization only."""
 seed()
 plan=Plan.objects.get(code='plus')
 now=datetime.utcnow()
 Membership.objects(organization_id=str(org.id)).update_one(upsert=True,
     set_on_insert__plan='plus',set_on_insert__status='trial',
     set_on_insert__start=now,set_on_insert__end=now+timedelta(days=14),
     set_on_insert__limits=dict(plan.limits),set_on_insert__features=list(plan.features))

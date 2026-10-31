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
 'basic':('NexEase',749,dict(users=2,invoices=100,bills=100,products=500,warehouses=1,employees=0,ai=0,scan_pages=0),[]),
 'plus':('NexEase Plus',1499,dict(users=5,invoices=500,bills=500,products=5000,warehouses=3,employees=25,ai=0,scan_pages=0),['advanced_reports','gst','workforce']),
 'pro':('NexEase Pro',1999,dict(users=10,invoices=2000,bills=2000,products=20000,warehouses=10,employees=100,ai=300,scan_pages=100),['advanced_reports','gst','workforce','ai'])}
def enabled():return os.getenv('SAAS_ENFORCEMENT','true').lower()=='true'
def seed():
 for code,(name,price,limits,features) in DEFAULTS.items():
  Plan.objects(code=code).update_one(upsert=True,set_on_insert__name=name,set_on_insert__price_paise=price*100,set_on_insert__limits=limits,set_on_insert__features=features)
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
 if feature and (not active or feature not in m.features):raise ValidationError('This feature requires an active '+('Pro' if feature=='ai' else 'Plus or Pro')+' plan.')

def feature_for(path):
 if any(s in path for s in ['/business/gst/','/business/records/gst_']):return 'gst'
 if any(s in path for s in ['/business/workforce/','/business/payroll','/business/daily-work/','/business/bulk-assign/','/business/labour','/business/workers/','/business/balances/']):return 'workforce'
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

def usage(org,m=None):
 m=m or state(org)
 if not m:return {}
 return {k:get_db().saas_usage.count_documents({'organization_id':str(org.id),'period':m.start.isoformat(),'kind':k}) for k in ['invoices','bills']}

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
       u={'_id':uid,'organization_id':str(org.id),'period':m.start.isoformat(),'kind':kind}
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

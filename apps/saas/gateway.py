"""Razorpay subscription activation only from API-verified captured invoices."""
import os,json,base64,hmac,hashlib
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from datetime import datetime
from .models import Plan,Membership,Checkout
from mongoengine.connection import get_db
from .entitlements import org_lock

def ready():return os.getenv('PAYMENTS_ENABLED','false')=='true' and all(os.getenv(k) for k in ['RAZORPAY_KEY_ID','RAZORPAY_KEY_SECRET','RAZORPAY_WEBHOOK_SECRET']) and os.getenv('BILLING_TERMS_READY','false')=='true' and all(os.getenv(k,'').startswith('https://') for k in ['BILLING_TERMS_URL','PRIVACY_URL','REFUND_POLICY_URL'])
def mode():return 'test' if os.getenv('RAZORPAY_KEY_ID','').startswith('rzp_test_') else 'live'
def api(path,body=None,method=None):
 if not ready():raise ValueError('Payments are not enabled. Ask the owner for trial access.')
 auth=base64.b64encode((os.environ['RAZORPAY_KEY_ID']+':'+os.environ['RAZORPAY_KEY_SECRET']).encode()).decode()
 req=Request('https://api.razorpay.com/v1/'+path,data=json.dumps(body).encode() if body is not None else None,method=method or ('POST' if body is not None else 'GET'),headers={'Authorization':'Basic '+auth,'Content-Type':'application/json'})
 try:
  with urlopen(req,timeout=25) as r:return json.load(r)
 except (HTTPError,URLError,TimeoutError):raise ValueError('Payment provider request failed. Check gateway dashboard and retry; do not assume payment failed.')
def publish(plan):
 r=api('plans',{'period':'monthly','interval':1,'item':{'name':plan.name+' v'+str(plan.revision),'amount':plan.price_paise,'currency':'INR','description':'Monthly organization subscription. Final displayed price includes applicable tax.'}})
 plan.razorpay_plan_id=r['id'];plan.gateway_mode=mode();plan.published=True;plan.save()

def reconcile(subscription_id,payment_id=None):
 c=Checkout.objects(subscription_id=subscription_id,mode=mode()).first()
 if not c:raise ValueError('Subscription not found for this gateway mode.')
 s=api('subscriptions/'+subscription_id)
 if s.get('id')!=subscription_id:raise ValueError('Subscription mismatch.')
 start=s.get('current_start');end=s.get('current_end')
 if not start or not end:return {'status':s.get('status'),'message':'Waiting for a paid subscription period.'}
 # Authentication/mandate amounts never grant access. Verify the actual paid invoice.
 invoices=[]
 for skip in range(0,300,100):
  batch=api('invoices?subscription_id='+subscription_id+'&count=100&skip='+str(skip)).get('items',[]);invoices.extend(batch)
  if len(batch)<100:break
 paid=None;refunded=False
 for inv in invoices:
  if inv.get('subscription_id')!=subscription_id or inv.get('status')!='paid' or inv.get('currency')!='INR' or inv.get('amount_paid')!=c.price_paise:continue
  if inv.get('billing_start')!=start or inv.get('billing_end')!=end:continue
  if payment_id and inv.get('payment_id')!=payment_id:continue
  p=api('payments/'+inv['payment_id'])
  if p.get('currency')=='INR' and p.get('amount')==c.price_paise and p.get('status') in ('captured','refunded'):
   get_db().saas_payments.update_one({'_id':inv['payment_id']},{'$set':{'organization_id':c.organization_id,'subscription_id':subscription_id,'invoice_id':inv.get('id',''),'amount_paise':p['amount'],'refunded_paise':p.get('amount_refunded',0),'mode':c.mode,'paid_at':inv.get('paid_at'),'period_start':start,'period_end':end,'receipt_url':inv.get('short_url','')}},upsert=True)
  if p.get('currency')=='INR' and p.get('amount')==c.price_paise and p.get('amount_refunded',0):refunded=True
  if p.get('status')=='captured' and p.get('currency')=='INR' and p.get('amount')==c.price_paise and not p.get('amount_refunded',0):paid=inv;break
 with org_lock(c.organization_id):
  m=Membership.objects(organization_id=c.organization_id).first()
  if paid:
   if m and m.subscription_id not in ('',subscription_id) and m.gateway_mode==c.mode and m.end>datetime.utcnow():raise ValueError('Another subscription is active. Owner review required.')
   if not m:m=Membership(organization_id=c.organization_id)
   newstart=datetime.utcfromtimestamp(start);newend=datetime.utcfromtimestamp(end)
   if m.subscription_id==subscription_id and m.start>newstart:return {'status':m.status}
   m.plan=c.plan;m.gateway_mode=c.mode;m.status='active';m.start=newstart;m.end=newend;m.subscription_id=subscription_id;m.limits=c.limits;m.features=c.features;m.updated_at=datetime.utcnow();m.save()
  elif m and m.subscription_id==subscription_id and (refunded or m.end<=datetime.utcnow()):m.status='refunded' if refunded else 'expired';m.save()
  c.status=s.get('status','unknown');c.save()
 return {'status':c.status,'message':'Paid access verified.' if paid else 'No captured current-period invoice verified yet.'}

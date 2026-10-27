import bootstrap
import unittest,os,json,time,hashlib,hmac
from datetime import datetime,timedelta
from unittest.mock import patch
from io import BytesIO
from decimal import Decimal
from django.test import RequestFactory
from django.contrib.auth.hashers import make_password
from cryptography.fernet import Fernet
from mongoengine.connection import get_db
from mongoengine.errors import ValidationError
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.sales.models import Invoice,InvoiceItem,Customer
from apps.products.models import Product,Category
from apps.purchasing.models import VendorBill
from apps.business.models import BusinessRecord
from apps.saas.models import Plan,Membership,Checkout,PlatformOwner,AIProposal,OwnerAudit
from apps.saas.entitlements import seed,require,state,org_lock,resource_count,feature_for
from apps.saas.security import cipher,totp,verify_totp,rate
from apps.saas import views,ai,gateway
from apps.saas.middleware import SaaSMiddleware

class Session(dict):
 def cycle_key(self):pass
class SaaSTests(unittest.TestCase):
 def setUp(self):
  self.env=patch.dict(os.environ,{'SAAS_ENFORCEMENT':'true','OWNER_ENCRYPTION_KEY':Fernet.generate_key().decode(),'AI_ENABLED':'true','OPENAI_API_KEY':'test-not-real','RAZORPAY_KEY_ID':'rzp_test_fake','RAZORPAY_KEY_SECRET':'secret','RAZORPAY_WEBHOOK_SECRET':'webhook','PAYMENTS_ENABLED':'true','BILLING_TERMS_READY':'true','BILLING_TERMS_URL':'https://example.com/terms','PRIVACY_URL':'https://example.com/privacy','REFUND_POLICY_URL':'https://example.com/refunds'});self.env.start()
  for c in get_db().list_collection_names():get_db().drop_collection(c)
  seed();self.org=Organization(name='Trial',email='org@example.com').save();self.other=Organization(name='Other',email='other@example.com').save()
  self.user=User(organization=self.org,email='user@example.com',password=make_password('testpass'),first_name='A',last_name='B').save();self.grant()
 def tearDown(self):self.env.stop()
 def grant(self,code='pro',**limits):
  p=Plan.objects.get(code=code);Membership.objects(organization_id=str(self.org.id)).delete();return Membership(organization_id=str(self.org.id),plan=code,status='trial',start=datetime.utcnow()-timedelta(days=1),end=datetime.utcnow()+timedelta(days=29),limits={**p.limits,**limits},features=p.features).save()
 def request(self,path='/',data=None,method='POST'):
  r=RequestFactory().get(path,data or {}) if method=='GET' else RequestFactory().post(path,json.dumps(data or {}),content_type='application/json');r.user=self.user;r.api_user=self.user;r.api_organization=self.org;r.session=Session();return r
 def call(self,view,data=None,method='POST',**kw):
  req=self.request(data=data,method=method)
  with patch('apps.organizations.api_context_service.APIOrganizationContextService.resolve',return_value={'user':self.user,'organization':self.org}),patch('apps.authorization.services.AuthorizationService.has_permission',return_value=True):return view(req,**kw)
 def invoice(self,n='I1'):
  c=Customer.objects(organization=self.org).first() or Customer(organization=self.org,code='C1',name='Client').save();cat=Category.objects(organization=self.org).first() or Category(organization=self.org,name='Service').save();p=Product.objects(organization=self.org).first() or Product(organization=self.org,sku='S1',name='Service',category=cat,unit='PCS').save()
  return Invoice(organization=self.org,invoice_number=n,customer=c,billing_name=c.name,invoice_date=datetime.utcnow(),items=[InvoiceItem(product=p,quantity=1,unit_price=100,line_subtotal=100,line_total=100)],subtotal=100,total_amount=100,balance_due=100,created_by=self.user).save()
 def extract(self,kind='expense'):
  f={k:'' for k in ai.FIELDS};f.update(date='2026-10-25',party_name='Petrol pump',category='Petrol / fuel',description='Site visit',amount='500',payment_mode='UPI')
  return {'kind':kind,'fields':f,'items':[],'questions':[],'warnings':[]}
 def proposal(self,kind='expense'):
  return AIProposal(organization_id=str(self.org.id),user_id=str(self.user.id),request_key='some-unique-key-123',kind=kind,data=self.extract(kind),state='review').save()
 def owner(self):return PlatformOwner(email='owner@example.com',password=make_password('Owner-password-long123!'),totp_secret=cipher().encrypt(b'JBSWY3DPEHPK3PXP').decode()).save()
 def owner_request(self,data=None):
  o=PlatformOwner.objects.first() or self.owner();r=self.request(data=data);r.session['nexease_owner']={'email':o.email,'generation':o.generation,'at':time.time()};return r
 def checkout(self):return Checkout(subscription_id='sub_test',organization_id=str(self.org.id),plan='pro',price_paise=199900,limits=Plan.objects.get(code='pro').limits,features=['workforce','ai'],mode='test').save()
 def remote(self,refunded=0,status='captured',amount=199900):
  now=int(time.time());start=now-100;end=now+10000
  def api(path,*args,**kw):
   if path.startswith('subscriptions/'):return {'id':'sub_test','current_start':start,'current_end':end,'status':'active'}
   if path.startswith('invoices?'):return {'items':[{'subscription_id':'sub_test','status':'paid','currency':'INR','amount_paid':199900,'paid_at':start-1,'billing_start':start,'billing_end':end,'payment_id':'pay_test'}]}
   if path.startswith('payments/'):return {'status':status,'currency':'INR','amount':amount,'amount_refunded':refunded}
   raise AssertionError(path)
  return api
 def test_plan_defaults(self):self.assertEqual([Plan.objects.get(code=x).price_paise for x in ['basic','plus','pro']],[74900,149900,199900]);seed();self.assertEqual(Plan.objects.count(),3)
 def test_basic_cannot_workforce_or_ai(self):
  self.grant('basic')
  for f in ['workforce','ai','advanced_reports','gst']:
   with self.assertRaises(ValidationError):require(self.org,f)
 def test_plus_cannot_ai(self):
  self.grant('plus');require(self.org,'workforce')
  with self.assertRaises(ValidationError):require(self.org,'ai')
 def test_expired_reads_allowed_writes_denied(self):
  m=state(self.org);m.end=datetime.utcnow()-timedelta(seconds=1);m.save();require(self.org)
  with self.assertRaises(ValidationError):require(self.org,write=True)
 def test_suspension_denies_reads(self):
  m=state(self.org);m.suspended=True;m.save()
  with self.assertRaises(ValidationError):require(self.org)
 def test_user_limit(self):
  self.grant('basic',users=1)
  with self.assertRaises(ValidationError):User(organization=self.org,email='b@example.com',password='x',first_name='B',last_name='C').save()
 def test_user_password_edit_when_expired(self):
  m=state(self.org);m.end=datetime.utcnow()-timedelta(days=1);m.save();self.user.set_password('new-password');self.user.save()
 def test_initial_signup_user_allowed(self):User(organization=self.other,email='first@example.com',password='x',first_name='A',last_name='B').save()
 def test_new_product_limit(self):
  self.grant(products=0);cat=Category(organization=self.org,name='C').save()
  with self.assertRaises(ValidationError):Product(organization=self.org,sku='P',name='P',unit='PCS',category=cat).save()
 def test_invoice_quota_counts_issue_not_draft(self):
  self.grant(invoices=1);a=self.invoice();b=self.invoice('I2');a.status='ISSUED';a.save();a.status='CANCELLED';a.save()
  b.status='ISSUED'
  with self.assertRaises(ValidationError):b.save()
 def test_invoice_retry_does_not_double_count(self):
  self.grant(invoices=1);a=self.invoice();a.status='ISSUED';a.save();a.balance_due=50;a.save();self.assertEqual(get_db().saas_usage.count_documents({}),1)
 def test_invoice_rollback_releases_allowance(self):
  self.grant(invoices=1);a=self.invoice();a.status='ISSUED';a.save();a.status='DRAFT';a.save();self.assertEqual(get_db().saas_usage.count_documents({}),0)
 def test_new_cycle_restores_allowance(self):
  self.grant(invoices=1);a=self.invoice();a.status='ISSUED';a.save();m=state(self.org);m.start=datetime.utcnow();m.save();b=self.invoice('I2');b.status='ISSUED';b.save()
 def test_employee_limit_applies_to_import_save(self):
  self.grant(employees=0)
  with self.assertRaises(ValidationError):BusinessRecord(organization=self.org,kind='employees',key='E',data={'active':True},created_by=self.user).save()
 def test_lock_nested_and_concurrent_rejected(self):
  with org_lock(self.org.id):
   with org_lock(self.org.id):pass
  self.assertEqual(get_db().saas_write_locks.count_documents({}),0)
  get_db().saas_write_locks.insert_one({'_id':str(self.org.id)})
  with self.assertRaises(ValidationError):
   with org_lock(self.org.id):pass
 def test_report_feature_route(self):
  for path in ['/api/v1/finance/cash-flow/','/api/v1/business/accountant-export/','/api/v1/exports/invoices/']:self.assertEqual(feature_for(path),'advanced_reports')
 def test_middleware_enforces_protected_route(self):
  self.grant('basic');r=self.request('/api/v1/business/daily-work/',method='GET');response=SaaSMiddleware(lambda r:None).process_view(r,None,(),{});self.assertEqual(response.status_code,403)
 def test_regular_user_cannot_owner(self):self.assertEqual(views.owner_console(self.request(method='GET')).status_code,401)
 def test_owner_totp_cannot_replay(self):
  o=self.owner();code=totp('JBSWY3DPEHPK3PXP',int(time.time())//30);self.assertTrue(verify_totp(o,code));self.assertFalse(verify_totp(o,code))
 def test_owner_session_expires(self):
  r=self.owner_request();r.session['nexease_owner']['at']=time.time()-1900;self.assertEqual(views.owner_console(r).status_code,401)
 def test_owner_generation_revokes_session(self):
  r=self.owner_request();PlatformOwner.objects.update(inc__generation=1);self.assertEqual(views.owner_console(r).status_code,401)
 def test_owner_report_requires_reason(self):self.assertEqual(views.owner_report(self.owner_request({'organization_id':str(self.org.id),'reason':''})).status_code,400)
 def test_owner_report_has_no_password(self):
  r=views.owner_report(self.owner_request({'organization_id':str(self.org.id),'reason':'Customer requested support'}));self.assertEqual(r.status_code,200,r.content);self.assertNotIn('pbkdf2',r.content.decode());self.assertNotIn('"password"',r.content.decode());self.assertEqual(OwnerAudit.objects(action='view-customer-report').count(),1)
 def test_owner_action_requires_fresh_credentials(self):self.assertEqual(views.owner_console(self.owner_request({'action':'suspend','organization_id':str(self.org.id),'reason':'Support issue'})).status_code,400)
 def test_owner_suspend(self):
  o=self.owner();r=self.owner_request({'action':'suspend','organization_id':str(self.org.id),'reason':'Support issue','password':'Owner-password-long123!','code':totp('JBSWY3DPEHPK3PXP',int(time.time())//30)});self.assertEqual(views.owner_console(r).status_code,200);self.assertTrue(state(self.org).suspended)
 def test_rate_limit(self):
  rate('key',1)
  with self.assertRaises(ValueError):rate('key',1)
 def test_gateway_requires_policies(self):
  with patch.dict(os.environ,{'REFUND_POLICY_URL':''}):self.assertFalse(gateway.ready())
 def test_payment_activation_verified_and_idempotent(self):
  self.checkout()
  with patch('apps.saas.gateway.api',side_effect=self.remote()):gateway.reconcile('sub_test');first=state(self.org).start;gateway.reconcile('sub_test')
  self.assertEqual(state(self.org).status,'active');self.assertEqual(state(self.org).start,first)
 def test_authorized_payment_does_not_grant(self):
  self.checkout()
  with patch('apps.saas.gateway.api',side_effect=self.remote(status='authorized')):gateway.reconcile('sub_test')
  self.assertEqual(state(self.org).status,'trial')
 def test_wrong_payment_amount_does_not_grant(self):
  self.checkout()
  with patch('apps.saas.gateway.api',side_effect=self.remote(amount=100)):gateway.reconcile('sub_test')
  self.assertEqual(state(self.org).status,'trial')
 def test_refund_revokes_paid_access(self):
  self.checkout()
  with patch('apps.saas.gateway.api',side_effect=self.remote()):gateway.reconcile('sub_test')
  with patch('apps.saas.gateway.api',side_effect=self.remote(refunded=199900)):gateway.reconcile('sub_test')
  self.assertEqual(state(self.org).status,'refunded')
 def test_webhook_bad_signature(self):self.assertEqual(views.webhook(self.request(data={'event':'subscription.charged'})).status_code,400)
 def test_webhook_valid_signature(self):
  self.checkout();r=self.request(data={'event':'subscription.charged','payload':{'subscription':{'entity':{'id':'sub_test'}}}});r.META['HTTP_X_RAZORPAY_SIGNATURE']=hmac.new(b'webhook',r.body,hashlib.sha256).hexdigest()
  with patch('apps.saas.gateway.api',side_effect=self.remote()):self.assertEqual(views.webhook(r).status_code,200)
  self.assertEqual(state(self.org).status,'active')
 def test_customer_cannot_verify_other_subscription(self):
  c=self.checkout();c.organization_id=str(self.other.id);c.save();self.assertEqual(self.call(views.subscription,{'action':'refresh','subscription_id':c.subscription_id}).status_code,400)
 def test_bad_checkout_signature_denied(self):
  self.checkout();self.assertEqual(self.call(views.subscription,{'action':'verify','subscription_id':'sub_test','razorpay_payment_id':'pay_test','razorpay_signature':'fake'}).status_code,400)
 def test_ai_basic_denied(self):self.grant('basic');self.assertEqual(self.call(ai.prepare,{'message':'test','request_key':'x'*20}).status_code,400)
 def test_ai_provider_disabled(self):
  with patch.dict(os.environ,{'AI_ENABLED':'false'}):self.assertEqual(self.call(ai.prepare,{'message':'test','request_key':'x'*20}).status_code,400)
 def test_ai_extract_then_confirm_once(self):
  raw={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(self.extract())}]}],'usage':{'input_tokens':100,'output_tokens':50}}
  with patch('apps.saas.ai.call_model',return_value=raw):r=self.call(ai.prepare,{'message':'500 petrol UPI','request_key':'x'*20})
  self.assertEqual(r.status_code,200,r.content);p=AIProposal.objects.get();self.assertEqual(BusinessRecord.objects.count(),0)
  r=self.call(ai.confirm,{'confirm':True},proposal_id=str(p.id));self.assertEqual(r.status_code,200,r.content);p.reload();self.assertEqual(p.state,'saved',p.result)
  r=self.call(ai.confirm,{'confirm':True},proposal_id=str(p.id));self.assertEqual(BusinessRecord.objects(kind='expenses').count(),1)
 def test_failed_ai_restores_customer_allowance(self):
  with patch('apps.saas.ai.call_model',side_effect=ValueError('fail')):r=self.call(ai.prepare,{'message':'test','request_key':'x'*20})
  self.assertEqual(r.status_code,400);u=get_db().saas_ai_usage.find_one();self.assertEqual(u['requests'],0);self.assertGreater(u['budget_units'],0)
 def test_ai_quota(self):
  self.grant(ai=0)
  with patch('apps.saas.ai.call_model') as model:self.assertEqual(self.call(ai.prepare,{'message':'test','request_key':'x'*20}).status_code,400);model.assert_not_called()
 def test_proposal_cross_tenant_denied(self):
  p=self.proposal();p.organization_id=str(self.other.id);p.save();self.assertEqual(self.call(ai.confirm,{'confirm':True},proposal_id=str(p.id)).status_code,404)
 def test_confirmation_required(self):self.assertEqual(self.call(ai.confirm,{},proposal_id=str(self.proposal().id)).status_code,400)
 def test_ambiguous_entry_not_saved(self):
  p=self.proposal('question');self.assertEqual(self.call(ai.confirm,{'confirm':True},proposal_id=str(p.id)).status_code,400);self.assertEqual(BusinessRecord.objects.count(),0)
 def test_invalid_expense_remains_editable(self):
  p=self.proposal();p.data['fields']['amount']='';p.save();r=self.call(ai.confirm,{'confirm':True},proposal_id=str(p.id));p.reload();self.assertEqual(p.state,'review');self.assertEqual(BusinessRecord.objects.count(),0)
 def test_invoice_totals_mismatch_blocked(self):
  p=self.proposal('invoice');p.data['fields']['document_total']='999';p.data['items']=[dict(sku='S',name='Item',unit='PCS',quantity='1',unit_price='100',tax_rate='0',discount='0')];p.save();r=self.call(ai.confirm,{'confirm':True},proposal_id=str(p.id));self.assertEqual(r.status_code,400);self.assertIn(b'total',r.content)
 def test_model_instructions_cannot_create_unknown_action(self):
  raw={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({**self.extract(),'kind':'delete_database'})}]}]}
  with self.assertRaises(ValueError):ai.parse_response(raw)
 def test_source_file_tenant_boundary(self):
  p=self.proposal();get_db().saas_ai_files.insert_one({'_id':str(p.id),'organization_id':str(self.other.id),'user_id':str(self.user.id),'content':b'x','mime':'image/png'});self.assertEqual(self.call(ai.source,method='GET',proposal_id=str(p.id)).status_code,404)

 def test_ai_confirm_requires_entry_permission(self):
  p=self.proposal();r=self.request(data={'confirm':True})
  with patch('apps.organizations.api_context_service.APIOrganizationContextService.resolve',return_value={'user':self.user,'organization':self.org}),patch('apps.authorization.services.AuthorizationService.has_permission',return_value=False):response=ai.confirm(r,str(p.id))
  self.assertEqual(response.status_code,403);self.assertEqual(BusinessRecord.objects.count(),0)
 def test_ai_invoice_creates_draft_only(self):
  p=self.proposal('invoice');p.data['fields'].update(party_name='Customer',party_code='C1',document_total='118',date='2026-10-25');p.data['items']=[dict(sku='S1',name='Item',unit='PCS',quantity='1',unit_price='100',tax_rate='18',discount='0')];p.save();r=self.call(ai.confirm,{'confirm':True},proposal_id=str(p.id));self.assertEqual(r.status_code,200,r.content);p.reload();self.assertEqual(p.state,'saved',p.result);self.assertEqual(Invoice.objects.get().status,'DRAFT');self.assertEqual(Invoice.objects.get().total_amount,118)
 def test_ai_bill_creates_draft_only(self):
  p=self.proposal('bill');p.data['fields'].update(party_name='Supplier',party_code='SUP1',number='SUP-INV-1',document_total='100',date='2026-10-25');p.data['items']=[dict(sku='S1',name='Item',unit='PCS',quantity='1',unit_price='100',tax_rate='0',discount='0')];p.save();r=self.call(ai.confirm,{'confirm':True},proposal_id=str(p.id));self.assertEqual(r.status_code,200,r.content);p.reload();self.assertEqual(p.state,'saved',p.result);self.assertEqual(VendorBill.objects.get().status,'DRAFT')
 def test_ai_pdf_page_allowance_and_no_auto_entry(self):
  from django.core.files.uploadedfile import SimpleUploadedFile
  from reportlab.pdfgen.canvas import Canvas
  buf=BytesIO();c=Canvas(buf);c.drawString(50,700,'Invoice');c.showPage();c.save()
  r=RequestFactory().post('/',{'request_key':'pdf-unique-key-12345','file':SimpleUploadedFile('bill.pdf',buf.getvalue(),content_type='application/pdf')});r.api_user=self.user;r.api_organization=self.org
  raw={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(self.extract())}]}]}
  with patch('apps.organizations.api_context_service.APIOrganizationContextService.resolve',return_value={'user':self.user,'organization':self.org}),patch('apps.authorization.services.AuthorizationService.has_permission',return_value=True),patch('apps.saas.ai.call_model',return_value=raw):result=ai.prepare(r)
  self.assertEqual(result.status_code,200,result.content);self.assertEqual(get_db().saas_ai_usage.find_one()['pages'],1);self.assertEqual(get_db().saas_ai_files.count_documents({}),1);self.assertEqual(BusinessRecord.objects.count(),0)
 def test_test_payment_cannot_authorize_live_mode(self):
  self.checkout()
  with patch('apps.saas.gateway.api',side_effect=self.remote()):gateway.reconcile('sub_test')
  with patch.dict(os.environ,{'RAZORPAY_KEY_ID':'rzp_live_other'}):
   with self.assertRaises(ValidationError):require(self.org,'ai',True)
 def test_future_period_does_not_grant_early_access(self):
  m=state(self.org);m.start=datetime.utcnow()+timedelta(days=1);m.save()
  with self.assertRaises(ValidationError):require(self.org,write=True)
 def test_owner_wrong_totp_never_changes_data(self):
  r=self.owner_request({'action':'suspend','organization_id':str(self.org.id),'reason':'Testing denied change','password':'Owner-password-long123!','code':'bad'});self.assertEqual(views.owner_console(r).status_code,400);self.assertFalse(state(self.org).suspended)

if __name__=='__main__':unittest.main(verbosity=2)

import os,json
from datetime import datetime,timedelta
from uuid import uuid4
from unittest.mock import patch
from django.test import SimpleTestCase,RequestFactory
from mongoengine.errors import ValidationError
from mongoengine.connection import get_db
from apps.organizations.models import Organization
from apps.saas.models import Membership,Plan
from apps.saas.entitlements import require,effective_features,module_access,seed,feature_for,DEFAULTS
from apps.saas.views import membership_json
from apps.saas.middleware import SaaSMiddleware

class TierPolicyTests(SimpleTestCase):
 def setUp(self):
  self.env=patch.dict(os.environ,SAAS_ENFORCEMENT='true');self.env.start();self.addCleanup(self.env.stop)
  self.org=Organization(name='Tier test',email=f'{uuid4()}@example.test').save()
 def tearDown(self):Membership.objects(organization_id=str(self.org.id)).delete();self.org.delete()
 def member(self,plan,features=None):
  Membership.objects(organization_id=str(self.org.id)).delete()
  return Membership(organization_id=str(self.org.id),plan=plan,status='active',start=datetime.utcnow()-timedelta(days=1),end=datetime.utcnow()+timedelta(days=2),features=features or [],limits=DEFAULTS[plan][2]).save()
 def test_basic_cannot_unlock_modules_with_stale_snapshot(self):
  self.member('basic',['finance','advanced_reports','workforce','gst','ai'])
  for f in ('finance','advanced_reports','workforce','gst','ai'):
   with self.assertRaises(ValidationError):require(self.org,f)
  self.assertEqual(module_access(self.org),dict(workforce=False,taxation=False,finance=False,ai=False));require(self.org,write=True)
 def test_plus_keeps_all_paid_modules_but_denies_ai(self):
  m=self.member('plus',['ai']);self.assertNotIn('ai',membership_json(m)['features'])
  for f in ('finance','advanced_reports','gst','workforce'):require(self.org,f)
  with self.assertRaises(ValidationError):require(self.org,'ai',True)
  self.assertFalse(module_access(self.org)['ai'])
 def test_pro_has_all_features_even_with_legacy_snapshot(self):
  self.member('pro',['ai'])
  for f in ('finance','advanced_reports','workforce','gst','ai'):require(self.org,f)
  self.assertTrue(all(module_access(self.org).values()))
 def test_expired_and_suspended_members_cannot_enter_paid_modules(self):
  m=self.member('pro');m.suspended=True;m.save()
  with self.assertRaises(ValidationError):require(self.org,'finance')
  self.assertFalse(any(module_access(self.org).values()));m.suspended=False;m.end=datetime.utcnow()-timedelta(seconds=1);m.save()
  with self.assertRaises(ValidationError):require(self.org,'ai')
 def test_backend_finance_and_gst_routes_are_classified(self):
  for path in ['/api/v1/bank-accounts/','/api/v1/journal-entries/x/post/','/api/v1/general-ledger/','/api/v1/trial-balance/','/finance/bank-accounts/']:
   self.assertEqual(feature_for(path),'finance')
  self.assertEqual(feature_for('/api/v1/business/gst/export/'),'gst')
  self.assertIsNone(feature_for('/api/v1/invoices/'));self.assertIsNone(feature_for('/api/v1/customer-payments/'));self.assertIsNone(feature_for('/api/v1/business/gst-lookup/'))
 def test_basic_finance_direct_api_and_legacy_url_are_blocked(self):
  from types import SimpleNamespace
  self.member('basic');mw=SaaSMiddleware(lambda r:r)
  for path in ['/api/v1/bank-accounts/','/finance/bank-accounts/']:
   r=RequestFactory().get(path);r.user=SimpleNamespace(is_authenticated=True,organization=self.org)
   self.assertEqual(mw.process_view(r,None,(),{}).status_code,403)

 def test_native_api_decorator_checks_resolved_tenant_without_middleware_user(self):
  from types import SimpleNamespace
  from django.http import HttpResponse
  from apps.core.api.decorators import api_login_required
  self.member('basic');user=SimpleNamespace(is_active=True,organization=self.org)
  @api_login_required
  def endpoint(request):return HttpResponse('Sensitive finance data')
  request=RequestFactory().get('/api/v1/bank-accounts/')
  with patch('apps.core.api.decorators.APIOrganizationContextService.resolve',return_value={'user':user,'organization':self.org}):
   self.assertEqual(endpoint(request).status_code,403)
 def test_expired_user_can_still_log_out(self):
  from types import SimpleNamespace
  from django.http import HttpResponse
  from apps.core.api.decorators import api_login_required
  m=self.member('basic');m.end=datetime.utcnow()-timedelta(days=1);m.save()
  @api_login_required
  def endpoint(request):return HttpResponse('Logged out')
  request=RequestFactory().post('/api/v1/auth/logout/')
  with patch('apps.core.api.decorators.APIOrganizationContextService.resolve',return_value={'user':SimpleNamespace(is_active=True,organization=self.org),'organization':self.org}):
   self.assertEqual(endpoint(request).status_code,200)

class CatalogueUpgradeTests(SimpleTestCase):
 def setUp(self):
  self.collection=get_db().saas_catalog_revisions;self.old=list(Plan.objects);self.marker=self.collection.find_one({'_id':'launch-749-999-1299-v2'})
  Plan.objects.delete();self.collection.delete_one({'_id':'launch-749-999-1299-v2'})
 def tearDown(self):
  Plan.objects.delete()
  for p in self.old:p.save()
  self.collection.delete_one({'_id':'launch-749-999-1299-v2'})
  if self.marker:self.collection.insert_one(self.marker)
 def test_existing_published_catalogue_is_repriced_without_touching_contracts(self):
  for code,price in [('basic',749),('plus',1499),('pro',1999)]:Plan(code=code,name=code,price_paise=price*100,published=True,razorpay_plan_id='old-'+code).save()
  seed();self.assertEqual([Plan.objects.get(code=c).price_paise for c in ('basic','plus','pro')],[74900,99900,129900]);self.assertFalse(Plan.objects.get(code='plus').published);self.assertEqual(Plan.objects.get(code='plus').razorpay_plan_id,'')
  p=Plan.objects.get(code='plus');p.price_paise=109900;p.save();seed();self.assertEqual(Plan.objects.get(code='plus').price_paise,109900)

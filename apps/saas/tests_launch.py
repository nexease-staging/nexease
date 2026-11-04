import json,os
from datetime import datetime,timedelta,date
from unittest.mock import patch
from uuid import uuid4
from decimal import Decimal
from django.test import SimpleTestCase,RequestFactory
from django.core.cache import cache
from mongoengine.connection import get_db
from apps.organizations.models import Organization
from apps.products.models import Product,Category
from apps.inventory.models import Warehouse,Inventory,StockMovement
from apps.accounts.models import User
from apps.authorization.models import Permission,Role
from apps.saas.models import AIProposal,Membership
from apps.saas.ai import FIELDS,prepare,confirm
from apps.saas.ai_stock import resolve_stock,confirm_stock,parse_stock_command
from apps.business.gst_provider import normalize_taxpayer,sandbox_lookup
from apps.saas.deadlines import calendar_rows

class StockActionTests(SimpleTestCase):
 def setUp(self):
  self.env=patch.dict(os.environ,SAAS_ENFORCEMENT='false',AI_ENABLED='true',OPENAI_API_KEY='test-not-real');self.env.start();self.addCleanup(self.env.stop)
  self.org=Organization(name='AI launch tests',email=f'{uuid4()}@example.test').save()
  self.category=Category(organization=self.org,name='Water').save()
  self.product=Product(organization=self.org,category=self.category,sku='BISLERI',name='Bisleri',unit='PCS').save()
  self.wh=Warehouse(organization=self.org,name='Main',code='MAIN').save()
  permissions=[Permission.objects(code=x).first() or Permission(code=x,name=x,module="inventory").save() for x in ['inventory.adjust','inventory.create']]
  self.role=Role(organization=self.org,name='Stock editor',permissions=permissions).save()
  self.user=User(organization=self.org,role=self.role,email=f'{uuid4()}@example.test',password='test',first_name='Stock',last_name='Tester').save()
  Membership(organization_id=str(self.org.id),plan='pro',start=datetime.utcnow()-timedelta(days=1),end=datetime.utcnow()+timedelta(days=2),status='trial',features=['ai'],limits={'ai':300,'scan_pages':100}).save()
 def tearDown(self):
  for model in [StockMovement,Inventory,Product,Category,Warehouse,User,Role]:model.objects(organization=self.org).delete()
  AIProposal.objects(organization_id=str(self.org.id)).delete();Membership.objects(organization_id=str(self.org.id)).delete();self.org.delete()
 def data(self,**fields):return {'kind':'stock_adjustment','fields':{**dict.fromkeys(FIELDS,''),'product_name':'Bisleri','quantity_change':'100',**fields},'items':[],'questions':[],'warnings':[]}
 def request(self,body=None):
  r=RequestFactory().post('/api/v1/saas/ai/',data=json.dumps(body or {'confirm':True}),content_type='application/json');r.api_user=self.user;r.api_organization=self.org;return r
 def proposal(self,data=None):return AIProposal(organization_id=str(self.org.id),user_id=str(self.user.id),request_key=uuid4().hex,kind='stock_adjustment',data=data or self.data(),state='review').save()
 def test_english_stock_intent_is_not_product_creation(self):
  result=parse_stock_command('add bisleri 100 qty in stock');self.assertEqual(result['product_name'],'bisleri');self.assertEqual(result['quantity_change'],'100')
  self.assertIsNone(parse_stock_command('set stock to 100'));self.assertIsNone(parse_stock_command('add Bisleri and Pepsi 100 in stock'))
 def test_remove_is_signed(self):self.assertEqual(parse_stock_command('remove Bisleri 10 qty from stock')['quantity_change'],'-10')
 def test_unique_product_and_warehouse_resolved(self):
  d=self.data(product_name='bIsLeRi');resolve_stock(self.org,d);self.assertFalse(d['questions']);self.assertEqual(d['fields']['product_id'],str(self.product.id));self.assertEqual(d['fields']['warehouse_id'],str(self.wh.id))
 def test_multiple_warehouses_need_choice(self):
  Warehouse(organization=self.org,name='Second',code='TWO').save();d=self.data();resolve_stock(self.org,d);self.assertTrue(d['questions']);self.assertEqual(d['fields']['warehouse_id'],'')
 def test_explicit_warehouse_resolves(self):
  Warehouse(organization=self.org,name='Second',code='TWO').save();d=self.data(warehouse_name='MAIN');resolve_stock(self.org,d);self.assertFalse(d['questions'])
 def test_unknown_product_never_created(self):
  p=self.proposal(self.data(product_name='Missing'))
  with self.assertRaises(ValueError):confirm_stock(self.request(),p)
  self.assertEqual(Product.objects(organization=self.org).count(),1);self.assertEqual(Inventory.objects(organization=self.org).count(),0)
 def test_cross_tenant_identifier_rejected(self):
  d=self.data(product_id='000000000000000000000001');resolve_stock(self.org,d);self.assertTrue(d['questions']);self.assertEqual(d['fields']['product_id'],'')
 def test_stock_add_updates_existing_inventory_and_ledger(self):
  Inventory(organization=self.org,product=self.product,warehouse=self.wh,quantity=20).save();p=self.proposal();r=confirm_stock(self.request(),p);self.assertEqual(r.status_code,200);self.assertEqual(Inventory.objects(organization=self.org).first().quantity,Decimal('120'));self.assertEqual(StockMovement.objects(organization=self.org,reference_type='AI_STOCK').count(),1);self.assertEqual(Product.objects(organization=self.org).count(),1)
 def test_initial_stock_uses_zero_row_plus_tracked_movement(self):
  p=self.proposal();confirm_stock(self.request(),p);self.assertEqual(Inventory.objects(organization=self.org).first().quantity,Decimal('100'));self.assertEqual(StockMovement.objects(organization=self.org).first().reference_id,str(p.id))
 def test_negative_and_nonfinite_quantities_blocked(self):
  for q in ['NaN','Infinity','0','0.001']:
   d=self.data(quantity_change=q);resolve_stock(self.org,d);self.assertTrue(d['questions'])
  with self.assertRaises(ValueError):confirm_stock(self.request(),self.proposal(self.data(quantity_change='-1')))
 def test_reserved_stock_cannot_be_removed(self):
  Inventory(organization=self.org,product=self.product,warehouse=self.wh,quantity=20,reserved_quantity=15).save()
  with self.assertRaises(ValueError):confirm_stock(self.request(),self.proposal(self.data(quantity_change='-6')))
  self.assertEqual(Inventory.objects(organization=self.org).first().quantity,Decimal('20'))
 def test_permissions_are_enforced(self):
  self.role.permissions=[];self.role.save()
  with self.assertRaises(PermissionError):confirm_stock(self.request(),self.proposal())
  self.assertEqual(Inventory.objects(organization=self.org).count(),0)
 def test_duplicate_confirmation_does_not_add_twice(self):
  p=self.proposal();r=self.request();confirm.__wrapped__(r,str(p.id));second=confirm.__wrapped__(r,str(p.id));self.assertEqual(second.status_code,200);self.assertEqual(Inventory.objects(organization=self.org).first().quantity,Decimal('100'));self.assertEqual(StockMovement.objects(organization=self.org).count(),1)
 @patch('apps.saas.ai.call_model',side_effect=AssertionError('Unambiguous stock command should not need model'))
 def test_prepare_then_confirm_exact_customer_command(self,model):
  req=self.request({'message':'add bisleri 100 qty in stock','request_key':uuid4().hex});response=prepare.__wrapped__(req);self.assertEqual(response.status_code,200,response.content);body=json.loads(response.content)['data'];self.assertEqual(body['kind'],'stock_adjustment');self.assertEqual(body['data']['fields']['quantity_change'],'100');self.assertFalse(body['data']['questions']);self.assertEqual(Inventory.objects(organization=self.org).count(),0)
  response=confirm.__wrapped__(self.request(),body['id']);self.assertEqual(response.status_code,200,response.content);self.assertEqual(Inventory.objects(organization=self.org).first().quantity,Decimal('100'));model.assert_not_called()

class GSTProviderTests(SimpleTestCase):
 def setUp(self):cache.clear()
 def raw(self):return {'data':{'data':{'gstin':'27ABCDE1234F1Z5','lgnm':'Legal Ltd','tradeNam':'Trade','sts':'Active','dty':'Regular','pradr':{'addr':{'bno':'10','st':'Road','loc':'Pune','stcd':'Maharashtra','pncd':'411001'}}}}}
 def test_nested_payload_fills_names_address_state_without_inventing_contacts(self):
  d=normalize_taxpayer(self.raw(),'27ABCDE1234F1Z5');self.assertEqual(d['name'],'Trade');self.assertEqual(d['legal_name'],'Legal Ltd');self.assertEqual(d['state'],'27');self.assertIn('411001',d['address']);self.assertEqual(d['phone'],'');self.assertEqual(d['email'],'')
 def test_mismatched_gstin_rejected(self):
  with self.assertRaises(ValueError):normalize_taxpayer(self.raw(),'29ABCDE1234F1Z5')
 @patch('apps.business.gst_provider.request_json')
 def test_authentication_token_is_raw_and_cached(self,req):
  req.side_effect=[{'data':{'access_token':'raw-token'}},self.raw(),self.raw()]
  with patch.dict(os.environ,GST_SANDBOX_API_KEY='test-key',GST_SANDBOX_API_SECRET='test-secret',GST_SANDBOX_ENV='test'):
   sandbox_lookup('27ABCDE1234F1Z5');sandbox_lookup('27ABCDE1234F1Z5')
  self.assertEqual(req.call_count,3);self.assertEqual(req.call_args_list[1].args[1]['authorization'],'raw-token');self.assertNotIn('x-api-secret',req.call_args_list[1].args[1])
 def test_missing_configuration_fails_without_network(self):
  with patch.dict(os.environ,GST_SANDBOX_API_KEY='',GST_SANDBOX_API_SECRET=''):
   with self.assertRaises(ValueError):sandbox_lookup('27ABCDE1234F1Z5')

class CalendarTests(SimpleTestCase):
 def test_quarterly_dates_not_created_monthly_and_ist_used(self):
  with patch.dict(os.environ,NEXEASE_DEADLINES_JSON='[]'):rows=calendar_rows(date(2026,11,4))
  self.assertTrue(any(r['due_at'].startswith('2026-11-20') for r in rows));self.assertTrue(all(r['due_at'].endswith('+05:30') for r in rows));self.assertTrue(all(r['due_at'].startswith('2027-01') for r in rows if 'QRMP' in r['applies_to']))
 def test_extension_replaces_exact_period(self):
  custom={'id':'GSTR-3B-2026-10','title':'GSTR-3B','category':'GST','period':'2026-10','applies_to':'Monthly filers','due_at':'2026-11-25T23:59:59+05:30','source_url':'https://gst.gov.in/','verified_on':'2026-11-04'}
  with patch.dict(os.environ,NEXEASE_DEADLINES_JSON=json.dumps([custom])):rows=calendar_rows(date(2026,11,4))
  chosen=[r for r in rows if r['id']==custom['id']];self.assertEqual(len(chosen),1);self.assertEqual(chosen[0]['due_at'],custom['due_at']);self.assertEqual(chosen[0]['status'],'verified')
 def test_timezone_missing_rejected(self):
  custom={'id':'x','title':'x','category':'GST','period':'2026-10','applies_to':'Monthly','due_at':'2026-11-25T23:59:59','source_url':'https://gst.gov.in','verified_on':'2026-11-04'}
  with patch.dict(os.environ,NEXEASE_DEADLINES_JSON=json.dumps([custom])):
   with self.assertRaises(ValueError):calendar_rows()

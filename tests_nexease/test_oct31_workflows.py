import bootstrap
import io,json,unittest,zipfile
from datetime import datetime
from unittest.mock import patch
from django.test import RequestFactory
from mongoengine.connection import get_db
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.authorization.models import Role
from apps.products.models import Product,Category
from apps.sales.models import Customer,Invoice,InvoiceItem
from apps.business.models import BusinessRecord as Record
from apps.business.enhancements import invoice_zip,barcode_lookup,barcode_labels,populate_inputs,is_admin,module_for
from apps.business.direct_entry import direct_invoice
from apps.business.billing import invoice_details
from apps.business.pro_api import modules
from apps.business.gst_lookup import lookup
from apps.finance.services.document_api_service import DocumentAPIService
from pypdf import PdfReader

class WorkflowTests(unittest.TestCase):
 def setUp(self):
  for c in get_db().list_collection_names():get_db().drop_collection(c)
  self.org=Organization(name='QA Test',email='test@example.com',address='Pune').save()
  self.user=User(organization=self.org,email='admin@example.com',password='x',first_name='QA',last_name='Admin').save()
  self.user.role=Role(organization=self.org,name='Admin',is_system=True).save();self.user.save()
  self.cat=Category(organization=self.org,name='Goods').save()
  self.p=Product(organization=self.org,category=self.cat,sku='P1',barcode='123456789012',name='Helmet',unit='PCS').save()
  self.c=Customer(organization=self.org,code='C1',name='Customer without email',gstin='27ABCDE1234F1Z5').save()
 def call(self,view,body=None,method='POST',**kw):
  req=RequestFactory().get('/',body or {}) if method=='GET' else RequestFactory().post('/',json.dumps(body or {}),content_type='application/json');req.api_user=self.user;req.api_organization=self.org;req.user=self.user
  with patch('apps.authorization.services.AuthorizationService.has_permission',return_value=True):return view.__wrapped__(req,**kw)
 def invoice(self,number='I1'):
  return Invoice(organization=self.org,customer=self.c,created_by=self.user,invoice_number=number,invoice_date=datetime(2026,10,1),items=[InvoiceItem(product=self.p,item_name='Helmet',quantity=1,unit_price=100,line_subtotal=100,line_total=100)],subtotal=100,total_amount=100,balance_due=100,billing_name=self.c.name,billing_address='Pune').save()
 def test_pdf_without_customer_email(self):
  inv=self.invoice()
  with patch('apps.authorization.services.AuthorizationService.has_permission',return_value=True):r=DocumentAPIService.generate_pdf(user=self.user,organization=self.org,document_type='invoice',document_id=str(inv.id))
  self.assertTrue(r['content'].startswith(b'%PDF'));self.assertIn('Helmet',PdfReader(io.BytesIO(r['content'])).pages[0].extract_text())
 def test_zip_contains_two_unique_pdfs(self):
  a=self.invoice();b=self.invoice('I2');r=self.call(invoice_zip,{'ids':[str(a.id),str(b.id),str(a.id)]});self.assertEqual(r.status_code,200,r.content)
  with zipfile.ZipFile(io.BytesIO(r.content)) as z:self.assertEqual(len(z.namelist()),2);self.assertTrue(all(z.read(n).startswith(b'%PDF') for n in z.namelist()))
 def test_zip_rejects_unknown_and_empty(self):
  self.assertEqual(self.call(invoice_zip,{'ids':[]}).status_code,400)
  self.assertEqual(self.call(invoice_zip,{'ids':['0'*24]}).status_code,400)
 def test_barcode_exact_match(self):
  r=self.call(barcode_lookup,{'code':'123456789012'},'GET');self.assertEqual(r.status_code,200);self.assertEqual(json.loads(r.content)['data']['id'],str(self.p.id))
  self.assertEqual(self.call(barcode_lookup,{'code':'1234'},'GET').status_code,400)
 def test_barcode_labels(self):
  r=self.call(barcode_labels,{'ids':str(self.p.id),'copies':'2'},'GET');self.assertEqual(r.status_code,200);self.assertTrue(r.content.startswith(b'%PDF'))
  self.assertEqual(self.call(barcode_labels,{'ids':str(self.p.id),'copies':'201'},'GET').status_code,400)
 def test_other_tenant_barcode_inaccessible(self):
  self.org=Organization(name='Other',email='other@example.com').save()
  self.assertEqual(self.call(barcode_lookup,{'code':'123456789012'},'GET').status_code,400)
 def test_direct_minimal_customer_and_auto_codes(self):
  r=self.call(direct_invoice,{'invoice_date':'2026-10-01','customer':{'name':'New customer'},'items':[{'name':'Consultation','item_type':'service','hsn_code':'998519','quantity':'1','unit_price':'100'}],'billing_details':{'supply_type':'unregistered'}})
  self.assertEqual(r.status_code,200,r.content);inv=Invoice.objects.get();self.assertTrue(inv.customer.code);self.assertTrue(inv.items[0].product.sku);self.assertFalse(inv.customer.email)
 def test_direct_selected_customer_is_not_duplicated(self):
  r=self.call(direct_invoice,{'invoice_date':'2026-10-01','customer':{'id':str(self.c.id),'name':self.c.name},'items':[{'sku':'P1','name':'Helmet','quantity':'1','unit_price':'100'}]})
  self.assertEqual(r.status_code,200,r.content);self.assertEqual(Customer.objects.count(),1)
 def test_non_admin_cannot_edit_invoice(self):
  inv=self.invoice();self.user.role=Role(organization=self.org,name='Sales',is_system=False).save();self.user.save()
  self.assertFalse(is_admin(self.user));self.assertEqual(self.call(invoice_details,{'supply_type':'unregistered'},invoice_id=str(inv.id)).status_code,403)
 def test_module_settings_backward_compatible(self):
  r=self.call(modules,{'workforce':False,'expenses':True});self.assertEqual(r.status_code,200,r.content);self.org.reload();self.assertFalse(self.org.workforce_enabled);self.assertTrue(self.org.finance_enabled)
 def test_local_gstin_lookup(self):
  # Unwrap rate limiter too; its HTTP context is covered in the main suite.
  f=lookup
  while hasattr(f,'__wrapped__'):f=f.__wrapped__
  req=RequestFactory().get('/',{'gstin':self.c.gstin});req.api_user=self.user;req.api_organization=self.org
  with patch('apps.authorization.services.AuthorizationService.has_permission',return_value=True):r=f(req)
  self.assertEqual(r.status_code,200,r.content);self.assertEqual(json.loads(r.content)['data']['name'],self.c.name)
 def test_populate_approved_sources_and_retain_allowances(self):
  e=Record(organization=self.org,kind='employees',key='E1',created_by=self.user,data={'code':'E1','name':'Worker','joining_date':'2026-10-01','basis':'daily','rate':'600','overtime_rate':'100','active':True,'employment_type':'inhouse'}).save();eid=str(e.id)
  Record(organization=self.org,kind='timesheets',key='T1',created_by=self.user,data={'employee_id':eid,'date':'2026-10-05','hours':'8','overtime_hours':'2','status':'approved'}).save()
  Record(organization=self.org,kind='leave_requests',key='L1',created_by=self.user,data={'employee_id':eid,'start_date':'2026-10-06','end_date':'2026-10-06','days':'1','leave_type':'paid','status':'approved'}).save()
  Record(organization=self.org,kind='attendance',key=eid+':2026-10',created_by=self.user,data={'employee_id':eid,'month':'2026-10','period_days':'31','paid_days':'0','allowances':'500'}).save()
  r=self.call(populate_inputs,{'month':'2026-10'});self.assertEqual(r.status_code,200,r.content);row=Record.objects(kind='attendance').get().data;self.assertEqual(row['paid_days'],'2');self.assertEqual(row['allowances'],'500');self.assertEqual(row['overtime_hours'],'2.00')
  r=self.call(populate_inputs,{'month':'2026-10'});self.assertEqual(r.status_code,200);self.assertEqual(Record.objects(kind='attendance').count(),1)
 def test_module_routes(self):
  self.assertEqual(module_for('/api/v1/business/records/expenses/'),'expenses');self.assertEqual(module_for('/api/v1/business/barcode/lookup/'),'barcode');self.assertIsNone(module_for('/api/v1/business/modules/'))

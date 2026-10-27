import bootstrap
import unittest,json
from decimal import Decimal
from unittest.mock import patch
from django.test import RequestFactory
from mongoengine.connection import get_db
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.business.models import BusinessRecord as Record
from apps.business.views import validate,payroll
from apps.business.automation import payrow,advances
from apps.business.numbering import allocate,choice
from apps.business.flow_api import daily_work,labour_invoice
from apps.sales.models import Customer,Invoice
from apps.migration.services.employee_import import validate_employee,import_employee
class AutomationTests(unittest.TestCase):
 def setUp(self):
  for c in get_db().list_collection_names():get_db().drop_collection(c)
  self.org=Organization(name='Demo',email='demo@example.com').save();self.user=User(organization=self.org,email='user@example.com',password='test',first_name='Test',last_name='User').save()
  self.emp=self.record('employees','E1',{'code':'E1','name':'Ravi','basis':'daily','rate':'700','joining_date':'2026-01-01','active':True})
 def record(self,kind,key,data):return Record(organization=self.org,kind=kind,key=key,data=data,created_by=self.user).save()
 def req(self,data):
  r=RequestFactory().post('/',data=json.dumps(data),content_type='application/json');r.api_organization=self.org;r.api_user=self.user;return r
 def call(self,data):
  with patch('apps.authorization.services.AuthorizationService.has_permission',return_value=True):r=payroll.__wrapped__(self.req(data))
  return r.status_code,json.loads(r.content)
 def work(self):return self.record('timesheets','work',{'employee_id':str(self.emp.id),'date':'2026-10-01','hours':'8','overtime_hours':'0','status':'approved'})
 def test_advance_capped_at_net(self):
  self.work();self.record('advances','A1',{'employee_id':str(self.emp.id),'date':'2026-09-01','amount':'1000','recovered':'0','reference':'A1'})
  row=payrow(self.org,self.emp,'2026-10',{},'automatic');self.assertEqual(row['inputs']['advance_recovery'],'700.00');self.assertEqual(row['result']['net'],'0.00')
 def test_approval_recovery_and_partial_payment(self):
  self.work();self.record('advances','A1',{'employee_id':str(self.emp.id),'date':'2026-09-01','amount':'100','recovered':'0','reference':'A1'})
  status,out=self.call({'month':'2026-10','mode':'automatic'});self.assertEqual(status,200,out)
  status,out=self.call({'month':'2026-10','action':'approve','revision':out['data']['record']['revision']});self.assertEqual(status,200,out)
  self.assertEqual(out['data']['record']['data']['outstanding_total'],'600.00');self.assertEqual(advances(self.org,str(self.emp.id))[0]['outstanding'],'0.00')
  status,out=self.call({'month':'2026-10','action':'payment','employee_id':str(self.emp.id),'amount':'200','payment_reference':'P1','revision':out['data']['record']['revision']});self.assertEqual(status,200,out);self.assertEqual(out['data']['record']['data']['outstanding_total'],'400.00')
  status,_=self.call({'month':'2026-10','action':'payment','employee_id':str(self.emp.id),'amount':'401','payment_reference':'P2','revision':out['data']['record']['revision']});self.assertEqual(status,400)
 def test_changed_sources_block_approval(self):
  self.work();_,out=self.call({'month':'2026-10','mode':'automatic'});self.emp.data['rate']='800';self.emp.save()
  status,_=self.call({'month':'2026-10','action':'approve','revision':out['data']['record']['revision']});self.assertEqual(status,400)
 def test_locked_work(self):
  self.work();_,out=self.call({'month':'2026-10','mode':'automatic'});self.call({'month':'2026-10','action':'approve','revision':out['data']['record']['revision']});site=self.record('sites','S1',{'name':'Site','code':'S1'})
  with self.assertRaisesRegex(ValueError,'locked'):validate('timesheets',{'employee_id':str(self.emp.id),'site_id':str(site.id),'date':'2026-10-02','shift':'Day','hours':'8','billable_units':'1','billing_rate':'900','status':'approved'},self.org)
 def test_sequences_tenant_isolated(self):
  self.assertEqual(allocate(self.org,'Invoice'),'INV-00001');self.assertEqual(allocate(self.org,'Invoice'),'INV-00002')
  with self.assertRaises(ValueError):allocate(self.org,'Invoice','INV-00001')
  other=Organization(name='Other',email='other@example.com').save();self.assertEqual(allocate(other,'Invoice'),'INV-00001')
 def test_manual_number_and_no_renaming(self):
  c=Customer(organization=self.org,code='OLD',name='Existing').save();token=choice.set({'kind':'Customer','mode':'manual','number':'CUSTOM-1'})
  try:
   c.name='Updated';c.save();self.assertEqual(c.code,'OLD');new=Customer(organization=self.org,code='AUTO',name='New').save();self.assertEqual(new.code,'CUSTOM-1')
  finally:choice.reset(token)
 def test_employee_migration_and_duplicate_skip(self):
  from apps.migration.services.migration_row_validation_service import MigrationRowValidationService
  row={'code':'E2','name':'Amit','joining_date':'2026-01-01','basis':'daily','rate':'650'}
  result=MigrationRowValidationService.validate_rows(organization=self.org,migration_type='EMPLOYEES',rows=[row]);self.assertEqual(result['valid_rows'],1)
  with patch('apps.authorization.services.AuthorizationService.has_permission',return_value=True):import_employee(self.user,self.org,result['rows'][0]['normalized'])
  self.assertEqual(Record.objects(organization=self.org,kind='employees').count(),2)
  result=MigrationRowValidationService.validate_rows(organization=self.org,migration_type='EMPLOYEES',rows=[row],skip_duplicates=True);self.assertTrue(result['rows'][0]['skipped'])
 def test_employee_import_requires_code(self):self.assertFalse(validate_employee(self.org,{'name':'Missing'},set())['valid'])
 def test_employee_migration_access(self):
  from apps.migration.api.v1.employee_access import employee_migration_access
  @employee_migration_access
  def dummy(request):raise AssertionError('Protected view reached')
  with patch('apps.authorization.services.AuthorizationService.has_permission',return_value=False):self.assertEqual(dummy(self.req({'migration_type':'EMPLOYEES'})).status_code,403)
 def test_daily_board_uses_assignment_rate_and_blocks_repeat(self):
  site=self.record('sites','S1',{'code':'S1','name':'ABC','active':True});a=self.record('assignments','A1',{'employee_id':str(self.emp.id),'site_id':str(site.id),'start_date':'2026-10-01','end_date':'2026-10-31','shift':'Day','status':'active','billing_rate':'950'})
  data={'date':'2026-10-01','rows':[{'assignment_id':str(a.id),'hours':'8','overtime_hours':'0','billable_units':'1','billing_rate':'99999'}]}
  with patch('apps.authorization.services.AuthorizationService.has_permission',return_value=True):
   self.assertEqual(daily_work.__wrapped__(self.req(data)).status_code,200);self.assertEqual(daily_work.__wrapped__(self.req(data)).status_code,400)
  self.assertEqual(Record.objects(kind='timesheets').first().data['billing_rate'],'950')
 def test_multiple_shifts_count_one_day(self):
  self.work();self.record('timesheets','work2',{'employee_id':str(self.emp.id),'date':'2026-10-01','hours':'4','status':'approved'})
  row=payrow(self.org,self.emp,'2026-10',{},'automatic');self.assertEqual(row['inputs']['paid_days'],'1');self.assertEqual(row['inputs']['hours'],'12.00')
 def test_invoice_retries_are_idempotent(self):
  Customer(organization=self.org,code='C1',name='ABC').save();site=self.record('sites','S1',{'code':'S1','name':'ABC site','customer_code':'C1'})
  self.record('timesheets','W1',{'site_id':str(site.id),'employee_id':str(self.emp.id),'date':'2026-10-01','status':'approved','billable_units':'1','billing_rate':'950','hours':'8'})
  data={'site_id':str(site.id),'month':'2026-10','invoice_date':'2026-10-31','tax_rate':'0'}
  with patch('apps.authorization.services.AuthorizationService.has_permission',return_value=True):a=labour_invoice.__wrapped__(self.req(data));b=labour_invoice.__wrapped__(self.req(data))
  self.assertEqual(a.status_code,200,a.content);self.assertEqual(b.status_code,200,b.content);self.assertEqual(Invoice.objects.count(),1);self.assertTrue(json.loads(b.content)['data']['existing'])
  inv=Invoice.objects.first();self.assertEqual(inv.total_amount,Decimal('950.00'));self.assertFalse(inv.stock_review_required);self.assertEqual(inv.status,'DRAFT')
if __name__=='__main__':unittest.main(verbosity=2)
